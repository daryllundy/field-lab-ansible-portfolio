import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_elastic_agent_downloaded(host):
    """Property 28: Elastic Agent downloaded."""
    assert host.file("/tmp/elastic-agent.tar.gz").exists

def test_elastic_agent_extracted(host):
    """Property 29: Elastic Agent extracted."""
    # The version is hardcoded in the role, so we hardcode it here too
    assert host.file("/opt/elastic-agent-8.15.3-linux-x86_64").is_directory
