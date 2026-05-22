import os
import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('all')


def test_network_packages(host):
    assert host.package("dnsmasq").is_installed
    assert host.package("unbound").is_installed


def test_dhcp_ranges(host):
    config = host.file("/etc/dnsmasq.d/lab.conf")
    assert config.exists
    assert config.contains("dhcp-range=192.168.50.100,192.168.50.200,12h")
    assert config.contains("dhcp-range=192.168.60.100,192.168.60.200,12h")


def test_dns_domain(host):
    config = host.file("/etc/dnsmasq.d/lab.conf")
    assert config.contains("domain=lab.local")


def test_vlan_configuration(host):
    config = host.file("/etc/netplan/99-lab-vlans.yaml")
    assert config.exists
    assert config.contains("vlan50:")
    assert config.contains("vlan60:")
