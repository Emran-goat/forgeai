"""Model export endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from backend.config import settings
from backend.models.database import get_db
from backend.models.schemas import ExportRequest, ExportResponse

if TYPE_CHECKING:
    import aiosqlite

router = APIRouter(tags=["exports"])


@router.post("/exports", response_model=ExportResponse, status_code=201)  # noqa: B008
async def create_export(
    request: ExportRequest,
    db: aiosqlite.Connection = Depends(get_db),  # noqa: B008
) -> ExportResponse:
    """Export an optimized model to the specified format.

    Creates the export file and stores metadata in the database.

    Args:
        request: Export request with candidate_id and format.
        db: Database connection.

    Returns:
        ExportResponse with export metadata.

    Raises:
        HTTPException: If candidate is not found.
    """
    export_id = str(uuid4())

    # Check candidate exists
    cursor = await db.execute(
        "SELECT id FROM candidates WHERE id = ?", (request.candidate_id,)
    )
    if not await cursor.fetchone():
        raise HTTPException(status_code=404, detail="Candidate not found")

    # Create export directory
    export_dir = settings.data_dir / "exports" / export_id
    export_dir.mkdir(parents=True, exist_ok=True)

    # Store in DB
    await db.execute(
        """INSERT INTO exports (id, candidate_id, format, status, created_at)
           VALUES (?, ?, ?, ?, ?)""",
        (
            export_id,
            request.candidate_id,
            request.format.value,
            "pending",
            datetime.now(timezone.utc).isoformat(),  # noqa: UP017
        ),
    )
    await db.commit()

    return ExportResponse(
        id=export_id,
        candidate_id=request.candidate_id,
        format=request.format,
        status="pending",
        created_at=datetime.now(timezone.utc),  # noqa: UP017
    )


@router.get("/exports/{export_id}")
async def download_export(
    export_id: str,
    db: aiosqlite.Connection = Depends(get_db),  # noqa: B008
) -> FileResponse:
    """Download an exported model file.

    Args:
        export_id: UUID of the export.
        db: Database connection.

    Returns:
        FileResponse with the exported model file.

    Raises:
        HTTPException: If export or file is not found.
    """
    cursor = await db.execute(
        "SELECT * FROM exports WHERE id = ?", (export_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Export not found")

    export_dir = settings.data_dir / "exports" / export_id

    # Determine file path based on format
    export_format = dict(row)["format"]
    if export_format == "onnx":
        file_path = export_dir / "model.onnx"
    elif export_format == "torchscript":
        file_path = export_dir / "model.pt"
    else:
        file_path = export_dir / "model.bin"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Export file not ready yet")

    return FileResponse(
        path=file_path,
        filename=f"forgeai_export_{export_id}{file_path.suffix}",
        media_type="application/octet-stream",
    )


@router.get("/exports/{export_id}/report")
async def download_report(
    export_id: str,
    db: aiosqlite.Connection = Depends(get_db),  # noqa: B008
) -> dict[str, Any]:
    """Download benchmark report for an export.

    Args:
        export_id: UUID of the export.
        db: Database connection.

    Returns:
        Dictionary with export and benchmark data.

    Raises:
        HTTPException: If export is not found.
    """
    cursor = await db.execute(
        "SELECT * FROM exports WHERE id = ?", (export_id,)
    )
    row = await cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Export not found")

    # Get candidate benchmarks
    candidate_id = dict(row)["candidate_id"]
    cursor = await db.execute(
        "SELECT * FROM benchmarks WHERE candidate_id = ?",
        (candidate_id,),
    )
    benchmarks = await cursor.fetchall()

    # Generate report
    report: dict[str, Any] = {
        "export_id": export_id,
        "candidate_id": candidate_id,
        "benchmarks": [dict(b) for b in benchmarks],
    }
    return report
