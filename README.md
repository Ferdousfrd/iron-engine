# Project Iron Engine ⚔️

An autonomous, cloud-native media processing and distribution infrastructure. Built to automate content synthesis, audio/video assembly, and multi-platform publishing for the **Iron North** historical media channel.

---

## Architecture Overview


[Phase 1: Node Hardening & Diagnostics] ──► [Phase 2: Historical DB & LLM Engine]
│                                         │
▼                                         ▼
[Phase 5: Automated Social Deployment] ◄── [Phase 4: Docker & n8n Orchestration] ◄── [Phase 3: Programmatic FFmpeg Engine]

---

## Phase 1: Infrastructure Security & Node Health Monitoring

This phase establishes a secured, headless Linux server node with automated monitoring daemons.

### 1. Hardware & System Baseline
* **Host Platform:** Dedicated x86_64 Node (Ubuntu 24.04.3 LTS)
* **Access Model:** Headless administration via encrypted SSH keys (Ed25519)
* **Power Policy:** Configured systemd-logind (`HandleLidSwitch=ignore`) for continuous headless runtime

### 2. Network Security Hardening (UFW)
A strict packet-filtering firewall strategy adhering to the Principle of Least Privilege:
* **Default Policies:** `DENY` incoming, `ALLOW` outgoing
* **Rules:**
  * Port `22/tcp` (SSH management)
  * Port `80/tcp` (HTTP reverse proxy / webhooks)
  * Port `443/tcp` (HTTPS TLS encrypted endpoints)

### 3. Automated Health Daemon (`sys_guard.sh`)
Located in `scripts/sys_guard.sh`, this Bash script runs on an automated cron schedule to monitor hardware constraints before triggering heavy media tasks:
* **Storage Protection:** Evaluates root disk partition (`/`) via `df` and `awk`. Alerts if utilization exceeds 80%.
* **Memory Pressure:** Tracks real-time RAM usage and alerts if consumption exceeds 85%.
* **Load Average:** Monitors 1-minute system load averages via `uptime`.
* **Logging:** Writes structured ISO-8601 timestamps to `logs/sys_guard.log`.

---

## Repository Structure

```text
iron-engine/
├── .gitignore          # Excludes logs, secrets, and raw video assets
├── README.md           # Engineering and deployment documentation
├── config/             # Environment variables and service configuration
├── data/               # Local staging directory for generated media (gitignored)
├── logs/               # Runtime logs from background daemons (gitignored)
└── scripts/
    └── sys_guard.sh    # Production node health monitoring daemon

Save and exit: `Ctrl + O`, `Enter`, and `Ctrl + X`.

---


