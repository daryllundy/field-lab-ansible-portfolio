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
	. .venv/bin/activate && pip install ansible ansible-lint yamllint molecule molecule-docker pytest-testinfra
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

.PHONY: test
test:
	. .venv/bin/activate && cd ansible/roles/base_hardening && molecule test
	. .venv/bin/activate && cd ansible/roles/users && molecule test
	. .venv/bin/activate && cd ansible/roles/packages && molecule test
