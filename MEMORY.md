# MEMORY.md

Decision log for this project. Read at session start. Append (don't rewrite) after any significant decision. Never contradict a logged decision without flagging it first.

Format per entry:

```
## YYYY-MM-DD — <short title>

**Decided:** <what>
**Why:** <reason>
**Rejected:** <alternative> — <why not>
```

---

## 2026-05-21 — Ansible Vault for secrets

**Decided:** Split `group_vars/<group>/` into `vars.yml` (plaintext refs) + `vault.yml` (AES256 encrypted). Secrets referenced as `{{ vault_* }}` from vars.yml.
**Why:** Standard Ansible pattern; vars.yml stays readable in diffs while real secrets are encrypted; demo vault password (`labvault`) is documented for portfolio reviewers.
**Rejected:** Plaintext `CHANGE_ME` placeholders — too easy for a hiring manager to read as "didn't bother with vault."

## 2026-05-21 — Multi-tag per task

**Decided:** Every task gets at least one tag; common pattern is `[specific, broad-parent]` e.g. `[firewall, security]`.
**Why:** Lets operators target either way (`--tags firewall` for narrow changes, `--tags security` for sweeps).
**Rejected:** Single-tag-per-task — too restrictive in practice.

## 2026-05-21 — hardening.yml expanded inline rather than as a new role

**Decided:** `hardening.yml` now runs `base_hardening` role plus inline sysctl + auditd tasks, rather than collapsing into base_hardening or creating a new `cis_hardening` role.
**Why:** The sysctl/auditd work is intentionally only triggered by `make harden`, not by `make bootstrap`. Keeping it in the playbook (not the role) preserves that separation. A separate role would be over-decomposed for the volume of work.
**Rejected:** Folding into `base_hardening` — would force sysctl/auditd on every bootstrap. Creating a `cis_hardening` role — premature abstraction.

## 2026-05-21 — RESUME.md stays gitignored

**Decided:** `RESUME.md` is not tracked in git, even though this is a portfolio project. Reference to it removed from CLAUDE.md/AGENTS.md.
**Why:** User preference. Resume lives on the filesystem for personal reference but is out of scope for the public repo.
**Rejected:** Tracking it for hiring-manager discoverability — explicit user preference overrides.

## 2026-05-21 — Squash merge for cleanup branch

**Decided:** Squashed all 13 cleanup-branch commits into one on `main` (plus a follow-up commit removing `docs/design.md`).
**Why:** Clean public history for a portfolio repo. Granular commits are preserved locally if needed; main shows the net intent.
**Rejected:** Fast-forward merge — would have surfaced two "auto-commit: task X completed" hook commits on main.

## 2026-05-22 — `logs/` directory kept with `.gitkeep`

**Decided:** Keep `logs/` tracked via `.gitkeep`; add a `%-logged` pattern Make target that tees output to `logs/<target>-<timestamp>.log`.
**Why:** The empty directory was previously dead code. Now it's load-bearing — Make targets actually use it. `.gitignore` rewritten as `logs/*` + `!logs/.gitkeep` so contents stay untracked.
**Rejected:** Removing the directory — would have lost optionality and required `mkdir -p` in the Make target.
