from __future__ import annotations

import logging
import re

SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(token|api[_-]?key|password|secret)\s*[:=]\s*\S+"),
]


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        for pat in SENSITIVE_PATTERNS:
            msg = pat.sub(lambda m: m.group(0).split(m.group(0)[-1] if False else "=")[0] + "=***", msg)
        record.msg = msg
        record.args = ()
        return True


def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    root = logging.getLogger()
    redactor = RedactingFilter()
    for h in root.handlers:
        h.addFilter(redactor)