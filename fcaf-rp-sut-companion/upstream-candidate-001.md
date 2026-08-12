# Upstream candidate: one concrete RP-as-SUT issuer-authentication case

Status: **posted 2026-08-12 as [FCAF issue #50](https://github.com/eu-digital-identity-wallet/eudi-doc-functional-conformance-assessment/issues/50)**

Public evidence baseline: `tyche-institute/eudi-rp-assurance-evidence` tag `v0.1.0`

The issue itself is the canonical public text; the internal submission record retains the exact administrative copy.

Proposed title: **Discussion: concrete RP-as-SUT test case for invalid SD-JWT issuer signature**

## Draft issue body

The current FCAF methodology names Relying Parties as a possible future SUT
and sketches the `RelyingParty_WalletSolution (RP_WS)` class, while correctly
limiting the initial phase to Wallet Solutions. Would maintainers welcome a
small, evidence-backed RP-as-SUT companion track beginning with the attached
issuer-authentication case?

The proposed `RP_WS_SM_IssuerAuthentication_001` follows the current test-case
template and tests one requirement only: a verifier rejects a `dc+sd-jwt`
presentation when the issuer-JWS signature cannot be verified.

Evidence package:

- one deterministic baseline presentation;
- one single-property issuer-signature mutation;
- the exact same compact objects executed at pinned commits of the EC EUDI
  verifier endpoint, Multipaz and walt.id;
- baseline `ACCEPT` and mutation `REJECT` on all three;
- raw stack-specific reasons plus source, dependency, policy, trust, time,
  input and evidence hashes in schema-validated provenance receipts.

Bounded questions:

1. Is `RP_WS_SM_IssuerAuthentication_001` consistent with the intended future
   RP SUT hierarchy and naming convention?
2. Is a research companion directory or discussion issue the preferred way to
   contribute an executable RP case before RP is activated as an FCAF SUT?
3. Should the expected result explicitly require that no processed credential
   payload reaches relying application logic after issuer-signature failure?

This is not presented as an adopted FCAF case or as conformance evidence. The
three executions are Tyche-controlled, not independent reproductions. The
full test specification and reproducible runner are available in the linked
packet.

## Publication gate — passed

The issue was posted only after the public repository and immutable `v0.1.0`
release were available and the privacy-minimised archive passed clean-extraction
verification. No live survey roster, response, personal data or private
correspondence was attached.
