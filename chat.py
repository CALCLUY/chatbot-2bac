#!/usr/bin/env python3
"""Command-line chat loop for the 2ème Bac SM AI tutor.

Plain text on purpose: this exists so you can judge the tutor's *teaching
quality* before any UI, animation or TTS work starts.

    python chat.py                       # interactive
    python chat.py --matiere SVT         # start scoped to a subject
    python chat.py --question "c'est quoi une limite ?" --matiere Mathématiques

In-chat commands:
    /matiere <nom>     restreindre la recherche (Mathématiques | Physique-Chimie | SVT)
    /matiere off       retirer le filtre
    /chapitre <nom>    restreindre à un chapitre (ou un semestre)
    /chapitre off      retirer le filtre
    /sources           ré-afficher les sources de la dernière réponse
    /prompt            afficher le dernier prompt envoyé (debug)
    /reset             effacer l'historique
    /quit              quitter

The tutor's system prompt lives in ``rag/prompts.py`` -- edit it there.
Every answer is followed by the sources it was grounded on, for your own
verification (real students will not see that block).

Anti-drift / anti-document safeguard
    The model tends to (a) drift back to pure formal French and (b) answer
    like a textbook (markdown headers, bold terms, stacked formulas) with
    darija tacked on as a footnote. Every generated answer is scanned for:

    * too few distinct darija markers (CHAT_DARIJA_MIN_MARKERS, default 2)
    * markdown formatting (headers, bold, numbered/bulleted lists)
    * more than 2 LaTeX formula blocks
    * more than ~5 sentences (the prompt cap is 3; 6+ forces a retry)
    * darija markers appearing only in the last 20% of the text
      (translation-at-the-end pattern)

    On any of those, the completion is retried ONCE with an explicit
    spoken-darija reminder. Each retry is logged to the console and to
    logs/darija_retry_log.jsonl (override: CHAT_DARIJA_RETRY_LOG).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

from rag.config import DEFAULT_CONFIG, Config, REPO_ROOT
from rag.display import _rule
from rag.llm import ChatClient, ChatError
from rag.prompts import build_messages
from rag.vectorstore import RetrievedChunk
from retrieve import Retriever

HELP = __doc__.strip()


# A bare "j'ai pas compris" / "kifach ?" carries no topic, so retrieving with it
# alone pulls in whatever chapter happens to match those words. When a turn looks
# like a follow-up, the previous student question is prepended to give the
# retriever something to work with.
FOLLOWUP_RE = re.compile(
    r"(j[e’']?\s*ai pas compris|je n['’]ai pas compris|pas compris|Compris pas|"
    r"reformule|explique encore|autre exemple|encore|continue|continuer|"
    r"pourquoi|pk\b|comment ça|kifach|wach|et alors|c'est-à-dire|"
    r"donne[- ]moi|donne la|je veux|juste la)",
    re.IGNORECASE,
)
MIN_CONTENT_WORDS = 5


# --------------------------------------------------------------------------- #
# Darija-mix guard — code-level safeguard against drifting back to pure French
# --------------------------------------------------------------------------- #
# The system prompt (rag/prompts.py) asks for a darija-French mix, but on long
# conversations the model tends to drift back to pure formal French. As a
# backstop, every generated answer is scanned for common darija markers
# (Latin-alphabet darija, the same spelling the students type). When fewer
# than DARIJA_MIN_MARKERS *distinct* markers are present, the answer is
# treated as a failed generation and the completion is retried ONCE with an
# explicit reminder appended. Every retry is logged to the console and to a
# JSONL file so the drift rate and the retry success rate stay measurable:
#
#     logs/darija_retry_log.jsonl   (override: CHAT_DARIJA_RETRY_LOG)
#
# Threshold override: CHAT_DARIJA_MIN_MARKERS (default 2).

DARIJA_MARKERS: tuple[str, ...] = (
    # Base list — the common markers every tutor reply should normally show
    "wach", "daba", "bghiti", "mzyan", "khouya", "rak", "3andek", "ghadi",
    "bla", "chwiya", "hadi", "dyal", "kayn", "walakin", "bezzaf",
    # Greetings / interjections
    "saha", "safi", "wakha", "safti",
    # "visualise" prompts (the v2 pedagogy uses them a lot)
    "tsawwar", "tsawwri", "tsawwer",
    # understanding / not understanding
    "fhemt", "fhemti", "fhem", "fahem", "fahemna", "3reft", "3refti", "machi",
    # question words
    "chno", "chnou", "kifach", "3lach", "3la", "3lik", "3li", "3lina",
    # pronouns / demonstratives / adverbs of place
    "nta", "nti", "ana", "ntoum", "howa", "haka", "hna", "hada", "hado",
    # common verbs (Latin-alphabet darija)
    "dir", "dirla", "dirha", "dirli", "bghit", "bghina", "bghitna", "9der",
    "t9der", "n9der", "9elleb", "9alleb", "3tik", "3tini", "t3tik", "awed",
    "3awed", "3lemni", "3lem", "3alna", "9dem", "9dim", "9el", "7it",
    "9raf", "3rf",
    # connectors / particles / fillers
    "7ba", "7ta", "wala", "ola", "ghir", "bss", "koulchi", "koulma", "chi",
    "walou", "bhal", "bzabt", "zbzt",
    # adverbs / intensifiers / size
    "mezyan", "mzyana", "kter", "bzzaf", "qrib", "9rib", "kbir", "kbira",
    "sghir", "sghira", "wahd", "wahda", "wahed",
    # problems / mistakes / needs
    "ghlta", "ghalat", "mouchkil", "mouchkila", "khas", "khass", "khasek",
    "khassni", "khassk",
    # exam / study vocabulary (darija form)
    "l7al", "jawab", "s7i7", "sahit", "doyour", "3amalat", "l7a9i9i",
    # possession / address
    "3andi", "3ndek", "3ndi", "3afak", "afak",
    # "simple" (the tutor promises "bsit" examples)
    "bsit", "bsita",
    # time
    "lyoum", "ghedda", "wa9t",
)

# Pre-compiled word-boundary matcher per marker. \b treats digits as word
# chars, so "3andek" / "9der" match their latin-alphabet darija spelling.
_DARIJA_MARKER_RES: dict[str, re.Pattern[str]] = {
    m: re.compile(rf"\b{re.escape(m)}\b") for m in DARIJA_MARKERS
}

DARIJA_RETRY_REMINDER = (
    "Ta dernière réponse était trop formelle et 100% française — reformule-la "
    "en mélangeant plus de darija, comme dans les exemples donnés dans tes "
    "instructions."
)

# Used when the answer looks like a document, is too long, or tacks darija
# on only at the end (the "En darija : ..." anti-pattern).
RESPONSE_RETRY_REMINDER = (
    "Ta réponse précédente était trop longue, trop formatée comme un document, "
    "et/ou la darija était ajoutée seulement à la fin. Recommence : parle "
    "directement en mélange darija-français dès la première phrase, sans titres "
    "ni gras, en une seule petite idée."
)

DARIJA_RETRY_LOG = Path(
    os.getenv("CHAT_DARIJA_RETRY_LOG", str(REPO_ROOT / "logs" / "darija_retry_log.jsonl"))
)

# Pedagogical cap in the system prompt is 3 sentences. We retry when the
# answer is clearly past "about 4-5 sentences" so a slightly long spoken
# turn does not loop, but a textbook dump does.
MAX_SENTENCES_BEFORE_RETRY = 5
MAX_LATEX_BLOCKS_BEFORE_RETRY = 2
DARIJA_TAIL_RATIO = 0.20
DARIJA_TAIL_MIN_CHARS = 200  # skip the tail-only check on very short replies

_HEADER_RE = re.compile(r"(?m)^\s{0,3}#{1,6}\s+\S")
_BOLD_RE = re.compile(r"\*\*[^*\n]{1,200}\*\*|__[^_\n]{1,200}__")
_LIST_ITEM_RE = re.compile(r"(?m)^\s{0,3}(?:[-*+]\s+\S|\d+[.)]\s+\S)")
_DARIJA_FOOTNOTE_RE = re.compile(
    r"(?i)\b(?:en\s+darija\s*[:\-—–]|traduction\s+darija|en\s+dialecte\s*:)"
)
_DISPLAY_LATEX_RE = re.compile(r"\$\$.+?\$\$", re.S)
_INLINE_LATEX_RE = re.compile(r"\$(?!\$)[^$\n]+\$")


def darija_min_markers() -> int:
    """Minimum number of DISTINCT darija markers an answer must contain."""
    try:
        return max(1, int(os.getenv("CHAT_DARIJA_MIN_MARKERS", "2")))
    except ValueError:
        return 2


def find_darija_markers(text: str) -> list[str]:
    """Return the distinct darija markers (from DARIJA_MARKERS) present in *text*.

    Matching is case-insensitive on whole words, so 'wach' inside 'wach
    fhemti' counts but a French word that merely contains the letters does not.
    """
    if not text:
        return []
    lowered = text.lower()
    return [m for m, rx in _DARIJA_MARKER_RES.items() if rx.search(lowered)]


def find_darija_marker_positions(text: str) -> list[int]:
    """Character offsets of every darija-marker match in *text* (lowercased)."""
    if not text:
        return []
    lowered = text.lower()
    positions: list[int] = []
    for rx in _DARIJA_MARKER_RES.values():
        positions.extend(m.start() for m in rx.finditer(lowered))
    return sorted(positions)


def count_latex_blocks(text: str) -> int:
    """Count ``$$...$$`` display blocks plus leftover ``$...$`` inline formulas."""
    if not text:
        return 0
    n_display = len(_DISPLAY_LATEX_RE.findall(text))
    remainder = _DISPLAY_LATEX_RE.sub("", text)
    n_inline = len(_INLINE_LATEX_RE.findall(remainder))
    return n_display + n_inline


def count_prose_sentences(text: str) -> int:
    """Count spoken sentences, treating headings and list items as sentences.

    A bulleted dump of ideas is exactly the over-explaining the prompt
    forbids, so list rows count even without a period.
    """
    if not text:
        return 0
    body = _DISPLAY_LATEX_RE.sub(" MATH ", text)
    body = _INLINE_LATEX_RE.sub(" MATH ", body)
    body = re.sub(r"\[Source \d+\]", " ", body)
    body = re.sub(r"^\s*(#{1,6}|[*+-]|\d+[.)])\s*", "\n", body, flags=re.M)
    body = body.replace("**", "").replace("__", "").replace("`", "")

    segments: list[str] = []
    for raw_line in body.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        protected = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", line)
        protected = re.sub(r"\b(etc|cf|ex|env|vs|M|N)\.", r"\1<DOT>", protected)
        parts = re.split(r"(?<=[.!?…])\s+", protected)
        for part in parts:
            piece = part.replace("<DOT>", ".").strip(" \t-*•")
            if len(piece) >= 2:
                segments.append(piece)
    return len(segments)


def has_markdown_formatting(text: str) -> bool:
    """True when the answer is structured like a document, not spoken."""
    if not text:
        return False
    if _HEADER_RE.search(text):
        return True
    if _BOLD_RE.search(text):
        return True
    if len(_LIST_ITEM_RE.findall(text)) >= 2:
        return True
    return False


def darija_only_in_tail(text: str, tail_ratio: float = DARIJA_TAIL_RATIO) -> bool:
    """True when every darija marker sits in the last *tail_ratio* of *text*.

    A short spoken reply can legitimately put its last darija word near the
    end, so the check is skipped under DARIJA_TAIL_MIN_CHARS. No markers at
    all is a different issue (too_few_darija_markers).
    """
    if not text or len(text) < DARIJA_TAIL_MIN_CHARS:
        return False
    positions = find_darija_marker_positions(text)
    if not positions:
        return False
    cutoff = int(len(text) * (1.0 - tail_ratio))
    return all(pos >= cutoff for pos in positions)


def retry_reminder_for(issues: Sequence[str]) -> str:
    """Pick the reminder that matches why the first draft was rejected."""
    documentish = {
        "markdown_formatting",
        "too_many_latex_blocks",
        "too_many_sentences",
        "darija_only_at_end",
        "darija_as_footnote",
    }
    if documentish.intersection(issues):
        return RESPONSE_RETRY_REMINDER
    return DARIJA_RETRY_REMINDER


def assess_response(text: str, min_markers: int | None = None) -> dict:
    """Return a structured quality verdict for one tutor reply.

    ``issues`` is the list of trigger codes; any non-empty list means retry.
    """
    if min_markers is None:
        min_markers = darija_min_markers()
    text = text or ""
    markers = find_darija_markers(text)
    n_sentences = count_prose_sentences(text)
    n_latex = count_latex_blocks(text)
    issues: list[str] = []
    reasons: list[str] = []

    if len(markers) < min_markers:
        issues.append("too_few_darija_markers")
        reasons.append(
            f"{len(markers)} darija marker(s) {markers or '[]'} "
            f"(minimum {min_markers})"
        )

    if has_markdown_formatting(text):
        issues.append("markdown_formatting")
        bits = []
        if _HEADER_RE.search(text):
            bits.append("headers")
        if _BOLD_RE.search(text):
            bits.append("bold")
        n_lists = len(_LIST_ITEM_RE.findall(text))
        if n_lists >= 2:
            bits.append(f"{n_lists} list items")
        reasons.append("markdown " + ", ".join(bits) if bits else "markdown")

    if n_latex > MAX_LATEX_BLOCKS_BEFORE_RETRY:
        issues.append("too_many_latex_blocks")
        reasons.append(f"{n_latex} LaTeX blocks (max {MAX_LATEX_BLOCKS_BEFORE_RETRY})")

    if n_sentences > MAX_SENTENCES_BEFORE_RETRY:
        issues.append("too_many_sentences")
        reasons.append(f"{n_sentences} sentences (max ~{MAX_SENTENCES_BEFORE_RETRY})")

    if darija_only_in_tail(text):
        issues.append("darija_only_at_end")
        reasons.append(f"all darija markers sit in the last {int(DARIJA_TAIL_RATIO * 100)}% of the text")

    if _DARIJA_FOOTNOTE_RE.search(text):
        issues.append("darija_as_footnote")
        reasons.append("explicit 'En darija :' / translation-footnote label")

    return {
        "markers": markers,
        "issues": issues,
        "reasons": reasons,
        "n_sentences": n_sentences,
        "n_latex": n_latex,
        "should_retry": bool(issues),
    }


def log_darija_retry(record: dict) -> None:
    """Log one retry event: JSONL line (for stats) + console line (visible)."""
    line = {"at": datetime.now().isoformat(timespec="seconds"), **record}
    try:
        DARIJA_RETRY_LOG.parent.mkdir(parents=True, exist_ok=True)
        with DARIJA_RETRY_LOG.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    except OSError as exc:  # logging must never break the conversation
        print(f"  [darija-check] warning — could not write retry log: {exc}")
    first = record.get("first_markers", [])
    issues = record.get("first_issues") or record.get("issues") or []
    issue_txt = ", ".join(issues) if issues else "trop formelle"
    outcome = record.get("outcome")
    if outcome == "retry_api_error_fallback":
        print(f"  [darija-check] retry API error — keeping first answer ({record.get('error', '')})")
    elif outcome in ("retry_passed", "retry_still_failed"):
        second = record.get("second_markers", [])
        second_issues = record.get("second_issues") or []
        print(f"  [darija-check] R2 {outcome} "
              f"({len(second)} marker(s)"
              f"{'; leftover issues: ' + ', '.join(second_issues) if second_issues else ''})")
    else:
        print(f"  [darija-check] R1 rejected ({issue_txt}; "
              f"{len(first)} marker(s) darija : "
              f"{', '.join(first) if first else 'aucun'} — minimum "
              f"{record.get('min_markers', darija_min_markers())}) "
              f"→ re-génération avec rappel")


def build_retrieval_query(question: str, history: Sequence[dict]) -> str:
    """Return the text to search with, expanding bare follow-ups."""
    previous = next((t["content"] for t in reversed(history) if t.get("role") == "user"), None)
    if not previous:
        return question

    words = [w for w in re.findall(r"\w+", question) if len(w) > 2]
    is_followup = len(words) < MIN_CONTENT_WORDS or bool(FOLLOWUP_RE.search(question))
    if not is_followup:
        return question

    return f"{previous} {question}".strip()


class TutorSession:
    """One conversation: retrieval + prompt assembly + chat completion."""

    def __init__(self, config: Config | None = None, retriever: Retriever | None = None,
                 client: ChatClient | None = None, verbose: bool = True):
        self.config = config or DEFAULT_CONFIG
        self.verbose = verbose
        self.retriever = retriever or Retriever(config=self.config, verbose=verbose)
        self.client = client or ChatClient(config=self.config)
        self.history: list[dict] = []          # plain student/assistant turns
        self.last_hits: list[RetrievedChunk] = []
        self.last_messages: list[dict] = []

    # ------------------------------------------------------------------ #
    def prepare(self, question: str, matiere: str | None = None, chapitre: str | None = None,
                top_k: int | None = None) -> tuple[list[RetrievedChunk], list[dict]]:
        """Retrieve the grounding context and build the request messages.

        Split out from :meth:`ask` so the retrieved sources can still be
        inspected (and saved) when the chat API fails.
        """
        # diverse=True: fetch extra candidates, drop the weak tail, cap
        # duplicates from one file and re-rank with MMR. A tutor answer needs a
        # mix of lesson + example, not six copies of the same exam paper.
        retrieval_query = build_retrieval_query(question, self.history)
        hits = self.retriever.retrieve(
            retrieval_query,
            top_k=top_k or self.config.chat_top_k,
            matiere=matiere,
            chapitre=chapitre,
            diverse=True,
        )
        self.last_hits = hits
        self.last_messages = build_messages(self.history, question, hits)
        return hits, self.last_messages

    def ask(self, question: str, matiere: str | None = None, chapitre: str | None = None,
            top_k: int | None = None) -> dict:
        """Answer one student question. Returns a dict with answer + sources.

        Includes a ``darija_check`` field: how many darija markers the answer
        contained, which quality issues fired (markdown / length / latex /
        darija-only-at-the-end), and whether the retry was triggered.
        """
        hits, messages = self.prepare(question, matiere=matiere, chapitre=chapitre, top_k=top_k)
        min_markers = darija_min_markers()
        turn_index = sum(1 for t in self.history if t["role"] == "user") + 1

        answer = self.client.complete(messages).content
        first = assess_response(answer, min_markers=min_markers)
        darija_check: dict = {
            "min_markers": min_markers,
            "attempt": 1,
            "retried": False,
            "markers": first["markers"],
            "issues": first["issues"],
            "reasons": first["reasons"],
            "n_sentences": first["n_sentences"],
            "n_latex": first["n_latex"],
            "outcome": "ok",
        }

        if first["should_retry"]:
            reminder = retry_reminder_for(first["issues"])
            log_darija_retry({
                "model": self.client.model,
                "turn_index": turn_index,
                "question_preview": question[:120],
                "min_markers": min_markers,
                "first_markers": first["markers"],
                "first_issues": first["issues"],
                "first_reasons": first["reasons"],
                "n_sentences": first["n_sentences"],
                "n_latex": first["n_latex"],
                "reminder": reminder,
            })
            darija_check["retried"] = True
            darija_check["first_markers"] = first["markers"]
            darija_check["first_issues"] = first["issues"]
            darija_check["first_reasons"] = first["reasons"]
            darija_check["first_answer"] = answer
            darija_check["reminder"] = reminder
            # The reminder refers to the model's OWN last reply, so the failed
            # answer is replayed to it as an assistant turn first.
            retry_messages = messages + [
                {"role": "assistant", "content": answer},
                {"role": "user", "content": reminder},
            ]
            try:
                answer = self.client.complete(retry_messages).content
            except ChatError as exc:
                # The first (formal) answer is still a usable answer: keep it
                # rather than losing the whole turn to a failed retry call.
                darija_check["outcome"] = "retry_api_error_fallback"
                darija_check["retry_error"] = str(exc)
                log_darija_retry({
                    "model": self.client.model,
                    "turn_index": turn_index,
                    "question_preview": question[:120],
                    "first_issues": first["issues"],
                    "outcome": "retry_api_error_fallback",
                    "error": str(exc),
                })
            else:
                second = assess_response(answer, min_markers=min_markers)
                darija_check["attempt"] = 2
                darija_check["markers"] = second["markers"]
                darija_check["issues"] = second["issues"]
                darija_check["reasons"] = second["reasons"]
                darija_check["n_sentences"] = second["n_sentences"]
                darija_check["n_latex"] = second["n_latex"]
                darija_check["outcome"] = ("retry_passed"
                                           if not second["should_retry"]
                                           else "retry_still_failed")
                log_darija_retry({
                    "model": self.client.model,
                    "turn_index": turn_index,
                    "question_preview": question[:120],
                    "first_markers": first["markers"],
                    "first_issues": first["issues"],
                    "second_markers": second["markers"],
                    "second_issues": second["issues"],
                    "second_reasons": second["reasons"],
                    "outcome": darija_check["outcome"],
                })

        # Keep the history clean: store the bare question, not the grounded
        # prompt, so old passages are not replayed on every turn.
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})

        return {"question": question, "answer": answer, "sources": hits,
                "messages": messages, "darija_check": darija_check}

    def reset(self) -> None:
        self.history.clear()
        self.last_hits = []
        self.last_messages = []


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #
def print_sources(hits, max_chars: int = 160) -> None:
    if not hits:
        print("  (aucune source récupérée)")
        return
    print(f"  {len(hits)} extrait(s) utilisé(s) comme contexte :")
    for i, hit in enumerate(hits, start=1):
        meta = hit.metadata
        place = " | ".join(
            p for p in (meta.get("matiere"), meta.get("chapitre") or meta.get("semestre"),
                        meta.get("sujet") or meta.get("seance"), meta.get("type")) if p
        )
        preview = " ".join(hit.content.split())[:max_chars]
        print(f"    [Source {i}] {hit.score:.3f}  {place}")
        print(f"              {meta.get('file_path', '')} "
              f"(extrait {meta.get('chunk_index')}/{meta.get('n_chunks')}, ligne ~{meta.get('start_line')})")
        print(f"              {preview}…")


def print_answer(answer: str, hits, show_sources: bool = True) -> None:
    print()
    print("PROF :")
    for line in answer.split("\n"):
        print(f"  {line}" if line.strip() else "")
    if show_sources:
        print()
        print("  " + _rule("─"))
        print_sources(hits)
        print("  " + _rule("─"))
    print()


def save_transcript(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


# --------------------------------------------------------------------------- #
# Interactive loop
# --------------------------------------------------------------------------- #
def interactive(session: TutorSession, matiere: str | None, chapitre: str | None,
                save_path: Path | None) -> int:
    print(_rule("═"))
    print("  Tuteur 2Bac SM — Mathématiques / Physique-Chimie / SVT")
    print(f"  modèle : {session.client.model}")
    print(f"  filtres : matière={matiere or '(aucune)'}  chapitre={chapitre or '(aucun)'}")
    print("  /help pour les commandes, /quit pour sortir")
    print(_rule("═"))
    print()

    while True:
        try:
            raw = input("TOI : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÀ bientôt !")
            return 0

        if not raw:
            continue
        if raw.lower() in ("/quit", "/exit", "quit", "exit"):
            print("À bientôt !")
            return 0
        if raw.lower() in ("/help", "/aide"):
            print(HELP)
            continue
        if raw.lower() == "/reset":
            session.reset()
            print("  (historique effacé)")
            continue
        if raw.lower() == "/sources":
            print_sources(session.last_hits)
            continue
        if raw.lower() == "/prompt":
            print(json.dumps(session.last_messages, ensure_ascii=False, indent=2)[:4000])
            continue

        if raw.lower().startswith("/matiere"):
            value = raw.split(" ", 1)[1].strip() if " " in raw else ""
            matiere = None if value.lower() in ("off", "none", "") else value
            print(f"  matière = {matiere or '(aucune)'}")
            continue
        if raw.lower().startswith("/chapitre"):
            value = raw.split(" ", 1)[1].strip() if " " in raw else ""
            chapitre = None if value.lower() in ("off", "none", "") else value
            print(f"  chapitre = {chapitre or '(aucun)'}")
            continue

        try:
            result = session.ask(raw, matiere=matiere, chapitre=chapitre)
        except ChatError as exc:
            print(f"\n[erreur API] {exc}\n")
            continue
        print_answer(result["answer"], result["sources"])

        if save_path:
            save_transcript(save_path, {
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "model": session.client.model,
                "history": session.history,
            })


# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Chat with the 2bac AI tutor (plain text).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=HELP,
    )
    parser.add_argument("--question", "-q", help="ask a single question and exit")
    parser.add_argument("--matiere", help="filter retrieval by subject")
    parser.add_argument("--chapitre", help="filter retrieval by chapter/semester")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--no-sources", action="store_true", help="hide the sources block")
    parser.add_argument("--save", type=Path, default=None, help="write the transcript to this JSON file")
    parser.add_argument("--model", default=None, help="override CHAT_MODEL")
    args = parser.parse_args(argv)

    if DEFAULT_CONFIG.chat_key_is_placeholder():
        print("CHAT_API_KEY is not set. Copy .env.example to .env and fill it in "
              "(or export CHAT_API_KEY=...).")
        return 1

    session = TutorSession(verbose=True)
    if args.model:
        session.client.model = args.model

    if session.retriever.store.count() == 0:
        print("The vector index is empty. Build it first:  python ingest.py")
        return 1

    if args.question:
        try:
            result = session.ask(args.question, matiere=args.matiere,
                                 chapitre=args.chapitre, top_k=args.top_k)
        except ChatError as exc:
            print(f"[erreur API] {exc}")
            return 1
        print(f"\nTOI : {args.question}")
        print_answer(result["answer"], result["sources"], show_sources=not args.no_sources)
        if args.save:
            save_transcript(args.save, {
                "saved_at": datetime.now().isoformat(timespec="seconds"),
                "model": session.client.model,
                "history": session.history,
            })
            print(f"transcript saved to {args.save}")
        return 0

    return interactive(session, args.matiere, args.chapitre, args.save)


if __name__ == "__main__":
    sys.exit(main())
