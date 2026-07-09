"""Pydantic request/response models for ForgeAI API."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class OptimizationStatus(str, Enum):
    """Status of an optimization job."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportFormat(str, Enum):
    """Supported export formats."""

    ONNX = "onnx"
    TORCHSCRIPT = "torchscript"
    JIT = "jit"


class HardwareTarget(str, Enum):
    """Supported hardware targets."""

    MI300X = "mi300x"
    MI250X = "mi250x"
    CPU = "cpu"


class ErrorDetail(BaseModel):
    """Error detail payload."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    error: ErrorDetail


class ModelUploadResponse(BaseModel):
    """Response for model upload."""

    id: str
    filename: str
    architecture: str
    params_m: float
    file_size_bytes: int
    created_at: datetime


class ModelInfo(BaseModel):
    """Model metadata."""

    id: str
    filename: str
    architecture: str
    params_m: float
    file_size_bytes: int
    created_at: datetime


class ConstraintSet(BaseModel):
    """Optimization constraints."""

    max_latency_ms: float | None = None
    max_memory_gb: float | None = None
    min_accuracy: float | None = None


class SearchSpace(BaseModel):
    """Architecture search space definition."""

    student_architectures: list[str] = Field(default_factory=lambda: ["auto"])
    pruning_ratios: list[float] = Field(default_factory=lambda: [0.1, 0.3, 0.5, 0.7])
    quantization_modes: list[str] = Field(default_factory=lambda: ["int8", "fp8", "int4"])


class OptimizationCreate(BaseModel):
    """Request to create an optimization job."""

    model_id: str
    hardware_target: HardwareTarget = HardwareTarget.MI300X
    constraints: ConstraintSet = Field(default_factory=ConstraintSet)
    objectives: list[str] = Field(
        default_factory=lambda: ["accuracy", "latency", "throughput", "vram"]
    )
    search_space: SearchSpace = Field(default_factory=SearchSpace)


class OptimizationResponse(BaseModel):
    """Response for optimization job creation/status."""

    id: str
    status: OptimizationStatus
    created_at: datetime
    hardware_target: str
    total_phases: int
    current_phase: str | None = None


class CandidateMetrics(BaseModel):
    """Metrics for a candidate architecture."""

    accuracy_top1: float
    latency_ms: float
    throughput_img_s: float
    vram_gb: float
    flops_g: float


class CandidateInfo(BaseModel):
    """Candidate architecture information."""

    id: str
    optimization_id: str
    architecture: str
    params_m: float
    metrics: CandidateMetrics | None = None
    pareto_rank: int | None = None
    is_pareto_optimal: bool = False


class BenchmarkResult(BaseModel):
    """Benchmark result for a candidate."""

    id: str
    candidate_id: str
    hardware_target: str
    latency_ms: float
    throughput_img_s: float
    vram_gb: float
    flops_g: float
    created_at: datetime


class ParetoPoint(BaseModel):
    """Point on the Pareto frontier."""

    candidate_id: str
    accuracy: float
    latency_ms: float
    throughput_img_s: float
    vram_gb: float
    is_pareto_optimal: bool = True


class ExportRequest(BaseModel):
    """Request to export a model."""

    candidate_id: str
    format: ExportFormat = ExportFormat.ONNX


class ExportResponse(BaseModel):
    """Response for export request."""

    id: str
    candidate_id: str
    format: ExportFormat
    status: str
    created_at: datetime


class HardwareInfo(BaseModel):
    """Hardware target information."""

    id: str
    name: str
    vendor: str
    vram_gb: float
    bandwidth_gbps: float
    compute_units: int
    tdp_watts: float


class WebSocketMessage(BaseModel):
    """WebSocket message envelope."""

    type: str
    data: dict[str, Any] = Field(default_factory=dict)
