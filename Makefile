SHELL := /bin/bash
ANSIBLE := ansible-playbook
LINT := ansible-lint
YAMLLINT := yamllint

.PHONY: help
help:
	@echo "Targets:"
	@echo "  setup           - Create Python venv and install tooling using uv"
	@echo "  lint            - Run ansible-lint and yamllint"
	@echo "  ping            - Ansible ping all hosts"
	@echo "  bootstrap       - Apply base setup to all nodes"
	@echo "  harden          - Apply CIS-lite hardening"
	@echo "  dev-tools       - Install GitLab CE, Runner, VS Code Server, Jupyter"
	@echo "  network         - Configure VLANs, DHCP/DNS (lab)"
	@echo "  storage         - Configure NFS + restic backups"
	@echo "  monitoring      - Deploy Wazuh/Elastic Agent"
	@echo "  dr-test         - Run backup restore test"
	@echo "  test            - Run Molecule tests for all roles"
	@echo "  docs-serve      - Serve docs with mkdocs if present"

.PHONY: setup
setup:
	uv venv
	uv pip install .
	@echo "Run: source .venv/bin/activate"

.PHONY: lint
lint:
	uv run $(LINT) ansible/
	uv run $(YAMLLINT) ansible/ group_vars/ host_vars/ || true

.PHONY: ping
ping:
	uv run ansible -i inventories/lab.ini all -m ping

.PHONY: bootstrap
bootstrap:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/bootstrap.yml -K

.PHONY: harden
harden:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/hardening.yml -K

.PHONY: dev-tools
dev-tools:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/dev_tooling.yml -K

.PHONY: network
network:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/network.yml -K

.PHONY: storage
storage:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/storage.yml -K

.PHONY: monitoring
monitoring:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/monitoring.yml -K

.PHONY: dr-test
dr-test:
	uv run $(ANSIBLE) -i inventories/lab.ini playbooks/dr_test.yml -K

.PHONY: docs-serve
docs-serve:
	@if command -v mkdocs >/dev/null 2>&1; then mkdocs serve; else echo "Install mkdocs to use this"; fi

.PHONY: test
test:
	uv run bash -c "cd ansible/roles/base_hardening && molecule test"
	uv run bash -c "cd ansible/roles/users && molecule test"
	uv run bash -c "cd ansible/roles/packages && molecule test"
	uv run bash -c "cd ansible/roles/gitlab && molecule test"
	uv run bash -c "cd ansible/roles/gitlab_runner && molecule test"
	uv run bash -c "cd ansible/roles/vscode_server && molecule test"
	uv run bash -c "cd ansible/roles/jupyter && molecule test"
	uv run bash -c "cd ansible/roles/network && molecule test"
	uv run bash -c "cd ansible/roles/storage && molecule test"
	uv run bash -c "cd ansible/roles/monitoring && molecule test"
	uv run bash -c "cd ansible/roles/dr_test && molecule test"
