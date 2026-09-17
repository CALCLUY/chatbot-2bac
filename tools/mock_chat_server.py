#!/usr/bin/env python3
"""A fake OpenAI-compatible chat endpoint, for testing the plumbing offline.

Use it when the real relay is unreachable (no network, firewall, expired key):
it proves that retrieval, prompt assembly, the HTTP call and response parsing
all work, without needing the model.

    python tools/mock_chat_server.py --port 8765 --log /tmp/mock_requests.jsonl

    CHAT_BASE_URL=http://127.0.0.1:8765/v1 python chat.py -q "c'est quoi une limite ?"

The reply is obviously synthetic (it describes the request it received), so a
transcript produced against this server is a *plumbing* check, never a
teaching-quality check.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def mock_reply(payload: dict) -> str:
    messages = payload.get("messages", [])
    system = next((m["content"] for m in messages if m.get("role") == "system"), "")
    user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    context_chars = 0
    if "<contexte>" in user and "</contexte>" in user:
        context_chars = len(user.split("<contexte>")[1].split("</contexte>")[0])
    question = user.split("Question de l'élève :")[-1].strip() if "Question de l'élève :" in user else ""

    return (
        f"[MOCK RESPONSE — no real model was called]\n"
        f"received {len(messages)} message(s); "
        f"system prompt {len(system)} chars; "
        f"grounding context {context_chars} chars; "
        f"history turns {sum(1 for m in messages if m.get('role') == 'assistant')}; "
        f"model={payload.get('model')}; temperature={payload.get('temperature')}\n"
        f"student question: {question[:200]}"
    )


class Handler(BaseHTTPRequestHandler):
    log_path: str | None = None

    def _send_json(self, code: int, body: dict) -> None:
        raw = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):                                  # noqa: N802
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            self._send_json(400, {"error": {"message": "invalid JSON"}})
            return

        if self.path.rstrip("/").endswith("/chat/completions"):
            if self.log_path:
                with open(self.log_path, "a", encoding="utf-8") as handle:
                    handle.write(json.dumps({
                        "at": datetime.now().isoformat(timespec="seconds"),
                        "path": self.path,
                        "authorization": self.headers.get("Authorization", "")[:24] + "…",
                        "payload": payload,
                    }, ensure_ascii=False) + "\n")
            content = mock_reply(payload)
            self._send_json(200, {
                "id": "chatcmpl-mock",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": payload.get("model", "mock"),
                "choices": [{
                    "index": 0,
                    "message": {"role": "assistant", "content": content},
                    "finish_reason": "stop",
                }],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            })
        else:
            self._send_json(404, {"error": {"message": f"unknown path {self.path}"}})

    def do_GET(self):                                   # noqa: N802
        self._send_json(200, {"status": "mock chat server", "log": self.log_path})

    def log_message(self, fmt, *args):                   # quieter logs
        sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--log", default=None, help="append every request to this JSONL file")
    args = parser.parse_args()

    Handler.log_path = args.log
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"mock chat server on http://{args.host}:{args.port}/v1  (log={args.log})", file=sys.stderr)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
