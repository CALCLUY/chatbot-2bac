#!/usr/bin/env python3
"""Minimal local web chat for evaluating the tutor's teaching quality.

Deliberately plain: raw text in, raw text out, plus the sources each answer was
grounded on. No whiteboard, no animation, no TTS -- those come later.

    python web_chat.py --port 8000

The page and the JSON API are served from the same origin, so the browser only
ever uses relative URLs (no localhost calls from client code).

"Mock" mode answers locally using the assembled prompt instead of calling the
model, so the UI and the whole retrieval/prompt path can be exercised even when
the chat API is unreachable. Mock replies are clearly marked and never
represent real teaching quality.
"""

from __future__ import annotations

import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from chat import TutorSession
from rag.config import DEFAULT_CONFIG
from rag.llm import ChatError
from rag.prompts import SYSTEM_PROMPT
from tools.mock_chat_server import mock_reply

WEB_DIR = Path(__file__).resolve().parent / "web"
SESSION: TutorSession | None = None
_REACHABLE: dict = {"checked": False, "ok": False, "detail": ""}


def api_reachable(force: bool = False) -> dict:
    """TCP+TLS probe of the chat endpoint.

    Cached after the first call: it proves the host is reachable without
    spending a completion, so the UI can fall back to mock mode instead of
    showing connection errors.
    """
    if _REACHABLE["checked"] and not force:
        return _REACHABLE

    from urllib.parse import urlparse
    import socket
    import ssl

    parsed = urlparse(DEFAULT_CONFIG.chat_base_url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    try:
        with socket.create_connection((host, port), timeout=3) as sock:
            if parsed.scheme == "https":
                ctx = ssl.create_default_context()
                with ctx.wrap_socket(sock, server_hostname=host):
                    pass
        _REACHABLE.update(checked=True, ok=True, detail="")
    except Exception as exc:                                  # noqa: BLE001
        _REACHABLE.update(checked=True, ok=False,
                          detail=f"{type(exc).__name__}: {exc}")
    return _REACHABLE


def _sources_payload(hits) -> list[dict]:
    out = []
    for hit in hits:
        meta = hit.metadata
        place = " | ".join(
            p for p in (meta.get("matiere"),
                        meta.get("chapitre") or meta.get("semestre"),
                        meta.get("sujet") or meta.get("seance"),
                        meta.get("type")) if p
        )
        out.append({
            "score": round(hit.score, 4),
            "place": place,
            "file": meta.get("file_path", ""),
            "heading": meta.get("heading_path", ""),
            "chunk": f"{meta.get('chunk_index')}/{meta.get('n_chunks')}",
            "line": meta.get("start_line"),
            "block_type": meta.get("block_type", ""),
            "preview": " ".join(hit.content.split())[:300],
        })
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "TutorWebChat/0.1"

    # ------------------------------------------------------------------ #
    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    # ------------------------------------------------------------------ #
    def do_GET(self):                                        # noqa: N802
        if self.path.startswith("/api/health"):
            self._send_json(200, {
                "ok": SESSION is not None,
                "model": DEFAULT_CONFIG.chat_model,
                "base_url": DEFAULT_CONFIG.chat_base_url,
                "key_set": not DEFAULT_CONFIG.chat_key_is_placeholder(),
                "vectors": SESSION.retriever.store.count() if SESSION else 0,
                "system_prompt_chars": len(SYSTEM_PROMPT),
                **api_reachable(),
            })
            return

        if self.path in ("/", "/index.html"):
            page = WEB_DIR / "index.html"
            if page.is_file():
                self._send(200, page.read_bytes(), "text/html; charset=utf-8")
            else:
                self._send(404, b"web/index.html not found", "text/plain")
            return

        if self.path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return

        self._send(404, b"not found", "text/plain")

    # ------------------------------------------------------------------ #
    # ------------------------------------------------------------------ #
    @staticmethod
    def _explain_chat_error(exc: ChatError) -> str:
        """Turn a connection failure into something actionable."""
        reach = api_reachable()
        if reach["checked"] and not reach["ok"]:
            return (
                "Impossible de joindre l'API depuis CET environnement : "
                f"{reach['detail']}\n\n"
                "Ce serveur de preview tourne dans un sandbox dont la sortie réseau est "
                "limitée (seuls pypi/npm/github passent). Ce n'est pas ta clé ni ton endpoint.\n"
                "Pour de vraies réponses : clone le dépôt et lance `python web_chat.py` "
                "sur ta machine — là, l'API répondra et ce message disparaîtra.\n"
                "En attendant, bascule sur « Mock » pour tester l'interface."
            )
        return str(exc)

    def do_POST(self):                                       # noqa: N802
        if not self.path.startswith("/api/chat"):
            self._send_json(404, {"error": "not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        message = (payload.get("message") or "").strip()
        if not message:
            self._send_json(400, {"error": "empty message"})
            return

        history = payload.get("history") or []
        matiere = payload.get("matiere") or None
        chapitre = payload.get("chapitre") or None
        use_mock = payload.get("backend") == "mock"

        assert SESSION is not None
        # The browser owns the conversation; replay it before answering.
        SESSION.history = [{"role": t["role"], "content": t["content"]}
                           for t in history if t.get("role") in ("user", "assistant")]

        try:
            hits, messages = SESSION.prepare(message, matiere=matiere, chapitre=chapitre)
        except Exception as exc:                              # noqa: BLE001
            self._send_json(500, {"error": f"retrieval failed: {exc}"})
            return

        error = None
        darija_check = None
        if use_mock:
            answer = mock_reply({"messages": messages, "model": DEFAULT_CONFIG.chat_model,
                                 "temperature": DEFAULT_CONFIG.chat_temperature})
            SESSION.history.append({"role": "user", "content": message})
            SESSION.history.append({"role": "assistant", "content": answer})
        else:
            try:
                # Use ask() so the darija/document retry safeguard runs; it
                # will retrieve again, so restore the browser-owned history
                # first (ask() appends the new turn itself).
                result = SESSION.ask(message, matiere=matiere, chapitre=chapitre)
                answer = result["answer"]
                darija_check = result.get("darija_check")
                hits = result.get("sources") or hits
                messages = result.get("messages") or messages
            except ChatError as exc:
                answer, error = "", self._explain_chat_error(exc)

        self._send_json(200, {
            "answer": answer,
            "error": error,
            "mock": use_mock,
            "darija_check": darija_check,
            "sources": _sources_payload(hits),
            "prompt": {
                "system_chars": len(SYSTEM_PROMPT),
                "messages": [{"role": m["role"], "chars": len(m["content"])} for m in messages],
            },
        })

    def log_message(self, fmt, *args):                        # noqa: D102
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    global SESSION

    parser = argparse.ArgumentParser(description="Local web chat for the 2bac tutor.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    if DEFAULT_CONFIG.chat_key_is_placeholder():
        print("WARNING: CHAT_API_KEY is not set; 'API réelle' mode will fail. "
              "Use 'Mock' mode, or fill in .env.", file=sys.stderr)

    print("loading index + embedder ...", file=sys.stderr)
    SESSION = TutorSession(verbose=False)
    count = SESSION.retriever.store.count()
    if count == 0:
        print("ERROR: the vector index is empty. Run `python ingest.py` first.", file=sys.stderr)
        return 1
    print(f"ready: {count} vectors | model={SESSION.client.model} | {SESSION.client.base_url}",
          file=sys.stderr)

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"web chat on http://{args.host}:{args.port}/", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
