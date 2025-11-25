# Field Lab Ansible Portfolio

Production-grade Infrastructure as Code (IaC) solution for automating provisioning and management of a complete lab environment including developer workstations, CI/CD infrastructure, network services, storage solutions, security hardening, and monitoring capabilities.

## Features

- **Security Hardening**: CIS-lite baseline, UFW firewall, SSH hardening, Fail2Ban
- **User Management**: Automated user provisioning with SSH key management
- **CI/CD Infrastructure**: Self-hosted GitLab CE and GitLab Runners
- **Developer Tooling**: VS Code Server and JupyterLab on workstations
- **Network Services**: VLAN configuration, DNS/DHCP with Dnsmasq
- **Storage & Backup**: NFS storage with automated Restic backups
- **Monitoring**: Elastic Agent for telemetry collection
- **Disaster Recovery**: Automated DR testing procedures

## Quick Start

### Prerequisites

- Python 3.11+
- Docker (for Molecule tests)
- `uv` (Python package manager)
- SSH access to target hosts
- Sudo privileges on target hosts

### Installation

1. Install `uv` if not already installed:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Set up the environment:
   ```bash
   make setup
   ```

3. Configure your inventory and variables:
   - Edit `inventories/lab.ini` with your host information
   - Update `group_vars/*.yml` with environment-specific values

### Deployment

```bash
# Test connectivity
make ping

# Apply base configuration
make bootstrap

# Apply security hardening
make harden

# Deploy developer tools
make dev-tools

# Configure network services
make network

# Set up storage and backups
make storage

# Deploy monitoring
make monitoring
```

## Testing

This project uses a comprehensive validation testing framework with three complementary approaches:

### 1. Property-Based Testing with Hypothesis

Property-based tests validate universal correctness properties across generated inputs using the Hypothesis framework. These tests verify that the infrastructure configuration maintains invariants regardless of specific values.

**What are Property-Based Tests?**

Instead of testing specific examples, property-based tests verify that certain properties hold true for *all* valid inputs. For example:
- "For any inventory file, all required groups must be defined"
- "For any Makefile, the setup target must install all required dependencies"
- "For any role with Molecule tests, the Docker driver must be configured"

**Running Property-Based Tests:**

```bash
# Run all property-based tests
uv run pytest tests/

# Run specific test categories
uv run pytest tests/test_property_idempotency.py
uv run pytest tests/test_property_variable_substitution.py
uv run pytest tests/test_property_inventory_parsing.py

# Run with verbose output
uv run pytest tests/ -v

# Run with coverage report
uv run pytest tests/ --cov
```

**Property Test Categories:**

- **Configuration Validation** (`test_config.py`, `test_inventory_config.py`): Validates inventory structure, group variables, and configuration files
- **Makefile Validation** (`test_makefile.py`): Verifies automation targets and command syntax
- **CI/CD Validation** (`test_cicd.py`): Validates GitHub Actions workflow configuration
- **Molecule Configuration** (`test_molecule_config.py`): Verifies Molecule test setup for all roles
- **Idempotency Properties** (`test_property_idempotency.py`): Tests that roles produce consistent results when applied multiple times
- **Variable Substitution** (`test_property_variable_substitution.py`): Validates template rendering with generated values
- **Inventory Parsing** (`test_property_inventory_parsing.py`): Tests inventory structure and group membership

### 2. Integration Testing with Molecule

Molecule provides end-to-end role testing in isolated Docker containers, validating that roles work correctly on fresh systems.

**Running Molecule Tests:**

```bash
# Run all Molecule tests
make test

# Test a specific role
cd ansible/roles/base_hardening && uv run molecule test

# Run only the converge step (apply role)
cd ansible/roles/base_hardening && uv run molecule converge

# Run only verification tests
cd ansible/roles/base_hardening && uv run molecule verify

# Keep container running for debugging
cd ansible/roles/base_hardening && uv run molecule converge && uv run molecule login
```

**Molecule Test Sequence:**

1. **Syntax**: Validate Ansible syntax
2. **Create**: Spin up Docker container
3. **Prepare**: Apply prerequisite configuration
4. **Converge**: Apply the role
5. **Idempotence**: Re-apply role and verify no changes
6. **Verify**: Run testinfra assertions
7. **Destroy**: Clean up container

