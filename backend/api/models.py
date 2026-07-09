"""Model upload and management endpoints."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import aiosqlite
from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, File

from backend.config import settings
from backend.models.database import get_db
from backend.models.schemas import ModelInfo, ModelUploadResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["models"])

ALLOWED_EXTENSIONS: set[str] = {".pt", ".pth", ".onnx", ".bin"}
MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024 * 1024  # 5 GB


def _detect_architecture(file_path: Path) -> tuple[str, float]:
    """Detect model architecture and parameter count from a file.

    Attempts to load the file as a PyTorch checkpoint or ONNX model.
    Falls back to heuristic detection based on file size.

    Args:
        file_path: Path to the saved model file.

    Returns:
        Tuple of (architecture_name, parameter_count_in_millions).
    """
    suffix = file_path.suffix.lower()

    if suffix in (".pt", ".pth", ".bin"):
        try:
            import torch

            checkpoint = torch.load(str(file_path), map_location="cpu", weights_only=True)
            if isinstance(checkpoint, dict):
                if "state_dict" in checkpoint:
                    state_dict = checkpoint["state_dict"]
                elif "model" in checkpoint:
                    state_dict = checkpoint["model"]
                else:
                    state_dict = checkpoint
                total_params = sum(p.numel() for p in state_dict.values() if hasattr(p, "numel"))
                return _guess_architecture_from_state_dict(state_dict), round(total_params / 1e6, 2)
        except Exception:
            logger.debug("Could not load as PyTorch checkpoint, using heuristic")

    if suffix == ".onnx":
        try:
            import onnx

            model = onnx.load(str(file_path))
            total_params = 0
            for initializer in model.graph.initializer:
                dim = 1
                for d in initializer.dims:
                    dim *= d
                total_params += dim
            return "onnx_model", round(total_params / 1e6, 2)
        except Exception:
            logger.debug("Could not load as ONNX model, using heuristic")

    file_size = file_path.stat().st_size
    estimated_params = file_size / 4  # Assume fp32
    return "unknown", round(estimated_params / 1e6, 2)


def _guess_architecture_from_state_dict(state_dict: dict) -> str:
    """Guess architecture name from state dict key patterns.

    Args:
        state_dict: Model state dictionary.

    Returns:
        Best-guess architecture name string.
    """
    keys = list(state_dict.keys())
    if not keys:
        return "unknown"

    if any("blocks" in k and "mlp" in k for k in keys):
        return "vit_base_patch16_224"
    if any("layer1" in k for k in keys):
        return "resnet50"
    if any("features" in k and "classifier" in keys for k in keys):
        return "efficientnet_b0"
    if any("encoder" in k for k in keys):
        return "encoder_model"

    return "custom_model"


@router.post("/models", response_model=ModelUploadResponse, status_code=201)
async def upload_model(
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(get_db),
) -> ModelUploadResponse:
    """Upload a teacher model file.

    Accepts .pt, .pth, .onnx, .bin files up to 5 GB.
    Saves to data/models/{model_id}/ and stores metadata in DB.

    Args:
        file: Uploaded model file.
        db: Database connection dependency.

    Returns:
        ModelUploadResponse with model metadata.

    Raises:
        HTTPException: 400 if file extension is not allowed.
    """
    filename = file.filename or "unknown"
    ext = Path(filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File extension '{ext}' not allowed. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    model_id = str(uuid4())
    sanitized_filename = Path(filename).name
    model_dir = settings.data_dir / "models" / model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    file_path = model_dir / sanitized_filename

    file_size = 0
    with open(file_path, "wb") as f:
        while True:
            chunk = await file.read(8192)
            if not chunk:
                break
            file_size += len(chunk)
            if file_size > MAX_FILE_SIZE_BYTES:
                file_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="File too large (max 5 GB)")
            f.write(chunk)

    architecture, params_m = await asyncio.to_thread(_detect_architecture, file_path)
    now = datetime.now(timezone.utc).isoformat()

    await db.execute(
        "INSERT INTO models (id, filename, architecture, params_m, file_size_bytes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (model_id, sanitized_filename, architecture, params_m, file_size, now),
    )
    await db.commit()

    logger.info("Uploaded model %s (%s, %.1fM params)", model_id, architecture, params_m)

    return ModelUploadResponse(
        id=model_id,
        filename=sanitized_filename,
        architecture=architecture,
        params_m=params_m,
        file_size_bytes=file_size,
        created_at=datetime.fromisoformat(now),
    )


@router.get("/models", response_model=list[ModelInfo])
async def list_models(
    db: aiosqlite.Connection = Depends(get_db),
) -> list[ModelInfo]:
    """List all uploaded models, newest first.

    Args:
        db: Database connection dependency.

    Returns:
        List of ModelInfo objects.
    """
    cursor = await db.execute("SELECT * FROM models ORDER BY created_at DESC")
    rows = await cursor.fetchall()
    return [
        ModelInfo(
            id=row["id"],
            filename=row["filename"],
            architecture=row["architecture"],
            params_m=row["params_m"],
            file_size_bytes=row["file_size_bytes"],
            created_at=datetime.fromisoformat(row["created_at"]),
        )
        for row in rows
    ]


@router.get("/models/{model_id}", response_model=ModelInfo)
async def get_model(
    model_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> ModelInfo:
    """Get model details by ID.

    Args:
        model_id: UUID of the model.
        db: Database connection dependency.

    Returns:
        ModelInfo for the requested model.

    Raises:
        HTTPException: 404 if model not found.
    """
    cursor = await db.execute("SELECT * FROM models WHERE id = ?", (model_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Model not found")

    return ModelInfo(
        id=row["id"],
        filename=row["filename"],
        architecture=row["architecture"],
        params_m=row["params_m"],
        file_size_bytes=row["file_size_bytes"],
        created_at=datetime.fromisoformat(row["created_at"]),
    )


@router.delete("/models/{model_id}", status_code=204, response_class=Response)
async def delete_model(
    model_id: str,
    db: aiosqlite.Connection = Depends(get_db),
) -> Response:
    """Delete a model and its file from disk.

    Args:
        model_id: UUID of the model to delete.
        db: Database connection dependency.

    Raises:
        HTTPException: 404 if model not found.
    """
    cursor = await db.execute("SELECT id FROM models WHERE id = ?", (model_id,))
    row = await cursor.fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Model not found")

    model_dir = settings.data_dir / "models" / model_id
    if model_dir.exists():
        import shutil

        shutil.rmtree(model_dir)

    await db.execute("DELETE FROM models WHERE id = ?", (model_id,))
    await db.commit()

    logger.info("Deleted model %s", model_id)
    return Response(status_code=204)
