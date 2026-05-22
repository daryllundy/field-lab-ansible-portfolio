import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_jupyterlab_installed(host):
    assert host.run("which jupyter").rc == 0


def test_jupyterlab_service(host):
    unit = host.file("/etc/systemd/system/jupyterlab.service")
    assert unit.exists
    assert unit.contains("ExecStart=/usr/bin/jupyter lab")
