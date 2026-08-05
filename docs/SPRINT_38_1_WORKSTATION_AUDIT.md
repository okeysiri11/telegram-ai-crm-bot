# Sprint 38.1 — Developer Workstation Foundation
# Phase 1 — Full Development Environment Audit

**Mode:** Inspect only — **no changes made**  
**Host:** `macbook`  
**Project:** `/Users/macbook/Desktop/TelegramBotCourse` (ADOS Enterprise OS)  
**Audit date:** 2026-08-04  

**Legend**

| Symbol | Meaning |
|--------|---------|
| ✔ | Installed / OK |
| ⚠ | Missing or incomplete (needed for ADOS) |
| ⬆ | Needs update |
| ❌ | Problem / risk |

---

## 1. Operating System

| Item | Value | Status |
|------|-------|--------|
| Product | macOS Ventura | ✔ |
| Version | **13.5** (Build 22G74) | ⬆ available **13.7.8** |
| Architecture | **Intel x86_64** (not Apple Silicon) | ✔ (supported) |
| CPU | Intel Core i5-7267U @ 3.10GHz (**2C/4T**) | ❌ undersized for monorepo |
| RAM | **8 GB** physical | ❌ critical bottleneck |
| Free RAM at audit | ~148 MB unused; heavy compressor/swap | ❌ memory pressure |
| Load average | **10.3 / 18.9 / 12.0** on 4 logical CPUs | ❌ overloaded |
| Disk | 233 GB APFS; **~141 GB free** (~8% used on system volume) | ✔ storage OK |
| Safari update | 18.6 available | ⬆ |
| Xcode CLT | 14.3.1 | ⬆ newer CLT available (brew doctor) |
| Homebrew support | macOS 13 = **Tier 3** (unsupported) | ⚠ |

### Recommendation

This machine can do light API/docs work, but **full ADOS stack** (Postgres + Redis + API + Vite web + kernel + Cursor AI indexing) will thrash 8 GB RAM. Prefer ≥16 GB RAM (ideally 32 GB) or offload Docker DB/Redis to a remote/dev VM.

---

## 2. Development Tools

| Tool | Version / Path | Status |
|------|----------------|--------|
| Git | 2.55.0 → `/usr/local/bin/git` | ✔ |
| Homebrew | 6.0.13 → `/usr/local/bin/brew` | ✔ / ⬆ outdated formulae |
| Python 3 | **3.14.6** (Homebrew) | ✔ / ⚠ very new — pin CI carefully |
| `python` symlink | Missing (only `python3`) | ⚠ |
| pip3 | 26.1.2 | ✔ |
| uv | Not installed | ⚠ recommended |
| Node.js | **v24.18.0** | ✔ / ⚠ engines say `>=20`; prefer LTS 22 for stability |
| npm | 11.16.0 | ✔ |
| pnpm | Missing | ⚠ optional |
| Yarn | Missing | ⚠ optional (not required) |
| Docker Desktop | **Not installed** | ❌ P0 for local `dev:infra` |
| Docker Compose | Missing (no Docker) | ❌ |
| kubectl | Missing | ⚠ P2 (needed for k8s deploys later) |
| gh (GitHub CLI) | **Missing** | ❌ P0 for PR/Actions workflow |
| OpenSSL | 3.6.3 (Homebrew) | ✔ |
| Java | `/usr/bin/java` stub only — **no JRE/JDK** | ⚠ unless needed |
| Go | Missing | ⚠ optional |
| Rust / Cargo | Missing | ⚠ optional |
| pyenv | Missing | ⚠ optional if brew Python OK |
| poetry | Missing | ⚠ project uses pip/venv |
| nvm | Missing | ⚠ optional; brew Node is global |

**Homebrew outdated:** `ca-certificates`, `cmake`, `pkgconf`, `sqlite`, `visual-studio-code`  

**brew doctor highlights**

- ❌ Broken symlinks: `/usr/local/bin/cursor`, `/usr/local/bin/obsidian`
- ⚠ Unbrewed headers in `/usr/local/include/node/*`
- ⬆ Command Line Tools update recommended
- ⚠ macOS 13 Tier 3

---

## 3. Cursor Environment

