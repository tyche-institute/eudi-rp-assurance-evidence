#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve().parent
SCHEMA = HERE / "lifecycle-receipt.schema.json"
CORPUS = HERE / "lifecycle-vectors.json"
RESULTS = HERE / "results.json"
CHECKSUMS = HERE / "SHA256SUMS"


def apply(record: dict, path: str, value) -> dict:
    result = copy.deepcopy(record)
    parts = [part for part in path.split("/") if part]
    target = result
    for part in parts[:-1]:
        target = target[part]
    target[parts[-1]] = value
    return result


def semantic_reason(record: dict) -> str | None:
    binding = record["rp_binding"]
    if binding["registered_party_id_sha256"] != binding["authenticated_party_id_sha256"]:
        return "RP_IDENTITY_NOT_REGISTRATION_BOUND"
    if binding["registered_contact_sha256"] != binding["selected_contact_sha256"]:
        return "CONTACT_NOT_REGISTRATION_BOUND"
    events = record["lifecycle"]["events"]
    if record["lifecycle"]["state"] != events[-1]["state"]:
        return "LIFECYCLE_STATE_UNSUPPORTED"
    for event in events:
        if event["state"] != "INITIATED" and "evidence_sha256" not in event:
            return "LIFECYCLE_EVIDENCE_MISSING"
    if record["lifecycle"]["state"] == "COMPLETED" and record["request_authentication"]["state"] != "PASSED":
        return "COMPLETION_WITHOUT_AUTHENTICATION"
    return None


def classify(record: dict, validator: Draft202012Validator) -> tuple[str, str]:
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        if errors[0].validator == "additionalProperties":
            return "REJECT", "SCHEMA_FORBIDDEN_FIELD"
        return "REJECT", f"SCHEMA_{errors[0].validator.upper()}"
    reason = semantic_reason(record)
    return ("REJECT", reason) if reason else ("ACCEPT", "PROFILE_VALID")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    baselines = {item["base_id"]: item["record"] for item in corpus["baselines"]}
    observations = []

    for base_id, record in baselines.items():
        verdict, reason = classify(record, validator)
        if (verdict, reason) != ("ACCEPT", "PROFILE_VALID"):
            raise SystemExit(f"{base_id}: baseline rejected as {reason}")
        observations.append({"case_id": base_id, "verdict": verdict, "reason": reason})

    for case in corpus["cases"]:
        mutated = apply(baselines[case["base_id"]], case["path"], case["value"])
        verdict, reason = classify(mutated, validator)
        if verdict != case["expected_verdict"] or reason != case["expected_reason"]:
            raise SystemExit(f"{case['case_id']}: expected {case['expected_verdict']}/{case['expected_reason']}, got {verdict}/{reason}")
        observations.append({"case_id": case["case_id"], "verdict": verdict, "reason": reason})

    result = {
        "schema_version": corpus["schema_version"],
        "corpus_id": corpus["corpus_id"],
        "corpus_sha256": hashlib.sha256(CORPUS.read_bytes()).hexdigest(),
        "baseline_accepts": 2,
        "negative_rejects": 3,
        "observations": observations,
        "execution_control": "tyche-research-oracle-only",
        "external_implementation_executions": 0,
        "claim_boundary": "Synthetic lifecycle-profile validation; not a wallet or RP implementation result, legal finding, or ARF conformance test."
    }
    result_text = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not RESULTS.is_file() or RESULTS.read_text(encoding="utf-8") != result_text:
            raise SystemExit("results.json is stale")
        print("ARF L/M lifecycle vector deterministic rebuild PASS")
        return 0

    RESULTS.write_text(result_text, encoding="utf-8")
    checksum_names = (
        "README.md",
        "lifecycle-receipt.schema.json",
        "lifecycle-vectors.json",
        "results.json",
        "source-pins.json",
        "upstream-candidate-lm.md",
        "verify_vectors.py",
    )
    CHECKSUMS.write_text("".join(
        f"{hashlib.sha256((HERE / name).read_bytes()).hexdigest()}  {name}\n"
        for name in checksum_names
    ), encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
