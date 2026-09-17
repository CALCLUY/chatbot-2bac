# chatbot-2bac

Retrieval pipeline for an AI tutor for **2ème Bac Sciences Mathématiques** (Morocco),
covering **Mathématiques**, **Physique-Chimie** and **SVT**.

This repository currently contains **the retrieval layer only** — parse → chunk → embed →
store → retrieve. There is no chat or answer-generation logic yet.

```
corpus (.txt) ──► parser ──► chunker ──► embedder ──► Chroma ──► retrieve(query, filters)
                     │          │            │
                 metadata   LaTeX-safe   swappable
                            boundaries   backends
```

---

## Quick start

```bash
# 1. install
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. get the corpus (the .txt lessons / exercises / exam papers)
git clone https://github.com/CALCLUY/data-2bac-sma.git data/data-2bac-sma

# 3. (optional but recommended) configure real embeddings
cp .env.example .env
#    then replace [EMBEDDING_MODEL_HERE] and [EMBEDDING_API_KEY_HERE]

# 4. build the index
python ingest.py

# 5. sanity-check retrieval
python test_retrieval.py
```

Step 3 is genuinely optional: until you fill in the placeholders the pipeline runs on a
free offline embedder, so you can build an index and test retrieval immediately.

---

## The two placeholders

They live in `rag/config.py` and in `.env.example`. Find them with:

```bash
grep -rn "EMBEDDING_MODEL_HERE\|EMBEDDING_API_KEY_HERE" .
```

| Placeholder | Where | Meaning |
|---|---|---|
| `[EMBEDDING_MODEL_HERE]` | `EMBEDDING_MODEL` | e.g. `text-embedding-3-small` |
| `[EMBEDDING_API_KEY_HERE]` | `EMBEDDING_API_KEY` | your API key |

Any OpenAI-compatible `/embeddings` endpoint works. Point `EMBEDDING_BASE_URL` elsewhere
for Ollama (`http://localhost:11434/v1`), OpenRouter, vLLM, Mistral, Azure, … — still using
the `openai` backend.

### Embedding backends (`EMBEDDING_BACKEND`)

| Value | When it is used | Notes |
|---|---|---|
| `auto` (default) | **openai** if both placeholders are filled → else **sentence-transformers** if installed → else **hashing** | recommended |
| `openai` | forced | errors out clearly if the placeholders are still unfilled |
| `sentence-transformers` | forced local model | free, offline, CPU; needs the optional dependency (pulls in torch) |
| `hashing` | forced offline fallback | zero dependencies, deterministic, TF-IDF — **lexical, not semantic** |

> The `hashing` backend exists so the pipeline is testable before you have a model or a key.
> It validates indexing, metadata filtering and ranking, but for real semantic quality
> configure `openai` (or `sentence-transformers`) and rebuild.

---

## Ingestion — `python ingest.py`

Builds the vector index from the corpus. It is idempotent: it rebuilds the collection from
scratch each run (`--no-reset` appends instead).

```bash
python ingest.py                    # build the full index
python ingest.py --stats-only       # parse + chunk + report, write nothing
python ingest.py --limit 20         # first 20 files only (fast smoke test)
python ingest.py --no-reset         # add to the existing collection
python ingest.py --data-dir /path/to/2bac-data-sma
```

Output:

```
[stats] corpus root : data/data-2bac-sma/2bac-data-sma
[stats] .txt files  : 327
[stats]   physique-chimie    132
[stats]   mathematiques      122
[stats]   svt                73
[parse] 327 documents
[chunk] 3196 chunks; LaTeX violations: 0
[embeddings] backend=hashing model=tfidf-hashing
[store] collection '2bac-sma' now holds 3196 vectors

[done] files=327  chunks=3196  dim=1024  backend=hashing  latex_violations=0  elapsed=7.7s
```

Artefacts written (all under `data/`, all git-ignored):

| Path | Contents |
|---|---|
| `data/chroma_db/` | the Chroma persistent index |
| `data/chunks.jsonl` | one JSON object per chunk (content + metadata) for offline inspection |
| `data/chroma_db/<collection>-hashing-idf.json` | fitted IDF table, only for the `hashing` backend |

---

## Retrieval — `python retrieve.py`

