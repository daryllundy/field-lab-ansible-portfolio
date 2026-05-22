import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_vscode_server_installed(host):
    assert host.file("/usr/bin/code-server").exists


def test_vscode_server_service(host):
    service = host.service("code-server@molecule")
    assert service.is_enabled
