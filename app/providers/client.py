"""Single-shot providers. No cross-boundary fallback or retries are automatic."""

from dataclasses import dataclass

import httpx

from app.config import Settings
from app.models import InferenceTask


@dataclass(frozen=True)
class ProviderResult:
    text: str
    input_tokens: int | None
    output_tokens: int | None


class ProviderError(Exception):
    pass


async def call_ollama(task: InferenceTask, config: Settings) -> ProviderResult:
    url = config.ollama_url.rstrip("/") + "/api/chat"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(url, json={
                "model": config.ollama_model,
                "stream": False,
                "messages": [{"role": "user", "content": task.prompt}],
                "options": {"num_predict": task.max_output_tokens},
            })
            res.raise_for_status()
            data = res.json()
            content = data["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Invalid provider response")
            return ProviderResult(content, data.get("prompt_eval_count"), data.get("eval_count"))
    except (httpx.HTTPError, KeyError, ValueError, TypeError) as exc:
        raise ProviderError("Local model request failed") from exc


async def call_azure(task: InferenceTask, config: Settings) -> ProviderResult:
    url = (
        config.azure_endpoint.rstrip("/")
        + "/openai/deployments/"
        + config.azure_deployment
        + "/chat/completions"
    )
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            res = await client.post(
                url,
                params={"api-version": config.azure_api_version},
                headers={"api-key": config.azure_api_key},
                json={
                    "messages": [{"role": "user", "content": task.prompt}],
                    "max_tokens": task.max_output_tokens,
                },
            )
            res.raise_for_status()
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            if not isinstance(content, str):
                raise ValueError("Invalid provider response")
            usage = data.get("usage") or {}
            return ProviderResult(
                content, usage.get("prompt_tokens"), usage.get("completion_tokens")
            )
    except (httpx.HTTPError, IndexError, KeyError, ValueError, TypeError) as exc:
        raise ProviderError("Cloud model request failed") from exc
