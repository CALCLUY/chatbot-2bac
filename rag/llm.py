"""Step 2b -- call the chat-completions API.

A thin client for any OpenAI-compatible ``/v1/chat/completions`` endpoint
(the Aster relay, OpenAI, Ollama, vLLM, OpenRouter, ...). It deliberately does
no prompt construction -- see ``rag/prompts.py`` for that -- and no retrieval
logic -- see ``retrieve.py``.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Sequence

from .config import Config


class ChatError(RuntimeError):
    """Raised when the chat API cannot be reached or returns an error."""


@dataclass
class ChatResponse:
    content: str
    model: str
    raw: dict | None = None

    def __str__(self) -> str:      # pragma: no cover - convenience
        return self.content


class ChatClient:
    """Minimal wrapper over ``POST {base_url}/chat/completions``."""

    def __init__(self, config: Config | None = None, base_url: str | None = None,
                 api_key: str | None = None, model: str | None = None,
                 temperature: float | None = None, max_tokens: int | None = None,
                 timeout: float | None = None, max_retries: int = 2):
        from .config import DEFAULT_CONFIG

        cfg = config or DEFAULT_CONFIG
        self.base_url = (base_url or cfg.chat_base_url).rstrip("/")
        self.api_key = api_key or cfg.chat_api_key
        self.model = model or cfg.chat_model
        self.temperature = cfg.chat_temperature if temperature is None else temperature
        self.max_tokens = cfg.chat_max_tokens if max_tokens is None else max_tokens
        self.timeout = timeout if timeout is not None else cfg.chat_timeout
        self.max_retries = max_retries
        self._client = None

    # ------------------------------------------------------------------ #
    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI          # imported lazily
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
                max_retries=0,                  # we do our own backoff below
            )
        return self._client

    def _payload(self, messages: Sequence[dict]) -> dict:
        payload: dict = {"model": self.model, "messages": list(messages)}
        # Omitted entirely when unset: relay endpoints differ in which
        # optional parameters they accept.
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        if self.max_tokens is not None:
            payload["max_tokens"] = self.max_tokens
        return payload

    # ------------------------------------------------------------------ #
    def complete(self, messages: Sequence[dict]) -> ChatResponse:
        """Send *messages* and return the assistant reply."""
        payload = self._payload(messages)
        delay = 2.0
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 2):
            try:
                response = self.client.chat.completions.create(**payload)
                choice = response.choices[0]
                raw = response.model_dump() if hasattr(response, "model_dump") else None
                return ChatResponse(
                    content=(choice.message.content or "").strip(),
                    model=getattr(response, "model", self.model) or self.model,
                    raw=raw,
                )
            except Exception as exc:                      # noqa: BLE001
                last_error = exc
                if attempt <= self.max_retries:
                    time.sleep(delay)
                    delay *= 2

        raise ChatError(
            f"chat completion failed after {self.max_retries + 1} attempt(s) "
            f"against {self.base_url} (model={self.model}): "
            f"{type(last_error).__name__}: {last_error}"
        ) from last_error

    def complete_text(self, messages: Sequence[dict]) -> str:
        return self.complete(messages).content

    def __repr__(self) -> str:      # pragma: no cover - debugging helper
        return f"<ChatClient base_url={self.base_url!r} model={self.model!r}>"
