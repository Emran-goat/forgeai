from __future__ import annotations

import json

from backend.models.assistant import (
    OptimizationConfig,
    OptimizationConstraints,
)
from backend.services.gemma_service import gemma_service


SETUP_SYSTEM_PROMPT = """You are ForgeAI's optimization advisor. Parse the user's natural language description into a structured optimization config.

Rules:
- Extract model type (vision, language, multimodal)
- Extract hardware target (MI300X, MI250X, CPU)
- Extract constraints (latency, memory, accuracy)
- Recommend optimization phases based on model type
- Suggest reasonable default parameters
- Always explain your reasoning
- Provide 2-3 follow-up prompts the user might want

Available phases: architecture_search, distillation, pruning, quantization, benchmark, pareto, hyperparameter

Respond with ONLY valid JSON in this format:
{
  "model_type": "vision|language|multimodal",
  "target_hardware": "MI300X|MI250X|CPU",
  "constraints": {
    "max_latency_ms": number or null,
    "max_memory_gb": number or null,
    "min_accuracy_retention": number or null
  },
  "recommended_phases": ["phase1", "phase2"],
  "parameters": {
    "sparsity": 0.3,
    "quantization_format": "INT8",
    "n_trials": 20,
    "timeout": 300
  },
  "explanation": "string explaining your choices",
  "suggested_prompts": ["prompt1", "prompt2", "prompt3"]
}"""

RUN_SYSTEM_PROMPT = """You are ForgeAI's optimization planner. Given the user's goal, generate a complete optimization configuration.

Rules:
- Select phases based on model type and goals
- Set reasonable parameters (don't over-optimize)
- Explain each phase choice
- Estimate total runtime
- If constraints are aggressive, warn the user
- Always include benchmark and pareto phases for comparison

Respond with ONLY valid JSON in this format:
{
  "model_type": "vision|language|multimodal",
  "target_hardware": "MI300X|MI250X|CPU",
  "constraints": {
    "max_latency_ms": number or null,
    "max_memory_gb": number or null,
    "min_accuracy_retention": number or null
  },
  "recommended_phases": ["phase1", "phase2"],
  "parameters": {
    "sparsity": 0.3,
    "quantization_format": "INT8",
    "n_trials": 20,
    "timeout": 300
  },
  "explanation": "string explaining your choices and estimated runtime",
  "suggested_prompts": ["prompt1", "prompt2"]
}"""


def _parse_config_from_response(response: str) -> dict:
    text = response.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        text = "\n".join(lines)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "model_type": "vision",
            "target_hardware": "MI300X",
            "constraints": {},
            "recommended_phases": [
                "pruning",
                "quantization",
                "benchmark",
                "pareto",
            ],
            "parameters": {"sparsity": 0.3, "quantization_format": "INT8"},
            "explanation": response,
            "suggested_prompts": [
                "Run optimization",
                "Adjust constraints",
            ],
        }


def _build_config(raw: dict) -> OptimizationConfig:
    constraints_raw = raw.get("constraints", {})
    constraints = OptimizationConstraints(
        max_latency_ms=constraints_raw.get("max_latency_ms"),
        max_memory_gb=constraints_raw.get("max_memory_gb"),
        min_accuracy_retention=constraints_raw.get("min_accuracy_retention"),
        target_sparsity=constraints_raw.get("target_sparsity"),
    )
    return OptimizationConfig(
        model_type=raw.get("model_type", "vision"),
        target_hardware=raw.get("target_hardware", "MI300X"),
        constraints=constraints,
        recommended_phases=raw.get(
            "recommended_phases",
            ["pruning", "quantization", "benchmark", "pareto"],
        ),
        parameters=raw.get("parameters", {}),
    )


async def parse_setup_request(
    message: str, model_info: dict | None = None
) -> tuple[OptimizationConfig, str, list[str]]:
    context = {}
    if model_info:
        context["model_info"] = model_info

    response = await gemma_service.chat_with_context(
        system_prompt=SETUP_SYSTEM_PROMPT,
        user_message=message,
        context=context if context else None,
    )

    raw = _parse_config_from_response(response)
    config = _build_config(raw)
    explanation = raw.get("explanation", "Configuration generated based on your requirements.")
    suggested = raw.get("suggested_prompts", ["Run optimization", "Adjust constraints"])

    return config, explanation, suggested


async def generate_run_config(
    message: str, model_info: dict
) -> tuple[OptimizationConfig, str]:
    response = await gemma_service.chat_with_context(
        system_prompt=RUN_SYSTEM_PROMPT,
        user_message=message,
        context={"model_info": model_info},
    )

    raw = _parse_config_from_response(response)
    config = _build_config(raw)
    explanation = raw.get("explanation", "Optimization plan generated.")

    return config, explanation
