from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone, timedelta

from aiogram import Bot

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.models import Claim, Event, Job, Subscription, Verdict, Evidence, Source
from sqlalchemy.orm.attributes import flag_modified
from app.db.session import get_sessionmaker, init_db
from app.verification.claims import extract_claims
from app.verification.evidence import collect_evidence
from app.verification.judge import judge_claim
from app.verification.top_media import check_top_media, TOP_MEDIA
from app.tracking.diff import evidence_fingerprint
from app.bot.keyboards import check_keyboard


async def _update_progress(job_id: str, step: str) -> None:
    sm = get_sessionmaker()
    async with sm() as s:
        from app.db.models import Job
        j = await s.get(Job, job_id)
        if j is not None:
            res = j.result or {}
            prog = res.get("progress", [])
            prog.append({"step": step, "time": datetime.now(timezone.utc).isoformat()})
            res["progress"] = prog
            j.result = res
            flag_modified(j, "result")
            await s.commit()


def _freq_to_hours(freq: str) -> int:
    """把提交时选择的更新频率映射为小时数；与 web 层 _interval_to_hours 保持一致。"""
    mapping = {"6h": 6, "12h": 12, "24h": 24, "3d": 72, "week": 168}
    return mapping.get((freq or "").lower(), 24)


async def _ensure_subscription(event_id: str, freq: str, chat_id, text: str) -> None:
    """落实提交时选择的“更新频率”：核查完成后据此创建/更新订阅。

    过去 freq 只被写进 job.payload，worker 从未消费，导致用户以为开启了追踪
    实际却没有订阅。这里幂等地建立订阅，避免与手动 /api/track 产生重复。
    """
    if not freq or freq == "none":
        return
    sm = get_sessionmaker()
    iv = _freq_to_hours(freq)
    async with sm() as s:
        from sqlalchemy import select
        from app.db.models import Subscription
        res = await s.execute(
            select(Subscription).where(
                Subscription.event_id == event_id, Subscription.active == True  # noqa: E712
            )
        )
        sub = res.scalars().first()
        if sub:
            sub.interval_hours = iv
            sub.paused = False
            sub.next_run_at = datetime.now(timezone.utc) + timedelta(hours=iv)
        else:
            s.add(Subscription(
                event_id=event_id,
                user_id=int(chat_id or 0),
                chat_id=int(chat_id or 0),
                interval_hours=iv,
                next_run_at=datetime.now(timezone.utc) + timedelta(hours=iv),
            ))
        await s.commit()


