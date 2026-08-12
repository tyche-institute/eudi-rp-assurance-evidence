#!/usr/bin/env python3
"""Generate one-property SD-JWT+KB mutations for a decision-scope census."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_GENERATOR = HERE.parent / "common-presentation-corpus" / "generate_fixture.py"


def load_base_generator():
    spec = importlib.util.spec_from_file_location("tyche_common_fixture", BASE_GENERATOR)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load common-presentation generator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    base = load_base_generator()
    issuer_header = {"alg": "ES256", "typ": "dc+sd-jwt", "x5c": [base.ISSUER_X5C]}
    holder_public_jwk = {
        "crv": "P-256",
        "kty": "EC",
        "x": base.HOLDER_X,
        "y": base.HOLDER_Y,
    }
    issuer_public_jwk = {
        "crv": "P-256",
        "kty": "EC",
        "x": base.ISSUER_X,
        "y": base.ISSUER_Y,
    }
    issuer_payload = {
        "_sd_alg": "sha-256",
        "cnf": {"jwk": holder_public_jwk},
        "exp": base.ISSUED_AT + 31_536_000,
        "family_name": "Example",
        "given_name": "Erika",
        "iat": base.ISSUED_AT,
        "iss": "https://issuer.tyche.test",
        "nbf": base.ISSUED_AT - 60,
        "vct": "urn:tyche:test:person:1",
    }
    issuer_jwt = base.sign_jws(issuer_header, issuer_payload, base.ISSUER_PRIVATE_D)

    def make_presentation(
        current_issuer_jwt: str = issuer_jwt,
        *,
        nonce: str = base.NONCE,
        audience: str = base.AUDIENCE,
        issued_at: int = base.ISSUED_AT,
        damage_kb_signature: bool = False,
    ) -> str:
        hashable = f"{current_issuer_jwt}~"
        kb_jwt = base.sign_jws(
            {"alg": "ES256", "typ": "kb+jwt"},
            {
                "aud": audience,
                "iat": issued_at,
                "nonce": nonce,
                "sd_hash": base.b64url(hashlib.sha256(hashable.encode("ascii")).digest()),
            },
            base.HOLDER_PRIVATE_D,
        )
        if damage_kb_signature:
            kb_jwt = base.mutate_signature(kb_jwt)
        return f"{hashable}{kb_jwt}"

    cases = [
        {
            "case_id": "SCOPE_BASELINE_001",
            "mutation_axis": "none",
            "profile_expected_verdict": "ACCEPT",
            "presentation": make_presentation(),
        },
        {
            "case_id": "SCOPE_ISSUER_SIGNATURE_INVALID_001",
            "mutation_axis": "issuer-signature",
            "profile_expected_verdict": "REJECT",
            "presentation": make_presentation(base.mutate_signature(issuer_jwt)),
        },
        {
            "case_id": "SCOPE_KB_SIGNATURE_INVALID_001",
            "mutation_axis": "key-binding-signature",
            "profile_expected_verdict": "REJECT",
            "presentation": make_presentation(damage_kb_signature=True),
        },
        {
            "case_id": "SCOPE_NONCE_MISMATCH_001",
            "mutation_axis": "nonce",
            "profile_expected_verdict": "REJECT",
            "presentation": make_presentation(nonce="tyche-wrong-nonce-001"),
        },
        {
            "case_id": "SCOPE_AUDIENCE_MISMATCH_001",
            "mutation_axis": "audience",
            "profile_expected_verdict": "REJECT",
            "presentation": make_presentation(audience="https://other-rp.tyche.test"),
        },
        {
            "case_id": "SCOPE_STALE_KB_IAT_001",
            "mutation_axis": "freshness",
            "profile_expected_verdict": "REJECT",
            "presentation": make_presentation(issued_at=base.ISSUED_AT - 600),
        },
    ]
    for case in cases:
        case["presentation_sha256"] = sha256_text(case["presentation"])

    corpus = {
        "schema_version": "0.1.0-research",
        "corpus_id": "urn:tyche:eudi:decision-scope-census:001",
        "format": "dc+sd-jwt",
        "fixed_context": {
            "audience": base.AUDIENCE,
            "evaluated_at": base.EVALUATED_AT,
            "iat_epoch_seconds": base.ISSUED_AT,
            "nonce": base.NONCE,
        },
        "issuer_public_jwk": issuer_public_jwk,
        "cases": cases,
        "excluded_axes": [
            {
                "axis": "disclosure-binding",
                "reason": "cross-project coordinated-disclosure and anonymity hold",
                "gate_file": "../../fcaf-rp-sut-companion/disclosure-binding-hold.md",
            }
        ],
        "claim_boundary": (
            "Synthetic one-property mutations at selected entry points. A result describes the "
            "observed scope at one pinned source/configuration; it is not a deployed-product, "
            "vulnerability, certification or official conformance finding."
        ),
    }
    (HERE / "corpus.json").write_text(
        json.dumps(corpus, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
