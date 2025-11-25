import os
import yaml
import pytest
from pathlib import Path

def get_molecule_files():
    """Find all molecule.yml files in the project."""
    root_dir = Path(__file__).parent.parent
    return list(root_dir.glob("ansible/roles/**/molecule/*/molecule.yml"))

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_molecule_docker_driver_configured(molecule_file):
    """Property 32: Molecule Docker driver configured."""
    with open(molecule_file) as f:
        config = yaml.safe_load(f)
    
    assert "driver" in config, f"Driver not configured in {molecule_file}"
    assert config["driver"]["name"] == "docker", f"Driver is not docker in {molecule_file}"

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_molecule_test_sequence_complete(molecule_file):
    """Property 33: Molecule test sequence complete."""
    with open(molecule_file) as f:
        config = yaml.safe_load(f)
    
    required_sequence = [
        "dependency",
        "cleanup",
        "destroy",
        "syntax",
        "create",
        "prepare",
        "converge",
        "idempotence",
        "side_effect",
        "verify",
        "cleanup",
        "destroy",
    ]
    
    assert "scenario" in config, f"Scenario not configured in {molecule_file}"
    assert "test_sequence" in config["scenario"], f"Test sequence not configured in {molecule_file}"
    
    # We check if the configured sequence contains the required steps in order, 
    # or if it exactly matches. The requirement says "complete", usually implying standard full sequence.
    # Let's check for exact match or at least presence of critical steps.
    # Given the file content I saw, it lists them explicitly.
    assert config["scenario"]["test_sequence"] == required_sequence, f"Test sequence is incomplete or incorrect in {molecule_file}"

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_testinfra_verifier_configured(molecule_file):
    """Property 34: Testinfra verifier configured."""
    with open(molecule_file) as f:
        config = yaml.safe_load(f)
    
    assert "verifier" in config, f"Verifier not configured in {molecule_file}"
    assert config["verifier"]["name"] == "testinfra", f"Verifier is not testinfra in {molecule_file}"

@pytest.mark.parametrize("molecule_file", get_molecule_files())
def test_linting_configured(molecule_file):
    """Property 35: Linting configured."""
    with open(molecule_file) as f:
        config = yaml.safe_load(f)
    
    assert "lint" in config, f"Linting not configured in {molecule_file}"
    # Check for ansible-lint and yamllint in the lint command
    lint_cmd = config["lint"]
    assert "ansible-lint" in lint_cmd, f"ansible-lint not used in {molecule_file}"
    assert "yamllint" in lint_cmd, f"yamllint not used in {molecule_file}"
