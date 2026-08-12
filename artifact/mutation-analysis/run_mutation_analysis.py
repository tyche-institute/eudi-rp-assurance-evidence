#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path


HERE = Path(__file__).resolve().parent
ARTIFACT = HERE.parent
CORPUS = ARTIFACT / "corpus" / "vectors.json"
OUTPUT_JSON = HERE / "mutation-results.json"
OUTPUT_CSV = HERE / "kill-matrix.csv"

IMPLEMENTATIONS = {
    "python": {
        "source": ARTIFACT / "verifiers" / "python" / "verifier.py",
        "suffix": ".py",
        "command": lambda path: ["python3", str(path)],
        "pattern": re.compile(
            r'(?m)^(?P<indent>    )if (?P<condition>.+):\n'
            r'(?P=indent)    return "(?P<reason>R_[A-Z_]+)"$'
        ),
        "replacement": lambda match: (
            f'{match.group("indent")}if False:  # MUTANT {match.group("reason")}\n'
            f'{match.group("indent")}    return "{match.group("reason")}"'
        ),
    },
    "javascript": {
        "source": ARTIFACT / "verifiers" / "javascript" / "verifier.mjs",
        "suffix": ".mjs",
        "command": lambda path: ["node", str(path)],
        "pattern": re.compile(
            r'(?m)^(?P<indent>    )\[(?P<condition>.+), "(?P<reason>R_[A-Z_]+)"\],$'
        ),
        "replacement": lambda match: (
            f'{match.group("indent")}[false, "{match.group("reason")}"], // MUTANT'
        ),
    },
    "jq": {
        "source": ARTIFACT / "verifiers" / "jq" / "verifier.jq",
        "suffix": ".jq",
        "command": lambda path: ["jq", "-c", "-f", str(path)],
        "pattern": re.compile(
            r'(?m)^(?P<indent>  )(?P<branch>if|elif) (?P<condition>.+) then '
            r'"(?P<reason>R_[A-Z_]+)"$'
        ),
        "replacement": lambda match: (
            f'{match.group("indent")}{match.group("branch")} false then '
            f'"{match.group("reason")}"'
        ),
    },
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], corpus_bytes: bytes) -> tuple[int, dict | None, str]:
    process = subprocess.run(
        command,
        input=corpus_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if process.returncode:
        return process.returncode, None, process.stderr.decode("utf-8", errors="replace")
    try:
        return 0, json.loads(process.stdout), process.stderr.decode("utf-8", errors="replace")
    except json.JSONDecodeError as error:
        return 0, None, f"invalid JSON output: {error}"


def result_map(output: dict) -> dict[str, tuple[str, str]]:
    return {item["id"]: (item["verdict"], item["reason"]) for item in output["results"]}


def mutate_one(source: str, pattern: re.Pattern, replacement, target_reason: str) -> str:
    matches = [match for match in pattern.finditer(source) if match.group("reason") == target_reason]
    if len(matches) != 1:
        raise RuntimeError(f"expected one source rule for {target_reason}, found {len(matches)}")
    match = matches[0]
    return source[:match.start()] + replacement(match) + source[match.end():]


def main() -> int:
    corpus_bytes = CORPUS.read_bytes()
    corpus = json.loads(corpus_bytes)
    oracle = {
        vector["id"]: (vector["expected_verdict"], vector["expected_reason"])
        for vector in corpus["vectors"]
    }
    rejection_reasons = sorted({reason for _, reason in oracle.values() if reason.startswith("R_")})
    if len(rejection_reasons) != 17:
        raise SystemExit(f"expected 17 rejection rules, found {len(rejection_reasons)}")

    rows: list[dict[str, object]] = []
    source_hashes: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="tyche-oracle-mutation-") as temp_name:
        temp_dir = Path(temp_name)
        for implementation, config in IMPLEMENTATIONS.items():
            source_path: Path = config["source"]
            source = source_path.read_text(encoding="utf-8")
            source_hashes[implementation] = sha256(source_path)
            discovered = sorted(match.group("reason") for match in config["pattern"].finditer(source))
            if discovered != rejection_reasons:
                raise SystemExit(
                    f"{implementation}: source rule set differs from corpus: {discovered}"
                )

            original_code, original_output, original_error = run(config["command"](source_path), corpus_bytes)
            if original_code or original_output is None or result_map(original_output) != oracle:
                raise SystemExit(
                    f"{implementation}: original implementation does not match the frozen oracle: "
                    f"{original_error}"
                )

            for target_reason in rejection_reasons:
                mutant_source = mutate_one(
                    source, config["pattern"], config["replacement"], target_reason
                )
                mutant_path = temp_dir / f"{implementation}-{target_reason}{config['suffix']}"
                mutant_path.write_text(mutant_source, encoding="utf-8")
                code, output, error = run(config["command"](mutant_path), corpus_bytes)
                differences: list[str] = []
                status = "INVALID"
                if code == 0 and output is not None:
                    actual = result_map(output)
                    if set(actual) != set(oracle):
                        error = "mutant returned a different vector set"
                    else:
                        differences = sorted(
                            vector_id for vector_id in oracle if actual[vector_id] != oracle[vector_id]
                        )
                        status = "KILLED" if differences else "SURVIVED"
                rows.append({
                    "implementation": implementation,
                    "mutant_id": f"{implementation}:{target_reason}:condition-false",
                    "target_reason": target_reason,
                    "operator": "RULE_CONDITION_FALSE",
                    "status": status,
                    "changed_outcome_count": len(differences),
                    "killed_by": differences,
                    "error": error.strip() if status == "INVALID" else "",
                })

    valid = [row for row in rows if row["status"] != "INVALID"]
    killed = [row for row in valid if row["status"] == "KILLED"]
    survived = [row for row in valid if row["status"] == "SURVIVED"]
    invalid = [row for row in rows if row["status"] == "INVALID"]
    per_implementation = {}
    for implementation in IMPLEMENTATIONS:
        subset = [row for row in rows if row["implementation"] == implementation]
        subset_valid = [row for row in subset if row["status"] != "INVALID"]
        subset_killed = [row for row in subset_valid if row["status"] == "KILLED"]
        per_implementation[implementation] = {
            "generated": len(subset),
            "valid": len(subset_valid),
            "killed": len(subset_killed),
            "survived": sum(row["status"] == "SURVIVED" for row in subset),
            "invalid": sum(row["status"] == "INVALID" for row in subset),
            "mutation_score": len(subset_killed) / len(subset_valid) if subset_valid else None,
        }
    result = {
        "schema_version": "0.1.0-research",
        "operator": "RULE_CONDITION_FALSE",
        "corpus_sha256": sha256(CORPUS),
        "source_sha256": source_hashes,
        "vectors": len(oracle),
        "rules": len(rejection_reasons),
        "generated_mutants": len(rows),
        "valid_mutants": len(valid),
        "killed_mutants": len(killed),
        "surviving_mutants": len(survived),
        "invalid_mutants": len(invalid),
        "mutation_score": len(killed) / len(valid) if valid else None,
        "per_implementation": per_implementation,
        "rows": rows,
        "claim_boundary": (
            "Sensitivity to one declared rule-omission operator in three study-authored paths. "
            "Not completeness, independence, real-stack behavior or conformance evidence."
        ),
    }
    OUTPUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "implementation", "mutant_id", "target_reason", "operator", "status",
                "changed_outcome_count", "killed_by", "error",
            ],
        )
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "killed_by": ";".join(row["killed_by"])})
    print(json.dumps({key: result[key] for key in (
        "generated_mutants", "valid_mutants", "killed_mutants", "surviving_mutants",
        "invalid_mutants", "mutation_score",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
