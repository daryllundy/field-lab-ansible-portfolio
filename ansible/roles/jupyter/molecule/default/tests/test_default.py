import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_jupyterlab_installed(host):
    """Property 18: JupyterLab installed."""
    # Check if jupyter command works
    # We might need to check path or install location
    # pip install usually puts it in /usr/local/bin or /usr/bin
    assert host.run("which jupyter").rc == 0

def test_jupyterlab_service(host):
    """Property 19: JupyterLab service configuration."""
    assert host.file("/etc/systemd/system/jupyterlab.service").exists
    assert host.file("/etc/systemd/system/jupyterlab.service").contains("ExecStart=/usr/bin/jupyter lab")
