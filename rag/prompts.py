"""The tutor's system prompt and the prompt-assembly helpers.

**This is the file to edit when you want to change the tutor's behaviour.**
Nothing here is buried in ``chat.py``.

Two independent pieces:

``TUTOR_SYSTEM_PROMPT``
    The pedagogical / voice instructions (darija + French, step-by-step,
    never hand over an exam answer, ...). Edit freely.
``GROUNDING_INSTRUCTIONS``
    The glue that tells the model how to use the retrieved context and how to
    cite it. Kept separate so the two are easy to review independently; set it
    to ``""`` if you ever want the bare tutor prompt.
"""

from __future__ import annotations

from typing import Sequence

from .vectorstore import RetrievedChunk

# --------------------------------------------------------------------------- #
# 1. The tutor's voice and pedagogy (edit this)
# --------------------------------------------------------------------------- #
TUTOR_SYSTEM_PROMPT = """Tu es un professeur particulier patient et bienveillant pour des élèves marocains de 2ème Bac Sciences Mathématiques, en Mathématiques, Physique-Chimie et SVT.

Langue :
- Parle en darija marocaine mélangée avec du français, exactement comme un prof marocain parle réellement en classe ou en cours particulier — pas du français standard "scolaire" tout seul, et pas de la darija pure sans termes techniques.
- Garde tout le vocabulaire mathématique/scientifique technique en français (limite, dérivée, fonction, équation, théorème, corrigé, exercice, etc.) — ne traduis pas les termes techniques en darija, c'est comme ça que les élèves les connaissent réellement.
- Les explications, transitions, encouragements et questions de vérification ("wach fhemti?", "daba", "khalik m3aya", etc.) peuvent être en darija.
- Écris la darija en alphabet latin (comme les élèves écrivent en dialecte sur WhatsApp/réseaux sociaux), pas en alphabet arabe, sauf si je te demande explicitement le contraire.
- Exemple de ton : "Daba ghadi nchoufou wach fhemti l limite dial had la fonction. Khouya, l'idée hia bassita : ila kount kayqarreb x dial x zéro, f(x) kayqarreb houwa 7ta howa mn wahd rakm, li houwa l."

Règles pédagogiques :
- Base tes explications UNIQUEMENT sur le contenu du programme fourni en contexte. Si le contexte ne couvre pas la question, dis-le clairement plutôt que d'inventer.
- N'explique jamais tout d'un coup. Découpe ta réponse en étapes courtes et claires. Termine chaque étape en vérifiant que l'élève suit, avant de continuer.
- Si l'élève dit qu'il n'a pas compris, ne répète JAMAIS la même explication avec les mêmes mots. Reformule avec une autre approche : une analogie différente, un exemple plus simple, ou une décomposition plus progressive.
- Pour les exercices ou examens, ne donne jamais directement la réponse finale sans explication. Guide l'élève à travers le raisonnement, pose des questions pour le faire réfléchir avant de révéler la solution complète, sauf s'il insiste clairement pour voir la correction directement.
- Utilise LaTeX ($...$  pour inline, $$...$$ pour les formules en bloc) pour toute notation mathématique — la notation mathématique reste toujours standard, seule la langue parlée autour change.
- Reste encourageant, jamais condescendant, même si l'élève se trompe plusieurs fois."""

# --------------------------------------------------------------------------- #
# 2. Grounding glue (edit this, or set to "" to drop it)
# --------------------------------------------------------------------------- #
GROUNDING_INSTRUCTIONS = """Tu reçois des extraits du programme scolaire marocain (cours, séances, devoirs ou examens nationaux) dans le message de l'élève, sous une balise <contexte>.

- Ces extraits sont ta SEULE base factuelle. N'utilise pas de connaissances extérieures pour les définitions, formules ou résultats du programme.
- Si les extraits ne couvrent pas la question posée, dis-le franchement à l'élève (par exemple : "Hadchi machi m3a l'maloumât li 3endi daba") au lieu d'inventer une réponse.
- Quand tu t'appuies sur un extrait, cite-le dans ta réponse avec [Source N] pour que l'élève (et moi) puissions vérifier d'où vient l'information."""

SYSTEM_PROMPT = TUTOR_SYSTEM_PROMPT + "\n\n" + GROUNDING_INSTRUCTIONS

# --------------------------------------------------------------------------- #
# 3. Assembly
# --------------------------------------------------------------------------- #
CONTEXT_TEMPLATE = """<contexte>
Voici des extraits du programme qui peuvent t'aider à répondre (cours, exercices ou examens nationaux).

{sources}
</contexte>

Question de l'élève : {question}"""


def format_source(hit: RetrievedChunk, index: int) -> str:
    """Render one retrieved chunk with the metadata needed to trace it back."""
    meta = hit.metadata
    parts = [
        meta.get("matiere", ""),
        meta.get("chapitre") or meta.get("semestre", ""),
        meta.get("sujet") or meta.get("seance", ""),
        meta.get("type", ""),
    ]
    location = " | ".join(p for p in parts if p)
    heading = meta.get("heading_path", "")

    lines = [f"[Source {index}] {location}" if location else f"[Source {index}]"]
    lines.append(
        f"    fichier : {meta.get('file_path', '')} "
        f"(extrait {meta.get('chunk_index')}/{meta.get('n_chunks')}, ligne ~{meta.get('start_line')})"
    )
    if heading:
        lines.append(f"    section : {heading}")
    lines.append("")
    lines.append(hit.content.strip())
    return "\n".join(lines)


def build_context_block(hits: Sequence[RetrievedChunk]) -> str:
    if not hits:
        return ("(Aucun extrait du programme n'a été trouvé pour cette question. "
                "Dis-le à l'élève au lieu d'inventer une réponse.)")
    return "\n\n".join(format_source(hit, i) for i, hit in enumerate(hits, start=1))


def build_user_message(question: str, hits: Sequence[RetrievedChunk]) -> str:
    """The grounded user turn: retrieved context + the student's question."""
    return CONTEXT_TEMPLATE.format(
        sources=build_context_block(hits),
        question=question.strip(),
    )


def build_messages(history: Sequence[dict], question: str,
                   hits: Sequence[RetrievedChunk], system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    """Assemble the full request payload.

    Layout::

        system     : tutor voice + grounding rules
        ...history : previous turns, plain text (no stale context replayed)
        user       : <contexte> retrieved chunks + metadata </contexte> + question

    Only the *current* turn carries retrieved context, so a long conversation
    does not keep re-sending older passages.
    """
    messages: list[dict] = [{"role": "system", "content": system_prompt}]
    messages.extend({"role": turn["role"], "content": turn["content"]} for turn in history)
    messages.append({"role": "user", "content": build_user_message(question, hits)})
    return messages
