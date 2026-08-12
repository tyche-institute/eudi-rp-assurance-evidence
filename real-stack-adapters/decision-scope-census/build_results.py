#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import platform
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
SCHEMA = PACKET / "receipt-schema-v1.1-candidate" / "decision-provenance-receipt-1.1.schema.json"
CORPUS = HERE / "corpus.json"
RESULTS = HERE / "results"
RECEIPTS = RESULTS / "receipts"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def observations_from_xml(results_dir: Path) -> dict[str, tuple[str, str]]:
    files = list(results_dir.glob("TEST-*TycheDecisionScopeCensusTest.xml"))
    if len(files) != 1:
        raise SystemExit(f"expected one census XML in {results_dir}, found {len(files)}")
    root = ET.parse(files[0]).getroot()
    counts = {key: int(root.attrib.get(key, 0)) for key in ("tests", "failures", "errors", "skipped")}
    if counts != {"tests": 1, "failures": 0, "errors": 0, "skipped": 0}:
        raise SystemExit(f"unexpected test counts in {files[0]}: {counts}")
    output = root.findtext("system-out") or ""
    observed: dict[str, tuple[str, str]] = {}
    for line in output.splitlines():
        match = re.search(r"TYCHE_SCOPE_OBSERVATION\|([^|]+)\|([^|]+)\|(.*)$", line)
        if match:
            observed[match.group(1)] = (match.group(2), match.group(3).strip())
    return observed


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


