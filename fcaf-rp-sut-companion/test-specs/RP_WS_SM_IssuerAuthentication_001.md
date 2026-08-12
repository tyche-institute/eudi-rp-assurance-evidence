# RP_WS_SM_IssuerAuthentication_001 — reject an invalid issuer signature

Status: **Tyche research proposal; executed locally; not adopted by FCAF**  
Specification version: **0.1.0, 2026-08-12**  
Proposed SUT: **Relying Party**  
Proposed test class/layer/area: **RP_WS / SM / IssuerAuthentication**

## 1. Test case identifier

- **Test case ID:** `RP_WS_SM_IssuerAuthentication_001`
- **Naming note:** candidate identifier following the current FCAF hierarchy. It
  is not allocated or reserved by the FCAF project.

## 2. Objective

Confirm that a Relying Party validating a `dc+sd-jwt` presentation accepts a
valid issuer-signed baseline, rejects the otherwise identical presentation
when the issuer-JWS signature is invalid, and does not expose the processed
credential payload to the relying application after that failure.

## 3. References

- [FCAF methodology and candidate RP SUT/class hierarchy](https://github.com/eu-digital-identity-wallet/eudi-doc-functional-conformance-assessment/blob/7494831a1a9085bb6649c0a2f190e7c32070fcef/docs/fcaf/index.md)
- [FCAF test-specification template](https://github.com/eu-digital-identity-wallet/eudi-doc-functional-conformance-assessment/blob/7494831a1a9085bb6649c0a2f190e7c32070fcef/docs/fcaf/templates/test-spec-template.md)
- [RFC 9901 §7.1, verification of the SD-JWT](https://www.rfc-editor.org/rfc/rfc9901.html#section-7.1)
- [RFC 9901 §7.3, verification by the Verifier](https://www.rfc-editor.org/rfc/rfc9901.html#section-7.3)
- [RFC 9901 §9.1, mandatory issuer signature verification](https://www.rfc-editor.org/rfc/rfc9901.html#section-9.1)

The testable requirement is the verifier-side rejection of an issuer-signed
JWT whose signature cannot be verified. This case does not test issuer trust,
certificate-path validation, status, business authorization or lawful use.

## 4. EUDI-wallet relevancy

- **Origin label:** `EUDI_generic`
- **Scope label:** `EUDI_required`
- **Rationale:** issuer authentication is a general SD-JWT integrity
  requirement and is relevant whenever an EUDI relying party accepts this
  format.

## 5. Profile applicability

Applicable when all of the following are true:

- the Relying Party supports compact `dc+sd-jwt` presentations;
- `ES256` is allowed for the test profile;
- the test harness can supply a fixed issuer key/trust input and fixed
  nonce/audience/time context;
- the Relying Party exposes an observable accept/reject result before claims
  are released to business logic.

Mark **Not Applicable** when `dc+sd-jwt` or `ES256` is outside the declared IUT
profile. Lack of a test hook is not evidence of a pass.

## 6. Preconditions

1. Regenerate `common-presentation-corpus/corpus.json` with
   `generate_fixture.py`; `sha256sum -c SHA256SUMS` succeeds.
2. Pin the IUT source/binary version, dependency material, policy
   configuration and build command.
3. Configure only the synthetic test issuer from the corpus as acceptable for
   issuer-signature evaluation. Do not reuse this key or certificate in
   production.
4. Fix the context to:
   - evaluation time `2026-08-12T08:00:05Z`;
   - nonce `tyche-common-nonce-001`;
   - audience `https://rp.tyche.test`.
5. The baseline and mutation are the exact compact strings in the corpus. The
   harness must not reissue, normalize or reconstruct them.
6. The mutation changes the first base64url character of the issuer-JWS
   signature. The `sd_hash` is recomputed and the KB-JWT is re-signed so holder
   binding, nonce and audience remain valid.

## 7. Test scenario

| Step | Description | Inputs/configuration |
|---|---|---|
| 1 | Verify corpus integrity and load the fixed evaluation context. | `corpus.json`, `SHA256SUMS` |
| 2 | Submit the complete baseline presentation to the normal issuer-signature validation path. | `COMMON-SDJWT-BASELINE-001` |
| 3 | Submit the complete issuer-signature mutation through the same path without changing policy, trust, time, nonce or audience. | `RP_WS_SM_IssuerAuthentication_001` |
| 4 | Emit a decision-provenance receipt that binds the input, source, dependencies, configuration, trust material, fixed context, raw reason and evidence hashes. | `decision-provenance-receipt.schema.json` |

## 8. Expected results

| Step | Pass criterion |
|---|---|
| 1 | Corpus checksum succeeds and the test harness reports the pinned configuration. |
| 2 | Baseline verdict is `ACCEPT`; the processed payload has `vct = urn:tyche:test:person:1`. |
| 3 | Mutation verdict is `REJECT`; the observable reason denotes issuer-signature failure; no processed credential payload is made available to relying business logic. |
| 4 | The receipt validates against the schema and every recorded evidence hash resolves. |

The overall verdict is **Pass** only if every step passes. An unparseable
mutation, a key-binding failure, a nonce/audience failure, or a trust-policy
failure is not a pass for this test objective because it does not isolate the
issuer signature.

## Executed research evidence

| Pinned stack | Baseline | Mutation | Raw reason |
|---|---|---|---|
| EC EUDI verifier endpoint `db544250…` | ACCEPT | REJECT | `ContainsInvalidJwt` |
| Multipaz `570aa247…` | ACCEPT | REJECT | `SignatureVerificationException: Error validating issuer signature` |
| walt.id `f773918a…` | ACCEPT | REJECT | `InvalidJwsSignatureException: Invalid JWS signature` |

All three rows use the same compact presentations and have a schema-validated
receipt under `real-stack-adapters/results/common-presentation-provenance/`.

## Claim boundary

The executions are Tyche-controlled tests of pinned maintained source. They
are not independently reproduced, do not exercise a complete deployed RP
service or all OpenID4VP processing, and do not establish product, EUDIW or
FCAF conformance. The current official FCAF designates Wallet Solution as the
initial SUT; this is a concrete proposal for a possible future RP-as-SUT suite.
