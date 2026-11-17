from __future__ import annotations

import asyncio
import hashlib
from typing import List, Dict, Any
from urllib.parse import urlparse

from app.core.config import get_settings
from app.ingest.fetch import fetch_url
from app.ingest.extract import extract_text
from app.verification.search import unified_search
from app.verification.source_policy import classify_source


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
    for q in queries:
        res = await unified_search(q, max_results=max_results * 4)
        candidate_hits.extend(res)
    try:
        from app.ingest.open_web import enhanced_collect, feed_to_hit
        extra = await enhanced_collect(claim_text[:160], claim_text, max_results=max_results * 2)
        for it in extra.items:
            candidate_hits.append(feed_to_hit(it))
    except Exception:
        pass

    # 通用搜索常被维基/百科/广告占据，可信媒体命中率低。补充对头部公信力
    # 媒体的 site: 查询（公开搜索，合规），确保证据池有真实的主流媒体链接。
    if len([r for r in candidate_hits if (classify_source(r.get("url", ""))[0] in ("media", "fact_checker", "authority"))]) < max_results:
        from app.verification.top_media import TOP_MEDIA
        from app.verification.search import search_duckduckgo as _ddg
        head = [m for m in TOP_MEDIA[:8]]
        async def _site(m):
            try:
                hits = await asyncio.wait_for(_ddg(f"site:{m['domain']} {claim_text[:110]}", max_results=2), timeout=12)
                return hits if isinstance(hits, list) else []
            except Exception:
                return []
        for batch in range(0, len(head), 4):
            group = head[batch:batch + 4]
            for hits in await asyncio.gather(*[_site(m) for m in group], return_exceptions=True):
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
        seen_urls.add(url)
        fr = await fetch_url(url)
        title, text = ("", "")
        if not fr.error and fr.text:
            title, text = extract_text(fr.text, url)
        if not title:
            title = r.get("title", "")
        snippet = (text[:600] if text else r.get("snippet", ""))
        published_at = r.get("published_at") or None
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