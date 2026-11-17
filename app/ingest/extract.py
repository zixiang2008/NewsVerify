from __future__ import annotations

from typing import Tuple

try:
    import trafilatura
except Exception:  # pragma: no cover
    trafilatura = None

from bs4 import BeautifulSoup


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