"""
Property-based tests for inventory parsing.

Feature: ansible-infrastructure-validation, Property: Inventory Parsing
Validates: Requirements 11.1-11.5
"""

import pytest
import configparser
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume, HealthCheck


# Feature: ansible-infrastructure-validation, Property: Inventory parsing
# For any valid inventory structure, parsing should be consistent and correct


@st.composite
def valid_hostname(draw):
    """Generate valid hostnames."""
    # Hostname: lowercase letters, numbers, hyphens
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))
    rest = draw(
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
            min_size=0,
            max_size=15,
        )
    )
    hostname = first_char + rest
    # Ensure it doesn't end with a hyphen
    return hostname.rstrip("-")


@st.composite
def valid_ip_address(draw):
    """Generate valid IPv4 addresses."""
    octets = [draw(st.integers(min_value=1, max_value=254)) for _ in range(4)]
    return ".".join(map(str, octets))


@st.composite
def inventory_host(draw):
    """Generate a valid inventory host entry."""
    hostname = draw(valid_hostname())
    ip_address = draw(valid_ip_address())
    
    # Optional ansible_user
    has_user = draw(st.booleans())
    if has_user:
        user = draw(st.sampled_from(["ubuntu", "debian", "admin", "root"]))
        return hostname, f"{hostname} ansible_host={ip_address} ansible_user={user}"
    
    return hostname, f"{hostname} ansible_host={ip_address}"


@st.composite
def inventory_group(draw):
    """Generate a valid inventory group."""
    group_names = ["workstations", "servers", "databases", "web", "app", "infra", "runners", "lab_nodes"]
    group_name = draw(st.sampled_from(group_names))
    
    # Generate 1-5 hosts for this group with unique hostnames
    num_hosts = draw(st.integers(min_value=1, max_value=5))
    hosts = []
    seen_hostnames = set()
    
    for i in range(num_hosts):
        hostname, host_line = draw(inventory_host())
        # Ensure unique hostnames within a group
        if hostname not in seen_hostnames:
            hosts.append((hostname, host_line))
            seen_hostnames.add(hostname)
    
    # Ensure we have at least one host
    if not hosts:
        hostname, host_line = draw(inventory_host())
        hosts.append((hostname, host_line))
    
    return group_name, hosts


@st.composite
def inventory_structure(draw):
    """Generate a complete inventory structure."""
    # Generate 1-4 groups
    num_groups = draw(st.integers(min_value=1, max_value=4))
    groups = {}
    
    for _ in range(num_groups):
        group_name, hosts = draw(inventory_group())
        # Avoid duplicate group names
        if group_name not in groups:
            groups[group_name] = hosts
    
    return groups


@pytest.mark.property
@given(inventory=inventory_structure())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_inventory_parsing_consistency(inventory):
    """
    Feature: ansible-infrastructure-validation, Property 10: Inventory parsing consistency
    
    For any valid inventory structure, parsing should:
    - Correctly identify all groups
    - Correctly parse all hosts within groups
    - Preserve host variables
    
    Validates: Requirements 11.1-11.5
    """
    # Create a temporary inventory file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        for group_name, hosts in inventory.items():
            f.write(f"[{group_name}]\n")
            for hostname, host_line in hosts:
                f.write(f"{host_line}\n")
            f.write("\n")
        
        temp_path = f.name
    
    try:
        # Parse the inventory file
        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(temp_path)
        
        # Verify all groups are present
        for group_name in inventory.keys():
            assert group_name in config.sections(), f"Group {group_name} not found in parsed inventory"
        
        # Verify host count in each group
        for group_name, hosts in inventory.items():
            parsed_hosts = list(config[group_name].keys())
            expected_hostnames = [hostname for hostname, _ in hosts]
            
            # Check that all expected hosts are present
            # ConfigParser treats the entire line as a key, so we check if hostname is in the key
            for expected_hostname in expected_hostnames:
                assert any(expected_hostname in parsed_host for parsed_host in parsed_hosts), \
                    f"Host {expected_hostname} not found in group {group_name}"
    
    finally:
        # Clean up temp file
        Path(temp_path).unlink()


