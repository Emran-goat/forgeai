from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SetupRequest(BaseModel):
    """Request model for natural language optimization setup."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=2000)
    model_id: str | None = None


class OptimizationConstraints(BaseModel):
    """Parsed optimization constraints."""

    model_config = ConfigDict(str_strip_whitespace=True)

    max_latency_ms: float | None = None
    max_memory_gb: float | None = None
    min_accuracy_retention: float | None = None
    target_sparsity: float | None = Field(default=None, ge=0.0, le=1.0)


class OptimizationConfig(BaseModel):
    """Generated optimization configuration."""

    model_config = ConfigDict(str_strip_whitespace=True)

    model_type: str = Field(..., description="vision, language, or multimodal")
    target_hardware: str = Field(..., description="MI300X, MI250X, or CPU")
    constraints: OptimizationConstraints
    recommended_phases: list[str]
    parameters: dict[str, str | int | float | bool]


class SetupResponse(BaseModel):
    """Response model for setup endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    config: OptimizationConfig
    explanation: str
    suggested_prompts: list[str]


class ChatMessage(BaseModel):
    """Single chat message."""

    model_config = ConfigDict(str_strip_whitespace=True)

    role: str = Field(..., pattern=r"^(system|user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=2000)
    context: dict | None = None
    history: list[ChatMessage] = Field(default_factory=list)


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    response: str
    suggested_followups: list[str]


class RunRequest(BaseModel):
    """Request model for AI-driven optimization run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=2000)
    model_id: str | None = None
    auto_config: bool = True


class RunResponse(BaseModel):
    """Response model for AI-driven optimization run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    optimization_id: str
    config_generated: OptimizationConfig
    explanation: str
    websocket_url: str


class VisualizeRequest(BaseModel):
    """Request model for chart generation."""

    model_config = ConfigDict(str_strip_whitespace=True)

    chart_type: str = Field(default="auto", pattern=r"^(auto|pareto|comparison|timeline|bar)$")
    data: dict
    options: dict = Field(default_factory=dict)


class ChartData(BaseModel):
    """Generated chart specification."""

    model_config = ConfigDict(str_strip_whitespace=True)

    chart_type: str
    data: list[dict]
    layout: dict


class VisualizeResponse(BaseModel):
    """Response model for visualization endpoint."""

    model_config = ConfigDict(str_strip_whitespace=True)

    chart: ChartData
    explanation: str
    suggested_next: list[str]


class ExportRequest(BaseModel):
    """Request model for AI-assisted export."""

    model_config = ConfigDict(str_strip_whitespace=True)

    message: str = Field(..., min_length=1, max_length=2000)
    optimization_id: str | None = None
    format: str = Field(default="onnx", pattern=r"^(onnx|torchscript|coreml)$")


class ExportResponse(BaseModel):
    """Response model for AI-assisted export."""

    model_config = ConfigDict(str_strip_whitespace=True)

    export_id: str
    format: str
    download_url: str
    guide: str
    explanation: str
