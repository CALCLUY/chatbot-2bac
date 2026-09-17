"""Step 1 -- read the corpus and split every file into (metadata, body).

Every ``.txt`` file in the corpus starts with a YAML-ish front-matter block::

    ---
    Matière: Physique-Chimie
    Semestre / Section: Semestre 1
    Sujet: Ondes mécaniques progressives
    Type: Cours
    Source:
    ---

    <body>

The header keys are **not** uniform across the three subjects, so this module
normalises them onto one canonical schema (see ``CANONICAL_FIELDS``) and fills
in whatever can be inferred from the file path.

Observed header keys across all 327 files:
    Type (327), Source (327), Matière (205), Sujet (205), Chapitre (143),
    Semestre / Section (132), Filière (73), Séance (70), Professeur (70),
    Année (52), Session (52), Nature (52)

Mathématiques files carry no ``Matière`` key at all -- it is derived from the
top-level directory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .config import MATIERE_BY_DIR

# ``\A`` anchors to the very beginning so a later horizontal rule inside the
# document body is never mistaken for the header fence.
FRONT_MATTER_RE = re.compile(r"\A\s*---[ \t]*\r?\n(.*?)\r?\n[ \t]*---[ \t]*(?:\r?\n|\Z)", re.DOTALL)

# Canonical metadata schema attached to every chunk.
CANONICAL_FIELDS = (
    "matiere",     # Mathématiques | Physique-Chimie | SVT
    "chapitre",    # "Chapitre 1 : Limites et continuité" / SVT chapter title
    "semestre",    # "Semestre 1", "Devoirs SM", "Examens Nationaux", ...
    "seance",      # "Séance 1-1-1 : ..." (maths)
    "sujet",       # lesson / exam / homework title
    "type",        # Cours | Exercices | Examen National | Corrigé | Devoir ...
    "nature",      # Sujet | Corrigé (exam files)
    "annee",       # 2024 ...
    "session",     # Normale | Rattrapage
    "filiere",     # Sciences Mathématiques ...
    "professeur",
    "source",
)

# header key (as written in the files) -> canonical field
_HEADER_KEY_MAP = {
    "matière": "matiere",
    "matiere": "matiere",
    "chapitre": "chapitre",
    "semestre / section": "semestre",
    "semestre": "semestre",
    "section": "semestre",
    "séance": "seance",
    "seance": "seance",
    "sujet": "sujet",
    "type": "type",
    "nature": "nature",
    "année": "annee",
    "annee": "annee",
    "session": "session",
    "filière": "filiere",
    "filiere": "filiere",
    "professeur": "professeur",
    "source": "source",
}


@dataclass
class Document:
    """A parsed corpus file: normalised metadata + raw body."""

    path: Path                       # absolute path on disk
    rel_path: str                    # path relative to the corpus root
    metadata: dict                   # canonical metadata (canonical -> value)
    raw_header: dict = field(default_factory=dict)   # verbatim header keys
    body: str = ""

    # ------------------------------------------------------------------ #
    @property
    def doc_id(self) -> str:
        return self.rel_path

    def get(self, key: str, default: str = "") -> str:
        return self.metadata.get(key, default)


# --------------------------------------------------------------------------- #
# Header parsing
# --------------------------------------------------------------------------- #
def split_front_matter(text: str) -> tuple[dict, str]:
    """Return ``(raw_header_dict, body)``.

    Files without a front-matter block yield an empty header and the full text
    as body (no corpus file currently hits that path, but the parser stays safe).
    """
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text

    raw: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key:
            raw[key] = value

    body = text[match.end():]
    return raw, body


def normalise_header(raw: dict) -> dict:
    """Map verbatim header keys onto the canonical schema."""
    out: dict[str, str] = {}
    for key, value in raw.items():
        canonical = _HEADER_KEY_MAP.get(key.lower())
        if canonical and value:
            out[canonical] = value
    return out


def metadata_from_path(rel_path: str) -> dict:
    """Infer whatever the header does not say, from the directory layout.

    Layouts::
        mathematiques/chapitre-01-limites-et-continuite/seance-1-1-1-cours.txt
        mathematiques/examens-nationaux/2024/2024-normale-corrige.txt
        physique-chimie/semestre-1/01-ondes-mecaniques-progressives-cours.txt
        physique-chimie/examens-nationaux/2024/...
        svt/transfert-information-genetique-reproduction-sexuee/01-cours-partie1.txt
        svt/examens-nationaux/2024/2024-normale-sujet.txt
    """
    parts = Path(rel_path).parts
    inferred: dict[str, str] = {}

    if not parts:
        return inferred

    top = parts[0]
    if top in MATIERE_BY_DIR:
        inferred["matiere"] = MATIERE_BY_DIR[top]

    # A 4-digit directory is the exam year, e.g. examens-nationaux/2024/
    year_dir = next((p for p in parts if re.fullmatch(r"(19|20)\d{2}", p)), None)
    if year_dir:
        inferred["annee"] = year_dir
        inferred.setdefault("semestre", "Examens Nationaux")

    filename = Path(rel_path).stem
    # e.g. "2024-normale-corrige" / "2024-rattrapage-sujet"
    fm = re.match(r"^((?:19|20)\d{2})-(normale|rattrapage)-(sujet|corrige)", filename, re.I)
    if fm:
        inferred["annee"] = fm.group(1)
        inferred["session"] = fm.group(2).capitalize()
        inferred["nature"] = fm.group(3).capitalize()

    return inferred


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def parse_file(path: Path, corpus_root: Path) -> Document:
    """Parse a single ``.txt`` file into a :class:`Document`."""
    text = path.read_text(encoding="utf-8", errors="replace")
    raw_header, body = split_front_matter(text)
    rel_path = str(Path(path).resolve().relative_to(corpus_root.resolve()))

    metadata = normalise_header(raw_header)

    # Path-derived values act as a fallback only -- an explicit header wins.
    for key, value in metadata_from_path(rel_path).items():
        metadata.setdefault(key, value)

    return Document(
        path=Path(path).resolve(),
        rel_path=rel_path,
        metadata=metadata,
        raw_header=raw_header,
        body=body,
    )


def iter_corpus_files(corpus_root: Path) -> list[Path]:
    """Every ``.txt`` file under *corpus_root*, sorted for reproducibility."""
    return sorted(p for p in Path(corpus_root).rglob("*.txt") if p.is_file())


def parse_corpus(corpus_root: Path, limit: int | None = None) -> list[Document]:
    files = iter_corpus_files(corpus_root)
    if limit:
        files = files[:limit]
    return [parse_file(f, corpus_root) for f in files]