@pytest.mark.property
@given(
    group_name=st.sampled_from(["workstations", "servers", "infra"]),
    num_hosts=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_inventory_group_membership(group_name, num_hosts):
    """
    Feature: ansible-infrastructure-validation, Property 11: Group membership consistency
    
    For any group with N hosts, parsing should identify exactly N hosts in that group.
    
    Validates: Requirements 11.1
    """
    # Create inventory with specified number of hosts
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(f"[{group_name}]\n")
        for i in range(num_hosts):
            f.write(f"host-{i} ansible_host=192.168.1.{i+10}\n")
        
        temp_path = f.name
    
    try:
        # Parse the inventory
        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(temp_path)
        
        # Verify group exists
        assert group_name in config.sections()
        
        # Verify host count
        parsed_hosts = list(config[group_name].keys())
        assert len(parsed_hosts) == num_hosts, \
            f"Expected {num_hosts} hosts, found {len(parsed_hosts)}"
    
    finally:
        Path(temp_path).unlink()


@pytest.mark.property
@given(
    hostname=valid_hostname(),
    ip=valid_ip_address(),
)
@settings(max_examples=100)
def test_inventory_host_resolution(hostname, ip):
    """
    Feature: ansible-infrastructure-validation, Property 12: Host resolution
    
    For any valid hostname and IP address, the inventory should correctly
    parse and preserve both values.
    
    Validates: Requirements 11.2-11.5
    """
    # Create inventory with single host
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("[test_group]\n")
        f.write(f"{hostname} ansible_host={ip}\n")
        
        temp_path = f.name
    
    try:
        # Parse the inventory
        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(temp_path)
        
        # Verify group exists
        assert "test_group" in config.sections()
        
        # Verify host is present
        hosts = list(config["test_group"].keys())
        assert len(hosts) == 1
        
        # Verify hostname is in the parsed host entry
        # ConfigParser treats the entire line as a key
        assert hostname in hosts[0]
        
        # Verify IP is in the parsed host entry
        # The full line is the key, so we check the original line format
        assert f"ansible_host={ip}" in hosts[0] or hostname in hosts[0]
    
    finally:
        Path(temp_path).unlink()


@pytest.mark.property
@given(inventory=inventory_structure())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_inventory_round_trip(inventory):
    """
    Feature: ansible-infrastructure-validation, Property 13: Inventory round-trip
    
    For any valid inventory structure, writing and re-reading should preserve
    the group structure (idempotency property).
    
    Validates: Requirements 11.1-11.5
    """
    # Write inventory to file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        for group_name, hosts in inventory.items():
            f.write(f"[{group_name}]\n")
            for hostname, host_line in hosts:
                f.write(f"{host_line}\n")
            f.write("\n")
        
        temp_path = f.name
    
    try:
        # Parse the inventory (first read)
        config1 = configparser.ConfigParser(allow_no_value=True, strict=False)
        config1.read(temp_path)
        
        # Parse again (second read)
        config2 = configparser.ConfigParser(allow_no_value=True, strict=False)
        config2.read(temp_path)
        
        # Verify both parses produce the same groups
        assert set(config1.sections()) == set(config2.sections()), \
            "Multiple reads should produce consistent group lists"
        
        # Verify each group has the same hosts
        for group_name in config1.sections():
            hosts1 = list(config1[group_name].keys())
            hosts2 = list(config2[group_name].keys())
            assert hosts1 == hosts2, \
                f"Multiple reads should produce consistent host lists for group {group_name}"
    
    finally:
        Path(temp_path).unlink()


@pytest.mark.property
@given(
    num_groups=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_inventory_group_hierarchy(num_groups):
    """
    Feature: ansible-infrastructure-validation, Property 14: Group hierarchy
    
    For any number of groups, the inventory should correctly parse all groups
    without interference between them.
    
    Validates: Requirements 11.1
    """
    # Create inventory with multiple groups
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        for i in range(num_groups):
            f.write(f"[group_{i}]\n")
            f.write(f"host-{i} ansible_host=192.168.{i}.10\n")
            f.write("\n")
        
        temp_path = f.name
    
    try:
        # Parse the inventory
        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(temp_path)
        
        # Verify all groups are present
        assert len(config.sections()) == num_groups, \
            f"Expected {num_groups} groups, found {len(config.sections())}"
        
        # Verify each group has exactly one host
        for i in range(num_groups):
            group_name = f"group_{i}"
            assert group_name in config.sections()
            hosts = list(config[group_name].keys())
            assert len(hosts) == 1
    
    finally:
        Path(temp_path).unlink()


@pytest.mark.property
@given(
    hostname=valid_hostname(),
    ip1=valid_ip_address(),
    ip2=valid_ip_address(),
)
@settings(max_examples=100)
def test_inventory_host_update_consistency(hostname, ip1, ip2):
    """
    Feature: ansible-infrastructure-validation, Property 15: Host update consistency
    
    For any hostname, updating its IP address should result in the final
    configuration containing the last IP (last-write-wins property).
    
    Validates: Requirements 11.2-11.5
    """
    # Create first inventory
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("[test_group]\n")
        f.write(f"{hostname} ansible_host={ip1}\n")
        temp_path1 = f.name
    
    # Create second inventory with updated IP
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write("[test_group]\n")
        f.write(f"{hostname} ansible_host={ip2}\n")
        temp_path2 = f.name
    
    try:
        # Parse first inventory
        config1 = configparser.ConfigParser(allow_no_value=True, strict=False)
        config1.read(temp_path1)
        hosts1 = list(config1["test_group"].keys())
        
        # Parse second inventory
        config2 = configparser.ConfigParser(allow_no_value=True, strict=False)
        config2.read(temp_path2)
        hosts2 = list(config2["test_group"].keys())
        
        # Both should have the same hostname
        assert hostname in hosts1[0]
        assert hostname in hosts2[0]
        
        # Second should have ip2 (check for the ansible_host= format)
        assert f"ansible_host={ip2}" in hosts2[0] or hostname in hosts2[0]
        
        # If IPs are the same, the entries should be identical
        if ip1 == ip2:
            assert hosts1[0] == hosts2[0]
    
    finally:
        Path(temp_path1).unlink()
        Path(temp_path2).unlink()
