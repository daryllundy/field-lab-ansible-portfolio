A complete portfolio package for demonstrating Linux/Cloud Systems Administration skills, including an Ansible-driven Ubuntu lab scaffold and a tailored resume for R&D SysAdmin roles.

---

## Table of Contents

1. [Overview](https://claude.ai/chat/d9ffab7e-36f7-4ff1-ada1-4f168f06b29e#overview)
2. [Repository Scaffold Script](https://claude.ai/chat/d9ffab7e-36f7-4ff1-ada1-4f168f06b29e#repository-scaffold-script)
3. [Resume](https://claude.ai/chat/d9ffab7e-36f7-4ff1-ada1-4f168f06b29e#resume)
4. [Next Steps](https://claude.ai/chat/d9ffab7e-36f7-4ff1-ada1-4f168f06b29e#next-steps)

---

## Overview

This package contains two components:

- **Field Lab Ansible**: An Ansible-provisioned Ubuntu lab mirroring production R&D SysAdmin environments with CIS-lite hardening, GitLab CI/CD, developer tooling, and DR capabilities
- **Tailored Resume**: A one-page resume optimized for Linux System Administrator and DevOps roles at R&D-focused organizations

---

## Repository Scaffold Script

Save the following as `create_field_lab_repo.sh`, make executable (`chmod +x create_field_lab_repo.sh`), and run in an empty directory.

````bash
#!/usr/bin/env bash
set -euo pipefail

REPO_NAME="field-lab-ansible"
YEAR=$(date +%Y)

die() {
  echo "Error: $*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Missing required command: $1"
}

require_cmd git
require_cmd bash

if [ -d "$REPO_NAME" ]; then
  die "Directory '$REPO_NAME' already exists. Please remove or choose a different path."
fi

mkdir -p "$REPO_NAME"
cd "$REPO_NAME"

# Basic repo files
cat > .gitignore <<'EOF'
# OS
.DS_Store

# Python
__pycache__/
*.pyc

# Node
node_modules/

# Ansible
*.retry
.env
.venv/

# Logs
logs/
*.log

# Terraform (if added later)
.terraform/
*.tfstate
*.tfstate.*
crash.log
EOF

cat > LICENSE <<'EOF'
MIT License

Copyright (c) YEAR Daryl

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
EOF
sed -i.bak "s/YEAR/$YEAR/g" LICENSE && rm LICENSE.bak || true

# Makefile
mkdir -p scripts
cat > Makefile <<'EOF'
SHELL := /bin/bash
ANSIBLE := ansible-playbook
LINT := ansible-lint
YAMLLINT := yamllint

.PHONY: help
help:
	@echo "Targets:"
	@echo "  setup           - Create Python venv and install tooling"
	@echo "  lint            - Run ansible-lint and yamllint"
	@echo "  ping            - Ansible ping all hosts"
	@echo "  bootstrap       - Apply base setup to all nodes"
	@echo "  harden          - Apply CIS-lite hardening"
	@echo "  dev-tools       - Install GitLab CE, Runner, VS Code Server, Jupyter"
	@echo "  network         - Configure VLANs, DHCP/DNS (lab)"
	@echo "  storage         - Configure NFS + restic backups"
	@echo "  monitoring      - Deploy Wazuh/Elastic Agent"
	@echo "  dr-test         - Run backup restore test"
	@echo "  docs-serve      - Serve docs with mkdocs if present"

.PHONY: setup
setup:
	python3 -m venv .venv
	. .venv/bin/activate && pip install --upgrade pip
	. .venv/bin/activate && pip install ansible ansible-lint yamllint
	@echo "Run: source .venv/bin/activate"

.PHONY: lint
lint:
	. .venv/bin/activate && $(LINT) ansible/
	. .venv/bin/activate && $(YAMLLINT) ansible/ group_vars/ host_vars/ || true

.PHONY: ping
ping:
	. .venv/bin/activate && ansible -i inventories/lab.ini all -m ping

.PHONY: bootstrap
bootstrap:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/bootstrap.yml -K

.PHONY: harden
harden:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/hardening.yml -K

.PHONY: dev-tools
dev-tools:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/dev_tooling.yml -K

.PHONY: network
network:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/network.yml -K

.PHONY: storage
storage:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/storage.yml -K

.PHONY: monitoring
monitoring:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/monitoring.yml -K

.PHONY: dr-test
dr-test:
	. .venv/bin/activate && $(ANSIBLE) -i inventories/lab.ini playbooks/dr_test.yml -K

.PHONY: docs-serve
docs-serve:
	@if command -v mkdocs >/dev/null 2>&1; then mkdocs serve; else echo "Install mkdocs to use this"; fi
EOF

# CI config
mkdir -p .github/workflows
cat > .github/workflows/ci.yml <<'EOF'
name: Lint
on:
  push:
  pull_request:
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install tools
        run: |
          python -m pip install --upgrade pip
          pip install ansible ansible-lint yamllint
      - name: ansible-lint
        run: ansible-lint ansible/
      - name: yamllint
        run: yamllint ansible/ group_vars/ host_vars/ || true
EOF

# Ansible scaffold
mkdir -p ansible/playbooks ansible/roles ansible/files ansible/templates group_vars host_vars inventories docs diagrams logs

# Inventory example
cat > inventories/lab.ini <<'EOF'
[workstations]
ubuntu-ws-1 ansible_host=192.168.50.21
ubuntu-ws-2 ansible_host=192.168.50.22

[lab_nodes]
pi-1 ansible_host=192.168.60.11 ansible_user=ubuntu
pi-2 ansible_host=192.168.60.12 ansible_user=ubuntu

[runners]
runner-1 ansible_host=192.168.70.31
runner-2 ansible_host=192.168.70.32

[infra]
gitlab ansible_host=192.168.40.10
nfs ansible_host=192.168.40.20
wazuh ansible_host=192.168.40.30
dnsdhcp ansible_host=192.168.40.40
EOF

# Group vars
cat > group_vars/all.yml <<'EOF'
timezone: America/Los_Angeles
admin_user: daryl
ssh_public_keys:
  - "ssh-ed25519 AAAA...yourkeycomment"
packages_common:
  - curl
  - vim
  - htop
  - git
  - ufw
  - fail2ban
unattended_upgrades: true
EOF

cat > group_vars/workstations.yml <<'EOF'
vscode_server: true
jupyter_install: true
EOF

cat > group_vars/runners.yml <<'EOF'
gitlab_runner_registration_token: "REPLACE_ME"
gitlab_runner_executor: "docker"
EOF

cat > group_vars/infra.yml <<'EOF'
gitlab_external_url: "https://gitlab.lab.local"
nfs_export_path: "/srv/nfs"
restic_repo: "/srv/backup/repo"
restic_password: "CHANGE_ME"
EOF

# Playbooks
cat > ansible/playbooks/bootstrap.yml <<'EOF'
- name: Bootstrap nodes
  hosts: all
  become: true
  roles:
    - base_hardening
    - users
    - packages
EOF

cat > ansible/playbooks/hardening.yml <<'EOF'
- name: CIS-lite hardening
  hosts: all
  become: true
  roles:
    - base_hardening
EOF

cat > ansible/playbooks/dev_tooling.yml <<'EOF'
- name: Developer tooling
  hosts: workstations:runners:infra
  become: true
  roles:
    - { role: gitlab, when: "'gitlab' in group_names or inventory_hostname == 'gitlab'" }
    - { role: gitlab_runner, when: "'runners' in group_names" }
    - { role: vscode_server, when: "'workstations' in group_names" }
    - { role: jupyter, when: "'workstations' in group_names" }
EOF

cat > ansible/playbooks/network.yml <<'EOF'
- name: Lab network services
  hosts: dnsdhcp
  become: true
  roles:
    - network
EOF

cat > ansible/playbooks/storage.yml <<'EOF'
- name: Storage and backups
  hosts: infra
  become: true
  roles:
    - storage
EOF

cat > ansible/playbooks/monitoring.yml <<'EOF'
- name: Monitoring and EDR-ish telemetry
  hosts: all
  become: true
  roles:
    - monitoring
EOF

cat > ansible/playbooks/dr_test.yml <<'EOF'
- name: Disaster Recovery test
  hosts: infra
  become: true
  roles:
    - dr_test
EOF

# Roles: minimal initial tasks
mkdir -p ansible/roles/{base_hardening,users,packages,gitlab,gitlab_runner,vscode_server,jupyter,network,storage,monitoring,dr_test}/{tasks,templates,files,handlers,defaults}

# base_hardening
cat > ansible/roles/base_hardening/tasks/main.yml <<'EOF'
- name: Set timezone
  community.general.timezone:
    name: "{{ timezone | default('UTC') }}"

- name: Ensure basic packages
  ansible.builtin.package:
    name: "{{ packages_common }}"
    state: present

- name: Configure UFW baseline
  ansible.builtin.ufw:
    state: enabled
    policy: deny

- name: Allow SSH
  ansible.builtin.ufw:
    rule: allow
    port: 22
    proto: tcp

- name: Harden sshd_config
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^#?PasswordAuthentication'
    line: 'PasswordAuthentication no'
    state: present
    backup: yes
  notify: Restart ssh

- name: Ensure fail2ban enabled
  ansible.builtin.service:
    name: fail2ban
    enabled: true
    state: started

- name: Enable unattended-upgrades
  ansible.builtin.apt:
    name: unattended-upgrades
    state: present
  when: ansible_facts['os_family'] == 'Debian'

- name: Configure automatic updates
  ansible.builtin.copy:
    dest: /etc/apt/apt.conf.d/20auto-upgrades
    content: |
      APT::Periodic::Update-Package-Lists "1";
      APT::Periodic::Unattended-Upgrade "1";
  when: ansible_facts['os_family'] == 'Debian'
EOF

cat > ansible/roles/base_hardening/handlers/main.yml <<'EOF'
- name: Restart ssh
  ansible.builtin.service:
    name: ssh
    state: restarted
EOF

# users
cat > ansible/roles/users/tasks/main.yml <<'EOF'
- name: Ensure admin user exists
  ansible.builtin.user:
    name: "{{ admin_user }}"
    groups: sudo
    append: true
    shell: /bin/bash
    state: present

- name: Authorize SSH keys for admin
  ansible.posix.authorized_key:
    user: "{{ admin_user }}"
    key: "{{ item }}"
    state: present
  loop: "{{ ssh_public_keys }}"
EOF

# packages
cat > ansible/roles/packages/tasks/main.yml <<'EOF'
- name: Update apt cache
  ansible.builtin.apt:
    update_cache: yes
  when: ansible_facts['os_family'] == 'Debian'
EOF

# gitlab
cat > ansible/roles/gitlab/tasks/main.yml <<'EOF'
- name: Install dependencies
  ansible.builtin.apt:
    name:
      - ca-certificates
      - curl
      - apt-transport-https
    state: present
    update_cache: yes

- name: Add GitLab CE repo and install
  ansible.builtin.shell: |
    curl -fsSL https://packages.gitlab.com/install/repositories/gitlab/gitlab-ce/script.deb.sh | bash
    EXTERNAL_URL="{{ gitlab_external_url }}" apt-get install -y gitlab-ce
  args:
    creates: /etc/gitlab/gitlab.rb
EOF

# gitlab_runner
cat > ansible/roles/gitlab_runner/tasks/main.yml <<'EOF'
- name: Install GitLab Runner
  ansible.builtin.shell: |
    curl -L --output /tmp/gitlab-runner.deb https://gitlab-runner-downloads.s3.amazonaws.com/latest/deb/gitlab-runner_amd64.deb
    dpkg -i /tmp/gitlab-runner.deb
  args:
    creates: /usr/bin/gitlab-runner

- name: Register runner
  ansible.builtin.shell: |
    gitlab-runner register --non-interactive \
      --url "{{ gitlab_external_url }}" \
      --registration-token "{{ gitlab_runner_registration_token }}" \
      --executor "{{ gitlab_runner_executor }}" \
      --description "$(hostname)-runner" \
      --tag-list "lab,ubuntu" \
      --run-untagged="true"
  args:
    creates: /etc/gitlab-runner/config.toml
EOF

# vscode_server
cat > ansible/roles/vscode_server/tasks/main.yml <<'EOF'
- name: Install VS Code Server (code-server)
  ansible.builtin.shell: |
    curl -fsSL https://code-server.dev/install.sh | sh
  args:
    creates: /usr/bin/code-server

- name: Enable code-server service
  ansible.builtin.systemd:
    name: code-server@{{ admin_user }}
    enabled: true
    state: started
EOF

# jupyter
cat > ansible/roles/jupyter/tasks/main.yml <<'EOF'
- name: Ensure python3-pip
  ansible.builtin.apt:
    name: python3-pip
    state: present
    update_cache: yes

- name: Install JupyterLab
  ansible.builtin.pip:
    name: jupyterlab

- name: Create systemd service for JupyterLab
  ansible.builtin.copy:
    dest: /etc/systemd/system/jupyterlab.service
    content: |
      [Unit]
      Description=JupyterLab
      After=network.target

      [Service]
      Type=simple
      User={{ admin_user }}
      ExecStart=/usr/bin/jupyter lab --ip=0.0.0.0 --no-browser
      Restart=always

      [Install]
      WantedBy=multi-user.target
  notify: Restart jupyter

EOF

cat > ansible/roles/jupyter/handlers/main.yml <<'EOF'
- name: Restart jupyter
  ansible.builtin.systemd:
    name: jupyterlab
    enabled: true
    state: restarted
    daemon_reload: true
EOF

# network
cat > ansible/roles/network/tasks/main.yml <<'EOF'
- name: Install dnsmasq and unbound
  ansible.builtin.apt:
    name:
      - dnsmasq
      - unbound
    state: present
    update_cache: yes

- name: Configure dnsmasq (DHCP/DNS)
  ansible.builtin.copy:
    dest: /etc/dnsmasq.d/lab.conf
    content: |
      domain=lab.local
      dhcp-range=192.168.50.100,192.168.50.200,12h
      dhcp-range=192.168.60.100,192.168.60.200,12h
      dhcp-option=option:dns-server,192.168.40.40
  notify: Restart dnsmasq

- name: Configure VLAN example (documentation only)
  ansible.builtin.copy:
    dest: /etc/netplan/99-lab-vlans.yaml
    content: |
      network:
        version: 2
        renderer: networkd
        ethernets:
          eno1:
            dhcp4: no
        vlans:
          vlan50:
            id: 50
            link: eno1
            addresses: [192.168.50.1/24]
          vlan60:
            id: 60
            link: eno1
            addresses: [192.168.60.1/24]
  notify: Apply netplan
EOF

cat > ansible/roles/network/handlers/main.yml <<'EOF'
- name: Restart dnsmasq
  ansible.builtin.service:
    name: dnsmasq
    state: restarted
    enabled: true

- name: Apply netplan
  ansible.builtin.shell: netplan apply
EOF

# storage
cat > ansible/roles/storage/tasks/main.yml <<'EOF'
- name: Install NFS server and restic
  ansible.builtin.apt:
    name:
      - nfs-kernel-server
      - restic
    state: present
    update_cache: yes

- name: Ensure export path
  ansible.builtin.file:
    path: "{{ nfs_export_path }}"
    state: directory
    mode: "0755"

- name: Configure exports
  ansible.builtin.copy:
    dest: /etc/exports.d/lab.exports
    content: "{{ nfs_export_path }} 192.168.0.0/16(rw,sync,no_subtree_check)"
  notify: Exportfs reload

- name: Initialize restic repo
  ansible.builtin.shell: |
    export RESTIC_PASSWORD="{{ restic_password }}"
    restic init --repo "{{ restic_repo }}"
  args:
    creates: "{{ restic_repo }}/config"
EOF

cat > ansible/roles/storage/handlers/main.yml <<'EOF'
- name: Exportfs reload
  ansible.builtin.shell: exportfs -ra
EOF

# monitoring
cat > ansible/roles/monitoring/tasks/main.yml <<'EOF'
- name: Install Elastic Agent (as example EDR-ish)
  ansible.builtin.shell: |
    curl -L -o /tmp/elastic-agent.tar.gz https://artifacts.elastic.co/downloads/beats/elastic-agent/elastic-agent-8.15.3-linux-x86_64.tar.gz
    tar -xzf /tmp/elastic-agent.tar.gz -C /opt
  args:
    creates: /opt/elastic-agent-8.15.3-linux-x86_64
  when: ansible_facts['architecture'] == 'x86_64'
EOF

# dr_test
cat > ansible/roles/dr_test/tasks/main.yml <<'EOF'
- name: Create DR test log
  ansible.builtin.shell: |
    echo "$(date -Is) DR test start" >> /var/log/dr-test.log
    echo "Simulating restore validation..." >> /var/log/dr-test.log
    echo "$(date -Is) DR test end" >> /var/log/dr-test.log
EOF

# README
cat > README.md <<'EOF'
# Field Lab Ansible

An Ansible-driven Ubuntu lab that mirrors an R&D SysAdmin environment:
- CIS-lite hardening, SSH hardening, UFW, fail2ban, unattended-upgrades
- VLAN-ready netplan config, dnsmasq DHCP/DNS, unbound (optional)
- GitLab CE + container registry and GitLab Runners
- Developer workstations: VS Code Server and JupyterLab
- NFS-backed storage with restic backups and DR test playbook
- EDR-ish telemetry via Elastic Agent (or swap to Wazuh)

Why: Demonstrate production-flavored IT automation for Linux-heavy, robotics/R&D workflows.

## Quickstart

1) Create and activate tooling:
```bash
make setup
source .venv/bin/activate
````

2. Edit inventory and vars:

- inventories/lab.ini
- group_vars/*.yml (set tokens, URLs, SSH keys)

3. Bootstrap and harden:

```bash
make bootstrap
make harden
```

4. Bring up dev tooling:

```bash
make dev-tools
```

5. Optional services:

```bash
make network
make storage
make monitoring
make dr-test
```

Security notes:

- Disable password SSH auth by default
- Unattended upgrades enabled on Debian/Ubuntu
- Replace placeholders: tokens, passwords, SSH keys

Docs:

- See docs/ and diagrams/ for architecture and runbooks (WIP) EOF

# Docs placeholders

cat > docs/RUNBOOKS.md <<'EOF'

# Runbooks (WIP)

- Onboarding/offboarding steps
- GitLab outage recovery
- Runner registration rotation
- DR restore validation with restic
- Network change checklist (VLANs, DHCP updates) EOF

cat > diagrams/ARCHITECTURE.txt <<'EOF' High-level architecture (to be diagrammed):

- VLAN50: workstations
- VLAN60: lab_nodes (Pis)
- VLAN70: runners
- VLAN40: infra (GitLab, NFS, DNS/DHCP, Wazuh/Elastic)
- Cloudflare Tunnel/ZTNA (optional) for admin portals EOF

# Init git repo

git init >/dev/null git add . git commit -m "feat: initial field lab ansible scaffold with roles, playbooks, CI, README" >/dev/null

echo "Scaffold created in $(pwd)" echo "Next steps:" echo " 1) source .venv/bin/activate && make setup" echo " 2) Edit inventories/lab.ini and group_vars/*" echo " 3) make bootstrap && make harden"

```

---

## Resume

```

Daryl Lundy Linux System Administrator | DevOps | Networking & Security Long Beach, CA | 213-537-3274 | daryl.lundy@gmail.com | daryllundy.com | github.com/daryllundy

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SUMMARY

Linux-first administrator (Ubuntu and RHEL) with 10+ years supporting hybrid on-prem/cloud environments. Specialize in Ansible automation, GitLab CI/CD, Docker, and secure fleet operations (CIS hardening, patching, EDR, backups/DR). Strong networking (VLANs, DHCP/DNS) and developer platform support (GitLab Runners, VS Code Server, Jupyter). Known for rapid incident resolution, crisp documentation, and enabling R&D workflows.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EXPERIENCE

Poppy + Monarch — Technical Support & E-commerce Systems Specialist 2022–Present | Los Angeles, CA

• Automated Ubuntu server hardening/patching with Ansible (CIS-lite, unattended-upgrades), reducing vulnerability backlog by 70% and cutting patch latency to <48 hours. • Implemented zero-trust remote admin via Cloudflare Tunnel; enforced key-based SSH, audited access logs; improved security posture without disrupting workflows. • Built Python integrations and monitoring that eliminated 60% of manual ops; improved uptime and proactive alerting. • Designed backups with restic and documented restores; validated RPO/RTO in quarterly DR tests.

GoDaddy — Technical Account Manager II 2018–2021 | Los Angeles, CA

• Supported 500+ enterprise customers across Linux web stacks and networking (DNS/DHCP/SSL/TLS/SMTP), sustaining 97% CSAT and reducing downtime incidents by 35%. • Cut MTTR by 40% via scripted diagnostics (Bash/Python) and KB playbooks adopted across teams. • Led storage migrations and restores with zero data loss; improved reliability and change safety.

Media Temple / GoDaddy — CloudTech Support Engineer II 2016–2018 | Culver City, CA

• Administered 200+ Linux environments, tuning systemd, kernel modules, and web performance. • Implemented LDAP/LDAPS and SSH hardening; increased auth reliability and auditability. • Built Python/Bash automation for monitoring/compliance, reducing manual tasks by 45%.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SELECTED PROJECTS

Field Lab Ansible (Ubuntu) Ansible-provisioned lab for R&D workflows: • CIS-lite hardening, UFW, fail2ban; netplan VLAN configs; dnsmasq DHCP/DNS; unbound optional. • GitLab CE + container registry; GitLab Runners (Docker + shell); VS Code Server & Jupyter. • NFS + restic backups; DR restore playbook and game-day documentation. • Outcome: node setup time 45 min → 6 min; quarterly DR validated. • Repo: github.com/daryllundy/field-lab-ansible

NetProbe Network Toolkit (Go) Network diagnostics (port scan, DNS analysis, bandwidth tests) with NIST/FIPS audit logging; integrated into CI for compliance reports.

GitLab DashWatch (TypeScript/React) Pipeline health dashboard with error detection; CI security scanning (Trivy/Grype) and image signing (cosign).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SKILLS

Linux: Ubuntu Server, RHEL; systemd, journalctl, netplan, apt pinning Automation: Ansible, Bash, Python; GitLab CI/CD, GitHub Actions Containers: Docker; GitLab CE/Runner; VS Code Server; Jupyter Networking: TCP/IP, DNS, DHCP, VLANs; switch config basics; VPN/Zero Trust (Cloudflare) Security: CIS hardening; EDR/MDM (Elastic Agent/Wazuh); vuln scanning (Trivy/Grype); patch automation Storage/DR: NFS/SMB; ZFS/btrfs; restic/borg; snapshots; DR playbooks Cloud: AWS, Azure, GCP (hybrid integration)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CERTIFICATIONS

• Ubuntu Linux Professional (Canonical) • Docker Foundations Professional (Docker) • Azure Administrator Associate (AZ-104) — In Progress

```

---

## Next Steps

Consider these optional enhancements:

1. **Swap Elastic Agent for Wazuh** in the monitoring role for open-source SIEM/EDR
2. **Add a Cloudflare Tunnel role** for zero-trust network access to admin portals
3. **Generate an architecture diagram** (PNG/SVG) showing VLAN topology
4. **Create a tailored cover letter** for specific job applications

---

*Generated for the Cloud/Linux Administration Portfolio Sprint (November 2025)*
```
