from __future__ import annotations

SYSTEMS = [
    {"key": "newsguard", "name": "NewsGuard", "role": "source long-term credibility", "status": "not_connected", "license": "commercial", "note": "Official rating not integrated; no score fabricated."},
    {"key": "adfontes", "name": "Ad Fontes Media", "role": "reliability & bias", "status": "not_connected", "license": "commercial", "note": "Official rating not integrated."},
    {"key": "allsides", "name": "AllSides", "role": "US political bias comparison", "status": "not_connected", "license": "commercial", "note": "Bias is not truth; applicability limited for non-US."},
    {"key": "reuters_institute", "name": "Reuters Institute", "role": "public trust research (background)", "status": "context_only", "license": "open research", "note": "Country/year-level background, not per-article rating."},
    {"key": "pew", "name": "Pew Research", "role": "platform/audience research (background)", "status": "context_only", "license": "open research", "note": "Background data; record survey date and sample."},
    {"key": "rsf", "name": "Reporters Without Borders", "role": "press freedom environment", "status": "context_only", "license": "open", "note": "Country environment, not per-article truth."},
]


def list_systems():
    return [dict(s) for s in SYSTEMS]