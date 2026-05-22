import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_gitlab_dependencies(host):
    assert host.package("curl").is_installed
    assert host.package("openssh-server").is_installed
    assert host.package("ca-certificates").is_installed


def test_gitlab_repository(host):
    assert host.file("/etc/apt/sources.list.d/gitlab_gitlab-ce.list").exists


def test_gitlab_ce_installed(host):
    assert host.package("gitlab-ce").is_installed
