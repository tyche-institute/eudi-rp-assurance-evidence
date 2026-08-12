#!/usr/bin/env python3
"""Generate a deterministic, standards-shaped SD-JWT+KB comparison corpus."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path

from ecdsa import NIST256p, SigningKey
from ecdsa.util import sigencode_string


HERE = Path(__file__).resolve().parent

ISSUER_PRIVATE_D = "KJ4k3Vcl5Sj9Mfq4rrNXBm2MoPoY3_Ak_PIR_EgsFhQ"
ISSUER_X = "G0RINBiF-oQUD3d5DGnegQuXenI29JDaMGoMvioKRBM"
ISSUER_Y = "ed3eFGs2pEtrp7vAZ7BLcbrUtpKkYWAT2JPUQK4lN4E"
ISSUER_X5C = (
    "MIIBeTCCAR8CFHrWgrGl5KdefSvRQhR+aoqdf48+MAoGCCqGSM49BAMCMBcxFTATBgNVBAMM"
    "DE1ET0MgUk9PVCBDQTAgFw0yNTA1MTQxNDA4MDlaGA8yMDc1MDUwMjE0MDgwOVowZTELMAkG"
    "A1UEBhMCQVQxDzANBgNVBAgMBlZpZW5uYTEPMA0GA1UEBwwGVmllbm5hMRAwDgYDVQQKDAd3"
    "YWx0LmlkMRAwDgYDVQQLDAd3YWx0LmlkMRAwDgYDVQQDDAd3YWx0LmlzMFkwEwYHKoZIzj0C"
    "AQYIKoZIzj0DAQcDQgAEG0RINBiF+oQUD3d5DGnegQuXenI29JDaMGoMvioKRBN53d4UazakS"
    "2unu8BnsEtxutS2kqRhYBPYk9RAriU3gTAKBggqhkjOPQQDAgNIADBFAiAOMwM7hH7q9Di+"
    "mT6qCi4LvB+kH8OxMheIrZ2eRPxtDQIhALHzTxwvN8Udt0Z2Cpo8JBihqacfeXkIxVAO8Xkx"
    "mXhB"
)

HOLDER_PRIVATE_D = "QN9Y3k_3Hy2OV0C5Pmez_ObEXJKcXonnMg3xTpcLOAg"
HOLDER_X = "eTT2WdzlmOWBItdgSmsqB1_BP69wfuwOe1IYvaY1WdI"
HOLDER_Y = "wbOu3GP02JiOVIRQ_ufWLRNOmDB6seYAabCmsGBfr_4"

ISSUED_AT = 1_786_521_600  # 2026-08-12T08:00:00Z
EVALUATED_AT = "2026-08-12T08:00:05Z"
NONCE = "tyche-common-nonce-001"
AUDIENCE = "https://rp.tyche.test"


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def decode_b64url(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def compact_json(value: object) -> bytes:
    return json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")


def sign_jws(header: dict, payload: dict, private_d: str) -> str:
    encoded_header = b64url(compact_json(header))
    encoded_payload = b64url(compact_json(payload))
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")
    key = SigningKey.from_string(decode_b64url(private_d), curve=NIST256p)
    signature = key.sign_deterministic(
        signing_input,
        hashfunc=hashlib.sha256,
        sigencode=sigencode_string,
    )
    return f"{encoded_header}.{encoded_payload}.{b64url(signature)}"


def mutate_signature(jwt: str) -> str:
    header, payload, signature = jwt.split(".")
    replacement = "A" if signature[0] != "A" else "B"
    return f"{header}.{payload}.{replacement}{signature[1:]}"


def presentation(issuer_jwt: str) -> str:
    hashable = f"{issuer_jwt}~"
    kb_jwt = sign_jws(
        {"alg": "ES256", "typ": "kb+jwt"},
        {
            "aud": AUDIENCE,
            "iat": ISSUED_AT,
            "nonce": NONCE,
            "sd_hash": b64url(hashlib.sha256(hashable.encode("ascii")).digest()),
        },
        HOLDER_PRIVATE_D,
    )
    return f"{hashable}{kb_jwt}"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def main() -> None:
    issuer_header = {"alg": "ES256", "typ": "dc+sd-jwt", "x5c": [ISSUER_X5C]}
    holder_public_jwk = {
        "crv": "P-256",
        "kty": "EC",
        "x": HOLDER_X,
        "y": HOLDER_Y,
    }
    issuer_public_jwk = {
        "crv": "P-256",
        "kty": "EC",
        "x": ISSUER_X,
        "y": ISSUER_Y,
    }
    issuer_payload = {
        "_sd_alg": "sha-256",
        "cnf": {"jwk": holder_public_jwk},
        "exp": ISSUED_AT + 31_536_000,
        "family_name": "Example",
        "given_name": "Erika",
        "iat": ISSUED_AT,
        "iss": "https://issuer.tyche.test",
        "nbf": ISSUED_AT - 60,
        "vct": "urn:tyche:test:person:1",
    }
    baseline_issuer_jwt = sign_jws(issuer_header, issuer_payload, ISSUER_PRIVATE_D)
    invalid_issuer_jwt = mutate_signature(baseline_issuer_jwt)
    baseline = presentation(baseline_issuer_jwt)
    invalid = presentation(invalid_issuer_jwt)

    corpus = {
        "schema_version": "1.0.0-research",
        "corpus_id": "urn:tyche:eudi:common-sdjwt-presentation:001",
        "format": "dc+sd-jwt",
        "fixed_context": {
            "audience": AUDIENCE,
            "evaluated_at": EVALUATED_AT,
            "iat_epoch_seconds": ISSUED_AT,
            "nonce": NONCE,
        },
        "issuer_public_jwk": issuer_public_jwk,
        "cases": [
            {
                "case_id": "COMMON-SDJWT-BASELINE-001",
                "expected_verdict": "ACCEPT",
                "mutation": "none",
                "presentation": baseline,
                "presentation_sha256": sha256_text(baseline),
            },
            {
                "case_id": "RP_WS_SM_IssuerAuthentication_001",
                "expected_verdict": "REJECT",
                "expected_reason": "invalid_issuer_signature",
                "mutation": (
                    "first base64url character of the issuer-JWS signature changed; "
                    "key-binding sd_hash recomputed and KB-JWT re-signed"
                ),
                "presentation": invalid,
                "presentation_sha256": sha256_text(invalid),
            },
        ],
        "claim_boundary": (
            "Synthetic non-production credential. The mutation isolates issuer-signature validity "
            "while preserving parsing, audience, nonce, evaluation time, holder key and key binding."
        ),
    }
    corpus_path = HERE / "corpus.json"
    corpus_path.write_text(
        json.dumps(corpus, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (HERE / "SHA256SUMS").write_text(
        f"{hashlib.sha256(corpus_path.read_bytes()).hexdigest()}  corpus.json\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
