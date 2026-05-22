import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_gitlab_runner_installed(host):
    assert host.package("gitlab-runner").is_installed


def test_runner_registration(host):
    assert host.file("/etc/gitlab-runner/config.toml").exists


def test_runner_executor(host):
    config = host.file("/etc/gitlab-runner/config.toml")
    assert config.contains('executor = "docker"')


def test_runner_description(host):
    config = host.file("/etc/gitlab-runner/config.toml")
    assert config.contains('name = "instance-runner"')
