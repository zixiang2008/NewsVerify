from __future__ import annotations

import asyncio
import hashlib
import logging
import re
from typing import List, Dict, Any
from urllib.parse import urlparse

log = logging.getLogger("newsverify.evidence")

from app.core.config import get_settings
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


async def collect_evidence(claim_text: str, max_results: int = 8) -> List[Dict[str, Any]]:
    settings = get_settings()
    queries = [claim_text]
    # Also a refutation-oriented query
    queries.append(f"{claim_text} (refutation OR false OR debunk)")
    items: List[Dict[str, Any]] = []
    seen_urls = set()

    # v0.6.0: compliant open-web discovery (Google News RSS + optional custom
    # feeds). This only widens candidate discovery; every hit still passes the
    # strict source whitelist before it can enter the evidence pool.
    candidate_hits: List[Dict[str, Any]] = []

    async def _rss():
        from app.ingest.open_web import enhanced_collect, feed_to_hit, _publisher_hit
        extra = await enhanced_collect(claim_text[:160], claim_text, max_results=max_results * 2)
        hits: List[Dict[str, Any]] = []
        for it in extra.items:
            # Google News item links are news.google.com redirects that the
            # strict policy drops as a search engine. Add the real publisher
            # URL from <source url> so RSS stays a usable fallback channel.
            pub = _publisher_hit(it)
            if pub:
                hits.append(pub)
            hits.append(feed_to_hit(it))
        return hits

    # D6 fix: 三条发现通道（原查询搜索 / 反驳查询搜索 / RSS）并行执行，
    # 整体设 25s 上限，避免串行等待把单条主张拖到数十秒。
    async def _discover():
        search_tasks = [unified_search(q, max_results=max_results * 4) for q in queries]
        results = await asyncio.gather(*search_tasks, _rss(), return_exceptions=True)
        for res in results:
            if isinstance(res, list):
                candidate_hits.extend(res)
            elif isinstance(res, Exception):
                log.debug("discovery channel failed: %s: %s", type(res).__name__, str(res)[:100])
    try:
        await asyncio.wait_for(_discover(), timeout=25)
    except asyncio.TimeoutError:
        log.warning("evidence discovery timed out for %r; continuing with partial candidates", claim_text[:50])
    except Exception as e:
        log.debug("discovery failed for %r: %s", claim_text[:50], str(e)[:100])

    # 2026-11-21 guard: the search upstream returned one fixed, unrelated BBC
    # travel article for every query. That URL is on the trusted-media
    # whitelist, so a trust filter alone cannot catch it. Enforce lexical
    # relevance across *all* discovery channels (search + RSS + site:) before
    # anything can enter the evidence pool.
    candidate_hits = filter_relevant(claim_text, candidate_hits)

    # 通用搜索常被维基/百科/广告占据，可信媒体命中率低。补充对头部公信力
    # 媒体的 site: 查询（公开搜索，合规），确保证据池有真实的主流媒体链接。
    if len([r for r in candidate_hits if (classify_source(r.get("url", ""))[0] in ("media", "fact_checker", "authority"))]) < max_results:
        from app.verification.top_media import TOP_MEDIA
        from app.verification.search import search_duckduckgo as _ddg
        from app.verification.source_policy import CN_AUTHORITY_DOMAINS
        head = [m["domain"] for m in TOP_MEDIA[:8]]
        # D1 fix: 中文/含 CJK 命题追加中文权威媒体 site: 检索，否则白名单全是
        # 西方媒体，文化/常识类中文命题系统性取不到证据。
        if re.search(r"[\u3400-\u9fff]", claim_text):
            head = head[:4] + sorted(CN_AUTHORITY_DOMAINS)[:6]
        async def _site(domain):
            try:
                hits = await asyncio.wait_for(_ddg(f"site:{domain} {claim_text[:110]}", max_results=2), timeout=8)
                return hits if isinstance(hits, list) else []
            except Exception:
                return []
        for batch in range(0, len(head), 4):
            group = head[batch:batch + 4]
            for hits in await asyncio.gather(*[_site(d) for d in group], return_exceptions=True):
                if isinstance(hits, list):
                    candidate_hits.extend([h for h in hits if isinstance(h, dict) and h.get("url")])

    for r in candidate_hits:
        url = r.get("url", "")
        if not url or url in seen_urls:
            continue
        source_type, host = classify_source(url)
        if source_type is None:
            continue
        # 搜索引擎域名只是检索入口，不是证据本身。它们的点击追踪/广告跳转
        # 链接（如 bing.com/aclick）会被白名单放行，但绝不能进入证据池，
        # 否则会跟随大量广告重定向，既污染证据又严重拖慢核查。
        if source_type == "search_engine":
            continue
        fr = await fetch_url(url)
        title, text = ("", "")
        if not fr.error and fr.text:
            title, text = extract_text(fr.text, url)
        # D2 fix: 丢弃反爬/JS 挑战页，绝不能把空页面文本当成有效证据。
        if is_block_page(title or r.get("title", ""), text):
            log.debug("dropping anti-bot/challenge page from evidence: %s", url[:120])
            continue
        if not title:
            title = r.get("title", "")
        snippet = (text[:600] if text else r.get("snippet", ""))
        # D5 fix: 搜索结果通常没有发布日期，从页面 meta 补全。
        published_at = r.get("published_at") or None
        if not published_at and not fr.error and fr.text:
            try:
                from app.ingest.extract import extract_published_at
                published_at = extract_published_at(fr.text)
            except Exception:
                published_at = None
        seen_urls.add(url)
        items.append({
            "title": title,
            "url": url,
            "final_url": fr.final_url if not fr.error else url,
            "snippet": snippet,
            "domain": host,
            "source_type": source_type,
            "content_hash": fr.content_hash,
            "independence_chain_id": _chain_id(url, snippet),
            "fetch_error": fr.error,
            "published_at": published_at,
            "discovery": r.get("discovery", ""),
        })
        if len(items) >= max_results * 2:
            break
    # Dedup by independence chain (collapse same chain)
    # Keep first per chain
    by_chain = {}
    for it in items:
        cid = it["independence_chain_id"]
        if cid not in by_chain:
            by_chain[cid] = it
    return list(by_chain.values())[:max_results]