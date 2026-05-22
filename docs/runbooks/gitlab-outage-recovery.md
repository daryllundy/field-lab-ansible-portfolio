# GitLab CE Outage Recovery

**Severity:** P1 — GitLab is unavailable for the lab (blocks CI, blocks code review)
**Owner:** infra on-call
**Estimated time:** 15–60 minutes depending on root cause
**Last tested:** not yet — this runbook is a portfolio sample

---

## When to use this runbook

Use this runbook when one or more of the following are true:

- `https://gitlab.lab.local` returns 502 / 503 / connection refused / timeout
- `git push` / `git clone` against the lab GitLab hangs or fails with TLS or auth errors
- Runners appear offline in the Admin → Runners page despite the runner hosts being up
- CI pipelines stick in `pending` for more than 5 minutes

Do **not** use this runbook for:

- A single failing pipeline (check the job log, not GitLab itself)
- A specific project's repo being corrupted (different procedure)
- LDAP / SSO auth issues when other GitLab functions work (auth runbook, not this one)

---

## Preconditions

Before starting:

- SSH access to the `gitlab` host (`192.168.40.10`) as a sudoer
- The vault password to decrypt `group_vars/infra/vault.yml` if you need restic
- 30+ minutes of focused time — do **not** start the restore-from-backup branch with less
- A second person reachable (Slack / phone) in case you need to escalate or hand off

---

## Diagnose before you act

**Do not restart anything until you've done all five diagnostic steps.** Restarting a flapping service before you understand why it's flapping is how 15-minute outages become 2-hour outages.

Set a 15-minute timer. If you can't identify the failure mode by the time it expires, skip ahead to **Restore from backup** and start the senior on-call.

### 1. Confirm the symptom externally

```bash
# From a workstation, not the gitlab host:
curl -fsS -o /dev/null -w "HTTP %{http_code} in %{time_total}s\n" https://gitlab.lab.local/-/health
```

Expected: `HTTP 200 in <1s`. If you get a non-200 or a timeout, the outage is real.

### 2. Check process state on the host

```bash
ssh gitlab
sudo gitlab-ctl status
```

Healthy output: every line shows `run: <name>: (pid xxxx) Ns; run: log: (pid xxxx) Ns` with `N` matching across services and growing over time.

Note down any service that shows `down`, `respawning` (pid changing each time you re-run), or has an uptime under 60 seconds while others are at hours/days.

### 3. Check disk space

```bash
df -h /var/opt/gitlab /var/log /tmp /
```

GitLab Omnibus is exceptionally sensitive to disk. If `/var/opt/gitlab` is over 90% full, jump to **Disk full** below — most "GitLab is down" reports trace to this.

### 4. Check the most recent logs

```bash
sudo gitlab-ctl tail | head -200
```

Look for, in roughly decreasing order of frequency:

- `No space left on device` → **Disk full**
- `could not connect to server`, `FATAL: the database system is starting up` → **Database**
- `puma worker timeout`, `Killing puma worker` → **Memory pressure / app crash**
- `SSL_CTX_use_certificate`, `certificate has expired` → **TLS**
- `502 Bad Gateway` from nginx logs → **Reverse proxy / upstream**

### 5. Check the host itself

```bash
uptime              # high load?
free -h             # OOM territory? swap thrashing?
sudo journalctl -u gitlab-runsvdir -n 50 --no-pager
```

---

## Decision tree

Based on diagnosis, jump to the matching section:

