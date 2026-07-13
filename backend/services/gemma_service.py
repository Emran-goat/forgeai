from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from backend.config import settings


GEMMA_MODEL = "accounts/fireworks/models/gemma-4-31b-it"
FIREWORKS_API_URL = "https://api.fireworks.ai/inference/chat/completions"
DEFAULT_TIMEOUT = 60.0


class GemmaServiceError(Exception):
    """Raised when Gemma API call fails."""


class GemmaService:
    """Client for Fireworks Gemma 4 API."""

    def __init__(self) -> None:
        if not settings.fireworks_api_key:
            raise GemmaServiceError(
                "Fireworks API key not configured. Set FORGEAI_FIREWORKS_API_KEY."
            )
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(DEFAULT_TIMEOUT),
            headers={
                "Authorization": f"Bearer {settings.fireworks_api_key}",
                "Content-Type": "application/json",
            },
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def chat(
        self,
        messages: list[dict[str, str]],
        stream: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str | AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model": GEMMA_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        if stream:
            return self._stream_response(payload)
        return await self._blocking_response(payload)

    async def chat_with_context(
        self,
        system_prompt: str,
        user_message: str,
        context: dict | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> str:
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history)

        context_block = ""
        if context:
            context_block = "\n\n## Context\n" + json.dumps(context, indent=2, default=str)

        messages.append({"role": "user", "content": user_message + context_block})

        result = await self.chat(messages, stream=False)
        return result if isinstance(result, str) else ""

    async def _blocking_response(self, payload: dict[str, Any]) -> str:
        try:
            response = await self._client.post(FIREWORKS_API_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.TimeoutException as e:
            raise GemmaServiceError(f"Request timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise GemmaServiceError(
                f"API error {e.response.status_code}: {e.response.text}"
            ) from e
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise GemmaServiceError(f"Invalid API response: {e}") from e

    async def _stream_response(
        self, payload: dict[str, Any]
    ) -> AsyncIterator[str]:
        try:
            async with self._client.stream(
                "POST", FIREWORKS_API_URL, json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str.strip() == "[DONE]":
                            break
                        try:
                            chunk = json.loads(data_str)
                            delta = chunk.get("choices", [{}])[0].get(
                                "delta", {}
                            )
                            content = delta.get("content", "")
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
        except httpx.TimeoutException as e:
            raise GemmaServiceError(f"Stream timed out: {e}") from e
        except httpx.HTTPStatusError as e:
            raise GemmaServiceError(
                f"Stream API error {e.response.status_code}: {e.response.text}"
            ) from e


gemma_service = GemmaService()
