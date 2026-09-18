#!/usr/bin/env python3
"""Mock-mode tests for the Gemini model-calling layer (rag/llm.py).

No live key is used. This checks that:

* OpenAI-shaped messages (system + history + RAG user turn) become a valid
  Gemini generateContent body;
* the reply is read from candidates[0].content.parts[*].text;
* safety blocks surface as ChatError;
* ChatClient.complete() still returns ChatResponse.content as plain text.

Add your GEMINI_API_KEY in .env, then run python run_test_conversations.py
(or python chat.py -q "...") to verify the integration works end-to-end.
This file alone is not that live check.
"""
from __future__ import annotations

import unittest

from rag.llm import (
    ChatClient,
    ChatError,
    ChatResponse,
    EDU_SAFETY_SETTINGS,
    extract_gemini_text,
    gemini_generate_url,
    messages_to_gemini,
)


def _gemini_ok(text: str, model: str = "gemini-3.8-flash") -> dict:
    return {
        "candidates": [{
            "content": {"role": "model", "parts": [{"text": text}]},
            "finishReason": "STOP",
        }],
        "modelVersion": model,
    }


class UrlTests(unittest.TestCase):
    def test_default_endpoint(self):
        url = gemini_generate_url(
            "https://generativelanguage.googleapis.com/v1beta",
            "gemini-3.8-flash",
        )
        self.assertEqual(
            url,
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-3.8-flash:generateContent",
        )

    def test_trailing_slash(self):
        url = gemini_generate_url(
            "https://generativelanguage.googleapis.com/v1beta/",
            "gemini-3.8-flash",
        )
        self.assertTrue(url.endswith("/models/gemini-3.8-flash:generateContent"))
        self.assertNotIn("//models", url.replace("https://", ""))

    def test_full_url_passthrough(self):
        full = "https://example.test/v1beta/models/x:generateContent"
        self.assertEqual(gemini_generate_url(full, "ignored"), full)

    def test_template(self):
        url = gemini_generate_url(
            "https://proxy.example/v1/models/{model}:generateContent",
            "gemini-3.8-flash",
        )
        self.assertIn("gemini-3.8-flash", url)


class MappingTests(unittest.TestCase):
    def test_system_history_and_rag_user_turn(self):
        messages = [
            {"role": "system", "content": "Tu es un professeur. Parle en darija."},
            {"role": "user", "content": "saha prof"},
            {"role": "assistant", "content": "Saha khouya, wach fhemti?"},
            {"role": "user", "content": "<contexte>\n[Source 1] méiose\n</contexte>\n\nQuestion de l'élève : chra7 liya la méiose"},
        ]
        body = messages_to_gemini(messages)
        self.assertIn("system_instruction", body)
        self.assertIn("darija", body["system_instruction"]["parts"][0]["text"])
        roles = [c["role"] for c in body["contents"]]
        self.assertEqual(roles, ["user", "model", "user"])
        self.assertIn("<contexte>", body["contents"][-1]["parts"][0]["text"])
        self.assertEqual(body["safetySettings"], EDU_SAFETY_SETTINGS)
        # Gemini must not see OpenAI "assistant" / "system" as content roles.
        self.assertNotIn("assistant", roles)
        self.assertNotIn("system", roles)

    def test_merges_consecutive_same_role(self):
        messages = [
            {"role": "user", "content": "un"},
            {"role": "user", "content": "deux"},
            {"role": "assistant", "content": "ok"},
        ]
        body = messages_to_gemini(messages)
        self.assertEqual(len(body["contents"]), 2)
        self.assertIn("un", body["contents"][0]["parts"][0]["text"])
        self.assertIn("deux", body["contents"][0]["parts"][0]["text"])

    def test_leading_assistant_gets_user_prefix(self):
        body = messages_to_gemini([{"role": "assistant", "content": "déjà"}])
        self.assertEqual(body["contents"][0]["role"], "user")

    def test_not_openai_chat_completions_shape(self):
        body = messages_to_gemini([{"role": "user", "content": "ping"}])
        self.assertNotIn("messages", body)
        self.assertNotIn("max_tokens", body)
        self.assertIn("contents", body)


class ParseTests(unittest.TestCase):
    def test_happy_path(self):
        self.assertEqual(extract_gemini_text(_gemini_ok("  Tsawwar m3aya.  ")),
                         "Tsawwar m3aya.")

    def test_joins_multiple_parts(self):
        data = {"candidates": [{"content": {"parts": [
            {"text": "Daba "}, {"text": "wach fhemti?"},
        ]}}]}
        self.assertEqual(extract_gemini_text(data), "Daba wach fhemti?")

    def test_prompt_blocked(self):
        with self.assertRaises(ChatError) as ctx:
            extract_gemini_text({"promptFeedback": {"blockReason": "SAFETY"},
                                 "candidates": []})
        self.assertIn("blocked", str(ctx.exception).lower())

    def test_finish_reason_safety(self):
        with self.assertRaises(ChatError):
            extract_gemini_text({
                "candidates": [{
                    "finishReason": "SAFETY",
                    "content": {"parts": [{"text": ""}]},
                }]
            })

    def test_openai_shaped_response_is_rejected(self):
        with self.assertRaises(ChatError):
            extract_gemini_text({
                "choices": [{"message": {"role": "assistant", "content": "nope"}}]
            })


class ClientMockTests(unittest.TestCase):
    def test_complete_returns_plain_text(self):
        client = ChatClient(
            api_key="not-a-real-key",
            model="gemini-3.8-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta",
            max_retries=0,
        )
        posted = {}

        def fake_post(url, payload):
            posted["url"] = url
            posted["payload"] = payload
            self.assertTrue(url.endswith(":generateContent"))
            self.assertIn("contents", payload)
            self.assertNotIn("messages", payload)
            return _gemini_ok("Daba wach fhemti l'idée?")

        client._post = fake_post  # type: ignore[method-assign]
        reply = client.complete([
            {"role": "system", "content": "Tu es un prof."},
            {"role": "user", "content": "chra7 liya les integrales"},
        ])
        self.assertIsInstance(reply, ChatResponse)
        self.assertEqual(reply.content, "Daba wach fhemti l'idée?")
        self.assertIn("system_instruction", posted["payload"])
        self.assertEqual(posted["payload"]["contents"][0]["role"], "user")

    def test_payload_includes_generation_config(self):
        client = ChatClient(api_key="x", temperature=0.4, max_tokens=512, max_retries=0)
        body = client._payload([{"role": "user", "content": "ping"}])
        self.assertEqual(body["generationConfig"]["temperature"], 0.4)
        self.assertEqual(body["generationConfig"]["maxOutputTokens"], 512)


if __name__ == "__main__":
    unittest.main()
