#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REFERENCE_RETURN = (
    ROOT
    / "real-stack-adapters/independent-reproducer-v0.2-candidate/results"
    / "tyche-controlled-reference-2026-08-12"
)


def run(*command: str, cwd: Path = ROOT) -> str:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise SystemExit(
            f"FAIL: {' '.join(command)}\n{result.stdout}\n{result.stderr}"
        )
    output = result.stdout.strip()
    if output:
        print(output)
    return output


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_manifest() -> set[Path]:
    manifest = ROOT / "RELEASE-SHA256SUMS"
    listed: set[Path] = set()
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        path = ROOT / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(f"FAIL: release hash mismatch: {relative}")
        listed.add(Path(relative))
    actual = {
        path.relative_to(ROOT)
        for path in ROOT.rglob("*")
        if path.is_file()
        and path.name != "RELEASE-SHA256SUMS"
        and ".git" not in path.relative_to(ROOT).parts
        and "__pycache__" not in path.relative_to(ROOT).parts
    }
    if listed != actual:
        raise SystemExit(
            "FAIL: release manifest set mismatch: "
            f"missing={sorted(actual-listed)}, extra={sorted(listed-actual)}"
        )
    return actual


def verify_nested_manifest(directory: Path, manifest_name: str = "SHA256SUMS") -> None:
    manifest = directory / manifest_name
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, relative = line.split("  ", 1)
        path = directory / relative
        if not path.is_file() or sha256(path) != digest:
            raise SystemExit(
                f"FAIL: nested hash mismatch: {directory.relative_to(ROOT)}/{relative}"
            )


def verify_privacy(actual: set[Path]) -> None:
    email = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
    forbidden = (
        "/home/",
        "/srv/",
        "contact-ledger",
        "fieldwork-log",
        "professional_email",
        "eudiw-survey.tyche.institute",
        "dfcc915f-a6ff-404c-9605-a34ef0809b77",
        "7937934",
    )
    scanner_sources = {
        Path("verify_release.py"),
        Path("assurance-graph/verify_graph.py"),
        Path("engagement/rp-programme-travel-mobility/build.sh"),
    }
    no_email_scan_suffixes = {".xml"}
    for relative in sorted(actual):
        path = ROOT / relative
        if path.is_symlink():
            raise SystemExit(f"FAIL: symlink in release: {relative}")
        if path.stat().st_size > 2_000_000:
            raise SystemExit(f"FAIL: unexpectedly large release file: {relative}")
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if relative not in scanner_sources:
            lowered = content.lower()
            if any(term in lowered for term in forbidden):
                raise SystemExit(f"FAIL: privacy scan: {relative}")
            if path.suffix.lower() not in no_email_scan_suffixes and email.search(content):
                raise SystemExit(f"FAIL: privacy email scan: {relative}")


def main() -> int:
    actual = verify_manifest()

    run(sys.executable, "real-stack-adapters/tools/verify_common_presentation_packet.py")
    run(sys.executable, "assurance-graph/build_graph.py", "--check")
    run(sys.executable, "assurance-graph/verify_graph.py")
    run(sys.executable, "arf-iteration-5-companion/verify_vectors.py", "--check")
    run(sys.executable, "real-stack-adapters/receipt-schema-v1.1-candidate/verify_schema.py")
    run(sys.executable, "real-stack-adapters/decision-scope-census/verify_results.py")
    run(sys.executable, "artifact/mutation-analysis/verify_mutation_analysis.py")
    for relative in (
        "real-stack-adapters/receipt-schema-v1.1-candidate",
        "real-stack-adapters/decision-scope-census",
        "artifact/mutation-analysis",
    ):
        verify_nested_manifest(ROOT / relative)

    kit = ROOT / "real-stack-adapters/independent-reproducer-v0.2-candidate"
    # Invoke through Bash so verification also works after extraction tools that
    # conservatively discard executable bits from ZIP entries.
    run("bash", str(kit / "verify-return.sh"), str(REFERENCE_RETURN))
    run(sys.executable, str(kit / "test-verifier-semantics.py"), str(REFERENCE_RETURN))

    summary = json.loads(
        (REFERENCE_RETURN / "return-summary.json").read_text(encoding="utf-8")
    )
    if summary != {
        **summary,
        "independent_run_package": False,
        "android_sdk_used": False,
        "in_scope_mismatches": 0,
        "observations": 12,
        "entry_point_executions": 2,
        "status": "PASS_RETURN_COMPLETE_NO_IN_SCOPE_MISMATCH",
    }:
        raise SystemExit("FAIL: reference-return claim boundary changed")
    expected_image = (
        "sha256:6663ff8c0511c09567e7e17dd82eb6b6943056a8b230680650085add9d610f33"
    )
    if (REFERENCE_RETURN / "CONTAINER-IMAGE-ID").read_text(encoding="utf-8").strip() != expected_image:
        raise SystemExit("FAIL: reference container image ID changed")

    verify_privacy(actual)
    print(json.dumps({
        "status": "PASS_PUBLIC_RELEASE_V0_2_0",
        "files": len(actual),
        "decision_scope_observations": 18,
        "reference_return_observations": 12,
        "valid_rule_omission_mutants_killed": 51,
        "tampered_evidence_rejected": True,
        "oracle_disagreement_representable": True,
        "independent_executions": 0,
        "public_release_modified": False,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
