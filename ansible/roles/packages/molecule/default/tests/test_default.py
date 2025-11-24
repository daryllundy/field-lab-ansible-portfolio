import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_apt_update(host):
    # Hard to verify apt update directly without installing something or checking timestamps
    # But if the role ran successfully, apt update should have succeeded.
    # We can check if /var/lib/apt/lists is populated
    assert host.file("/var/lib/apt/lists").is_directory
