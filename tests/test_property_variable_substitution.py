import pytest
import yaml
from hypothesis import given, strategies as st, settings, HealthCheck


@st.composite
def valid_url(draw):
    protocol = draw(st.sampled_from(["http", "https"]))
    hostname_parts = draw(st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=10),
        min_size=1, max_size=3,
    ))
    hostname = ".".join(hostname_parts)
    port = draw(st.one_of(st.none(), st.integers(min_value=1024, max_value=65535)))
    if port:
        return f"{protocol}://{hostname}:{port}"
    return f"{protocol}://{hostname}"


@st.composite
def valid_path(draw):
    components = draw(st.lists(
        st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=10),
        min_size=1, max_size=5,
    ))
    return "/" + "/".join(components)


@st.composite
def valid_password(draw):
    return draw(st.text(
        alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
        min_size=8, max_size=32,
    ))


@st.composite
def valid_timezone(draw):
    return draw(st.sampled_from([
        "UTC", "America/New_York", "America/Los_Angeles", "America/Chicago",
        "Europe/London", "Europe/Paris", "Asia/Tokyo", "Australia/Sydney",
    ]))


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
def global_variables(draw):
    num_keys = draw(st.integers(min_value=1, max_value=3))
    return {
        "timezone": draw(valid_timezone()),
        "admin_user": draw(valid_username()),
        "ssh_public_keys": [draw(valid_ssh_key()) for _ in range(num_keys)],
        "packages_common": draw(valid_package_list()),
        "unattended_upgrades": draw(st.booleans()),
    }


@st.composite
def workstation_variables(draw):
    return {
        "vscode_server": draw(st.booleans()),
        "jupyter_install": draw(st.booleans()),
    }


@st.composite
def runner_variables(draw):
    return {
        "gitlab_runner_registration_token": draw(st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-",
            min_size=20, max_size=40,
        )),
        "gitlab_runner_executor": draw(st.sampled_from(["docker", "shell", "kubernetes"])),
    }


@st.composite
def infrastructure_variables(draw):
    return {
        "gitlab_external_url": draw(valid_url()),
        "nfs_export_path": draw(valid_path()),
        "restic_repo": draw(valid_path()),
        "restic_password": draw(valid_password()),
    }


def assert_round_trip(vars_data, required_fields):
    reloaded = yaml.safe_load(yaml.dump(vars_data, default_flow_style=False))
    for field in required_fields:
        assert field in reloaded, f"Field {field} missing after round-trip"
        assert reloaded[field] == vars_data[field]
    return reloaded


@pytest.mark.property
@given(vars_data=global_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_global_variables_substitution(vars_data):
    reloaded = assert_round_trip(
        vars_data,
        ["timezone", "admin_user", "ssh_public_keys", "packages_common", "unattended_upgrades"],
    )
    assert isinstance(reloaded["timezone"], str)
    assert isinstance(reloaded["admin_user"], str)
    assert isinstance(reloaded["ssh_public_keys"], list)
    assert isinstance(reloaded["packages_common"], list)
    assert isinstance(reloaded["unattended_upgrades"], bool)


@pytest.mark.property
@given(vars_data=workstation_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_workstation_variables_substitution(vars_data):
    reloaded = assert_round_trip(vars_data, ["vscode_server", "jupyter_install"])
    assert isinstance(reloaded["vscode_server"], bool)
    assert isinstance(reloaded["jupyter_install"], bool)


@pytest.mark.property
@given(vars_data=runner_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_runner_variables_substitution(vars_data):
    reloaded = assert_round_trip(vars_data, ["gitlab_runner_registration_token", "gitlab_runner_executor"])
    assert isinstance(reloaded["gitlab_runner_registration_token"], str)
    assert reloaded["gitlab_runner_executor"] in ["docker", "shell", "kubernetes"]


@pytest.mark.property
@given(vars_data=infrastructure_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_infrastructure_variables_substitution(vars_data):
    reloaded = assert_round_trip(
        vars_data,
        ["gitlab_external_url", "nfs_export_path", "restic_repo", "restic_password"],
    )
    assert reloaded["gitlab_external_url"].startswith(("http://", "https://"))
    assert reloaded["nfs_export_path"].startswith("/")
    assert reloaded["restic_repo"].startswith("/")


@pytest.mark.property
@given(url1=valid_url(), url2=valid_url())
@settings(max_examples=100)
def test_url_substitution_consistency(url1, url2):
    yaml1 = yaml.dump({"gitlab_external_url": url1})
    yaml2 = yaml.dump({"gitlab_external_url": url2})
    assert yaml.safe_load(yaml2)["gitlab_external_url"] == url2
    if url1 == url2:
        assert yaml1 == yaml2


@pytest.mark.property
@given(path1=valid_path(), path2=valid_path())
@settings(max_examples=100)
def test_path_substitution_consistency(path1, path2):
    yaml1 = yaml.dump({"nfs_export_path": path1})
    yaml2 = yaml.dump({"nfs_export_path": path2})
    final = yaml.safe_load(yaml2)
    assert final["nfs_export_path"] == path2
    assert final["nfs_export_path"].startswith("/")
    if path1 == path2:
        assert yaml1 == yaml2
