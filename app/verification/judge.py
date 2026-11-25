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
- Confidence measures certainty in the LABEL, but must stay low (<=0.35) for "insufficient_evidence" and "not_checkable" — you cannot be highly certain about a claim you cannot verify. High confidence is reserved for supported/refuted with strong independent evidence.
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
    confidence = float(data.get("confidence", 0.0) or 0.0)
    confidence = max(0.0, min(1.0, confidence))
    # An "insufficient evidence" verdict is by definition low-certainty: the
    # model cannot be 1.0 sure about a claim it just said it cannot verify.
    # Cap it so the UI/API never surfaces the contradictory
    # insufficient_evidence + confidence 1.0 combination seen on 2026-11-21.
    if label == "insufficient_evidence":
        confidence = min(confidence, 0.35)
    elif label == "not_checkable":
        confidence = min(confidence, 0.5)

    # 2026-11-24 判定守卫：supported / refuted / mixed / outdated 必须至少有
    # 一条可打开的来源 URL。历史数据里曾出现"已核实但证据为空"的记录；模型
    # 也可能在证据被拦截页污染后给出高置信结论。这里在写库前强制降级。
    openable = [
        str(e.get("url", ""))
        for e in evidence_items
        if isinstance(e, dict)
        and str(e.get("url", "")).startswith(("http://", "https://"))
        and not e.get("fetch_error")
    ]
    verdict_labels = {"supported", "refuted", "mixed", "outdated"}
    gaps = list(data.get("evidence_gaps", []) or [])
    if label in verdict_labels and not openable:
        gaps.append("判定守卫：没有可打开的证据 URL，结论自动降级为 insufficient_evidence")
        return {
            "label": "insufficient_evidence",
            "confidence": min(confidence, 0.35),
            "rationale": (data.get("rationale", "") or "") +
                         " [判定守卫：原结论缺少可打开来源，已降级]",
            "counter_argument": data.get("counter_argument", ""),
            "evidence_gaps": gaps,
            "cited_urls": [],
        }
    # 引用的 URL 必须来自本次证据池，杜绝"引用了不存在的来源"。
    allowed = set(openable)
    cited = [u for u in (data.get("cited_urls", []) or []) if u in allowed] if openable else []
    return {
        "label": label,
        "confidence": confidence,
        "rationale": data.get("rationale", ""),
        "counter_argument": data.get("counter_argument", ""),
        "evidence_gaps": gaps,
        "cited_urls": cited,
    }