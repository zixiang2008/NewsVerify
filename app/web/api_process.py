"""Build the complete, auditable process record for one verification event.

The same payload powers the public ``/api/v1/events/{id}/process`` endpoint and
the mind-map model returned by ``/api/v1/events/{id}/mindmap``.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Claim, Event, Evidence, Job, Notification, Source, Subscription, Verdict
from app.verification.source_policy import classify_source
from app.verification.top_media import TOP_MEDIA


def _iso(value):
    return value.isoformat() if value else None


def _media_match(url: str, domain: str):
    """Match a source to a Top30 outlet by *host*, never by URL substring.

    A previous ``md in url`` check let any URL whose query string happened to
    contain a media domain (e.g. a Chrome support page carrying a tracking
    parameter) light up that outlet. Only an exact host or a genuine subdomain
    of the outlet counts as a report.
    """
    from urllib.parse import urlparse

    host = (domain or "").lower().strip()
    if not host:
        try:
            host = urlparse(url or "").netloc.lower().split("@")[-1].split(":")[0].rstrip(".")
        except Exception:
            host = ""
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return None, None, None
    for m in TOP_MEDIA:
        md = (m.get("domain") or "").lower()
        if md and (host == md or host.endswith("." + md)):
            return m.get("rank"), m.get("name"), m.get("factual")
    return None, None, None


async def build_process(session: AsyncSession, event_id: str) -> dict | None:
    event = await session.get(Event, event_id)
    if not event:
        return None

    jobs_res = await session.execute(
        select(Job).where(Job.payload["event_id"].as_string() == event_id).order_by(Job.created_at)
    )
    jobs = jobs_res.scalars().all()
    claims = (await session.execute(select(Claim).where(Claim.event_id == event_id))).scalars().all()
    verdicts = (await session.execute(select(Verdict).where(Verdict.event_id == event_id))).scalars().all()
    subs = (await session.execute(select(Subscription).where(Subscription.event_id == event_id))).scalars().all()
    sub_ids = [s.id for s in subs]
    notes = []
    if sub_ids:
        notes = (await session.execute(
            select(Notification).where(Notification.subscription_id.in_(sub_ids)).order_by(Notification.sent_at)
        )).scalars().all()

    job_list = []
    for j in jobs:
        result = j.result or {}
        job_list.append({
            "id": j.id, "kind": j.kind, "status": j.status, "attempts": j.attempts,
            "error": j.error, "result": result,
            "progress": result.get("progress", []),
            "created_at": _iso(j.created_at), "started_at": _iso(j.started_at),
            "finished_at": _iso(j.finished_at),
        })

    claim_list = []
    for c in claims:
        evs = (await session.execute(select(Evidence).where(Evidence.claim_id == c.id))).scalars().all()
        evidence = []
        for ev in evs:
            src = await session.get(Source, ev.source_id)
            url = src.url if src else ""
            domain = (src.domain if src else "") or ""
            stype, _ = classify_source(url)
            rank, media_name, factual = _media_match(url, domain)
            evidence.append({
                "id": ev.id, "snippet": ev.snippet, "stance": ev.stance,
                "url": url, "domain": domain, "title": src.title if src else "",
                "source_type": stype or "untrusted",
                "media_rank": rank, "media_name": media_name, "factual": factual,
                "published_at": _iso(getattr(src, "published_at", None)),
                "retrieved_at": _iso(ev.retrieved_at),
            })
        v = next((x for x in verdicts if x.claim_id == c.id), None)
        claim_list.append({
            "id": c.id, "text": c.text, "language": c.language,
            "verdict": ({
                "label": v.label, "confidence": v.confidence, "rationale": v.rationale,
                "counter_argument": v.counter_argument, "evidence_gaps": v.evidence_gaps,
                "model": v.model, "prompt_version": v.prompt_version, "created_at": _iso(v.created_at),
            } if v else None),
            "evidence": evidence,
        })

    # 2026-11-24 P4: v0.7.x 遗留记录可能"已核实但零证据"。不篡改历史判定，
    # 但在 API/前端显式标注，避免被当成当前版本的判定质量。
    legacy_cutoff = datetime(2026, 11, 19, tzinfo=timezone.utc)
    ev_created = event.created_at
    legacy_claims: list[str] = []
    if ev_created is not None:
        created = ev_created if ev_created.tzinfo else ev_created.replace(tzinfo=timezone.utc)
        if created < legacy_cutoff:
            for c in claim_list:
                v = c.get("verdict") or {}
                if v.get("label") in {"supported", "refuted", "mixed", "outdated"} and not c["evidence"]:
                    v["legacy_unverified"] = True
                    legacy_claims.append(c["text"][:80])

    latest = job_list[-1] if job_list else None
    result = latest.get("result", {}) if latest else {}
    top_media = result.get("top_media") or []
    lit = [m for m in top_media if (m.get("hit_count") or 0) > 0]
    active_subs = [s for s in subs if s.active and not s.paused]

    detail = {
        "id": event.id, "title": event.title, "status": event.status,
        "created_at": _iso(event.created_at), "updated_at": _iso(event.updated_at),
        "summary": result.get("summary"),
        "legacy_warning": (
            "历史版本（v0.8.0 之前）遗留记录：判定为已核实/已证伪但无可打开证据，"
            "请勿作为当前判定质量的依据。"
        ) if legacy_claims else None,
        "legacy_unverified_claims": legacy_claims,
        "retrieval_ok": result.get("retrieval_ok"),
        "collection_diagnostics": result.get("collection_diagnostics", []),
        "media_hits": len(lit), "total_reports": sum(int(m.get("hit_count") or 0) for m in top_media),
        "top_media": top_media, "jobs": job_list, "claims": claim_list,
        "subscriptions": [{
            "id": s.id, "active": s.active, "paused": s.paused,
            "interval_hours": s.interval_hours, "next_run_at": _iso(s.next_run_at),
            "last_run_at": _iso(s.last_run_at),
        } for s in subs],
        "notifications": [{
            "id": n.id, "kind": n.kind, "content_hash": n.content_hash,
            "sent_at": _iso(n.sent_at), "created_at": _iso(n.sent_at),
        } for n in notes],
    }

    model = {
        "eventId": event.id,
        "root": {
            "id": "root", "title": "📰 " + event.title[:30],
            "sub": f"{len(claim_list)} 主张 · {len(lit)}/30 媒体" + (" · 追踪中" if active_subs else ""),
            "action": {"type": "detail", "id": event.id},
        },
        "branches": [
            {"id": "claims", "icon": "🔬", "title": "主张与判定", "meta": f"{len(claim_list)} 条原子主张",
             # D8: 节点标题为图示摘要，超长时显式加省略号，避免"半句"被误读为
             # 截断的主张原文；完整主张见 detail.claims[].text（未截断）。
             "children": [{"id": f"c{i}",
                           "title": (c["text"][:60] + "…") if len(c["text"]) > 60 else c["text"],
                           "full_text": c["text"],
                           "sub": f"证据 {len(c['evidence'])} 条" + (f" · 置信 {int((c['verdict'] or {}).get('confidence', 0) * 100)}%" if c["verdict"] else "")}
                          for i, c in enumerate(claim_list)]},
            {"id": "evidence", "icon": "📚", "title": "证据与溯源",
             "meta": f"{len({e['url'] for c in claim_list for e in c['evidence'] if e['url']})} 个独立来源",
             "children": [{"id": f"e{i}", "title": (e.get("title") or e.get("domain") or "来源")[:46],
                           "sub": (e.get("media_name") or e.get("domain") or "") + (f" · 榜第 {e['media_rank']} 名" if e.get("media_rank") else " · 非榜单来源"),
                           "url": e.get("url", "")}
                          for i, e in enumerate({e["url"]: e for c in claim_list for e in c["evidence"] if e["url"]}.values())]},
            {"id": "media", "icon": "🌐", "title": "媒体覆盖", "meta": f"{len(lit)}/{len(top_media) or 30} 家",
             "children": [{"id": "m0", "title": f"{len(lit)} / {len(top_media) or 30} 家媒体报道", "sub": f"共 {detail['total_reports']} 条来源"},
                          {"id": "m1", "title": "已报道媒体", "sub": "、".join(str(m.get("name")) for m in lit[:10])}]},
            {"id": "track", "icon": "📡", "title": "持续追踪", "meta": f"{len(notes)} 条更新",
             "children": [{"id": "t0", "title": (f"🟢 追踪中 · 间隔 {active_subs[0].interval_hours}h" if active_subs else "⚪ 未开启追踪")}] +
                         [{"id": f"t{i+1}", "title": n["kind"], "sub": n["sent_at"] or ""}
                          for i, n in enumerate(detail["notifications"][:8])]},
            {"id": "progress", "icon": "⏳", "title": "处理进度", "meta": f"{len(result.get('progress', []))} 个步骤",
             "children": [{"id": f"p{i}", "title": str(p.get("step", ""))[:50]} for i, p in enumerate(result.get("progress", []))] or [{"id": "p0", "title": "—", "sub": "暂无进度记录"}]},
            {"id": "history", "icon": "🗂", "title": "任务历史", "meta": f"{len(job_list)} 次执行",
             "children": [{"id": f"j{i}", "title": f"{j['kind']} · {j['status']}", "sub": j["finished_at"] or ""}
                          for i, j in enumerate(job_list)]},
        ],
    }
    return {"detail": detail, "mindmap": model}
