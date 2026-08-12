#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parent
RESULTS = HERE / "mutation-results.json"
MATRIX = HERE / "kill-matrix.csv"
CORPUS = ARTIFACT / "corpus" / "vectors.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    result = json.loads(RESULTS.read_text(encoding="utf-8"))
    if result["corpus_sha256"] != sha256(CORPUS):
        raise SystemExit("corpus hash mismatch")
    sources = {
        "python": ARTIFACT / "verifiers/python/verifier.py",
        "javascript": ARTIFACT / "verifiers/javascript/verifier.mjs",
        "jq": ARTIFACT / "verifiers/jq/verifier.jq",
    }
    if result["source_sha256"] != {name: sha256(path) for name, path in sources.items()}:
        raise SystemExit("verifier source hash mismatch")
    if result["operator"] != "RULE_CONDITION_FALSE" or result["rules"] != 17:
        raise SystemExit("mutation design changed")
    if result["generated_mutants"] != 51 or len(result["rows"]) != 51:
        raise SystemExit("mutant inventory is incomplete")
    counts = {
        status: sum(row["status"] == status for row in result["rows"])
        for status in ("KILLED", "SURVIVED", "INVALID")
    }
    if result["killed_mutants"] != counts["KILLED"]:
        raise SystemExit("killed count mismatch")
    if result["surviving_mutants"] != counts["SURVIVED"]:
        raise SystemExit("survivor count mismatch")
    if result["invalid_mutants"] != counts["INVALID"]:
        raise SystemExit("invalid count mismatch")
    if result["valid_mutants"] != counts["KILLED"] + counts["SURVIVED"]:
        raise SystemExit("valid denominator mismatch")
    expected_score = counts["KILLED"] / result["valid_mutants"]
    if result["mutation_score"] != expected_score:
        raise SystemExit("mutation score mismatch")
    with MATRIX.open(encoding="utf-8", newline="") as stream:
        csv_rows = list(csv.DictReader(stream))
    if len(csv_rows) != 51:
        raise SystemExit("CSV row count mismatch")
    print(json.dumps({
        "status": "PASS_MUTATION_ANALYSIS",
        "generated_mutants": result["generated_mutants"],
        "valid_mutants": result["valid_mutants"],
        "killed_mutants": result["killed_mutants"],
        "surviving_mutants": result["surviving_mutants"],
        "invalid_mutants": result["invalid_mutants"],
        "mutation_score": result["mutation_score"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
