from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

import httpx

log = logging.getLogger("newsverify.evidence")

from app.core.config import get_settings
from app.core.security import validate_url
from app.ingest.fetch import fetch_url
from app.ingest.extract import extract_text
from app.verification.search import unified_search, filter_relevant
from app.verification.source_policy import classify_source


# 2026-11-22 D2 fix: 反爬/JS 挑战页的特征串。它们内容为空或只有一句提示，
# 却被当成"有效证据"进入证据池（缺陷报告：30% 证据是 Access Denied）。
_BLOCK_PAGE_MARKERS = (
    "access denied", "just a moment", "enable js", "enable javascript",
    "javascript and cookies", "disable any ad blocker", "checking your browser",
    "cf-browser-verification", "please enable cookies", "403 forbidden",
    "request blocked", "are you a robot", "验证以继续", "请开启 javascript",
)


def is_block_page(title: str, text: str) -> bool:
    """True when a fetched page is an anti-bot / JS challenge rather than content."""
    head = f"{title or ''}\n{text or ''}"[:1500].lower()
    if not head.strip():
        return True
    if any(m in head for m in _BLOCK_PAGE_MARKERS):
        # A real article may mention e.g. "enable JavaScript" deep in the body;
        # only treat it as a block page when the marker is in the first ~400 chars
        # (challenge pages put it front and centre) or the body is very short.
        lead = head[:400]
        if any(m in lead for m in _BLOCK_PAGE_MARKERS) or len(text or "") < 200:
            return True
    return len(text or "") < 80


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.lower()
    except Exception:
        return ""


def _chain_id(url: str, text: str) -> str:
    """来源独立性链 ID（借鉴 Veracity / MBFC 的来源独立性实践）。

    启发式规则：
    - 同一域名 + 相同正文前 80 字 → 同一条独立性链（同源/转载折叠）；
    - 不同域名即使正文相似也保留为独立来源，但正文指纹会写入 snippet_hash
      供上层判定使用。
    这样“多家转载同一通稿”不会伪装成多份独立证据。
    """
    normalized = "".join((text or "").split())[:80]
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12] if normalized else "empty"
    return _domain(url) + ":" + h


async def _fetch_jina_reader(url: str) -> Dict[str, Any] | None:
    """Best-effort reader fallback for anti-bot pages (opt-in via env).

    Only public article URLs are sent, and the evidence link stays the original
    publisher URL. The reader is a retrieval aid, not a source of authority.
    """
    settings = get_settings()
    if not getattr(settings, "jina_reader_fallback", False):
        return None
    try:
        validate_url(url)
        proxy = "https://r.jina.ai/" + url
        async with httpx.AsyncClient(timeout=14, follow_redirects=True) as client:
            resp = await client.get(proxy, headers={"User-Agent": "NewsVerifyFactCheck/0.8"})
        if resp.status_code >= 400 or len(resp.text) < 200:
            return None
        text = resp.text
        title = ""
        for line in text.splitlines()[:4]:
            if line.lower().startswith("title:"):
                title = line.split(":", 1)[1].strip()
                break
        if is_block_page(title, text):
            return None
        return {"title": title, "text": text, "final_url": url,
                "content_hash": hashlib.sha256(resp.content).hexdigest(),
                "via": "jina_reader"}
    except Exception as exc:
        log.debug("reader fallback failed for %s: %s: %s", url[:90], type(exc).__name__, str(exc)[:80])
        return None


