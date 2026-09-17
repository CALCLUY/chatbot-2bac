"""Configuration for the 2bac RAG pipeline (ingestion + retrieval).

All user-editable knobs live here. Every value can be overridden either by an
environment variable or by a `.env` file sitting at the repository root.

The two values you are expected to fill in before running a *real* ingestion are
the embedding model and its API key. They ship as the literal placeholders
``[EMBEDDING_MODEL_HERE]`` / ``[EMBEDDING_API_KEY_HERE]`` so that you can find
them with::

    grep -rn "EMBEDDING_MODEL_HERE\\|EMBEDDING_API_KEY_HERE" .

Until they are filled in the pipeline transparently falls back to a dependency
free *lexical hashing* embedder, which lets you exercise and test the whole
index/retrieve loop offline (see ``rag/embeddings.py``).
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------- #
# Placeholders -- replace these (or set the matching env vars) to go live.
# --------------------------------------------------------------------------- #
PLACEHOLDER_MODEL = "[EMBEDDING_MODEL_HERE]"
PLACEHOLDER_API_KEY = "[EMBEDDING_API_KEY_HERE]"

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load .env if python-dotenv is available (it is optional)."""
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:  # pragma: no cover - optional dependency
        return
    for candidate in (Path.cwd() / ".env", REPO_ROOT / ".env"):
        if candidate.is_file():
            load_dotenv(candidate, override=False)


# Loaded once at import time so that every `_env(...)` call below sees the
# values from `.env`.
_load_dotenv()


def _env(name: str, default: str | None = None) -> str | None:
    return os.getenv(name, default)


def _is_placeholder(value: str | None) -> bool:
    """True when a value is missing, blank, or still an unfilled placeholder."""
    if value is None:
        return True
    stripped = value.strip()
    if not stripped:
        return True
    return stripped.startswith("[") and stripped.endswith("]")


