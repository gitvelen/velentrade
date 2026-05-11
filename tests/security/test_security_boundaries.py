from velentrade.domain.agents.registry import build_agent_capability_profiles
from velentrade.security.finance import FinanceAccessPolicy, FinanceFieldEncryptor
from velentrade.security.logging import redact_sensitive_text


def test_finance_sensitive_raw_fields_are_encrypted_and_role_gated():
    encryptor = FinanceFieldEncryptor(secret="test-secret")
    ciphertext = encryptor.encrypt("家庭负债 500000")
    assert ciphertext != "家庭负债 500000"
    assert encryptor.decrypt(ciphertext) == "家庭负债 500000"

    policy = FinanceAccessPolicy()
    assert policy.can_read_raw("cfo", "income") is True
    assert policy.can_read_raw("finance_service", "debt") is True
    assert policy.can_read_raw("macro_analyst", "debt") is False
    assert policy.read_decision("macro_analyst", "debt").reason_code == "sensitive_data_restricted"


def test_sensitive_plaintext_is_redacted_from_logs():
    text = "收入 1000000, 负债 500000, token abc"
    redacted = redact_sensitive_text(text)
    assert "1000000" not in redacted
    assert "500000" not in redacted
    assert "收入" in redacted
    assert "[REDACTED]" in redacted


def test_non_cfo_profiles_do_not_have_finance_raw_read_permission():
    profiles = build_agent_capability_profiles()
    for agent_id, profile in profiles.items():
        denied = profile.default_context_policy.denied
        if agent_id not in {"cfo"}:
            assert "finance_sensitive_raw" in denied
