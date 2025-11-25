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
    """Property 42: Makefile setup target."""
    targets = get_targets(makefile_content)
    assert "setup" in targets, "Makefile missing 'setup' target"

def test_makefile_lint_target(makefile_content):
    """Property 43: Makefile lint target."""
    targets = get_targets(makefile_content)
    assert "lint" in targets, "Makefile missing 'lint' target"

def test_makefile_test_target(makefile_content):
    """Property 44: Makefile test target."""
    targets = get_targets(makefile_content)
    assert "test" in targets, "Makefile missing 'test' target"

def test_makefile_deployment_targets(makefile_content):
    """Property 45: Makefile deployment targets."""
    targets = get_targets(makefile_content)
    required_targets = [
        "bootstrap",
        "harden",
        "dev-tools",
        "network",
        "storage",
        "monitoring",
        "dr-test",
    ]
    for target in required_targets:
        assert target in targets, f"Makefile missing '{target}' target"

def test_makefile_ping_target(makefile_content):
    """Property 46: Makefile ping target."""
    targets = get_targets(makefile_content)
    assert "ping" in targets, "Makefile missing 'ping' target"
