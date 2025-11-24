# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a portfolio repository for demonstrating Linux/Cloud Systems Administration skills. It contains:

1. **Field Lab Ansible**: An Ansible-driven Ubuntu lab scaffold that mirrors production R&D SysAdmin environments
2. **Tailored Resume**: A one-page resume optimized for Linux System Administrator and DevOps roles

The repository includes a comprehensive scaffold script (`create_field_lab_repo.sh` embedded in NOTES.md) that generates a complete Ansible infrastructure project.

## Current State

The repository currently contains only planning documentation in NOTES.md. The actual Ansible infrastructure has not yet been scaffolded. When implementing, you'll need to:

1. Extract and execute the `create_field_lab_repo.sh` script from NOTES.md
2. Or manually create the directory structure and files as outlined in the scaffold

## Architecture

### Intended Lab Structure

The field lab will consist of:

- **VLAN 40 (Infra)**: GitLab CE, NFS server, DNS/DHCP, Wazuh/Elastic monitoring
- **VLAN 50 (Workstations)**: Ubuntu workstations with VS Code Server and JupyterLab
- **VLAN 60 (Lab Nodes)**: Raspberry Pi devices running Ubuntu
- **VLAN 70 (Runners)**: GitLab Runner nodes for CI/CD

### Key Ansible Roles

When scaffolded, the project will include these roles:

- `base_hardening`: CIS-lite hardening, SSH config, UFW firewall, fail2ban, unattended-upgrades
- `users`: Admin user setup and SSH key management
- `gitlab`: GitLab CE installation and configuration
- `gitlab_runner`: GitLab Runner registration and setup
- `vscode_server`: VS Code Server (code-server) deployment
- `jupyter`: JupyterLab installation and systemd service
- `network`: VLAN configuration, dnsmasq DHCP/DNS, unbound
- `storage`: NFS server setup and restic backup configuration
- `monitoring`: Elastic Agent or Wazuh deployment for EDR-like telemetry
- `dr_test`: Disaster recovery testing playbook

### Playbooks

- `bootstrap.yml`: Initial node setup with base hardening, users, packages
- `hardening.yml`: Apply CIS-lite security controls
- `dev_tooling.yml`: Install GitLab, Runners, VS Code Server, Jupyter
- `network.yml`: Configure DNS/DHCP and VLANs
- `storage.yml`: Setup NFS and backup systems
- `monitoring.yml`: Deploy monitoring/EDR agents
- `dr_test.yml`: Test disaster recovery procedures

## Common Commands

### Development Setup

```bash
# Create Python virtual environment and install Ansible tooling
make setup

# Activate virtual environment
source .venv/bin/activate
```

### Linting

```bash
# Run ansible-lint and yamllint
make lint
```

### Ansible Operations

```bash
# Test connectivity to all hosts
make ping

# Bootstrap nodes (initial setup)
make bootstrap

# Apply CIS-lite hardening
make harden

# Install development tools (GitLab, Runners, VS Code, Jupyter)
make dev-tools

# Configure network services (DHCP/DNS)
make network

# Setup storage and backups
make storage

# Deploy monitoring agents
make monitoring

# Run disaster recovery test
make dr-test
```

### Manual Ansible Commands

```bash
# Run a specific playbook with the lab inventory
ansible-playbook -i inventories/lab.ini playbooks/bootstrap.yml -K

# Run against specific hosts
ansible-playbook -i inventories/lab.ini playbooks/hardening.yml -K --limit workstations

# Check mode (dry run)
ansible-playbook -i inventories/lab.ini playbooks/dev_tooling.yml -K --check

# With extra verbosity
ansible-playbook -i inventories/lab.ini playbooks/network.yml -K -vvv
```

## Important Configuration Files

### Inventory

- `inventories/lab.ini`: Defines all hosts organized by groups (workstations, lab_nodes, runners, infra)

### Group Variables

- `group_vars/all.yml`: Common settings (timezone, admin user, SSH keys, packages)
- `group_vars/workstations.yml`: Workstation-specific config (VS Code Server, Jupyter)
- `group_vars/runners.yml`: GitLab Runner registration tokens and executor settings
- `group_vars/infra.yml`: Infrastructure services config (GitLab URL, NFS paths, restic settings)

### Security Considerations

Before deploying:

1. **Replace all placeholder values**:
   - SSH public keys in `group_vars/all.yml`
   - GitLab Runner registration token in `group_vars/runners.yml`
   - Restic password in `group_vars/infra.yml`
   - GitLab external URL in `group_vars/infra.yml`

2. **Review security defaults**:
   - Password authentication is disabled in SSH by default
   - UFW firewall is enabled with deny-by-default policy
   - Unattended upgrades are enabled on Debian/Ubuntu
   - fail2ban is enabled for brute-force protection

3. **Do not commit secrets**:
   - Never commit actual passwords, tokens, or private keys
   - Use Ansible Vault for sensitive data in production
   - The `.gitignore` excludes `.env` files

## CI/CD

The project includes GitHub Actions workflow at `.github/workflows/ci.yml` that:

- Runs on all pushes and pull requests
- Installs Python 3.11 and Ansible tooling
- Executes ansible-lint on all playbooks
- Runs yamllint on YAML files

## Development Notes

### When Adding New Roles

1. Create role directory structure: `ansible/roles/ROLE_NAME/{tasks,templates,files,handlers,defaults}`
2. Define tasks in `tasks/main.yml`
3. Add handlers in `handlers/main.yml` if needed
4. Document role variables in `defaults/main.yml`
5. Update relevant playbooks to include the new role

### When Modifying Playbooks

1. Always test with `--check` (dry run) first
2. Use `--limit` for testing on a subset of hosts
3. Ensure idempotency - playbooks should be safe to run multiple times
4. Update documentation if behavior changes

### Testing Strategy

1. Run `make lint` before committing
2. Test playbooks on a single node first with `--limit`
3. Use `--check` mode to verify what would change
4. Validate in the lab environment before production
5. Document any manual verification steps in runbooks

## Resume Information

The NOTES.md file contains a comprehensive resume for Daryl Lundy targeting Linux System Administrator and DevOps positions at R&D-focused organizations. Key highlights:

- 10+ years of Linux administration (Ubuntu, RHEL)
- Ansible automation and GitLab CI/CD expertise
- Security focus: CIS hardening, patching, EDR, backups/DR
- Networking: VLANs, DHCP/DNS configuration
- Developer platform support: GitLab Runners, VS Code Server, Jupyter

## Project Purpose

This portfolio demonstrates production-flavored IT automation for Linux-heavy, robotics/R&D workflows. It showcases:

- Infrastructure as Code with Ansible
- Security-first approach with hardening and compliance
- CI/CD capabilities with GitLab
- Network design and service deployment
- Disaster recovery planning and testing
- Developer productivity tooling
