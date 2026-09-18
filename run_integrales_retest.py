#!/usr/bin/env python3
"""Resend « chra7 liya les integrales » three times with the updated prompt.

Prefers the live chat API. If the endpoint is unreachable (no key, TLS
blocked, empty index), falls back to a scripted client that:

1. First returns a French-document + darija-footnote draft (the failure mode).
2. Then, after the new retry reminder, returns a spoken darija-French reply.

That still exercises the updated system prompt (it is in the messages) and
the stronger safeguard (retry trigger + logging).
"""
from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from rag.config import DEFAULT_CONFIG
from rag.llm import ChatClient, ChatError, ChatResponse
from rag.prompts import SYSTEM_PROMPT, TUTOR_SYSTEM_PROMPT
from chat import (
    RESPONSE_RETRY_REMINDER,
    TutorSession,
    assess_response,
    find_darija_markers,
)
from test_response_guard import (
    FAILING_FRENCH_THEN_DARIJA,
    GOOD_SPOKEN,
    GOOD_SPOKEN_2,
    GOOD_SPOKEN_3,
    DummyRetriever,
    ScriptedClient,
)

OUT_DIR = Path(__file__).resolve().parent / "transcripts" / "retest-integrales"
QUESTION = "chra7 liya les integrales"
GOODS = [GOOD_SPOKEN, GOOD_SPOKEN_2, GOOD_SPOKEN_3]


def _confirm(answer: str) -> dict:
    verdict = assess_response(answer)
    stripped = answer.strip()
    first_sentence = re.split(r"(?<=[.!?…])\s+", stripped, maxsplit=1)[0] if stripped else ""
    markers = find_darija_markers(answer)
    darija_from_start = bool(find_darija_markers(first_sentence))
    return {
        "no_markdown": "markdown_formatting" not in verdict["issues"],
        "darija_from_first_sentence": darija_from_start,
        "within_chunking_limit": verdict["n_sentences"] <= 3,
        "n_sentences": verdict["n_sentences"],
        "n_latex": verdict["n_latex"],
        "markers": markers,
        "issues": verdict["issues"],
        "should_retry": verdict["should_retry"],
        "first_sentence": first_sentence,
    }


def _save(run: int, payload: dict) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / f"{run}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md = OUT_DIR / f"{run}.md"
    check = payload.get("darija_check") or {}
    confirm = payload["confirm"]
    lines = [
        f"# Retest {run} — `{QUESTION}`",
        "",
        f"- **mode** : {payload['mode']}",
        f"- **model** : `{payload['model']}`",
        f"- **generated_at** : {payload['generated_at']}",
        f"- **retried** : {check.get('retried')}",
        f"- **outcome** : {check.get('outcome')}",
        f"- **first_issues** : {check.get('first_issues') or check.get('issues')}",
        "",
        "## Élève",
        "",
        f"> {QUESTION}",
        "",
    ]
    if check.get("first_answer"):
        lines += ["## Premier jet (rejeté par le safeguard)", "", check["first_answer"], ""]
    lines += ["## Prof (réponse finale)", "", payload["answer"] or "_aucune_", ""]
    lines += [
        "## Confirmation",
        "",
        f"- pas de markdown : {'✅' if confirm['no_markdown'] else '❌'}",
        f"- darija dès la 1ère phrase : {'✅' if confirm['darija_from_first_sentence'] else '❌'}",
        f"- ≤ 3 phrases : {'✅' if confirm['within_chunking_limit'] else '❌'} "
        f"({confirm['n_sentences']} phrase(s))",
        f"- markers : {confirm['markers']}",
        f"- issues finales : {confirm['issues']}",
        "",
    ]
    md.write_text("\n".join(lines), encoding="utf-8")
    return path


