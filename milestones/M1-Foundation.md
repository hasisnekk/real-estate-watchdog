# Milestone 1 — Foundation

**Status**: Complete  
**Phase**: Phase 1 (No Apify, No External Cost)  
**Goal**: Docker Compose skeleton, config loading, DB migrations, structlog, full async entry point

---

## What Was Built

Milestone 1 establishes every piece of infrastructure the application depends on. Nothing functional (scraping, notifications) runs yet — this milestone's sole purpose is to prove the skeleton boots, connects to the database, runs migrations, and can be rebuilt on any machine.

### 1. Project Layout

The complete folder structure defined in the spec was created, including all stub modules for Phase 2 adapters (Apify, Azorim, Ashtrom). Every stub is importable Python with a clear `NotImplementedError` so future milestones simply fill in the body.

```
real-estate-watchdog/
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── Makefile
├── requirements.txt
├── config/
│   ├── default.yaml          ← full search config for your apartment search
│   └── scoring.yaml          ← all scoring weights and thresholds
├── src/
│   ├── main.py               ← asyncio.run(main()) — boots the full system
│   ├── scheduler.py          ← APScheduler stub (populated in M3)
│   ├── pipeline.py           ← pipeline orchestrator stub (populated in M2)
│   ├── adapters/             ← all adapter stubs created
│   ├── core/
│   │   ├── config.py         ← dynaconf + pydantic config loader + full schema
│   │   ├── models.py         ← RawListing + Listing pydantic v2 models
│   │   └── ...               ← normalizer/filter/dedup/scoring stubs
│   └── db/
│       ├── connection.py     ← asyncpg pool + custom migration runner
│       ├── repository.py     ← DB operations stub (populated in M3)
│       └── migrations/
│           ├── 001_initial.sql       ← full 7-table schema
│           └── 002_enrichment_cache.sql
├── scripts/
│   ├── backup.sh
│   ├── restore.sh
│   └── migrate.sh
├── tests/                    ← test stubs (populated in M2)
└── data/                     ← runtime data directories (bind-mounted)
    ├── seed/
    ├── spool/
    ├── logs/
    └── backups/
```

### 2. Configuration System

**Two-layer config**: dynaconf reads `config/default.yaml` + `config/scoring.yaml`, then overlays secrets from `.env` and environment variables. The raw dynaconf settings are immediately validated by pydantic v2, producing typed `AppConfig` and `ScoringConfig` objects. The application fails fast at startup if any required field is missing or has a wrong type.

**Key config sections** (all with defaults, fully overridable):
- `search.*` — transaction type, budget, rooms, must-haves, city list, sources
- `enrichment.*` — gov enrichment toggles and cache TTL
- `notifications.discord.*` — webhook URLs (injected from env vars), thresholds, batching
- `persistence.*` — raw payload and image URL flags
- `scoring.*` — all point values, thresholds, formulas

**Infra secrets** (not in YAML, always from env):
- `DATABASE_URL` — set by docker-compose from postgres vars
- `REDIS_URL` — set by docker-compose
- `DISCORD_*_WEBHOOK_URL` — set by `.env` via `env_file`
- `APIFY_API_TOKEN` — set by `.env`

### 3. Database Schema (7 tables, applied via migration runner)

| Table | Purpose |
|---|---|
| `listings` | Core listing data, scores, enrichment, status |
| `listing_snapshots` | One previous snapshot per listing (for change detection) |
| `listing_events` | Full event log (first_seen, price_dropped, etc.) |
| `source_runs` | Per-run tracking for circuit breaker and ops visibility |
| `dedup_matches` | Cross-source duplicate links |
| `notification_queue` | Batching queue for normal-priority Discord messages |
| `enrichment_cache` | Address → building-age result cache (1-week TTL) |

The migration runner (`src/db/connection.py::run_migrations`) is custom and lightweight:
1. Creates `schema_migrations` table on first run
2. Reads all `*.sql` files from `src/db/migrations/` sorted by name
3. Applies each file in a transaction, records it in `schema_migrations`
4. On subsequent startups, skips already-applied migrations
5. Any migration failure rolls back and aborts startup (fail-fast)

### 4. Async Entry Point (`src/main.py`)

Full startup sequence matching the spec:

```
asyncio.run(main())
  ├─ setup_logging()               → structlog to stdout + file
  ├─ load_config()                 → dynaconf + pydantic validation
  ├─ create_pool()                 → asyncpg pool (min=2, max=10)
  ├─ run_migrations()              → apply pending SQL files
  ├─ create_redis_pool()           → redis.asyncio connection pool
  ├─ asyncio.create_task(          → spool recovery (stub in M1, active in M3)
  │     spool_recovery_loop())
  ├─ setup_scheduler()             → APScheduler AsyncIOScheduler (no jobs in M1)
  └─ run_forever() with SIGTERM/SIGINT handler for graceful shutdown
```

