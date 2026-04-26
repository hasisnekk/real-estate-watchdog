"""
asyncpg connection pool and custom SQL migration runner.

Migration runner behaviour:
- Creates schema_migrations table on first boot.
- Reads all *.sql files from src/db/migrations/ sorted lexicographically.
- Applies each file inside a transaction; records it in schema_migrations.
- Idempotent: already-applied migrations are skipped on subsequent starts.
- Any migration error rolls back and raises — container exits with a non-zero code.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import asyncpg
import structlog

logger = structlog.get_logger(__name__)

MIGRATIONS_DIR = Path(__file__).parent / "migrations"

# Pool is module-level so it can be imported by other modules after init.
_pool: asyncpg.Pool | None = None


async def create_pool(database_url: str) -> asyncpg.Pool:
    """Create and return the asyncpg connection pool."""
    global _pool
    _pool = await asyncpg.create_pool(
        dsn=database_url,
        min_size=2,
        max_size=10,
        command_timeout=60,
        # Ensure asyncpg uses UTC for all timestamptz values
        server_settings={"timezone": "UTC"},
    )
    logger.info("db_pool_created", min_size=2, max_size=10)
    return _pool


def get_pool() -> asyncpg.Pool:
    """Return the module-level pool (must call create_pool first)."""
    if _pool is None:
        raise RuntimeError("DB pool not initialized. Call create_pool() first.")
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("db_pool_closed")


# ---------------------------------------------------------------------------
# Migration runner
# ---------------------------------------------------------------------------


_CREATE_MIGRATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    id          SERIAL PRIMARY KEY,
    filename    VARCHAR(256) NOT NULL UNIQUE,
    applied_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


async def run_migrations(pool: asyncpg.Pool, migrations_dir: Path = MIGRATIONS_DIR) -> None:
    """
    Apply any pending SQL migration files from migrations_dir.

    Each .sql file is applied in its own transaction. If a migration fails,
    the error is re-raised and the application will not start.
    """
    async with pool.acquire() as conn:
        # Ensure the tracking table exists (idempotent DDL)
        await conn.execute(_CREATE_MIGRATIONS_TABLE)

        applied: set[str] = {
            row["filename"]
            for row in await conn.fetch(
                "SELECT filename FROM schema_migrations ORDER BY filename"
            )
        }

    migration_files = sorted(migrations_dir.glob("*.sql"))
    pending = [f for f in migration_files if f.name not in applied]

    if not pending:
        logger.info("migrations_checked", applied=len(applied), pending=0)
        return

    logger.info(
        "migrations_checked",
        applied=len(applied),
        pending=len(pending),
        files=[f.name for f in pending],
    )

    for migration_file in pending:
        sql = migration_file.read_text(encoding="utf-8")
        logger.info("migration_applying", filename=migration_file.name)

        async with pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)",
                    migration_file.name,
                )

        logger.info("migration_applied", filename=migration_file.name)
