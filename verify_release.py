#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def run(*command: str, cwd: Path = ROOT) -> None:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.returncode:
        raise SystemExit(f"FAIL: {' '.join(command)}\n{result.stdout}\n{result.stderr}")
    if result.stdout.strip():
        print(result.stdout.strip())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
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
        if path.is_file() and path.name not in {"RELEASE-SHA256SUMS"} and "__pycache__" not in path.parts
    }
    if listed != actual:
        raise SystemExit(f"FAIL: release manifest set mismatch: missing={sorted(actual-listed)}, extra={sorted(listed-actual)}")

    run(sys.executable, "real-stack-adapters/tools/verify_common_presentation_packet.py")
    run(sys.executable, "assurance-graph/build_graph.py", "--check")
    run(sys.executable, "assurance-graph/verify_graph.py")
    run(sys.executable, "arf-iteration-5-companion/verify_vectors.py", "--check")

    email = re.compile(r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b")
    forbidden = (
        "/home/", "/srv/", "contact-ledger", "fieldwork-log", "professional_email",
        "eudiw-survey.tyche.institute", "dfcc915f-a6ff-404c-9605-a34ef0809b77", "7937934"
    )
    text_suffixes = {".md", ".json", ".py", ".sh", ".kt", ".csv", ".tex", ".cff", ".patch", ".log", ""}
    scanner_sources = {
        Path("verify_release.py"),
        Path("assurance-graph/verify_graph.py"),
        Path("engagement/rp-programme-travel-mobility/build.sh"),
    }
    for relative in sorted(actual):
        path = ROOT / relative
        if path.is_symlink():
            raise SystemExit(f"FAIL: symlink in release: {relative}")
        if path.stat().st_size > 2_000_000:
            raise SystemExit(f"FAIL: unexpectedly large release file: {relative}")
        if relative in scanner_sources or path.suffix.lower() not in text_suffixes or path.suffix.lower() == ".pdf":
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        lowered = content.lower()
        if email.search(content) or any(term in lowered for term in forbidden):
            raise SystemExit(f"FAIL: privacy scan: {relative}")

    print(json.dumps({
        "status": "PASS_PUBLIC_RELEASE_CANDIDATE",
        "files": len(actual),
        "common_presentation_receipts": 3,
        "assurance_graph_nodes": 54,
        "assurance_graph_edges": 76,
        "arf_lm_baseline_accepts": 2,
        "arf_lm_negative_rejects": 3,
        "independent_executions": 0
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
