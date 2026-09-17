#!/usr/bin/env python3
"""Audit saved transcripts against the rules in ``rag/prompts.py``.

Produces the review note (``transcripts/REVIEW-NOTES.md``): for every scenario
and every tutor turn it reports the mechanical evidence -- sentence count,
whether a full solution appears to have been handed over, whether an
out-of-programme question was answered as if it were in scope -- and prints a
PASS / FLAG verdict per rule.

Two kinds of check live here:

*AUTOMATIC* -- decidable from the text (sentence budget, citation of sources on
an out-of-scope question, verbatim repetition after "j'ai pas compris").

*MANUAL* -- needs a human read (is the analogy actually good? did the tutor
remember the student's earlier mistake?). Those are listed with the verbatim
turn so you can eyeball them quickly.

    python check_transcripts.py                       # audits transcripts/
    python check_transcripts.py --dir transcripts --json

Nothing here calls the model; it only reads the transcripts already on disk.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSCRIPT_DIR = HERE / "transcripts"

# --------------------------------------------------------------------------- #
# Rule knobs -- keep in sync with TUTOR_SYSTEM_PROMPT in rag/prompts.py
# --------------------------------------------------------------------------- #
MAX_SENTENCES = 3            # "Limite absolue : 3 phrases maximum"
GUIDANCE_EXCHANGES = 2       # "au moins 2 échanges de guidage" avant de révéler

# A turn where revealing the full correction is allowed by the prompt.
# Rule 4 needs BOTH >= 2 guidance exchanges AND an explicit request, so:
#   - scenario 5: allowed on NO turn -- the student only demands twice and
#     follows zero guidance, so v2 must keep holding (this is a change from v1,
#     whose goal said "yields if the student insists").
#   - scenario 8 turn 4: the student has been guided for 3 turns, proposes his
#     own attempt AND explicitly asks for "l correction kamla" -> may reveal.
REVEAL_ALLOWED_TURNS = {
    "5-examen-reponse": set(),
    "8-eleve-obsine-reponse-examen": {4},
}

# Markers of "this is not in the programme" (fr + darija, several spellings).
OUT_OF_SCOPE_RE = re.compile(
    r"(hors[ -]programme|hors du programme|pas dans le programme|"
    r"ne fait pas partie|n'?est pas (dans|au) programme|"
    r"machi f ?l'?programme|machi m3a l'?maloum|"
    r"ma kaynch f ?l'?programme|kharraj ?mn ?l'?programme|"
    r"3ndna ghir|kan3rfou ghir|l'?programme dial|"
    r"je ne (peux|saurais) pas|aucun extrait|"
    r"ma 3ndich maloum|ma 3endich had l'|kharej 3an)",
    re.IGNORECASE,
)

# Markers that a final answer / worked solution is being handed over.
SOLUTION_RE = re.compile(
    r"(la réponse (finale )?est|la solution (est|:)|le résultat (est|final)|"
    r"donc la réponse|donc on (obtient|a)|on trouve (que )?|on obtient|"
    r"l ?jawab (howa|hia)|l7al (howa|hia)|hadchi 3ni|alors la réponse|"
    r"corrigé complet|la correction complète|réponse finale)",
    re.IGNORECASE,
)

# Behaviour changes introduced by the v2 prompt that alter what an *existing*
# scenario is supposed to produce. Read these before judging a turn as a failure.
CONTRACT_CHANGES: list[tuple[str, str]] = [
    ("5-examen-reponse",
     "v1 : le prof cède « s'il insiste clairement ». **v2 : l'insistance seule ne suffit "
     "plus** — la règle 4 exige >= 2 échanges de guidage ET une demande explicite. "
     "L'élève de ce scénario ne suit aucun guidage : une correction complète au tour 2 "
     "est désormais un **échec**, alors que c'était un succès en v1. Les tours sont "
     "inchangés pour rester comparable."),
    ("3-svt-question",
     "La question porte sur TROIS notions (méiose, réduction chromatique, différence "
     "avec la mitose). Sous la règle « une seule idée nouvelle par réponse », le prof "
     "doit en traiter UNE et annoncer qu'il garde les autres pour après. Répondre aux "
     "trois d'un coup est désormais un échec, même si c'est plus « complet »."),
    ("2-physique-exercice",
     "Même effet : l'énoncé pose DEUX questions (le mot unique, transversale ou "
     "longitudinale). Attendu v2 : une seule des deux, guidée, puis vérification."),
    ("1-maths-concept",
     "v1 acceptait une définition + un exemple dans le même message. v2 impose : "
     "analogie d'abord, 3 phrases max, vérification, et seulement ENSUITE la "
     "définition epsilon/alpha au tour suivant. Une réponse v1 « correcte » échoue "
     "donc maintenant le découpage."),
    ("global",
     "Le prompt v2 assume explicitement de « frustrer légèrement l'élève ». Des "
     "réponses plus courtes et moins complètes qu'en v1 sont **attendues**, pas un "
     "signe de régression — tant que l'analogie et la vérification sont là."),
]

# Per-scenario manual checkpoints, rendered into the note.
MANUAL_CHECKS: dict[str, list[str]] = {
    "1-maths-concept": [
        "Analogie / image mentale AVANT la définition formelle (règle exemples concrets).",
        "Une seule idée nouvelle : idée intuitive -> vérification -> (tour suivant) formule epsilon/alpha.",
        "Darija en alphabet latin + termes techniques en français.",
    ],
    "2-physique-exercice": [
        "Guide sans répondre : les questions 1 et 2 ne doivent PAS être résolues d'un coup.",
        "Au moins une image mentale (corde, vibration) avant le terme technique.",
    ],
    "3-svt-question": [
        "Méiose ET réduction chromatique ET comparaison mitose ne doivent PAS être traitées dans le même message (une idée à la fois).",
        "Analogie concrète avant la définition.",
    ],
    "4-pas-compris": [
        "Le tour 2 reformule avec une AUTRE approche (pas les mêmes mots que le tour 1).",
        "Le tour 2 est plus court / plus simple, pas plus long.",
    ],
    "5-examen-reponse": [
        "Tour 1 : demande ce que l'élève a déjà essayé, ne donne rien.",
        "Tour 2 : l'élève demande explicitement la correction -- mais a-t-il suivi 2 échanges de guidage ? Sinon le prof doit encore tenir.",
    ],
    "6-multi-tour-erreur": [
        "Tour 2 : corrige l'erreur (0) sans condescendance et sans valider la fausse règle.",
        "Tour 3 : ne valide PAS la sur-généralisation (« toute limite avec numérateur nul vaut 0 »).",
        "Tour 4 : se souvient de l'erreur précise du tour 2 sans que l'élève la répète (MÉMOIRE DU CONTEXTE).",
    ],
    "7-eleve-decourage": [
        "Reste encourageant sous la frustration, jamais condescendant.",
        "NE lâche PAS la réponse complète pour calmer l'élève ; réduit la difficulté à une seule petite étape.",
        "Nouvelle analogie au tour 2/3 plutôt que répétition.",
    ],
    "8-eleve-obsine-reponse-examen": [
        "Tours 1-3 : tient bon, aucune correction complète malgré « wrini l7al » au tour 3.",
        "Chaque tour avance d'une étape du processus (essais -> indice -> une étape guidée).",
        "Tour 4 : révèle enfin, mais ÉTAPE PAR ÉTAPE, jamais le résultat brut.",
    ],
    "9-hors-programme": [
        "Dit clairement que c'est hors programme, sans inventer de chiffres ou de faits.",
        "Ramène l'élève vers Maths / Physique-Chimie / SVT.",
        "N'appose PAS de [Source N] sur du contenu hors sujet.",
    ],
}


# --------------------------------------------------------------------------- #
# Text metrics
# --------------------------------------------------------------------------- #
def _protect_math(text: str) -> str:
    """Blank out LaTeX so `$...$` / `$$...$$` punctuation cannot inflate counts."""
    text = re.sub(r"\$\$.+?\$\$", " MATH ", text, flags=re.S)
    text = re.sub(r"\$[^$\n]*\$", " MATH ", text)
    return text


def count_sentences(text: str) -> tuple[int, list[str]]:
    """Return (number of sentences, the sentences) for one tutor turn.

    Counts prose sentences, list items and headings, because a bulleted "3
    idées" is exactly the over-explaining the prompt forbids -- hiding behind
    a list would defeat the check.
    """
    body = _protect_math(text)
    body = re.sub(r"\[Source \d+\]", " ", body)
    # Markdown scaffolding -> keep the words, drop the punctuation-free noise.
    body = re.sub(r"^\s*(#{1,6}|\*|-|\+|\d+[.)])\s*", "\n", body, flags=re.M)
    body = body.replace("**", "").replace("__", "").replace("`", "")

    segments: list[str] = []
    for raw_line in body.split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # Split on sentence enders, ignoring decimals and common abbreviations.
        protected = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", line)
        protected = re.sub(r"\b(etc|cf|ex|env|vs|M|N)\.", r"\1<DOT>", protected)
        parts = re.split(r"(?<=[.!?…])\s+", protected)
        for part in parts:
            piece = part.replace("<DOT>", ".").strip(" \t-*•")
            if len(piece) >= 2:
                segments.append(piece)
    return len(segments), segments


def count_ideas(text: str) -> dict:
    """Cheap proxy for « définition ET exemple ET exercice dans le même message ».

    Every pattern is word-anchored on purpose. A previous ``hi\\b`` / ``hia``
    (darija copula) matched the *tail* of ordinary words -- "katm**chi**" tripped
    the definition detector -- so an analogy-only reply was wrongly reported as
    a definition. Darija has no reliable surface marker for "this is a
    definition", which is why the stacking verdict below is advisory, not a
    hard fail.
    """
    low = text.lower()
    return {
        "definition": bool(re.search(
            r"(\bdéfinition\b|\bon appelle\b|\bon dit que\b|\bdéfinie par\b|"
            r"\bc'?est (quoi|lorsque|quand)\b|\bforme (générale|exponentielle|algébrique)\b|"
            r"\bhi\b|\bhia\b|\bkay?3ni\b)", low)),
        "example": bool(re.search(
            r"(\bexemple\b|\bpar exemple\b|\bbhal\b|\btsawwar\b|\bimagine\b|\bprenons\b|"
            r"\bsoit la fonction\b|\bchouf f rassek\b)", low)),
        "exercise": bool(re.search(
            r"(\bexercice\b|\bapplication\b|\bessaie\b|\bjarrab\b|\bà toi\b|\bcalcule(z)?\b|"
            r"\bmontre(?:r)? que\b|\bdémontr)", low)),
        "formal_formula": bool(re.search(r"\\(forall|varepsilon|epsilon|lim|frac|Rightarrow)", text)),
    }


def similarity(a: str, b: str) -> float:
    """Word-overlap ratio, to catch a verbatim re-explanation."""
    wa = {w for w in re.findall(r"[a-zà-ÿ0-9']+", a.lower()) if len(w) > 2}
    wb = {w for w in re.findall(r"[a-zà-ÿ0-9']+", b.lower()) if len(w) > 2}
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(1, min(len(wa), len(wb)))


# --------------------------------------------------------------------------- #
# Auditing
# --------------------------------------------------------------------------- #
def audit(record: dict) -> dict:
    sid = record["id"]
    turns = record["turns"]
    answers = [t.get("answer") or "" for t in turns]
    incomplete = record.get("status") != "OK"

    findings: list[dict] = []

    def add(rule: str, turn: int, ok: bool | None, evidence: str) -> None:
        findings.append({"rule": rule, "turn": turn, "ok": ok, "evidence": evidence})

    for i, ans in enumerate(answers, start=1):
        if not ans.strip():
            continue
        n, sentences = count_sentences(ans)
        longest = max(sentences, key=len) if sentences else ""
        add("decoupage: <= 3 phrases", i, n <= MAX_SENTENCES,
            f"{n} phrase(s)" + (f" — plus longue : « {longest[:90]}… »" if longest and n > MAX_SENTENCES else ""))

        ideas = count_ideas(ans)
        stacked = [k for k in ("definition", "example", "exercise") if ideas[k]]
        # The prompt forbids definition + exemple + exercice *together*. Two of
        # the three is NOT a violation -- "analogie AVANT la définition formelle"
        # positively requires an analogy and a definition in the same message.
        # So: hard fail on all three, advisory on two, pass on one/none.
        if len(stacked) == 3:
            add("une seule idée à la fois", i, False,
                "cumul interdit : définition + exemple + exercice dans le même message")
        elif len(stacked) == 2:
            add("une seule idée à la fois", i, None,
                f"2 contenus détectés ({', '.join(stacked)}) — autorisé si l'un est "
                "l'analogie qui PRÉCÈDE la définition ; à confirmer à la lecture")
        else:
            add("une seule idée à la fois", i, True,
                f"1 contenu ({stacked[0] if stacked else 'aucun détecté'})")

        if ideas["formal_formula"] and not ideas["example"]:
            add("analogie AVANT la définition formelle", i, None,
                "notation LaTeX formelle présente mais aucune analogie/image mentale "
                "détectée par mots-clés — à confirmer à la lecture")

        sol = SOLUTION_RE.search(ans)
        allowed = i in REVEAL_ALLOWED_TURNS.get(sid, set())
        if sid in {"5-examen-reponse", "7-eleve-decourage", "8-eleve-obsine-reponse-examen"}:
            add("réponse d'examen: pas de solution avant l'étape 4", i,
                allowed or not sol,
                ("révélation AUTORISÉE à ce tour" if allowed and sol else
                 ("marqueur de solution détecté" if sol else "aucun marqueur de solution")))

        if sid == "9-hors-programme":
            cited = re.findall(r"\[Source \d+\]", ans)
            declared = bool(OUT_OF_SCOPE_RE.search(ans))
            add("hors programme: le dit clairement", i, declared,
                ("déclare le hors-programme" if declared else "AUCUNE déclaration de hors-programme")
                + (f" ; {len(cited)} citation(s) [Source N] sur du hors-sujet" if cited and not declared else ""))

        if sid == "4-pas-compris" and i == 2 and len(answers) >= 2:
            sim = similarity(answers[0], answers[1])
            add("reformulation: ne répète pas les mêmes mots", i, sim < 0.55,
                f"recouvrement lexical tour1/tour2 = {sim:.0%}")

    if incomplete:
        add("transcript complet", 0, False, f"statut = {record.get('status')}")

    return {
        "id": sid,
        "title": record["title"],
        "status": record.get("status"),
        "turns": len(turns),
        "findings": findings,
        "manual": MANUAL_CHECKS.get(sid, []),
        "answers": answers,
    }


def render_note(audits: list[dict], model: str) -> str:
    out = [
        "# Note de revue — conformité au system prompt v2",
        "",
        f"- **Généré le** : {datetime.now().isoformat(timespec='seconds')}",
        f"- **Modèle** : `{model}`",
        f"- **Règles auditées** : `rag/prompts.py` (découpage <= {MAX_SENTENCES} phrases, "
        f"analogie avant définition, réponse d'examen après >= {GUIDANCE_EXCHANGES} échanges de guidage, "
        "hors programme annoncé)",
        "",
    ]

    incomplete = [a for a in audits if a["status"] != "OK"]
    failed = [f for a in audits for f in a["findings"] if f["ok"] is False]
    advisory = [f for a in audits for f in a["findings"] if f["ok"] is None]
    out += [
        "## Résumé",
        "",
        f"- Transcripts audités : **{len(audits)}**",
        f"- Transcripts INCOMPLETE (pas de réponse du modèle) : **{len(incomplete)}**",
        f"- Échecs automatiques (❌) : **{len(failed)}**",
        f"- Points à confirmer à la lecture (❔) : **{len(advisory)}**",
        "",
        "❌ = vérifiable mécaniquement. ❔ = le texte seul ne permet pas de trancher "
        "(l'ordre analogie/définition, la qualité d'une image mentale, la mémoire du "
        "contexte) : l'extrait est cité, la décision est à vous.",
        "",
    ]
    if incomplete:
        out += [
            "> ⚠️ Les transcripts marqués INCOMPLETE n'ont **aucune réponse du modèle** : "
            "les règles pédagogiques ne peuvent PAS être vérifiées dessus. "
            "Le contexte de grounding est sauvé, relancez avec un `CHAT_API_KEY` "
            "et un `CHAT_BASE_URL` joignable, puis re-auditez.",
            "",
        ]

    out += [
        "## À lire AVANT de juger un tour : changements de contrat v1 -> v2",
        "",
        "Le prompt v2 ne fait pas que resserrer le style, il **inverse** l'attendu de "
        "certains scénarios existants. Un tour « réussi » en v1 peut être un échec en v2, "
        "et inversement.",
        "",
    ]
    for scope, text in CONTRACT_CHANGES:
        out += [f"- **`{scope}`** — {text}"]
    out.append("")

    out += ["## Échecs par scénario", ""]
    any_failure = False
    for a in audits:
        bad = [f for f in a["findings"] if f["ok"] is False]
        if not bad:
            continue
        any_failure = True
        out += [f"### `{a['id']}` — {a['title']}", "", f"Statut : **{a['status']}**", ""]
        for f in bad:
            where = f"tour {f['turn']}" if f["turn"] else "global"
            out += [f"- ❌ **{f['rule']}** ({where}) : {f['evidence']}"]
        out.append("")
    if not any_failure:
        out += ["_Aucun échec automatique détecté._", ""]

    out += ["## Détail complet par scénario", ""]
    for a in audits:
        out += [f"### `{a['id']}` — {a['title']}", ""]
        for f in a["findings"]:
            mark = {True: "✅", False: "❌", None: "❔"}[f["ok"]]
            where = f"tour {f['turn']}" if f["turn"] else "global"
            out += [f"- {mark} {f['rule']} ({where}) — {f['evidence']}"]
        if a["manual"]:
            out += ["", "**À vérifier à la lecture (non automatisable) :**", ""]
            out += [f"- {m}" for m in a["manual"]]
        out.append("")

    out += [
        "## Notes sur le prompt lui-même (revue statique, indépendante des transcripts)",
        "",
        "- **Artefact corrigé** : l'exemple « bonne réponse » du bloc limites contenait "
        "« koulma 9ribti kter, *kat googlé* chi 7aja li kat b9a fixe ». Ce n'était pas de la "
        "darija et la phrase était cassée ; comme c'est le modèle que le prompt donne à imiter "
        "pour expliquer une limite, il y avait un risque réel de le voir recopié tel quel. "
        "Remplacé par « kat9elleb 3la chi 7aja li katbqa fixe » (même intention pédagogique).",
        "- **Taille** : `SYSTEM_PROMPT` = tutor + grounding. La partie tutor est passée de "
        "~1 800 à ~5 500 caractères : le prompt est maintenant surtout fait de règles "
        "négatives (« ne jamais… ») et d'exemples. À surveiller au premier vrai run : un "
        "prompt très prescriptif peut produire des réponses *trop* courtes, qui frustrent "
        "l'élève au lieu de le faire progresser. C'est précisément ce que les scénarios 1, "
        "3 et 7 permettront de trancher.",
        "- **Tension interne assumée** : « frustrer légèrement l'élève » (rappel d'objectif) "
        "contre « reste encourageant, jamais condescendant » (autres règles). Non "
        "contradictoire, mais c'est le point le plus sensible à juger à la lecture.",
        "- **Cap de 3 phrases vs questions multiples** : les scénarios 2 et 3 posent "
        "plusieurs questions en un seul tour. Le prof va devoir en ignorer une partie et "
        "l'annoncer. Si au contraire il répond à tout, c'est le découpage qui a sauté — "
        "c'est le signal le plus fiable d'une régression sur ce prompt.",
        "",
        "---",
        "",
        "## Méthode",
        "",
        "Les verdicts ❌/✅ ci-dessus sont **mécaniques** (comptage de phrases après "
        "neutralisation du LaTeX, recherche de marqueurs lexicaux). Ils servent à "
        "repérer vite les tours suspects. La liste « À vérifier à la lecture » de "
        "chaque scénario est ce qui demande un œil humain : qualité de l'analogie, "
        "mémoire du contexte, ton. Un tour marqué ❌ peut être un faux positif "
        "(ex. une phrase longue mais légitime) — lisez l'extrait avant de conclure.",
        "",
    ]
    return "\n".join(out)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", type=Path, default=TRANSCRIPT_DIR)
    parser.add_argument("--json", action="store_true", help="also dump the audit as JSON")
    args = parser.parse_args(argv)

    # index.json and audit.json are this tool's / the harness's own outputs,
    # not transcripts -- reading them as records would be self-poisoning.
    NOT_TRANSCRIPTS = {"index.json", "audit.json"}
    files = sorted(p for p in args.dir.glob("*.json") if p.name not in NOT_TRANSCRIPTS)
    if not files:
        print(f"No transcripts found in {args.dir}. Run: python run_test_conversations.py")
        return 1

    audits = [audit(json.loads(p.read_text(encoding="utf-8"))) for p in files]

    index_path = args.dir / "index.json"
    model = "(inconnu)"
    if index_path.is_file():
        model = json.loads(index_path.read_text(encoding="utf-8")).get("model", model)

    note = render_note(audits, model)
    out_path = args.dir / "REVIEW-NOTES.md"
    out_path.write_text(note, encoding="utf-8")

    if args.json:
        (args.dir / "audit.json").write_text(
            json.dumps([{k: v for k, v in a.items() if k != "answers"} for a in audits],
                       ensure_ascii=False, indent=2), encoding="utf-8")

    n_fail = sum(1 for a in audits for f in a["findings"] if f["ok"] is False)
    n_incomplete = sum(1 for a in audits if a["status"] != "OK")
    print(f"audited {len(audits)} transcript(s) -> {out_path}")
    print(f"  automatic failures : {n_fail}")
    print(f"  incomplete (no model answer) : {n_incomplete}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
