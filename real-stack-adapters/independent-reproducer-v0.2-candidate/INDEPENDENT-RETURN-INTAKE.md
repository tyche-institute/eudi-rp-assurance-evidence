# Independent return intake checklist

Use this checklist only after a controller voluntarily supplies a return directory. Do not alter
the supplied files and do not treat a self-selected controller label as proof by itself.

## 1. Preserve the received object

- Copy the return into a new read-only intake location.
- Record the transport date, transport method and SHA-256 of `RETURN-SHA256SUMS`.
- Do not overwrite the included controller, environment, logs, receipts or summary.
- Keep any private correspondence outside a public artifact tree.

## 2. Verify technical completeness

From this kit directory:

```sh
./verify-return.sh /path/to/received-return
```

The package is technically complete only if schema validation, exact pins, raw-XML/receipt
consistency, evidence hashes, corpus coverage, controller consistency and the return manifest all
pass. A labelled `WITH_IN_SCOPE_MISMATCH` result is technically complete; scientific disagreement
is not a checksum failure.

## 3. Classify control separately

Record two different decisions:

1. **technical package validity** — established by the verifier;
2. **independence provenance** — supported by credible evidence that Tyche did not control the
   environment or execution.

For independence, check that both receipts consistently state an independent controller class and
`independent_of_tyche=true`, then assess the disclosed controller identifier and relationship.
An organisation or stable pseudonymous lab identifier is sufficient; a personal name or email is
not required. If the relationship cannot reasonably be assessed, label the package
`independence-unverified` even when it is technically valid.

## 4. Review a disagreement without erasing it

- Preserve the original return unchanged.
- Reproduce the comparison from raw XML, receipt and corpus.
- Distinguish `IN_SCOPE` from caller-supplied or non-representable dimensions.
- Open a new analysis note for any explanation; never edit the returned verdict to match Tyche's
  oracle.
- Do not call an observation a product defect, vulnerability or conformance failure without a
  separately justified claim path.

## 5. Public-use gate

Before including a return in a release or paper, confirm that the controller permits the intended
level of attribution and evidence disclosure, and run a privacy/secret scan. Otherwise report only
the technically defensible aggregate state or keep the return private. Receipt validity alone is
not publication permission.
