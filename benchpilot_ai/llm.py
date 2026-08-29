from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from .config import Settings, get_settings


class LLMProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...


@dataclass
class DisabledLLM:
    reason: str = "LLM enhancement disabled"

    def generate(self, prompt: str) -> str:  # pragma: no cover - deliberately unavailable
        raise RuntimeError(self.reason)


@dataclass
class OllamaProvider:
    base_url: str
    model: str
    timeout_seconds: int = 45

    def generate(self, prompt: str) -> str:
        body = json.dumps({"model": self.model, "prompt": prompt, "stream": False, "format": "json"}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return str(payload["response"])
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Local LLM request failed: {exc}") from exc


def provider_from_settings(settings: Settings | None = None) -> LLMProvider | None:
    settings = settings or get_settings()
    if settings.llm_mode == "ollama":
        return OllamaProvider(settings.ollama_base_url, settings.ollama_model)
    return None
