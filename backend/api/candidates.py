"""Candidate architecture endpoints."""

from __future__ import annotations

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException

from backend.models.database import get_db
from backend.models.schemas import CandidateInfo, CandidateMetrics

router = APIRouter(tags=["candidates"])


@router.get(
    "/optimizations/{optimization_id}/candidates",
    response_model=list[CandidateInfo],
)
async def list_candidates(
    optimization_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> list[CandidateInfo]:
    """List candidates for an optimization job.

    Args:
        optimization_id: UUID of the parent optimization.
        db: Database connection dependency.

    Returns:
        List of CandidateInfo objects for the optimization.

    Raises:
        HTTPException: 404 if optimization does not exist.
    """
    cursor = await db.execute(
        "SELECT id FROM optimizations WHERE id = ?", (optimization_id,)
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Optimization not found")

    cursor = await db.execute(
        "SELECT * FROM candidates WHERE optimization_id = ? ORDER BY pareto_rank ASC",
        (optimization_id,),
    )
    rows = await cursor.fetchall()
    return [_row_to_candidate_info(row) for row in rows]


@router.get("/candidates/{candidate_id}", response_model=CandidateInfo)
async def get_candidate(
    candidate_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> CandidateInfo:
    """Get candidate details.

    Args:
        candidate_id: UUID of the candidate.
        db: Database connection dependency.

    Returns:
        CandidateInfo for the requested candidate.

    Raises:
        HTTPException: 404 if candidate not found.
    """
    cursor = await db.execute("SELECT * FROM candidates WHERE id = ?", (candidate_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Candidate not found")

    return _row_to_candidate_info(row)


def _row_to_candidate_info(row: aiosqlite.Row) -> CandidateInfo:
    """Convert a database row to a CandidateInfo.

    Args:
        row: Database row from the candidates table.

    Returns:
        Populated CandidateInfo with optional metrics.
    """
    metrics = None
    if row["accuracy_top1"] is not None:
        metrics = CandidateMetrics(
            accuracy_top1=row["accuracy_top1"],
            latency_ms=row["latency_ms"] or 0.0,
            throughput_img_s=row["throughput_img_s"] or 0.0,
            vram_gb=row["vram_gb"] or 0.0,
            flops_g=row["flops_g"] or 0.0,
        )

    return CandidateInfo(
        id=row["id"],
        optimization_id=row["optimization_id"],
        architecture=row["architecture"],
        params_m=row["params_m"],
        metrics=metrics,
        pareto_rank=row["pareto_rank"],
        is_pareto_optimal=bool(row["is_pareto_optimal"]),
    )
