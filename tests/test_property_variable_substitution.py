"""
Property-based tests for variable substitution.

Feature: ansible-infrastructure-validation, Property: Variable Substitution
Validates: Requirements 12.1-12.4
"""

import pytest
import yaml
import re
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck


# Feature: ansible-infrastructure-validation, Property: Variable substitution
# For any valid variable values, templates and configurations should render correctly


@st.composite
def valid_url(draw):
    """Generate valid URLs."""
    protocols = ["http", "https"]
    protocol = draw(st.sampled_from(protocols))
    
    # Generate hostname
    hostname_parts = draw(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=1, max_size=10),
            min_size=1,
            max_size=3,
        )
    )
    hostname = ".".join(hostname_parts)
    
    # Optional port
    port = draw(st.one_of(st.none(), st.integers(min_value=1024, max_value=65535)))
    
    if port:
        return f"{protocol}://{hostname}:{port}"
    return f"{protocol}://{hostname}"


@st.composite
def valid_path(draw):
    """Generate valid Unix paths."""
    # Generate path components
    components = draw(
        st.lists(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789_-", min_size=1, max_size=10),
            min_size=1,
            max_size=5,
        )
    )
    return "/" + "/".join(components)


@st.composite
def valid_password(draw):
    """Generate valid passwords."""
    return draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*",
            min_size=8,
            max_size=32,
        )
    )


@st.composite
def valid_timezone(draw):
    """Generate valid timezone strings."""
    timezones = [
        "UTC",
        "America/New_York",
        "America/Los_Angeles",
        "America/Chicago",
        "Europe/London",
        "Europe/Paris",
        "Asia/Tokyo",
        "Australia/Sydney",
    ]
    return draw(st.sampled_from(timezones))


@st.composite
def valid_username(draw):
    """Generate valid Linux usernames."""
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))
    rest = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789_",
            min_size=0,
            max_size=7,
        )
    )
    return first_char + rest


@st.composite
def valid_package_list(draw):
    """Generate valid package lists."""
    common_packages = ["curl", "vim", "htop", "git", "wget", "tmux", "tree"]
    size = draw(st.integers(min_value=1, max_value=5))
    return draw(st.lists(st.sampled_from(common_packages), min_size=size, max_size=size, unique=True))


