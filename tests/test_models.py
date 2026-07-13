"""Tests for Pydantic schemas."""

import pytest

from backend.models.schemas import (
    HardwareSpec,
    ModelCreate,
    OptimizationCreate,
    OptimizationStatus,
)


def test_model_create():
    """Test ModelCreate schema."""
    model = ModelCreate(
        name="test-model",
        framework="pytorch",
        architecture="resnet50",
    )
    assert model.name == "test-model"
    assert model.framework == "pytorch"


def test_optimization_create():
    """Test OptimizationCreate schema."""
    opt = OptimizationCreate(
        model_id="test-id",
        hardware="MI300X",
        constraints={"max_latency_ms": 50},
    )
    assert opt.model_id == "test-id"
    assert opt.hardware == "MI300X"


def test_hardware_spec():
    """Test HardwareSpec schema."""
    spec = HardwareSpec(
        name="MI300X",
        vram_gb=192,
        tdp_watts=750,
    )
    assert spec.name == "MI300X"
    assert spec.vram_gb == 192


def test_optimization_status():
    """Test OptimizationStatus enum."""
    assert OptimizationStatus.PENDING == "pending"
    assert OptimizationStatus.RUNNING == "running"
    assert OptimizationStatus.COMPLETED == "completed"
    assert OptimizationStatus.FAILED == "failed"
