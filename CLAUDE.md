# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Portfolio repository demonstrating Linux/Cloud Systems Administration skills. Ansible-driven Ubuntu lab mirroring a production R&D SysAdmin environment.

Python tooling is managed via `uv` and `pyproject.toml`. All roles, playbooks, group_vars, inventory, tests, and CI are in place.

## Architecture

### Lab Network

| VLAN | Purpose | Hosts |
|------|---------|-------|
| 40 (Infra) | GitLab CE, NFS, DNS/DHCP, Elastic monitoring | gitlab, nfs, wazuh, dnsdhcp |
| 50 (Workstations) | Ubuntu workstations with VS Code Server + JupyterLab | ubuntu-ws-1, ubuntu-ws-2 |
| 60 (Lab Nodes) | Raspberry Pi Ubuntu nodes | pi-1, pi-2 |
| 70 (Runners) | GitLab CI/CD runners | runner-1, runner-2 |

### Roles (`ansible/roles/`)

Every role has `defaults/main.yml` documenting accepted variables and `molecule/default/` for integration tests.

| Role | What it does |
|------|-------------|
| `base_hardening` | Timezone, packages, UFW deny-by-default, SSH password auth off, fail2ban, unattended-upgrades |
| `users` | Admin user + sudo group membership, authorized SSH keys |
| `packages` | apt cache refresh |
| `gitlab` | GitLab CE install via official repo script |
| `gitlab_runner` | GitLab Runner install + `--non-interactive` registration |
| `vscode_server` | code-server install + systemd service |
| `jupyter` | JupyterLab via pip + parameterized systemd unit |
| `network` | dnsmasq DHCP/DNS + netplan VLAN config via Jinja2 templates |
| `storage` | nfs-kernel-server, restic init |
| `monitoring` | Elastic Agent download, extract, install, service (gated on `fleet_server_url`) |
| `dr_test` | Canary backup → restic restore → verify → clean up; fails loudly if restore is missing |

### Playbooks (`ansible/playbooks/`)

| Playbook | Hosts | What it does |
|----------|-------|-------------|
| `bootstrap.yml` | all | base_hardening + users + packages |
| `hardening.yml` | all | base_hardening + sysctl (CIS params) + auditd |
| `dev_tooling.yml` | workstations/runners/infra | gitlab, gitlab_runner, vscode_server, jupyter (role-conditioned) |
| `network.yml` | dnsdhcp | dnsmasq + netplan VLANs |
| `storage.yml` | infra | NFS + restic |
| `monitoring.yml` | all | Elastic Agent |
| `dr_test.yml` | infra | DR backup/restore test |

### Top-level Entrypoint

`site.yml` at the repo root imports all playbooks in deployment order (bootstrap → hardening → network → storage → dev_tooling → monitoring). Use this for full-stack provisioning:

```bash
ansible-playbook -i inventories/lab.ini site.yml -K --vault-password-file .vault_pass
```

## Commands

### Setup

```bash
make setup              # create .venv and install all tooling via uv
source .venv/bin/activate
```

### Lint and Test

```bash
make lint               # ansible-lint + yamllint
uv run pytest           # config validation + Hypothesis property tests (74 tests)
make test               # Molecule integration tests for all 11 roles (requires Docker)
uv run pytest -m property   # property tests only
```

Lint target: `ansible-lint` passes at the **production** profile (strictest).

### Ansible Operations

```bash
make ping               # connectivity check
make bootstrap          # initial node setup
make harden             # CIS-lite hardening + sysctl + auditd
make dev-tools          # GitLab, Runners, VS Code Server, Jupyter
make network            # DNS/DHCP + VLANs
make storage            # NFS + restic init
make monitoring         # Elastic Agent
make dr-test            # backup/restore DR test
```

### Targeted runs with tags

```bash
# Apply only firewall rules across all hosts
ansible-playbook -i inventories/lab.ini ansible/playbooks/hardening.yml -K --tags firewall

# Patch packages only
ansible-playbook -i inventories/lab.ini ansible/playbooks/bootstrap.yml -K --tags patching

# Re-run audit config without full hardening
ansible-playbook -i inventories/lab.ini ansible/playbooks/hardening.yml -K --tags audit
```

