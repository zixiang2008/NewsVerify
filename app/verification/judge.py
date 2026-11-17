from __future__ import annotations

import json
from typing import List, Dict, Any

from app.core.config import get_settings
from app.verification.llm import LLMClient

SYSTEM = """You are a fact-check judge. You receive a claim and a set of evidence items (title, url, snippet, stance hint).
You must:
- Determine label: supported / refuted / mixed / insufficient_evidence / outdated / not_checkable.
- Base verdict ONLY on provided evidence. Do not invent facts.
- "insufficient_evidence" when evidence is weak/missing; never claim supported without evidence.
- "outdated" when evidence shows the claim was true in the past but not now.
- Consider source independence: repeated copies of one source do not count as multiple independent evidence.
- Write strongest counter_argument before committing.
- List evidence_gaps.
Return JSON: {"label":..., "confidence":0.0-1.0, "rationale":"...", "counter_argument":"...", "evidence_gaps":["..."], "cited_urls":["..."]}."""


async def judge_claim(claim_text: str, evidence_items: List[Dict[str, Any]]) -> Dict[str, Any]:
    llm = LLMClient()
    settings = get_settings()
    ev_text = json.dumps(evidence_items[:20], ensure_ascii=False, indent=2)
    user = f"Claim:\n{claim_text}\n\nEvidence:\n{ev_text}\n\nJudge now."
    data = await llm.chat_json(SYSTEM, user, model=settings.llm_judge_model)
    label = data.get("label", "insufficient_evidence")
    if label not in {"supported", "refuted", "mixed", "insufficient_evidence", "outdated", "not_checkable"}:
        label = "insufficient_evidence"
    return {
        "label": label,
        "confidence": float(data.get("confidence", 0.0) or 0.0),
        "rationale": data.get("rationale", ""),
        "counter_argument": data.get("counter_argument", ""),
        "evidence_gaps": data.get("evidence_gaps", []) or [],
        "cited_urls": data.get("cited_urls", []) or [],
    }