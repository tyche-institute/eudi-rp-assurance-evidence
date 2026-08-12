#!/usr/bin/env python3
"""Generate a frozen, non-overlapping RP assurance corpus.

The corpus models the request, presentation, and post-presentation reliance
boundary. It deliberately does not reuse the SD-JWT census corpus or its
headline step-5 experiment.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "corpus" / "vectors.json"


def baseline() -> dict:
    return {
        "rp": {
            "registration_id": "EE-RP-000042",
            "registered": True,
            "registration_status": "active",
            "registered_rp_id": "x509_hash:rp.example",
            "authenticated_rp_id": "x509_hash:rp.example",
            "registered_purposes": ["age-assurance", "account-opening"],
            "transaction_purpose": "age-assurance",
            "registered_attributes": ["age_over_18", "family_name"],
            "requested_attributes": ["age_over_18"],
        },
        "presentation": {
            "parse_ok": True,
            "issuer_signature_valid": True,
            "all_disclosures_bound": True,
            "holder_binding_valid": True,
            "expected_audience": "x509_hash:rp.example",
            "audience": "x509_hash:rp.example",
            "expected_nonce": "n-7f3c",
            "nonce": "n-7f3c",
            "issued_at": 1_800_000_000,
            "evaluated_at_epoch": 1_800_000_120,
            "max_age_seconds": 300,
            "credential_status": "active",
            "issuer_trusted": True,
        },
        "reliance": {
            "approved_attributes": ["age_over_18"],
            "used_attributes": ["age_over_18"],
            "lawful_basis_recorded": True,
            "verifier_version": "verifier-under-test/1.0.0",
            "policy_version": "rp-policy/2026-08-11",
            "decision_log_complete": True,
        },
    }


CASES: list[tuple[str, str, str, object]] = [
    ("RPV-001", "conformant baseline", "", None),
    ("RPV-002", "conformant second registered purpose", "rp.transaction_purpose", "account-opening"),
    ("RPV-003", "conformant two-attribute request", "rp.requested_attributes", ["family_name", "age_over_18"]),
    ("RPV-004", "presentation cannot be parsed", "presentation.parse_ok", False),
    ("RPV-005", "relying party is absent from register", "rp.registered", False),
    ("RPV-006", "relying-party registration suspended", "rp.registration_status", "suspended"),
    ("RPV-007", "relying-party registration cancelled", "rp.registration_status", "cancelled"),
    ("RPV-008", "authenticated RP differs from registered RP", "rp.authenticated_rp_id", "x509_hash:other.example"),
    ("RPV-009", "purpose not declared at registration", "rp.transaction_purpose", "employment-screening"),
    ("RPV-010", "one requested attribute not registered", "rp.requested_attributes", ["age_over_18", "date_of_birth"]),
    ("RPV-011", "empty registered attribute set with non-empty request", "rp.registered_attributes", []),
    ("RPV-012", "issuer signature invalid", "presentation.issuer_signature_valid", False),
    ("RPV-013", "a disclosed value is not issuer-bound", "presentation.all_disclosures_bound", False),
    ("RPV-014", "holder binding invalid", "presentation.holder_binding_valid", False),
    ("RPV-015", "audience mismatch", "presentation.audience", "x509_hash:other.example"),
    ("RPV-016", "nonce mismatch", "presentation.nonce", "n-replayed"),
    ("RPV-017", "presentation one second beyond freshness window", "presentation.evaluated_at_epoch", 1_800_000_301),
    ("RPV-018", "presentation exactly at freshness boundary", "presentation.evaluated_at_epoch", 1_800_000_300),
    ("RPV-019", "presentation from the future", "presentation.issued_at", 1_800_000_121),
    ("RPV-020", "credential revoked", "presentation.credential_status", "revoked"),
    ("RPV-021", "credential suspended", "presentation.credential_status", "suspended"),
    ("RPV-022", "issuer outside applicable trust policy", "presentation.issuer_trusted", False),
    ("RPV-023", "reliance uses an unapproved attribute", "reliance.used_attributes", ["age_over_18", "family_name"]),
    ("RPV-024", "lawful basis not recorded", "reliance.lawful_basis_recorded", False),
    ("RPV-025", "decision log incomplete", "reliance.decision_log_complete", False),
    ("RPV-026", "verifier version missing", "reliance.verifier_version", ""),
    ("RPV-027", "policy version missing", "reliance.policy_version", ""),
    ("RPV-028", "multiple failures: registration precedes cryptography", "__multi__", {"rp.registered": False, "presentation.issuer_signature_valid": False}),
    ("RPV-029", "multiple failures: over-request precedes nonce", "__multi__", {"rp.requested_attributes": ["date_of_birth"], "presentation.nonce": "wrong"}),
    ("RPV-030", "multiple failures: signature precedes stale", "__multi__", {"presentation.issuer_signature_valid": False, "presentation.evaluated_at_epoch": 1_800_000_999}),
    ("RPV-031", "multiple failures: reliance over-use precedes audit", "__multi__", {"reliance.used_attributes": ["family_name"], "reliance.decision_log_complete": False}),
    ("RPV-032", "attribute order is not semantically significant", "rp.registered_attributes", ["family_name", "age_over_18"]),
    ("RPV-033", "no attributes requested or used", "__multi__", {"rp.requested_attributes": [], "reliance.approved_attributes": [], "reliance.used_attributes": []}),
    ("RPV-034", "empty registered purpose list", "rp.registered_purposes", []),
    ("RPV-035", "negative age is stale", "presentation.issued_at", 1_800_000_999),
    ("RPV-036", "audit record absent although protocol checks pass", "__multi__", {"reliance.verifier_version": "", "reliance.policy_version": "", "reliance.decision_log_complete": False}),
]


EXPECTED = {
    "RPV-001": "A_PROFILE_CONFORMANT", "RPV-002": "A_PROFILE_CONFORMANT", "RPV-003": "A_PROFILE_CONFORMANT",
    "RPV-004": "R_PARSE_INVALID", "RPV-005": "R_RP_UNREGISTERED", "RPV-006": "R_RP_SUSPENDED",
    "RPV-007": "R_RP_SUSPENDED", "RPV-008": "R_RP_IDENTITY_MISMATCH", "RPV-009": "R_PURPOSE_MISMATCH",
    "RPV-010": "R_ATTRIBUTE_OVER_REQUEST", "RPV-011": "R_ATTRIBUTE_OVER_REQUEST",
    "RPV-012": "R_ISSUER_SIGNATURE_INVALID", "RPV-013": "R_DISCLOSURE_UNBOUND",
    "RPV-014": "R_HOLDER_BINDING_INVALID", "RPV-015": "R_AUDIENCE_MISMATCH", "RPV-016": "R_NONCE_MISMATCH",
    "RPV-017": "R_PRESENTATION_STALE", "RPV-018": "A_PROFILE_CONFORMANT", "RPV-019": "R_PRESENTATION_STALE",
    "RPV-020": "R_CREDENTIAL_INACTIVE", "RPV-021": "R_CREDENTIAL_INACTIVE", "RPV-022": "R_ISSUER_UNTRUSTED",
    "RPV-023": "R_USE_EXCEEDS_APPROVAL", "RPV-024": "R_LAWFUL_BASIS_UNRECORDED",
    "RPV-025": "R_AUDIT_EVIDENCE_INCOMPLETE", "RPV-026": "R_AUDIT_EVIDENCE_INCOMPLETE",
    "RPV-027": "R_AUDIT_EVIDENCE_INCOMPLETE", "RPV-028": "R_RP_UNREGISTERED",
    "RPV-029": "R_ATTRIBUTE_OVER_REQUEST", "RPV-030": "R_ISSUER_SIGNATURE_INVALID",
    "RPV-031": "R_USE_EXCEEDS_APPROVAL", "RPV-032": "A_PROFILE_CONFORMANT",
    "RPV-033": "A_PROFILE_CONFORMANT", "RPV-034": "R_PURPOSE_MISMATCH",
    "RPV-035": "R_PRESENTATION_STALE", "RPV-036": "R_AUDIT_EVIDENCE_INCOMPLETE",
}


def set_path(doc: dict, path: str, value: object) -> None:
    cursor = doc
    parts = path.split(".")
    for part in parts[:-1]:
        cursor = cursor[part]
    cursor[parts[-1]] = value


def main() -> None:
    vectors = []
    for vector_id, title, path, value in CASES:
        tx = baseline()
        if path == "__multi__":
            for subpath, subvalue in value.items():
                set_path(tx, subpath, subvalue)
        elif path:
            set_path(tx, path, value)
        expected_code = EXPECTED[vector_id]
        canonical = json.dumps(tx, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
        vectors.append({
            "id": vector_id,
            "title": title,
            "expected_verdict": "ACCEPT" if expected_code.startswith("A_") else "REJECT",
            "expected_reason": expected_code,
            "transaction": tx,
            "transaction_sha256": hashlib.sha256(canonical).hexdigest(),
        })
    payload = {
        "corpus_id": "urn:tyche:eudi:rp-assurance-corpus:0.1.0",
        "generated_by": "generate_vectors.py",
        "vector_count": len(vectors),
        "vectors": vectors,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(vectors)} vectors to {OUT}")


if __name__ == "__main__":
    main()
