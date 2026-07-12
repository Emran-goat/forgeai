"""Optimization job management endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from uuid import uuid4

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.models.database import get_db
from backend.models.schemas import (
    OptimizationCreate,
    OptimizationResponse,
    OptimizationStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["optimizations"])

_active_tasks: dict[str, asyncio.Task[None]] = {}


async def _run_optimization_background(
    optimization_id: str,
    config: dict,
) -> None:
    """Execute optimization in background and update DB on completion.

    Args:
        optimization_id: ID of the optimization to run.
        config: Configuration dict for the orchestrator.
    """
    from backend.core.optimizer import OptimizationOrchestrator
    from backend.models.database import get_db

    db = await get_db()
    try:
        orchestrator = OptimizationOrchestrator(optimization_id, config)
        result = await orchestrator.run()

        final_status = "completed" if result["status"] == "completed" else "failed"
        await db.execute(
            "UPDATE optimizations SET status = ?, current_phase = NULL WHERE id = ?",
            (final_status, optimization_id),
        )
        await db.commit()

        if result.get("candidates"):
            for cand in result["candidates"]:
                cand_id = cand.get("id", str(uuid4()))
                metrics = cand.get("metrics")
                await db.execute(
                    "INSERT OR REPLACE INTO candidates "
                    "(id, optimization_id, architecture, params_m, accuracy_top1, "
                    "latency_ms, throughput_img_s, vram_gb, flops_g, pareto_rank, is_pareto_optimal) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        cand_id,
                        optimization_id,
                        cand.get("architecture", "unknown"),
                        cand.get("params_m", 0.0),
                        metrics.get("accuracy_top1") if metrics else None,
                        metrics.get("latency_ms") if metrics else None,
                        metrics.get("throughput_img_s") if metrics else None,
                        metrics.get("vram_gb") if metrics else None,
                        metrics.get("flops_g") if metrics else None,
                        cand.get("pareto_rank"),
                        1 if cand.get("is_pareto_optimal") else 0,
                    ),
                )
            await db.commit()

        logger.info("Optimization %s finished: %s", optimization_id, result["status"])

    except Exception:
        logger.exception("Optimization %s failed unexpectedly", optimization_id)
        try:
            await db.execute(
                "UPDATE optimizations SET status = 'failed' WHERE id = ?",
                (optimization_id,),
            )
            await db.commit()
        except Exception:
            logger.exception("Failed to update DB for failed optimization %s", optimization_id)
    finally:
        _active_tasks.pop(optimization_id, None)


@router.post("/optimizations", response_model=OptimizationResponse, status_code=201)
async def create_optimization(
    request: OptimizationCreate,
    db: aiosqlite.Connection = Depends(get_db),
) -> OptimizationResponse:
    """Start a new optimization job.

    Creates the job in DB and starts the optimization pipeline in background.

    Args:
        request: Optimization creation parameters.
        db: Database connection dependency.

    Returns:
        OptimizationResponse with initial job status.

    Raises:
        HTTPException: 404 if referenced model does not exist.
    """
    cursor = await db.execute("SELECT id FROM models WHERE id = ?", (request.model_id,))
    model_row = await cursor.fetchone()
    if model_row is None:
        raise HTTPException(status_code=404, detail="Model not found")

    job_id = str(uuid4())
    now = datetime.now(timezone.utc).isoformat()

    constraints_json = json.dumps(request.constraints.model_dump())
    objectives_json = json.dumps(request.objectives)
    search_space_json = json.dumps(request.search_space.model_dump())

    await db.execute(
        "INSERT INTO optimizations "
        "(id, model_id, hardware_target, status, total_phases, current_phase, "
        "constraints, objectives, search_space, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            job_id,
            request.model_id,
            request.hardware_target.value,
            OptimizationStatus.QUEUED.value,
            7,
            None,
            constraints_json,
            objectives_json,
            search_space_json,
            now,
        ),
    )
    await db.commit()

    config = {
        "model_id": request.model_id,
        "hardware_target": request.hardware_target.value,
        "constraints": request.constraints.model_dump(),
        "objectives": request.objectives,
        "search_space": request.search_space.model_dump(),
    }

    task = asyncio.create_task(_run_optimization_background(job_id, config))
    _active_tasks[job_id] = task

    logger.info("Created optimization %s for model %s", job_id, request.model_id)

    return OptimizationResponse(
        id=job_id,
        status=OptimizationStatus.QUEUED,
        created_at=datetime.fromisoformat(now),
        hardware_target=request.hardware_target.value,
        total_phases=7,
        current_phase=None,
    )


@router.get("/optimizations", response_model=list[OptimizationResponse])
async def list_optimizations(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[OptimizationResponse]:
    """List all optimization jobs, newest first.

    Args:
        db: Database connection dependency.

    Returns:
        List of OptimizationResponse objects.
    """
    cursor = await db.execute("SELECT * FROM optimizations ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [_row_to_optimization_response(row) for row in rows]


@router.get("/optimizations/{job_id}", response_model=OptimizationResponse)
async def get_optimization(
    job_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> OptimizationResponse:
    """Get optimization job status.

    Args:
        job_id: UUID of the optimization job.
        db: Database connection dependency.

    Returns:
        OptimizationResponse for the requested job.

    Raises:
        HTTPException: 404 if job not found.
    """
    cursor = await db.execute("SELECT * FROM optimizations WHERE id = ?", (job_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Optimization not found")

    return _row_to_optimization_response(row)


@router.delete("/optimizations/{job_id}", status_code=204, response_class=Response)
async def cancel_optimization(
    job_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> Response:
    """Cancel a running optimization job.

    Sets the cancellation flag so the next phase boundary raises
    CancellationError, and updates the DB status to 'cancelled'.

    Args:
        job_id: UUID of the optimization to cancel.
        db: Database connection dependency.

    Raises:
        HTTPException: 404 if job not found or already completed.
    """
    cursor = await db.execute(
        "SELECT id, status FROM optimizations WHERE id = ?", (job_id,)
    )
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Optimization not found")

    current_status = row["status"]
    if current_status in (OptimizationStatus.COMPLETED.value, OptimizationStatus.FAILED.value):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot cancel optimization in '{current_status}' status",
        )

    from backend.core.optimizer import cancel_optimization as cancel_opt

    cancel_opt(job_id)

    task = _active_tasks.pop(job_id, None)
    if task and not task.done():
        task.cancel()

    await db.execute(
        "UPDATE optimizations SET status = ?, current_phase = NULL WHERE id = ?",
        (OptimizationStatus.CANCELLED.value, job_id),
    )
    await db.commit()

    logger.info("Cancelled optimization %s", job_id)
    return Response(status_code=204)


def _row_to_optimization_response(row: aiosqlite.Row) -> OptimizationResponse:
    """Convert a database row to an OptimizationResponse.

    Args:
        row: Database row from the optimizations table.

    Returns:
        Populated OptimizationResponse.
    """
    current_phase = row["current_phase"]
    return OptimizationResponse(
        id=row["id"],
        status=OptimizationStatus(row["status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        hardware_target=row["hardware_target"],
        total_phases=row["total_phases"],
        current_phase=current_phase,
    )
