"""Step 3 -- embeddings.

Three interchangeable backends are provided, all behind one small interface:

``openai``
    Any OpenAI-compatible ``/embeddings`` endpoint. This is the production path:
    fill in ``EMBEDDING_MODEL_HERE`` / ``EMBEDDING_API_KEY_HERE``.
``sentence-transformers``
    A local HuggingFace model (no API key, no cost, runs on CPU). Good default
    for French + maths: ``intfloat/multilingual-e5-small``.
``hashing``
    A dependency-free TF-IDF hashing embedder used **only** as an offline
    fallback while the placeholders are still unfilled. It is deterministic and
    lexical rather than truly semantic -- it exists so the whole
    index/retrieve/test loop can be exercised before you pay for (or wait on)
    a real model.

Resolve one with :func:`get_embedder`.
"""

from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from pathlib import Path
from typing import Sequence

import numpy as np

from .config import PLACEHOLDER_MODEL, Config

# --------------------------------------------------------------------------- #
# Shared text normalisation (used by the hashing backend)
# --------------------------------------------------------------------------- #
_FRENCH_STOPWORDS = frozenset("""
a au aux avec ce ces cette dans de des du elle elles en est et eux il ils je la le les leur
lui ma mais me meme mes mon ne nous nos on ou par pas pour qu que qui sa se ses son sur ta te
tes toi ton tu un une vos votre vous c d j l m n s t y etre avoir fait faire plus moins comme
donc alors ainsi aussi tout tous toute toutes est sont etait etre ce cet cette ces
""".split())

_LATEX_CMD_RE = re.compile(r"\\([a-zA-Z]+)")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalise_text(text: str) -> str:
    """Lower-case, de-accent, and turn LaTeX commands into plain words.

    ``\\lim\\limits_{x \\to 1}`` -> ``lim limits x to 1``: the command names are
    meaningful tokens for maths retrieval, so they are kept rather than dropped.
    """
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = _LATEX_CMD_RE.sub(r" \1 ", text)
    text = _NON_ALNUM_RE.sub(" ", text)
    return text


# --------------------------------------------------------------------------- #
# Base interface
# --------------------------------------------------------------------------- #
class Embedder:
    """Common interface: ``dim`` + ``encode(texts, input_type)``."""

    backend_name = "base"

    def __init__(self, model: str, dim: int | None = None):
        self.model = model
        self._dim = dim

    @property
    def dim(self) -> int:
        if self._dim is None:
            probe = self.encode(["dimension probe"], input_type="document")
            self._dim = int(probe.shape[1])
        return self._dim

    def supports_batching(self) -> bool:
        return True

    def fit(self, corpus_texts: Sequence[str]) -> None:  # noqa: D102 - optional
        """Optional: let stateful backends (IDF) see the corpus first."""

    def encode(self, texts: Sequence[str], input_type: str = "document") -> np.ndarray:
        """Return an ``(n, dim)`` float32 array of **L2-normalised** vectors."""
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return f"<{type(self).__name__} model={self.model!r}>"


