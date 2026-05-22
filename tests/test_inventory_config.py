import configparser
import yaml
import pytest
from pathlib import Path

@pytest.fixture
def inventory_file():
    return Path(__file__).parent.parent / "inventories/lab.ini"

@pytest.fixture
def group_vars_dir():
    return Path(__file__).parent.parent / "group_vars"

def test_inventory_groups_defined(inventory_file):
    config = configparser.ConfigParser(allow_no_value=True)
    config.read(inventory_file)

    required_groups = ["workstations", "lab_nodes", "runners", "infra"]
    for group in required_groups:
        assert group in config.sections(), f"Group {group} not defined in inventory"

def test_global_variables_defined(group_vars_dir):
    vars_file = group_vars_dir / "all.yml"
    with open(vars_file) as f:
        vars_data = yaml.safe_load(f)

    required_vars = ["timezone", "admin_user", "ssh_public_keys", "packages_common", "unattended_upgrades"]
    for var in required_vars:
        assert var in vars_data, f"Variable {var} not defined in all.yml"

def test_workstation_variables_defined(group_vars_dir):
    vars_file = group_vars_dir / "workstations.yml"
    with open(vars_file) as f:
        vars_data = yaml.safe_load(f)

    for var in ["vscode_server", "jupyter_install"]:
        assert var in vars_data, f"Variable {var} not defined in workstations.yml"

def test_runner_variables_defined(group_vars_dir):
    vars_file = group_vars_dir / "runners/vars.yml"
    with open(vars_file) as f:
        vars_data = yaml.safe_load(f)

    for var in ["gitlab_runner_registration_token", "gitlab_runner_executor"]:
        assert var in vars_data, f"Variable {var} not defined in runners/vars.yml"

def test_infrastructure_variables_defined(group_vars_dir):
    vars_file = group_vars_dir / "infra/vars.yml"
    with open(vars_file) as f:
        vars_data = yaml.safe_load(f)

    for var in ["gitlab_external_url", "nfs_export_path", "restic_repo", "restic_password"]:
        assert var in vars_data, f"Variable {var} not defined in infra/vars.yml"
