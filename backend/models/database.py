"""Async SQLite database setup and operations."""

from pathlib import Path

import aiosqlite

from backend.config import settings

_db: aiosqlite.Connection | None = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS models (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    architecture TEXT NOT NULL,
    params_m REAL NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS optimizations (
    id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    hardware_target TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'queued',
    total_phases INTEGER NOT NULL DEFAULT 6,
    current_phase TEXT,
    constraints TEXT,
    objectives TEXT,
    search_space TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (model_id) REFERENCES models(id)
);

CREATE TABLE IF NOT EXISTS candidates (
    id TEXT PRIMARY KEY,
    optimization_id TEXT NOT NULL,
    architecture TEXT NOT NULL,
    params_m REAL NOT NULL,
    accuracy_top1 REAL,
    latency_ms REAL,
    throughput_img_s REAL,
    vram_gb REAL,
    flops_g REAL,
    pareto_rank INTEGER,
    is_pareto_optimal INTEGER DEFAULT 0,
    FOREIGN KEY (optimization_id) REFERENCES optimizations(id)
);

CREATE TABLE IF NOT EXISTS benchmarks (
    id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    hardware_target TEXT NOT NULL,
    latency_ms REAL NOT NULL,
    throughput_img_s REAL NOT NULL,
    vram_gb REAL NOT NULL,
    flops_g REAL NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);

CREATE TABLE IF NOT EXISTS exports (
    id TEXT PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    format TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    file_path TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id)
);
"""


async def init_db() -> None:
    """Initialize the database and create tables."""
    global _db
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    _db = await aiosqlite.connect(str(settings.db_path))
    _db.row_factory = aiosqlite.Row
    await _db.executescript(SCHEMA)
    await _db.commit()


async def close_db() -> None:
    """Close the database connection."""
    global _db
    if _db:
        await _db.close()
        _db = None


async def get_db() -> aiosqlite.Connection:
    """Get the database connection."""
    if _db is None:
        await init_db()
    assert _db is not None
    return _db
