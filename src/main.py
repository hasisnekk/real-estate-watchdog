"""
Real-Estate Watchdog — async entry point.

Startup sequence:
  1. Configure structlog
  2. Load and validate config (dynaconf + pydantic)
  3. Create asyncpg connection pool
  4. Run DB migrations
  5. Create Redis connection pool
  6. Start spool recovery background task
  7. Start APScheduler (jobs registered by scheduler.py)
  8. Run until SIGINT/SIGTERM → graceful shutdown (30s grace period)
"""

from __future__ import annotations

import asyncio
import logging
import logging.handlers
import signal
import sys
from pathlib import Path

import structlog
import redis.asyncio as aioredis

from src.core.config import load_config
from src.db.connection import create_pool, close_pool, run_migrations
from src.scheduler import setup_scheduler, teardown_scheduler

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# structlog setup
# ---------------------------------------------------------------------------


def setup_logging(log_level: str = "info", log_file: Path | None = None) -> None:
    """
    Configure structlog for JSON output.
    Writes to stdout (captured by docker compose logs) and optionally a file.
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]

    if log_file is not None:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.handlers.TimedRotatingFileHandler(
            filename=str(log_file),
            when="midnight",
            backupCount=7,
            encoding="utf-8",
        )
        handlers.append(file_handler)

    logging.basicConfig(
        format="%(message)s",
        level=level,
        handlers=handlers,
        force=True,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


# ---------------------------------------------------------------------------
# Spool recovery background task (stub — logic added in M3)
# ---------------------------------------------------------------------------


async def spool_recovery_loop() -> None:
    """
    Background task: wakes every 300 seconds and replays any pending JSONL spool files.
    Spool files are written when DB writes fail; this loop replays them when the DB
    becomes available again.

    Full implementation in Milestone 3. This stub just logs that it's running.
    """
    spool_dir = Path("data/spool")
    spool_dir.mkdir(parents=True, exist_ok=True)

    while True:
        await asyncio.sleep(300)
        spool_files = list(spool_dir.glob("failed_*.jsonl"))
        if spool_files:
            logger.warning(
                "spool_files_pending",
                count=len(spool_files),
                note="Full replay logic implemented in M3",
            )


# ---------------------------------------------------------------------------
# Main coroutine
# ---------------------------------------------------------------------------


async def main() -> None:
    # ── 1. Load config ─────────────────────────────────────────────────────
    app_cfg, scoring_cfg, infra_cfg = load_config()

    # ── 2. Configure logging ───────────────────────────────────────────────
    setup_logging(
        log_level=infra_cfg.log_level,
        log_file=Path("data/logs/watchdog.json"),
    )

    logger.info("watchdog_starting", version="1.0.0")

    enabled_sources = app_cfg.enabled_sources
    logger.info(
        "config_loaded",
        sources_enabled=len(enabled_sources),
        source_names=[s.name for s in enabled_sources],
        transaction_type=app_cfg.search.transaction_type,
    )

    # ── 3. Create DB pool ──────────────────────────────────────────────────
    db_pool = await create_pool(infra_cfg.database_url)

    # ── 4. Run DB migrations ───────────────────────────────────────────────
    await run_migrations(db_pool)

    # ── 5. Create Redis pool ───────────────────────────────────────────────
    redis_pool = aioredis.from_url(
        infra_cfg.redis_url,
        encoding="utf-8",
        decode_responses=True,
        max_connections=10,
    )
    # Verify Redis is reachable
    await redis_pool.ping()
    logger.info("redis_connected", url=infra_cfg.redis_url)

    # ── 6. Start spool recovery background task ────────────────────────────
    spool_task = asyncio.create_task(spool_recovery_loop(), name="spool_recovery")

    # ── 7. Start APScheduler ───────────────────────────────────────────────
    scheduler = await setup_scheduler(
        app_cfg=app_cfg,
        scoring_cfg=scoring_cfg,
        db_pool=db_pool,
        redis_pool=redis_pool,
    )

    logger.info("watchdog_started")

    # ── 8. Run until shutdown signal ───────────────────────────────────────
    stop_event = asyncio.Event()

    def _handle_signal(sig: signal.Signals) -> None:
        logger.info("shutdown_signal_received", signal=sig.name)
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _handle_signal, sig)
        except (NotImplementedError, OSError):
            # Windows does not support add_signal_handler for all signals
            pass

    await stop_event.wait()

    # ── Graceful shutdown (30-second grace period) ─────────────────────────
    logger.info("watchdog_shutting_down")

    await teardown_scheduler(scheduler)

    spool_task.cancel()
    try:
        await asyncio.wait_for(spool_task, timeout=5.0)
    except (asyncio.CancelledError, asyncio.TimeoutError):
        pass

    await redis_pool.aclose()
    logger.info("redis_disconnected")

    await close_pool()

    logger.info("watchdog_stopped")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    asyncio.run(main())