```python
from retrieve import retrieve

hits = retrieve(
    "Comment calculer la limite d'une fonction en un point ?",
    matiere="Mathématiques",      # optional filter
    chapitre="Chapitre 1 : Limites et continuité",   # optional filter
    top_k=5,
)

for hit in hits:
    print(hit.score, hit.metadata["file_path"])
    print(hit.content)            # verbatim chunk, LaTeX intact
```

Each hit is a `RetrievedChunk` with:

* `.content` — the verbatim chunk text (LaTeX untouched),
* `.metadata` — all 24 metadata fields,
* `.score` — cosine similarity (higher is better).

### Filtering

Filters are exact-match metadata filters: `matiere`, `chapitre`, `type`, `annee`,
`block_type`, or any of `semestre`, `seance`, `sujet`, `nature`, `session`, `filiere`
via a raw clause.

```python
# Only exam papers
retrieve("décroissance radioactive", type="Examen National", annee=2024)

# Only definitions
retrieve("limite", block_type="définition")

# Escape hatch: a raw Chroma where-clause
retrieve("méiose", where={"$or": [{"matiere": {"$eq": "SVT"}}, {"matiere": {"$eq": "Mathématiques"}}]})
```

`chapitre` also matches the `semestre` field, because Physique-Chimie files are organised
by semester rather than by chapter (`Chapitre` vs `Semestre / Section` in the headers).

### Command line

```bash
python retrieve.py "c'est quoi la méiose ?"
python retrieve.py "limite d'une fonction" --matiere Mathématiques --top-k 3
python retrieve.py "décroissance radioactive" --chapitre "Semestre 1"
python retrieve.py "probabilités" --type "Examen National" --annee 2024
```

Reuse one `Retriever` for many questions — the model and the collection are loaded once:

```python
from retrieve import Retriever
r = Retriever()
r.retrieve("..."), r.retrieve("..."), r.retrieve("...")
```

---

## Testing — `python test_retrieval.py`

Three sample queries (one per subject) plus one filtered query, printing retrieved chunks
with their source metadata.

```bash
python test_retrieval.py            # full output
python test_retrieval.py --brief    # score + source per hit
python test_retrieval.py --json     # machine-readable
python test_retrieval.py --top-k 5
```

Beyond printing, it asserts for every query that: results are returned, every hit
satisfies the metadata filters, scores are non-negative, and results are ordered
best-first. It exits non-zero if any check fails — so it works as a smoke test in CI.

---

## How the pipeline works

### 1. Parsing (`rag/parser.py`)

Each `.txt` file starts with a front-matter block:

```
---
Matière: Physique-Chimie
Semestre / Section: Semestre 1
Sujet: Ondes mécaniques progressives
Type: Cours
Source:
---
<body>
```

Header keys differ between subjects, so they are normalised onto one schema. Observed
across all 327 files: `Type` and `Source` (327), `Matière` and `Sujet` (205), `Chapitre`
(143), `Semestre / Section` (132), `Filière` (73), `Séance` and `Professeur` (70),
`Année`/`Session`/`Nature` (52).

**Mathématiques files carry no `Matière` key**, so `matiere` is derived from the top-level
directory; exam files get `annee`, `session` and `nature` from the path
(`2024-normale-corrige.txt` → 2024 / Normale / Corrigé). An explicit header always wins
over a path-derived value.

### 2. Chunking (`rag/chunker.py`)

Chunks follow the structure the teachers wrote, not blind character counts:

* **headings** (`##`, `###`, `####`) always start a new chunk;
* **block labels** — `Définition`, `Proposition`, `Théorème`, `Corollaire`, `Exemple`,
  `Remarque`, `Application`, `Preuve`, `Exercice`, `Document`, … — always start a new chunk;
* consecutive segments are then packed up to `CHUNK_MAX_CHARS` (default 1400);
* chunks below `CHUNK_MIN_CHARS` (120) are folded into a neighbour so no one-liner like a
  bare heading or the word *Preuve* is indexed on its own;
* slide numbers (`1/7`), `* * *` separators, `FIN` markers and the repeated title/professor
  boilerplate are dropped.

Example — `seance-1-1-1-cours-partie1.txt` becomes:

