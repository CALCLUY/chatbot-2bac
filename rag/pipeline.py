"""Orchestration shared by ``ingest.py`` and ``retrieve.py``.

    parse  ->  chunk  ->  embed  ->  upsert into Chroma
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass

import numpy as np

from .chunker import chunk_documents, validate_latex_integrity
from .config import Config
from .embeddings import Embedder, get_embedder, hashing_state_path
from .parser import parse_corpus
from .vectorstore import VectorStore


@dataclass
class IngestStats:
    files: int = 0
    chunks: int = 0
    latex_violations: int = 0
    elapsed_s: float = 0.0
    backend: str = ""
    model: str = ""
    dim: int = 0

    def render(self) -> str:
        return (
            f"files={self.files}  chunks={self.chunks}  dim={self.dim}  "
            f"backend={self.backend}  model={self.model}  "
            f"latex_violations={self.latex_violations}  elapsed={self.elapsed_s:.1f}s"
        )


# --------------------------------------------------------------------------- #
# Stages
# --------------------------------------------------------------------------- #
def build_chunks(config: Config, limit: int | None = None, verbose: bool = True) -> list:
    """Parse + chunk the corpus (no embeddings, no database)."""
    root = config.resolve_data_dir()
    if verbose:
        print(f"[parse] reading corpus from {root}")
    docs = parse_corpus(root, limit=limit)
    if verbose:
        print(f"[parse] {len(docs)} documents")

    chunks = chunk_documents(docs, config)

    violations = validate_latex_integrity(chunks)
    if verbose:
        print(f"[chunk] {len(chunks)} chunks; LaTeX violations: {len(violations)}")
    if violations:
        print(f"[chunk] WARNING: {len(violations)} chunk(s) split a LaTeX formula, e.g. {violations[:3]}")
    return chunks


def embed_all(chunks: list, embedder: Embedder, batch_size: int = 64, verbose: bool = True) -> np.ndarray:
    texts = [c.metadata["embedding_text"] for c in chunks]
    if verbose:
        print(f"[embed] encoding {len(texts)} chunks with {embedder.backend_name} ...")

    # The TF-IDF fallback needs to see the corpus once before it can weight terms.
    if hasattr(embedder, "fit") and embedder.backend_name == "hashing":
        embedder.fit(texts)

    vectors = np.zeros((len(texts), embedder.dim), dtype=np.float32)
    for start in range(0, len(texts), batch_size):
        end = min(start + batch_size, len(texts))
        vectors[start:end] = embedder.encode(texts[start:end], input_type="document")
        if verbose and (end % (batch_size * 10) == 0 or end == len(texts)):
            print(f"[embed]   {end}/{len(texts)}")
    return vectors


def dump_chunks(chunks: list, path) -> None:
    """Write every chunk + metadata to JSONL (useful for offline inspection)."""
    if not path:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps({"content": chunk.content, **chunk.metadata}, ensure_ascii=False) + "\n")


def run_ingestion(config: Config, reset: bool = True, limit: int | None = None,
                  dump: bool = True, verbose: bool = True) -> IngestStats:
    started = time.time()
    stats = IngestStats()

    chunks = build_chunks(config, limit=limit, verbose=verbose)
    if not chunks:
        raise SystemExit("No chunks produced -- is DATA_DIR pointing at the corpus?")
    stats.files = len({c.metadata["file_path"] for c in chunks})
    stats.chunks = len(chunks)
    stats.latex_violations = len(validate_latex_integrity(chunks))

    embedder = get_embedder(config, verbose=verbose)
    stats.backend = embedder.backend_name
    stats.model = embedder.model

    vectors = embed_all(chunks, embedder, batch_size=config.embedding_batch_size, verbose=verbose)
    stats.dim = int(vectors.shape[1])

    # Persist the fitted IDF table so queries are weighted the same way.
    if embedder.backend_name == "hashing":
        state_path = hashing_state_path(config)
        embedder.save_state(state_path)
        if verbose:
            print(f"[embed] saved IDF state to {state_path}")

    store = VectorStore(config)
    if reset and store.count():
        if verbose:
            print(f"[store] resetting collection {store.name!r} ({store.count()} existing vectors)")
        store.reset()

    if verbose:
        print(f"[store] upserting {len(chunks)} vectors into {config.chroma_dir}")
    store.add(chunks, vectors)
    store.set_provenance({
        "embedding_backend": stats.backend,
        "embedding_model": stats.model,
        "embedding_dim": stats.dim,
        "n_chunks": stats.chunks,
        "n_files": stats.files,
    })

    if dump and config.chunks_dump:
        dump_chunks(chunks, config.chunks_dump)
        if verbose:
            print(f"[store] chunk dump written to {config.chunks_dump}")

    if verbose:
        print(f"[store] collection {store.name!r} now holds {store.count()} vectors")

    stats.elapsed_s = time.time() - started
    return stats