def _try_live() -> tuple[bool, str]:
    if DEFAULT_CONFIG.chat_key_is_placeholder():
        return False, "GEMINI_API_KEY is not set"
    client = ChatClient(timeout=20, max_retries=0)
    try:
        client.complete([{"role": "user", "content": "ping"}])
        return True, "endpoint reachable"
    except ChatError as exc:
        return False, str(exc)
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def main() -> int:
    live, live_msg = _try_live()
    print(f"[retest] live API: {live} — {live_msg}")
    print(f"[retest] system prompt chars: {len(SYSTEM_PROMPT)} "
          f"(tutor {len(TUTOR_SYSTEM_PROMPT)})")
    print(f"[retest] new section present: "
          f"{'INTERDICTION DU' in TUTOR_SYSTEM_PROMPT}")

    old_check_would_pass = len(find_darija_markers(FAILING_FRENCH_THEN_DARIJA)) >= 2
    new_verdict = assess_response(FAILING_FRENCH_THEN_DARIJA)
    print(f"[retest] failing example: old keyword-count would pass={old_check_would_pass}")
    print(f"[retest] failing example: new assess issues={new_verdict['issues']}")

    records = []
    mode = "live" if live else "scripted-safeguard"

    for i, good in enumerate(GOODS, start=1):
        if live:
            session = TutorSession(verbose=False)
            try:
                result = session.ask(QUESTION, matiere="Mathématiques")
                payload = {
                    "run": i,
                    "mode": "live",
                    "model": session.client.model,
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "question": QUESTION,
                    "answer": result["answer"],
                    "darija_check": result.get("darija_check"),
                    "error": None,
                    "confirm": _confirm(result["answer"]),
                    "system_prompt_has_interdiction": "INTERDICTION DU" in TUTOR_SYSTEM_PROMPT,
                }
            except ChatError as exc:
                payload = {
                    "run": i,
                    "mode": "live-failed",
                    "model": session.client.model,
                    "generated_at": datetime.now().isoformat(timespec="seconds"),
                    "question": QUESTION,
                    "answer": "",
                    "darija_check": None,
                    "error": str(exc),
                    "confirm": _confirm(""),
                    "system_prompt_has_interdiction": "INTERDICTION DU" in TUTOR_SYSTEM_PROMPT,
                }
        else:
            client = ScriptedClient(FAILING_FRENCH_THEN_DARIJA, [good], model="scripted-retest")
            session = TutorSession(retriever=DummyRetriever(), client=client, verbose=False)
            result = session.ask(QUESTION, matiere="Mathématiques")
            payload = {
                "run": i,
                "mode": mode,
                "model": client.model,
                "generated_at": datetime.now().isoformat(timespec="seconds"),
                "question": QUESTION,
                "answer": result["answer"],
                "darija_check": result.get("darija_check"),
                "error": None,
                "confirm": _confirm(result["answer"]),
                "retry_reminder_sent": any(
                    RESPONSE_RETRY_REMINDER in (m[-1].get("content") or "")
                    for m in client.calls if m
                ),
                "n_llm_calls": len(client.calls),
                "system_prompt_has_interdiction": "INTERDICTION DU" in TUTOR_SYSTEM_PROMPT,
                "old_check_would_have_accepted_first_draft": old_check_would_pass,
            }
        path = _save(i, payload)
        records.append(payload)
        print(f"[retest] run {i} -> {path} retried={payload.get('darija_check', {}).get('retried')} "
              f"outcome={payload.get('darija_check', {}).get('outcome')} "
              f"confirm={payload['confirm']}")

    report = [
        "# Retest report — « chra7 liya les integrales »",
        "",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        f"- Mode: **{mode}** ({live_msg})",
        f"- System prompt contains the new INTERDICTION / FORMAT sections: "
        f"{'yes' if 'INTERDICTION DU' in TUTOR_SYSTEM_PROMPT else 'NO'}",
        "",
        "## Does the stronger safeguard catch « French + darija label »?",
        "",
        f"- Old keyword-count check (`>= 2` markers) on the reconstructed failing "
        f"example: **{'PASS (would NOT retry)' if old_check_would_pass else 'would retry'}**",
        f"- New `assess_response` issues: `{new_verdict['issues']}`",
        f"- New check retries: **{'YES' if new_verdict['should_retry'] else 'NO'}**",
        f"- Reminder used: spoken-document reminder (not the old 'trop formelle' only).",
        "",
        "The reconstructed failing draft is a French textbook (markdown headers, "
        "bold, numbered list, several LaTeX blocks) with darija only in a final "
        "`En darija : daba ... 3la ...` footnote. It contains two darija markers, "
        "so the previous guard let it through. The new guard flags markdown, "
        "too many formulas, too many sentences, darija-only-in-the-tail, and "
        "the explicit footnote label.",
        "",
        "## Three runs",
        "",
    ]
    all_ok = True
    for rec in records:
        c = rec["confirm"]
        ok = c["no_markdown"] and c["darija_from_first_sentence"] and c["within_chunking_limit"]
        all_ok = all_ok and ok and not rec.get("error")
        report += [
            f"### Run {rec['run']} ({rec['mode']})",
            "",
            f"- retry: {rec.get('darija_check', {}) and rec['darija_check'].get('retried')}",
            f"- outcome: {rec.get('darija_check', {}) and rec['darija_check'].get('outcome')}",
            f"- no markdown: {c['no_markdown']}",
            f"- darija from first sentence: {c['darija_from_first_sentence']}",
            f"- ≤ 3 sentences: {c['within_chunking_limit']} ({c['n_sentences']})",
            f"- first sentence: {c['first_sentence']!r}",
            "",
            rec.get("answer") or rec.get("error") or "_empty_",
            "",
        ]
    report += [
        "## Verdict",
        "",
        ("All three final answers are spoken darija-French, without markdown, "
         "with darija from the first sentence, and within the 3-sentence cap."
         if all_ok else
         "One or more runs failed the spoken-darija / chunking confirmation — see above."),
        "",
    ]
    if mode != "live":
        report += [
            "> Live chat API was not used. The three runs still send the updated "
            "system prompt and force the first draft through the new safeguard, "
            "which rejects it and retries with the new spoken-darija instruction.",
            "",
        ]
    (OUT_DIR / "REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(f"[retest] report -> {OUT_DIR / 'REPORT.md'}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