| Diagnosis | Section |
|-----------|---------|
| Disk >90% full on `/var/opt/gitlab` | [Disk full](#disk-full) |
| One or more services down or respawning, disk OK | [Service crash](#service-crash) |
| All services green but UI returns 502 | [Reverse proxy / TLS](#reverse-proxy--tls) |
| Postgres errors in logs | [Database recovery](#database-recovery) |
| Host pingable, GitLab port unreachable | [Network](#network) |
| Unknown after 15 minutes | [Restore from backup](#restore-from-backup-last-resort) |

---

## Disk full

Most common cause. Reclaim in this order — stop at the first one that frees enough:

```bash
# 1. Expire old GitLab job artifacts (safe, automatic if scheduled but often disabled)
sudo gitlab-rake gitlab:cleanup:orphan_job_artifact_files DRY_RUN=true
# If the dry-run output looks reasonable:
sudo gitlab-rake gitlab:cleanup:orphan_job_artifact_files

# 2. Rotate and compress logs
sudo gitlab-ctl cleanse-logs
sudo find /var/log/gitlab -name "*.log.*" -mtime +14 -delete

# 3. Prune old container registry blobs (only if registry is in use)
sudo gitlab-ctl registry-garbage-collect -m

# 4. Last resort: expire CI artifacts older than 30 days
sudo gitlab-rake "gitlab:cleanup:expired_job_artifacts[30]"
```

After each step, re-run `df -h /var/opt/gitlab`. Once you're under 80%, restart impacted services:

```bash
sudo gitlab-ctl restart puma sidekiq
```

If you can't get under 90% without deleting recent data, you have a capacity problem — grow the disk before declaring the incident resolved.

---

## Service crash

If a specific service is down/respawning:

```bash
# Get its recent log
sudo gitlab-ctl tail <service> | tail -100

# Try a clean restart of just that service
sudo gitlab-ctl restart <service>

# Wait 30s, then re-check
sudo gitlab-ctl status | grep <service>
```

If the service won't stay up after one restart, run a full reconfigure (this rewrites configs from `/etc/gitlab/gitlab.rb`):

```bash
# ALWAYS take a snapshot of /etc/gitlab first
sudo cp -a /etc/gitlab /etc/gitlab.bak.$(date +%Y%m%d-%H%M%S)
sudo gitlab-ctl reconfigure
```

Reconfigure takes 3–8 minutes. Do **not** interrupt it. If it fails partway, the error message above the traceback is the actionable bit — read it, do not just re-run.

---

## Reverse proxy / TLS

If `gitlab-ctl status` is fully green but the UI returns 502:

```bash
# Test nginx → puma path directly
sudo curl -fsS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8080/-/health

# Check nginx error log
sudo tail -50 /var/log/gitlab/nginx/gitlab_error.log

# Check TLS cert expiry
sudo openssl x509 -in /etc/gitlab/ssl/gitlab.lab.local.crt -noout -dates
```

Common fixes:

- Cert expired → renew, then `sudo gitlab-ctl restart nginx`
- nginx config syntax error → fix `/etc/gitlab/gitlab.rb`, then `sudo gitlab-ctl reconfigure`
- Puma not actually listening on 8080 → see **Service crash**

---

## Database recovery

Postgres errors usually mean either (a) postgres is wedged or (b) the database is corrupted.

```bash
# Stop everything except postgres
sudo gitlab-ctl stop unicorn puma sidekiq nginx

# Confirm postgres is healthy
sudo gitlab-ctl status postgresql
sudo gitlab-psql -d gitlabhq_production -c '\dt' | head

# If postgres is up and \dt works, restart the app:
sudo gitlab-ctl start
```

If postgres is **not** up, do **not** run `gitlab-ctl reconfigure` — it will not fix a corrupted PG cluster and may make it worse. Go to **Restore from backup**.

---

## Network

If the host responds to ping but GitLab's port (443) is unreachable:

```bash
# From the gitlab host, verify nginx is listening
ss -tnlp | grep -E ':80|:443'

# From a workstation, verify routing
traceroute -n gitlab.lab.local

# Check UFW didn't get reset
ssh gitlab "sudo ufw status numbered"
```

If UFW is blocking 443: `sudo ufw allow 443/tcp` and re-test. If `ss` shows nothing listening on 443: nginx didn't start — see **Service crash**.

---

## Restore from backup (last resort)

Only do this when:

- You've spent 15+ minutes diagnosing without finding root cause, AND
- You've notified the senior on-call, AND
- You have a `restic` snapshot tagged `gitlab` from before the outage

```bash
# 1. List available snapshots
ssh gitlab
export RESTIC_PASSWORD=$(ansible-vault view group_vars/infra/vault.yml --vault-password-file .vault_pass | grep vault_restic_password | cut -d'"' -f2)
restic -r /srv/backup/repo snapshots --tag gitlab

# 2. Stop GitLab fully
sudo gitlab-ctl stop

# 3. Move (do not delete) the current data — you may need it for forensics
sudo mv /var/opt/gitlab/backups /var/opt/gitlab/backups.broken.$(date +%Y%m%d-%H%M%S)
sudo mv /var/opt/gitlab/git-data /var/opt/gitlab/git-data.broken.$(date +%Y%m%d-%H%M%S)

# 4. Restore from the chosen snapshot
restic -r /srv/backup/repo restore <snapshot-id> --target /

# 5. Re-apply ownership (restic preserves but Omnibus is picky)
sudo gitlab-ctl reconfigure

# 6. Run the included GitLab backup restore (the restic snapshot contains
#    GitLab's own backup tarball under /var/opt/gitlab/backups/)
sudo gitlab-backup restore BACKUP=<timestamp-of-tarball>
```

The `gitlab-backup restore` step will prompt twice for confirmation. Read each prompt — they will overwrite the database and the secrets file.

---

## Verify

After **any** mitigation, run all of these in order. Do not declare the incident resolved until all pass.

```bash
# 1. All services up and stable for 60+ seconds
sudo gitlab-ctl status
sleep 60 && sudo gitlab-ctl status

# 2. GitLab self-check
sudo gitlab-rake gitlab:check SANITIZE=true

# 3. Web UI returns 200 from outside the host
curl -fsS -o /dev/null -w "%{http_code}\n" https://gitlab.lab.local/-/health
# Expected: 200

# 4. A runner picks up a job
# Trigger a pipeline on a smoke-test project. Expect green within 2 minutes.
# If runners don't pick up jobs, see the (not-yet-written) Runner Registration runbook.
```

If any step fails, you have **not** resolved the incident.

---

## Rollback

If your mitigation made things worse and you took the snapshot in **Service crash** step 2, you can roll back the config:

```bash
sudo gitlab-ctl stop
sudo rm -rf /etc/gitlab
sudo mv /etc/gitlab.bak.<timestamp> /etc/gitlab
sudo gitlab-ctl reconfigure
sudo gitlab-ctl start
```

For data rollback after a bad restore: the `.broken.<timestamp>` directories from **Restore from backup** step 3 still contain the pre-restore state.

---

## After the incident

Within 24 hours:

- [ ] Write a postmortem covering: timeline, root cause, contributing factors, mitigation, prevention
- [ ] If disk was the cause: schedule capacity review for `/var/opt/gitlab`
- [ ] If a service crashed: file a bug with the relevant log excerpt
- [ ] Update this runbook's **Last tested** date
- [ ] If a step in this runbook was wrong, fix it — runbook drift is how 3am incidents go bad

---

## Common mistakes to avoid

- Running `gitlab-ctl reconfigure` as the first action — masks root cause and can take 8 minutes you don't have
- Restarting postgres while a backup is in progress — corrupts the backup
- Force-killing puma workers (`gitlab-ctl kill puma`) instead of restart — leaves orphaned sockets
- Deleting `/var/opt/gitlab/backups/*.tar` to reclaim disk — that's your DR
- Editing files under `/var/opt/gitlab/` directly — they get overwritten on next reconfigure; edit `/etc/gitlab/gitlab.rb` instead

---

## Related

- [GitLab Omnibus troubleshooting docs](https://docs.gitlab.com/omnibus/troubleshooting.html)
- `ansible/roles/gitlab/` — Ansible role that installs GitLab CE
- `ansible/roles/storage/` — NFS + restic backup config
- `group_vars/infra/vault.yml` — restic password (encrypted)
