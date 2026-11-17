from __future__ import annotations

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
    for q in queries:
        # Request a larger pool because the strict source whitelist discards
        # aggregators and content farms (Baidu, QQ, Sohu, Wikipedia, ...).
        res = await unified_search(q, max_results=max_results * 4)
        for r in res:
            url = r.get("url", "")
            if not url or url in seen_urls:
                continue
            source_type, host = classify_source(url)
            if source_type is None:
                continue
            seen_urls.add(url)
            fr = await fetch_url(url)
            title, text = ("", "")
            if not fr.error and fr.text:
                title, text = extract_text(fr.text, url)
            if not title:
                title = r.get("title", "")
            snippet = (text[:600] if text else r.get("snippet", ""))
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
                "published_at": None,
            })
            if len(items) >= max_results * 2:
                break
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