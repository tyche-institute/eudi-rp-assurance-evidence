#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


PINS = {
    "eudi-official": "db5442501ea06907e614377a20d802748e8bfddb",
    "waltid": "f773918a3ad226ba7c0908d58941f18a3b89591d",
}
INDEPENDENT_CONTROLS = {
    "independent-implementation-owner-run",
    "independent-third-party-run",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def expected_comparison(applicability: str, expected: str, observed: str) -> str:
    if applicability != "IN_SCOPE" or "NOT_RUN" in {expected, observed}:
        return "NOT_ASSESSED"
    return "MATCH" if expected == observed else "MISMATCH"


def observations_from_xml(path: Path) -> dict[str, tuple[str, str]]:
    root = ET.parse(path).getroot()
    counts = {key: int(root.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    if counts != {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}:
        fail(f"test XML did not record one completed test: {path.name}: {counts}")
    output = root.findtext("system-out") or ""
    observations: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        match = re.search(r"TYCHE_RETURN_OBSERVATION\|([^|]+)\|([^|]+)\|(.*)$", line)
        if match:
            observations[match.group(1)] = (match.group(2), match.group(3).strip())
    return observations


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--return-dir", type=Path, required=True)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--corpus", type=Path, required=True)
    return parser.parse_args()


def fail(message: str) -> None:
    raise SystemExit(f"RETURN VERIFICATION FAILED: {message}")


def main() -> int:
    args = parse_args()
    if not args.return_dir.is_dir():
        fail("return directory is missing")
    schema = json.loads(args.schema.read_text(encoding="utf-8"))
    corpus = json.loads(args.corpus.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    corpus_hash = sha256(args.corpus)
    case_map = {case["case_id"]: case for case in corpus["cases"]}
    if len(case_map) != 6:
        fail("expected six unique corpus cases")
    if any(case["mutation_axis"] == "disclosure-binding" for case in case_map.values()):
        fail("held disclosure-binding axis entered the return corpus")

    environment_path = args.return_dir / "environment.json"
    if not environment_path.is_file():
        fail("environment manifest is missing")
    environment = json.loads(environment_path.read_text(encoding="utf-8"))
    if any((
        environment.get("android_home_set"),
        environment.get("android_sdk_root_set"),
        environment.get("sdkmanager_present"),
    )):
        fail("return is not a no-Android execution")
    environment_hash = sha256(environment_path)

    receipt_paths = sorted((args.return_dir / "receipts").glob("*.json"))
    if len(receipt_paths) != 2:
        fail(f"expected two receipts, found {len(receipt_paths)}")
    adapters: set[str] = set()
    rows: list[dict[str, object]] = []
    controller_records: set[tuple[object, ...]] = set()
    for path in receipt_paths:
        receipt = json.loads(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(receipt), key=lambda error: list(error.path))
        if errors:
            fail(f"{path.name}: {errors[0].json_path}: {errors[0].message}")
        adapter = receipt["adapter_id"]
        if adapter not in PINS or receipt["source_commit"] != PINS[adapter]:
            fail(f"{path.name}: source pin mismatch")
        if receipt["record_status"] != "executed-observation":
            fail(f"{path.name}: receipt is not an executed observation")
        if receipt["input"]["corpus_sha256"] != corpus_hash:
            fail(f"{path.name}: corpus hash mismatch")
        if receipt["execution"]["environment_sha256"] != environment_hash:
            fail(f"{path.name}: environment hash mismatch")
        control = receipt["execution"]["control"]
        independent = receipt["execution"]["independent_of_tyche"]
        if independent != (control in INDEPENDENT_CONTROLS):
            fail(f"{path.name}: independence and controller class disagree")
        controller_records.add((
            control,
            independent,
            receipt["execution"]["controller_identifier"],
            receipt["execution"]["relationship_to_tyche"],
            receipt["execution"]["executed_at"],
        ))
        if len(receipt["observations"]) != 6:
            fail(f"{path.name}: expected six observations")
        xml_path = args.return_dir / "raw" / f"{adapter}-test.xml"
        if not xml_path.is_file():
            fail(f"{path.name}: raw test XML is missing")
        xml_observations = observations_from_xml(xml_path)
        if set(xml_observations) != set(case_map):
            fail(f"{path.name}: raw XML observation set is incomplete")
        observed_ids: set[str] = set()
        for observation in receipt["observations"]:
            case_id = observation["case_id"]
            if case_id not in case_map or case_id in observed_ids:
                fail(f"{path.name}: invalid or duplicate case {case_id}")
            case = case_map[case_id]
            if observation["object_sha256"] != case["presentation_sha256"]:
                fail(f"{path.name}: object hash mismatch for {case_id}")
            if observation["mutation_axis"] != case["mutation_axis"]:
                fail(f"{path.name}: mutation-axis mismatch for {case_id}")
            if observation["oracle_expected_verdict"] != case["profile_expected_verdict"]:
                fail(f"{path.name}: oracle mismatch for {case_id}")
            if (
                observation["observed_verdict"], observation["raw_reason"]
            ) != xml_observations[case_id]:
                fail(f"{path.name}: receipt/XML observation mismatch for {case_id}")
            comparison = expected_comparison(
                observation["applicability"],
                observation["oracle_expected_verdict"],
                observation["observed_verdict"],
            )
            if observation["comparison"] != comparison:
                fail(f"{path.name}: inconsistent comparison for {case_id}")
            observed_ids.add(case_id)
            rows.append({"adapter_id": adapter, **observation})
        for evidence in receipt["evidence_files"]:
            evidence_path = args.return_dir / evidence["path"]
            try:
                evidence_path.resolve().relative_to(args.return_dir.resolve())
            except ValueError:
                fail(f"{path.name}: evidence escapes the return directory")
            if not evidence_path.is_file() or sha256(evidence_path) != evidence["sha256"]:
                fail(f"{path.name}: evidence hash mismatch for {evidence['path']}")
        adapters.add(adapter)

    if adapters != set(PINS):
        fail(f"adapter set mismatch: {sorted(adapters)}")
    if len(controller_records) != 1:
        fail("receipts do not describe one consistent controller/run")
    if len(rows) != 12:
        fail(f"expected twelve observations, found {len(rows)}")

    summary_path = args.return_dir / "return-summary.json"
    if not summary_path.is_file():
        fail("return summary is missing")
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    mismatches = sum(row["comparison"] == "MISMATCH" for row in rows)
    independent = next(iter(controller_records))[1]
    if summary["corpus_sha256"] != corpus_hash:
        fail("summary corpus hash mismatch")
    if summary["entry_point_executions"] != 2 or summary["observations"] != 12:
        fail("summary execution counts are inconsistent")
    if summary["in_scope_mismatches"] != mismatches:
        fail("summary mismatch count is inconsistent")
    if summary["independent_run_package"] != independent:
        fail("summary independence claim is inconsistent")
    if summary["android_sdk_used"] is not False:
        fail("summary incorrectly claims Android use")
    expected_status = (
        "PASS_RETURN_COMPLETE_NO_IN_SCOPE_MISMATCH"
        if mismatches == 0
        else "PASS_RETURN_COMPLETE_WITH_IN_SCOPE_MISMATCH"
    )
    if summary["status"] != expected_status:
        fail("summary status is inconsistent")
    expected_receipts = [str(path.relative_to(args.return_dir)) for path in receipt_paths]
    if sorted(summary["receipts"]) != expected_receipts:
        fail("summary receipt inventory is inconsistent")
    summary_rows = sorted(
        summary["rows"], key=lambda row: (row["adapter_id"], row["case_id"])
    )
    receipt_rows = sorted(rows, key=lambda row: (row["adapter_id"], row["case_id"]))
    if summary_rows != receipt_rows:
        fail("summary observations differ from receipts")
    controller = next(iter(controller_records))
    if summary["controller"] != {
        "control": controller[0],
        "controller_identifier": controller[2],
        "relationship_to_tyche": controller[3],
    }:
        fail("summary controller differs from receipts")

    print(json.dumps({
        "status": "PASS_RETURN_PACKAGE_VALID",
        "return_status": expected_status,
        "adapters": sorted(adapters),
        "observations": len(rows),
        "in_scope_mismatches": mismatches,
        "independent_run_package": independent,
        "android_sdk_used": False,
        "corpus_sha256": corpus_hash,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
