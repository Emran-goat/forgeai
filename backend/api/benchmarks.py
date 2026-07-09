"""Benchmark result endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import aiosqlite
from fastapi import APIRouter, Depends, Query

from backend.config import settings
from backend.core.fireworks_client import FireworksClient, FireworksConfig
from backend.models.database import get_db
from backend.models.schemas import BenchmarkResult, ParetoPoint

router = APIRouter(tags=["benchmarks"])


@router.get("/benchmarks", response_model=list[BenchmarkResult])
async def list_benchmarks(
    hardware: str | None = Query(default=None, description="Filter by hardware target"),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[BenchmarkResult]:
    """Query benchmark results with optional hardware filter.

    Args:
        hardware: Optional hardware target to filter by.
        db: Database connection dependency.

    Returns:
        List of BenchmarkResult objects matching the filter.
    """
    if hardware:
        cursor = await db.execute(
            "SELECT * FROM benchmarks WHERE hardware_target = ? ORDER BY created_at DESC",
            (hardware,),
        )
    else:
        cursor = await db.execute("SELECT * FROM benchmarks ORDER BY created_at DESC")

    rows = await cursor.fetchall()
    return [
        BenchmarkResult(
            id=row["id"],
            candidate_id=row["candidate_id"],
            hardware_target=row["hardware_target"],
            latency_ms=row["latency_ms"],
            throughput_img_s=row["throughput_img_s"],
            vram_gb=row["vram_gb"],
            flops_g=row["flops_g"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


@router.get("/benchmarks/pareto", response_model=list[ParetoPoint])
async def get_pareto_frontier(
    optimization_id: str = Query(..., description="Optimization ID to query"),
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ParetoPoint]:
    """Get Pareto frontier candidates for an optimization.

    Returns candidates marked as Pareto-optimal with their metrics.

    Args:
        optimization_id: UUID of the optimization to query.
        db: Database connection dependency.

    Returns:
        List of ParetoPoint objects on the frontier.
    """
    cursor = await db.execute(
        "SELECT c.id, c.accuracy_top1, c.latency_ms, c.throughput_img_s, c.vram_gb "
        "FROM candidates c "
        "WHERE c.optimization_id = ? AND c.is_pareto_optimal = 1 "
        "ORDER BY c.accuracy_top1 DESC",
        (optimization_id,),
    )
    rows = await cursor.fetchall()
    return [
        ParetoPoint(
            candidate_id=row["id"],
            accuracy=row["accuracy_top1"] or 0.0,
            latency_ms=row["latency_ms"] or 0.0,
            throughput_img_s=row["throughput_img_s"] or 0.0,
            vram_gb=row["vram_gb"] or 0.0,
            is_pareto_optimal=True,
        )
        for row in rows
    ]


@router.get("/benchmarks/fireworks")
async def benchmark_fireworks(
    model: str = Query(default="llama-3.3-70b", description="Fireworks model"),
    prompt: str = Query(default="Explain quantum computing in one paragraph."),
    iterations: int = Query(default=3, ge=1, le=10),
) -> dict[str, Any]:
    """Benchmark Fireworks AI inference on AMD MI300X GPUs.

    Runs prompt through Fireworks hosted API (AMD Instinct backend)
    and returns latency, throughput, and token metrics.

    Args:
        model: Fireworks model identifier.
        prompt: Prompt to send for benchmarking.
        iterations: Number of iterations to average.

    Returns:
        Aggregated benchmark results from Fireworks AMD backend.
    """
    if not settings.fireworks_api_key:
        return {"error": "FIREWORKS_API_KEY not configured", "results": []}

    config = FireworksConfig(api_key=settings.fireworks_api_key, model=model)
    client = FireworksClient(config)

    results = []
    for _ in range(iterations):
        result = client.chat(prompt)
        results.append(result)

    successful = [r for r in results if r.success]
    if not successful:
        return {"error": results[0].error if results else "No results", "results": []}

    avg_latency = sum(r.latency_ms for r in successful) / len(successful)
    avg_tps = sum(r.tokens_per_second for r in successful) / len(successful)
    total_tokens = sum(r.total_tokens for r in successful)

    return {
        "model": model,
        "provider": "fireworks-ai",
        "hardware": "AMD-Instinct-MI300X",
        "iterations": iterations,
        "avg_latency_ms": round(avg_latency, 2),
        "avg_tokens_per_second": round(avg_tps, 2),
        "total_tokens": total_tokens,
        "results": [
            {
                "latency_ms": r.latency_ms,
                "tokens_per_second": r.tokens_per_second,
                "tokens_generated": r.tokens_generated,
                "total_tokens": r.total_tokens,
            }
            for r in successful
        ],
    }
