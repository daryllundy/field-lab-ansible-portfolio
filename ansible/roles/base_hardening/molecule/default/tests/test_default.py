import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_passwd_file(host):
    passwd = host.file("/etc/passwd")
    assert passwd.contains("root")
    assert passwd.user == "root"
    assert passwd.group == "root"


def test_sshd_config(host):
    sshd_config = host.file("/etc/ssh/sshd_config")
    assert sshd_config.exists
    assert sshd_config.contains("PasswordAuthentication no")


def test_packages(host):
    assert host.package("curl").is_installed
    assert host.package("git").is_installed