| Item | Finding | Status |
|------|---------|--------|
| Cursor app location | **`/Users/macbook/Desktop/Cursor.app`** (not `/Applications`) | ⚠ nonstandard |
| Cursor version | **3.13.21** | ✔ |
| `/Applications/Cursor.app` | Absent | ⚠ |
| User settings | Minimal (smart commit, no minimap, TS server 1024 MB, GPU accel off) | ✔ tuned for low RAM |
| Workspace `.vscode/settings.json` | Strong excludes/watcher excludes for venv/node_modules | ✔ excellent for 8 GB |
| Extensions | `anysphere.remote-ssh` 1.1.13; `anthropic.claude-code` 2.1.221 (+ stale 2.1.220 dir) | ✔ / ⚠ cleanup stale ext |
| AI models configured | Not visible in `settings.json` (Cursor account/UI models) | ⚠ verify in Cursor Settings → Models |
| Indexing | Workspace excludes reduce index load | ✔ |
| Project `.cursor/rules` | `ados-core`, `ados-architecture`, `ados-orchestrator` | ✔ |
| Memories | Agent transcripts present (~6); no separate Memories dump audited | ✔ |
| MCP configuration | Project `mcps/` folder **empty** | ⚠ no MCP servers wired |
| Automations / hooks | No `hooks.json` in repo; skills present under `~/.cursor/skills-cursor` | ✔ skills / ⚠ no project hooks |
| Plans | `~/.cursor/plans/sprint_33.1_ux_foundation_*.plan.md` | ✔ |
| Cursor cache | `~/.cursor` ≈ **766 MB**; ShipIt cache **2.4 GB** under Library/Caches | ⬆ cleanup candidate |

---

## 4. Git

| Item | Value | Status |
|------|-------|--------|
| user.name | `okeysiri11` | ✔ |
| user.email | `166515048+okeysiri11@users.noreply.github.com` | ✔ |
| credential.helper | `osxkeychain` | ✔ HTTPS auth |
| init.defaultBranch | **unset** globally | ⚠ set to `main` |
| Remote | `https://github.com/okeysiri11/telegram-ai-crm-bot.git` | ✔ |
| Current branch | `2026-07-24-u42q` (ahead 3 of origin) | ⚠ |
| Dirty working tree | **~1300** porcelain entries (large uncommitted 37.x surface) | ❌ release risk |
| SSH to GitHub | `Host key verification failed` / **no `~/.ssh` directory** | ❌ no SSH keys |

---

## 5. GitHub

| Item | Status |
|------|--------|
| Remote repo reachable via HTTPS naming | ✔ `okeysiri11/telegram-ai-crm-bot` |
| `gh` CLI | ❌ not installed — cannot audit auth/Actions/Codespaces from CLI |
| GitHub Actions in repo | ✔ `.github/workflows/architecture.yml`, `knowledge-validation.yml` |
| Codespaces | ⚠ unknown without `gh`; not required for local ADOS |
| Authentication | Likely HTTPS + macOS Keychain (no SSH) | ⚠ verify with `gh auth login` after install |

---

## 6. Python Environment

| Item | Status |
|------|--------|
| System/Homebrew Python | ✔ 3.14.6 |
| Project `.venv` | ✔ ~129 MB — primary (pytest used this in prior sprints) |
| Project `venv/` | ⚠ **duplicate** ~116 MB; `package.json` scripts call `./venv/bin/python` |
| Global pip packages | ⚠ alembic, asyncpg, SQLAlchemy installed **globally** — prefer venv-only |
| pip cache | ~30 MB | ✔ modest |
| uv | ⚠ missing — faster installs/locks recommended |
| pyenv / poetry | ⚠ missing (optional) |

---

## 7. Node Environment

| Item | Status |
|------|--------|
| Node | ✔ v24.18.0 |
| npm | ✔ 11.16.0 |
| Global npm pkgs | ✔ only `npm`, `corepack` |
| pnpm / yarn / nvm | ⚠ missing (optional) |
| `src/web/node_modules` | ~145 MB | ✔ |
| `src/kernel/node_modules` | ~51 MB | ✔ |
| `platform_console/node_modules` | ~150 MB | ✔ |
| Root `package.json` | ✔ multi-package orchestration; `dev:infra` needs Docker |

---

## 8. Docker

| Item | Status |
|------|--------|
| Docker Desktop / daemon | ❌ **not installed** |
| Compose | ❌ |
| Images / containers / volumes / networks | ❌ N/A |
| Impact | `npm run dev:infra` (`docker compose up -d postgres redis`) **cannot run locally** |

---

## 9. Terminal

| Item | Status |
|------|--------|
| Login shell | ✔ `/bin/zsh` |
| `~/.zprofile` | ✔ `eval "$(/usr/local/bin/brew shellenv zsh)"` |
| `~/.zshrc` | ⚠ only adds `$HOME/.local/bin` — minimal |
| Aliases | ⚠ none defined |
| PATH issues | ❌ Non-login / Cursor agent shells sometimes **omit brew** → tools appear “missing” until `brew shellenv` |
| Interactive load | High system load may make terminal feel slow | ❌ hardware |

---

## 10. Security

