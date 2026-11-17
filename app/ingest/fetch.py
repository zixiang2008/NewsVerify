from __future__ import annotations

import hashlib
from dataclasses import dataclass

import httpx

from app.core.security import MAX_DOWNLOAD_BYTES, MAX_REDIRECTS, validate_url


@dataclass
class FetchResult:
    url: str
    final_url: str
    status_code: int
    content_type: str
    text: str
    content_hash: str
    error: str | None = None


async def fetch_url(url: str) -> FetchResult:
    try:
        validate_url(url)
    except Exception as e:
        return FetchResult(url=url, final_url=url, status_code=0, content_type="", text="", content_hash="", error=str(e))

    headers = {
        "User-Agent": "NewsVerifyBot/0.1 (+https://github.com; fact-check research)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            headers=headers,
        ) as client:
            # Validate each redirect target.
            resp = await client.get(url)
            # Re-validate final URL.
            validate_url(str(resp.url))
            content = resp.content
            if len(content) > MAX_DOWNLOAD_BYTES:
                return FetchResult(url=url, final_url=str(resp.url), status_code=resp.status_code,
                                   content_type=resp.headers.get("content-type", ""),
                                   text="", content_hash="", error="content too large")
            ctype = resp.headers.get("content-type", "")
            text = ""
            if "text" in ctype or "html" in ctype or "xml" in ctype or "json" in ctype:
                text = resp.text
            h = hashlib.sha256(content).hexdigest()
            return FetchResult(url=url, final_url=str(resp.url), status_code=resp.status_code,
                               content_type=ctype, text=text, content_hash=h)
    except Exception as e:
        return FetchResult(url=url, final_url=url, status_code=0, content_type="", text="", content_hash="", error=str(e))