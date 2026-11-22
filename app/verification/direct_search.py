"""Direct HTML search fallback that bypasses the ddgs metasearch library.

2026-11-21 incident: ddgs (yahoo backend) returned one fixed, unrelated BBC
travel article for every query on the NAS host. This module hits the public
HTML endpoints directly with httpx + BeautifulSoup so retrieval can recover
even when the metasearch library is stuck. It is intentionally isolated and
best-effort: any failure simply yields an empty list.

All parsing is read-only public HTML; no login, paywall or CAPTCHA bypass.
Every hit is still subject to the query-relevance gate and the strict source
whitelist downstream — this module only widens discovery.
"""
from __future__ import annotations

import logging
from typing import List, Dict
from urllib.parse import quote, urlparse, parse_qs, unquote

import httpx
from bs4 import BeautifulSoup

log = logging.getLogger("newsverify.direct_search")

UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 NewsVerifyFactCheck/0.8 (+research)"
)


def _text(el) -> str:
    try:
        return el.get_text(" ", strip=True) if el is not None else ""
    except Exception:
        return ""


def _parse_yahoo(html: str, limit: int) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict[str, str]] = []
    for block in soup.select("div.algo, div.dd.algo, div[data-testid='algo']"):
        a = block.select_one("h3 a") or block.select_one("h3.title a")
        if a is None:
            continue
        url = (a.get("href") or "").strip()
        title = _text(a)
        if not url or not title:
            continue
        snippet_el = (
            block.select_one("div.compText")
            or block.select_one("span.fc-fz-14")
            or block.select_one("div.fc-fz-14")
        )
        out.append({"title": title, "url": url, "snippet": _text(snippet_el)})
        if len(out) >= limit:
            break
    return out


def _parse_ddg(html: str, limit: int) -> List[Dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    out: List[Dict[str, str]] = []
    for block in soup.select("div.result, div.web-result"):
        a = block.select_one("a.result__a")
        if a is None:
            continue
        title = _text(a)
        href = (a.get("href") or "").strip()
        url = ""
        if "uddg=" in href:
            try:
                qs = parse_qs(urlparse(href).query)
                url = unquote(qs.get("uddg", [href])[0])
            except Exception:
                url = href
        elif href.startswith("http"):
            url = href
        elif href.startswith("//"):
            url = "https:" + href
        if not url or not title:
            continue
        snippet_el = block.select_one("a.result__snippet") or block.select_one("div.result__snippet")
        out.append({"title": title, "url": url, "snippet": _text(snippet_el)})
        if len(out) >= limit:
            break
    return out


async def direct_search(query: str, max_results: int = 8) -> List[Dict[str, str]]:
    """Try Yahoo HTML then DuckDuckGo HTML; return the first non-empty set."""
    engines = [
        ("yahoo", "https://search.yahoo.com/search?p=" + quote(query), _parse_yahoo),
        ("ddg", "https://html.duckduckgo.com/html/?q=" + quote(query), _parse_ddg),
    ]
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True, headers={"User-Agent": UA}) as client:
            for name, url, parser in engines:
                try:
                    resp = await client.get(url)
                    if resp.status_code >= 400:
                        log.warning("direct search %s HTTP %s", name, resp.status_code)
                        continue
                    results = parser(resp.text, max_results)
                    if results:
                        return results
                    log.info("direct search %s returned no parseable results", name)
                except Exception as exc:
                    log.warning("direct search %s failed: %s: %s", name, type(exc).__name__, str(exc)[:80])
    except Exception as exc:
        log.warning("direct search client failed: %s: %s", type(exc).__name__, str(exc)[:80])
    return []
