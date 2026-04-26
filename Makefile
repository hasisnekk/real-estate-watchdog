.PHONY: up down logs shell db-shell build rebuild status \
        backup restore spool-replay \
        build-remote load-image \
        test lint

# ── Local / Server helpers ─────────────────────────────────────────────────────

## Start all services in detached mode
up:
	docker compose up -d

## Stop all services (keeps volumes)
down:
	docker compose down

## Stream logs from the watchdog container
logs:
	docker compose logs -f watchdog

## Open an interactive bash shell inside the watchdog container
shell:
	docker compose exec watchdog bash

## Open psql inside the DB container
db-shell:
	docker compose exec db psql -U watchdog watchdog

## Build the Docker image (requires internet for pip install)
build:
	docker compose build

## Force rebuild without layer cache
rebuild:
	docker compose build --no-cache

## Show status of all containers
status:
	docker compose ps

# ── VPN / Offline Build Workflow ───────────────────────────────────────────────
# Use when PyPI is blocked by VPN on the deployment server.
# Run 'make build-remote' on your laptop (has internet), then transfer + load.

## Instructions for building on an external machine (prints commands to run on laptop)
build-remote:
	@echo "Run these commands on your laptop (not the server):"
	@echo ""
	@echo "  docker build -t real-estate-watchdog:latest ."
	@echo "  docker save real-estate-watchdog:latest | gzip > watchdog.tar.gz"
	@echo "  scp watchdog.tar.gz viko@YOUR_SERVER:/home/viko/real-estate-watchdog/"
	@echo ""
	@echo "Then on the server, run: make load-image"

## Load a pre-built image tarball (run on the server after 'make build-remote')
load-image:
	@echo "Loading image from /home/viko/real-estate-watchdog/watchdog.tar.gz ..."
	docker load < /home/viko/real-estate-watchdog/watchdog.tar.gz
	@echo "Done. Edit docker-compose.yml: change 'build: .' to 'image: real-estate-watchdog:latest'"

# ── Data Operations ────────────────────────────────────────────────────────────

## Run a manual database backup now
backup:
	bash scripts/backup.sh

## Restore from the most recent backup (or pass BACKUP_FILE=path/to/file.sql.gz)
restore:
	bash scripts/restore.sh $(BACKUP_FILE)

## Replay any pending JSONL spool files into the database
spool-replay:
	docker compose exec watchdog python -c "import asyncio; from src.db.spool import replay_spool_files; asyncio.run(replay_spool_files())"

# ── Testing ────────────────────────────────────────────────────────────────────

## Run all tests inside Docker
test:
	docker compose exec watchdog python -m pytest tests/ -v

## Run a single source manually (e.g.: make run-source source=csv_seed)
run-source:
	docker compose exec watchdog python -c \
	  "import asyncio; from src.pipeline import run_source_once; asyncio.run(run_source_once('$(source)'))"

# ── Lint ───────────────────────────────────────────────────────────────────────
lint:
	docker compose exec watchdog python -m py_compile src/main.py src/core/config.py src/db/connection.py
	@echo "Syntax check passed."
