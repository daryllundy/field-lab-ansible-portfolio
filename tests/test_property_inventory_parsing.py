import pytest
import configparser
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck


@st.composite
def valid_hostname(draw):
    first_char = draw(st.sampled_from("abcdefghijklmnopqrstuvwxyz"))
    rest = draw(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789-", min_size=0, max_size=15))
    return (first_char + rest).rstrip("-")


@st.composite
def valid_ip_address(draw):
    octets = [draw(st.integers(min_value=1, max_value=254)) for _ in range(4)]
    return ".".join(map(str, octets))


@st.composite
def inventory_host(draw):
    hostname = draw(valid_hostname())
    ip_address = draw(valid_ip_address())
    has_user = draw(st.booleans())
    if has_user:
        user = draw(st.sampled_from(["ubuntu", "debian", "admin", "root"]))
        return hostname, f"{hostname} ansible_host={ip_address} ansible_user={user}"
    return hostname, f"{hostname} ansible_host={ip_address}"


@st.composite
def inventory_group(draw):
    group_name = draw(st.sampled_from(
        ["workstations", "servers", "databases", "web", "app", "infra", "runners", "lab_nodes"]
    ))
    num_hosts = draw(st.integers(min_value=1, max_value=5))
    hosts = []
    seen = set()
    for _ in range(num_hosts):
        hostname, host_line = draw(inventory_host())
        if hostname not in seen:
            hosts.append((hostname, host_line))
            seen.add(hostname)
    if not hosts:
        hostname, host_line = draw(inventory_host())
        hosts.append((hostname, host_line))
    return group_name, hosts


@st.composite
def inventory_structure(draw):
    num_groups = draw(st.integers(min_value=1, max_value=4))
    groups = {}
    for _ in range(num_groups):
        group_name, hosts = draw(inventory_group())
        if group_name not in groups:
            groups[group_name] = hosts
    return groups


def write_inventory(groups):
    f = tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False)
    for group_name, hosts in groups.items():
        f.write(f"[{group_name}]\n")
        for _, host_line in hosts:
            f.write(f"{host_line}\n")
        f.write("\n")
    f.close()
    return f.name


@pytest.mark.property
@given(inventory=inventory_structure())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_inventory_parsing_consistency(inventory):
    path = write_inventory(inventory)
    try:
        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(path)
        for group_name, hosts in inventory.items():
            assert group_name in config.sections()
            parsed = list(config[group_name].keys())
            for hostname, _ in hosts:
                assert any(hostname in p for p in parsed)
    finally:
        Path(path).unlink()


@pytest.mark.property
@given(
    group_name=st.sampled_from(["workstations", "servers", "infra"]),
    num_hosts=st.integers(min_value=1, max_value=10),
)
@settings(max_examples=100)
def test_inventory_group_membership(group_name, num_hosts):
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write(f"[{group_name}]\n")
            for i in range(num_hosts):
                f.write(f"host-{i} ansible_host=192.168.1.{i+10}\n")
            path = f.name

        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(path)
        assert group_name in config.sections()
        assert len(list(config[group_name].keys())) == num_hosts
    finally:
        if path:
            Path(path).unlink()


@pytest.mark.property
@given(hostname=valid_hostname(), ip=valid_ip_address())
@settings(max_examples=100)
def test_inventory_host_resolution(hostname, ip):
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            f.write("[test_group]\n")
            f.write(f"{hostname} ansible_host={ip}\n")
            path = f.name

        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(path)
        assert "test_group" in config.sections()
        hosts = list(config["test_group"].keys())
        assert len(hosts) == 1
        assert hostname in hosts[0]
    finally:
        if path:
            Path(path).unlink()


@pytest.mark.property
@given(inventory=inventory_structure())
@settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_inventory_round_trip(inventory):
    path = write_inventory(inventory)
    try:
        config1 = configparser.ConfigParser(allow_no_value=True, strict=False)
        config1.read(path)
        config2 = configparser.ConfigParser(allow_no_value=True, strict=False)
        config2.read(path)
        assert set(config1.sections()) == set(config2.sections())
        for group in config1.sections():
            assert list(config1[group].keys()) == list(config2[group].keys())
    finally:
        Path(path).unlink()


@pytest.mark.property
@given(num_groups=st.integers(min_value=1, max_value=10))
@settings(max_examples=100)
def test_inventory_group_hierarchy(num_groups):
    path = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
            for i in range(num_groups):
                f.write(f"[group_{i}]\n")
                f.write(f"host-{i} ansible_host=192.168.{i}.10\n\n")
            path = f.name

        config = configparser.ConfigParser(allow_no_value=True, strict=False)
        config.read(path)
        assert len(config.sections()) == num_groups
        for i in range(num_groups):
            assert f"group_{i}" in config.sections()
            assert len(list(config[f"group_{i}"].keys())) == 1
    finally:
        if path:
            Path(path).unlink()


@pytest.mark.property
@given(hostname=valid_hostname(), ip1=valid_ip_address(), ip2=valid_ip_address())
@settings(max_examples=100)
def test_inventory_host_update_consistency(hostname, ip1, ip2):
    paths = []
    try:
        for ip in [ip1, ip2]:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
                f.write("[test_group]\n")
                f.write(f"{hostname} ansible_host={ip}\n")
                paths.append(f.name)

        configs = []
        for p in paths:
            c = configparser.ConfigParser(allow_no_value=True, strict=False)
            c.read(p)
            configs.append(list(c["test_group"].keys()))

        assert hostname in configs[0][0]
        assert hostname in configs[1][0]
        if ip1 == ip2:
            assert configs[0][0] == configs[1][0]
    finally:
        for p in paths:
            Path(p).unlink()
