# CLAUDE.md

Boilerplate instructions for Claude Code. Copy into the root of every new project. Edit the **Project Context** block at the top per repo. Everything else is locked.

---

## Project Context

**Project:** Field Lab Ansible Portfolio
**Goal:** Demonstrate production-flavored Linux SysAdmin / DevOps / SRE skills via an Ansible-driven Ubuntu lab, with code quality and operational maturity that holds up under technical screening.
**Audience:** Hiring managers and technical interviewers screening for DevOps, SRE, Cloud Engineer, and Technical Support roles.
**Stack constraints:** Ansible only for IaC (no Terraform / Pulumi); Ubuntu/Debian target hosts; FQCN required on every module (`ansible.builtin.*`, `community.general.*`, `ansible.posix.*`); Python tooling via `uv` (no `pip` outside `.venv`); Molecule scenarios use the Docker driver.
**Avoid:** AI-generated bloat patterns — "Executive Summary"-style docs, `Property N:` / `Validates: Requirement N.N` annotations, formal report metadata (Author / Version / Last Updated headers), buzzword openers ("production-grade", "comprehensive"), emojis in docs or code, speculative "Future Enhancements" sections, plaintext secrets, `Co-Authored-By: Claude` trailers on commits.

If a task conflicts with anything in this block, flag it before proceeding.

---

## About Me

- **Name:** Daryl Lundy
- **Location:** Long Beach, CA
- **Role:** DevOps / SRE / Cloud Engineer / Technical Support (8+ years)
- **Strong in:** Linux infrastructure, AWS, Ansible, Docker, Kubernetes, GitLab, Prometheus/Grafana/Loki, WordPress, Shopify, Go (CLI tooling), bash, technical support and escalations
- **Comfortable in:** Python, JavaScript/TypeScript, Next.js, React, Terraform, multi-agent Claude Code orchestration
- **Still learning:** Deeper Go patterns, advanced K8s operators, frontend design systems

Adjust depth accordingly. Don't over-explain Linux, networking, cloud, or CI/CD basics. Don't skip context on newer frontend frameworks or niche libraries.

---

## Communication Preferences

- **No preamble.** Start every response with the actual answer. No "Great question!", "Certainly!", "Of course!", or restating what I asked.
- **Match length to task.** Simple questions get short answers. Complex tasks get full detail. No padding, no closing restatements.
- **Show options before significant work.** For non-trivial tasks, present 2–3 approaches with tradeoffs and wait for me to pick before proceeding.
- **Flag uncertainty explicitly.** If you're not sure about a fact, version, API shape, or technical detail, say so before including it. Never fill gaps with plausible-sounding guesses.
- **Voice:** direct, technical, dry. Skip hedging. Skip motivational closers.

---

## Tech Stack Defaults

Use these unless I explicitly say otherwise. If something seems like the wrong tool for the task, flag it — but don't silently substitute.

- **Language:** YAML (Ansible playbooks/roles) and Python 3.10+ (tests, tooling)
- **Framework:** Ansible — roles + playbooks + Molecule
- **Package manager:** `uv` for Python; `ansible-galaxy` for collections (`community.general`, `ansible.posix`)
- **Database:** n/a — infrastructure project, no app database
- **Testing:** `pytest` + Hypothesis for static/property tests; Molecule + testinfra for role integration tests
- **Styling (if UI):** n/a — no UI
- **Infra:** Ansible-managed Ubuntu/Debian hosts; Docker (Molecule test isolation); GitHub Actions for CI

---

## Behavior Rules

These are non-negotiable. They apply every session.

### 1. Ask, don't assume
If intent, architecture, or requirements are unclear, ask before writing a line. No silent assumptions.

### 2. Simplest solution first
Implement the minimum that solves the problem. No speculative abstractions, no flexibility that wasn't requested, no error handling for impossible cases. If a senior engineer would call it overcomplicated, simplify.

### 3. Surgical changes only
Only modify files, functions, and lines directly related to the current task. Do not refactor, rename, reorganize, reformat, or "improve" anything I didn't ask you to change. Match existing style even if you'd write it differently. If you spot something else worth fixing, mention it in a note at the end. Do not touch it.

### 4. Confirm before significant rewrites
Before rewriting sections, removing paragraphs, restructuring flow, or changing tone of existing content: stop. Describe what you're about to change and why. Wait for my confirmation.

### 5. Confirm before destructive actions
Before deleting any file, overwriting existing code, dropping database records, removing dependencies, or anything irreversible: stop, list what will be affected, ask for explicit confirmation. Only proceed after I say yes **in the current message**. Prior context is not consent.

### 6. Hard stops require in-session "yes"
The following require explicit confirmation in the current message, no exceptions:
- Deploying or pushing to any environment
- Running migrations or schema changes
- Sending any external API call with side effects
- Executing any command with irreversible side effects
- Sending, posting, publishing, sharing, or scheduling anything on my behalf (emails, calendar invites, doc shares, etc.)

