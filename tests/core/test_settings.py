from velentrade.core.settings import Settings


def test_settings_capture_single_owner_runtime_defaults():
    settings = Settings()
    assert settings.env == "test"
    assert settings.single_owner is True
    assert settings.database_url_env == "VELENTRADE_DATABASE_URL"
    assert settings.redis_url_env == "VELENTRADE_REDIS_URL"
    assert settings.agent_runner_url_env == "VELENTRADE_AGENT_RUNNER_URL"
