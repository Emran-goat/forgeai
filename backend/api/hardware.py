"""Hardware target information endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.models.schemas import HardwareInfo

router = APIRouter(tags=["hardware"])

HARDWARE_DB: dict[str, HardwareInfo] = {
    "mi300x": HardwareInfo(
        id="mi300x",
        name="AMD Instinct MI300X",
        vendor="AMD",
        vram_gb=192.0,
        bandwidth_gbps=5300.0,
        compute_units=304,
        tdp_watts=750.0,
    ),
    "mi250x": HardwareInfo(
        id="mi250x",
        name="AMD Instinct MI250X",
        vendor="AMD",
        vram_gb=128.0,
        bandwidth_gbps=3200.0,
        compute_units=110,
        tdp_watts=560.0,
    ),
    "cpu": HardwareInfo(
        id="cpu",
        name="CPU (Fallback)",
        vendor="Generic",
        vram_gb=0.0,
        bandwidth_gbps=0.0,
        compute_units=0,
        tdp_watts=0.0,
    ),
}


@router.get("/hardware", response_model=list[HardwareInfo])
async def list_hardware() -> list[HardwareInfo]:
    """List available hardware targets.

    Returns:
        List of all supported hardware configurations.
    """
    return list(HARDWARE_DB.values())


@router.get("/hardware/{hardware_id}", response_model=HardwareInfo)
async def get_hardware(hardware_id: str) -> HardwareInfo:
    """Get hardware target details.

    Args:
        hardware_id: ID of the hardware target (e.g., 'mi300x').

    Returns:
        HardwareInfo for the requested target.

    Raises:
        HTTPException: 404 if hardware target not found.
    """
    if hardware_id not in HARDWARE_DB:
        raise HTTPException(status_code=404, detail="Hardware not found")
    return HARDWARE_DB[hardware_id]