### 7. Think before non-trivial work
For architecture decisions, complex debugging, or non-trivial features: work through the problem step by step before writing code. Show reasoning. Identify uncertainty. Then implement. Use extended thinking for system architecture, performance tradeoffs, database design, or long-term technical decisions.

---

## End-of-Task Output

After any coding task, end with this block:

```
Files changed:
  - path/to/file: <one-line description>
What was modified:
  - <one line per file>
Files intentionally not touched:
  - <list anything adjacent I might expect you touched but you didn't>
Follow-up needed:
  - <anything I should know or do next>
```

---

## Memory Files

### MEMORY.md
Maintain a `MEMORY.md` in the project root. Read it at the start of every session.
- After any significant decision, append an entry: **What was decided / Why / What was rejected and why**.
- Never contradict a logged decision without flagging it first.
- When I say "session end", "wrapping up", or "let's stop here": write a session summary with **Worked on / Completed / In progress / Decisions made / Next session priorities**.

### ERRORS.md
Maintain an `ERRORS.md` in the project root. Check it before suggesting approaches to similar tasks.
- When an approach takes more than 2 attempts to work, log: **What didn't work / What worked instead / Note for next time**.

---

## Permanent Project Constraints

- Secrets only via Ansible Vault. No plaintext secrets in vars files. Reference `vault_*` variables from `group_vars/*/vars.yml`, store encrypted values in `group_vars/*/vault.yml`.
- Every task in every role must have at least one tag. See AGENTS.md for the tag taxonomy.
- Every role must have a `defaults/main.yml` documenting accepted variables with safe defaults.
- `ansible-lint` must pass at the **production** profile. Do not suppress with `noqa` without a documented reason.
- `RESUME.md` is intentionally gitignored. Never commit, stage, or propose adding it.
- `.claude/` is gitignored. Never commit local Claude Code settings.
- Never add `Co-Authored-By: Claude` trailers to commit messages or PR descriptions.
- `AGENTS.md` mirrors the project-context sections below for non-Claude agents (Codex etc.). Keep the two in sync when project details change.

If any task conflicts with one of these, flag it before proceeding.

---

# Project Context

Everything below this line is the project-specific context. Edit freely as the codebase changes.

## Architecture

### Lab network

| VLAN | Purpose | Hosts |
|------|---------|-------|
| 40 (Infra) | GitLab CE, NFS, DNS/DHCP, Elastic monitoring | gitlab, nfs, elastic, dnsdhcp |
| 50 (Workstations) | Ubuntu workstations with VS Code Server + JupyterLab | ubuntu-ws-1, ubuntu-ws-2 |
| 60 (Lab Nodes) | Raspberry Pi Ubuntu nodes | pi-1, pi-2 |
| 70 (Runners) | GitLab CI/CD runners | runner-1, runner-2 |

### Repository layout

```
site.yml                            # top-level entrypoint: imports all playbooks in order
ansible/
  playbooks/                        # bootstrap → hardening → network → storage → dev_tooling → monitoring → dr_test
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
  workstations.yml                  # vscode_server, jupyter_install
  infra/
    vars.yml                        # gitlab_external_url, nfs paths; restic_password → {{ vault_restic_password }}
    vault.yml                       # AES256-encrypted
  runners/
    vars.yml                        # gitlab_runner_executor; token → {{ vault_gitlab_runner_token }}
    vault.yml                       # AES256-encrypted
tests/                              # pytest: config validation + Hypothesis property tests
```

## Roles

Every role has `defaults/main.yml` documenting accepted variables and `molecule/default/` for integration tests.

| Role | Key variables | What it does |
|------|---------------|-------------|
| `base_hardening` | `timezone`, `packages_common`, `unattended_upgrades` | UFW deny-by-default, SSH password auth off, fail2ban, unattended-upgrades |
| `users` | `admin_user`, `ssh_public_keys` | Admin user + sudo + authorized keys |
| `packages` | `packages_common` | apt cache refresh |
| `gitlab` | `gitlab_external_url` | GitLab CE install via official repo script |
| `gitlab_runner` | `gitlab_external_url`, `gitlab_runner_registration_token`, `gitlab_runner_executor` | GitLab Runner install + `--non-interactive` registration |
| `vscode_server` | `admin_user`, `vscode_server_port` | code-server install + systemd service |
| `jupyter` | `admin_user`, `jupyter_port`, `jupyter_ip` | JupyterLab via pip + systemd unit |
| `network` | `lab_domain`, `dhcp_ranges`, `dns_server`, `uplink_interface` | dnsmasq DHCP/DNS + netplan VLANs via Jinja2 templates |
| `storage` | `nfs_export_path`, `nfs_clients`, `restic_repo`, `restic_password` | NFS server + restic init |
| `monitoring` | `elastic_agent_version`, `fleet_server_url`, `fleet_enrollment_token` | Elastic Agent download, extract, install, service (gated on `fleet_server_url`) |
| `dr_test` | `restic_repo`, `restic_password` | Canary backup → restic restore → verify → clean up; fails loudly if restore is missing |

