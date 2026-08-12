#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent


def fail(message: str) -> None:
    raise SystemExit(f"FAIL: {message}")


def main() -> int:
    graph = json.loads((HERE / "graph-v0.1.json").read_text(encoding="utf-8"))
    schema = json.loads((HERE / "graph.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    errors = sorted(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(graph),
                    key=lambda error: list(error.path))
    if errors:
        fail(errors[0].message)

    node_ids = [node["id"] for node in graph["nodes"]]
    edge_ids = [edge["id"] for edge in graph["edges"]]
    if len(node_ids) != len(set(node_ids)) or len(edge_ids) != len(set(edge_ids)):
        fail("node or edge IDs are not unique")
    known = set(node_ids)
    for edge in graph["edges"]:
        if edge["from"] not in known or edge["to"] not in known:
            fail(f"dangling edge {edge['id']}")

    rules = {node["id"] for node in graph["nodes"] if node["type"] == "profile_rule"}
    objectives = {node["id"] for node in graph["nodes"] if node["type"] == "candidate_objective"}
    mappings = [edge for edge in graph["edges"] if edge["type"] == "operationalized_by"]
    if len(rules) != 17 or len(objectives) != 17 or len(mappings) != 17:
        fail("expected a 17-rule, 17-objective, 17-mapping graph")
    if {edge["from"] for edge in mappings} != rules or {edge["to"] for edge in mappings} != objectives:
        fail("rule-to-objective mapping is not one-to-one")

    with (PROJECT / "fcaf-rp-sut-companion/test-objectives-v0.1.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        csv_objectives = {f"objective:{row['candidate_test_objective_id']}" for row in csv.DictReader(handle)}
    if csv_objectives != objectives:
        fail("graph objectives differ from the source inventory")

    evidence = [node for node in graph["nodes"] if node["type"] == "evidence_receipt"]
    if len(evidence) != 3 or any(node["status"] != "tyche_controlled_not_independent" for node in evidence):
        fail("expected three explicitly non-independent receipt nodes")
    if graph["metrics"]["independent_executions"] != 0:
        fail("independent execution count must remain zero")

    receipt_check = subprocess.run(
        [sys.executable, str(PROJECT / "real-stack-adapters/tools/verify_common_presentation_packet.py")],
        capture_output=True, text=True, check=False
    )
    if receipt_check.returncode != 0:
        fail(f"underlying receipt packet invalid: {receipt_check.stderr.strip()}")
    rebuild = subprocess.run(
        [sys.executable, str(HERE / "build_graph.py"), "--check"],
        capture_output=True, text=True, check=False
    )
    if rebuild.returncode != 0:
        fail(rebuild.stderr.strip() or rebuild.stdout.strip())

    forbidden = ("contact-ledger", "respondent", "professional_email", "@")
    serialized = json.dumps(graph, sort_keys=True).lower()
    if any(term in serialized for term in forbidden):
        fail("privacy scan found a forbidden contact/survey term")

    print(json.dumps({
        "status": "PASS",
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        **graph["metrics"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