**Roles with Molecule Tests:**

- `base_hardening`: Security configuration, firewall, SSH hardening
- `users`: User creation, SSH key authorization
- `packages`: Package cache updates
- `gitlab`: GitLab CE installation
- `gitlab_runner`: GitLab Runner setup
- `vscode_server`: VS Code Server deployment
- `jupyter`: JupyterLab installation
- `network`: Network services configuration
- `storage`: NFS and Restic setup
- `monitoring`: Elastic Agent deployment
- `dr_test`: Disaster recovery testing

### 3. Linting and Static Analysis

**Running Linters:**

```bash
# Run all linters
make lint

# Run ansible-lint only
uv run ansible-lint ansible/

# Run yamllint only
uv run yamllint ansible/ group_vars/ host_vars/
```

### Test Reports

After running tests, review the validation report:

```bash
cat validation_report.md
```

This report provides a comprehensive summary of all validated properties, test coverage, and any identified gaps.

## Property-Based Testing Approach

### Philosophy

Property-based testing shifts focus from "does this work for these specific examples?" to "does this maintain these invariants for all valid inputs?" This approach:

- **Catches edge cases** that manual test cases miss
- **Validates correctness properties** from the design specification
- **Provides confidence** that the system behaves correctly across the entire input space
- **Documents intent** by encoding what the system should do as executable properties

### How It Works

1. **Define Properties**: Each property is a universal statement about system behavior
   ```python
   # Property: For any inventory file, required groups must be defined
   @given(st.text())
   def test_inventory_groups_defined(inventory_content):
       # Test implementation
   ```

2. **Generate Inputs**: Hypothesis generates diverse test cases automatically
   - Random values within constraints
   - Edge cases (empty strings, boundary values)
   - Previously failing cases (regression testing)

3. **Verify Invariants**: Each generated input is tested against the property
   - If any input violates the property, the test fails
   - Hypothesis shrinks the failing case to the minimal example

4. **Iterate**: Failed tests reveal bugs or specification gaps
   - Fix the code if it's a bug
   - Refine the test if it's a test issue
   - Update the specification if it's incomplete

### Property Test Structure

Each property test includes:

```python
# Feature: ansible-infrastructure-validation, Property N: Description
# Validates: Requirements X.Y

@given(strategy)
@settings(max_examples=100)
def test_property_name(generated_input):
    # Arrange: Set up test conditions
    # Act: Perform operation
    # Assert: Verify property holds
```

### Writing New Property Tests

When adding new functionality:

1. **Identify invariants** from the design specification
2. **Write the property** as a test function
3. **Define generators** for valid inputs using Hypothesis strategies
4. **Run the test** with `uv run pytest`
5. **Triage failures** using the counterexample

## Troubleshooting

### Common Issues

#### 1. uv Command Not Found

**Symptom**: `bash: uv: command not found`

**Solution**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH (if not automatic)
export PATH="$HOME/.cargo/bin:$PATH"

# Verify installation
uv --version
```

#### 2. Docker Permission Denied (Molecule Tests)

**Symptom**: `permission denied while trying to connect to the Docker daemon socket`

**Solution**:
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Verify Docker access
docker ps
```

#### 3. Molecule Test Failures - Container Won't Start

**Symptom**: `Failed to create container` or `Container exited immediately`

**Solution**:
```bash
# Check Docker is running
docker ps

# Clean up old containers
docker system prune -f

# Try with privileged mode (already configured in molecule.yml)
cd ansible/roles/<role_name>
uv run molecule destroy
uv run molecule test
```

#### 4. SSH Connection Failures

**Symptom**: `Failed to connect to the host via ssh`

**Solution**:
```bash
# Test connectivity manually
ansible all -i inventories/lab.ini -m ping

# Check SSH key permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Verify host is reachable
ping <host_ip>

# Check SSH configuration
ssh -vvv user@host
```

#### 5. Ansible Vault Errors

**Symptom**: `Decryption failed` or `vault password required`

**Solution**:
```bash
# Provide vault password via prompt
ansible-playbook playbook.yml --ask-vault-pass

# Or use password file
ansible-playbook playbook.yml --vault-password-file ~/.vault_pass

# Encrypt sensitive variables
ansible-vault encrypt group_vars/infra.yml
```

