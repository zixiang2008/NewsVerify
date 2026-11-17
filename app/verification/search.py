from __future__ import annotations

import httpx
from typing import List, Dict

from app.core.config import get_settings


async def search_duckduckgo(query: str, max_results: int = 8, retries: int = 1) -> List[Dict[str, str]]:
    """联网搜索（ddgs 库）。

    实测 NAS 网络下 DDG 的 html 端点常超时，而 ddgs 默认会轮询 7 个搜索引擎
    后端导致单查询 7 秒以上。这里显式锁定单一后端：优先 yahoo（快且稳定），
    失败再退到 duckduckgo；避免全后端轮询。函数名保留历史命名。
    """
    import asyncio

    backends = ["yahoo", "duckduckgo"]
    for backend in backends:
        for attempt in range(retries + 1):
            results: List[Dict[str, str]] = []
            try:
                from ddgs import DDGS
                with DDGS() as ddgs:
                    for r in ddgs.text(query, max_results=max_results, backend=backend):
                        if r.get("href"):
                            results.append({"title": r.get("title", ""), "url": r.get("href", ""), "snippet": r.get("body", "")})
                if results:
                    return results
            except Exception:
                pass
            if attempt < retries:
                await asyncio.sleep(0.3)
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
        return out
    except Exception:
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
        return out
    except Exception:
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
        return out[:max_results]
    except Exception:
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
        # prepend official
        results = fc + results
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