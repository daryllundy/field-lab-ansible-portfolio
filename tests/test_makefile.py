import pytest
from pathlib import Path

@pytest.fixture
def makefile_content():
    makefile_path = Path(__file__).parent.parent / "Makefile"
    with open(makefile_path) as f:
        return f.read()

def get_targets(makefile_content):
    targets = []
    for line in makefile_content.splitlines():
        if line.startswith(".PHONY:"):
            targets.extend(line.split(":")[1].strip().split())
    return targets

def test_makefile_setup_target(makefile_content):
    assert "setup" in get_targets(makefile_content)

def test_makefile_lint_target(makefile_content):
    assert "lint" in get_targets(makefile_content)

def test_makefile_test_target(makefile_content):
    assert "test" in get_targets(makefile_content)

def test_makefile_deployment_targets(makefile_content):
    targets = get_targets(makefile_content)
    for target in ["bootstrap", "harden", "dev-tools", "network", "storage", "monitoring", "dr-test"]:
        assert target in targets, f"Makefile missing '{target}' target"

def test_makefile_ping_target(makefile_content):
    assert "ping" in get_targets(makefile_content)
