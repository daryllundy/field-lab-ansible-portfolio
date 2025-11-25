import pytest

@pytest.fixture(scope="session")
def ansible_inventory_path():
    return "inventories/hosts.yml"
