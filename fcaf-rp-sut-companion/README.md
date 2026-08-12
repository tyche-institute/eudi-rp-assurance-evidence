# Tyche RP-as-SUT companion seed for EUDIW FCAF

Version: **0.1 research seed**  
Snapshot: **2026-08-12**  
Official FCAF source pin: `7494831a1a9085bb6649c0a2f190e7c32070fcef` (`main`)  
Status: **not submitted; not adopted; not an official FCAF artifact**

## Purpose

The official Functional Conformance Assessment Framework currently identifies the Wallet Solution
as its initial System Under Test. Its methodology also lists Relying Parties as a possible later SUT
and sketches `RelyingParty_WalletSolution (RP_WS)` and related classes.

This directory translates the study's existing 17-rule verifier-assurance profile into
**candidate test objectives** shaped for that future RP-as-SUT space. It is designed to answer a
narrow question:

> What independently rerunnable evidence could a concrete relying-party implementation provide
> for the request, presentation and later-reliance decisions that it actually makes?

## Contents

- `test-objectives-v0.1.csv`: 17 candidate objectives mapped to the research profile and FCAF-style
  SUT/class/layer fields.
- `test-specs/RP_WS_SM_IssuerAuthentication_001.md`: first promoted full
  candidate, backed by one common presentation corpus and three pinned-stack
  provenance receipts.
- `upstream-candidate-001.md`: bounded maintainer discussion draft; not posted.

The inventory remains at Test Objective maturity except for
`RP_WS_SM_IssuerAuthentication_001`, which passed the promotion gate and now
has precise preconditions, ordered test steps, inputs, profiles, pass/fail
criteria and three local pinned-stack executions.

## Promotion gate

A candidate objective becomes a full local test specification only when all of the following exist:

1. a source-pinned requirement or an explicit `research-proposal` label;
2. one valid baseline object and one single-property mutation;
3. a maintained implementation path that natively represents the decision;
4. an observable expected result without guessing from unrelated behaviour;
5. exact source/configuration/input/output hashes and the raw reason;
6. a statement of what the result cannot establish.

The next three promotion candidates are:

1. `RP_WS_SM_RegistrationIdentity_001` — bind registered and authenticated RP identity;
2. `RP_WS_IA_IntendedUse_001` — enforce registered purpose and requested-attribute bounds;
3. `RP_WS_SH_DecisionEvidence_001` — identify the exact verifier/policy/registration decision
   object in a reproducible receipt.

Promoted on 2026-08-12:

- `RP_WS_SM_IssuerAuthentication_001` — common `dc+sd-jwt` baseline and
  issuer-signature mutation; baseline accepted and mutation rejected at the
  pinned EC, Multipaz and walt.id commits. This is executed Tyche research
  evidence, not an official FCAF result.

`R_USE_EXCEEDS_APPROVAL` and `R_LAWFUL_BASIS_UNRECORDED` remain research extensions unless and until
an authoritative EUDI test locus and observable interface are pinned. They must not be presented as
current FCAF requirements.

## Claim boundary

- The identifiers and layer assignments are Tyche candidates, not reserved or assigned FCAF IDs.
- Wallet-side conformance does not establish relying-party conformance or lawful later use.
- Passing a Tyche case is not EUDI, FCAF, ENISA, ETSI or legal conformance.
- Source inspection is not deployed behaviour.
- A named negative implementation finding requires reproduction, triage and appropriate disclosure
  before publication.

## Upstream rule

Do not open a generic “FCAF is missing RP tests” issue. The first upstream contribution should carry
one exact source pin, one complete test specification, one runnable vector, one receipt and one
bounded request for clarification or incorporation.
