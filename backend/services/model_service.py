"""Model upload and storage service."""

from __future__ import annotations

import asyncio
import logging
import shutil
from pathlib import Path
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)


async def save_model(file_content: bytes, filename: str, model_id: str) -> Path:
    """Save uploaded model file to disk.

    Args:
        file_content: Raw file bytes.
        filename: Original filename.
        model_id: Generated model ID.

    Returns:
        Path where the file was saved.
    """
    model_dir = settings.data_dir / "models" / model_id
    model_dir.mkdir(parents=True, exist_ok=True)
    file_path = model_dir / filename
    await asyncio.to_thread(file_path.write_bytes, file_content)
    logger.info("Saved model %s to %s", model_id, file_path)
    return file_path


async def delete_model_file(model_id: str) -> bool:
    """Delete model file from disk.

    Args:
        model_id: The model ID to delete.

    Returns:
        True if deleted, False if not found.
    """
    model_dir = settings.data_dir / "models" / model_id
    if model_dir.exists():
        await asyncio.to_thread(shutil.rmtree, model_dir)
        logger.info("Deleted model directory %s", model_dir)
        return True
    return False


async def get_model_path(model_id: str) -> Path | None:
    """Get file path for an uploaded model.

    Args:
        model_id: The model ID.

    Returns:
        Path to the model file, or None if not found.
    """
    model_dir = settings.data_dir / "models" / model_id
    if model_dir.exists():
        files = list(model_dir.iterdir())
        if files:
            return files[0]
    return None


async def detect_architecture(file_path: Path) -> tuple[str, float]:
    """Detect model architecture and parameter count.

    Args:
        file_path: Path to the model file.

    Returns:
        Tuple of (architecture_name, params_millions).
    """
    try:
        import torch

        checkpoint: Any = torch.load(file_path, map_location="cpu", weights_only=True)

        if isinstance(checkpoint, dict):
            if "model" in checkpoint:
                state_dict = checkpoint["model"]
            elif "state_dict" in checkpoint:
                state_dict = checkpoint["state_dict"]
            else:
                state_dict = checkpoint
        else:
            state_dict = checkpoint

        total_params = sum(
            p.numel() for p in state_dict.values() if hasattr(p, "numel")
        )
        params_m = total_params / 1_000_000

        keys = list(state_dict.keys()) if isinstance(state_dict, dict) else []
        if any("blocks" in k for k in keys):
            architecture = "vit_base_patch16_224"
        elif any("layer" in k and "conv" in k for k in keys):
            architecture = "resnet50"
        else:
            architecture = "unknown"

        return architecture, params_m
    except Exception:
        logger.warning("Could not detect architecture: %s", file_path)
        return "unknown", 0.0