Available tags: `security`, `hardening`, `firewall`, `ssh`, `sysctl`, `audit`, `packages`, `patching`, `users`, `gitlab`, `runner`, `devtools`, `vscode`, `jupyter`, `network`, `dns`, `dhcp`, `vlan`, `storage`, `nfs`, `backup`, `monitoring`, `dr`.

### Manual playbook invocation

```bash
# Full site deploy
ansible-playbook -i inventories/lab.ini site.yml -K --vault-password-file .vault_pass

# Single playbook, check mode
ansible-playbook -i inventories/lab.ini ansible/playbooks/hardening.yml -K --check

# Limit to subset of hosts
ansible-playbook -i inventories/lab.ini ansible/playbooks/bootstrap.yml -K --limit lab_nodes

# Verbose
ansible-playbook -i inventories/lab.ini ansible/playbooks/network.yml -K -vvv
```

## Configuration

### ansible.cfg

`roles_path = ./ansible/roles`, default inventory `inventories/lab.ini`, host key checking off, no retry files.

### Inventory (`inventories/lab.ini`)

INI format, four groups: `workstations`, `lab_nodes`, `runners`, `infra`.

### Group Variables

```
group_vars/
  all.yml                   # timezone, admin_user, ssh_public_keys, packages_common
  workstations.yml          # vscode_server, jupyter_install
  infra/
    vars.yml                # gitlab_external_url, nfs_export_path, restic_repo, restic_password (→ vault)
    vault.yml               # AES256-encrypted: vault_restic_password
  runners/
    vars.yml                # gitlab_runner_executor, gitlab_runner_registration_token (→ vault)
    vault.yml               # AES256-encrypted: vault_gitlab_runner_token
```

### Ansible Vault

Sensitive values (`restic_password`, `gitlab_runner_registration_token`) are stored in encrypted `vault.yml` files and referenced via `{{ vault_* }}` variables in the corresponding `vars.yml`.

**Demo vault password:** `labvault` — rotate before any real deployment.

```bash
# View vault contents
ansible-vault view group_vars/infra/vault.yml --vault-password-file .vault_pass

# Edit vault contents
ansible-vault edit group_vars/infra/vault.yml --vault-password-file .vault_pass

# Re-encrypt with a new password
ansible-vault rekey group_vars/infra/vault.yml
```

`.vault_pass` is in `.gitignore`. Never commit it or actual secret values.

### Monitoring variables

`fleet_server_url` and `fleet_enrollment_token` in `group_vars/all.yml` (or host_vars) are required for Elastic Agent to enroll with Fleet. When unset, the role downloads and extracts the agent but skips install — safe for staging without a Fleet server.

## CI/CD (`.github/workflows/ci.yml`)

Two jobs on every push/PR:

1. **lint** — `ansible-lint ansible/` + `yamllint ansible/ group_vars/ host_vars/`
2. **syntax-check** — `ansible-playbook --syntax-check` on every playbook in `ansible/playbooks/`

Both use Python 3.11.

## Development Notes

### Adding a new role

1. `ansible/roles/ROLE_NAME/{tasks,templates,files,handlers,defaults}/`
2. `tasks/main.yml` — use FQCN (`ansible.builtin.*`, `community.general.*`) and add tags to every task
3. `defaults/main.yml` — document every variable the role accepts with safe defaults
4. `handlers/main.yml` — any service restarts or notifications
5. `molecule/default/` — Molecule scenario for the role
6. Add role to the relevant playbook(s)
7. Add the role to the `make test` Makefile target
8. If the role uses secrets, store them in the relevant group's `vault.yml` and reference via `{{ vault_* }}`

### Adding a new secret

1. Add a `vault_*` variable to the relevant `group_vars/<group>/vault.yml`:
   ```bash
   ansible-vault edit group_vars/infra/vault.yml --vault-password-file .vault_pass
   ```
2. Reference it in `group_vars/<group>/vars.yml` as `my_var: "{{ vault_my_var }}"`
3. Add the variable with an empty-string default to the role's `defaults/main.yml`

### Modifying playbooks

1. Always `--check` first
2. `--limit` to a single host for first run
3. Playbooks must be idempotent — safe to run multiple times
4. `hardening.yml` intentionally does more than `bootstrap.yml`; don't collapse them

### Tag conventions

Apply the most specific tag(s) that describe what the task changes. Use broad tags (`security`, `packages`) alongside specific ones (`firewall`, `patching`) so operators can target either way. Every task must have at least one tag.
