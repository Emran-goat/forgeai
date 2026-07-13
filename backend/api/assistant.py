from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.models.assistant import (
    ChatRequest,
    ChatResponse,
    ExportRequest,
    ExportResponse,
    RunRequest,
    RunResponse,
    SetupRequest,
    SetupResponse,
    VisualizeRequest,
    VisualizeResponse,
)
from backend.services.gemma_service import GemmaServiceError, gemma_service
from backend.services.optimization_advisor import (
    generate_run_config,
    parse_setup_request,
)
from backend.services.visualization import generate_auto_chart

router = APIRouter(prefix="/assistant", tags=["assistant"])

CHAT_SYSTEM_PROMPT = """You are ForgeAI's optimization assistant. You have access to the user's optimization results, pipeline state, and hardware specifications.

Rules:
- Explain results in clear, non-technical language when possible
- Use specific numbers from the data (latency, params, accuracy)
- Suggest concrete next steps
- If asked about tradeoffs, quantify them
- Reference specific candidates by name/ID
- Be concise — 2-4 paragraphs max per response"""

VISUALIZE_SYSTEM_PROMPT = """You are ForgeAI's visualization expert. Given optimization data, explain what the chart shows and suggest improvements.

Rules:
- Explain the key insights from the data
- Highlight important patterns (tradeoffs, outliers, knee points)
- Suggest 2-3 alternative views
- Be concise"""


@router.post("/setup", response_model=SetupResponse)
async def setup_optimization(request: SetupRequest) -> SetupResponse:
    """Parse natural language into optimization config."""
    try:
        config, explanation, suggested = await parse_setup_request(
            request.message
        )
        return SetupResponse(
            config=config,
            explanation=explanation,
            suggested_prompts=suggested,
        )
    except GemmaServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}") from e


@router.post("/chat", response_model=ChatResponse)
async def chat_with_assistant(request: ChatRequest) -> ChatResponse:
    """Chat with AI about optimization results."""
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]

        response = await gemma_service.chat_with_context(
            system_prompt=CHAT_SYSTEM_PROMPT,
            user_message=request.message,
            context=request.context,
            history=history,
        )

        followups = _generate_followups(request.message, response)

        return ChatResponse(response=response, suggested_followups=followups)
    except GemmaServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}") from e


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    """Stream chat response."""
    try:
        history = [{"role": m.role, "content": m.content} for m in request.history]

        messages = [{"role": "system", "content": CHAT_SYSTEM_PROMPT}]
        messages.extend(history)

        context_block = ""
        if request.context:
            context_block = "\n\n## Context\n" + json.dumps(
                request.context, indent=2, default=str
            )
        messages.append(
            {"role": "user", "content": request.message + context_block}
        )

        stream = await gemma_service.chat(messages, stream=True)

        async def event_generator() -> AsyncIterator[str]:
            async for chunk in stream:
                data = json.dumps({"type": "token", "content": chunk})
                yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except GemmaServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}") from e


@router.post("/run", response_model=RunResponse)
async def run_optimization(request: RunRequest) -> RunResponse:
    """Let AI decide and trigger optimization."""
    try:
        model_info = {}
        if request.model_id:
            model_info["model_id"] = request.model_id

        config, explanation = await generate_run_config(
            request.message, model_info
        )

        optimization_id = str(uuid.uuid4())

        return RunResponse(
            optimization_id=optimization_id,
            config_generated=config,
            explanation=explanation,
            websocket_url=f"/api/v1/ws/optimization/{optimization_id}",
        )
    except GemmaServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}") from e


@router.post("/visualize", response_model=VisualizeResponse)
async def visualize_results(request: VisualizeRequest) -> VisualizeResponse:
    """Generate charts from optimization results."""
    try:
        chart = generate_auto_chart(request.data, request.options)

        explanation_response = await gemma_service.chat_with_context(
            system_prompt=VISUALIZE_SYSTEM_PROMPT,
            user_message=f"Explain this {chart.chart_type} chart and suggest improvements.",
            context={"chart_data": request.data},
        )

        suggested = [
            "Add memory usage as bubble size",
            "Show before/after comparison",
            "Overlay Pareto frontier",
        ]

        return VisualizeResponse(
            chart=chart,
            explanation=explanation_response,
            suggested_next=suggested,
        )
    except GemmaServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}") from e


@router.post("/export", response_model=ExportResponse)
async def export_model(request: ExportRequest) -> ExportResponse:
    """AI-assisted model export."""
    try:
        export_id = str(uuid.uuid4())

        context = {"format": request.format, "optimization_id": request.optimization_id}

        guide_response = await gemma_service.chat_with_context(
            system_prompt="You are a deployment expert. Generate a concise deployment guide for the given model format and hardware.",
            user_message=request.message,
            context=context,
        )

        return ExportResponse(
            export_id=export_id,
            format=request.format,
            download_url=f"/api/v1/exports/{export_id}/download",
            guide=guide_response,
            explanation=f"Model exported to {request.format.upper()} format.",
        )
    except GemmaServiceError as e:
        raise HTTPException(status_code=503, detail=f"AI service unavailable: {e}") from e


def _generate_followups(question: str, answer: str) -> list[str]:
    followups = []
    q_lower = question.lower()
    if "pruning" in q_lower or "sparsity" in q_lower:
        followups.append("What happens at 50% sparsity?")
    if "quantization" in q_lower:
        followups.append("Compare INT8 vs INT4 results")
    if "pareto" in q_lower or "tradeoff" in q_lower:
        followups.append("Show me the knee point explanation")
    if "latency" in q_lower:
        followups.append("What's the theoretical minimum latency?")
    if not followups:
        followups = [
            "Explain these results in more detail",
            "What would happen with stricter constraints?",
            "Recommend the best candidate",
        ]
    return followups[:3]
