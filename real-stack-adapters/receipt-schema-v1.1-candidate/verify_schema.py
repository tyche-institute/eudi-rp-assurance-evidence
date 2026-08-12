#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parent
SCHEMA = ROOT / "decision-provenance-receipt-1.1.schema.json"
FIXTURES = ROOT / "fixtures"


def expected_comparison(expected: str, observed: str) -> str:
    if "NOT_RUN" in {expected, observed}:
        return "NOT_ASSESSED"
    return "MATCH" if expected == observed else "MISMATCH"


def main() -> int:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    records: list[dict[str, object]] = []

    for path in sorted(FIXTURES.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
        if errors:
            raise SystemExit(f"{path.name}: {errors[0].json_path}: {errors[0].message}")
        if record["record_status"] != "schema-example-not-execution":
            raise SystemExit(f"{path.name}: fixture must not claim execution")
        for observation in record["observations"]:
            comparison = (
                expected_comparison(
                    observation["oracle_expected_verdict"], observation["observed_verdict"]
                )
                if observation["applicability"] == "IN_SCOPE"
                else "NOT_ASSESSED"
            )
            if observation["comparison"] != comparison:
                raise SystemExit(f"{path.name}: inconsistent oracle comparison")
        records.append(record)

    independent = next(
        record for record in records if record["execution"]["independent_of_tyche"] is True
    )
    if independent["execution"]["control"] != "independent-implementation-owner-run":
        raise SystemExit("independent fixture has the wrong controller class")
    if independent["observations"][0]["comparison"] != "MISMATCH":
        raise SystemExit("independent disagreement is not representable")

    print(json.dumps({
        "status": "PASS_RECEIPT_SCHEMA_1_1_CANDIDATE",
        "fixtures": len(records),
        "independent_control_representable": True,
        "oracle_disagreement_representable": True,
        "published_schema_1_0_modified": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
