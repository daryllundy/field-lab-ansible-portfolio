import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')

def test_dr_test_log_created(host):
    """Property 30: DR test log created."""
    assert host.file("/var/log/dr-test.log").exists

def test_dr_test_log_content(host):
    """Property 31: DR test log content."""
    log = host.file("/var/log/dr-test.log").content_string
    assert "DR test start" in log
    assert "Simulating restore validation..." in log
    assert "DR test end" in log
