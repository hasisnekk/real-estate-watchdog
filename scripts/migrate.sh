#!/bin/bash
# migrate.sh — manually apply pending SQL migrations
# The application also runs migrations automatically at startup.
# Use this script when you want to apply migrations without restarting the app
# (e.g., adding a new index or table while the app is running).

set -euo pipefail

echo "[$(date -u +%FT%TZ)] Running migrations via watchdog container..."

docker compose exec watchdog python -c "
import asyncio
from src.core.config import load_config
from src.db.connection import create_pool, run_migrations

async def run():
    _, _, infra = load_config()
    pool = await create_pool(infra.database_url)
    await run_migrations(pool)
    await pool.close()
    print('Migrations complete.')

asyncio.run(run())
"

echo "[$(date -u +%FT%TZ)] Done."
