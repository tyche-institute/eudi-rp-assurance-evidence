#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "common-presentation-corpus" / "corpus.json"
SCHEMA = ROOT / "decision-provenance-receipt.schema.json"
RECEIPTS = ROOT / "results" / "common-presentation-provenance"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    corpus_sha = sha256(CORPUS)
    negative = next(c for c in corpus["cases"] if c["case_id"] == "RP_WS_SM_IssuerAuthentication_001")
    receipts = sorted(RECEIPTS.glob("*.json"))
    if len(receipts) != 3:
        raise SystemExit(f"expected three receipts, found {len(receipts)}")
    adapters: set[str] = set()
    for path in receipts:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(receipt), key=lambda error: list(error.path))
        if errors:
            raise SystemExit(f"{path.name}: {errors[0].message}")
        if receipt["input"]["corpus_sha256"] != corpus_sha:
            raise SystemExit(f"{path.name}: corpus hash mismatch")
        if receipt["input"]["presentation_sha256"] != negative["presentation_sha256"]:
            raise SystemExit(f"{path.name}: presentation hash mismatch")
        for evidence in receipt["evidence_files"]:
            evidence_path = ROOT / evidence["path"]
            if not evidence_path.is_file() or sha256(evidence_path) != evidence["sha256"]:
                raise SystemExit(f"{path.name}: invalid evidence {evidence['path']}")
        adapters.add(receipt["adapter_id"])
    expected = {"eudi-official", "multipaz", "waltid"}
    if adapters != expected:
        raise SystemExit(f"adapter set mismatch: {sorted(adapters)}")
    print(json.dumps({
        "status": "PASS", "corpus_sha256": corpus_sha,
        "presentation_sha256": negative["presentation_sha256"],
        "receipts": [path.name for path in receipts],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
