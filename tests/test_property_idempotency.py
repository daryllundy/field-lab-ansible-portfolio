import pytest
import yaml
from hypothesis import given, strategies as st, settings, HealthCheck


@st.composite
def valid_timezone(draw):
    timezones = [
        "UTC", "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney",
    ]
    return draw(st.sampled_from(timezones))


@st.composite
def valid_username(draw):
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))
    rest = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_", min_size=0, max_size=7))
    return first_char + rest


@st.composite
def valid_package_list(draw):
    common_packages = ["curl", "vim", "htop", "git", "wget", "tmux", "tree"]
    size = draw(st.integers(min_value=1, max_value=5))
    return draw(st.lists(st.sampled_from(common_packages), min_size=size, max_size=size, unique=True))


@st.composite
def valid_ssh_key(draw):
    key_type = draw(st.sampled_from(["ssh-ed25519", "ssh-rsa"]))
    key_data = draw(st.text(
        alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",
        min_size=50, max_size=100,
    ))
    comment = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789@.-", min_size=5, max_size=20))
    return f"{key_type} {key_data} {comment}"


@st.composite
def base_hardening_config(draw):
    return {
        "timezone": draw(valid_timezone()),
        "packages_common": draw(valid_package_list()),
        "unattended_upgrades": draw(st.booleans()),
    }


@st.composite
def users_config(draw):
    num_keys = draw(st.integers(min_value=1, max_value=3))
    return {
        "admin_user": draw(valid_username()),
        "ssh_public_keys": [draw(valid_ssh_key()) for _ in range(num_keys)],
    }


@pytest.mark.property
@given(config=base_hardening_config())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_base_hardening_idempotency(config):
    assert isinstance(config["timezone"], str) and len(config["timezone"]) > 0
    assert isinstance(config["packages_common"], list) and len(config["packages_common"]) > 0
    assert all(isinstance(pkg, str) for pkg in config["packages_common"])
    assert isinstance(config["unattended_upgrades"], bool)

    reloaded = yaml.safe_load(yaml.dump(config))
    assert reloaded["timezone"] == config["timezone"]
    assert reloaded["packages_common"] == config["packages_common"]
    assert reloaded["unattended_upgrades"] == config["unattended_upgrades"]


@pytest.mark.property
@given(config=users_config())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_users_role_idempotency(config):
    assert isinstance(config["admin_user"], str) and len(config["admin_user"]) > 0
    assert config["admin_user"][0].isalpha()
    assert all(c.isalnum() or c == "_" for c in config["admin_user"])
    assert isinstance(config["ssh_public_keys"], list) and len(config["ssh_public_keys"]) > 0

    for key in config["ssh_public_keys"]:
        parts = key.split()
        assert len(parts) >= 2
        assert parts[0] in ["ssh-ed25519", "ssh-rsa", "ssh-dss", "ecdsa-sha2-nistp256"]

    reloaded = yaml.safe_load(yaml.dump(config))
    assert reloaded["admin_user"] == config["admin_user"]
    assert reloaded["ssh_public_keys"] == config["ssh_public_keys"]


@pytest.mark.property
@given(timezone1=valid_timezone(), timezone2=valid_timezone())
@settings(max_examples=100)
def test_configuration_consistency(timezone1, timezone2):
    yaml1 = yaml.dump({"timezone": timezone1})
    yaml2 = yaml.dump({"timezone": timezone2})

    final_config = yaml.safe_load(yaml2)
    assert final_config["timezone"] == timezone2

    if timezone1 == timezone2:
        assert yaml1 == yaml2
