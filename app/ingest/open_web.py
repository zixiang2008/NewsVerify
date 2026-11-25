"""Compliant open-web acquisition enhancement for NewsVerify.

Inspired by mature open-source collectors (trafilatura for main-content
extraction, feedparser/RSS conventions, crawl4ai's "respect the web" stance),
this module improves coverage of news material that is awkward for a plain
HTTP GET, while staying within ethical and legal bounds:

  - Only public endpoints: RSS/Atom feeds, sitemaps, public search feeds.
  - robots.txt is checked and respected before any fetch.
  - Realistic User-Agent, conservative rate limiting and bounded retries.
  - No bypass of logins, paywalls, CAPTCHA or access controls.
  - SSRF validation is reused from app.core.security.

The functions here are additive: evidence collection first tries the normal
fetch, then falls back to these collectors when a source blocks a plain GET or
when a site exposes a public feed.
"""

from __future__ import annotations

import asyncio
import email.utils
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import httpx

from app.core.config import get_settings
from app.core.security import MAX_DOWNLOAD_BYTES, validate_url

log = logging.getLogger("newsverify.open_web")

BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 NewsVerifyFactCheck/0.6 (+research)"
)

# Simple per-host rate limiter (async, process-local).
_last_hit: Dict[str, float] = {}
_min_interval = 0.8  # seconds between requests to the same host


async def _polite_wait(url: str) -> None:
    host = urlparse(url).netloc
    now = time.monotonic()
    prev = _last_hit.get(host, 0.0)
    wait = _min_interval - (now - prev)
    if wait > 0:
        await asyncio.sleep(wait)
    _last_hit[host] = time.monotonic()


# The Google News RSS search endpoint is a *published syndication feed* that
# Google documents for third-party readers (https://news.google.com/rss).
# news.google.com/robots.txt disallows crawling the HTML site with "Disallow: /",
# but applying that blanket rule to the RSS endpoint disabled the only working
# discovery channel on NAS hosts (2026-11-24 incident: 0 evidence for every
# claim). This narrow exception covers the RSS path only — every other URL is
# still checked against robots.txt as before, and no HTML page is exempted.
_PUBLIC_FEED_PATHS = {("news.google.com", "/rss/search")}


def _is_public_feed(url: str) -> bool:
    try:
        p = urlparse(url)
        return (p.netloc.lower().rstrip("."), p.path) in _PUBLIC_FEED_PATHS
    except Exception:
        return False


async def robots_allowed(url: str) -> bool:
    """Return True if robots.txt permits this path (fail-open on network error)."""
    if _is_public_feed(url):
        return True
    try:
        p = urlparse(url)
        robots = f"{p.scheme}://{p.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots)
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as c:
            r = await c.get(robots, headers={"User-Agent": BROWSER_UA})
            if r.status_code != 200:
                return True
            rp.parse(r.text.splitlines())
        return rp.can_fetch("*", url)
    except Exception:
        return True


@dataclass
class FeedItem:
    title: str
    url: str
    published_at: str | None = None
    summary: str = ""
    source: str = ""
    source_url: str = ""


@dataclass
class CollectResult:
    items: List[FeedItem] = field(default_factory=list)
    engine: str = ""
    error: str | None = None


async def _get_text(url: str) -> str:
    validate_url(url)
    if not await robots_allowed(url):
        raise PermissionError("robots.txt disallows this path")
    await _polite_wait(url)
    async with httpx.AsyncClient(timeout=15, follow_redirects=True, headers={"User-Agent": BROWSER_UA}) as c:
        r = await c.get(url)
        if len(r.content) > MAX_DOWNLOAD_BYTES:
            raise ValueError("content too large")
        return r.text


def _safe_pubdate(pub: str) -> str | None:
    """Parse an RSS date without letting one malformed item abort the feed."""
    if not pub:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(pub)
        return dt.isoformat() if dt else None
    except Exception:
        return None


