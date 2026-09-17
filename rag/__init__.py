"""Retrieval-augmented generation pipeline for the 2ème Bac SM (Maroc) AI tutor.

Scope of this package is deliberately limited to *retrieval*:
parse -> chunk -> embed -> store -> retrieve. No chat / answer-generation logic.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["config", "parser", "chunker", "embeddings", "vectorstore", "pipeline"]