async def collect_evidence(claim_text: str, max_results: int = 8,
                           diagnostics: Dict[str, Any] | None = None) -> List[Dict[str, Any]]:
    """Collect openable, relevant, trusted evidence for one claim.

    ``diagnostics`` is an optional out-parameter used by the worker to surface
    fetch_failed / anti-bot counts in the progress timeline without changing
    the evidence contract.
    """
    settings = get_settings()
    diag: Dict[str, Any] = diagnostics if diagnostics is not None else {}
    diag.update({"discovered": 0, "relevant": 0, "fetch_failed": 0,
                 "block_pages": 0, "reader_recovered": 0, "accepted": 0})
    queries = [claim_text, f"{claim_text} (refutation OR false OR debunk)"]
    items: List[Dict[str, Any]] = []
    seen_urls: set[str] = set()

    # v0.6.0: compliant open-web discovery (Google News RSS + optional custom
    # feeds). v0.8.4: RSS article links are resolved to the real publisher URL
    # — <source url> is only a homepage and must never become evidence.
    async def _rss():
        from app.ingest.open_web import enhanced_collect, resolve_news_items
        cjk = bool(re.search(r"[\u3400-\u9fff]", claim_text))
        locale = "zh-CN" if cjk else "en-US"
        extra = await enhanced_collect(claim_text[:160], claim_text,
                                       max_results=max(max_results * 2, 12))
        resolved = await resolve_news_items(extra.items, limit=max(max_results * 2, 12), locale=locale)
        if not resolved:
            log.warning("RSS discovery produced no resolvable articles for %r", claim_text[:50])
        return resolved

    # D6 fix: 三条发现通道（原查询搜索 / 反驳查询搜索 / RSS）并行执行。
    # 2026-11-24 P3: 过去用 gather 统一等待，任何一条慢通道超时都会取消全部
    # 通道（包括已经完成的 RSS），导致"失败路径 80 秒且 0 证据"。现在逐条
    # 完成即并入候选池，并为每条通道单独设超时。
    candidate_hits: List[Dict[str, Any]] = []
    channels = [
        ("search", asyncio.wait_for(unified_search(queries[0], max_results=max_results * 3), timeout=8)),
        ("refutation", asyncio.wait_for(unified_search(queries[1], max_results=max_results * 3), timeout=8)),
        ("rss", asyncio.wait_for(_rss(), timeout=12)),
    ]
    tasks = [asyncio.create_task(coro) for _, coro in channels]
    task_names = {t: name for t, (name, _) in zip(tasks, channels)}
    try:
        for fut in asyncio.as_completed(tasks, timeout=13):
            name = task_names.get(fut, "channel")
            try:
                res = await fut
            except Exception as exc:
                log.debug("discovery channel failed: %s: %s", type(exc).__name__, str(exc)[:100])
                continue
            if isinstance(res, list):
                candidate_hits.extend(res)
                log.debug("discovery channel %s yielded %d candidates", name, len(res))
    except asyncio.TimeoutError:
        log.warning("evidence discovery timed out for %r; using %d partial candidates",
                    claim_text[:50], len(candidate_hits))
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()

    diag["discovered"] = len(candidate_hits)
    # 2026-11-21 guard: fixed/unrelated upstream results must never enter the
    # evidence pool. Applied to every discovery channel, including RSS.
    candidate_hits = filter_relevant(claim_text, candidate_hits)
    diag["relevant"] = len(candidate_hits)

    # 通用搜索常被维基/百科/广告占据，可信媒体命中率低。仅当发现通道没有拿到
    # 足够可信命中时才补做少量 site: 查询；有 RSS 结果时直接跳过，省下十几秒。
    trusted_count = len([
        r for r in candidate_hits
        if classify_source(r.get("url", ""))[0] in ("media", "fact_checker", "authority")
    ])
    if trusted_count < 2:
        from app.ingest.open_web import enhanced_collect, resolve_news_items
        from app.verification.top_media import TOP_MEDIA
        cjk = bool(re.search(r"[\u3400-\u9fff]", claim_text))
        # site: 查询改走 Google News RSS：2026-11-24 实测 ddgs 的 site: 检索
        # 在该 NAS 出口全部返回空/无关页，而 Google News RSS 能返回新华社、
        # 央视网等真实文章。用短关键词而非整句，命中率更高。
        filler = "的是了在与为对和及吗呢什么哪些一个我们你们他们这个那个作者报道新闻核查"
        compact = re.sub(r"[\s，。？！,.?!:：;；]+", " ", claim_text)
        compact = "".join(" " if ch in filler else ch for ch in compact)
        compact = re.sub(r"\s+", " ", compact).strip()[:80] or claim_text[:80]
        head = [m["domain"] for m in TOP_MEDIA[:4]]
        if cjk:
            head = ["news.cn", "cctv.com", "people.com.cn", "chinanews.com.cn"]
        locale = "zh-CN" if cjk else "en-US"

        async def _site_rss(domain):
            try:
                feed = await asyncio.wait_for(
                    enhanced_collect(f"site:{domain} {compact}", claim_text, max_results=6),
                    timeout=8)
                return await resolve_news_items(feed.items, limit=6, locale=locale)
            except Exception:
                return []

        site_tasks = [asyncio.create_task(_site_rss(d)) for d in head]
        try:
            site_results = await asyncio.wait_for(
                asyncio.gather(*site_tasks, return_exceptions=True), timeout=10)
        except asyncio.TimeoutError:
            site_results = []
            for t in site_tasks:
                t.cancel()
        added = 0
        for hits in site_results:
            if isinstance(hits, list):
                new = [h for h in hits if isinstance(h, dict) and h.get("url")]
                candidate_hits.extend(new)
                added += len(new)
        candidate_hits = filter_relevant(claim_text, candidate_hits)
        diag["site_candidates"] = added
        diag["discovered"] += added
        diag["relevant"] = len(candidate_hits)

    # Fetch candidates concurrently with a bounded fan-out and a hard phase
    # budget. Blocked / failed pages are counted as fetch_failed and never
    # become evidence — the next candidate is used instead.
    sem = asyncio.Semaphore(6)

    async def _prepare(hit: Dict[str, Any]) -> Dict[str, Any] | None:
        url = hit.get("url", "")
        if not url or url in seen_urls:
            return None
        source_type, host = classify_source(url)
        if source_type is None or source_type == "search_engine":
            return None
        async with sem:
            try:
                fr = await asyncio.wait_for(fetch_url(url), timeout=9)
            except Exception as exc:
                diag["fetch_failed"] += 1
                log.debug("fetch timeout/failed %s: %s", url[:90], type(exc).__name__)
                return None
            title, text, raw_html = "", "", ""
            if not fr.error and fr.text:
                raw_html = fr.text
                title, text = extract_text(fr.text, url)
            reject_reason = None
            if fr.error or fr.status_code >= 400:
                reject_reason = f"http_{fr.status_code or 'error'}"
            elif is_block_page(title or hit.get("title", ""), text):
                reject_reason = "anti_bot_challenge"
            if reject_reason:
                diag["fetch_failed"] += 1
                if reject_reason == "anti_bot_challenge":
                    diag["block_pages"] += 1
                reader = await _fetch_jina_reader(url)
                if reader:
                    diag["reader_recovered"] += 1
                    title, text = reader["title"], reader["text"]
                    fr_content_hash, via = reader["content_hash"], reader["via"]
                    pm = re.search(r"Published Time:\s*(\S+)", text[:800])
                    if pm:
                        raw_html = f'<meta property="article:published_time" content="{pm.group(1)}">'
                else:
                    log.info("fetch_failed (%s), trying next source: %s", reject_reason, url[:110])
                    return None
            else:
                fr_content_hash, via = fr.content_hash, ""

        if not title:
            title = hit.get("title", "")
        snippet = (text[:600] if text else hit.get("snippet", ""))
        published_at = hit.get("published_at") or None
        if not published_at and raw_html:
            try:
                from app.ingest.extract import extract_published_at
                published_at = extract_published_at(raw_html)
            except Exception:
                published_at = None
        seen_urls.add(url)
        return {
            "title": title,
            "url": url,
            "final_url": url,
            "snippet": snippet,
            "domain": host,
            "source_type": source_type,
            "content_hash": fr_content_hash,
            "independence_chain_id": _chain_id(url, snippet),
            "fetch_error": None,
            "published_at": published_at,
            "discovery": hit.get("discovery", ""),
            "retrieval_via": via,
        }

    tasks = [asyncio.create_task(_prepare(h))
             for h in candidate_hits[:max(max_results * 2, 12)]]
    try:
        for fut in asyncio.as_completed(tasks, timeout=14):
            try:
                prepared = await fut
            except Exception as exc:
                diag["fetch_failed"] += 1
                log.debug("candidate preparation failed: %s: %s", type(exc).__name__, str(exc)[:80])
                continue
            if prepared:
                items.append(prepared)
                if len(items) >= max_results * 2:
                    break
    except asyncio.TimeoutError:
        log.warning("evidence fetch phase timed out for %r; using %d partial items",
                    claim_text[:50], len(items))
    finally:
        for t in tasks:
            if not t.done():
                t.cancel()

    # Dedup by independence chain (collapse same-chain syndication)
    by_chain: Dict[str, Dict[str, Any]] = {}
    for it in items:
        cid = it["independence_chain_id"]
        if cid not in by_chain:
            by_chain[cid] = it
    result = list(by_chain.values())[:max_results]
    diag["accepted"] = len(result)
    return result
