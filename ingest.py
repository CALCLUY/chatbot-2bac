#!/usr/bin/env python3
"""Build the vector index from the ``data-2bac-sma`` corpus.

Pipeline: parse -> chunk -> embed -> upsert into Chroma.

Typical use::

    # 1. get the corpus
    git clone https://github.com/CALCLUY/data-2bac-sma.git data/data-2bac-sma

    # 2. fill in EMBEDDING_MODEL / EMBEDDING_API_KEY in .env (optional; without
    #    them an offline lexical embedder is used so you can still test)

    # 3. build the index
    python ingest.py

Useful flags::

    python ingest.py --stats-only        # chunk the corpus, print stats, write nothing
    python ingest.py --limit 20          # index the first 20 files only (quick smoke test)
    python ingest.py --no-reset          # add to the existing collection instead of rebuilding
"""

from __future__ import annotations

import argparse
import collections
import statistics
from pathlib import Path

from rag.chunker import validate_latex_integrity
from rag.config import DEFAULT_CONFIG, Config
from rag.parser import iter_corpus_files
from rag.pipeline import build_chunks, run_ingestion


def _print_corpus_stats(config: Config) -> None:
    root = config.resolve_data_dir()
    files = iter_corpus_files(root)
    try:
        by_subject = collections.Counter(f.relative_to(root).parts[0] for f in files)
    except ValueError:                       # pragma: no cover - defensive
        by_subject = collections.Counter(f.parts[0] for f in files)
    print(f"[stats] corpus root : {config.resolve_data_dir()}")
    print(f"[stats] .txt files  : {len(files)}")
    for subject, count in by_subject.most_common():
        print(f"[stats]   {subject:<18} {count}")


def _print_chunk_stats(chunks) -> None:
    sizes = [len(c.content) for c in chunks]
    print(f"[stats] chunks      : {len(chunks)}")
    print(f"[stats]   min/median/mean/max chars: {min(sizes)} / "
          f"{int(statistics.median(sizes))} / {int(statistics.mean(sizes))} / {max(sizes)}")
    print(f"[stats]   with LaTeX: {sum(1 for c in chunks if c.metadata['has_math'])}")
    print(f"[stats]   with figures: {sum(1 for c in chunks if c.metadata['has_formula_image'])}")

    for field in ("matiere", "type", "block_type"):
        counter = collections.Counter(c.metadata.get(field, "") or "(none)" for c in chunks)
        top = ", ".join(f"{k}={v}" for k, v in counter.most_common(6))
        print(f"[stats]   by {field:<11}: {top}")

    violations = validate_latex_integrity(chunks)
    status = "OK" if not violations else f"{len(violations)} VIOLATIONS"
    print(f"[stats] LaTeX integrity: {status}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Build the 2bac RAG vector index.")
    parser.add_argument("--data-dir", type=Path, default=None, help="path to the 2bac-data-sma corpus")
    parser.add_argument("--chroma-dir", type=Path, default=None, help="where to store the Chroma index")
    parser.add_argument("--collection", default=None, help="Chroma collection name")
    parser.add_argument("--limit", type=int, default=None, help="only index the first N files")
    parser.add_argument("--reset", dest="reset", action="store_true", default=True,
                        help="rebuild the collection from scratch (default)")
    parser.add_argument("--no-reset", dest="reset", action="store_false",
                        help="append to the existing collection")
    parser.add_argument("--stats-only", action="store_true",
                        help="parse + chunk + report, but do not embed or write")
    parser.add_argument("--no-dump", dest="dump", action="store_false", default=True,
                        help="skip the chunks.jsonl dump")
    args = parser.parse_args(argv)

    # Start from the defaults (which already read .env / environment) and
    # apply only what the command line overrides.
    config = DEFAULT_CONFIG
    if args.data_dir:
        config.data_dir = args.data_dir
    if args.chroma_dir:
        config.chroma_dir = args.chroma_dir
    if args.collection:
        config.collection_name = args.collection

    data_dir = config.resolve_data_dir()
    if not data_dir.is_dir():
        print(f"[error] corpus not found at {data_dir}\n"
              "Clone it with:\n"
              "  git clone https://github.com/CALCLUY/data-2bac-sma.git data/data-2bac-sma")
        return 1

    _print_corpus_stats(config)

    if args.stats_only:
        chunks = build_chunks(config, limit=args.limit)
        _print_chunk_stats(chunks)
        return 0

    stats = run_ingestion(config, reset=args.reset, limit=args.limit, dump=args.dump)
    print("\n[done] " + stats.render())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