# --------------------------------------------------------------------------- #
# Paths / storage
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    # --- data source -------------------------------------------------------
    # Clone the corpus with:
    #   git clone https://github.com/CALCLUY/data-2bac-sma.git data/data-2bac-sma
    # The .txt files live in the inner `2bac-data-sma/` folder; resolve_data_dir()
    # descends into it automatically, so pointing DATA_DIR at either the clone
    # root or straight at `2bac-data-sma/` both work.
    data_dir: Path = field(default_factory=lambda: Path(_env("DATA_DIR", str(REPO_ROOT / "data" / "data-2bac-sma"))))

    # --- vector store ------------------------------------------------------
    chroma_dir: Path = field(default_factory=lambda: Path(_env("CHROMA_DIR", str(REPO_ROOT / "data" / "chroma_db"))))
    collection_name: str = field(default_factory=lambda: _env("COLLECTION_NAME", "2bac-sma"))

    # Optional JSONL dump of every chunk (handy for debugging / re-embedding
    # without re-parsing the corpus).
    chunks_dump: Path | None = field(default_factory=lambda: (
        Path(p) if (p := _env("CHUNKS_DUMP", str(REPO_ROOT / "data" / "chunks.jsonl"))) else None
    ))

    # --- embeddings --------------------------------------------------------
    embedding_backend: str = field(default_factory=lambda: _env("EMBEDDING_BACKEND", "auto"))
    embedding_model: str = field(default_factory=lambda: _env("EMBEDDING_MODEL", PLACEHOLDER_MODEL))
    embedding_api_key: str = field(default_factory=lambda: _env("EMBEDDING_API_KEY", PLACEHOLDER_API_KEY))
    embedding_base_url: str = field(default_factory=lambda: _env("EMBEDDING_BASE_URL", "https://api.openai.com/v1"))
    # Model used when the backend resolves to sentence-transformers (local).
    embedding_model_local: str = field(default_factory=lambda: _env(
        "EMBEDDING_MODEL_LOCAL", "intfloat/multilingual-e5-small"))
    embedding_batch_size: int = field(default_factory=lambda: int(_env("EMBEDDING_BATCH_SIZE", "64")))
    embedding_dim: int | None = field(default_factory=lambda: (
        int(d) if (d := _env("EMBEDDING_DIM")) else None
    ))

    # --- chunking ----------------------------------------------------------
    chunk_max_chars: int = field(default_factory=lambda: int(_env("CHUNK_MAX_CHARS", "1400")))
    chunk_min_chars: int = field(default_factory=lambda: int(_env("CHUNK_MIN_CHARS", "120")))

    # --- retrieval ---------------------------------------------------------
    top_k: int = field(default_factory=lambda: int(_env("TOP_K", "5")))

    # --- retrieval post-processing (see rag/selection.py) -------------------
    # Drop hits scoring below this fraction of the best hit.
    retrieval_min_score_ratio: float = field(default_factory=lambda: float(_env("RETRIEVAL_MIN_SCORE_RATIO", "0.5")))
    # At most N chunks from any single source file.
    retrieval_max_per_file: int = field(default_factory=lambda: int(_env("RETRIEVAL_MAX_PER_FILE", "2")))
    # MMR trade-off: 1.0 = pure relevance, 0.0 = pure diversity.
    retrieval_mmr_lambda: float = field(default_factory=lambda: float(_env("RETRIEVAL_MMR_LAMBDA", "0.6")))
    # How many candidates to fetch before trimming/diversifying.
    retrieval_fetch_multiplier: int = field(default_factory=lambda: int(_env("RETRIEVAL_FETCH_MULTIPLIER", "4")))

    # --- chat / LLM (step 2) -------------------------------------------------
    # Any OpenAI-compatible /v1/chat/completions endpoint.
    chat_base_url: str = field(default_factory=lambda: _env(
        "CHAT_BASE_URL",
        "https://chatbotoauth-z3twqyf2.manus.space/v1"))
    chat_api_key: str = field(default_factory=lambda: _env("CHAT_API_KEY", "[CHAT_API_KEY_HERE]"))
    chat_model: str = field(default_factory=lambda: _env("CHAT_MODEL", "gpt-5.6-luna"))
    chat_temperature: float = field(default_factory=lambda: float(_env("CHAT_TEMPERATURE", "0.7")))
    chat_max_tokens: int | None = field(default_factory=lambda: (
        int(t) if (t := _env("CHAT_MAX_TOKENS")) else None
    ))
    # How many chunks to ground a chat answer on (more than for bare retrieval,
    # because the tutor needs enough material to build a step-by-step answer).
    chat_top_k: int = field(default_factory=lambda: int(_env("CHAT_TOP_K", "6")))
    chat_timeout: float = field(default_factory=lambda: float(_env("CHAT_TIMEOUT", "120")))

    # ----------------------------------------------------------------- #
    def resolve_data_dir(self) -> Path:
        """Return the folder that actually contains mathematiques/ svt/ ..."""
        base = Path(self.data_dir).expanduser()
        if not base.is_dir():
            return base
        inner = base / "2bac-data-sma"
        if inner.is_dir():
            return inner
        # Some clones put the corpus one level deeper.
        for child in sorted(base.iterdir()):
            if child.is_dir() and (child / "2bac-data-sma").is_dir():
                return child / "2bac-data-sma"
        return base

    def model_is_placeholder(self) -> bool:
        return _is_placeholder(self.embedding_model)

    def api_key_is_placeholder(self) -> bool:
        return _is_placeholder(self.embedding_api_key)

    def chat_key_is_placeholder(self) -> bool:
        return _is_placeholder(self.chat_api_key)

    def describe_embeddings(self) -> str:
        return (
            f"backend={self.embedding_backend} model={self.embedding_model} "
            f"base_url={self.embedding_base_url} "
            f"key={'(placeholder)' if self.api_key_is_placeholder() else 'set'}"
        )


DEFAULT_CONFIG = Config()


# Canonical subject labels (French), used for filtering and for display.
MATIERE_BY_DIR = {
    "mathematiques": "Mathématiques",
    "physique-chimie": "Physique-Chimie",
    "svt": "SVT",
}
