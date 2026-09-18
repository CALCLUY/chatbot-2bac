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

Anti-drift safeguard (darija check)
    The model tends to drift back to pure formal French on long
    conversations. Every generated answer is therefore scanned for darija
    markers (DARIJA_MARKERS); if fewer than the minimum (CHAT_DARIJA_MIN_MARKERS,
    default 2) distinct markers are found, the completion is retried ONCE
    with an explicit darija reminder appended. Each retry is logged to the
    console and to logs/darija_retry_log.jsonl so you can measure how often
    the model drifts and whether the retry fixes it.
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

DARIJA_RETRY_LOG = Path(
    os.getenv("CHAT_DARIJA_RETRY_LOG", str(REPO_ROOT / "logs" / "darija_retry_log.jsonl"))
)


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
    print(f"  [darija-check] R1 trop formelle ({len(first)} marker(s) darija : "
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
        contained and whether the anti-drift retry was triggered (see
        DARIJA_MARKERS above).
        """
        hits, messages = self.prepare(question, matiere=matiere, chapitre=chapitre, top_k=top_k)
        min_markers = darija_min_markers()
        turn_index = sum(1 for t in self.history if t["role"] == "user") + 1

        answer = self.client.complete(messages).content
        first_markers = find_darija_markers(answer)
        darija_check: dict = {
            "min_markers": min_markers,
            "attempt": 1,
            "retried": False,
            "markers": first_markers,
            "outcome": "ok",
        }

        if len(first_markers) < min_markers:
            # --- anti-drift safeguard: the answer is (almost) pure French ---
            log_darija_retry({
                "model": self.client.model,
                "turn_index": turn_index,
                "question_preview": question[:120],
                "min_markers": min_markers,
                "first_markers": first_markers,
            })
            darija_check["retried"] = True
            darija_check["first_markers"] = first_markers
            # The reminder refers to the model's OWN last reply, so the failed
            # answer is replayed to it as an assistant turn first.
            retry_messages = messages + [
                {"role": "assistant", "content": answer},
                {"role": "user", "content": DARIJA_RETRY_REMINDER},
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
                    "outcome": "retry_api_error_fallback",
                    "error": str(exc),
                })
            else:
                from_markers = find_darija_markers(answer)
                darija_check["attempt"] = 2
                darija_check["markers"] = from_markers
                darija_check["outcome"] = ("retry_passed"
                                           if len(from_markers) >= min_markers
                                           else "retry_still_failed")
                log_darija_retry({
                    "model": self.client.model,
                    "turn_index": turn_index,
                    "question_preview": question[:120],
                    "first_markers": first_markers,
                    "second_markers": from_markers,
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
