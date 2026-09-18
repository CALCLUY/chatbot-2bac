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

## Chat tutor (step 2) — `python chat.py`

A plain-text chat loop for judging **teaching quality** before any UI, animation
or TTS work.

```bash
python chat.py                                  # interactive
python chat.py --matiere SVT                    # start scoped to a subject
python chat.py -q "c'est quoi une limite ?" --matiere Mathématiques
```

In-chat commands: `/matiere <nom>`, `/chapitre <nom>` (or `off` to clear),
`/sources`, `/prompt` (dump the last request), `/reset`, `/help`, `/quit`.

Each turn:

1. retrieves grounded chunks with the step-1 retriever (subject/chapter filters
   applied, MMR-diversified so you get a lesson + an example rather than six
   copies of one exam paper);
2. builds `[system prompt] + [conversation history] + [<contexte> chunks + question]`;
3. calls the Gemini ``generateContent`` API via the isolated client in
   ``rag/llm.py`` (OpenAI-shaped ``messages`` in, plain text out);
4. prints the answer **followed by the sources it drew from** (file, séance,
   score) for your own verification — real students would not see that block.

### The system prompt

In **`rag/prompts.py`**, not inline:

* `TUTOR_SYSTEM_PROMPT` — the tutor's voice and pedagogy (darija + French,
  step-by-step, never hand over an exam answer, …).
* `GROUNDING_INSTRUCTIONS` — how to use the retrieved context and cite it
  (`[Source N]`). Set it to `""` to drop it.

`SYSTEM_PROMPT` is the two concatenated, which is what gets sent.

The tutor prompt is written around an explicit anti-goal — *"ton objectif n'est
PAS de donner l'information la plus complète possible rapidement"* — and four
enforceable rule blocks:

| Rule block | What it constrains |
|---|---|
| **Langue** | darija in latin script + technical vocabulary kept in French |
| **Découpage strict** | one new idea per reply, hard cap of **3 sentences**, never définition+exemple+exercice in one message, complex notions split even further (intuition → check → formal) |
| **Exemples concrets / images mentales** | an analogy from a Moroccan teenager's daily life **before** the formal definition, a second numeric example after it, "tsawwar / imagine / chouf f rassek" for the truly abstract notions |
| **Réponses d'examen** | a fixed 4-step process — ask what they tried → one hint → guide one step at a time → reveal **only** after ≥2 guidance exchanges *and* an explicit request ("wrini l7al"). Exception: a student who already proposed an answer and asks to *check* it |

Scenarios 6–9 of the test harness exist specifically to stress these four
blocks; `check_transcripts.py` turns the results into a review note.

### Configuration (Gemini)

The tutor talks to **Google Gemini**, not an OpenAI-style chat-completions
endpoint. Copy `.env.example` to `.env` and paste a real key:

