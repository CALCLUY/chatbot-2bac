#!/usr/bin/env python3
"""Retrieval for the 2ème Bac SM tutor corpus.

This is the reusable entry point for the RAG pipeline: give it a student's
question, optionally narrow it down by subject/chapter, and get back the top-k
most relevant chunks **with their metadata**.

Library use::

    from retrieve import retrieve

    hits = retrieve("Comment calculer la limite d'une fonction en un point ?",
                    matiere="Mathématiques", top_k=5)
    for hit in hits:
        print(hit.score, hit.metadata["chapitre"], hit.content[:200])

Command line::

    python retrieve.py "c'est quoi la méiose ?"
    python retrieve.py "limite d'une fonction" --matiere Mathématiques --top-k 3
    python retrieve.py "décroissance radioactive" --chapitre "Semestre 1"
"""

from __future__ import annotations

import argparse
from typing import Sequence

from rag.config import DEFAULT_CONFIG, Config
from rag.display import print_results
from rag.embeddings import get_embedder
from rag.vectorstore import RetrievedChunk, VectorStore, build_where


class Retriever:
    """Embeds a query and searches the Chroma collection.

    The embedder and the vector store are loaded once and reused, so asking
    many questions in a row only pays the model load cost a single time.
    """

    def __init__(self, config: Config | None = None, embedder=None, store: VectorStore | None = None,
                 verbose: bool = False):
        self.config = config or DEFAULT_CONFIG
        self._embedder = embedder
        self._store = store
        self._verbose = verbose

    # -- lazily built collaborators --------------------------------------- #
    @property
    def embedder(self):
        if self._embedder is None:
            self._embedder = get_embedder(self.config, verbose=self._verbose)
        return self._embedder

    @property
    def store(self) -> VectorStore:
        if self._store is None:
            self._store = VectorStore(self.config)
            self._store.check_embedder(self.embedder, verbose=self._verbose)
        return self._store

    # -- the actual retrieval --------------------------------------------- #
    def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        matiere: str | None = None,
        chapitre: str | None = None,
        type: str | None = None,          # noqa: A002 - mirrors the corpus metadata field
        annee: str | int | None = None,
        block_type: str | None = None,
        where: dict | None = None,
    ) -> list[RetrievedChunk]:
        """Return the ``top_k`` chunks most similar to *query*.

        Parameters
        ----------
        query:
            The student's question (French, may contain LaTeX).
        top_k:
            How many chunks to return. Defaults to ``config.top_k`` (5).
        matiere, chapitre, type, annee, block_type:
            Optional metadata filters. ``chapitre`` also matches the
            ``semestre`` field, because Physique-Chimie files are organised by
            semester rather than by chapter.
        where:
            An escape hatch: a raw Chroma ``where`` clause used verbatim.

        Returns
        -------
        list[RetrievedChunk]
            Ordered best-first. Each item carries ``.content`` (verbatim text,
            LaTeX intact), ``.metadata`` and ``.score`` (cosine similarity).
        """
        if not query or not query.strip():
            raise ValueError("query must be a non-empty string")

        filters = {
            "matiere": matiere,
            "chapitre": chapitre,
            "type": type,
            "annee": str(annee) if annee is not None else None,
            "block_type": block_type,
        }
        filters = {k: v for k, v in filters.items() if v not in (None, "")}
        clause = where or build_where(filters)   # an explicit clause wins
        k = int(top_k or self.config.top_k)

        vector = self.embedder.encode([query], input_type="query")[0]
        return self.store.query(vector, top_k=k, where=clause)


# --------------------------------------------------------------------------- #
# Module-level convenience wrapper (the "retrieval function" of the spec)
# --------------------------------------------------------------------------- #
_DEFAULT: Retriever | None = None


def retrieve(query: str, **kwargs) -> list[RetrievedChunk]:
    """Retrieve top-k chunks for *query* using a process-wide default retriever.

    Accepts the same keyword arguments as :meth:`Retriever.retrieve`.
    """
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = Retriever(verbose=True)
    return _DEFAULT.retrieve(query, **kwargs)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Retrieve relevant chunks from the 2bac corpus.")
    parser.add_argument("query", help="the student's question")
    parser.add_argument("--matiere", help="filter by subject (Mathématiques | Physique-Chimie | SVT)")
    parser.add_argument("--chapitre", help="filter by chapter (also matches 'semestre')")
    parser.add_argument("--type", help="filter by type (Cours | Exercices | Examen National | ...)")
    parser.add_argument("--annee", help="filter by exam year")
    parser.add_argument("--block-type", dest="block_type",
                        help="filter by block type (définition, proposition, exemple, ...)")
    parser.add_argument("--top-k", type=int, default=None, help="number of results (default 5)")
    parser.add_argument("--max-chars", type=int, default=600, help="preview length per chunk")
    args = parser.parse_args(argv)

    retriever = Retriever(verbose=True)
    if retriever.store.count() == 0:
        print("The collection is empty. Build the index first:  python ingest.py")
        return 1

    hits = retriever.retrieve(
        args.query,
        top_k=args.top_k,
        matiere=args.matiere,
        chapitre=args.chapitre,
        type=args.type,
        annee=args.annee,
        block_type=args.block_type,
    )
    filters = {
        "matiere": args.matiere, "chapitre": args.chapitre, "type": args.type,
        "annee": args.annee, "block_type": args.block_type,
    }
    print_results(args.query, hits, filters=filters, max_chars=args.max_chars)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
