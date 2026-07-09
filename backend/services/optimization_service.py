"""Optimization job management service."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiosqlite

from backend.models.schemas import OptimizationStatus

logger = logging.getLogger(__name__)


async def start_optimization(
    db: aiosqlite.Connection,
    job_id: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    """Start an optimization job in the background.

    Args:
        db: Database connection.
        job_id: Unique job identifier.
        config: Optimization configuration.

    Returns:
        Job status dict.
    """
    from backend.api.websocket import create_progress_callback
    from backend.core.optimizer import OptimizationOrchestrator

    await db.execute(
        "UPDATE optimizations SET status = ?, current_phase = ? WHERE id = ?",
        (OptimizationStatus.RUNNING.value, "search", job_id),
    )
    await db.commit()

    orchestrator = OptimizationOrchestrator(optimization_id=job_id, config=config)
    callback = create_progress_callback(job_id)

    asyncio.create_task(
        _run_optimization_background(orchestrator, db, job_id, callback)
    )

    return {"job_id": job_id, "status": "running"}


async def _run_optimization_background(
    orchestrator: Any,
    db: aiosqlite.Connection,
    job_id: str,
    callback: Any,
) -> None:
    """Run optimization in background and update DB on completion."""
    try:
        result = await orchestrator.run(progress_callback=callback)
        status = OptimizationStatus.COMPLETED
        if result.get("status") == "cancelled":
            status = OptimizationStatus.CANCELLED
        await db.execute(
            "UPDATE optimizations SET status = ?, current_phase = NULL WHERE id = ?",
            (status.value, job_id),
        )
        await db.commit()
        logger.info("Optimization %s finished with status %s", job_id, status.value)
    except Exception:
        logger.exception("Optimization %s failed", job_id)
        await db.execute(
            "UPDATE optimizations SET status = ?, current_phase = NULL WHERE id = ?",
            (OptimizationStatus.FAILED.value, job_id),
        )
        await db.commit()


async def cancel_optimization(db: aiosqlite.Connection, job_id: str) -> bool:
    """Cancel a running optimization job.

    Args:
        db: Database connection.
        job_id: Job to cancel.

    Returns:
        True if cancellation was requested, False if not found.
    """
    from backend.core.optimizer import cancel_optimization as cancel_opt

    was_cancelled = cancel_opt(job_id)
    if not was_cancelled:
        return False

    await db.execute(
        "UPDATE optimizations SET status = ? WHERE id = ?",
        (OptimizationStatus.CANCELLED.value, job_id),
    )
    await db.commit()
    return True