Graceful shutdown (30-second grace period):
1. Stop accepting new scheduler jobs
2. Wait for in-progress jobs to finish (up to 30s)
3. Cancel spool recovery task
4. Close DB pool
5. Close Redis pool

### 5. structlog Configuration

Output: **JSON to both stdout and `/app/data/logs/watchdog.json`** (daily rotation).

Every log entry carries:
```json
{
  "timestamp": "2026-04-26T10:00:00.000Z",
  "level": "info",
  "event": "watchdog_started",
  "source": null,
  "run_id": null
}
```

Log levels follow the spec:
- `DEBUG` — raw adapter data (dev only)
- `INFO` — listing processed, run start/end, notifications
- `WARNING` — dedup collision, cache miss, soft limit
- `ERROR` — source failure, DB write failure, Discord failure

### 6. Docker Compose Setup

Three services with health checks:
- **`db`** — PostgreSQL 16 Alpine, bind-mount to `/home/viko/real-estate-watchdog/postgres/data`
- **`redis`** — Redis 7 Alpine, RDB persistence every 60 seconds
- **`watchdog`** — Python 3.12-slim, depends on db+redis health checks, bind-mounts spool + logs + config

The `watchdog` service uses `build: .` in development and can be switched to a pre-loaded image tag for VPN-restricted servers.

---

## External Setup Required (Do This Before Running)

### Step 1 — Verify Docker is Installed on the RHEL Server

```bash
docker --version
docker compose version
```

Expected: Docker 24+ and Compose v2. If missing:

```bash
# On RHEL 9.6
sudo dnf install -y docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and back in for group change to take effect
```

### Step 2 — Create the Runtime Data Directories on the Server

These are bind-mounted into the containers. Create them before `docker compose up`:

```bash
mkdir -p /home/viko/real-estate-watchdog/postgres/data
mkdir -p /home/viko/real-estate-watchdog/redis
mkdir -p /home/viko/real-estate-watchdog/spool
mkdir -p /home/viko/real-estate-watchdog/logs
mkdir -p /home/viko/real-estate-watchdog/backups
```

No `sudo` needed — everything lives in your home directory and is already owned by `viko`.

### Step 3 — Push to GitHub (from Windows) and Pull on the Server

This is the standard workflow: commit on Windows → push to GitHub → pull on the server. No file copying needed.

**A. Create the GitHub repository** (one-time setup):