1. Open [Google AI Studio](https://aistudio.google.com/apikey) and create an API key.
2. Put it on the `GEMINI_API_KEY=` line in `.env` (that file is git-ignored).
3. Leave `GEMINI_MODEL_NAME` / `GEMINI_API_ENDPOINT` as they are unless you
   need another model or a proxy.

Do **not** put the key in source code. `.env.example` ships with an empty
`GEMINI_API_KEY=`.

| Variable | Default |
|---|---|
| `GEMINI_API_KEY` | *(empty — paste your key here)* |
| `GEMINI_MODEL_NAME` | `gemini-3.8-flash` |
| `GEMINI_API_ENDPOINT` | `https://generativelanguage.googleapis.com/v1beta` |
| `CHAT_TEMPERATURE` | `0.7` |
| `CHAT_TOP_K` | `6` (chunks used to ground each answer) |

Add your `GEMINI_API_KEY` in `.env`, then run `python test_gemini_client.py`
to verify the request mapping and response parsing (that script is **mock-
mode**: it does not call Gemini). Once the key is set, run
`python chat.py -q "c'est quoi une limite ?" --matiere Mathématiques` or
`python run_test_conversations.py` for an end-to-end live check.

The old OpenAI-style `CHAT_BASE_URL` / `CHAT_API_KEY` / `CHAT_MODEL` variables
are commented out in `.env.example` and labelled **OLD — OpenAI, no longer
used**.

#### Gemini safety (SVT / biology)

Default Gemini safety filters can block legitimate 2ème Bac SVT content
(méiose, reproduction, caryotype, …) under `HARM_CATEGORY_SEXUALLY_EXPLICIT`.
`rag/llm.py` therefore sends educational safety settings:
`BLOCK_NONE` for sexually explicit, `BLOCK_ONLY_HIGH` for harassment / hate /
dangerous content. If a curriculum question is still blocked, the error
message includes `blockReason` / `finishReason` so you can see it.

There is **no JSON step-structure** in this tutor: replies are spoken
darija-French prose. The existing darija/document retry in `chat.py` is what
re-asks the model when the first draft is unusable; that loop is unchanged
and works with Gemini the same way (plain text in, plain text out).

### Test conversations — `python run_test_conversations.py`

Runs nine scripted conversations and writes them to `transcripts/`
(`.md` for reading, `.json` for diffing):

| # | Scenario | What it checks |
|---|---|---|
| 1 | `1-maths-concept` | a maths concept question (limites) |
| 2 | `2-physique-exercice` | a physics exercise — must guide, not answer |
| 3 | `3-svt-question` | an SVT course question (méiose) |
| 4 | `4-pas-compris` | "j'ai pas compris" — must re-explain *differently* |
| 5 | `5-examen-reponse` | demanding an exam answer — guides first, yields only if the student insists |
| 6 | `6-multi-tour-erreur` | **edge case** — 4 turns where the student gets it wrong, then over-generalises: does the tutor keep context and stay patient? |
| 7 | `7-eleve-decourage` | **edge case** — "ma fahemch walou, khasni no9ta": stays patient, does *not* dump the answer to end the frustration |
| 8 | `8-eleve-obsine-reponse-examen` | **edge case** — insists on the exam answer 3 times in a row (incl. an explicit "wrini l7al"): does the 4-step guidance process hold, or does it cave early? |
| 9 | `9-hors-programme` | **edge case** — crypto, astronomy, Python: says clearly it is out of programme instead of inventing an answer |

```bash
python run_test_conversations.py                    # all nine
python run_test_conversations.py --only svt         # just one
python run_test_conversations.py --require-live     # abort rather than write INCOMPLETE files
```

If the API is unreachable the script still writes every transcript, marked
**INCOMPLETE**, with the retrieved sources intact — so you can review the
grounding now and fill in the answers by re-running later. A preflight probe
reports a dead endpoint in seconds instead of after all 21 turns
(`--skip-preflight` to disable it).

### Auditing the transcripts — `python check_transcripts.py`

Reads `transcripts/*.json` and writes `transcripts/REVIEW-NOTES.md`: per turn it
counts sentences (LaTeX neutralised first, so `$\frac{a}{b}$` cannot inflate the
count), flags definition+exemple+exercice stacked in one message, flags a
solution marker appearing before the turn where revealing it is allowed, checks
that a "j'ai pas compris" turn actually re-words the previous explanation, and
checks that out-of-programme questions are declared as such.

```bash
python check_transcripts.py            # -> transcripts/REVIEW-NOTES.md
python check_transcripts.py --json     # also dump transcripts/audit.json
```

The mechanical verdicts (❌/✅) are there to *locate* the suspect turns fast; each
scenario also lists the points that need a human read (is the analogy good? did
it remember the student's mistake?). A ❌ can be a false positive — read the
extract before concluding. On **INCOMPLETE** transcripts no pedagogical rule can
be checked at all, since there is no model answer.

### Two subtle chat behaviours worth knowing

* **Follow-up expansion.** A bare *"j'ai pas compris"* carries no topic, so
  retrieving with it alone pulls in whatever chapter matches those words. When
  a turn looks like a follow-up, the previous student question is prepended to
  the search query (`build_retrieval_query` in `chat.py`). Without it that turn
  was grounded on unrelated chapters (scores 0.19–0.30); with it, on the right
  chapter (0.60).
* **History stays clean.** Only the *current* turn carries retrieved context;
  previous turns are replayed as plain student/assistant text, so a long
  conversation does not re-send stale passages.

### Offline plumbing check

`python test_gemini_client.py` checks the Gemini request mapping and response
parsing with a fake `generateContent` payload — no API key required.

`tools/mock_chat_server.py` is still there as a fake HTTP endpoint for the
retrieval → prompt path when you do not want to hit Gemini:

```bash
python tools/mock_chat_server.py --port 8765 --log /tmp/mock_requests.jsonl
```

**Its replies are synthetic — never use them to judge teaching quality.**

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
| `GEMINI_API_KEY` | *(empty)* | Google AI Studio key for the tutor |
| `GEMINI_MODEL_NAME` | `gemini-3.8-flash` | Gemini model id |
| `GEMINI_API_ENDPOINT` | `https://generativelanguage.googleapis.com/v1beta` | generateContent base URL |

---

## Layout

```
ingest.py              CLI: build the vector index
retrieve.py            CLI + reusable retrieve() function
test_retrieval.py      three sample queries, prints chunks + metadata
chat.py                CLI chat loop with the AI tutor
run_test_conversations.py   runs the 9 scripted conversations -> transcripts/
check_transcripts.py     audits transcripts/ against the prompt rules -> REVIEW-NOTES.md
test_gemini_client.py    mock-mode tests for the Gemini request/response mapping
requirements.txt
.env.example           copy to .env and fill in the placeholders
transcripts/           generated: 9 test conversations (.md + .json) + REVIEW-NOTES.md
rag/
  config.py            settings, placeholders, backend resolution
  parser.py            front-matter parsing + metadata normalisation
  chunker.py           semantic, LaTeX-safe chunking + integrity check
  embeddings.py        openai / sentence-transformers / tfidf / hashing backends
  vectorstore.py       Chroma wrapper, filters, provenance
  selection.py         score trimming, per-file cap, MMR diversity
  pipeline.py          parse -> chunk -> embed -> upsert
  prompts.py           THE SYSTEM PROMPT + grounding/prompt assembly
  llm.py               chat-completions client
  display.py           terminal rendering
tools/
  mock_chat_server.py  fake OpenAI-compatible endpoint for offline plumbing tests
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
| `[preflight] FAILED` / every transcript says **INCOMPLETE — ChatError** | the Gemini endpoint is unreachable or `GEMINI_API_KEY` is wrong — nothing to do with retrieval. Set `GEMINI_API_KEY` / `GEMINI_MODEL_NAME` / `GEMINI_API_ENDPOINT` in `.env`, then re-run `python run_test_conversations.py`; the transcripts are overwritten in place |
| Gemini `blockReason` / `finishReason=SAFETY` on an SVT question | default safety filters can flag biology/reproduction. The client already sends educational `safetySettings`; if it still blocks, try another `GEMINI_MODEL_NAME` or inspect the error |
| want to check the plumbing without a model | `python test_gemini_client.py` (mock Gemini request/response). Replies are synthetic: a **plumbing** check, never a teaching-quality check |
nthetic: a **plumbing** check, never a teaching-quality check |
