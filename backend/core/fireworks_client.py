"""Fireworks AI API client for hosted AMD GPU inference."""

import time
from dataclasses import dataclass, field
from typing import Any

import httpx


FIREWORKS_BASE_URL = "https://api.fireworks.ai/inference/v1"
FIREWORKS_MODELS = {
    "glm-5.2": "accounts/fireworks/models/glm-5p2",
    "glm-5.1": "accounts/fireworks/models/glm-5p1",
    "deepseek-v4": "accounts/fireworks/models/deepseek-v4-pro",
    "kimi-k2.5": "accounts/fireworks/models/kimi-k2p5",
    "kimi-k2.6": "accounts/fireworks/models/kimi-k2p6",
}


@dataclass
class FireworksConfig:
    api_key: str
    model: str = "llama-3.3-70b"
    max_tokens: int = 256
    temperature: float = 0.0

    @property
    def model_id(self) -> str:
        return FIREWORKS_MODELS.get(self.model, self.model)


@dataclass
class FireworksResult:
    model: str
    provider: str = "fireworks-ai"
    hardware: str = "AMD-Instinct-MI300X"
    latency_ms: float = 0.0
    tokens_generated: int = 0
    tokens_per_second: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    success: bool = True
    error: str = ""
    raw_response: dict[str, Any] = field(default_factory=dict)


class FireworksClient:
    """Client for Fireworks AI inference API (AMD MI300X backend)."""

    def __init__(self, config: FireworksConfig) -> None:
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        prompt: str,
        system: str = "You are a helpful assistant.",
        max_tokens: int | None = None,
    ) -> FireworksResult:
        """Send a chat completion request to Fireworks."""
        payload = {
            "model": self.config.model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": self.config.temperature,
        }

        start = time.perf_counter()
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{FIREWORKS_BASE_URL}/chat/completions",
                    headers=self.headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()

            elapsed_ms = (time.perf_counter() - start) * 1000
            usage = data.get("usage", {})
            choice = data["choices"][0]
            content = choice["message"]["content"]
            tokens_generated = len(content.split())

            return FireworksResult(
                model=self.config.model,
                latency_ms=round(elapsed_ms, 2),
                tokens_generated=tokens_generated,
                tokens_per_second=round(
                    tokens_generated / (elapsed_ms / 1000) if elapsed_ms > 0 else 0,
                    2,
                ),
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                raw_response=data,
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start) * 1000
            return FireworksResult(
                model=self.config.model,
                latency_ms=round(elapsed_ms, 2),
                success=False,
                error=str(e),
            )

    def benchmark(
        self,
        prompts: list[str] | None = None,
        iterations: int = 3,
    ) -> list[FireworksResult]:
        """Run benchmark with multiple prompts and iterations."""
        if prompts is None:
            prompts = [
                "Explain quantum computing in one paragraph.",
                "Write a Python function to sort a list.",
                "What are the three laws of thermodynamics?",
                "Describe the architecture of a Transformer model.",
                "Compare ROCm and CUDA for AI inference.",
            ]

        results: list[FireworksResult] = []
        for prompt in prompts:
            for _ in range(iterations):
                result = self.chat(prompt)
                results.append(result)
        return results
