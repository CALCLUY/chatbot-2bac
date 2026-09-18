"""The isolated model-calling layer (Gemini ``generateContent``).

This module is the *only* place that talks to the LLM provider. It does no
prompt construction (see ``rag/prompts.py``), no retrieval (see
``retrieve.py``), and no darija/document validation (see ``chat.py``).

Callers keep using the same interface as before::

    client.complete(messages) -> ChatResponse   # messages = OpenAI-shaped
                                                # [{role, content}, ...]
    client.complete_text(messages) -> str

Internally those messages are mapped onto Gemini's ``system_instruction`` +
``contents`` (roles ``user`` / ``model``), posted to
``{GEMINI_API_ENDPOINT}/models/{model}:generateContent``, and the reply is
read from ``candidates[0].content.parts[*].text``.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Sequence
from urllib.parse import urlencode

from .config import Config

# Harm categories that can over-block legitimate 2bac SVT (méiose, reproduction,
# caryotype, …). BLOCK_NONE keeps the filters from dropping curriculum text;
# harassment / hate still use BLOCK_ONLY_HIGH. See README "Gemini safety".
EDU_SAFETY_SETTINGS: list[dict] = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_ONLY_HIGH"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_ONLY_HIGH"},
]

_SAFETY_FINISH = frozenset({"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "RECITATION"})


class ChatError(RuntimeError):
    """Raised when the chat API cannot be reached or returns an error."""


@dataclass
class ChatResponse:
    content: str
    model: str
    raw: dict | None = None

    def __str__(self) -> str:      # pragma: no cover - convenience
        return self.content


def gemini_generate_url(endpoint: str, model: str) -> str:
    """Build the generateContent URL from a configurable endpoint.

    Accepts any of:

    * ``https://generativelanguage.googleapis.com/v1beta``
    * the same with a trailing slash
    * a full URL already ending in ``:generateContent``
    * a template containing ``{model}``
    """
    base = (endpoint or "").strip()
    if not base:
        raise ChatError("GEMINI_API_ENDPOINT is empty")
    if "{model}" in base:
        return base.format(model=model)
    stripped = base.rstrip("/")
    if stripped.endswith(":generateContent"):
        return stripped
    return f"{stripped}/models/{model}:generateContent"


def messages_to_gemini(messages: Sequence[dict]) -> dict:
    """Map OpenAI-style ``[{role, content}]`` onto a Gemini generateContent body.

    * ``role=system`` → top-level ``system_instruction`` (all system turns joined).
    * ``role=assistant`` → Gemini ``model``.
    * everything else → Gemini ``user``.
    * Consecutive turns of the same Gemini role are merged (the API requires
      user/model alternation).
    * RAG context stays inside the last user turn — ``build_messages`` already
      put it there; we do not reshape it.
    """
    system_parts: list[str] = []
    contents: list[dict] = []

    for raw in messages:
        role = (raw.get("role") or "user").lower()
        text = raw.get("content") if isinstance(raw.get("content"), str) else ""
        if text is None:
            text = ""
        if role == "system":
            if text.strip():
                system_parts.append(text)
            continue
        gemini_role = "model" if role in ("assistant", "model") else "user"
        if contents and contents[-1]["role"] == gemini_role:
            prev = contents[-1]["parts"][0].get("text") or ""
            contents[-1]["parts"][0]["text"] = (prev + "\n\n" + text).strip()
        else:
            contents.append({"role": gemini_role, "parts": [{"text": text}]})

    if not contents:
        contents = [{"role": "user", "parts": [{"text": ""}]}]
    elif contents[0]["role"] != "user":
        # Gemini wants the first content turn to be `user`.
        contents.insert(0, {"role": "user", "parts": [{"text": "(continue)"}]})

    payload: dict = {"contents": contents, "safetySettings": EDU_SAFETY_SETTINGS}
    if system_parts:
        payload["system_instruction"] = {"parts": [{"text": "\n\n".join(system_parts)}]}
    return payload


def extract_gemini_text(data: dict) -> str:
    """Pull the assistant text out of a Gemini generateContent JSON body."""
    if not isinstance(data, dict):
        raise ChatError(f"Gemini response is not a JSON object: {type(data).__name__}")

    feedback = data.get("promptFeedback") or {}
    block = feedback.get("blockReason")
    if block:
        raise ChatError(
            f"Gemini blocked the prompt (promptFeedback.blockReason={block}). "
            "SVT topics such as méiose/reproduction can trip default safety "
            "filters; edu safety settings are already BLOCK_NONE for "
            "HARM_CATEGORY_SEXUALLY_EXPLICIT."
        )

    error = data.get("error")
    if error:
        message = error.get("message") if isinstance(error, dict) else str(error)
        raise ChatError(f"Gemini API error: {message}")

    candidates = data.get("candidates") or []
    if not candidates:
        raise ChatError("Gemini returned no candidates")

    cand = candidates[0] or {}
    finish = cand.get("finishReason")
    if finish in _SAFETY_FINISH:
        raise ChatError(
            f"Gemini blocked the completion (finishReason={finish}). "
            "If this was a legitimate SVT curriculum question, check safety "
            "settings / GEMINI_MODEL_NAME."
        )

    parts = ((cand.get("content") or {}).get("parts")) or []
    chunks = []
    for part in parts:
        if isinstance(part, dict) and isinstance(part.get("text"), str):
            chunks.append(part["text"])
    text = "".join(chunks).strip()
    if not text:
        raise ChatError(
            f"Gemini candidate had no text parts (finishReason={finish or 'unset'})"
        )
    return text


class ChatClient:
    """Gemini generateContent client with the historical ChatClient interface."""

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

    # ------------------------------------------------------------------ #
    def _payload(self, messages: Sequence[dict]) -> dict:
        body = messages_to_gemini(messages)
        gen: dict = {}
        if self.temperature is not None:
            gen["temperature"] = self.temperature
        if self.max_tokens is not None:
            gen["maxOutputTokens"] = self.max_tokens
        if gen:
            body["generationConfig"] = gen
        return body

    def _post(self, url: str, payload: dict) -> dict:
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        # Key goes in the header so it never lands in logged URLs.
        query = urlencode({"key": self.api_key}) if self.api_key else ""
        full = f"{url}?{query}" if query else url
        request = urllib.request.Request(
            full,
            data=raw,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "x-goog-api-key": self.api_key or "",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise ChatError(
                f"Gemini HTTP {exc.code} against {url} (model={self.model}): {detail[:500]}"
            ) from exc
        except urllib.error.URLError as exc:
            raise ChatError(
                f"Gemini request failed against {url} (model={self.model}): {exc.reason}"
            ) from exc
        try:
            return json.loads(body) if body else {}
        except json.JSONDecodeError as exc:
            raise ChatError(f"Gemini returned non-JSON: {body[:300]!r}") from exc

    def complete(self, messages: Sequence[dict]) -> ChatResponse:
        """Send *messages* (OpenAI-shaped) and return the assistant reply."""
        payload = self._payload(messages)
        url = gemini_generate_url(self.base_url, self.model)
        delay = 2.0
        last_error: Exception | None = None

        for attempt in range(1, self.max_retries + 2):
            try:
                data = self._post(url, payload)
                text = extract_gemini_text(data)
                return ChatResponse(content=text, model=self.model, raw=data)
            except ChatError as exc:
                last_error = exc
                # Do not retry safety blocks — they will fail the same way.
                msg = str(exc).lower()
                if "blocked" in msg or "blockreason" in msg:
                    break
                if attempt <= self.max_retries:
                    time.sleep(delay)
                    delay *= 2
            except Exception as exc:                      # noqa: BLE001
                last_error = exc
                if attempt <= self.max_retries:
                    time.sleep(delay)
                    delay *= 2

        raise ChatError(
            f"chat completion failed after {self.max_retries + 1} attempt(s) "
            f"against {url} (model={self.model}): "
            f"{type(last_error).__name__}: {last_error}"
        ) from last_error

    def complete_text(self, messages: Sequence[dict]) -> str:
        return self.complete(messages).content

    def __repr__(self) -> str:      # pragma: no cover - debugging helper
        return f"<ChatClient base_url={self.base_url!r} model={self.model!r}>"
