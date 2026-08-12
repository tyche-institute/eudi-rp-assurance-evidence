#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
PROFILE = PROJECT / "artifact/profile/profile.json"
OBJECTIVES = PROJECT / "fcaf-rp-sut-companion/test-objectives-v0.1.csv"
CORPUS = PROJECT / "real-stack-adapters/common-presentation-corpus/corpus.json"
MANIFESTS = PROJECT / "real-stack-adapters/manifests"
RECEIPTS = PROJECT / "real-stack-adapters/results/common-presentation-provenance"
OUTPUT = HERE / "graph-v0.1.json"
SUMMARY = HERE / "SUMMARY.md"
CHECKSUMS = HERE / "SHA256SUMS"


SOURCE_NODES = {
    "ARF-3.0.0": {
        "label": "EUDI Wallet Architecture and Reference Framework 3.0.0",
        "url": "https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework",
        "pin": "6373eee10b6e80225c7ce706a5ff1775fb799b22",
    },
    "FCAF": {
        "label": "EUDI Wallet Functional Conformance Assessment Framework methodology",
        "url": "https://github.com/eu-digital-identity-wallet/eudi-doc-functional-conformance-assessment/blob/7494831a1a9085bb6649c0a2f190e7c32070fcef/docs/fcaf/index.md",
        "pin": "7494831a1a9085bb6649c0a2f190e7c32070fcef",
    },
    "RFC-9901": {
        "label": "RFC 9901: Selective Disclosure for JWTs",
        "url": "https://www.rfc-editor.org/rfc/rfc9901.html",
        "pin": "RFC-9901",
    },
    "OpenID4VP-1.0": {
        "label": "OpenID for Verifiable Presentations 1.0",
        "url": "https://openid.net/specs/openid-4-verifiable-presentations-1_0.html",
        "pin": "1.0-final",
    },
    "eIDAS-Art-5b": {
        "label": "Regulation (EU) No 910/2014, Article 5b",
        "url": "https://eur-lex.europa.eu/eli/reg/2014/910/2024-10-18",
        "pin": "consolidated-2024-10-18",
    },
    "CIR-2025-848": {
        "label": "Commission Implementing Regulation (EU) 2025/848",
        "url": "https://eur-lex.europa.eu/eli/reg_impl/2025/848/oj",
        "pin": "2025-848",
    },
    "ETSI-TS-119-475": {
        "label": "ETSI TS 119 475",
        "url": "https://www.etsi.org/deliver/etsi_ts/119400_119499/119475/",
        "pin": "profile-anchor",
    },
    "CIR-2024-2981-TR40": {
        "label": "Commission Implementing Regulation (EU) 2024/2981, Topic 40 anchor",
        "url": "https://eur-lex.europa.eu/eli/reg_impl/2024/2981/oj",
        "pin": "2024-2981",
    },
    "CIR-2024-2981-TR90": {
        "label": "Commission Implementing Regulation (EU) 2024/2981, Topic 90 anchor",
        "url": "https://eur-lex.europa.eu/eli/reg_impl/2024/2981/oj",
        "pin": "2024-2981",
    },
    "CIR-2024-2981-TR91": {
        "label": "Commission Implementing Regulation (EU) 2024/2981, Topic 91 anchor",
        "url": "https://eur-lex.europa.eu/eli/reg_impl/2024/2981/oj",
        "pin": "2024-2981",
    },
    "research-proposal": {
        "label": "Tyche research proposal",
        "url": "https://tyche.institute/",
        "pin": "0.1.0-research",
    },
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def slug(value: str) -> str:
    return value.replace("/", "_").replace(" ", "_")


def build() -> dict:
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    with OBJECTIVES.open(newline="", encoding="utf-8") as handle:
        objectives = list(csv.DictReader(handle))
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    manifests = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(MANIFESTS.glob("*.json"))]
    receipts = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(RECEIPTS.glob("*.json"))]

    nodes: list[dict] = []
    edges: list[dict] = []

    def node(node_id: str, node_type: str, label: str, status: str, **properties) -> None:
        nodes.append({"id": node_id, "type": node_type, "label": label, "status": status, "properties": properties})

    def edge(source: str, target: str, edge_type: str, scope: str) -> None:
        edge_id = f"edge:{len(edges) + 1:03d}:{slug(edge_type)}"
        edges.append({"id": edge_id, "from": source, "to": target, "type": edge_type, "scope": scope})

    for source_id, source in sorted(SOURCE_NODES.items()):
        source_type = "research_source" if source_id == "research-proposal" else "official_source"
        source_status = "research_proposal_not_normative" if source_id == "research-proposal" else "pinned_or_versioned_anchor"
        properties = {key: value for key, value in source.items() if key != "label"}
        node(f"source:{slug(source_id)}", source_type, source["label"], source_status, **properties)

    profile_id = "profile:rp_verifier_assurance_0.1"
    node(profile_id, "research_profile", profile["title"], profile["status"], version=profile["version"],
         sha256=digest(PROFILE), claim_boundary=profile["claim_boundary"])

    objective_by_rule = {row["source_profile_rule"]: row for row in objectives}
    for rule in profile["rules"]:
        rule_id = f"rule:{rule['id']}"
        node(rule_id, "profile_rule", rule["requirement"], "research_rule_not_official_requirement",
             phase=rule["phase"], anchors=rule["anchors"])
        edge(profile_id, rule_id, "contains", "The research profile contains this rule.")
        objective = objective_by_rule[rule["id"]]
        objective_id = f"objective:{objective['candidate_test_objective_id']}"
        node(objective_id, "candidate_objective", objective["objective"], objective["status"],
             sut=objective["candidate_sut"], test_class=objective["candidate_class"],
             layer=objective["candidate_layer"], area=objective["candidate_area"],
             expected_evidence=objective["expected_result_or_evidence"])
        edge(rule_id, objective_id, "operationalized_by",
             "One candidate objective translates this research rule; it does not make the rule official.")
        for anchor in rule["anchors"]:
            edge(rule_id, f"source:{slug(anchor)}", "anchored_in",
                 "The research rule cites this normative or documentary anchor.")

    test_case_id = "case:RP_WS_SM_IssuerAuthentication_001"
    node(test_case_id, "test_case", "Reject an invalid SD-JWT issuer signature",
         "local_test_spec_executed_not_fcaf",
         path="fcaf-rp-sut-companion/test-specs/RP_WS_SM_IssuerAuthentication_001.md")
    edge("objective:RP_WS_SM_IssuerAuthentication_001", test_case_id, "realized_by",
         "This is the first full local specification for the candidate objective.")
    edge(test_case_id, "source:FCAF", "anchored_in",
         "The local research specification follows the current FCAF template and proposed future RP SUT hierarchy.")

    corpus_id = "corpus:common_sdjwt_001"
    negative = next(item for item in corpus["cases"] if item["case_id"] == "RP_WS_SM_IssuerAuthentication_001")
    node(corpus_id, "corpus", "Common deterministic SD-JWT presentation corpus",
         "synthetic_test_only", corpus_id=corpus["corpus_id"], format=corpus["format"],
         sha256=digest(CORPUS), mutation_presentation_sha256=negative["presentation_sha256"])
    edge(test_case_id, corpus_id, "uses_corpus",
         "The test case uses the exact baseline and isolated issuer-signature mutation in this corpus.")

    manifests_by_commit = {manifest["pinned_commit"]: manifest for manifest in manifests}
    for receipt in receipts:
        manifest = manifests_by_commit[receipt["source_commit"]]
        implementation_id = f"implementation:{receipt['adapter_id']}"
        node(implementation_id, "implementation", manifest["implementation"],
             "pinned_maintained_source", repository=receipt["repository"],
             commit=receipt["source_commit"], source_tree=receipt["source_tree"])
        receipt_id = f"receipt:{receipt['adapter_id']}"
        receipt_path = next(p for p in sorted(RECEIPTS.glob("*.json"))
                            if json.loads(p.read_text(encoding="utf-8"))["adapter_id"] == receipt["adapter_id"])
        node(receipt_id, "evidence_receipt", receipt["receipt_id"],
             "tyche_controlled_not_independent", sha256=digest(receipt_path),
             baseline_verdict=receipt["baseline"]["verdict"],
             mutation_verdict=receipt["mutation"]["verdict"],
             raw_reason=receipt["mutation"]["raw_reason"],
             claim_boundary=receipt["claim_boundary"])
        edge(test_case_id, receipt_id, "evidenced_by",
             "The receipt records a Tyche-controlled execution of this exact case.")
        edge(receipt_id, implementation_id, "decision_from",
             "The receipt binds its observed decision to this pinned implementation source.")
        edge(receipt_id, corpus_id, "consumed_exact_input",
             "The receipt records the SHA-256 of this exact corpus and mutated presentation.")

    nodes.sort(key=lambda item: item["id"])
    edges.sort(key=lambda item: item["id"])
    return {
        "schema_version": "0.1.0-research",
        "graph_id": "urn:tyche:eudi:assurance-graph:0.1",
        "snapshot_date": "2026-08-12",
        "claim_boundary": (
            "Typed joins among research artifacts and pinned evidence only; not an official EUDIW/FCAF graph, "
            "not conformance, and not independent reproduction."
        ),
        "nodes": nodes,
        "edges": edges,
        "metrics": {
            "profile_rules": len(profile["rules"]),
            "candidate_objectives": len(objectives),
            "fully_specified_objectives": 1,
            "exact_object_implementations": len(receipts),
            "provenance_receipts": len(receipts),
            "independent_executions": 0,
        },
    }


