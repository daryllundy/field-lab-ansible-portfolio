# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project

Ansible-driven Ubuntu lab portfolio demonstrating Linux SysAdmin / DevOps / SRE skills: CIS hardening, GitLab CI/CD, NFS/restic DR, Elastic Agent monitoring, VLAN networking. Python tooling via `uv`.

## Safe commands (run without asking)

```bash
# Lint — must exit 0 before any commit
uv run ansible-lint ansible/
uv run yamllint ansible/ group_vars/

# Tests — no external deps, always safe
uv run pytest

# Syntax check — read-only, does not contact hosts
for pb in ansible/playbooks/*.yml; do ansible-playbook --syntax-check "$pb"; done

# Install Ansible collection deps (declarative)
ansible-galaxy collection install -r ansible/requirements.yml

# Read vault (demo password: labvault)
ansible-vault view group_vars/infra/vault.yml --vault-password-file <(echo 'labvault')
ansible-vault view group_vars/runners/vault.yml --vault-password-file <(echo 'labvault')

# Explore the repo
find ansible/ -type f | sort
cat ansible/roles/*/tasks/main.yml
cat ansible/roles/*/defaults/main.yml
```

## Do NOT run

| Command | Why |
|---------|-----|
| `make test` / `molecule test` | Requires Docker — do not assume it is available |
| `make ping` / `make bootstrap` / any `ansible-playbook` without `--syntax-check` | Contacts real hosts |
| `ansible-vault encrypt` or `rekey` on committed files | Breaks decryption for everyone |
| `git push --force`, `git reset --hard`, `git clean -f` | Destructive, irreversible |
| `pip install` outside `.venv` | Use `uv run` or activate `.venv` first |

## Verification after any change

```bash
uv run ansible-lint ansible/        # expected: "Passed: 0 failure(s), 0 warning(s) … 'production' profile passed"
uv run pytest                       # expected: "74 passed" (or more if tests were added)
```

Both must pass before committing. If lint fails, fix the violation — do not suppress it with `noqa` unless genuinely a false positive, and document why.

## Repository layout

```
site.yml                            # top-level entrypoint: imports all playbooks in order
Makefile                            # %-logged pattern target tees any deploy to logs/<target>-<ts>.log
ansible/
  requirements.yml                  # collection deps (community.general, ansible.posix)
  playbooks/                        # individual playbooks (bootstrap → hardening → network → storage → dev_tooling → monitoring → dr_test)
  roles/
    <role>/
      tasks/main.yml                # FQCN tasks; every task has tags
      defaults/main.yml             # every variable the role accepts, with safe defaults
      handlers/main.yml
      templates/                    # Jinja2 templates (network role)
      molecule/default/             # Docker-based integration tests
inventories/lab.ini                 # groups: workstations, lab_nodes, runners, infra
group_vars/
  all.yml                           # common: timezone, admin_user, ssh_public_keys, packages_common
  workstations.yml                  # vscode_server, jupyter_install, packages_extra
  infra/
    vars.yml                        # gitlab_external_url, nfs paths, packages_extra; restic_password → {{ vault_restic_password }}
    vault.yml                       # AES256-encrypted
  runners/
    vars.yml                        # gitlab_runner_executor, packages_extra; token → {{ vault_gitlab_runner_token }}
    vault.yml                       # AES256-encrypted
host_vars/
  gitlab.yml                        # host-level override example (gitlab_external_url)
logs/                               # tee'd Make target output lands here (.gitkeep pins the dir)
tests/                              # pytest: config validation + Hypothesis property tests
```

## Roles

| Role | Key variables (see defaults/main.yml) |
|------|--------------------------------------|
| `base_hardening` | `timezone`, `packages_common`, `unattended_upgrades` |
| `users` | `admin_user`, `ssh_public_keys` |
| `packages` | `packages_extra` (per-group package list, empty by default) |
| `gitlab` | `gitlab_external_url` |
| `gitlab_runner` | `gitlab_external_url`, `gitlab_runner_registration_token`, `gitlab_runner_executor` |
| `vscode_server` | `admin_user`, `vscode_server_port` |
| `jupyter` | `admin_user`, `jupyter_port`, `jupyter_ip` |
| `network` | `lab_domain`, `dhcp_ranges`, `dns_server`, `uplink_interface` |
| `storage` | `nfs_export_path`, `nfs_clients`, `restic_repo`, `restic_password` |
| `monitoring` | `elastic_agent_version`, `fleet_server_url`, `fleet_enrollment_token` |
| `dr_test` | `restic_repo`, `restic_password` |

The `monitoring` role gates install/service on `fleet_server_url` being non-empty. The `dr_test` role writes a canary file, backs it up, restores to a temp dir, verifies the canary, then cleans up — fails loudly if the restore is incomplete.

## Logged Make targets

Any deployment target can be suffixed with `-logged` to tee output to `logs/<target>-<timestamp>.log`. Examples:

```bash
make bootstrap-logged          # logs/bootstrap-20260522-100534.log
make harden-logged
make dev-tools-logged
```

Implementation is a `%-logged` pattern rule in the Makefile. `logs/` is tracked via `.gitkeep`; its contents are gitignored.

## Hardening playbook

`hardening.yml` does more than `bootstrap.yml` — on top of `base_hardening` it applies CIS sysctl parameters (`/etc/sysctl.d/99-cis.conf`) and installs/configures auditd with identity and exec audit rules. Do not collapse these two playbooks.

## Vault workflow

Secrets (`restic_password`, `gitlab_runner_registration_token`) live in encrypted `vault.yml` files and are referenced as `{{ vault_* }}` in the corresponding `vars.yml`.

```bash
# Edit a vault file
ansible-vault edit group_vars/infra/vault.yml --vault-password-file <(echo 'labvault')

# Add a new secret
# 1. Edit vault.yml → add vault_my_secret: "value"
# 2. Edit vars.yml  → add my_var: "{{ vault_my_secret }}"
# 3. Edit role defaults/main.yml → add my_var: ""
```

Demo vault password: `labvault` — rotate before real deployment. `.vault_pass` is gitignored.

## Coding conventions

- **FQCN**: `ansible.builtin.copy`, not `copy`; `community.general.ufw`, not `ufw`
- **Tags**: every task gets at least one tag — see taxonomy below
- **Idempotency**: use `creates:`, `state: present`, `regexp` guards — not bare `command` that re-runs
- **No inline secrets**: vault only
- **No comments explaining what the code does**: name the task well instead

## Tag taxonomy

`security` · `hardening` · `firewall` · `ssh` · `sysctl` · `audit` · `packages` · `patching` · `users` · `gitlab` · `runner` · `devtools` · `vscode` · `jupyter` · `network` · `dns` · `dhcp` · `vlan` · `storage` · `nfs` · `backup` · `monitoring` · `dr`

Use the most specific tag(s) plus any relevant broad parent tag (e.g., `[hardening, firewall, security]`).

## Adding a role checklist

- [ ] `tasks/main.yml` — FQCN, tagged, idempotent
- [ ] `defaults/main.yml` — every variable with a safe default
- [ ] `handlers/main.yml` — any service restarts
- [ ] `molecule/default/` — Docker/testinfra scenario
- [ ] Added to relevant playbook
- [ ] Added to `make test` in Makefile
- [ ] `uv run ansible-lint ansible/` passes
- [ ] `uv run pytest` passes

## CI

`.github/workflows/ci.yml` runs two jobs on every push/PR:
1. `lint` — ansible-lint + yamllint, Python 3.11
2. `syntax-check` — `--syntax-check` on every playbook

Both must pass. Do not merge with a failing CI.