# --------------------------------------------------------------------------- #
# 1. Offline TF-IDF hashing fallback
# --------------------------------------------------------------------------- #
class HashingEmbedder(Embedder):
    """Deterministic lexical embeddings: TF-IDF over word + char n-grams.

    No network, no API key, no model download. Good enough to validate that
    indexing, metadata filtering and ranking all work end to end.
    """

    backend_name = "hashing"

    def __init__(self, model: str = "tfidf-hashing", dim: int = 1024, ngram: int = 4):
        super().__init__(model, dim)
        self.ngram = ngram
        self._doc_count = 0
        self._df: dict[str, int] = {}

    # -- feature extraction ------------------------------------------------ #
    @staticmethod
    def _tokens(text: str) -> list[str]:
        norm = normalise_text(text)
        return [t for t in norm.split() if len(t) > 1 and t not in _FRENCH_STOPWORDS]

    def _features(self, text: str) -> list[str]:
        feats = self._tokens(text)
        compact = re.sub(r"\s+", "", normalise_text(text))
        if len(compact) >= self.ngram:
            # Strided char n-grams: sub-word signal for LaTeX-heavy terms.
            feats.extend(compact[i:i + self.ngram] for i in range(0, len(compact) - self.ngram + 1, 2))
        return feats

    # -- IDF --------------------------------------------------------------- #
    def fit(self, corpus_texts: Sequence[str]) -> None:
        df: dict[str, int] = {}
        n = 0
        for text in corpus_texts:
            n += 1
            for feat in set(self._features(text)):
                df[feat] = df.get(feat, 0) + 1
        self._df = df
        self._doc_count = max(n, 1)

    def _idf(self, feat: str) -> float:
        if not self._df:                      # unfit -> plain sublinear tf
            return 1.0
        df = self._df.get(feat, 0)
        return math.log(1.0 + (self._doc_count / (1.0 + df)))

    # -- persistence ------------------------------------------------------ #
    # The fitted IDF table must be reused at query time, otherwise documents
    # are weighted with IDF while queries are not and the scores diverge.
    def save_state(self, path) -> None:
        import json

        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"dim": self._dim, "ngram": self.ngram,
                        "doc_count": self._doc_count, "df": self._df}),
            encoding="utf-8",
        )

    def load_state(self, path) -> bool:
        import json

        path = Path(path)
        if not path.is_file():
            return False
        data = json.loads(path.read_text(encoding="utf-8"))
        self._dim = int(data.get("dim", self._dim))
        self.ngram = int(data.get("ngram", self.ngram))
        self._doc_count = int(data.get("doc_count", 0))
        self._df = {k: int(v) for k, v in data.get("df", {}).items()}
        return bool(self._df)

    # -- encoding ---------------------------------------------------------- #
    @staticmethod
    def _hash(feat: str) -> tuple[int, int]:
        digest = hashlib.blake2b(feat.encode("utf-8"), digest_size=8).digest()
        value = int.from_bytes(digest, "big")
        return value % (1 << 40), (value >> 40) & 1

    def encode(self, texts: Sequence[str], input_type: str = "document") -> np.ndarray:
        out = np.zeros((len(texts), self._dim), dtype=np.float32)
        for row, text in enumerate(texts):
            counts: dict[str, int] = {}
            for feat in self._features(text):
                counts[feat] = counts.get(feat, 0) + 1
            for feat, tf in counts.items():
                index, sign = self._hash(feat)
                weight = (1.0 + math.log(tf)) * self._idf(feat)
                out[row, index % self._dim] += weight if sign else -weight
        _l2_normalise(out)
        return out


# --------------------------------------------------------------------------- #
# 2. OpenAI-compatible API
# --------------------------------------------------------------------------- #
class OpenAIEmbedder(Embedder):
    """Calls ``POST {base_url}/embeddings`` with the ``openai`` SDK."""

    backend_name = "openai"

    def __init__(self, model: str, api_key: str, base_url: str, dim: int | None = None,
                 batch_size: int = 64, max_retries: int = 4):
        super().__init__(model, dim)
        self.api_key = api_key
        self.base_url = base_url
        self.batch_size = batch_size
        self.max_retries = max_retries
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from openai import OpenAI  # imported lazily: only needed for this backend
            self._client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url or None,
                max_retries=self.max_retries,
                timeout=60.0,
            )
        return self._client

    def encode(self, texts: Sequence[str], input_type: str = "document") -> np.ndarray:
        import time

        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = list(texts[start:start + self.batch_size])
            attempt, delay = 0, 1.5
            while True:
                try:
                    response = self.client.embeddings.create(model=self.model, input=batch)
                    vectors.extend([item.embedding for item in response.data])
                    break
                except Exception:  # noqa: BLE001 - retry on any transport/API error
                    attempt += 1
                    if attempt > self.max_retries:
                        raise
                    time.sleep(delay)
                    delay *= 2
        arr = np.asarray(vectors, dtype=np.float32)
        _l2_normalise(arr)
        return arr


