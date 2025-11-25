import yaml
import pytest
from pathlib import Path

@pytest.fixture
def ci_workflow_content():
    workflow_path = Path(__file__).parent.parent / ".github/workflows/ci.yml"
    with open(workflow_path) as f:
        return yaml.safe_load(f)

def test_github_actions_triggers(ci_workflow_content):
    """Property 47: GitHub Actions trigger events."""
    # PyYAML 1.1 parses 'on' as boolean True
    triggers = ci_workflow_content.get("on") or ci_workflow_content.get(True)
    assert triggers, "Workflow missing 'on' trigger"
    
    if isinstance(triggers, list):
        assert "push" in triggers, "Missing 'push' trigger"
        assert "pull_request" in triggers, "Missing 'pull_request' trigger"
    else:
        assert "push" in triggers, "Missing 'push' trigger"
        assert "pull_request" in triggers, "Missing 'pull_request' trigger"

def test_ci_python_version(ci_workflow_content):
    """Property 48: CI Python version."""
    jobs = ci_workflow_content["jobs"]
    # Check lint job
    lint_steps = jobs["lint"]["steps"]
    python_setup = next((step for step in lint_steps if "actions/setup-python" in step.get("uses", "")), None)
    assert python_setup, "Missing setup-python step in lint job"
    assert python_setup["with"]["python-version"] == "3.11", "Python version mismatch in lint job"

def test_ci_dependencies_installed(ci_workflow_content):
    """Property 49: CI dependencies installed."""
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    install_step = next((step for step in lint_steps if step.get("name") == "Install tools"), None)
    assert install_step, "Missing 'Install tools' step in lint job"
    run_cmd = install_step["run"]
    assert "ansible" in run_cmd, "ansible not installed"
    assert "ansible-lint" in run_cmd, "ansible-lint not installed"
    assert "yamllint" in run_cmd, "yamllint not installed"

def test_ci_ansible_lint_execution(ci_workflow_content):
    """Property 50: CI ansible-lint execution."""
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    lint_step = next((step for step in lint_steps if step.get("name") == "ansible-lint"), None)
    assert lint_step, "Missing 'ansible-lint' step in lint job"
    assert "ansible-lint" in lint_step["run"], "ansible-lint not executed"

def test_ci_yamllint_execution(ci_workflow_content):
    """Property 51: CI yamllint execution."""
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    lint_step = next((step for step in lint_steps if step.get("name") == "yamllint"), None)
    assert lint_step, "Missing 'yamllint' step in lint job"
    assert "yamllint" in lint_step["run"], "yamllint not executed"
