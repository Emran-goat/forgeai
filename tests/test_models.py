"""Tests for Pydantic schemas."""

import pytest

from backend.models.schemas import (
    HardwareInfo,
    ModelUploadResponse,
    OptimizationCreate,
    OptimizationStatus,
    ConstraintSet,
    HardwareTarget,
)


def test_model_upload_response():
    """Test ModelUploadResponse schema."""
    model = ModelUploadResponse(
        id="test-id",
        filename="model.pth",
        architecture="resnet50",
        params_m=25.6,
        file_size_bytes=1024000,
        created_at="2024-01-01T00:00:00",
    )
    assert model.filename == "model.pth"
    assert model.architecture == "resnet50"


def test_optimization_create():
    """Test OptimizationCreate schema."""
    opt = OptimizationCreate(
        model_id="test-id",
        hardware_target=HardwareTarget.MI300X,
        constraints=ConstraintSet(max_latency_ms=50),
    )
    assert opt.model_id == "test-id"
    assert opt.hardware_target == HardwareTarget.MI300X


def test_hardware_info():
    """Test HardwareInfo schema."""
    spec = HardwareInfo(
        id="mi300x",
        name="MI300X",
        vendor="AMD",
        vram_gb=192,
        bandwidth_gbps=5300,
        compute_units=304,
        tdp_watts=750,
    )
    assert spec.name == "MI300X"
    assert spec.vram_gb == 192


def test_optimization_status():
    """Test OptimizationStatus enum."""
    assert OptimizationStatus.QUEUED == "queued"
    assert OptimizationStatus.RUNNING == "running"
    assert OptimizationStatus.COMPLETED == "completed"
    assert OptimizationStatus.FAILED == "failed"