def main() -> int:
    if len(sys.argv) != 13:
        raise SystemExit(
            "usage: build_results.py EC_REPO EC_RUN EC_CLONE EC_DEP "
            "MP_REPO MP_RUN MP_CLONE MP_DEP WALT_REPO WALT_RUN WALT_CLONE WALT_DEP"
        )
    args = [Path(value) for value in sys.argv[1:]]
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    corpus_sha = sha256(CORPUS)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    Draft202012Validator.check_schema(schema)
    RECEIPTS.mkdir(parents=True, exist_ok=True)
    executed_at = datetime.now(timezone.utc).isoformat()
    patch = PACKET / "build-isolation" / "multipaz-jvm-only.patch"
    environment_sha = sha256_text(platform.platform() + "|" + platform.machine())

    configs = [
        {
            "adapter": "eudi-official",
            "repo": args[0], "run_log": args[1], "clone_log": args[2], "dep": args[3],
            "url": "https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint",
            "commit": "db5442501ea06907e614377a20d802748e8bfddb",
            "xml": args[0] / "build/test-results/test",
            "entry_kind": "library-api",
            "entry_identifier": "SdJwtVcValidator.validate",
            "entry_path": "src/main/kotlin/eu/europa/ec/eudi/verifier/endpoint/adapter/out/sdjwtvc/SdJwtVcValidator.kt",
            "exercised": ["syntax-parsing", "issuer-signature", "holder-binding", "nonce", "audience", "freshness"],
            "bypassed": ["issuer-trust"],
            "notes": "Trust-chain decision was neutralised by the test classification callback; presentation-context checks use the selected validator entry point.",
            "applicability": {},
            "isolation": False,
            "policy": "fixed clock; 10-second tolerance; classified test VCT; trust callback ignored",
        },
        {
            "adapter": "multipaz",
            "repo": args[4], "run_log": args[5], "clone_log": args[6], "dep": args[7],
            "url": "https://github.com/openwallet-foundation/multipaz",
            "commit": "570aa2475bd5b7e437d9041bf8ff1127bcf86cfb",
            "xml": args[4] / "multipaz/build/test-results/jvmTest",
            "entry_kind": "library-api",
            "entry_identifier": "SdJwtKb.verify",
            "entry_path": "multipaz/src/commonMain/kotlin/org/multipaz/sdjwt/SdJwtKb.kt",
            "exercised": ["syntax-parsing", "issuer-signature", "holder-binding"],
            "bypassed": ["nonce", "audience", "freshness", "issuer-trust"],
            "notes": "Issuer key and nonce/audience/creation-time predicates are supplied by the caller; a JVM-only build-isolation patch is applied outside production Kotlin source.",
            "applicability": {
                "nonce": "CALLER_SUPPLIED_POLICY",
                "audience": "CALLER_SUPPLIED_POLICY",
                "freshness": "CALLER_SUPPLIED_POLICY",
            },
            "isolation": True,
            "policy": "explicit corpus issuer JWK; caller predicates for nonce, audience and KB iat",
        },
        {
            "adapter": "waltid",
            "repo": args[8], "run_log": args[9], "clone_log": args[10], "dep": args[11],
            "url": "https://github.com/walt-id/waltid-identity",
            "commit": "f773918a3ad226ba7c0908d58941f18a3b89591d",
            "xml": args[8] / "waltid-libraries/credentials/waltid-verification-policies2/build/test-results/jvmTest",
            "entry_kind": "library-api",
            "entry_identifier": "CredentialSignaturePolicy.verify",
            "entry_path": "waltid-libraries/credentials/waltid-verification-policies2/src/commonMain/kotlin/id/walt/policies2/vc/policies/CredentialSignaturePolicy.kt",
            "exercised": ["syntax-parsing", "issuer-signature"],
            "bypassed": ["holder-binding", "nonce", "audience", "freshness", "issuer-trust"],
            "notes": "The selected credential-signature policy does not consume verifier nonce, audience, evaluation time or the KB-JWT as presentation context.",
            "applicability": {
                "key-binding-signature": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
                "nonce": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
                "audience": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
                "freshness": "NOT_REPRESENTABLE_AT_ENTRY_POINT",
            },
            "isolation": False,
            "policy": "CredentialSignaturePolicy default JWS verification after credential parsing",
        },
    ]

    matrix: list[dict[str, str]] = []
    receipt_names: list[str] = []
    for cfg in configs:
        observed = observations_from_xml(cfg["xml"])
        if set(observed) != {case["case_id"] for case in corpus["cases"]}:
            raise SystemExit(f"{cfg['adapter']}: incomplete observation set")
        dependencies = json.loads(cfg["dep"].read_text(encoding="utf-8"))
        test_source = HERE / "external-tests" / cfg["adapter"] / "TycheDecisionScopeCensusTest.kt"
        build_material = "\n".join([
            cfg["commit"], corpus_sha, sha256(test_source), cfg["policy"],
            sha256(patch) if cfg["isolation"] else "no-build-isolation-artifact",
        ])
        observations: list[dict[str, str]] = []
        for case in corpus["cases"]:
            case_id = case["case_id"]
            verdict, raw_reason = observed[case_id]
            applicability = cfg["applicability"].get(case["mutation_axis"], "IN_SCOPE")
            item = {
                "case_id": case_id,
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
            matrix.append({
                "adapter_id": cfg["adapter"],
                "case_id": case_id,
                "mutation_axis": case["mutation_axis"],
                "applicability": applicability,
                "profile_expected_verdict": case["profile_expected_verdict"],
                "observed_verdict": verdict,
                "comparison": item["comparison"],
                "raw_reason": raw_reason,
            })
        isolation = {
            "applied": cfg["isolation"],
            "description": (
                "JVM-only build-configuration isolation; production Kotlin source unchanged."
                if cfg["isolation"] else "No build-isolation artifact applied."
            ),
        }
        if cfg["isolation"]:
            isolation.update({
                "artifact_path": "../build-isolation/multipaz-jvm-only.patch",
                "artifact_sha256": sha256(patch),
            })
        evidence_files = [
            {"path": f"results/{path.name}", "sha256": sha256(path)}
            for path in (cfg["clone_log"], cfg["run_log"])
        ]
        receipt = {
            "schema_version": "1.1.0-research-candidate",
            "receipt_id": f"urn:tyche:eudi:provenance:{cfg['adapter']}:decision-scope-census:2026-08-12",
            "record_status": "executed-observation",
            "experiment_id": corpus["corpus_id"],
            "adapter_id": cfg["adapter"],
            "repository": cfg["url"],
            "source_commit": cfg["commit"],
            "source_tree": git(cfg["repo"], "rev-parse", "HEAD^{tree}"),
            "dependency_material": {"paths": dependencies["paths"], "sha256": dependencies["sha256"]},
            "build": {
                "configuration_sha256": sha256_text(build_material),
                "production_source_unmodified": True,
                "isolation": isolation,
            },
            "policy_configuration_sha256": sha256_text(cfg["policy"]),
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
            "entry_point": {
                "kind": cfg["entry_kind"],
                "identifier": cfg["entry_identifier"],
                "source_path": cfg["entry_path"],
            },
            "decision_scope": {
                "checks_exercised": cfg["exercised"],
                "checks_caller_supplied_or_bypassed": cfg["bypassed"],
                "notes": cfg["notes"],
            },
            "input": {"format": corpus["format"], "corpus_sha256": corpus_sha},
            "observations": observations,
            "execution": {
                "control": "tyche-controlled-local-run",
                "independent_of_tyche": False,
                "controller_identifier": "Tyche Institute",
                "relationship_to_tyche": "study author controlled the execution",
                "executed_at": executed_at,
                "environment_sha256": environment_sha,
            },
            "evidence_files": evidence_files,
            "claim_boundary": (
                "Tyche-controlled execution at one selected pinned entry point. Applicability "
                "classifies entry-point scope, not product quality. This is not an independent "
                "reproduction, deployed workflow, vulnerability, certification or conformance result."
            ),
        }
        errors = sorted(validator.iter_errors(receipt), key=lambda error: list(error.path))
        if errors:
            raise SystemExit(f"{cfg['adapter']}: {errors[0].json_path}: {errors[0].message}")
        receipt_path = RECEIPTS / f"{cfg['adapter']}-decision-scope-census-2026-08-12.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        receipt_names.append(receipt_path.name)

    summary = {
        "schema_version": "0.1.0-research",
        "executed_at": executed_at,
        "corpus_sha256": corpus_sha,
        "source_pins": {cfg["adapter"]: cfg["commit"] for cfg in configs},
        "observations": len(matrix),
        "independent_executions": 0,
        "matrix": matrix,
        "receipts": receipt_names,
        "claim_boundary": (
            "Selected entry-point decision-scope census under Tyche control. ACCEPT outside an "
            "entry point's represented scope is not an implementation failure."
        ),
    }
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "decision-scope-summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
