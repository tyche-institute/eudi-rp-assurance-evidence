#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

IMPLEMENTATION = "python-imperative/0.1.0"


def subset(left: list[str], right: list[str]) -> bool:
    return set(left).issubset(set(right))


def evaluate(tx: dict) -> str:
    rp, p, r = tx["rp"], tx["presentation"], tx["reliance"]
    if not p["parse_ok"]:
        return "R_PARSE_INVALID"
    if not rp["registered"]:
        return "R_RP_UNREGISTERED"
    if rp["registration_status"] != "active":
        return "R_RP_SUSPENDED"
    if rp["authenticated_rp_id"] != rp["registered_rp_id"]:
        return "R_RP_IDENTITY_MISMATCH"
    if rp["transaction_purpose"] not in rp["registered_purposes"]:
        return "R_PURPOSE_MISMATCH"
    if not subset(rp["requested_attributes"], rp["registered_attributes"]):
        return "R_ATTRIBUTE_OVER_REQUEST"
    if not p["issuer_signature_valid"]:
        return "R_ISSUER_SIGNATURE_INVALID"
    if not p["all_disclosures_bound"]:
        return "R_DISCLOSURE_UNBOUND"
    if not p["holder_binding_valid"]:
        return "R_HOLDER_BINDING_INVALID"
    if p["audience"] != p["expected_audience"]:
        return "R_AUDIENCE_MISMATCH"
    if p["nonce"] != p["expected_nonce"]:
        return "R_NONCE_MISMATCH"
    age = p["evaluated_at_epoch"] - p["issued_at"]
    if age < 0 or age > p["max_age_seconds"]:
        return "R_PRESENTATION_STALE"
    if p["credential_status"] != "active":
        return "R_CREDENTIAL_INACTIVE"
    if not p["issuer_trusted"]:
        return "R_ISSUER_UNTRUSTED"
    if not subset(r["used_attributes"], r["approved_attributes"]):
        return "R_USE_EXCEEDS_APPROVAL"
    if not r["lawful_basis_recorded"]:
        return "R_LAWFUL_BASIS_UNRECORDED"
    if not r["decision_log_complete"] or not r["verifier_version"] or not r["policy_version"]:
        return "R_AUDIT_EVIDENCE_INCOMPLETE"
    return "A_PROFILE_CONFORMANT"


def main() -> None:
    corpus = json.load(sys.stdin)
    results = []
    for vector in corpus["vectors"]:
        reason = evaluate(vector["transaction"])
        results.append({
            "id": vector["id"],
            "implementation": IMPLEMENTATION,
            "verdict": "ACCEPT" if reason.startswith("A_") else "REJECT",
            "reason": reason,
        })
    json.dump({"implementation": IMPLEMENTATION, "results": results}, sys.stdout, separators=(",", ":"))
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
