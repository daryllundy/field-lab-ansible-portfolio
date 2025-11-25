import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_user_exists(host):
    """Property 6: Admin user creation."""
    user = host.user("testadmin")
    assert user.exists
    assert user.shell == "/bin/bash"
    assert "sudo" in user.groups


def test_ssh_key_authorized(host):
    """Property 7: SSH key authorization."""
    # Check if authorized_keys file exists and contains the key
    # The key content depends on what's passed in the molecule converge.yml or defaults
    # We can just check if the file exists and is not empty for now, or check for a specific comment if known.
    user = host.user("testadmin")
    authorized_keys = host.file(f"/home/{user.name}/.ssh/authorized_keys")
    assert authorized_keys.exists
    assert authorized_keys.user == user.name
    assert authorized_keys.group == user.name
    assert authorized_keys.mode == 0o600
    # Assuming a key was added, it should have content
    assert authorized_keys.content_string.strip() != ""