Go to [github.com/new](https://github.com/new) and create a new **private** repository named `real-estate-watchdog`. Do NOT initialize it with a README (the repo already has files).

**B. Push from your Windows machine** (PowerShell):

```powershell
cd "c:\Users\vtov\git_repos\real-estate-watchdog"

# Connect your local repo to GitHub (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/real-estate-watchdog.git

# Stage everything and make the first commit
git add .
git commit -m "Milestone 1: Foundation — Docker, config, DB migrations, async entrypoint"

# Push to GitHub
git push -u origin main
```

**C. Clone on the server** (SSH into the server):

```bash
# Clone the repo into the app directory
git clone https://github.com/YOUR_USERNAME/real-estate-watchdog.git /home/viko/real-estate-watchdog/app

# Verify
ls /home/viko/real-estate-watchdog/app/
# Should show: Dockerfile  Makefile  config/  docker-compose.yml  requirements.txt  src/  ...
```

**D. For all future changes** — the workflow is always:

```powershell
# On Windows: commit and push
git add .
git commit -m "your message"
git push
```

```bash
# On the server: pull and restart
cd /home/viko/real-estate-watchdog/app
git pull
docker compose restart watchdog   # or 'docker compose up -d --build' if Dockerfile changed
```

### Step 4 — Create the `.env` File (Never Commit This)

```bash
cd /home/viko/real-estate-watchdog/app
cp .env.example .env
```

Edit `.env` with your actual values:

```bash
nano .env
```

Fill in at minimum:
```
POSTGRES_PASSWORD=your_strong_password_here
```

The Discord and Apify values can be left as placeholders for M1 — they are not used yet. You will fill them in during M3 (Discord) and M5 (Apify).

### Step 5 — Build the Docker Image

**Option A — Server has internet access (PyPI not blocked)**:

```bash
cd /home/viko/real-estate-watchdog/app
docker compose build
```

Watch for any `pip install` errors. If it succeeds, proceed to Running Milestone 1.

**Option B — PyPI is blocked by VPN on the server (build on Windows, transfer only the image)**:

The project code is already on the server via `git pull`. The only thing you can't do on the server is `pip install` (PyPI blocked). Solution: build the Docker image on your Windows laptop and transfer just the image tarball.

On your Windows machine (with Docker Desktop installed):

```powershell
cd "c:\Users\vtov\git_repos\real-estate-watchdog"

# Build the image locally (your laptop has open internet)
docker build -t real-estate-watchdog:latest .

# Save it as a compressed tarball
docker save real-estate-watchdog:latest | gzip > watchdog.tar.gz

# Transfer only the image tarball to the server (~200–400 MB)
scp watchdog.tar.gz viko@YOUR_SERVER:/home/viko/real-estate-watchdog/app/
```

Then on the server:

```bash
cd /home/viko/real-estate-watchdog/app

# Load the pre-built image (no internet needed)
docker load < watchdog.tar.gz

# Edit docker-compose.yml: swap 'build: .' for 'image: real-estate-watchdog:latest'
nano docker-compose.yml
```

---

## Running Milestone 1

### Start All Services

```bash
cd /home/viko/real-estate-watchdog/app

# Start DB and Redis first, wait for health checks
docker compose up -d db redis

# Wait ~15 seconds for PostgreSQL to be ready, then start the app
docker compose up -d watchdog
```

Or start everything at once (docker compose will wait for healthchecks):

```bash
docker compose up -d
```

### Verify It's Working

```bash
# Check all containers are running and healthy
docker compose ps

# Stream logs from the watchdog app
docker compose logs -f watchdog

# Expected log output (JSON):
# {"timestamp": "...", "level": "info", "event": "watchdog_starting"}
# {"timestamp": "...", "level": "info", "event": "config_loaded", "sources_enabled": 1}
# {"timestamp": "...", "level": "info", "event": "db_pool_created", "min_size": 2, "max_size": 10}
# {"timestamp": "...", "level": "info", "event": "migrations_checked", "applied": 2, "pending": 0}
# {"timestamp": "...", "level": "info", "event": "redis_connected"}
# {"timestamp": "...", "level": "info", "event": "scheduler_started", "jobs": 0}
# {"timestamp": "...", "level": "info", "event": "watchdog_started"}
```

### Verify the Database Schema

```bash
# Open a psql session inside the DB container
docker compose exec db psql -U watchdog watchdog

# Inside psql, list tables:
\dt

# Expected output:
#  Schema |        Name         | Type  |  Owner
# --------+---------------------+-------+---------
#  public | dedup_matches       | table | watchdog
#  public | enrichment_cache    | table | watchdog
#  public | listing_events      | table | watchdog
#  public | listing_snapshots   | table | watchdog
#  public | listings            | table | watchdog
#  public | notification_queue  | table | watchdog
#  public | schema_migrations   | table | watchdog
#  public | source_runs         | table | watchdog

# Check which migrations were applied:
SELECT filename, applied_at FROM schema_migrations ORDER BY filename;

# Exit psql
\q
```

### Makefile Commands

```bash
make up           # docker compose up -d
make down         # docker compose down
make logs         # docker compose logs -f watchdog
make shell        # open bash shell inside watchdog container
make db-shell     # open psql inside db container
make build        # docker compose build
make build-remote # instructions for building on external machine (see Makefile)
make status       # show container status
```

---

## Verification Checklist

- [ ] `docker compose ps` shows all 3 containers as `healthy` or `running`
- [ ] `docker compose logs -f watchdog` shows `watchdog_started` event (no errors)
- [ ] `\dt` in psql shows all 8 tables (7 + `schema_migrations`)
- [ ] `schema_migrations` table has 2 rows (`001_initial.sql`, `002_enrichment_cache.sql`)
- [ ] No `ERROR` lines in logs
- [ ] Stopping and restarting the watchdog container (`docker compose restart watchdog`) does NOT re-apply migrations (idempotent)

---

## What Is NOT Done Yet (Coming in M2)

- No listing pipeline (normalizer, filter, scoring) — stubs only
- No data flows through the system — the app boots and idles
- No adapters are active — all `enabled: false` or stub implementations
- No Discord notifications
- No deduplication logic

---

## Architecture Decisions Made in M1

| Decision | Choice | Reason |
|---|---|---|
| Migration system | Custom SQL runner (not Alembic) | Simpler, no extra tooling, full control; Alembic can replace it later if needed |
| DB driver | asyncpg only | Fastest async PostgreSQL driver; APScheduler jobstore uses MemoryJobStore in M1 to avoid needing psycopg2 |
| Config system | dynaconf + pydantic v2 | dynaconf handles YAML + env layering; pydantic gives typed schema and fails fast |
| Logging | structlog JSON | Structured, async-safe, machine-readable; Docker stdout carries it for `docker compose logs` |
| Spool recovery | Background asyncio.Task | Decoupled from scheduler; wakes every 300s; started in M1 as no-op stub |
| Scheduler jobstore | MemoryJobStore (M1) | SQLAlchemy jobstore added in M3 after DB is proven stable |
