import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_user_exists(host):
    user = host.user("testadmin")
    assert user.exists
    assert user.shell == "/bin/bash"
    assert "sudo" in user.groups


def test_ssh_key_authorized(host):
    user = host.user("testadmin")
    authorized_keys = host.file(f"/home/{user.name}/.ssh/authorized_keys")
    assert authorized_keys.exists
    assert authorized_keys.user == user.name
    assert authorized_keys.group == user.name
    assert authorized_keys.mode == 0o600
    assert authorized_keys.content_string.strip() != ""
