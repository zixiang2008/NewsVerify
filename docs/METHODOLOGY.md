# Methodology

## Six systems
All six are metadata-only unless licensed data is provided:
- NewsGuard: not_connected (commercial)
- Ad Fontes: not_connected (commercial)
- AllSides: not_connected (commercial)
- Reuters Institute: context_only (country/year background)
- Pew Research: context_only (background)
- RSF: context_only (press freedom environment)

No official scores are fabricated. Self-assessment is labeled "本系统方法学分析".

## Fact-check engine
Independent of the six systems. For each claim returns one of:
supported / refuted / mixed / insufficient_evidence / outdated / not_checkable

Rules:
- Repost chains do not count as independent evidence.
- Allegation != fact; investigation != conviction.
- No evidence != false; unreadable source != insufficient evidence (marked fetch_failed).
- Political/sensitive events keep uncertainty and time bounds.
- No "verified" conclusion without an openable evidence URL.