def render_summary(graph: dict) -> str:
    metrics = graph["metrics"]
    return f"""# EUDIW Assurance Graph v0.1 — summary

| Measure | Recorded value |
|---|---:|
| Research-profile rules | {metrics['profile_rules']} |
| Candidate RP-as-SUT objectives | {metrics['candidate_objectives']} |
| Full local test specifications | {metrics['fully_specified_objectives']} |
| Pinned implementations consuming the exact object | {metrics['exact_object_implementations']} |
| Decision-provenance receipts | {metrics['provenance_receipts']} |
| Independently controlled executions | {metrics['independent_executions']} |

The graph records one fully specified issuer-authentication case with three Tyche-controlled
maintained-source decisions. The largest evidence gaps are RP registration/service binding,
intended-use enforcement, post-presentation reliance and independent execution.
"""


def write_checksums() -> None:
    paths = [HERE / name for name in (
        "README.md", "build_graph.py", "graph.schema.json", "graph-v0.1.json", "SUMMARY.md", "verify_graph.py"
    )]
    CHECKSUMS.write_text("".join(f"{digest(path)}  {path.name}\n" for path in paths), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    graph_text = json.dumps(build(), indent=2, sort_keys=True) + "\n"
    summary_text = render_summary(json.loads(graph_text))
    if args.check:
        if OUTPUT.read_text(encoding="utf-8") != graph_text or SUMMARY.read_text(encoding="utf-8") != summary_text:
            raise SystemExit("generated graph or summary is stale")
        print("Assurance Graph deterministic rebuild PASS")
        return 0
    OUTPUT.write_text(graph_text, encoding="utf-8")
    SUMMARY.write_text(summary_text, encoding="utf-8")
    write_checksums()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
