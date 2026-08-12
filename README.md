# EUDI RP Assurance Evidence v0.2.0-rc1

Status: **public draft release candidate; not tagged or released**.

This packet makes relying-party decision scope and independently controlled
reproduction first-class evidence. It extends the immutable public v0.1.2
packet without changing its recorded files or claims.

## New evidence in this candidate

| Component | Recorded result | Boundary |
|---|---:|---|
| Receipt schema 1.1 candidate | independent control and oracle disagreement are representable | a receipt records provenance assertions; it does not prove independence |
| Decision-scope census | 18 observations; 11 in scope; 3 caller-supplied; 4 not representable | selected pinned entry points, not whole products |
| Independent Reproducer Kit | one Docker command; 2 pinned JVM paths; 12 observations; no Android SDK | included reference run is Tyche-controlled, not independent |
| Verifier semantic self-test | evidence tamper rejected; evidence-consistent disagreement accepted | synthetic self-test is deleted after execution |
| Mutation analysis | 51/51 valid rule-omission mutants killed | sensitivity to one declared operator, not completeness |

The six-case decision-scope corpus SHA-256 is
`30fab5ed86987c156480ce6f64b5f5fa7a489b289406fdaaab7178252ab661d9`.

## Fast verification

Requires Python 3 and `jsonschema`:

```sh
python3 verify_release.py
```

This verifies every file hash, the v0.1.2 components, schema 1.1 fixtures,
the three-path decision-scope census, mutation-analysis results, the
Tyche-controlled reference return, fail-closed tamper handling, disagreement
handling and the privacy boundary.

## One-command independent return

Requires Docker and network access for the two pinned public source trees:

```sh
cd real-stack-adapters/independent-reproducer-v0.2-candidate
REPRO_CONTROL=independent-third-party-run \
REPRO_INDEPENDENT=true \
REPRO_CONTROLLER_ID='organisation-or-pseudonymous-lab-id' \
REPRO_RELATIONSHIP='no affiliation with Tyche; independently controlled execution' \
./run-one-command.sh
```

The return contains exact source pins, source-tree hashes, environment and
dependency manifests, raw logs/XML, two schema-1.1 receipts, a summary and a
SHA-256 manifest. An in-scope disagreement is preserved as a valid scientific
result and is labelled explicitly; it is not converted into a failed package.

## Recorded reference validation

- Final local image ID:
  `sha256:34d5c0307661638fb3afa70698ea25d8eb81dbd4345b88b78f0ecc73d75b6d44`.
- Base image:
  `eclipse-temurin@sha256:55fb9bf738f5d9b4a6c01b39337e3070d3e27370dd3c478fd1d5d3cd2233c6d8`.
- Pinned EC verifier endpoint commit:
  `db5442501ea06907e614377a20d802748e8bfddb`.
- Pinned walt.id commit:
  `f773918a3ad226ba7c0908d58941f18a3b89591d`.
- Result: `PASS_RETURN_COMPLETE_NO_IN_SCOPE_MISMATCH`, 12 observations,
  `independent_run_package=false`, `android_sdk_used=false`.

## Claim and privacy boundary

- Independent executions recorded in this candidate: **0**.
- The reference run proves that the return mechanism works; it is not an
  independent reproduction.
- The selected entry points do not have identical decision scope. ACCEPT
  outside represented scope is not an implementation defect.
- The packet is not certification, conformance, a production RP workflow or
  a vulnerability scanner.
- No participant, respondent, contact-list, professional-email, survey,
  production credential or held disclosure reproducer is included.
- The synthetic keys, certificates and credentials are test material and
  must never be trusted in production.

## Licence and third-party material

Tyche-authored material is under the MIT License. Limited test/build material
interoperates with the pinned Apache-2.0 upstream projects identified in
`THIRD_PARTY-NOTICES.md`; those projects do not endorse this packet or result.
