"""Terminal rendering helpers shared by ``retrieve.py`` and ``test_retrieval.py``."""

from __future__ import annotations

from typing import Sequence

from .vectorstore import RetrievedChunk

WIDTH = 100


def _rule(char: str = "─") -> str:
    return char * WIDTH


def truncate(text: str, max_chars: int) -> str:
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + " …"


def format_chunk(hit: RetrievedChunk, max_chars: int = 500, show_content: bool = True) -> str:
    """Render one hit as a readable, copy-pasteable block."""
    meta = hit.metadata
    where_bits = [meta.get("matiere", ""), meta.get("chapitre") or meta.get("semestre", ""),
                  meta.get("sujet", ""), meta.get("type", "")]
    location = " | ".join(b for b in where_bits if b)

    lines = [
        f"  [{hit.score:.4f}]  {hit.chunk_id}",
        f"           {location}",
        f"           file: {meta.get('file_path', '')} "
        f"(chunk {meta.get('chunk_index')}/{meta.get('n_chunks')}, line {meta.get('start_line')})",
    ]
    heading = meta.get("heading_path", "")
    if heading:
        lines.append(f"           section: {truncate(heading, 90)}")
    flags = []
    if meta.get("block_type"):
        flags.append(str(meta["block_type"]))
    if meta.get("has_math"):
        flags.append("LaTeX")
    if meta.get("has_formula_image"):
        flags.append("figure")
    if flags:
        lines.append(f"           tags: {', '.join(flags)}")

    if show_content:
        lines.append("")
        body = hit.content.strip()
        if len(body) > max_chars:
            body = body[:max_chars].rstrip() + " …"
        for paragraph in body.split("\n"):
            paragraph = paragraph.rstrip()
            if paragraph:
                lines.append(f"           {paragraph}")
    return "\n".join(lines)


def print_results(query: str, hits: Sequence[RetrievedChunk], filters: dict | None = None,
                  max_chars: int = 500) -> None:
    print(_rule("═"))
    print(f"QUERY: {query}")
    if filters:
        rendered = ", ".join(f"{k}={v}" for k, v in filters.items() if v)
        if rendered:
            print(f"FILTERS: {rendered}")
    print(_rule("═"))
    if not hits:
        print("  (no results)")
        return
    for rank, hit in enumerate(hits, start=1):
        print(f"\n#{rank}")
        print(format_chunk(hit, max_chars=max_chars))
    print()