| Item | Status |
|------|--------|
| SSH keys | ❌ **no `~/.ssh` directory** |
| GPG | ❌ not installed / no signing keys |
| Git credentials | ✔ osxkeychain helper |
| Stored tokens | ⚠ Keychain may hold GitHub HTTPS tokens — rotate if shared machine |
| `.env` | ✔ present; **gitignored** |
| `.env.example` | ✔ |
| `.env.production` | ❌ **NOT gitignored** — risk if real secrets exist and get committed |
| Repo `.gitignore` | ⚠ minimal (`.env`, venvs, pyc, DS_Store only) — expand for secrets/caches |
| Do not print secret values | ✔ audit did not dump `.env` contents |

---

## 11. Project Structure (TelegramBotCourse / ADOS)

| Area | Finding | Status |
|------|---------|--------|
| Architecture | Layered `platform_*`, `applications/`, `api/`, `src/web`, `src/kernel` | ✔ SoR pattern |
| Top-level directories | **~113** | ⚠ crowded root |
| Docs | `docs/` ~**1462** markdown files | ⚠ doc sprawl / navigation debt |
| Tests | Many `tests/test_*.py`; certification suites 37.x | ✔ |
| CI | 2 workflows only | ⚠ thin vs platform size |
| Scripts | `scripts/` present (dev, security, alembic helpers) | ✔ |
| Config | `config.py`, `alembic.ini`, compose files, `.cursor/rules` | ✔ |
| Dual legacy | `database_legacy.py` (~350 KB), many `*_handlers.py` at root | ⚠ legacy surface |
| Obsidian vault | `.obsidian/` in repo | ⚠ prefer out of tree or ignore |
| Uncommitted work | Massive dirty tree incl. Sprint 37.x certification | ❌ must commit/stabilize before RC tag |

---

## 12. Performance

| Item | Finding | Status |
|------|---------|--------|
| Free disk | ~141 GB | ✔ |
| Largest user areas | `~/Library` 41G; Desktop 2.9G; project ~1.0G | ✔ |
| Caches | Library/Caches **5.0G** (Cursor ShipIt 2.4G, VS Code ShipIt 875M, Homebrew 622M, Playwright 457M, npm 365M) | ⬆ cleanup |
| Dual venvs | ~245 MB combined | ⚠ consolidate |
| Docker disk | N/A (not installed) | — |
| Homebrew cleanup | Broken symlinks reported | ⬆ `brew cleanup` |
| Runtime fitness | 8 GB + high load + swap | ❌ primary workstation constraint |

---

## Priority backlog

### P0 — Blockers for a proper ADOS workstation

1. **Install Docker Desktop** (or Colima + docker CLI) so Postgres/Redis via Compose works.  
2. **Install GitHub CLI (`gh`)** and authenticate.  
3. **Stabilize Git working tree** (commit or stash Sprint 37.x) before any `v1.0.0-rc1` tag.  
4. **Fix `.env.production` gitignore** (and audit whether file contains real secrets).  
5. **Address RAM pressure** — close heavy apps; do not run full stack + Cursor indexing concurrently without relief; plan hardware upgrade.

### P1 — Required soon

1. Create `~/.ssh` keys **or** standardize on HTTPS + `gh auth`; fix GitHub host key / SSH path.  
2. Unify Python venv: pick `.venv` **or** `venv` and align `package.json` scripts.  
3. Install **uv**; keep dependencies in project venv only; remove global alembic/SQLAlchemy if unused.  
4. Update macOS **13.5 → 13.7.8** and Xcode CLT.  
5. `brew upgrade` outdated formulae; `brew cleanup` broken `cursor`/`obsidian` symlinks.  
6. Move Cursor.app to `/Applications` (or fix brew symlink intentionally).  
7. Expand `.gitignore` (`.env.*` except example, caches, `.obsidian` optional).  
8. Wire MCP servers if required for ADOS tooling (folder currently empty).  
9. Prefer Node **22 LTS** for day-to-day stability (optional nvm).  

### P2 — Optimize / optional

1. Install kubectl when approaching cluster deploys.  
2. pnpm (optional) for stricter monorepo installs.  
3. GPG commit signing.  
4. Clear ShipIt / Playwright caches when disk needed.  
5. Reduce docs sprawl / root handler clutter (architecture hygiene).  
6. Add CI jobs: pytest critical path, kernel vitest, secret scan.  
7. Java/Go/Rust only if a specific module needs them.  

---

## Sprint 38.1 — Step-by-step execution plan

> Execute in order. **Do not start until Phase 1 report is accepted.**  
> This plan is the recommended sequence for install / update / configure / remove / optimize.

### Step 0 — Preconditions (human)

1. Confirm backup/Time Machine.  
2. Close Chrome/Electron extras to free RAM.  
3. Decide: stay on this Mac (mitigate) vs move primary work to ≥16 GB machine.

### Step 1 — OS & CLT updates

