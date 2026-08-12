# Independent Reproducer Kit v0.2

Status: **released in evidence packet v0.2.0; independent executions remain zero**.

This kit turns the decision-scope experiment into a low-friction return path for independently
controlled evidence. It runs two pinned JVM verifier entry points in a clean container without an
Android SDK:

- EC EUDI verifier endpoint `SdJwtVcValidator.validate` at
  `db5442501ea06907e614377a20d802748e8bfddb`;
- walt.id `CredentialSignaturePolicy.verify` at
  `f773918a3ad226ba7c0908d58941f18a3b89591d`.

The six compact inputs differ one property at a time: baseline, issuer signature, KB signature,
nonce, audience and KB issuance time. Disclosure binding is excluded by the cross-project hold.

The final release-image clean run and verifier-semantic checks are recorded in `VALIDATION.md`.

## One command

From this directory:

```sh
./run-one-command.sh
```

The wrapper builds the checksum-pinned JDK 21 container and writes a new timestamped return
directory under `results/`. It refuses to overwrite an existing return directory. The first run
downloads the two pinned public source trees and their Gradle dependencies.

An independent controller may provide disclosed non-secret labels:

```sh
REPRO_CONTROL=independent-third-party-run \
REPRO_INDEPENDENT=true \
REPRO_CONTROLLER_ID='organisation-or-pseudonymous-lab-id' \
REPRO_RELATIONSHIP='no affiliation with Tyche; independently controlled execution' \
./run-one-command.sh
```

These labels are assertions inside the receipt. They make independence representable; they do not
prove independence by themselves. A paper-level independence claim still requires provenance and
reasonable validation of the controller relationship.

## Return contents

Each completed run returns:

- exact source pins and source-tree hashes;
- environment and dependency manifests;
- raw clone/build/test logs;
- twelve observations across two selected entry points;
- two decision-provenance receipts under schema 1.1;
- a machine-readable summary and `RETURN-SHA256SUMS`.

`verify-return.sh PATH` validates an existing return without rerunning the source builds. It checks
the schema, pins, corpus, evidence hashes, controller consistency, observation completeness and
oracle-comparison semantics. An oracle mismatch remains a valid recorded observation; it is not
rejected merely for disagreeing.

For a voluntarily supplied result, follow `INDEPENDENT-RETURN-INTAKE.md`: technical validity,
independence provenance and permission for public use are three separate decisions.

## Why two paths

The Multipaz JVM route remains in the broader packet, but the pinned repository configures Android
projects during JVM task discovery. Omitting it here is deliberate: this kit tests whether a
meaningful independent return can be obtained without requiring an Android SDK. It makes no claim
that two paths represent the whole ecosystem.

## Claim boundary

- A clean Tyche container run remains Tyche-controlled, not independent.
- The selected entry points do not have identical decision scope.
- ACCEPT outside a represented scope is not an implementation failure.
- The kit is not certification, conformance, a deployed RP workflow or a vulnerability scanner.
- No participant, survey, contact, production credential or held disclosure reproducer is included.