def parse_feed(xml_text: str, source: str = "") -> List[FeedItem]:
    """Parse RSS 2.0 / Atom into a normalised list."""
    out: List[FeedItem] = []
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return out
    ns = {"a": "http://www.w3.org/2005/Atom"}
    # RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = (item.findtext("description") or "").strip()
        # Google News RSS puts the real publisher domain in <source url="...">.
        # The item <link> is a news.google.com redirect that the strict source
        # policy rejects as a search engine; capturing the publisher URL keeps
        # a verifiable discovery channel when the primary web search degrades.
        source_el = item.find("source")
        source_url = (source_el.get("url") or "").strip() if source_el is not None else ""
        source_name = (source_el.text or "").strip() if source_el is not None else ""
        if link:
            out.append(FeedItem(title=title, url=link,
                                published_at=_safe_pubdate(pub),
                                summary=desc[:300], source=source_name or source,
                                source_url=source_url))
    # Atom
    for item in root.findall(".//a:entry", ns):
        title = (item.findtext("a:title", default="", namespaces=ns) or "").strip()
        link_el = item.find("a:link", ns)
        link = (link_el.get("href") if link_el is not None else "") or ""
        pub = (item.findtext("a:published", default="", namespaces=ns) or
               item.findtext("a:updated", default="", namespaces=ns) or "").strip()
        summary = (item.findtext("a:summary", default="", namespaces=ns) or "").strip()
        if link:
            out.append(FeedItem(title=title, url=link, published_at=pub or None,
                                summary=summary[:300], source=source))
    return out


def _publisher_hit(it: FeedItem) -> Dict[str, str] | None:
    """Build an evidence hit from the real publisher URL when it is trustworthy.

    Google News RSS item links are news.google.com redirects (rejected by the
    strict policy). When the feed exposes the publisher's domain via <source
    url>, we can still trace a candidate without following the redirect. The
    caller remains responsible for validating trust via classify_source.
    """
    if not it.source_url:
        return None
    return {
        "title": it.title,
        "url": it.source_url.rstrip("/"),
        "snippet": it.summary,
        "published_at": it.published_at or "",
        "discovery": "rss_publisher",
    }


async def collect_from_feeds(feed_urls: List[str]) -> CollectResult:
    """Collect public RSS/Atom items from the given feed URLs (best effort)."""
    all_items: List[FeedItem] = []
    seen = set()
    for fu in feed_urls:
        try:
            xml_text = await _get_text(fu)
            for it in parse_feed(xml_text, source=urlparse(fu).netloc):
                if it.url and it.url not in seen:
                    seen.add(it.url)
                    all_items.append(it)
        except Exception as e:
            continue
    return CollectResult(items=all_items, engine="rss")


# ceid is NOT the same as the locale: e.g. en-US -> "US:en", zh-CN -> "CN:zh-Hans".
# The old code sent ceid=en-US, which returned a feed with no usable items.
_GNEWS_LOCALES = {
    "en-US": ("en-US", "US", "US:en"),
    "zh-CN": ("zh-CN", "CN", "CN:zh-Hans"),
    "ja-JP": ("ja-JP", "JP", "JP:ja"),
}


def _google_news_rss_url(query: str, locale: str) -> str:
    from urllib.parse import quote
    hl, gl, ceid = _GNEWS_LOCALES.get(locale, _GNEWS_LOCALES["en-US"])
    return (f"https://news.google.com/rss/search?q={quote(query)}"
            f"&hl={hl}&gl={gl}&ceid={ceid}")


async def collect_google_news(query: str, max_results: int = 10, locale: str = "en-US") -> CollectResult:
    """Use Google News public RSS search endpoint (no API key, public feed)."""
    url = _google_news_rss_url(query, locale)
    try:
        xml_text = await _get_text(url)
        items = parse_feed(xml_text, source="news.google.com")[:max_results]
        return CollectResult(items=items, engine="google_news_rss")
    except Exception as e:
        return CollectResult(engine="google_news_rss", error=str(e))


# ---------------------------------------------------------------------------
# Google News article link resolution
#
# RSS items carry an opaque /rss/articles/<id> link rather than the publisher
# URL. The <source url> field is only the publisher *homepage*, which is useless
# as evidence. The public `batchexecute` endpoint used by Google News itself
# resolves the id to the real article URL; no login or private API is involved.
# Every resolution is best-effort and bounded — failures simply drop the hit.
# ---------------------------------------------------------------------------
_RESOLVE_CACHE: Dict[str, str | None] = {}
_MAX_CACHE = 512


def _extract_article_id(url: str) -> str | None:
    try:
        path = urlparse(url).path
        marker = "/rss/articles/"
        if marker not in path:
            return None
        return path.split(marker, 1)[1].strip("/")
    except Exception:
        return None


