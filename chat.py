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
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence

from rag.config import DEFAULT_CONFIG, Config
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
        """Answer one student question. Returns a dict with answer + sources."""
        hits, messages = self.prepare(question, matiere=matiere, chapitre=chapitre, top_k=top_k)

        answer = self.client.complete(messages).content

        # Keep the history clean: store the bare question, not the grounded
        # prompt, so old passages are not replayed on every turn.
        self.history.append({"role": "user", "content": question})
        self.history.append({"role": "assistant", "content": answer})

        return {"question": question, "answer": answer, "sources": hits, "messages": messages}

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
