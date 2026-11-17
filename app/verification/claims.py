from __future__ import annotations

from typing import List, Dict

from app.verification.llm import LLMClient

SYSTEM = """You are a fact-check claim extractor. Given news text (possibly in any language), extract check-worthy atomic factual claims.
Rules:
- Each claim must be a single, verifiable factual statement.
- Preserve original language of the input.
- Do not include opinions, predictions without dates, or unverifiable statements.
- Distinguish the claim from the source's framing.
Return JSON: {"claims": [{"text": "...", "language": "zh/en/...", "checkable": true}], "notes": "..."}.
Limit to the requested max claims. If no checkable claims, return empty list."""


async def extract_claims(text: str, max_claims: int = 8) -> List[Dict[str, str]]:
    llm = LLMClient()
    user = f"Max claims: {max_claims}\n\nText:\n{text[:8000]}"
    data = await llm.chat_json(SYSTEM, user)
    claims = data.get("claims", []) if isinstance(data, dict) else []
    out = []
    for c in claims[:max_claims]:
        if not isinstance(c, dict):
            continue
        t = (c.get("text") or "").strip()
        if not t:
            continue
        lang = (c.get("language") or "unknown")
        lang = lang.split("/")[0].strip()[:8] or "unknown"
        out.append({"text": t, "language": lang, "checkable": bool(c.get("checkable", True))})
    return out