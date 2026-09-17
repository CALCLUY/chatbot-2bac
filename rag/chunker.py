"""Step 2 -- split each document body into semantic, LaTeX-safe chunks.

Design goals (from the spec):

* chunk on *logical* boundaries -- headings, and the "Définition / Théorème /
  Proposition / Exemple / Remarque / Exercice / ..." block labels that the
  teachers use -- rather than on blind character counts;
* never split a LaTeX formula across chunks;
* attach the parsed file metadata to every chunk.

Why splitting is guaranteed LaTeX-safe
--------------------------------------
A survey of all 327 corpus files shows that **every** ``$...$`` and ``$$...$$``
expression is fully contained on a single line (0 lines with an unbalanced
``$``, 0 display blocks spanning a newline). The chunker therefore only ever
cuts *between* complete lines, which makes it impossible to cut a formula.
``validate_latex_integrity()`` re-asserts that invariant on the finished
chunks so a future corpus update cannot silently break it.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass, field

from .config import Config
from .parser import CANONICAL_FIELDS, Document

# --------------------------------------------------------------------------- #
# Line classification
# --------------------------------------------------------------------------- #
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Standalone "block label" lines, e.g. "Définition 1", "Proposition 2",
# "Exemple", "Remarques", "Preuve", "Exercice 3", "Document 2", ...
LABEL_WORDS = (
    r"d[ée]finition|propri[ée]t[ée]s?|th[ée]or[èe]me|corollaire|lemme|proposition|"
    r"exemples?|applications?|remarques?|rappels?|preuve|d[ée]monstration|"
    r"m[ée]thodes?|activit[ée]s?|exercices?|corrig[ée]s?|solutions?|documents?|"
    r"conclusion|cons[ée]quences?|r[ée]sum[ée]s?"
)
LABEL_RE = re.compile(
    rf"^(?P<label>{LABEL_WORDS})(?P<num>\s*[0-9]+(?:\s*[.\-][0-9]+)*)?\s*[:\-\u2013]?\s*$",
    re.IGNORECASE,
)

# Slide/page numbers used by the SVT course PDFs ("1/7").
PAGE_MARKER_RE = re.compile(r"^\s*\d{1,2}\s*/\s*\d{1,2}\s*$")
SEPARATOR_RE = re.compile(r"^\s*(?:\*\s*\*\s*\*|-{3,}|_{3,}|={3,})\s*$")
# Boilerplate title block repeated right after the front matter.
BOILERPLATE_RE = re.compile(
    r"^\s*(?:Professeur\s*:.*|Math[ée]matiques\s*:.*|Physique et Chimie\s*:.*|"
    r"Sciences de la Vie et de la Terre\s*:?.*|SVT\s*:.*|FIN\b.*)\s*$",
    re.IGNORECASE,
)
MATH_RE = re.compile(r"\$")
FORMULA_IMAGE_RE = re.compile(r"\[FORMULA_IMAGE_UNREADABLE\]")

KIND_HEADING = "heading"
KIND_LABEL = "label"
KIND_TEXT = "text"
KIND_SKIP = "skip"
KIND_BLANK = "blank"


def classify_line(line: str) -> tuple[str, re.Match | None]:
    if not line.strip():
        return KIND_BLANK, None
    m = HEADING_RE.match(line)
    if m:
        return KIND_HEADING, m
    m = LABEL_RE.match(line.strip())
    if m:
        return KIND_LABEL, m
    if PAGE_MARKER_RE.match(line) or SEPARATOR_RE.match(line):
        return KIND_SKIP, None
    return KIND_TEXT, None


def _is_boilerplate(line: str, index_within_body: int) -> bool:
    """Title/professor lines are only boilerplate in the first few lines."""
    return index_within_body < 12 and bool(BOILERPLATE_RE.match(line))


# --------------------------------------------------------------------------- #
# Segment / chunk containers
# --------------------------------------------------------------------------- #
@dataclass
class Segment:
    """A run of complete lines that must stay together (one paragraph or one
    heading/label line)."""
    lines: list[str]
    heading_path: tuple[str, ...]
    kind: str
    start_line: int
    label: str | None = None

    @property
    def text(self) -> str:
        return "\n".join(self.lines).strip()

    @property
    def size(self) -> int:
        return len(self.text)

    @property
    def is_boundary(self) -> bool:
        """Boundaries always begin a new chunk."""
        return self.kind in (KIND_HEADING, KIND_LABEL)


@dataclass
class Chunk:
    content: str
    metadata: dict = field(default_factory=dict)

    @property
    def chunk_id(self) -> str:
        return self.metadata["chunk_id"]

    @property
    def embedding_text(self) -> str:
        return self.metadata["embedding_text"]

    def __len__(self) -> int:
        return len(self.content)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def normalise_for_embedding(text: str) -> str:
    """Light cleanup applied *only* to the text sent to the embedding model.

    The stored ``content`` is always the verbatim original (LaTeX intact); this
    function only removes pure-noise LaTeX artefacts so the encoder sees a
    cleaner signal.
    """
    out = text
    # Empty \\left. / \\right. delimiters are artifacts of the PDF extraction.
    out = re.sub(r"\\(left|right)\s*\.", "", out)
    # Collapse runs of whitespace but keep paragraph breaks readable.
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def _slug(value: str) -> str:
    value = unicodedata.normalize("NFD", value.lower())
    value = "".join(c for c in value if unicodedata.category(c) != "Mn")
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value


def _make_chunk_id(rel_path: str, index: int, content: str) -> str:
    stem = rel_path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    digest = hashlib.sha1(f"{rel_path}::{index}::{content}".encode("utf-8")).hexdigest()[:12]
    return f"{_slug(stem)}-{index:03d}-{digest}"


# --------------------------------------------------------------------------- #
# Segmentation
# --------------------------------------------------------------------------- #
def build_segments(doc: Document) -> list[Segment]:
    """Turn a document body into ordered :class:`Segment` objects."""
    segments: list[Segment] = []
    stack: list[tuple[int, str]] = []   # (heading level, heading title)
    current: list[str] = []
    current_kind = KIND_TEXT
    current_path: tuple[str, ...] = ()
    current_label: str | None = None
    start_line = 0

    def flush() -> None:
        nonlocal current, current_kind, current_label
        if current and any(l.strip() for l in current):
            segments.append(
                Segment(
                    lines=list(current),
                    heading_path=current_path,
                    kind=current_kind,
                    start_line=start_line,
                    label=current_label,
                )
            )
        current = []
        current_kind = KIND_TEXT
        current_label = None

    body_lines = doc.body.split("\n")
    seen_content = 0

    for lineno, raw_line in enumerate(body_lines, start=1):
        line = raw_line.rstrip()
        kind, match = classify_line(line)

        if kind == KIND_BLANK:
            flush()
            continue
        if kind == KIND_SKIP:
            continue
        if _is_boilerplate(line, seen_content):
            continue

        seen_content += 1

        if kind == KIND_HEADING:
            assert match is not None
            level, title = len(match.group(1)), match.group(2).strip()
            flush()
            while stack and stack[-1][0] >= level:
                stack.pop()
            stack.append((level, title))
            current_path = tuple(t for _, t in stack)
            current = [line]
            current_kind = KIND_HEADING
            start_line = lineno
            continue

        if kind == KIND_LABEL:
            assert match is not None
            label = match.group("label").lower()
            num = (match.group("num") or "").strip()
            flush()
            current_path = tuple(t for _, t in stack)
            current = [line]
            current_kind = KIND_LABEL
            current_label = f"{label} {num}".strip()
            start_line = lineno
            continue

        # Plain text: continue the current paragraph.
        if not current:
            current_path = tuple(t for _, t in stack)
            current_kind = KIND_TEXT
            start_line = lineno
        current.append(line)

    flush()
    return segments


# --------------------------------------------------------------------------- #
# Packing
# --------------------------------------------------------------------------- #
def _split_oversize(seg: Segment, max_chars: int) -> list[Segment]:
    """Break one huge segment on *line* boundaries (never inside a line)."""
    parts: list[Segment] = []
    buf: list[str] = []
    size = 0
    start = seg.start_line
    for i, line in enumerate(seg.lines):
        if buf and size + len(line) + 1 > max_chars:
            parts.append(Segment(list(buf), seg.heading_path, seg.kind, start, seg.label))
            buf, size = [], 0
            start = seg.start_line + i
        buf.append(line)
        size += len(line) + 1
    if buf:
        parts.append(Segment(list(buf), seg.heading_path, seg.kind, start, seg.label))
    return parts


def pack_segments(segments: list[Segment], max_chars: int, min_chars: int) -> list[list[Segment]]:
    """Group segments into chunks: respect boundaries, then heal tiny chunks."""
    groups: list[list[Segment]] = []
    current: list[Segment] = []
    current_size = 0

    for seg in segments:
        pieces = _split_oversize(seg, max_chars) if seg.size > max_chars else [seg]
        for piece in pieces:
            if current and (piece.is_boundary or current_size + piece.size > max_chars):
                groups.append(current)
                current, current_size = [], 0
            current.append(piece)
            current_size += piece.size + 2

    if current:
        groups.append(current)

    # Heal undersized chunks by folding them into a neighbour, so we do not
    # index one-liners such as a bare heading or the word "Preuve".
    merge_ceiling = int(max_chars * 1.5)
    merged: list[list[Segment]] = []
    for group in groups:
        size = sum(s.size for s in group)
        if merged:
            prev_size = sum(s.size for s in merged[-1])
            if prev_size < min_chars or size < min_chars:
                if prev_size + size <= merge_ceiling:
                    merged[-1].extend(group)
                    continue
        merged.append(group)

    # A trailing runt would otherwise survive the pass above.
    if len(merged) > 1:
        last_size = sum(s.size for s in merged[-1])
        prev_size = sum(s.size for s in merged[-2])
        if last_size < min_chars and prev_size + last_size <= merge_ceiling:
            merged[-2].extend(merged.pop())

    return merged


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def _block_type(group: list[Segment]) -> str:
    first = group[0]
    if first.kind == KIND_LABEL and first.label:
        return first.label.split(" ")[0]
    if first.kind == KIND_HEADING:
        return "section"
    return "paragraphe"


def chunk_document(doc: Document, config: Config) -> list[Chunk]:
    """Chunk a single parsed document."""
    segments = build_segments(doc)
    if not segments:
        return []

    groups = pack_segments(segments, config.chunk_max_chars, config.chunk_min_chars)
    total = len(groups)
    chunks: list[Chunk] = []

    for index, group in enumerate(groups):
        content = "\n\n".join(s.text for s in group if s.text).strip()
        if not content:
            continue

        heading_path = group[0].heading_path
        meta = {key: doc.metadata.get(key, "") for key in CANONICAL_FIELDS}
        meta.update(
            {
                "file_path": doc.rel_path,
                "file_name": doc.rel_path.rsplit("/", 1)[-1],
                "heading_path": " > ".join(heading_path),
                "block_type": _block_type(group),
                "chunk_index": index,
                "n_chunks": total,
                "start_line": group[0].start_line,
                "char_count": len(content),
                "has_math": bool(MATH_RE.search(content)),
                "has_formula_image": bool(FORMULA_IMAGE_RE.search(content)),
            }
        )

        # Human/encoder facing context prefix: subject + chapter + section path.
        breadcrumb = " / ".join(
            p for p in (meta.get("matiere"), meta.get("chapitre") or meta.get("semestre"),
                        meta.get("sujet"), meta.get("heading_path")) if p
        )
        meta["embedding_text"] = (
            f"{breadcrumb}\n{content}" if breadcrumb else content
        )

        meta["chunk_id"] = _make_chunk_id(doc.rel_path, index, content)
        chunks.append(Chunk(content=content, metadata=meta))

    # n_chunks must reflect the chunks we actually kept.
    for chunk in chunks:
        chunk.metadata["n_chunks"] = len(chunks)
    return chunks


def chunk_documents(docs: list[Document], config: Config) -> list[Chunk]:
    out: list[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, config))
    return out


# --------------------------------------------------------------------------- #
# Validation
# --------------------------------------------------------------------------- #
def validate_latex_integrity(chunks: list[Chunk]) -> list[str]:
    """Return a list of chunks whose LaTeX delimiters are unbalanced.

    Empty list == the "never split a formula" invariant holds.
    """
    bad: list[str] = []
    for chunk in chunks:
        for line in chunk.content.split("\n"):
            stripped = re.sub(r"\$\$.*?\$\$", "", line)   # drop complete display maths
            if stripped.count("$") % 2:
                bad.append(chunk.metadata.get("chunk_id", "?"))
                break
    return bad
