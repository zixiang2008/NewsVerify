from __future__ import annotations

from app.ingest.fetch import fetch_url
from app.ingest.extract import extract_text


async def handle_youtube(url: str) -> tuple[str, str, str]:
    # Returns (title, text, status_note)
    fr = await fetch_url(url)
    if fr.error:
        return "", "", f"YouTube content unavailable: {fr.error}"
    title, text = extract_text(fr.text, url)
    if not text or len(text) < 200:
        # Try oembed title
        try:
            oembed = await fetch_url(f"https://www.youtube.com/oembed?url={url}&format=json")
            if not oembed.error and oembed.text:
                import json
                data = json.loads(oembed.text)
                title = data.get("title", title)
        except Exception:
            pass
        return title, text, "YouTube: could not retrieve full transcript; only metadata/title available."
    return title, text, "YouTube: page text retrieved (transcript not guaranteed)."


async def handle_x(url: str) -> tuple[str, str, str]:
    fr = await fetch_url(url)
    if fr.error:
        return "", "", f"X/Twitter content unavailable: {fr.error}"
    title, text = extract_text(fr.text, url)
    if not text or len(text) < 100:
        return title, text, "X/Twitter: could not retrieve full post text (login/anti-bot likely)."
    return title, text, "X/Twitter: page text retrieved."


async def handle_image(_url: str) -> tuple[str, str, str]:
    return "", "", "Image OCR not enabled in MVP; please forward text/screenshot text."