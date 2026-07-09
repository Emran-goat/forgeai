"""ROCm detection and configuration utilities."""

from typing import Any


def detect_rocm() -> dict[str, Any]:
    """Detect ROCm availability and version."""
    return {"available": False, "version": None, "devices": []}


def get_gpu_count() -> int:
    """Get number of available GPUs."""
    return 0


def set_rocm_devices(devices: str) -> None:
    """Set ROCm visible devices."""
    pass
