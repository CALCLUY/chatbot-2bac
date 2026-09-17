"""Step 4 -- the vector store (Chroma, local & self-hostable).

Chroma is used in ``PersistentClient`` mode: it is an ordinary directory on
disk, needs no server and no paid plan, and supports metadata filtering
natively (which FAISS would force us to re-implement by hand).

Cosine similarity is used throughout: vectors are L2-normalised by the
embedder and the collection is created with ``hnsw:space = cosine``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import chromadb
from chromadb.config import Settings

from .config import Config

# Metadata keys that callers may filter on, mapped to the ``where`` operators
# we build for them.
FILTERABLE_FIELDS = ("matiere", "chapitre", "semestre", "seance", "sujet", "type",
                     "nature", "annee", "session", "filiere", "block_type")

# ``chapitre`` is not populated on every file (Physique-Chimie uses
# ``Semestre / Section`` instead), so a chapitre filter is satisfied by either
# field. See parser.metadata_from_path().
CHAPTER_ALIASES = ("chapitre", "semestre")


@dataclass
class RetrievedChunk:
    """One hit: the verbatim chunk text, its metadata, and a similarity score."""

    chunk_id: str
    content: str
    metadata: dict
    score: float                       # cosine similarity in [-1, 1]; higher is better
    embedding: list | None = None      # only populated when refinement is used

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<RetrievedChunk {self.chunk_id} score={self.score:.3f}>"


def sanitise_metadata(metadata: dict) -> dict:
    """Chroma accepts only str/int/float/bool and rejects ``None``."""
    clean: dict[str, Any] = {}
    for key, value in metadata.items():
        if value is None:
            clean[key] = ""
        elif isinstance(value, (str, int, float, bool)):
            clean[key] = value
        else:
            clean[key] = str(value)
    return clean


def build_where(filters: dict | None) -> dict | None:
    """Translate friendly filters into a Chroma ``where`` clause.

    ``{"matiere": "SVT", "chapitre": "Semestre 1"}`` becomes a conjunction of
    equality clauses, with ``chapitre`` expanded to ``chapitre OR semestre``.
    Unknown keys raise rather than being silently dropped.
    """
    if not filters:
        return None

    clauses: list[dict] = []
    for key, value in filters.items():
        if value is None or value == "":
            continue
        if key not in FILTERABLE_FIELDS:
            raise ValueError(
                f"Unsupported filter {key!r}. Allowed: {', '.join(FILTERABLE_FIELDS)}"
            )
        if key in CHAPTER_ALIASES and key == "chapitre":
            clauses.append({"$or": [{field: {"$eq": value}} for field in CHAPTER_ALIASES]})
        else:
            clauses.append({key: {"$eq": value}})

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {"$and": clauses}


class VectorStore:
    """Thin wrapper around a single Chroma collection."""

    def __init__(self, config: Config):
        self.config = config
        self.path = config.chroma_dir
        self.path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self.path),
            settings=Settings(anonymized_telemetry=False, allow_reset=True),
        )
        self.collection = self._client.get_or_create_collection(
            name=config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # -- introspection ---------------------------------------------------- #
    def count(self) -> int:
        return self.collection.count()

    @property
    def name(self) -> str:
        return self.config.collection_name

    # -- writing ---------------------------------------------------------- #
    def reset(self) -> None:
        self._client.delete_collection(self.config.collection_name)
        self.collection = self._client.get_or_create_collection(
            name=self.config.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def add(self, chunks: Sequence, embeddings) -> None:
        """Upsert chunks together with their (already computed) embeddings."""
        import numpy as np

        vectors = np.asarray(embeddings, dtype=np.float32)
        if vectors.ndim != 2 or len(vectors) != len(chunks):
            raise ValueError(f"embedding shape {vectors.shape} does not match {len(chunks)} chunks")

        self.collection.upsert(
            ids=[c.metadata["chunk_id"] for c in chunks],
            documents=[c.content for c in chunks],          # verbatim, LaTeX intact
            embeddings=[v.tolist() for v in vectors],
            metadatas=[sanitise_metadata(c.metadata) for c in chunks],
        )

    def set_provenance(self, info: dict) -> None:
        """Record how the index was built (model, counts) on the collection."""
        existing = dict(self.collection.metadata or {})
        # Chroma refuses any modify() payload that touches "hnsw:space", even
        # when the value is unchanged, so it must not be echoed back.
        existing.pop("hnsw:space", None)
        existing.update({k: str(v) if not isinstance(v, (str, int, float, bool)) else v
                         for k, v in info.items() if v is not None})
        self.collection.modify(metadata=existing)

    @property
    def provenance(self) -> dict:
        return dict(self.collection.metadata or {})

    def check_embedder(self, embedder, verbose: bool = True) -> None:
        """Warn when the current embedder does not match how the index was built.

        Mixing two embedding models makes the cosine scores meaningless, and a
        different dimensionality would fail outright inside Chroma -- better to
        say so up front.
        """
        info = self.provenance
        if not info.get("embedding_model"):
            return
        same_model = str(info.get("embedding_model")) == str(embedder.model)
        same_backend = str(info.get("embedding_backend")) == str(embedder.backend_name)
        built_dim = int(info.get("embedding_dim") or 0)
        if not (same_model and same_backend):
            print(
                f"[warn] this index was built with backend={info.get('embedding_backend')} "
                f"model={info.get('embedding_model')}, but you are querying it with "
                f"backend={embedder.backend_name} model={embedder.model}. "
                "Re-run `python ingest.py` to rebuild with the current settings."
            )
        elif built_dim and built_dim != embedder.dim:
            print(f"[warn] index dimension {built_dim} != embedder dimension {embedder.dim}")

    # -- reading ---------------------------------------------------------- #
    def query(self, embedding: Sequence[float], top_k: int, where: dict | None,
              include: Sequence[str] = ("documents", "metadatas", "distances"),
              with_embeddings: bool = False) -> list[RetrievedChunk]:
        if self.count() == 0:
            return []

        fields = list(include)
        if with_embeddings and "embeddings" not in fields:
            fields.append("embeddings")

        kwargs: dict[str, Any] = {
            "query_embeddings": [list(map(float, embedding))],
            "n_results": min(top_k, self.count()),
            "include": fields,
        }
        if where:
            kwargs["where"] = where

        result = self.collection.query(**kwargs)
        ids = result["ids"][0]
        documents = result["documents"][0] if result.get("documents") else [""] * len(ids)
        metadatas = result["metadatas"][0] if result.get("metadatas") else [{}] * len(ids)
        distances = result["distances"][0] if result.get("distances") else [0.0] * len(ids)
        vectors = result.get("embeddings")
        vectors = vectors[0] if vectors else [None] * len(ids)

        hits: list[RetrievedChunk] = []
        for chunk_id, document, metadata, distance, vector in zip(
                ids, documents, metadatas, distances, vectors):
            hits.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    content=document or "",
                    metadata=dict(metadata or {}),
                    # Chroma returns cosine *distance*; convert to similarity.
                    score=1.0 - float(distance),
                    embedding=[float(x) for x in vector] if vector is not None else None,
                )
            )
        return hits
