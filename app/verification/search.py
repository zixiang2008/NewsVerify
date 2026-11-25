from __future__ import annotations

import asyncio
import hashlib
import logging
import re
import unicodedata
from typing import List, Dict

import httpx

from app.core.config import get_settings

log = logging.getLogger("newsverify.search")

# ---------------------------------------------------------------------------
# Relevance guard
#
# 2026-11-21 incident: the search upstream returned one fixed, unrelated BBC
# travel article for *every* query (both "Paris is the capital of France" and
# a Chinese lyric check). Because collect_evidence accepted any whitelisted
# URL, the fixed article became the sole "evidence" and every claim was judged
# insufficient_evidence. The upstream cannot be trusted to honour the query,
# so every hit must prove a minimum lexical overlap with the query before it
# is allowed into the evidence pool. This is a retrieval-quality guard, not a
# truth judgment — it only asks "did the engine actually search what we asked".
# ---------------------------------------------------------------------------

_STOPWORDS = {
    # English / Latin function words
    "the", "a", "an", "of", "is", "are", "was", "were", "be", "been", "to",
    "in", "on", "at", "for", "from", "by", "with", "and", "or", "but", "as",
    "it", "its", "this", "that", "these", "those", "do", "does", "did", "not",
    "refutation", "false", "debunk", "news", "report", "article", "latest",
    "best", "top", "travel", "places", "2026", "2025",
    # Chinese function / generic words
    "的", "是", "了", "和", "与", "在", "有", "及", "对", "为", "吗", "呢",
    "什么", "怎么", "哪些", "一个", "我们", "你们", "他们", "这个", "那个",
    "新闻", "报道", "消息", "核查", "事实", "真假", "辟谣",
    # Japanese / Korean common particles (kept minimal)
    "です", "ます", "の", "に", "は", "が", "を", "で",
}

# CJK / Hangul token span — we split these into overlapping bigrams because
# Chinese has no spaces; bigrams give a robust, library-free relevance signal.
_CJK_SPAN = re.compile(r"[\u3400-\u9fff\uac00-\ud7af]+")
_LATIN_WORD = re.compile(r"[a-z0-9][a-z0-9'’\-]{2,}")


def _query_tokens(query: str) -> set[str]:
    """Extract normalised content tokens from a query.

    Latin words are kept whole; each CJK run also contributes character
    bigrams so a single Chinese term still overlaps with titles/snippets that
    use slightly different segmentation.
    """
    text = unicodedata.normalize("NFKC", query or "").lower()
    tokens: set[str] = set()
    for word in _LATIN_WORD.findall(text):
        if word not in _STOPWORDS and len(word) >= 3:
            tokens.add(word)
    for run in _CJK_SPAN.findall(text):
        if len(run) == 1:
            if run not in _STOPWORDS:
                tokens.add(run)
            continue
        for i in range(len(run) - 1):
            bg = run[i:i + 2]
            if bg not in _STOPWORDS:
                tokens.add(bg)
    return tokens


def _haystack(hit: Dict[str, str]) -> str:
    return unicodedata.normalize(
        "NFKC",
        " ".join(str(hit.get(k) or "") for k in ("title", "snippet", "url")),
    ).lower()


def _relevance(query_tokens: set[str], hit: Dict[str, str]) -> float:
    """Fraction of query tokens present in a hit. 0 means unrelated."""
    if not query_tokens:
        return 1.0
    hay = _haystack(hit)
    matched = sum(1 for t in query_tokens if t in hay)
    return matched / len(query_tokens)


def _is_relevant(query: str, hit: Dict[str, str]) -> bool:
    """A hit must share at least one content token, or >=20% of query tokens.

    Short one-token queries (e.g. a person's name) require that single token.
    Long queries tolerate a little noise but never a zero-overlap result.
    """
    tokens = _query_tokens(query)
    if not tokens:
        return True
    score = _relevance(tokens, hit)
    min_hits = 1 if len(tokens) <= 4 else max(1, int(len(tokens) * 0.15))
    matched = sum(1 for t in tokens if t in _haystack(hit))
    return matched >= min_hits and score > 0


