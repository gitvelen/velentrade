from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass

from cryptography.fernet import Fernet

from velentrade.domain.common import GuardDecision


class FinanceFieldEncryptor:
    def __init__(self, secret: str) -> None:
        digest = hashlib.sha256(secret.encode("utf-8")).digest()
        self._fernet = Fernet(base64.urlsafe_b64encode(digest))

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode("utf-8")).decode("ascii")

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")


@dataclass(frozen=True)
class FinanceAccessPolicy:
    raw_allowed_roles: frozenset[str] = frozenset({"cfo", "finance_service"})

    def can_read_raw(self, role: str, field: str) -> bool:
        return role in self.raw_allowed_roles and field in {"income", "debt", "family", "major_expense", "tax"}

    def read_decision(self, role: str, field: str) -> GuardDecision:
        if self.can_read_raw(role, field):
            return GuardDecision(True, "OK", "finance_raw_allowed", "Raw finance field access allowed.")
        return GuardDecision(
            False,
            "SENSITIVE_DATA_RESTRICTED",
            "sensitive_data_restricted",
            "Raw finance fields are only available to CFO and finance service.",
            {"role": role, "field": field},
        )
