#!/usr/bin/env python3
"""Sanity-check retrieval quality against the indexed corpus.

Runs three sample queries (one per subject: Mathématiques, Physique-Chimie,
SVT), plus a filtered query that shows metadata filtering at work, and prints
the retrieved chunks together with their source metadata.

    python test_retrieval.py            # pretty output
    python test_retrieval.py --brief    # scores + source only (quick scan)
    python test_retrieval.py --json     # machine-readable

Run `python ingest.py` first. If the index is empty the script says so instead
of failing cryptically.
"""

from __future__ import annotations

import argparse
import json
import sys
import time

from rag.display import _rule, print_results
from retrieve import Retriever

# --------------------------------------------------------------------------- #
# The three probe queries -- one per subject, phrased the way a 2bac student
# would actually ask them.
# --------------------------------------------------------------------------- #
SAMPLE_QUERIES = [
    {
        "query": "Comment calculer la limite d'une fonction en un point ?",
        "filters": {"matiere": "Mathématiques"},
        "why": "Maths: should surface the Chapitre 1 'Limites et continuité' course material.",
    },
    {
        "query": "Quelle est la différence entre une onde transversale et une onde longitudinale ?",
        "filters": {"matiere": "Physique-Chimie"},
        "why": "Physique: should surface the 'Ondes mécaniques progressives' lesson (Semestre 1).",
    },
    {
        "query": "Quelles sont les étapes de la méiose et la réduction chromatique ?",
        "filters": {"matiere": "SVT"},
        "why": "SVT: should surface the 'Transfert de l'information génétique' meiosis course.",
    },
]

FILTERED_QUERY = {
    "query": "équation chimique et taux d'avancement final d'une réaction acide-base",
    "filters": {"matiere": "Physique-Chimie", "chapitre": "Semestre 1"},
    "why": "Filtered: every hit must come from the Physique-Chimie 'Semestre 1' section.",
}


def _brief(query: str, hits) -> None:
    print(_rule("═"))
    print(f"QUERY: {query}")
    print(_rule("═"))
    for rank, hit in enumerate(hits, start=1):
        meta = hit.metadata
        location = " | ".join(
            b for b in (meta.get("matiere"), meta.get("chapitre") or meta.get("semestre"),
                        meta.get("type")) if b
        )
        preview = " ".join(hit.content.split())[:90]
        print(f"  {rank}. {hit.score:.4f}  {location}")
        print(f"     {meta.get('file_path')}  [{meta.get('block_type')}]")
        print(f"     {preview}…")
    print()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Run sample queries against the 2bac index.")
    parser.add_argument("--top-k", type=int, default=3, help="results per query (default 3)")
    parser.add_argument("--max-chars", type=int, default=420, help="preview length per chunk")
    parser.add_argument("--brief", action="store_true", help="compact output")
    parser.add_argument("--json", dest="as_json", action="store_true", help="emit JSON")
    args = parser.parse_args(argv)

    # In --json mode stdout must contain nothing but the JSON document.
    retriever = Retriever(verbose=not args.as_json)
    if retriever.store.count() == 0:
        if args.as_json:
            print("[]")
        else:
            print("The vector index is empty -- nothing to retrieve.\n"
                  "Build it first:\n"
                  "    python ingest.py")
        return 1

    if not args.as_json:
        print(f"Index: {retriever.store.count()} vectors in collection "
              f"{retriever.store.name!r} at {retriever.config.chroma_dir}\n")

    cases = SAMPLE_QUERIES + [FILTERED_QUERY]
    payload = []
    failures = 0

    for case in cases:
        started = time.time()
        hits = retriever.retrieve(case["query"], top_k=args.top_k, **case["filters"])
        elapsed = time.time() - started

        if args.as_json:
            payload.append({
                "query": case["query"],
                "filters": case["filters"],
                "elapsed_s": round(elapsed, 3),
                "results": [
                    {"rank": i, "chunk_id": h.chunk_id, "score": round(h.score, 6),
                     "content": h.content, "metadata": h.metadata}
                    for i, h in enumerate(hits, start=1)
                ],
            })
            continue

        print(f"\n### expectation: {case['why']}")
        if args.brief:
            _brief(case["query"], hits)
        else:
            print_results(case["query"], hits, filters=case["filters"], max_chars=args.max_chars)
        print(f"  ({len(hits)} results in {elapsed:.2f}s)")

        # --- automated sanity checks -------------------------------------- #
        if not hits:
            print("  [FAIL] no results returned")
            failures += 1
            continue

        problems = []
        for key, expected in case["filters"].items():
            for hit in hits:
                if key == "chapitre":
                    ok = expected in (hit.metadata.get("chapitre"), hit.metadata.get("semestre"))
                else:
                    ok = hit.metadata.get(key) == expected
                if not ok:
                    problems.append(
                        f"{key} filter leak: got {hit.metadata.get(key)!r} / "
                        f"{hit.metadata.get('semestre')!r}, expected {expected!r}"
                    )
                    break

        scores = [h.score for h in hits]
        if any(s < 0 for s in scores):
            problems.append(f"negative similarity score: {min(scores):.4f}")
        if scores and scores != sorted(scores, reverse=True):
            problems.append("results are not ordered best-first")

        if problems:
            failures += 1
            for problem in problems:
                print(f"  [FAIL] {problem}")
        else:
            print("  [OK] filters respected, scores ordered")

    if args.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print()
        print(_rule("═"))
        if failures:
            print(f"{failures}/{len(cases)} query/queries had problems -- see [FAIL] lines above.")
        else:
            print(f"All {len(cases)} sample queries returned well-formed, correctly filtered results.")
        print(_rule("═"))

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