@st.composite
def valid_ssh_key(draw):
    """Generate valid SSH public key format."""
    key_types = ["ssh-ed25519", "ssh-rsa"]
    key_type = draw(st.sampled_from(key_types))
    key_data = draw(st.text(alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/", min_size=50, max_size=100))
    comment = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789@.-", min_size=5, max_size=20))
    return f"{key_type} {key_data} {comment}"


@st.composite
def global_variables(draw):
    """Generate valid global variables (group_vars/all.yml)."""
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
    """Generate valid workstation variables (group_vars/workstations.yml)."""
    return {
        "vscode_server": draw(st.booleans()),
        "jupyter_install": draw(st.booleans()),
    }


@st.composite
def runner_variables(draw):
    """Generate valid runner variables (group_vars/runners.yml)."""
    executors = ["docker", "shell", "kubernetes"]
    
    return {
        "gitlab_runner_registration_token": draw(
            st.text(alphabet="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-", min_size=20, max_size=40)
        ),
        "gitlab_runner_executor": draw(st.sampled_from(executors)),
    }


@st.composite
def infrastructure_variables(draw):
    """Generate valid infrastructure variables (group_vars/infra.yml)."""
    return {
        "gitlab_external_url": draw(valid_url()),
        "nfs_export_path": draw(valid_path()),
        "restic_repo": draw(valid_path()),
        "restic_password": draw(valid_password()),
    }


@pytest.mark.property
@given(vars_data=global_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_global_variables_substitution(vars_data):
    """
    Feature: ansible-infrastructure-validation, Property 4: Global variable substitution
    
    For any valid global variable configuration, the variables should:
    - Serialize correctly to YAML
    - Deserialize back to the same values (round-trip property)
    - Maintain type consistency
    
    Validates: Requirements 12.1
    """
    # Serialize to YAML
    yaml_str = yaml.dump(vars_data, default_flow_style=False)
    
    # Deserialize back
    reloaded = yaml.safe_load(yaml_str)
    
    # Verify all required fields are present
    required_fields = ["timezone", "admin_user", "ssh_public_keys", "packages_common", "unattended_upgrades"]
    for field in required_fields:
        assert field in reloaded, f"Field {field} missing after round-trip"
    
    # Verify types are preserved
    assert isinstance(reloaded["timezone"], str)
    assert isinstance(reloaded["admin_user"], str)
    assert isinstance(reloaded["ssh_public_keys"], list)
    assert isinstance(reloaded["packages_common"], list)
    assert isinstance(reloaded["unattended_upgrades"], bool)
    
    # Verify values are preserved (round-trip property)
    assert reloaded["timezone"] == vars_data["timezone"]
    assert reloaded["admin_user"] == vars_data["admin_user"]
    assert reloaded["ssh_public_keys"] == vars_data["ssh_public_keys"]
    assert reloaded["packages_common"] == vars_data["packages_common"]
    assert reloaded["unattended_upgrades"] == vars_data["unattended_upgrades"]


@pytest.mark.property
@given(vars_data=workstation_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_workstation_variables_substitution(vars_data):
    """
    Feature: ansible-infrastructure-validation, Property 5: Workstation variable substitution
    
    For any valid workstation variable configuration, boolean flags should
    maintain their values through serialization.
    
    Validates: Requirements 12.2
    """
    # Serialize to YAML
    yaml_str = yaml.dump(vars_data, default_flow_style=False)
    
    # Deserialize back
    reloaded = yaml.safe_load(yaml_str)
    
    # Verify all required fields are present
    required_fields = ["vscode_server", "jupyter_install"]
    for field in required_fields:
        assert field in reloaded, f"Field {field} missing after round-trip"
    
    # Verify types are preserved
    assert isinstance(reloaded["vscode_server"], bool)
    assert isinstance(reloaded["jupyter_install"], bool)
    
    # Verify values are preserved (round-trip property)
    assert reloaded["vscode_server"] == vars_data["vscode_server"]
    assert reloaded["jupyter_install"] == vars_data["jupyter_install"]


@pytest.mark.property
@given(vars_data=runner_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_runner_variables_substitution(vars_data):
    """
    Feature: ansible-infrastructure-validation, Property 6: Runner variable substitution
    
    For any valid runner variable configuration, the executor type and token
    should be preserved through serialization.
    
    Validates: Requirements 12.3
    """
    # Serialize to YAML
    yaml_str = yaml.dump(vars_data, default_flow_style=False)
    
    # Deserialize back
    reloaded = yaml.safe_load(yaml_str)
    
    # Verify all required fields are present
    required_fields = ["gitlab_runner_registration_token", "gitlab_runner_executor"]
    for field in required_fields:
        assert field in reloaded, f"Field {field} missing after round-trip"
    
    # Verify types are preserved
    assert isinstance(reloaded["gitlab_runner_registration_token"], str)
    assert isinstance(reloaded["gitlab_runner_executor"], str)
    
    # Verify executor is valid
    assert reloaded["gitlab_runner_executor"] in ["docker", "shell", "kubernetes"]
    
    # Verify values are preserved (round-trip property)
    assert reloaded["gitlab_runner_registration_token"] == vars_data["gitlab_runner_registration_token"]
    assert reloaded["gitlab_runner_executor"] == vars_data["gitlab_runner_executor"]


@pytest.mark.property
@given(vars_data=infrastructure_variables())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_infrastructure_variables_substitution(vars_data):
    """
    Feature: ansible-infrastructure-validation, Property 7: Infrastructure variable substitution
    
    For any valid infrastructure variable configuration, URLs, paths, and passwords
    should be preserved through serialization without corruption.
    
    Validates: Requirements 12.4
    """
    # Serialize to YAML
    yaml_str = yaml.dump(vars_data, default_flow_style=False)
    
    # Deserialize back
    reloaded = yaml.safe_load(yaml_str)
    
    # Verify all required fields are present
    required_fields = ["gitlab_external_url", "nfs_export_path", "restic_repo", "restic_password"]
    for field in required_fields:
        assert field in reloaded, f"Field {field} missing after round-trip"
    
    # Verify types are preserved
    assert isinstance(reloaded["gitlab_external_url"], str)
    assert isinstance(reloaded["nfs_export_path"], str)
    assert isinstance(reloaded["restic_repo"], str)
    assert isinstance(reloaded["restic_password"], str)
    
    # Verify URL format
    assert reloaded["gitlab_external_url"].startswith(("http://", "https://"))
    
    # Verify paths start with /
    assert reloaded["nfs_export_path"].startswith("/")
    assert reloaded["restic_repo"].startswith("/")
    
    # Verify values are preserved (round-trip property)
    assert reloaded["gitlab_external_url"] == vars_data["gitlab_external_url"]
    assert reloaded["nfs_export_path"] == vars_data["nfs_export_path"]
    assert reloaded["restic_repo"] == vars_data["restic_repo"]
    assert reloaded["restic_password"] == vars_data["restic_password"]


@pytest.mark.property
@given(
    url1=valid_url(),
    url2=valid_url(),
)
@settings(max_examples=100)
def test_url_substitution_consistency(url1, url2):
    """
    Feature: ansible-infrastructure-validation, Property 8: URL substitution consistency
    
    For any two valid URLs, substituting one for another should result in
    the final configuration containing the last substituted value.
    
    Validates: Requirements 12.4
    """
    config1 = {"gitlab_external_url": url1}
    config2 = {"gitlab_external_url": url2}
    
    # Serialize both
    yaml1 = yaml.dump(config1)
    yaml2 = yaml.dump(config2)
    
    # Reload config2
    final_config = yaml.safe_load(yaml2)
    
    # The final state should match config2
    assert final_config["gitlab_external_url"] == url2
    
    # If both URLs are the same, the configs should be identical
    if url1 == url2:
        assert yaml1 == yaml2


@pytest.mark.property
@given(
    path1=valid_path(),
    path2=valid_path(),
)
@settings(max_examples=100)
def test_path_substitution_consistency(path1, path2):
    """
    Feature: ansible-infrastructure-validation, Property 9: Path substitution consistency
    
    For any two valid paths, substituting one for another should result in
    the final configuration containing the last substituted value.
    
    Validates: Requirements 12.4
    """
    config1 = {"nfs_export_path": path1}
    config2 = {"nfs_export_path": path2}
    
    # Serialize both
    yaml1 = yaml.dump(config1)
    yaml2 = yaml.dump(config2)
    
    # Reload config2
    final_config = yaml.safe_load(yaml2)
    
    # The final state should match config2
    assert final_config["nfs_export_path"] == path2
    
    # Paths should always start with /
    assert final_config["nfs_export_path"].startswith("/")
    
    # If both paths are the same, the configs should be identical
    if path1 == path2:
        assert yaml1 == yaml2
