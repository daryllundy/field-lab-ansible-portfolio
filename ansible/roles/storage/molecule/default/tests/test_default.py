import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_storage_packages(host):
    assert host.package("nfs-kernel-server").is_installed
    assert host.package("restic").is_installed


def test_nfs_export_directory(host):
    assert host.file("/srv/nfs").is_directory


def test_nfs_exports(host):
    exports = host.file("/etc/exports.d/lab.exports")
    assert exports.exists
    assert exports.contains("/srv/nfs 192.168.0.0/16(rw,sync,no_subtree_check)")


def test_restic_repository(host):
    assert host.file("/srv/backup/repo/config").exists
