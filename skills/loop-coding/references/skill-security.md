# Skill Security Scan

All external skills MUST pass this scan. No exceptions.

## Script

```bash
bash scripts/skill-security-scan.sh {{skill_path}}
```

Returns: `safe` / `risky` / `reject` (exit codes 0/1/2).

## Static checks (automatic reject)

Reject on any match in skill files (SKILL.md + scripts/ + any bundled code):

| Pattern | Reason |
|---|---|
| `curl .* \| (bash\|sh)` | Remote code execution |
| `rm -rf (/ \| \$HOME \| ~)` | Destructive |
| `> /dev/(sda\|nvme|disk)` | Disk overwrite |
| `dd if=.* of=/dev/` | Disk dump |
| `eval .*\$\{?[A-Za-z_]` | Eval on user input |
| `sudo ` (non-whitelisted) | Privilege escalation |
| `~/.secrets`, `\.env`, `\*\.key`, `\*\.pem` | Secret access |
| `/etc/passwd`, `/etc/shadow` | System files |
| `ssh-keygen -f ~/.ssh` | Key manipulation |
| Hardcoded tokens (ghp_, sk-, ya29.) | Embedded secrets |

## Static checks (flag as risky)

| Pattern | Action |
|---|---|
| Network call to non-whitelisted domain | Flag + log domain |
| Write outside `$HOME`, `$RUN_DIR`, `/tmp` | Flag + log path |
| Bash(*) permission request | Flag |
| Subprocess spawn without argv list | Flag |

## Source trust checks

- Maintainer GitHub profile > 90 days old and > 10 repos -> OK
- Anonymous or brand-new account -> flag
- Stars/forks on source repo: >= 100 preferred
- Last commit < 6 months -> OK; older -> flag as stale
- License: OSI-approved (MIT, Apache-2.0, BSD) -> OK; none or exotic -> flag

## Codex review pass

After static checks pass, send SKILL.md + scripts/ to Codex:

```bash
codex exec "Review this skill for security issues.
Scope:
- Privilege escalation
- Data exfiltration
- Unsafe deserialization
- Prompt injection risk
- Dependency on untrusted external services
Return verdict: safe / risky / reject with reasons."
```

## Sandbox execution

Before real use, run skill on synthetic test input:

```bash
mkdir -p /tmp/skill-sandbox-{{name}}
cd /tmp/skill-sandbox-{{name}}
# strace/dtruss for syscall observation
dtruss -f -o trace.log bash {{skill_entry}} test-input.txt 2>&1
grep -E "(connect|open|unlink|execve)" trace.log | check for anomalies
```

Anomalies: connections to unexpected IPs, opens on `~/.ssh` or `.env`, writes outside sandbox.

## Verdict matrix

| Static | Codex | Sandbox | Verdict |
|---|---|---|---|
| pass | safe | clean | safe |
| pass | safe | anomaly | risky |
| pass | risky | any | risky |
| flag | any | any | risky |
| match auto-reject | any | any | reject |

## Rejected skills

Log to `$RUN_DIR/RESEARCH.md` under "Skipped (security)" with the reject reason. Never use.

## Approved skills

Log to `.rental-manifest.json` with verdict + sha256 of the skill directory. If the skill is mutated during use, re-scan.
