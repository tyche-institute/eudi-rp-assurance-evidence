# EUDI RP Assurance Evidence

Executable research artifacts for asking a question that wallet conformance alone cannot answer:

> Which relying-party verifier, policy, registration and evidence actually produced the decision?

## Result at this release

One deterministic `dc+sd-jwt` baseline and one isolated invalid-issuer-signature mutation were
supplied as the exact same compact presentations to three pinned maintained-source paths:

| Implementation path | Pinned commit | Baseline | Mutation |
|---|---|---:|---:|
| EC EUDI verifier endpoint | `db5442501ea06907e614377a20d802748e8bfddb` | ACCEPT | REJECT |
| OpenWallet Foundation Multipaz | `570aa2475bd5b7e437d9041bf8ff1127bcf86cfb` | ACCEPT | REJECT |
| walt.id | `f773918a3ad226ba7c0908d58941f18a3b89591d` | ACCEPT | REJECT |

The corpus SHA-256 is
`4cc80a8468dd11561d4c4e6146a278fb4f6e98fe74ab8d65fc8c961eacfe80f5`.
All three executions were controlled by Tyche. They are not independent reproductions, deployed
RP tests, product certifications or EUDIW/FCAF conformance results.

## What is included

- `real-stack-adapters/` — deterministic corpus, exact adapter tests, clean-clone runner, raw logs
  and three decision-provenance receipts;
- `fcaf-rp-sut-companion/` — 17 candidate RP-as-SUT objectives and the first complete FCAF-shaped
  research test specification;
- `assurance-graph/` — a 54-node, 76-edge deterministic graph joining sources, research rules,
  objectives, the test, corpus, implementations and receipts;
- `arf-iteration-5-companion/` — synthetic lifecycle receipts and three negative vectors for ARF
  Topics L/M;
- `engagement/rp-programme-travel-mobility/` — a one-page, plain-language travel and mobility
  field packet plus canonical structured cards.

## Fast verification

Requires Python 3 and `jsonschema`:

```sh
python3 verify_release.py
```

This checks the release manifest, regenerates and validates the Assurance Graph, executes the ARF
L/M research oracle, and validates the common-presentation provenance packet.

To rerun the three external source builds, install Git, curl, unzip, a compatible JDK and an Android
SDK location (or allow the checksum-pinned command-line-tools bootstrap), then run:

```sh
TYCHE_ANDROID_SDK_ROOT=/path/to/android-sdk \
  ./real-stack-adapters/tools/run_common_presentation_probe.sh
```

The external build is intentionally not part of the fast verification path.

## Claim and privacy boundary

- Candidate RP identifiers are not reserved or adopted FCAF IDs.
- Research rules and lifecycle semantics are not represented as current legal or official
  requirements.
- A receipt records evidence and assertions; it does not establish lawfulness.
- No participant, survey, traveller, booking, contact-list or production-credential data are in
  this release.
- The synthetic signing key and certificate are test material and must never be trusted in
  production.

## Sources

- [FCAF methodology](https://github.com/eu-digital-identity-wallet/eudi-doc-functional-conformance-assessment/blob/7494831a1a9085bb6649c0a2f190e7c32070fcef/docs/fcaf/index.md)
- [RFC 9901](https://www.rfc-editor.org/rfc/rfc9901.html)
- [ARF Topics L/M](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/blob/6373eee10b6e80225c7ce706a5ff1775fb799b22/docs/discussion-topics/l%2Bm-data-deletion-and-reporting-of-wrp-to-dpa.md)
- [TS7 data-deletion interface](https://github.com/eu-digital-identity-wallet/eudi-doc-standards-and-technical-specifications/blob/bdc9780224bf4fb07ae7ddc11a2a6962e4536442/docs/technical-specifications/ts7-common-interface-for-data-deletion-request.md)

## Upstream use

- [FCAF issue #50](https://github.com/eu-digital-identity-wallet/eudi-doc-functional-conformance-assessment/issues/50) asks three bounded questions about the first RP-as-SUT case.
- [ARF Topic L comment](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/discussions/691#discussioncomment-17986586) proposes evidence-bearing deletion-request lifecycle states.
- [ARF Topic M comment](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/discussions/692#discussioncomment-17986587) separates user allegations, verifier facts and later DPA findings.
- Topic I was not reposted: Tyche's earlier bounded-mandate contribution remains the canonical comment there.

## License and citation

Tyche-authored material is released under the MIT License; see `LICENSE`. Pinned upstream projects
and limited derived test/build material are identified in `THIRD_PARTY-NOTICES.md`. Citation
metadata are in `CITATION.cff`.
