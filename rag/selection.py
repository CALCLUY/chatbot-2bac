"""Post-processing of retrieved candidates: trimming and diversity.

Chroma hands back the nearest neighbours, which for this corpus tends to be
several chunks from the *same* exam paper (exam corrections are dense in
LaTeX like ``\\lim``, so a whole file lights up at once). Feeding six
near-identical passages to the tutor crowds out the lesson that would
actually explain the concept.

Two small, standard RAG steps fix that:

``trim_by_score``
    Drop the tail: anything scoring far below the best hit is noise.
``mmr_select``
    Maximal-marginal-relevance: greedily pick chunks that are relevant to the
    query *and* different from what is already selected.

Both are opt-in so that plain ``retrieve()`` keeps returning raw
best-first-by-score results (what ``test_retrieval.py`` asserts on).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np

from .config import Config
from .vectorstore import RetrievedChunk


def trim_by_score(hits: Sequence[RetrievedChunk], min_ratio: float = 0.5) -> list[RetrievedChunk]:
    """Keep hits scoring at least ``min_ratio`` × the best hit's score.

    A *relative* floor is used because absolute cosine values are not
    comparable across embedding models.
    """
    if not hits or min_ratio <= 0:
        return list(hits)
    best = max(h.score for h in hits)
    if best <= 0:
        return list(hits)
    kept = [h for h in hits if h.score >= best * min_ratio]
    return kept or [hits[0]]


def max_per_file(hits: Sequence[RetrievedChunk], limit: int = 2) -> list[RetrievedChunk]:
    """Cap how many chunks may come from any single source file."""
    if limit <= 0:
        return list(hits)
    counts: dict[str, int] = {}
    kept: list[RetrievedChunk] = []
    for hit in hits:
        path = hit.metadata.get("file_path", "")
        if counts.get(path, 0) >= limit:
            continue
        counts[path] = counts.get(path, 0) + 1
        kept.append(hit)
    return kept


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1.0
    return float(np.dot(a, b) / denom)


def mmr_select(hits: Sequence[RetrievedChunk], top_k: int, lam: float = 0.6) -> list[RetrievedChunk]:
    """Pick ``top_k`` hits balancing relevance against redundancy.

    ``lam = 1`` is plain relevance order; ``lam = 0`` is pure diversity.
    Requires the hits to carry their ``.embedding``.
    """
    if len(hits) <= top_k or lam >= 1.0:
        return list(hits[:top_k])

    if any(h.embedding is None for h in hits):
        return list(hits[:top_k])

    vectors = [np.asarray(h.embedding, dtype=np.float32) for h in hits]
    chosen: list[int] = []
    remaining = list(range(len(hits)))

    while remaining and len(chosen) < top_k:
        if not chosen:
            pick = max(remaining, key=lambda i: hits[i].score)
        else:
            def score_of(i: int) -> float:
                redundancy = max(_cosine(vectors[i], vectors[j]) for j in chosen)
                return lam * hits[i].score - (1.0 - lam) * redundancy

            pick = max(remaining, key=score_of)
        chosen.append(pick)
        remaining.remove(pick)

    return [hits[i] for i in chosen]


def refine(hits: Sequence[RetrievedChunk], top_k: int, config: Config) -> list[RetrievedChunk]:
    """Apply the configured trim + diversity pipeline."""
    out = trim_by_score(hits, min_ratio=config.retrieval_min_score_ratio)
    out = max_per_file(out, limit=config.retrieval_max_per_file)
    out = mmr_select(out, top_k=top_k, lam=config.retrieval_mmr_lambda)
    return out
