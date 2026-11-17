from __future__ import annotations

import hashlib
from typing import List, Dict


def evidence_fingerprint(evidence_items: List[Dict]) -> str:
    urls = sorted({e.get("url", "") for e in evidence_items})
    snippets = "".join(e.get("snippet", "")[:100] for e in evidence_items)
    return hashlib.sha256(("|".join(urls) + snippets).encode()).hexdigest()


def verdict_changed(old_label: str, new_label: str) -> bool:
    return old_label != new_label