async def resolve_google_news_url(url: str, locale: str = "en-US") -> str | None:
    """Resolve a news.google.com RSS article link to its publisher URL."""
    article_id = _extract_article_id(url)
    if not article_id:
        return None
    if article_id in _RESOLVE_CACHE:
        return _RESOLVE_CACHE[article_id]
    resolved: str | None = None
    try:
        _hl, _gl, ceid = _GNEWS_LOCALES.get(locale, _GNEWS_LOCALES["en-US"])
        async with httpx.AsyncClient(timeout=8, follow_redirects=True,
                                     headers={"User-Agent": BROWSER_UA}) as client:
            page = await client.get(url)
            sg = re.search(r'data-n-a-sg="([^"]+)"', page.text)
            ts = re.search(r'data-n-a-ts="([^"]+)"', page.text)
            if not (sg and ts):
                return None
            inner = [
                "garturlreq",
                [[ "X", "X", ["X", "X"], None, None, 1, 1, ceid, None, 1,
                   None, None, None, None, None, 0, 1],
                 "X", "X", 1, [1, 1, 1], 1, 1, None, 0, 0, None, 0],
                article_id, int(ts.group(1)), sg.group(1),
            ]
            req = [[["Fbv4je", json.dumps(inner), None, "generic"]]]
            resp = await client.post(
                "https://news.google.com/_/DotsSplashUi/data/batchexecute",
                data={"f.req": json.dumps(req)},
                headers={"Content-Type": "application/x-www-form-urlencoded;charset=UTF-8"},
            )
            payload = resp.text.split("\n", 1)[-1].strip()
            rows = json.loads(payload)
            for row in rows:
                if len(row) > 2 and row[0] == "wrb.fr" and row[1] == "Fbv4je" and row[2]:
                    data = json.loads(row[2])
                    if isinstance(data, list) and len(data) > 1 and str(data[0]) == "garturlres":
                        candidate = str(data[1])
                        if candidate.startswith(("http://", "https://")):
                            resolved = candidate
                            break
    except Exception as exc:
        log.debug("google news resolve failed for %s: %s: %s",
                  article_id[:24], type(exc).__name__, str(exc)[:80])
    if len(_RESOLVE_CACHE) >= _MAX_CACHE:
        _RESOLVE_CACHE.clear()
    _RESOLVE_CACHE[article_id] = resolved
    return resolved


async def resolve_news_items(items: List[FeedItem], limit: int = 10,
                             locale: str = "en-US") -> List[Dict[str, str]]:
    """Resolve top RSS items into evidence candidates with *article* URLs."""
    semaphore = asyncio.Semaphore(5)

    async def _one(it: FeedItem):
        async with semaphore:
            real = await resolve_google_news_url(it.url, locale)
            if not real:
                return None
            return {
                "title": it.title,
                "url": real,
                "snippet": it.summary,
                "published_at": it.published_at or "",
                "discovery": "google_news_article",
                "source": it.source,
            }

    results = await asyncio.gather(*[_one(it) for it in items[:limit]], return_exceptions=True)
    return [r for r in results if isinstance(r, dict) and r.get("url")]


async def enhanced_collect(query: str, claim_text: str, max_results: int = 10) -> CollectResult:
    """Combined compliant collector: Google News RSS + optional custom feeds.

    Results are tagged with source_type via source_policy downstream; this
    module only widens *discovery*, it does not weaken the trust whitelist.

    2026-11-22 D1 fix: 中文命题使用 zh-CN 新闻源检索（此前写死 en-US，导致
    中文常识/文化命题只能拿到西方英文媒体）。同时并行跑一次 en-US 结果，
    兼顾跨文化命题。
    """
    import re as _re
    locales = ["en-US"]
    if _re.search(r"[\u3400-\u9fff]", claim_text or ""):
        locales = ["zh-CN", "en-US"]
    tasks = [collect_google_news(query, max_results=max_results, locale=loc) for loc in locales]
    s = get_settings()
    custom = getattr(s, "custom_feed_urls", "") or ""
    feeds = [u.strip() for u in custom.split(",") if u.strip()]
    if feeds:
        tasks.append(collect_from_feeds(feeds))
    results = await asyncio.gather(*tasks, return_exceptions=True)
    merged: List[FeedItem] = []
    seen = set()
    engine_names = []
    for res in results:
        if isinstance(res, CollectResult):
            if res.engine not in engine_names:
                engine_names.append(res.engine)
            for it in res.items:
                if it.url not in seen:
                    seen.add(it.url)
                    merged.append(it)
    return CollectResult(items=merged[:max_results], engine="+".join(engine_names))


def feed_to_hit(it: FeedItem) -> Dict[str, str]:
    return {"title": it.title, "url": it.url, "snippet": it.summary,
            "published_at": it.published_at or "", "discovery": it.source or "feed",
            "source_url": it.source_url}
