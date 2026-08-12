#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
SCHEMA = PACKET / "receipt-schema-v1.1-candidate" / "decision-provenance-receipt-1.1.schema.json"
CORPUS = HERE / "corpus.json"
RESULTS = HERE / "results"
SUMMARY = RESULTS / "decision-scope-summary.json"
RECEIPTS = RESULTS / "receipts"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    if any(case["mutation_axis"] == "disclosure-binding" for case in corpus["cases"]):
        raise SystemExit("held disclosure-binding axis entered the corpus")
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    receipts = sorted(RECEIPTS.glob("*.json"))
    if len(receipts) != 3:
        raise SystemExit(f"expected three receipts, found {len(receipts)}")
    adapters: set[str] = set()
    rows: list[dict[str, str]] = []
    for path in receipts:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(receipt), key=lambda error: list(error.path))
        if errors:
            raise SystemExit(f"{path.name}: {errors[0].json_path}: {errors[0].message}")
        if receipt["record_status"] != "executed-observation":
            raise SystemExit(f"{path.name}: receipt is not an execution")
        if receipt["execution"]["independent_of_tyche"] is not False:
            raise SystemExit(f"{path.name}: execution-control claim is inconsistent")
        if receipt["input"]["corpus_sha256"] != sha256(CORPUS):
            raise SystemExit(f"{path.name}: corpus hash mismatch")
        for evidence in receipt["evidence_files"]:
            evidence_path = HERE / evidence["path"]
            if not evidence_path.is_file() or sha256(evidence_path) != evidence["sha256"]:
                raise SystemExit(f"{path.name}: invalid evidence {evidence['path']}")
        adapters.add(receipt["adapter_id"])
        rows.extend({"adapter_id": receipt["adapter_id"], **item} for item in receipt["observations"])
    if adapters != {"eudi-official", "multipaz", "waltid"}:
        raise SystemExit(f"adapter set mismatch: {sorted(adapters)}")
    if len(rows) != 18:
        raise SystemExit(f"expected 18 observations, found {len(rows)}")

    by_key = {(row["adapter_id"], row["case_id"]): row for row in rows}
    negative_ids = {case["case_id"] for case in corpus["cases"] if case["profile_expected_verdict"] == "REJECT"}
    for adapter in ("eudi-official", "multipaz"):
        if by_key[(adapter, "SCOPE_BASELINE_001")]["observed_verdict"] != "ACCEPT":
            raise SystemExit(f"{adapter}: baseline not accepted")
        if any(by_key[(adapter, case_id)]["observed_verdict"] != "REJECT" for case_id in negative_ids):
            raise SystemExit(f"{adapter}: negative observation set changed")
    if by_key[("waltid", "SCOPE_ISSUER_SIGNATURE_INVALID_001")]["observed_verdict"] != "REJECT":
        raise SystemExit("waltid: issuer-signature observation changed")
    for case_id in negative_ids - {"SCOPE_ISSUER_SIGNATURE_INVALID_001"}:
        row = by_key[("waltid", case_id)]
        if row["observed_verdict"] != "ACCEPT" or row["comparison"] != "NOT_ASSESSED":
            raise SystemExit(f"waltid: out-of-scope observation changed for {case_id}")

    applicability = Counter(row["applicability"] for row in rows)
    expected_applicability = {
        "IN_SCOPE": 11,
        "CALLER_SUPPLIED_POLICY": 3,
        "NOT_REPRESENTABLE_AT_ENTRY_POINT": 4,
    }
    if dict(applicability) != expected_applicability:
        raise SystemExit(f"applicability matrix changed: {dict(applicability)}")
    if any(row["comparison"] == "MISMATCH" for row in rows):
        raise SystemExit("an in-scope oracle disagreement requires review")

    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    if summary["observations"] != 18 or summary["independent_executions"] != 0:
        raise SystemExit("summary counts are inconsistent")
    print(json.dumps({
        "status": "PASS_DECISION_SCOPE_CENSUS",
        "corpus_sha256": sha256(CORPUS),
        "observations": 18,
        "in_scope": applicability["IN_SCOPE"],
        "caller_supplied_policy": applicability["CALLER_SUPPLIED_POLICY"],
        "not_representable_at_entry_point": applicability["NOT_REPRESENTABLE_AT_ENTRY_POINT"],
        "independent_executions": 0,
        "disclosure_binding_excluded": True,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
