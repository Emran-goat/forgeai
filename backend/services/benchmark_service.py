"""Benchmark result storage service."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import aiosqlite

logger = logging.getLogger(__name__)


async def store_benchmark_result(
    db: aiosqlite.Connection,
    candidate_id: str,
    hardware_target: str,
    latency_ms: float,
    throughput_img_s: float,
    vram_gb: float,
    flops_g: float,
) -> str:
    """Store a benchmark result in the database.

    Args:
        db: Database connection.
        candidate_id: The candidate being benchmarked.
        hardware_target: Hardware used for benchmarking.
        latency_ms: Measured latency in milliseconds.
        throughput_img_s: Throughput in images per second.
        vram_gb: Peak VRAM usage in GB.
        flops_g: Estimated FLOPS in billions.

    Returns:
        The benchmark result ID.
    """
    benchmark_id = str(uuid4())
    await db.execute(
        """INSERT INTO benchmarks (id, candidate_id, hardware_target,
           latency_ms, throughput_img_s, vram_gb, flops_g, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            benchmark_id,
            candidate_id,
            hardware_target,
            latency_ms,
            throughput_img_s,
            vram_gb,
            flops_g,
            datetime.now(timezone.utc).isoformat(),
        ),
    )
    await db.commit()
    logger.info("Stored benchmark %s for candidate %s", benchmark_id, candidate_id)
    return benchmark_id


async def get_benchmarks_for_candidate(
    db: aiosqlite.Connection, candidate_id: str
) -> list[dict[str, Any]]:
    """Get all benchmark results for a candidate.

    Args:
        db: Database connection.
        candidate_id: Candidate to query.

    Returns:
        List of benchmark result dicts, most recent first.
    """
    cursor = await db.execute(
        "SELECT * FROM benchmarks WHERE candidate_id = ? ORDER BY created_at DESC",
        (candidate_id,),
    )
    rows = await cursor.fetchall()
    return [dict(row) for row in rows]