#### 6. Property Test Failures

**Symptom**: Hypothesis reports a failing counterexample

**Solution**:

1. **Review the counterexample**: Hypothesis provides the minimal failing input
   ```
   Falsifying example: test_property(value='...')
   ```

2. **Triage the failure**:
   - Is the test incorrect? → Fix the test
   - Is it a bug in the code? → Fix the implementation
   - Is the specification incomplete? → Update requirements

3. **Reproduce the failure**:
   ```bash
   # Hypothesis saves failing examples in .hypothesis/examples/
   uv run pytest tests/test_file.py::test_name -v
   ```

4. **Fix and verify**:
   ```bash
   # After fixing, run the specific test
   uv run pytest tests/test_file.py::test_name

   # Then run full suite
   uv run pytest tests/
   ```

#### 7. Linting Errors

**Symptom**: `ansible-lint` or `yamllint` reports errors

**Solution**:
```bash
# View detailed error messages
uv run ansible-lint ansible/ -v

# Fix common issues:
# - Use FQCN: ansible.builtin.copy instead of copy
# - Add task names: - name: "Task description"
# - Fix YAML formatting: proper indentation, quotes

# Auto-fix some issues
uv run ansible-lint ansible/ --fix
```

#### 8. Idempotency Test Failures

**Symptom**: Molecule reports changes on second run

**Solution**:

1. **Identify non-idempotent tasks**:
   ```bash
   cd ansible/roles/<role_name>
   uv run molecule converge
   uv run molecule idempotence -v
   ```

2. **Common causes**:
   - Commands without `creates` or `changed_when`
   - Templates without proper conditionals
   - Services restarting unnecessarily

3. **Fix patterns**:
   ```yaml
   # Use creates for commands
   - name: Download file
     ansible.builtin.command: wget http://example.com/file
     args:
       creates: /path/to/file

   # Use changed_when for checks
   - name: Check status
     ansible.builtin.command: systemctl is-active service
     register: result
     changed_when: false
   ```

#### 9. Missing Dependencies

**Symptom**: `ModuleNotFoundError` or `ImportError`

**Solution**:
```bash
# Reinstall dependencies
uv sync

# Or force reinstall
rm -rf .venv
make setup

# Verify installation
uv run python -c "import ansible; print(ansible.__version__)"
```

#### 10. Slow Test Execution

**Symptom**: Tests take too long to run

**Solution**:
```bash
# Run tests in parallel
uv run pytest tests/ -n auto

# Run only fast tests (skip Molecule)
uv run pytest tests/ -m "not slow"

# Reduce Hypothesis examples for faster feedback
uv run pytest tests/ --hypothesis-profile=dev
```

### Getting Help

- **View test output**: Run with `-v` or `-vv` for verbose output
- **Check logs**: Review `logs/` directory for Ansible execution logs
- **Molecule debugging**: Use `molecule login` to inspect container state
- **Hypothesis database**: Check `.hypothesis/examples/` for failing cases
- **Validation report**: Review `validation_report.md` for coverage gaps

### Best Practices

1. **Run tests before deployment**: Always run `make lint` and `make test`
2. **Test incrementally**: Test roles individually before full playbook runs
3. **Use check mode**: Run playbooks with `--check` to preview changes
4. **Keep tests fast**: Use Docker for Molecule, not VMs
5. **Review failures carefully**: Property test failures often reveal real bugs
6. **Update tests with code**: Keep tests synchronized with implementation changes

## Directory Structure

```
├── ansible/
│   ├── playbooks/          # Main orchestration playbooks
│   ├── roles/              # Reusable Ansible roles
│   │   └── */molecule/     # Molecule tests for each role
│   ├── files/              # Static assets
│   └── templates/          # Jinja2 templates
├── inventories/            # Host definitions
├── group_vars/             # Group-level variables
├── host_vars/              # Host-specific variables
├── tests/                  # Property-based validation tests
├── docs/                   # Documentation and runbooks
├── .kiro/specs/            # Feature specifications
└── validation_report.md    # Test coverage summary
```

## Contributing

1. Write tests first (property-based or Molecule)
2. Implement the feature
3. Run linters: `make lint`
4. Run tests: `make test` and `uv run pytest tests/`
5. Update documentation
6. Generate validation report

## License

See LICENSE file for details.