# --------------------------------------------------------------------------- #
# 3. Local sentence-transformers
# --------------------------------------------------------------------------- #
class SentenceTransformerEmbedder(Embedder):
    """Local HuggingFace sentence-transformers model (CPU friendly)."""

    backend_name = "sentence-transformers"

    def __init__(self, model: str, dim: int | None = None, batch_size: int = 32, device: str | None = None):
        super().__init__(model, dim)
        self.batch_size = batch_size
        self.device = device
        self._model = None

    @property
    def st_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model, device=self.device)
        return self._model

    def encode(self, texts: Sequence[str], input_type: str = "document") -> np.ndarray:
        payload = list(texts)
        # E5 family is trained with explicit role prefixes.
        if "e5" in self.model.lower():
            prefix = "query: " if input_type == "query" else "passage: "
            payload = [prefix + t for t in payload]
        arr = self.st_model.encode(
            payload,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(arr, dtype=np.float32)


# --------------------------------------------------------------------------- #
# Helpers / factory
# --------------------------------------------------------------------------- #
def _l2_normalise(matrix: np.ndarray) -> None:
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix /= norms


def hashing_state_path(config: Config):
    """Where the fitted IDF table for the offline backend is cached."""
    return Path(config.chroma_dir) / f"{config.collection_name}-hashing-idf.json"


def _have_sentence_transformers() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def get_embedder(config: Config, verbose: bool = True) -> Embedder:
    """Pick an embedder from the config, honouring ``EMBEDDING_BACKEND``.

    ``auto`` resolution order:
      1. ``openai``   -- when model *and* key are real (placeholders filled in)
      2. ``sentence-transformers`` -- when the package is installed
      3. ``hashing``  -- always available offline fallback
    """
    backend = (config.embedding_backend or "auto").lower()
    model = config.embedding_model or PLACEHOLDER_MODEL
    key_ready = not config.api_key_is_placeholder()

    if backend == "auto":
        if not config.model_is_placeholder() and key_ready:
            backend = "openai"
        elif _have_sentence_transformers():
            backend = "sentence-transformers"
            if model == PLACEHOLDER_MODEL:
                model = config.embedding_model_local
        else:
            backend = "hashing"

    if backend == "openai":
        if key_ready is False or config.model_is_placeholder():
            raise SystemExit(
                "EMBEDDING_BACKEND=openai but the model/API key are still placeholders.\n"
                f"  model = {model!r}\n"
                "  Set EMBEDDING_MODEL and EMBEDDING_API_KEY (or edit .env) first."
            )
        embedder: Embedder = OpenAIEmbedder(
            model=model,
            api_key=config.embedding_api_key,
            base_url=config.embedding_base_url,
            dim=config.embedding_dim,
            batch_size=config.embedding_batch_size,
        )
    elif backend in ("sentence-transformers", "st", "local"):
        if model == PLACEHOLDER_MODEL:
            model = config.embedding_model_local
        embedder = SentenceTransformerEmbedder(
            model=model, dim=config.embedding_dim, batch_size=config.embedding_batch_size
        )
    elif backend in ("hashing", "tfidf", "offline"):
        embedder = HashingEmbedder(dim=config.embedding_dim or 1024)
        # Reuse the IDF table fitted at ingestion time, if the index was built
        # with this backend.
        if embedder.load_state(hashing_state_path(config)):
            if verbose:
                print(f"[embeddings] loaded IDF state ({embedder._doc_count} docs)")
    else:
        raise SystemExit(f"Unknown EMBEDDING_BACKEND={backend!r} (expected auto|openai|sentence-transformers|hashing)")

    if verbose:
        print(f"[embeddings] backend={embedder.backend_name} model={embedder.model}")
        if embedder.backend_name == "hashing":
            print("[embeddings] NOTE: offline lexical fallback in use "
                  "(no EMBEDDING_MODEL/EMBEDDING_API_KEY configured).")
        elif embedder.backend_name == "sentence-transformers" and config.model_is_placeholder():
            print("[embeddings] NOTE: no EMBEDDING_MODEL/EMBEDDING_API_KEY configured, so a local "
                  "model is used. It will be downloaded on first run (~500 MB).")
    return embedder