async def _process_check_job(job: Job, bot: Bot) -> None:
    sm = get_sessionmaker()
    settings = get_settings()
    payload = job.payload or {}
    event_id = payload.get("event_id")
    text = payload.get("text", "")
    urls = payload.get("urls", []) or []
    deep = payload.get("deep", False)
    chat_id = payload.get("chat_id")
    freq = payload.get("freq", "none")
    max_claims = settings.max_claims_per_check * (2 if deep else 1)
    max_results = settings.max_search_results * (2 if deep else 1)

    await _update_progress(job.id, "收到任务，开始核查")
    # Gather source text
    source_text = text
    from app.ingest.fetch import fetch_url
    from app.ingest.extract import extract_text
    from app.ingest.platforms import handle_youtube, handle_x
    url_texts = []
    for u in urls:
        low = u.lower()
        if "youtube.com" in low or "youtu.be" in low:
            title, t, note = await handle_youtube(u)
        elif "x.com" in low or "twitter.com" in low:
            title, t, note = await handle_x(u)
        else:
            fr = await fetch_url(u)
            if fr.error:
                t = ""
                note = f"Fetch failed: {fr.error}"
            else:
                title, t = extract_text(fr.text, u)
                note = "OK"
        url_texts.append((u, title, t, note))
        if t:
            source_text += f"\n\n[URL {u}]\n{t}"

    # Mode: full = 完整流水线 + Top30；method = 仅方法论流水线；top30 = 仅媒体覆盖快查
    mode = (payload.get("mode") or "full")
    media_only = mode == "top30"
    if media_only:
        claims = []
        await _update_progress(job.id, "快速模式：仅执行 Top 30 媒体覆盖核查")
    else:
        claims = await extract_claims(source_text, max_claims=max_claims)
        await _update_progress(job.id, f"主张拆分完成：{len(claims)} 条")
    if not claims and not media_only:
        claims = [{"text": source_text[:500], "language": "unknown", "checkable": True}]

    async with sm() as session:
        # load event
        from sqlalchemy import select
        ev = await session.get(Event, event_id)
        if ev is None:
            ev = Event(id=event_id, title=text[:120] or "news", status="running")
            session.add(ev)
            await session.flush()

        verdict_lines = []
        all_evidence_items = []
        collection_diagnostics: list[dict] = []
        for c in claims:
            claim_text = c["text"]
            claim = Claim(event_id=event_id, text=claim_text, language=c.get("language", "unknown"))
            session.add(claim)
            await session.flush()

            diag: dict = {}
            evidence_items = await collect_evidence(claim_text, max_results=max_results, diagnostics=diag)
            collection_diagnostics.append({"claim": claim_text[:120], **diag})
            progress = f"证据收集：{claim_text[:30]} → {len(evidence_items)} 条"
            if diag.get("fetch_failed"):
                progress += f"（抓取失败/拦截页跳过 {diag['fetch_failed']} 个，换源重试）"
            if diag.get("reader_recovered"):
                progress += f"（读取代理恢复 {diag['reader_recovered']} 个）"
            await _update_progress(job.id, progress)
            # persist sources/evidence in the same session
            persisted = 0
            for ei in evidence_items:
                url = ei.get("url") or ""
                res = await session.execute(select(Source).where(Source.url == url))
                src = res.scalar_one_or_none()
                if src is None:
                    # 解析 RSS/搜索返回的发布时间；解析失败则留空（后续用 created_at 兜底）
                    pub = None
                    raw_pub = ei.get("published_at")
                    if raw_pub:
                        try:
                            pub = datetime.fromisoformat(str(raw_pub).replace("Z", "+00:00"))
                            if pub.tzinfo is None:
                                pub = pub.replace(tzinfo=timezone.utc)
                        except Exception:
                            pub = None
                    src = Source(
                        url=url,
                        domain=ei.get("domain", ""),
                        title=ei.get("title", ""),
                        content_hash=ei.get("content_hash", ""),
                        independence_chain_id=ei.get("independence_chain_id", ""),
                        published_at=pub,
                        fetched_at=datetime.now(timezone.utc),
                    )
                    session.add(src)
                    await session.flush()
                evi = Evidence(
                    claim_id=claim.id,
                    source_id=src.id,
                    stance="neutral",
                    snippet=ei.get("snippet", ""),
                    snippet_hash=hashlib.sha256((ei.get("snippet") or "").encode()).hexdigest(),
                )
                session.add(evi)
                persisted += 1
            await session.flush()
            await _update_progress(job.id, f"证据持久化：{persisted}/{len(evidence_items)} 条")

            v = await judge_claim(claim_text, evidence_items)
            await _update_progress(job.id, f"判定：{claim_text[:30]} → {v['label']}")
            verdict = Verdict(
                event_id=event_id,
                claim_id=claim.id,
                label=v["label"],
                confidence=v["confidence"],
                rationale=v["rationale"],
                counter_argument=v["counter_argument"],
                evidence_gaps=v["evidence_gaps"],
                model=get_settings().llm_judge_model,
                prompt_version="v1",
            )
            session.add(verdict)
            await session.flush()

            all_evidence_items.extend(evidence_items)
            verdict_lines.append(f"- [{v['label']}] {claim_text}\n  理由: {v['rationale'][:300]}")

        ev.status = "done"
        await session.commit()

    # Top-30 媒体交叉核查（best-effort，并发，带超时）
    # 前端据此为每条新闻点亮/置灰媒体；method 模式跳过，top30 模式只做这一步。
    top_media_results = []
    top_media_by_claim = []
    if mode in ("full", "top30"):
        try:
            await _update_progress(job.id, f"Top {len(TOP_MEDIA)} 媒体核查开始")
            # 只对最能代表新闻的首条主张做 Top30 媒体覆盖核查（避免逐条核查导致耗时翻倍）
            r = await check_top_media(
                claims[0]["text"] if claims else source_text[:200],
                max_per=2, evidence_items=all_evidence_items,
            )
            top_media_by_claim.append({"claim": claims[0]["text"] if claims else source_text[:200], "media": r})
            top_media_results = r
            hits = sum(1 for x in top_media_results if x.get("hit_count"))
            reports = sum(int(x.get("hit_count") or 0) for x in top_media_results)
            await _update_progress(job.id, f"Top {len(TOP_MEDIA)} 媒体核查完成：{hits} 家报道 / {reports} 条来源")
        except Exception as e:
            top_media_results = []
            top_media_by_claim = []
            await _update_progress(job.id, f"Top 30 核查跳过: {str(e)[:60]}")

    # Summary for UI
    media_hits = sum(1 for x in top_media_results if x.get("hit_count"))
    if verdict_lines:
        summary = "；".join(verdict_lines)
    elif media_only:
        summary = f"Top 30 媒体覆盖快查：{media_hits} 家媒体报道"
    else:
        summary = "无主张"

    # Build message
    fp = evidence_fingerprint(all_evidence_items)
    msg = ("Top 30 媒体覆盖快查" if media_only else "核查完成") + "\n\n" + "\n".join(verdict_lines)
    if media_only:
        msg += f"\n媒体报道: {media_hits}/{len(top_media_results)} 家"
    msg += f"\n\n证据条数: {len(all_evidence_items)}\n事件ID: {event_id}"
    if len(msg) > 3800:
        msg = msg[:3800] + "\n…[truncated]"
    if bot is not None and chat_id is not None:
        try:
            await bot.send_message(chat_id, msg, reply_markup=check_keyboard(event_id))
        except Exception as e:
            print(f"[worker] IM 结果推送失败 job={job.id} chat={chat_id}: {type(e).__name__}: {e}")

    # 落实提交时选择的更新频率：核查完成后建立/更新订阅（幂等）。
    # D7: 订阅是 last-mile 操作，失败不能让一个结果已完整的 job 被标 failed。
    try:
        await _ensure_subscription(event_id, freq, chat_id, text)
    except Exception as e:
        print(f"[worker] 追踪订阅落实失败（不影响核查结果） job={job.id}: {type(e).__name__}: {e}")
        await _update_progress(job.id, f"追踪订阅设置失败（结果不受影响）: {str(e)[:60]}")

    # store final result on the job, preserving the accumulated progress timeline.
    async with sm() as session:
        jj = await session.get(Job, job.id)
        if jj is not None:
            jj.status = "done"
            # 媒体覆盖统计：首条主张有多少家媒体报道
            media_hits = sum(1 for x in top_media_results if x.get("hit_count"))
            total_reports = sum(int(x.get("hit_count") or 0) for x in top_media_results)
            # 关键修复：过去这里直接覆盖 jj.result，丢掉了 _update_progress 累积的
            # progress 时间线，导致任务完成后弹窗里的“处理进度”变空。改为基于现有
            # result 合并，仅覆盖最终结果字段，保留 progress。
            res = dict(jj.result or {})
            # 内容层健康信号：接口 200 但证据全空时，监控不能报"健康"。
            retrieval_ok = bool(all_evidence_items)
            warnings = list(res.get("warnings") or [])
            if not retrieval_ok:
                warnings.append("检索取证层未返回任何证据：请检查 /api/v1/search/health，勿据此判定事实")
            res.update({
                "event_id": event_id, "claims": len(claims), "fingerprint": fp,
                "top_media": top_media_results,
                "top_media_by_claim": top_media_by_claim,
                "media_hits": media_hits,
                "total_reports": total_reports,
                "summary": summary,
                "retrieval_ok": retrieval_ok,
                "collection_diagnostics": collection_diagnostics,
                "warnings": warnings[-10:],
            })
            jj.result = res
            flag_modified(jj, "result")
            jj.finished_at = datetime.now(timezone.utc)
            await session.commit()


