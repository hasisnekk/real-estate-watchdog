"""
APScheduler v3 setup.

M1 stub: creates the AsyncIOScheduler with a MemoryJobStore but registers
no jobs. Jobs are registered in M3 (Komo) and later milestones.

In M3 this module will:
- Switch the jobstore to SQLAlchemyJobStore (PostgreSQL-backed)
- Register one CronTrigger job per enabled source
- Wire each job to pipeline.run_source(source_name, ...)
"""

from __future__ import annotations

import asyncpg
import redis.asyncio as aioredis
import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

from src.core.config import AppConfig, ScoringConfig

logger = structlog.get_logger(__name__)


async def setup_scheduler(
    app_cfg: AppConfig,
    scoring_cfg: ScoringConfig,
    db_pool: asyncpg.Pool,
    redis_pool: aioredis.Redis,
) -> AsyncIOScheduler:
    """
    Initialize and start the APScheduler AsyncIOScheduler.

    Returns the running scheduler instance so main.py can shut it down cleanly.
    """
    jobstores = {
        "default": MemoryJobStore(),
    }
    job_defaults = {
        "coalesce": False,
        "max_instances": 1,         # one run per source at a time
        "misfire_grace_time": 600,  # 10-minute grace period for missed fires
    }

    scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        job_defaults=job_defaults,
        timezone="UTC",
    )

    # ── M1: no jobs registered yet ────────────────────────────────────────
    # M3 will add:
    #   for source in app_cfg.enabled_sources:
    #       scheduler.add_job(
    #           pipeline.run_source,
    #           CronTrigger.from_crontab(source.schedule),
    #           id=f"source_{source.name}",
    #           kwargs={"source_name": source.name, "app_cfg": app_cfg, ...},
    #       )

    scheduler.start()
    logger.info("scheduler_started", jobs=len(scheduler.get_jobs()))

    return scheduler


async def teardown_scheduler(scheduler: AsyncIOScheduler) -> None:
    """Shut down the scheduler, waiting up to 30 seconds for in-progress jobs."""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("scheduler_stopped")