```
[0] paragraphe    304c   "Séance 1-1-1 : Limites et continuité - Partie 1 (Cours)"
[1] définition    672c   "Définition 1"
[2] application   568c   "Application"
[3] proposition  1070c   "Proposition 2"
[4] proposition   785c   "Proposition 3"
```

**LaTeX is never split.** A survey of the whole corpus showed every `$…$` and `$$…$$`
expression is fully contained on one line (0 lines with an unbalanced `$`, 0 display blocks
spanning a newline). The chunker therefore only ever cuts *between* complete lines, which
makes splitting a formula impossible. `validate_latex_integrity()` re-checks every finished
chunk and the ingestion summary reports the count (`latex_violations=0`), so a future corpus
update cannot silently break the invariant.

Each chunk also carries a `breadcrumb` (subject › chapter › section path) that is prefixed
to the text sent to the embedding model — the stored `content` stays verbatim.

### 3. Metadata on every chunk (24 fields)

From the header: `matiere`, `chapitre`, `semestre`, `seance`, `sujet`, `type`, `nature`,
`annee`, `session`, `filiere`, `professeur`, `source`.

Added by the chunker: `file_path`, `file_name`, `heading_path`, `block_type`, `chunk_index`,
`n_chunks`, `start_line`, `char_count`, `has_math`, `has_formula_image`, `chunk_id`,
`embedding_text`.

### 4. Storage (`rag/vectorstore.py`)

[Chroma](https://www.trychroma.com/) in `PersistentClient` mode — an ordinary directory on
disk, no server, no paid plan — chosen over FAISS because metadata filtering is built in.
The collection uses `hnsw:space = cosine` and vectors are L2-normalised.

---

## Configuration reference

All settings can be set in `.env` or as environment variables (see `.env.example`):

| Variable | Default | Purpose |
|---|---|---|
| `EMBEDDING_MODEL` | `[EMBEDDING_MODEL_HERE]` | embedding model name |
| `EMBEDDING_API_KEY` | `[EMBEDDING_API_KEY_HERE]` | API key |
| `EMBEDDING_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `EMBEDDING_BACKEND` | `auto` | `auto` / `openai` / `sentence-transformers` / `hashing` |
| `EMBEDDING_MODEL_LOCAL` | `intfloat/multilingual-e5-small` | local model for sentence-transformers |
| `EMBEDDING_BATCH_SIZE` | `64` | texts per API call |
| `DATA_DIR` | `./data/data-2bac-sma` | corpus location |
| `CHROMA_DIR` | `./data/chroma_db` | index location |
| `COLLECTION_NAME` | `2bac-sma` | Chroma collection |
| `CHUNK_MAX_CHARS` | `1400` | chunk size ceiling |
| `CHUNK_MIN_CHARS` | `120` | chunks below this are merged |
| `TOP_K` | `5` | default number of results |

---

## Layout

```
ingest.py              CLI: build the vector index
retrieve.py            CLI + reusable retrieve() function
test_retrieval.py      three sample queries, prints chunks + metadata
requirements.txt
.env.example           copy to .env and fill in the placeholders
rag/
  config.py            settings, placeholders, backend resolution
  parser.py            front-matter parsing + metadata normalisation
  chunker.py           semantic, LaTeX-safe chunking + integrity check
  embeddings.py        openai / sentence-transformers / hashing backends
  vectorstore.py       Chroma wrapper, filters, provenance
  pipeline.py          parse -> chunk -> embed -> upsert
  display.py           terminal rendering
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| `corpus not found at …` | clone the corpus: `git clone https://github.com/CALCLUY/data-2bac-sma.git data/data-2bac-sma` |
| `The vector index is empty` | run `python ingest.py` first |
| `Unsupported filter 'x'` | use one of: `matiere`, `chapitre`, `semestre`, `seance`, `sujet`, `type`, `nature`, `annee`, `session`, `filiere`, `block_type` |
| `[warn] index was built with … but you are querying it with …` | the embedder changed; re-run `python ingest.py` — scores from two different models are not comparable |
| slow first `sentence-transformers` run | it downloads the model (~500 MB) once, then caches it |
| poor relevance | if you are on the `hashing` backend, that is expected — configure real embeddings and rebuild |
