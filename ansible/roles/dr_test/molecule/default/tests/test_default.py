import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_dr_test_log_created(host):
    assert host.file("/var/log/dr-test.log").exists


def test_dr_test_log_records_pass(host):
    log = host.file("/var/log/dr-test.log").content_string
    assert "DR test PASSED" in log
    assert "backup and restore" in log


def test_restic_repo_initialized(host):
    assert host.file("/srv/backup/repo/config").exists


def test_canary_source_cleaned_up(host):
    assert not host.file("/tmp/dr-test-source").exists