async def _process_subscription(sub: Subscription, bot: Bot) -> None:
    sm = get_sessionmaker()
    settings = get_settings()
    async with sm() as session:
        from sqlalchemy import select
        # The caller claims the subscription in a *different* session before
        # scheduling this task, so re-attach it here; otherwise the final
        # next_run_at / fingerprint updates would be lost on a detached object.
        current = await session.get(Subscription, sub.id)
        if current is None or not current.active or current.paused:
            return
        sub = current
        ev = await session.get(Event, sub.event_id)
        if ev is None:
            return
        # Re-run a lightweight check: collect evidence for claims
        # For MVP, re-collect evidence for first claim only to detect changes
        claims_res = await session.execute(select(Claim).where(Claim.event_id == ev.id))
        claims = claims_res.scalars().all()
        if not claims:
            return
        all_items = []
        for c in claims[:3]:
            items = await collect_evidence(c.text, max_results=6)
            all_items.extend(items)
        # 去重后的唯一来源数，作为可读摘要的一部分
        unique_sources = len({(i.get("url") or "") for i in all_items if i.get("url")})
        fp = evidence_fingerprint(all_items)
        if fp and fp != sub.last_evidence_fingerprint and sub.last_evidence_fingerprint:
            # change detected -> notify
            from app.db.models import Notification
            content_hash = fp
            # 可读摘要：写进 kind 字段（String(32)），前端据此显示，而不是只显示哈希。
            readable = f"证据变化 · {unique_sources} 家来源"
            # dedup
            existing = await session.execute(
                select(Notification).where(Notification.subscription_id == sub.id, Notification.content_hash == content_hash)
            )
            if existing.scalar_one_or_none() is None:
                note = Notification(subscription_id=sub.id, content_hash=content_hash, kind=readable[:32])
                session.add(note)
                await session.commit()
                # 多渠道推送：优先走已配置的 IM 渠道（含 Telegram / 飞书 / 钉钉等），
                # 不再只依赖 Telegram bot.send_message(chat_id=0)——那对 web 订阅必然失败。
                notify_text = (
                    f"📡 追踪更新 · 事件 {sub.event_id[:8]}\n"
                    f"{readable}\n新证据条数: {len(all_items)}"
                )
                await _broadcast_im(notify_text, bot if (sub.chat_id or 0) != 0 else None, sub.chat_id)
        elif fp and not sub.last_evidence_fingerprint:
            # 首次基线：不发“变化”通知，但记录一条“追踪已启动”，让用户有明确反馈。
            from app.db.models import Notification
            baseline_hash = "baseline:" + fp[:24]
            existing = await session.execute(
                select(Notification).where(Notification.subscription_id == sub.id, Notification.content_hash == baseline_hash)
            )
            if existing.scalar_one_or_none() is None:
                session.add(Notification(subscription_id=sub.id, content_hash=baseline_hash,
                                         kind="追踪已启动 · 建立基线"))
                await session.commit()
        sub.last_evidence_fingerprint = fp
        sub.last_run_at = datetime.now(timezone.utc)
        sub.next_run_at = datetime.now(timezone.utc) + timedelta(hours=sub.interval_hours)
        await session.commit()


