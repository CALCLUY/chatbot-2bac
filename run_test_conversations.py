#!/usr/bin/env python3
"""Run the 10 scripted tutor conversations and save the transcripts.

This is the teaching-quality review harness. Ten conversations: the five
original scenarios (a maths concept, a physics exercise, an SVT question, a
"je n'ai pas compris" follow-up, and a student demanding an exam answer
outright), four v2-prompt edge cases: a multi-turn conversation where the
student makes a mistake (context memory + patience), a discouraged student
("ma fahemch walou, khasni no9ta"), a stubborn student who insists on the exam
answer three times in a row, and questions entirely outside the curriculum —
plus scenario 10, a 10-turn conversation on one math topic (limites) built
specifically to test the darija-French mix over a LONG conversation: the
student follows up, makes a mistake, says "je n'ai pas compris", and asks a
couple of questions in plain French.

Each saved turn also carries the output of the code-level darija check
(chat.py: DARIJA_MARKERS): how many darija markers the answer contained and
whether the anti-drift retry was triggered and fixed it.

    python run_test_conversations.py                 # writes transcripts/
    python run_test_conversations.py --only svt      # just one scenario
    python run_test_conversations.py --only 6 --only 7   # a subset
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
        "goal": "Le prof doit d'abord guider. ATTENTION — contrat modifié par le prompt v2 : "
                "l'insistance seule ne suffit PLUS. La règle 4 exige >= 2 échanges de guidage "
                "ET une demande explicite. Ici l'élève ne suit aucun guidage (2 simples "
                "demandes), donc la correction complète ne doit PAS être révélée, même au "
                "tour 2. Les tours sont inchangés par rapport à la v1 pour rester comparable.",
        "matiere": "SVT",
        "chapitre": None,
        "turns": [
            "Prof donne-moi direct la réponse de l'exercice 1 du bac SVT 2024 session normale : "
            "définir méiose et caryotype. J'ai pas le temps de réfléchir.",
            "Oui mais moi je veux juste la correction complète s'il te plaît, donne-la moi directement.",
        ],
    },

    # --------------------------------------------------------------------- #
    # Edge cases added for the v2 prompt review (scénarios 6-9).
    # Each one targets a rule that the v2 system prompt introduced or
    # tightened; the `goal` field states the acceptance criterion to check.
    # --------------------------------------------------------------------- #
    {
        "id": "6-multi-tour-erreur",
        "title": "Multi-tour — l'élève se trompe (limites, mémoire du contexte)",
        "goal": "Vérifier la MÉMOIRE DU CONTEXTE et la PATIENCE : l'élève propose une "
                "réponse fausse, puis sur-généralise à partir de son erreur. Le prof doit "
                "(a) corriger sans condescendance, (b) ne pas valider la fausse règle, "
                "(c) au dernier tour se souvenir de l'erreur précise du 2e tour sans que "
                "l'élève la répète. Échec si le prof perd le fil ou se répète mot pour mot.",
        "matiere": "Mathématiques",
        "chapitre": None,
        "turns": [
            "Saha prof, 3endi had l'exercice : $\\lim_{x \\to 2} \\frac{x^2 - 4}{x - 2}$. "
            "Kifach nbda ?",
            "Ana jarrabt : 7it $x^2 - 4$ kat3ti 0 f $x = 2$, donc l jawab howa 0. Wach s7i7 ?",
            "Ah... walakin mazal ma fhemtch 3lach. Wach kol limite li l numérateur dialha "
            "kayt3adel kat3ti 0 ? 7ta f $\\lim_{x \\to 3} \\frac{x^2 - 9}{x - 3}$ ?",
            "Safi daba fhemt. T9der t3awed liya chno kan l'ghalat diali l'awal, w chno "
            "l jawab l7a9i9i, bach ma n3awdouch f l'examen ?",
        ],
    },
    {
        "id": "7-eleve-decourage",
        "title": "Élève découragé — « ma fahemch walou, khasni no9ta »",
        "goal": "Vérifier la PATIENCE sous frustration : l'élève abandonne et réclame juste "
                "la note. Le prof doit rester encourageant, NE PAS lâcher la réponse "
                "complète pour calmer la frustration, et réduire encore la difficulté "
                "(une seule petite étape, une autre analogie). Échec s'il donne le résultat "
                "final ou s'il répète la même explication.",
        "matiere": "Mathématiques",
        "chapitre": None,
        "turns": [
            "Prof, 3endi devoir f les limites : $\\lim_{x \\to +\\infty} "
            "\\frac{3x^2 - x + 1}{2x^2 + 5}$. Chno ndir ?",
            "Ma fahemch walou, khasni no9ta. 3tini ghir l jawab safi, ma 3endi wa9t.",
            "Wallah ma 9adr nkamel, kolchi sa3b 3liya. Ghadi n9elleb 3la l7al f internet.",
        ],
    },
    {
        "id": "8-eleve-obsine-reponse-examen",
        "title": "Élève obstiné — réclame la réponse d'examen 3 fois de suite",
        "goal": "Vérifier que le PROCESSUS EN 4 ÉTAPES tient : 3 demandes insistantes de "
                "suite (dont un « wrini l7al » explicite au tour 3) ne doivent PAS "
                "déclencher la correction complète, parce que l'élève n'a encore suivi "
                "aucun échange de guidage. Au tour 4 seulement — après avoir proposé sa "
                "propre tentative ET redemandé la correction — le prof peut révéler la "
                "solution, étape par étape. Échec s'il cède avant le tour 4, ou s'il donne "
                "le résultat brut au tour 4.",
        "matiere": "Mathématiques",
        "chapitre": None,
        "turns": [
            "Prof, 3tini direct l jawab dial l'exercice 3 dial l'examen national math 2023 "
            "session normale, question 1-b) : $(1 - i)(1 + i\\sqrt{3}) = "
            "2\\sqrt{2}e^{i\\frac{\\pi}{12}}$. Ma 3endi wa9t n'feker.",
            "La, ma bghitch n'feker w ma bghitch l'indices. 3tini l jawab, safi.",
            "Nta kat3awd nfs l7aj. Ana kanbghi l jawab w bass. Wrini l7al daba.",
            "Wakha... jarrabt : $1 - i = \\sqrt{2}e^{-i\\frac{\\pi}{4}}$ w "
            "$1 + i\\sqrt{3} = 2e^{i\\frac{\\pi}{3}}$. Wach hada s7i7 ? Daba wrini "
            "l correction kamla 3afak.",
        ],
    },
    {
        "id": "9-hors-programme",
        "title": "Hors programme — questions en dehors du curriculum",
        "goal": "Vérifier l'HONNÊTETÉ : crypto/finance, astronomie (hors programme 2bac), "
                "puis programmation. Le prof doit dire clairement que ce n'est PAS dans le "
                "programme fourni et ne PAS inventer de réponse, puis ramener l'élève vers "
                "les Maths / Physique-Chimie / SVT. Échec s'il répond avec des chiffres, "
                "des faits non sourcés, ou des [Source N] plaqués sur du hors-programme.",
        "matiere": None,
        "chapitre": None,
        "turns": [
            "Prof, ch7al kayswa l bitcoin lyoum ? W wach n9der ndkhol l l'crypto b 500 dh "
            "w nreba7 ?",
            "W 3afak, ch7al mn kawkab kayn f l'mjara dialna ? W kifach khdam télescope "
            "James Webb b detail ?",
            "Okay wakha. Walakin 3lemni Python mn l'awal, bghit n'welli développeur.",
        ],
    },

    # --------------------------------------------------------------------- #
    # Drift test (added with the darija-reinforcement prompt section).
    # A single LONG conversation (10 turns) on one Mathématiques topic —
    # les limites — where the student follows up, makes a mistake (turn 5),
    # says "je n'ai pas compris" (turn 7) and asks several questions in
    # plain French (turns 3, 6, 9). Acceptance criterion for the review:
    # the darija-French mix must hold from turn 1 to turn 10; if it drifts
    # back to pure French, the darija_check field of each turn shows at
    # which turn it happened and whether the retry safeguard caught it.
    # --------------------------------------------------------------------- #
    {
        "id": "10-drift-long-limites",
        "title": "Test de drift — conversation longue (10 tours, limites en Mathématiques)",
        "goal": "Vérifier que le MÉLANGE DARIJA-FRANÇAIS tient sur une conversation "
                "longue (10 tours), et non pas seulement sur 1-2 échanges. L'élève "
                "pose des questions de suivi, se trompe (tour 5), dit « j'ai pas "
                "compris » (tour 7) et pose plusieurs questions en français "
                "standard (tours 3, 6, 9). Échec si un prof-réponse devient un "
                "paragraphe français pur sans expression darija — y compris vers "
                "la fin de la conversation. Le champ darija_check de chaque tour "
                "(marqueurs détectés, retry déclenché, résultat du retry) permet "
                "de localiser exactement le tour où le drift commence.",
        "matiere": "Mathématiques",
        "chapitre": None,
        "turns": [
            # T1 — ouverture, mélange darija/français (la question habituelle)
            "Saha prof, nta l7in. 3andi s7i7 b les limites, ma 9drtch n3ref kifach "
            "n7ssbha. T9der tjib l'idée m3aya 9bel les calculs ?",
            # T2 — question de suivi en darija
            "Tsawwar m3aya ok. Walakin chno 3la3t l'idée hadi m3a les limites d'une "
            "fonction f l'examen ? Kifach katban f les exercices ?",
            # T3 — question en FRANÇAIS standard (test: la réponse doit rester darija-français)
            "En fait, j'ai une question : pourquoi on ne peut pas toujours remplacer "
            "x par sa valeur dans l'expression ? Ce n'est pas très logique pour moi.",
            # T4 — suivi en darija avec expression concrète
            "Wakha. Daba chouf hada l'exemple : $\\lim_{x \\to 2} \\frac{x^2 - 4}{x - 2}$. "
            "7it l numérateur w l dénominateur kayt3adelu 3la 0, chno ndir f had l7ala?",
            # T5 — l'élève SE TROMPE (doit être corrigé sans condescendance)
            "Ahh ana jarrabt : 7it l numérateur 0 w l dénominateur 0, donc l limite "
            "howa 0. Wach s7i7 had l jawab ? Sana khassni njawb hadchi f l'examen.",
            # T6 — question en FRANÇAIS standard (2e question en français)
            "Ah d'accord, c'est une forme indéterminée. Donc est-ce que c'est toujours "
            "la même méthode quand on a 0/0, ou il y a des cas différents ?",
            # T7 — « je n'ai pas compris » : le prof DOIT changer d'approche
            "Franchement, j'ai pas compris l'explication dial la factorisation. Kifach "
            "twere9 $x^2 - 4$ bach nchoufo f l'exercice ? Reexplique ghir hadchi b "
            "wa7ed l'exemple bsit.",
            # T8 — suivi en darija vers +infini
            "Safi daba fhemt had l7aja. W chno y9en $+\\infty$ f "
            "$\\lim_{x \\to +\\infty}$ ? 9ed s7i7 3la les polynômes, kifach n7ssb "
            "la limite li l degrés ma kayt3adelouch ?",
            # T9 — question en FRANÇAIS standard (3e question en français)
            "Et pour un polynôme de degré 2 sur degré 2, par exemple "
            "(3x² - x + 1) / (2x² + 5), la méthode c'est de diviser le numérateur et "
            "le dénominateur par x² ? Est-ce que ça marche toujours quand les degrés "
            "sont égaux ?",
            # T10 — l'élève résume lui-même, demande de la pratique
            "Wakha prof, daba 9olt l7al mn rasi: 9ed les degrés walo, l limite howa "
            "l rapport dial les coefficients dial l plus grande puissance. S7i7 hadchi "
            "li fhemt? Bghit n'3awed 3la 2-3 exercices bach tkoun 9ayna s7i7 l'examen.",
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
        out += render_darija_check_md(turn.get("darija_check"))
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
        darija_check = None
        try:
            result = session.ask(question, matiere=spec["matiere"],
                                 chapitre=spec.get("chapitre"), top_k=top_k)
            answer, error = result["answer"], None
            sources = result["sources"]
            darija_check = result.get("darija_check")
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
            "darija_check": darija_check,
            "sources": [
                {"score": round(h.score, 6), "content": h.content, "metadata": h.metadata}
                for h in sources
            ],
        })

    return record


# --------------------------------------------------------------------------- #
# Darija-check rendering (anti-drift safeguard stats, see chat.py)
# --------------------------------------------------------------------------- #
def render_darija_check_md(check: dict | None) -> list[str]:
    """One line under a prof answer describing the darija-marker check."""
    if not check:
        return []
    issues = check.get("first_issues") or check.get("issues") or []
    issue_txt = f" ; issues={issues}" if issues else ""
    if not check.get("retried"):
        return [f"_(darija-check : {len(check.get('markers', []))} marker(s) darija — "
                f"OK, pas de retry{issue_txt})_", ""]
    first = check.get("first_markers", [])
    first_names = "(" + ", ".join(first) + ")" if first else "aucun"
    if check.get("outcome") == "retry_api_error_fallback":
        return [f"_(darija-check : {len(first)} marker(s){issue_txt} — retry déclenché, mais l'appel "
                f"de re-génération a échoué → réponse 1 conservée)_", ""]
    second = check.get("markers", [])
    second_issues = check.get("issues") or []
    verdict = {"retry_passed": "retry corrigé ✅",
               "retry_still_failed": "retry ÉCHOUÉ (qualité encore insuffisante) ⚠️"}.get(
                   check.get("outcome", ""), "retry déclenché")
    return [f"_(darija-check : {len(first)} marker(s) au 1er essai {first_names}{issue_txt} "
            f"→ **RETRY DÉCLENCHÉ** — 2e essai : {len(second)} marker(s)"
            f"{', issues=' + str(second_issues) if second_issues else ''}, {verdict})_", ""]


def darija_stats(records: list[dict]) -> str:
    """One-paragraph summary of the darija-check across all saved turns."""
    total = retried = passed = still_failed = fallback = 0
    drifting_turns: list[str] = []
    for rec in records:
        for i, turn in enumerate(rec["turns"], start=1):
            check = turn.get("darija_check")
            if not check or not check.get("retried"):
                total += 1
                continue
            total += 1
            retried += 1
            where = f"{rec['id']} · tour {i}"
            if check.get("outcome") == "retry_passed":
                passed += 1
            elif check.get("outcome") == "retry_still_failed":
                still_failed += 1
                drifting_turns.append(where)
            else:
                fallback += 1
                drifting_turns.append(where + " (retry API error)")
    lines = [
        "## Darija-check (safeguard anti-drift)",
        "",
        f"- Tours analysés : **{total}**",
        f"- Retry déclenché : **{retried}**"
        + (f" ({retried / total:.0%})" if total else ""),
    ]
    if retried:
        lines += [
            f"-  - corrigé au 2e essai : **{passed}**",
            f"-  - échec persistant (drift réel non corrigé) : **{still_failed}**",
            f"-  - erreur API pendant le retry (réponse 1 conservée) : **{fallback}**",
        ]
        if drifting_turns:
            lines += ["- Tours en échec / à relire : " + ", ".join(drifting_turns)]
        else:
            lines += ["- Aucun tour en échec : toutes les réponses ont fini avec "
                      "assez de marqueurs darija."]
    else:
        lines += ["- Aucune réponse n'est passée sous le seuil : le modèle n'a pas "
                  "dérivé vers le français pur sur ce lot."]
    lines += [f"- Journal détaillé : `logs/darija_retry_log.jsonl`", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Preflight
# --------------------------------------------------------------------------- #
def preflight(timeout: float = 20.0) -> tuple[bool, str]:
    """One cheap probe of the chat endpoint, so a dead relay is reported in
    seconds instead of after 21 turns x 3 retries each.

    Returns (reachable, human-readable message). Never raises.
    """
    from rag.llm import ChatClient, ChatError

    client = ChatClient(timeout=timeout, max_retries=0)
    try:
        reply = client.complete([{"role": "user", "content": "ping"}])
        return True, f"endpoint reachable (model replied: {reply.model})"
    except ChatError as exc:
        return False, str(exc)
    except Exception as exc:                          # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run and save the 10 tutor test conversations.")
    parser.add_argument("--only", action="append", default=None,
                        help="run just these scenario ids (substring match); repeatable")
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    parser.add_argument("--skip-preflight", action="store_true",
                        help="do not probe the chat endpoint before running")
    parser.add_argument("--require-live", action="store_true",
                        help="abort instead of writing INCOMPLETE transcripts when the "
                             "endpoint is unreachable")
    args = parser.parse_args(argv)

    if DEFAULT_CONFIG.chat_key_is_placeholder():
        print("CHAT_API_KEY is not set. Copy .env.example to .env and fill it in.")
        return 1

    if not args.skip_preflight:
        ok, message = preflight()
        if ok:
            print(f"[preflight] OK — {message}")
        else:
            print(f"[preflight] FAILED — {message}")
            print(f"[preflight]   CHAT_BASE_URL = {DEFAULT_CONFIG.chat_base_url}")
            print(f"[preflight]   CHAT_MODEL    = {DEFAULT_CONFIG.chat_model}")
            print("[preflight] Set a reachable OpenAI-compatible endpoint in .env "
                  "(CHAT_BASE_URL / CHAT_API_KEY / CHAT_MODEL).")
            if args.require_live:
                print("[preflight] --require-live given, aborting. Nothing was written.")
                return 1
            print("[preflight] Continuing anyway: transcripts will be written INCOMPLETE, "
                  "with the grounding context intact, so you can review it now and re-run "
                  "once the endpoint answers.")

    selected = CONVERSATIONS
    if args.only:
        selected = [c for c in CONVERSATIONS if any(needle in c["id"] for needle in args.only)]
        if not selected:
            print(f"No scenario matching {args.only!r}. Available: "
                  f"{', '.join(c['id'] for c in CONVERSATIONS)}")
            return 1

    def factory() -> TutorSession:
        return TutorSession(verbose=False)

    args.out.mkdir(parents=True, exist_ok=True)
    index: list[dict] = []
    records: list[dict] = []

    for spec in selected:
        record = run_conversation(spec, factory, args.top_k)
        records.append(record)
        md_path = args.out / f"{record['id']}.md"
        json_path = args.out / f"{record['id']}.json"
        md_path.write_text(build_markdown(record), encoding="utf-8")
        json_path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
        index.append({"id": record["id"], "title": record["title"], "status": record["status"],
                      "turns": len(record["turns"]), "md": md_path.name, "json": json_path.name})
        print(f"\n  -> saved {md_path}")

    # Anti-drift safeguard summary (see chat.py DARIJA_MARKERS).
    stats_md = darija_stats(records)
    print("\n" + stats_md)

    (args.out / "index.json").write_text(
        json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "model": DEFAULT_CONFIG.chat_model,
            "system_prompt_chars": len(SYSTEM_PROMPT),
            "darija_stats": stats_md,
            "conversations": index,
        }, ensure_ascii=False, indent=2), encoding="utf-8")

    # One combined file, so the whole batch can be read or pasted in one go.
    combined = [
        "# Transcripts — tuteur 2Bac SM",
        "",
        f"- **Généré le** : {datetime.now().isoformat(timespec='seconds')}",
        f"- **Modèle** : `{DEFAULT_CONFIG.chat_model}`",
        f"- **System prompt** : `rag/prompts.py` ({len(SYSTEM_PROMPT)} caractères)",
        "",
        stats_md,
    ]
    for item in index:
        body = (args.out / item["md"]).read_text(encoding="utf-8")
        combined += [body, ""]
    (args.out / "ALL.md").write_text("\n".join(combined), encoding="utf-8")

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
