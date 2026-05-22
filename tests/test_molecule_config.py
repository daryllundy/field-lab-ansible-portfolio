import yaml
import pytest
from pathlib import Path

def get_molecule_files():
    root_dir = Path(__file__).parent.parent
    return list(root_dir.glob("ansible/roles/**/molecule/*/molecule.yml"))

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_molecule_docker_driver_configured(molecule_file):
    with open(molecule_file) as f:
        config = yaml.safe_load(f)

    assert "driver" in config, f"Driver not configured in {molecule_file}"
    assert config["driver"]["name"] == "docker", f"Driver is not docker in {molecule_file}"

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_molecule_test_sequence_complete(molecule_file):
    with open(molecule_file) as f:
        config = yaml.safe_load(f)

    required_sequence = [
        "dependency", "cleanup", "destroy", "syntax", "create",
        "prepare", "converge", "idempotence", "side_effect",
        "verify", "cleanup", "destroy",
    ]

    assert "scenario" in config, f"Scenario not configured in {molecule_file}"
    assert "test_sequence" in config["scenario"], f"Test sequence not configured in {molecule_file}"
    assert config["scenario"]["test_sequence"] == required_sequence, f"Test sequence incorrect in {molecule_file}"

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_testinfra_verifier_configured(molecule_file):
    with open(molecule_file) as f:
        config = yaml.safe_load(f)

    assert "verifier" in config, f"Verifier not configured in {molecule_file}"
    assert config["verifier"]["name"] == "testinfra", f"Verifier is not testinfra in {molecule_file}"

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_linting_configured(molecule_file):
    with open(molecule_file) as f:
        config = yaml.safe_load(f)

    assert "lint" in config, f"Linting not configured in {molecule_file}"
    lint_cmd = config["lint"]
    assert "ansible-lint" in lint_cmd, f"ansible-lint not used in {molecule_file}"
    assert "yamllint" in lint_cmd, f"yamllint not used in {molecule_file}"
