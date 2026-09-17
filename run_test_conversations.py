#!/usr/bin/env python3
"""Run the 5 scripted tutor conversations and save the transcripts.

This is the teaching-quality review harness: five conversations that between
them cover a maths concept, a physics exercise, an SVT question, a
"je n'ai pas compris" follow-up, and a student demanding an exam answer
outright (to confirm the tutor guides instead of just answering).

    python run_test_conversations.py                 # writes transcripts/
    python run_test_conversations.py --only svt      # just one scenario
    python run_test_conversations.py --top-k 8       # ground on more chunks

If the chat API cannot be reached the script still writes each transcript,
marking it INCOMPLETE, so you can see the grounding context that *would* have
been sent and re-run later with:  python run_test_conversations.py
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from rag.config import DEFAULT_CONFIG
from rag.llm import ChatError
from rag.prompts import SYSTEM_PROMPT
from chat import TutorSession

OUT_DIR = Path(__file__).resolve().parent / "transcripts"

# --------------------------------------------------------------------------- #
# The five scenarios. Student turns are written the way a 2bac student types.
# --------------------------------------------------------------------------- #
CONVERSATIONS: list[dict] = [
    {
        "id": "1-maths-concept",
        "title": "Mathématiques — question de concept (limites)",
        "goal": "Expliquer un concept du programme : la limite d'une fonction en un point.",
        "matiere": "Mathématiques",
        "chapitre": None,
        "turns": [
            "Saha prof, je comprends pas bien c'est quoi la limite d'une fonction. Tu peux m'expliquer ?",
        ],
    },
    {
        "id": "2-physique-exercice",
        "title": "Physique-Chimie — énoncé d'exercice (ondes mécaniques)",
        "goal": "Accompagner un élève sur un exercice sans donner la réponse : il doit être guidé.",
        "matiere": "Physique-Chimie",
        "chapitre": None,
        "turns": [
            "Prof, j'ai un exercice et je sais pas par où commencer. Le voici : un vibreur provoque à "
            "l'extrémité S d'une corde élastique un mouvement vibratoire sinusoïdal d'équation "
            "$y_s(t) = a.cos(2\\pi Nt + \\varphi)$. La source S débute son mouvement à t0 = 0 s. "
            "On néglige toute atténuation. 1. L'expression « mouvement vibratoire sinusoïdal » peut "
            "être remplacée par un seul mot, lequel ? 2. L'onde qui se propage le long de la corde "
            "est-elle transversale ou longitudinale ? Justifier. Aide-moi à réfléchir.",
        ],
    },
    {
        "id": "3-svt-question",
        "title": "SVT — question de cours (méiose et réduction chromatique)",
        "goal": "Expliquer la méiose et la réduction chromatique, en restant dans le programme.",
        "matiere": "SVT",
        "chapitre": None,
        "turns": [
            "SVP prof, c'est quoi la méiose exactement ? Et la réduction chromatique, ça veut dire quoi ? "
            "J'ai du mal à faire la différence avec la mitose.",
        ],
    },
    {
        "id": "4-pas-compris",
        "title": "Reformulation — « je n'ai pas compris »",
        "goal": "Vérifier qu'après un « j'ai pas compris », le prof change d'approche au lieu de répéter.",
        "matiere": "Mathématiques",
        "chapitre": None,
        "turns": [
            "Prof, c'est quoi un nombre complexe et à quoi ça sert ?",
            "Franchement j'ai pas compris, tu peux me réexpliquer ?",
        ],
    },
    {
        "id": "5-examen-reponse",
        "title": "Demande directe d'une réponse d'examen (SVT bac 2024)",
        "goal": "Le prof doit d'abord guider, et ne donner la correction complète que si l'élève insiste.",
        "matiere": "SVT",
        "chapitre": None,
        "turns": [
            "Prof donne-moi direct la réponse de l'exercice 1 du bac SVT 2024 session normale : "
            "définir méiose et caryotype. J'ai pas le temps de réfléchir.",
            "Oui mais moi je veux juste la correction complète s'il te plaît, donne-la moi directement.",
        ],
    },
]


# --------------------------------------------------------------------------- #
# Transcript rendering
# --------------------------------------------------------------------------- #
def render_sources_md(hits: list[dict], max_chars: int = 220) -> str:
    """Render the stored source dicts ({score, content, metadata})."""
    if not hits:
        return "_Aucun extrait récupéré._"
    lines = []
    for i, hit in enumerate(hits, start=1):
        meta = hit.get("metadata", {})
        score = hit.get("score", 0.0)
        content = hit.get("content", "")
        place = " | ".join(
            p for p in (meta.get("matiere"), meta.get("chapitre") or meta.get("semestre"),
                        meta.get("sujet") or meta.get("seance"), meta.get("type")) if p
        )
        body = content.strip().replace("\n", " ")
        if len(body) > max_chars:
            body = body[:max_chars].rstrip() + " …"
        lines.append(
            f"- **[Source {i}]** (score {score:.3f}) {place}\n"
            f"  - fichier : `{meta.get('file_path', '')}` "
            f"(extrait {meta.get('chunk_index')}/{meta.get('n_chunks')}, ligne ~{meta.get('start_line')})\n"
            f"  - extrait : {body}"
        )
    return "\n".join(lines)


def build_markdown(record: dict) -> str:
    out = [
        f"# {record['title']}",
        "",
        f"- **Scénario** : `{record['id']}`",
        f"- **Objectif** : {record['goal']}",
        f"- **Généré le** : {record['generated_at']}",
        f"- **Modèle** : `{record['model']}`",
        f"- **Filtres** : matière = {record['matiere'] or '(aucune)'}, "
        f"chapitre = {record['chapitre'] or '(aucun)'}",
        f"- **Statut** : {record['status']}",
        "",
        "---",
        "",
    ]
    for turn in record["turns"]:
        out += ["## 🧑 Élève", "", f"> {turn['question']}", ""]
        if turn.get("error"):
            out += [f"**Erreur API :** `{turn['error']}`", ""]
        out += ["## 👨‍🏫 Prof", "", turn.get("answer") or "_aucune réponse_", ""]
        out += ["### Sources utilisées pour cette réponse", ""]
        out += [render_sources_md(turn["sources"]), ""]
        out += ["---", ""]
    return "\n".join(out)


# --------------------------------------------------------------------------- #
def run_conversation(spec: dict, session_factory, top_k: int | None) -> dict:
    session = session_factory()
    record = {
        "id": spec["id"],
        "title": spec["title"],
        "goal": spec["goal"],
        "matiere": spec["matiere"],
        "chapitre": spec.get("chapitre"),
        "model": session.client.model,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "turns": [],
        "status": "OK",
    }

    print(f"\n{'=' * 96}\n{spec['title']}\n{spec['goal']}\n{'=' * 96}")

    for question in spec["turns"]:
        print(f"\n🧑 ÉLÈVE : {question}\n")
        try:
            result = session.ask(question, matiere=spec["matiere"],
                                 chapitre=spec.get("chapitre"), top_k=top_k)
            answer, error = result["answer"], None
            sources = result["sources"]
            print("👨‍🏫 PROF :")
            for line in answer.split("\n"):
                print(f"  {line}" if line.strip() else "")
        except ChatError as exc:
            # Keep the retrieved context: it is still worth reviewing, and the
            # transcript can be completed by re-running once the API answers.
            sources, _ = session.prepare(question, matiere=spec["matiere"],
                                         chapitre=spec.get("chapitre"), top_k=top_k)
            answer, error = "", str(exc)
            record["status"] = f"INCOMPLETE — {type(exc).__name__}"
            print(f"  [erreur API] {exc}")

        print("\n  Sources :")
        for i, hit in enumerate(sources, start=1):
            meta = hit.metadata
            place = " | ".join(
                p for p in (meta.get("matiere"), meta.get("chapitre") or meta.get("semestre"),
                            meta.get("sujet") or meta.get("seance")) if p)
            print(f"    [Source {i}] {hit.score:.3f}  {place}")
            print(f"              {meta.get('file_path', '')}")

        record["turns"].append({
            "question": question,
            "answer": answer,
            "error": error,
            "sources": [
                {"score": round(h.score, 6), "content": h.content, "metadata": h.metadata}
                for h in sources
            ],
        })

    return record


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run and save the 5 tutor test conversations.")
    parser.add_argument("--only", default=None, help="run just one scenario id (substring match)")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)

    if DEFAULT_CONFIG.chat_key_is_placeholder():
        print("CHAT_API_KEY is not set. Copy .env.example to .env and fill it in.")
        return 1

    selected = CONVERSATIONS
    if args.only:
        selected = [c for c in CONVERSATIONS if args.only in c["id"]]
        if not selected:
            print(f"No scenario matching {args.only!r}. Available: "
                  f"{', '.join(c['id'] for c in CONVERSATIONS)}")
            return 1

    def factory() -> TutorSession:
        return TutorSession(verbose=False)

    args.out.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []

    for spec in selected:
        record = run_conversation(spec, factory, args.top_k)
        md_path = args.out / f"{record['id']}.md"
        json_path = args.out / f"{record['id']}.json"
        md_path.write_text(build_markdown(record), encoding="utf-8")
        json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append({"id": record["id"], "title": record["title"], "status": record["status"],
                      "turns": len(record["turns"]), "md": md_path.name, "json": json_path.name})
        print(f"\n  -> saved {md_path}")

    (args.out / "index.json").write_text(
        json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "model": DEFAULT_CONFIG.chat_model,
            "system_prompt_chars": len(SYSTEM_PROMPT),
            "conversations": index,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'=' * 96}\n{len(index)} transcript(s) written to {args.out}/")
    for item in index:
        print(f"  - {item['md']:<28} {item['status']}")
    failures = [i for i in index if i["status"] != "OK"]
    if failures:
        print(f"\n{len(failures)} conversation(s) incomplete (API unreachable). "
              "The grounding context is still saved — re-run once the API is reachable.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
