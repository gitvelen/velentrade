from velentrade.model_gateway.profiles import build_model_profiles, route_model_profile


def test_fake_test_model_profile_is_active_and_never_live_llm():
    profiles = build_model_profiles()
    fake = profiles["fake_test"]
    assert fake.purpose == "fake_test"
    assert fake.status == "active"
    assert fake.provider_profile_id == "deterministic_local"
    assert fake.model_name == "fake-test-deterministic"
    assert route_model_profile("fake_test").model_name == "fake-test-deterministic"