def filter_relevant(query: str, hits: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Public helper: drop results that do not relate to the query at all."""
    return [h for h in hits if isinstance(h, dict) and _is_relevant(query, h)]


def _results_signature(hits: List[Dict[str, str]]) -> str:
    urls = sorted(str(h.get("url") or h.get("title") or "") for h in hits if isinstance(h, dict))
    return hashlib.sha256("|".join(urls).encode("utf-8")).hexdigest()[:12]


async def search_duckduckgo(query: str, max_results: int = 8, retries: int = 1) -> List[Dict[str, str]]:
    """联网搜索（ddgs 库）。

    NAS 网络下 DDG 的 html 端点常超时，ddgs 默认会轮询多个后端导致单查询数秒。
    这里按 yahoo → duckduckgo 顺序尝试，任一后端拿到相关结果即返回。

    2026-11-21 加固：上游曾对所有查询返回同一条 BBC 旅游文章。因此每一条结果
    都必须通过查询相关性校验；同一批查询若出现完全相同的固定结果集，判为上游
    异常并返回空，宁可让判定走 insufficient_evidence，也不把无关内容当证据。
    """
    # yahoo first (fast/stable on NAS), duckduckgo as fallback.
    # ddgs is a *synchronous* library: calling it directly inside the event
    # loop blocks every concurrent discovery channel (2026-11-24 incident:
    # a 10s ddgs timeout starved the healthy RSS channel). Always offload it.
    def _ddgs_text(q: str, limit: int, backend_name: str):
        from ddgs import DDGS
        with DDGS() as ddgs:
            return list(ddgs.text(q, max_results=limit, backend=backend_name))

    backends = ["yahoo", "duckduckgo"]
    signatures: set[str] = set()
    for backend in backends:
        for attempt in range(retries + 1):
            results: List[Dict[str, str]] = []
            try:
                raw = await asyncio.to_thread(_ddgs_text, query, max_results, backend)
                for r in raw or []:
                    if r.get("href"):
                        results.append({
                            "title": r.get("title", ""),
                            "url": r.get("href", ""),
                            "snippet": r.get("body", ""),
                        })
                if results:
                    relevant = filter_relevant(query, results)
                    if not relevant:
                        log.warning(
                            "search upstream returned %d results but none relevant to query %r "
                            "(backend=%s, sample=%s) — treating as stale/fixed response",
                            len(results), query[:60], backend,
                            results[0].get("title", "")[:60],
                        )
                        # Do not fall through to a different backend blindly — a
                        # zero-overlap result set is the signature of the fixed
                        # response incident. Continue to next backend which may
                        # be healthy.
                        continue
                    sig = _results_signature(relevant)
                    if sig in signatures:
                        log.warning(
                            "search returned an identical result set across backends for query %r "
                            "(sig=%s) — possible cached/fixed upstream",
                            query[:60], sig,
                        )
                        continue
                    signatures.add(sig)
                    return relevant[:max_results]
                log.info("search backend=%s returned no results for %r", backend, query[:60])
            except Exception as exc:
                log.warning("search backend=%s failed for %r: %s: %s",
                            backend, query[:60], type(exc).__name__, str(exc)[:120])
            if attempt < retries:
                await asyncio.sleep(0.3)

    # Last resort: the ddgs library may be stuck returning a fixed page on this
    # host (2026-11-21 incident). Bypass it and hit the public HTML endpoints
    # directly. Still gated by relevance below.
    try:
        from app.verification.direct_search import direct_search
        direct = await direct_search(query, max_results)
        if direct:
            relevant = filter_relevant(query, direct)
            if relevant:
                log.warning(
                    "ddgs yielded no relevant results for %r; recovered %d via direct HTML search",
                    query[:60], len(relevant),
                )
                return relevant[:max_results]
    except Exception as exc:
        log.warning("direct search fallback failed for %r: %s: %s",
                    query[:60], type(exc).__name__, str(exc)[:80])
    return []


async def search_brave(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    s = get_settings()
    if not s.brave_search_api_key:
        return []
    url = "https://api.search.brave.com/res/v1/web/search"
    headers = {"X-Subscription-Token": s.brave_search_api_key, "Accept": "application/json"}
    params = {"q": query, "count": max_results}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        out = []
        for item in data.get("web", {}).get("results", []):
            out.append({"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("description", "")})
        return filter_relevant(query, out)
    except Exception as exc:
        log.warning("brave search failed for %r: %s: %s", query[:60], type(exc).__name__, str(exc)[:120])
        return []


async def search_searxng(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    s = get_settings()
    if not s.searxng_base_url:
        return []
    url = s.searxng_base_url.rstrip("/") + "/search"
    params = {"q": query, "format": "json", "categories": "general"}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        out = []
        for item in data.get("results", [])[:max_results]:
            out.append({"title": item.get("title", ""), "url": item.get("url", ""), "snippet": item.get("content", "")})
        return filter_relevant(query, out)
    except Exception as exc:
        log.warning("searxng search failed for %r: %s: %s", query[:60], type(exc).__name__, str(exc)[:120])
        return []


async def search_google_factcheck(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    s = get_settings()
    if not s.google_factcheck_api_key:
        return []
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": query, "key": s.google_factcheck_api_key, "pageSize": max_results}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.get(url, params=params)
            r.raise_for_status()
            data = r.json()
        out = []
        for claim in data.get("claims", []):
            text = claim.get("text", "")
            for review in claim.get("claimReview", []):
                out.append({
                    "title": review.get("title", ""),
                    "url": review.get("url", ""),
                    "snippet": f"{text} -> {review.get('textualRating','')} ({review.get('reviewDate','')})",
                })
        return filter_relevant(query, out[:max_results])
    except Exception as exc:
        log.warning("google factcheck failed for %r: %s: %s", query[:60], type(exc).__name__, str(exc)[:120])
        return []


async def unified_search(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    s = get_settings()
    provider = (s.search_provider or "duckduckgo").lower()
    results: List[Dict[str, str]] = []
    if provider == "brave":
        results = await search_brave(query, max_results)
    elif provider == "searxng":
        results = await search_searxng(query, max_results)
    else:
        results = await search_duckduckgo(query, max_results)
    # Always augment with Google Fact Check if key present (official)
    if s.google_factcheck_api_key:
        fc = await search_google_factcheck(query, max_results)
        results = fc + results
    # Final relevance gate — covers every provider, including fact-check API.
    results = filter_relevant(query, results)
    # Dedup by url
    seen = set()
    deduped = []
    for r in results:
        key = r.get("url") or r.get("title")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)
    return deduped[:max_results]


async def search_health_probe(query: str = "Reuters Paris France capital") -> dict:
    """Probe the *whole discovery layer*, not just one metasearch backend.

    2026-11-24: the ddgs/Yahoo backend returned fixed unrelated pages on NAS,
    while Google News RSS (with resolved article URLs) was healthy. A probe
    that only exercised ddgs reported "degraded" even when evidence collection
    worked, and vice versa. Two semantically different queries must return
    different result sets through the combined channels.
    """
    from app.ingest.open_web import enhanced_collect, resolve_news_items

    control = "BBC World News weather forecast tomorrow"

    async def _discover(q: str) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        try:
            feed = await enhanced_collect(q[:120], q, max_results=6)
            out.extend(await resolve_news_items(feed.items, limit=3))
        except Exception as exc:
            log.debug("health probe RSS failed: %s: %s", type(exc).__name__, str(exc)[:80])
        try:
            out.extend(await unified_search(q, max_results=3))
        except Exception as exc:
            log.debug("health probe search failed: %s: %s", type(exc).__name__, str(exc)[:80])
        return filter_relevant(q, out)

    a, b = await asyncio.gather(_discover(query), _discover(control))
    sig_a = _results_signature(a)
    sig_b = _results_signature(b)
    ok = bool(a) and bool(b) and sig_a != sig_b
    return {
        "healthy": ok,
        "query_results": len(a),
        "control_results": len(b),
        "query_signature": sig_a,
        "control_signature": sig_b,
        "channels": {"rss": "google_news", "search": get_settings().search_provider},
        "detail": "ok" if ok else "retrieval appears stale or unavailable",
    }
