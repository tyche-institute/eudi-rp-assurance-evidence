#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_verifier(verifier: Path, return_dir: Path, schema: Path, corpus: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            "python3", str(verifier),
            "--return-dir", str(return_dir),
            "--schema", str(schema),
            "--corpus", str(corpus),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("return_dir", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    kit = Path(__file__).resolve().parent
    verifier = kit / "container" / "verify_return.py"
    schema = kit.parent / "receipt-schema-v1.1-candidate" / "decision-provenance-receipt-1.1.schema.json"
    corpus = kit.parent / "decision-scope-census" / "corpus.json"

    baseline = run_verifier(verifier, args.return_dir, schema, corpus)
    if baseline.returncode:
        raise SystemExit(f"baseline return did not validate:\n{baseline.stdout}")

    with tempfile.TemporaryDirectory(prefix="tyche-return-verifier-selftest-") as temp_name:
        temp = Path(temp_name)
        tampered = temp / "tampered"
        shutil.copytree(args.return_dir, tampered)
        test_log = tampered / "raw" / "eudi-official-test.log"
        test_log.write_bytes(test_log.read_bytes() + b"\nTAMPER-SELF-TEST\n")
        rejected = run_verifier(verifier, tampered, schema, corpus)
        if rejected.returncode == 0 or "evidence hash mismatch" not in rejected.stdout:
            raise SystemExit("tampered evidence was not rejected fail-closed")

        disagreement = temp / "synthetic-disagreement"
        shutil.copytree(args.return_dir, disagreement)
        xml_path = disagreement / "raw" / "eudi-official-test.xml"
        old_marker = "TYCHE_RETURN_OBSERVATION|SCOPE_ISSUER_SIGNATURE_INVALID_001|REJECT|ContainsInvalidJwt"
        new_marker = "TYCHE_RETURN_OBSERVATION|SCOPE_ISSUER_SIGNATURE_INVALID_001|ACCEPT|SYNTHETIC_SELF_TEST_ACCEPT"
        xml_text = xml_path.read_text(encoding="utf-8")
        if xml_text.count(old_marker) != 1:
            raise SystemExit("expected XML marker not found exactly once")
        xml_path.write_text(xml_text.replace(old_marker, new_marker), encoding="utf-8")

        receipt_path = disagreement / "receipts" / "eudi-official-receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        target = next(
            item for item in receipt["observations"]
            if item["case_id"] == "SCOPE_ISSUER_SIGNATURE_INVALID_001"
        )
        target.update({
            "observed_verdict": "ACCEPT",
            "comparison": "MISMATCH",
            "raw_reason": "SYNTHETIC_SELF_TEST_ACCEPT",
            "normalized_reason": "NONE",
        })
        xml_evidence = next(
            item for item in receipt["evidence_files"]
            if item["path"] == "raw/eudi-official-test.xml"
        )
        xml_evidence["sha256"] = sha256(xml_path)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        summary_path = disagreement / "return-summary.json"
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        summary_target = next(
            item for item in summary["rows"]
            if item["adapter_id"] == "eudi-official"
            and item["case_id"] == "SCOPE_ISSUER_SIGNATURE_INVALID_001"
        )
        summary_target.update({
            "observed_verdict": "ACCEPT",
            "comparison": "MISMATCH",
            "raw_reason": "SYNTHETIC_SELF_TEST_ACCEPT",
            "normalized_reason": "NONE",
        })
        summary["in_scope_mismatches"] = 1
        summary["status"] = "PASS_RETURN_COMPLETE_WITH_IN_SCOPE_MISMATCH"
        summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        accepted = run_verifier(verifier, disagreement, schema, corpus)
        if accepted.returncode or "PASS_RETURN_COMPLETE_WITH_IN_SCOPE_MISMATCH" not in accepted.stdout:
            raise SystemExit(f"evidence-consistent disagreement was not accepted:\n{accepted.stdout}")

    print(json.dumps({
        "status": "PASS_VERIFIER_SEMANTICS",
        "baseline_return_valid": True,
        "tampered_evidence_rejected": True,
        "evidence_consistent_oracle_disagreement_accepted": True,
        "synthetic_self_test_retained": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
