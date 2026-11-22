from __future__ import annotations

from typing import Tuple

try:
    import trafilatura
except Exception:  # pragma: no cover
    trafilatura = None

from bs4 import BeautifulSoup


def extract_published_at(html: str) -> str | None:
    """Best-effort publication date from common meta tags (D5 fix).

    Returns an ISO-8601 string when a trustworthy meta field is present,
    otherwise None. Search snippets rarely carry a date, so reading the page
    metadata is the only way to populate Source.published_at for web hits.
    """
    if not html:
        return None
    try:
        soup = BeautifulSoup(html[:200000], "lxml")
        # Order matters: article timestamps before generic ones.
        selectors = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"name": "date"}),
            ("meta", {"name": "datePublished"}),
            ("meta", {"property": "og:article:published_time"}),
            ("meta", {"itemprop": "datePublished"}),
            ("time", {"datetime": True}),
        ]
        for tag, attrs in selectors:
            el = soup.find(tag, attrs)
            if not el:
                continue
            val = el.get("content") or el.get("datetime") or ""
            val = val.strip()
            if not val:
                continue
            import datetime as _dt
            # Normalise ISO / RFC-1123 / epoch-ish strings defensively.
            try:
                if val.isdigit() and len(val) >= 10:
                    d = _dt.datetime.fromtimestamp(int(val[:10]), tz=_dt.timezone.utc)
                    return d.isoformat()
                d = _dt.datetime.fromisoformat(val.replace("Z", "+00:00"))
                if d.tzinfo is None:
                    d = d.replace(tzinfo=_dt.timezone.utc)
                return d.isoformat()
            except Exception:
                try:
                    import email.utils as _eu
                    d = _eu.parsedate_to_datetime(val)
                    if d and d.tzinfo is None:
                        d = d.replace(tzinfo=_dt.timezone.utc)
                    return d.isoformat() if d else None
                except Exception:
                    continue
    except Exception:
        return None
    return None


def extract_text(html: str, url: str) -> Tuple[str, str]:
    """Return (title, text)."""
    title = ""
    text = ""
    if trafilatura is not None:
        try:
            text = trafilatura.extract(html, url=url, include_comments=False, include_tables=False) or ""
            meta = trafilatura.extract_metadata(html, default_url=url)
            if meta and meta.title:
                title = meta.title
        except Exception:
            text = ""
    if not text:
        try:
            soup = BeautifulSoup(html, "lxml")
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
            for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                tag.decompose()
            text = " ".join(soup.get_text(" ").split())
        except Exception:
            text = ""
    # Trim
    if len(text) > 12000:
        text = text[:12000] + " …[truncated]"
    return title, text