#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import subprocess
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


KIT = Path("/kit")
CORPUS = KIT / "corpus.json"
SCHEMA = KIT / "receipt.schema.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git(repo: Path, *arguments: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *arguments], text=True).strip()


def command_output(command: list[str]) -> str:
    process = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True)
    return process.stdout.decode("utf-8", errors="replace").strip()


def dependency_material(repo: Path, paths: list[str]) -> dict[str, object]:
    digest = hashlib.sha256()
    present: list[str] = []
    for relative in sorted(paths):
        path = repo / relative
        if not path.is_file():
            continue
        file_digest = sha256(path)
        present.append(relative)
        digest.update(relative.encode("utf-8") + b"\0" + bytes.fromhex(file_digest))
    if not present:
        raise SystemExit(f"no dependency files found in {repo}")
    return {"paths": present, "sha256": digest.hexdigest()}


def observations_from_xml(path: Path) -> dict[str, tuple[str, str]]:
    root = ET.parse(path).getroot()
    counts = {key: int(root.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    if counts != {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}:
        raise SystemExit(f"test execution did not complete: {path}: {counts}")
    output = root.findtext("system-out") or ""
    observations: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        match = re.search(r"TYCHE_RETURN_OBSERVATION\|([^|]+)\|([^|]+)\|(.*)$", line)
        if match:
            observations[match.group(1)] = (match.group(2), match.group(3).strip())
    return observations


def normalized_reason(axis: str, verdict: str) -> str:
    if verdict == "ACCEPT":
        return "NONE"
    return {
        "issuer-signature": "INVALID_ISSUER_SIGNATURE",
        "key-binding-signature": "INVALID_HOLDER_BINDING",
        "nonce": "NONCE_MISMATCH",
        "audience": "AUDIENCE_MISMATCH",
        "freshness": "FRESHNESS_FAILURE",
    }.get(axis, "OTHER")


def comparison(applicability: str, expected: str, observed: str) -> str:
    if applicability != "IN_SCOPE" or "NOT_RUN" in {expected, observed}:
        return "NOT_ASSESSED"
    return "MATCH" if expected == observed else "MISMATCH"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ec-repo", type=Path, required=True)
    parser.add_argument("--walt-repo", type=Path, required=True)
    parser.add_argument("--control", required=True)
    parser.add_argument("--independent", choices=("true", "false"), required=True)
    parser.add_argument("--controller-id", required=True)
    parser.add_argument("--relationship", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    corpus_sha = sha256(CORPUS)
    executed_at = datetime.now(timezone.utc).isoformat()
    independent = args.independent == "true"

    environment = {
        "architecture": platform.machine(),
        "base_image": __import__("os").environ["TYCHE_REPRO_BASE_IMAGE"],
        "java": command_output(["java", "-version"]),
        "kernel": platform.release(),
        "os": platform.platform(),
        "python": command_output(["python3", "--version"]),
        "android_home_set": False,
        "android_sdk_root_set": False,
        "sdkmanager_present": False,
    }
    environment_path = args.output / "environment.json"
    environment_path.write_text(json.dumps(environment, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    environment_sha = sha256(environment_path)

    configs = [
        {
            "adapter": "eudi-official",
            "repo": args.ec_repo,
            "url": "https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint",
            "commit": "db5442501ea06907e614377a20d802748e8bfddb",
            "dependencies": [
                "build.gradle.kts", "settings.gradle.kts", "gradle/libs.versions.toml",
                "gradle/wrapper/gradle-wrapper.properties",
            ],
            "test_source": KIT / "external-tests/eudi-official/TycheIndependentReturnTest.kt",
            "xml": args.output / "raw/eudi-official-test.xml",
            "evidence": [
                args.output / "raw/eudi-official-clone.log",
                args.output / "raw/eudi-official-test.log",
                args.output / "raw/eudi-official-test.xml",
                environment_path,
            ],
            "entry": {
                "kind": "library-api",
                "identifier": "SdJwtVcValidator.validate",
                "source_path": "src/main/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc/SdJwtVcValidator.kt",
            },
            "checks": ["syntax-parsing", "issuer-signature", "holder-binding", "nonce", "audience", "freshness"],
            "outside": ["issuer-trust"],
            "notes": "Trust-chain decision is neutralised by the test callback; presentation-context checks use the selected validator entry point.",
            "applicability": {},
            "policy": "fixed clock; 10-second tolerance; classified test VCT; trust callback ignored",
        },
        {
            "adapter": "waltid",
            "repo": args.walt_repo,
            "url": "https://github.com/walt-id/waltid-identity",
            "commit": "f773918a3ad226ba7c0908d58941f18a3b89591d",
            "dependencies": [
                "build.gradle.kts", "settings.gradle.kts", "gradle/libs.versions.toml",
                "gradle/wrapper/gradle-wrapper.properties",
                "waltid-libraries/credentials/waltid-verification-policies2/build.gradle.kts",
            ],
            "test_source": KIT / "external-tests/waltid/TycheIndependentReturnTest.kt",
            "xml": args.output / "raw/waltid-test.xml",
            "evidence": [
                args.output / "raw/waltid-clone.log",
                args.output / "raw/waltid-test.log",
                args.output / "raw/waltid-test.xml",
                environment_path,
            ],
            "entry": {
                "kind": "library-api",
                "identifier": "CredentialSignaturePolicy.verify",
                "source_path": "waltid-libraries/credentials/waltid-verification-policies2/src/commonMain/kotlin/id/walt/policies2/vc/policies/CredentialSignaturePolicy.kt",
            },
            "checks": ["syntax-parsing", "issuer-signature"],
            "outside": ["holder-binding", "nonce", "audience", "freshness", "issuer-trust"],
            "notes": "The selected credential-signature policy does not consume verifier nonce, audience, evaluation time or the KB-JWT as presentation context.",
            "applicability": {
                "key-binding-signature": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
                "nonce": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
                "audience": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
                "freshness": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
            },
            "policy": "CredentialSignaturePolicy default JWS verification after credential parsing",
        },
    ]

    all_rows: list[dict[str, str]] = []
    receipt_names: list[str] = []
    for config in configs:
        observed = observations_from_xml(config["xml"])
        expected_ids = {case["case_id"] for case in corpus["cases"]}
        if set(observed) != expected_ids:
            raise SystemExit(f"{config['adapter']}: incomplete observation set")
        dependencies = dependency_material(config["repo"], config["dependencies"])
        build_hash = sha256_text("\n".join([
            config["commit"], corpus_sha, sha256(config["test_source"]),
            config["policy"], environment["base_image"],
        ]))
        observations = []
        for case in corpus["cases"]:
            verdict, raw_reason = observed[case["case_id"]]
            applicability = config["applicability"].get(case["mutation_axis"], "IN_SCOPE")
            item = {
                "case_id": case["case_id"],
                "object_sha256": case["presentation_sha256"],
                "mutation_axis": case["mutation_axis"],
                "applicability": applicability,
                "oracle_expected_verdict": case["profile_expected_verdict"],
                "observed_verdict": verdict,
                "comparison": comparison(applicability, case["profile_expected_verdict"], verdict),
                "raw_reason": raw_reason,
                "normalized_reason": normalized_reason(case["mutation_axis"], verdict),
            }
            observations.append(item)
            all_rows.append({"adapter_id": config["adapter"], **item})
        evidence_files = [
            {"path": str(path.relative_to(args.output)), "sha256": sha256(path)}
            for path in config["evidence"]
        ]
        receipt = {
            "schema_version": "1.1.0-research-candidate",
            "receipt_id": f"urn:tyche:eudi:provenance:{config['adapter']}:independent-return:{executed_at}",
            "record_status": "executed-observation",
            "experiment_id": corpus["corpus_id"],
            "adapter_id": config["adapter"],
            "repository": config["url"],
            "source_commit": config["commit"],
            "source_tree": git(config["repo"], "rev-parse", "HEAD^{tree}"),
            "dependency_material": dependencies,
            "build": {
                "configuration_sha256": build_hash,
                "production_source_unmodified": True,
                "isolation": {"applied": False, "description": "No build-isolation artifact applied."},
            },
            "policy_configuration_sha256": sha256_text(config["policy"]),
            "trust_source": {
                "type": "synthetic-x5c-and-pinned-jwk",
                "revision": corpus["corpus_id"],
                "sha256": corpus_sha,
            },
            "evaluation_context": {
                "evaluated_at": corpus["fixed_context"]["evaluated_at"],
                "nonce": corpus["fixed_context"]["nonce"],
                "audience": corpus["fixed_context"]["audience"],
            },
            "entry_point": config["entry"],
            "decision_scope": {
                "checks_exercised": config["checks"],
                "checks_caller_supplied_or_bypassed": config["outside"],
                "notes": config["notes"],
            },
            "input": {"format": corpus["format"], "corpus_sha256": corpus_sha},
            "observations": observations,
            "execution": {
                "control": args.control,
                "independent_of_tyche": independent,
                "controller_identifier": args.controller_id,
                "relationship_to_tyche": args.relationship,
                "executed_at": executed_at,
                "environment_sha256": environment_sha,
            },
            "evidence_files": evidence_files,
            "claim_boundary": (
                "Selected pinned entry-point execution over synthetic inputs. Controller labels are "
                "self-asserted in this receipt. This is not a deployed workflow, vulnerability, "
                "certification or official conformance result."
            ),
        }
        errors = sorted(validator.iter_errors(receipt), key=lambda error: list(error.path))
        if errors:
            raise SystemExit(f"{config['adapter']}: {errors[0].json_path}: {errors[0].message}")
        receipt_path = args.output / "receipts" / f"{config['adapter']}-receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt_names.append(str(receipt_path.relative_to(args.output)))

    in_scope_mismatches = sum(row["comparison"] == "MISMATCH" for row in all_rows)
    summary = {
        "schema_version": "0.2.0-research-candidate",
        "status": (
            "PASS_RETURN_COMPLETE_NO_IN_SCOPE_MISMATCH"
            if in_scope_mismatches == 0
            else "PASS_RETURN_COMPLETE_WITH_IN_SCOPE_MISMATCH"
        ),
        "corpus_sha256": corpus_sha,
        "entry_point_executions": 2,
        "observations": len(all_rows),
        "in_scope_mismatches": in_scope_mismatches,
        "independent_run_package": independent,
        "controller": {
            "control": args.control,
            "controller_identifier": args.controller_id,
            "relationship_to_tyche": args.relationship,
        },
        "android_sdk_used": False,
        "receipts": receipt_names,
        "rows": all_rows,
        "claim_boundary": (
            "A complete return package can contain oracle disagreement. Independence remains a "
            "provenance claim requiring validation beyond the self-asserted receipt fields."
        ),
    }
    (args.output / "return-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
