import yaml
import pytest
from pathlib import Path

@pytest.fixture
def ci_workflow_content():
    workflow_path = Path(__file__).parent.parent / ".github/workflows/ci.yml"
    with open(workflow_path) as f:
        return yaml.safe_load(f)

def test_github_actions_triggers(ci_workflow_content):
    # PyYAML 1.1 parses 'on' as boolean True
    triggers = ci_workflow_content.get("on") or ci_workflow_content.get(True)
    assert triggers, "Workflow missing 'on' trigger"

    if isinstance(triggers, list):
        assert "push" in triggers
        assert "pull_request" in triggers
    else:
        assert "push" in triggers
        assert "pull_request" in triggers

def test_ci_python_version(ci_workflow_content):
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    python_setup = next((step for step in lint_steps if "actions/setup-python" in step.get("uses", "")), None)
    assert python_setup, "Missing setup-python step in lint job"
    assert python_setup["with"]["python-version"] == "3.11"

def test_ci_dependencies_installed(ci_workflow_content):
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    install_step = next((step for step in lint_steps if step.get("name") == "Install tools"), None)
    assert install_step, "Missing 'Install tools' step"
    run_cmd = install_step["run"]
    assert "ansible" in run_cmd
    assert "ansible-lint" in run_cmd
    assert "yamllint" in run_cmd

def test_ci_ansible_lint_execution(ci_workflow_content):
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    lint_step = next((step for step in lint_steps if step.get("name") == "ansible-lint"), None)
    assert lint_step, "Missing 'ansible-lint' step"
    assert "ansible-lint" in lint_step["run"]

def test_ci_yamllint_execution(ci_workflow_content):
    jobs = ci_workflow_content["jobs"]
    lint_steps = jobs["lint"]["steps"]
    lint_step = next((step for step in lint_steps if step.get("name") == "yamllint"), None)
    assert lint_step, "Missing 'yamllint' step"
    assert "yamllint" in lint_step["run"]
