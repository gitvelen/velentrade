from __future__ import annotations

import re

SENSITIVE_LABELS = ("收入", "负债", "家庭", "重大支出", "税务")


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for label in SENSITIVE_LABELS:
        redacted = re.sub(rf"({label}\s*)[0-9][0-9,\.]*", rf"\1[REDACTED]", redacted)
    return redacted