## Playbooks

| Playbook | Hosts | What it does |
|----------|-------|-------------|
| `bootstrap.yml` | all | base_hardening + users + packages |
| `hardening.yml` | all | base_hardening + sysctl (CIS params) + auditd |
| `dev_tooling.yml` | workstations/runners/infra | gitlab, gitlab_runner, vscode_server, jupyter (role-conditioned) |
| `network.yml` | dnsdhcp | dnsmasq + netplan VLANs |
| `storage.yml` | infra | NFS + restic |
| `monitoring.yml` | all | Elastic Agent |
| `dr_test.yml` | infra | DR backup/restore test |

`hardening.yml` does more than `bootstrap.yml` — on top of `base_hardening` it applies CIS sysctl parameters (`/etc/sysctl.d/99-cis.conf`) and configures auditd. Do not collapse the two.

`site.yml` at the repo root imports all playbooks in deployment order. Full-stack provision:

```bash
ansible-playbook -i inventories/lab.ini site.yml -K --vault-password-file .vault_pass
```

## Commands

### Setup, lint, test

```bash
make setup                          # create .venv and install all tooling via uv
make lint                           # ansible-lint + yamllint
uv run pytest                       # config validation + Hypothesis property tests (74 tests)
make test                           # Molecule integration tests for all 11 roles (requires Docker)
uv run pytest -m property           # property tests only
```

Lint passes at the **production** profile.

### Ansible operations

```bash
make ping bootstrap harden dev-tools network storage monitoring dr-test
```

### Targeted runs with tags

```bash
ansible-playbook -i inventories/lab.ini ansible/playbooks/hardening.yml -K --tags firewall
ansible-playbook -i inventories/lab.ini ansible/playbooks/bootstrap.yml -K --tags patching
ansible-playbook -i inventories/lab.ini ansible/playbooks/hardening.yml -K --tags audit
```

### Manual invocation

```bash
ansible-playbook -i inventories/lab.ini ansible/playbooks/hardening.yml -K --check       # dry run
ansible-playbook -i inventories/lab.ini ansible/playbooks/bootstrap.yml -K --limit pi-1  # single host
```

## Vault workflow

Sensitive values (`restic_password`, `gitlab_runner_registration_token`) live in encrypted `vault.yml` files and are referenced via `{{ vault_* }}` from the corresponding `vars.yml`.

```bash
# View
ansible-vault view group_vars/infra/vault.yml --vault-password-file <(echo 'labvault')

# Edit
ansible-vault edit group_vars/infra/vault.yml --vault-password-file <(echo 'labvault')
```

**Demo vault password:** `labvault` — rotate before any real deployment. `.vault_pass` is gitignored.

**Adding a new secret:**
1. `ansible-vault edit group_vars/<group>/vault.yml` → add `vault_my_secret: "value"`
2. Edit `group_vars/<group>/vars.yml` → add `my_var: "{{ vault_my_secret }}"`
3. Edit role `defaults/main.yml` → add `my_var: ""` (safe empty default)

## Tag taxonomy

`security` · `hardening` · `firewall` · `ssh` · `sysctl` · `audit` · `packages` · `patching` · `users` · `gitlab` · `runner` · `devtools` · `vscode` · `jupyter` · `network` · `dns` · `dhcp` · `vlan` · `storage` · `nfs` · `backup` · `monitoring` · `dr`

Use the most specific tag(s) plus any relevant broad parent (e.g., `[hardening, firewall, security]`). Every task must have at least one tag.

## CI

`.github/workflows/ci.yml` runs on every push/PR with Python 3.11:
1. **lint** — `ansible-lint ansible/` + `yamllint ansible/ group_vars/ host_vars/`
2. **syntax-check** — `ansible-playbook --syntax-check` on every playbook

Both must pass before merge.

## Adding a new role

1. `ansible/roles/ROLE_NAME/{tasks,templates,files,handlers,defaults}/`
2. `tasks/main.yml` — FQCN, tagged tasks, idempotent
3. `defaults/main.yml` — every variable with a safe default
4. `handlers/main.yml` — service restarts
5. `molecule/default/` — Docker/testinfra scenario
6. Add role to relevant playbook(s)
7. Add role to `make test` in Makefile
8. If the role uses secrets, store them in the relevant `vault.yml` and reference via `{{ vault_* }}`
9. `uv run ansible-lint ansible/` and `uv run pytest` must both pass