async def _broadcast_im(text: str, bot: Bot | None, telegram_chat_id) -> None:
    """把追踪更新推送到所有已配置的 IM 渠道；Telegram 仅在有有效 chat_id 时额外推送。"""
    from app.integrations import registry as im_registry, IMReply
    try:
        await im_registry.reload_from_db()
        for ch in im_registry.catalogue():
            if not ch.get("configured"):
                continue
            channel = im_registry.get(ch["key"])
            if not channel:
                continue
            try:
                await channel.send_message("tracking", IMReply(text=text))
            except Exception as e:
                print(f"[worker] IM 渠道推送失败 {ch.get('key')}: {type(e).__name__}: {e}")
                continue
    except Exception as e:
        print(f"[worker] IM 渠道重载失败: {type(e).__name__}: {e}")
    if bot is not None and telegram_chat_id:
        try:
            await bot.send_message(telegram_chat_id, text)
        except Exception as e:
            print(f"[worker] Telegram 追踪推送失败 chat={telegram_chat_id}: {type(e).__name__}: {e}")


async def run_worker() -> None:
    settings = get_settings()
    setup_logging(settings.log_level)
    await init_db()
    # Bot 仅用于结果推送；token 缺失/失效不应导致整个核查系统瘫痪。
    # 降级时 bot=None，核查照常执行，只是跳过 Telegram 推送。
    bot = None
    try:
        if settings.telegram_bot_token:
            bot = Bot(token=settings.telegram_bot_token)
    except Exception as _e:  # noqa: BLE001
        print(f"[worker] Telegram bot 初始化失败，已降级为不推送模式: {_e}")
    sm = get_sessionmaker()
    # 僵尸任务回收：worker 崩溃/重启后，超时的 running job 永远卡住。
    # 启动时把超过 STALE_MINUTES 仍未完成的 running job 重置为 queued 重新处理。
    try:
        from sqlalchemy import update as _update
        stale_before = datetime.now(timezone.utc) - timedelta(minutes=10)
        async with sm() as session:
            await session.execute(
                _update(Job)
                .where(Job.status == "running", Job.started_at < stale_before)
                .values(status="queued", started_at=None)
            )
            await session.commit()
    except Exception as _e:
        print(f"[worker] 僵尸任务回收失败: {_e}")
    # 2026-11-24 P2 fix: 过去每轮按序处理 5 个 job，单条核查数十秒时队尾
    # 要等 5–15 分钟。现在按 WORKER_CONCURRENCY 并发处理，轮询间隔压到 2s。
    concurrency = max(1, int(settings.worker_concurrency or 1))
    sem = asyncio.Semaphore(concurrency)
    sub_sem = asyncio.Semaphore(2)

    async def _run_subscription(sub: Subscription) -> None:
        # 订阅重查可能持续数十秒；绝不能阻塞 queued job 的领取（P2）。
        async with sub_sem:
            try:
                await _process_subscription(sub, bot)
            except Exception as e:
                print(f"[worker] 订阅处理失败 sub={sub.id}: {type(e).__name__}: {e}")

    async def _run_claim_job(job: Job) -> None:
        async with sem:
            try:
                await _process_check_job(job, bot)
            except Exception as e:
                async with sm() as s2:
                    jj = await s2.get(Job, job.id)
                    if jj is not None:
                        # D7 fix: 核心结果（verdicts/evidence）已提交且 event=done 时，
                        # 即便 last-mile 步骤抛错也必须标 done，避免"结果完整却是 failed"。
                        result = jj.result or {}
                        core_complete = bool(result.get("event_id")) and bool(result.get("fingerprint"))
                        if core_complete:
                            jj.status = "done"
                            jj.error = None
                            res = dict(result)
                            warns = list(res.get("warnings") or [])
                            warns.append(f"last-mile 步骤异常（结果完整）: {str(e)[:200]}")
                            res["warnings"] = warns[-10:]
                            jj.result = res
                            flag_modified(jj, "result")
                        else:
                            jj.status = "failed"
                            jj.error = str(e)[:2000]
                        jj.finished_at = datetime.now(timezone.utc)
                        await s2.commit()

    while True:
        try:
            claimed = []
            async with sm() as session:
                from sqlalchemy import select
                res = await session.execute(select(Job).where(Job.status == "queued").order_by(Job.created_at).limit(5))
                jobs = res.scalars().all()
                for j in jobs:
                    j.status = "running"
                    j.started_at = datetime.now(timezone.utc)
                    j.attempts += 1
                    claimed.append(j)
                await session.commit()
            if claimed:
                await asyncio.gather(*[_run_claim_job(j) for j in claimed], return_exceptions=True)
            # Process due subscriptions without blocking the job queue:
            # claim them first, then schedule as background tasks.
            claimed_subs = []
            async with sm() as session:
                from sqlalchemy import select
                now = datetime.now(timezone.utc)
                res = await session.execute(select(Subscription).where(Subscription.active == True, Subscription.paused == False, Subscription.next_run_at <= now))
                for sub in res.scalars().all():
                    sub.next_run_at = now + timedelta(minutes=10)
                    claimed_subs.append(sub)
                await session.commit()
            for sub in claimed_subs:
                asyncio.create_task(_run_subscription(sub))
        except Exception as e:
            print("worker error:", e)
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run_worker())