1. Install **macOS 13.7.8** (Software Update).  
2. Install Safari 18.6.  
3. Update **Command Line Tools** (Xcode 15.2 CLT per brew doctor, or latest for Ventura).  
4. Reboot; re-check `sw_vers` and free memory.

### Step 2 — Homebrew hygiene

1. `brew update`  
2. `brew upgrade` (ca-certificates, cmake, pkgconf, sqlite, …)  
3. `brew cleanup` (remove broken `cursor` / `obsidian` symlinks)  
4. Review `/usr/local/include/node` headers (remove only if confirmed leftover junk).  
5. Ensure login shells always load `brew shellenv` (already in `.zprofile`).

### Step 3 — Core CLI for ADOS

1. `brew install gh` → `gh auth login` (HTTPS or SSH).  
2. Install **Docker Desktop for Mac (Intel)** → enable Compose → start daemon.  
3. Verify: `docker info`, `docker compose version`.  
4. From repo: `docker compose up -d postgres redis` (or project’s `dev:infra`).  
5. Optional: `brew install uv kubectl`.

### Step 4 — Git / secrets hygiene

1. Set `git config --global init.defaultBranch main`.  
2. Either generate SSH key + add to GitHub **or** document HTTPS-only workflow.  
3. Add `.env.production` (and `.env.*` pattern) to `.gitignore`; keep `.env.example` tracked.  
4. Rotate any secrets that may have been at risk.  
5. Plan commit strategy for ~1300 dirty files (feature branches / RC commit) — **no force-push**.

### Step 5 — Python toolchain

1. Choose single venv path (recommend **`.venv`**).  
2. Update root scripts that call `./venv/bin/python` → `.venv`.  
3. Remove or archive unused `venv/` after confirming parity.  
4. Install **uv**; recreate lock/install into `.venv` from `requirements.txt`.  
5. Uninstall global pip packages that belong in the project (`alembic`, `asyncpg`, `SQLAlchemy`) if not needed system-wide.

### Step 6 — Node toolchain

1. Keep npm; optionally install **nvm** and Node **22 LTS** for ADOS.  
2. Re-run `npm install` at root / `src/web` / `src/kernel` / `platform_console` as needed.  
3. Confirm `engines.node` policy in docs.

### Step 7 — Cursor configuration

1. Move `Desktop/Cursor.app` → `/Applications/Cursor.app` (optional but cleaner).  
2. Remove stale extension folder `anthropic.claude-code-2.1.220-*`.  
3. Verify Models (Cloud / API keys) in Cursor UI.  
4. Keep low-RAM settings (TS server 1024, GPU off, excludes).  
5. Configure MCP servers under project if team requires Datadog/GitHub/etc.  
6. Optionally add Cursor hooks for format/test gates.  
7. Clear old ShipIt caches if disk reclaim needed.

### Step 8 — Shell DX

1. Extend `~/.zshrc` with safe aliases (`gs`, `gc`, `pytest`, `ados-venv`).  
2. Ensure Cursor integrated terminal is a **login shell** or sources brew.  
3. Document required env vars in README (no secret values).

### Step 9 — Project / CI optimization

1. Expand `.gitignore`.  
2. Add CI workflow for critical pytest + kernel vitest.  
3. Document workstation requirements (RAM, Docker, Python, Node) in `docs/developer_guide.md`.  
4. Schedule Homebrew/cache cleanup monthly.

### Step 10 — Verification gate (end of 38.1)

| Check | Pass criteria |
|-------|----------------|
| `docker compose ps` | postgres + redis healthy |
| `gh auth status` | logged in |
| `.venv` pytest smoke | critical suite green |
| `npm run test --prefix src/kernel` | vitest green |
| Git | SSH or HTTPS auth OK; secrets ignored |
| Cursor | opens project; rules load; terminal sees brew tools |

---

## Summary scorecard

| Domain | Grade | Notes |
|--------|-------|-------|
| OS | ⚠ | Ventura 13.5, updates pending; Tier 3 brew |
| Hardware | ❌ | 8 GB / dual-core insufficient for full stack |
| Core languages | ✔ | Python 3.14 + Node 24 present |
| Containers | ❌ | No Docker |
| GitHub tooling | ❌ | No `gh`; no SSH |
| Cursor | ✔ | Present & RAM-tuned; MCP empty |
| Project | ⚠ | Rich platform; dirty tree; thin CI; doc sprawl |
| Security posture | ⚠ | `.env` ignored; `.env.production` not; no SSH/GPG |

**Bottom line:** Tooling for Python/Node/Git exists, but the workstation is **not production-dev ready** until Docker + `gh` + git/secrets hygiene + RAM strategy are fixed. Hardware is the hard ceiling.

---

*End of Phase 1 audit — no modifications were applied to the system or repository.*
