import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_vscode_server_installed(host):
    """Property 16: VS Code Server installed."""
    assert host.file("/usr/bin/code-server").exists

def test_vscode_server_service(host):
    """Property 17: VS Code Server service enabled."""
    service = host.service("code-server@molecule")
    assert service.is_enabled
    # Note: Service might not be running in Docker without systemd init
