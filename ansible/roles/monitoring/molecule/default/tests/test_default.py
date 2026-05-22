import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

ELASTIC_AGENT_VERSION = "8.15.3"


def test_elastic_agent_downloaded(host):
    tarball = f"/tmp/elastic-agent-{ELASTIC_AGENT_VERSION}-linux-x86_64.tar.gz"
    assert host.file(tarball).exists


def test_elastic_agent_extracted(host):
    extracted = f"/opt/elastic-agent-{ELASTIC_AGENT_VERSION}-linux-x86_64"
    assert host.file(extracted).is_directory


def test_elastic_agent_binary_present(host):
    binary = f"/opt/elastic-agent-{ELASTIC_AGENT_VERSION}-linux-x86_64/elastic-agent"
    assert host.file(binary).exists
