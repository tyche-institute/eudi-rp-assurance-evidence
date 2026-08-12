# Validation record — Independent Reproducer Kit v0.2 candidate

- **Date:** 2026-08-12
- **State:** local candidate; not published; independent executions = 0

## Final clean run

The documented one-command interface was executed with a new output directory:

```sh
REPRO_OUTPUT_DIR="$PWD/results/final-clean-validation-2026-08-12" \
  ./run-one-command.sh
```

The wrapper rebuilt the Docker image, cloned both public upstream source trees at the exact pins,
ran the two selected JVM entry points and verified the completed return package.

| Check | Recorded result |
|---|---|
| Return status | `PASS_RETURN_COMPLETE_NO_IN_SCOPE_MISMATCH` |
| Adapters | `eudi-official`, `waltid` |
| Observations | 12 |
| In-scope mismatches | 0 |
| Independent run package | `false` |
| Android SDK used | `false` |
| Corpus SHA-256 | `30fab5ed86987c156480ce6f64b5f5fa7a489b289406fdaaab7178252ab661d9` |
| Final image ID | `sha256:34d5c0307661638fb3afa70698ea25d8eb81dbd4345b88b78f0ecc73d75b6d44` |
| Pinned base image | `eclipse-temurin@sha256:55fb9bf738f5d9b4a6c01b39337e3070d3e27370dd3c478fd1d5d3cd2233c6d8` |

Every item in `RETURN-SHA256SUMS` passed, including the environment manifest, raw clone and test
logs, raw JUnit XML, both schema-1.1 receipts, summary and image ID.

## Verifier semantics

`test-verifier-semantics.py` ran three temporary cases against the final return:

1. the untouched return validated;
2. a byte appended to a hashed raw evidence file was rejected fail-closed;
3. a synthetic in-scope disagreement, made consistent across raw XML, receipt and summary, was
   accepted and labelled `PASS_RETURN_COMPLETE_WITH_IN_SCOPE_MISMATCH`.

The temporary tamper and disagreement copies were deleted automatically. No synthetic finding was
retained in the evidence directory.

## Claim boundary

This proves that the kit can produce and validate a complete return without Android SDK and can
preserve a contradictory observation. It does not make the Tyche-controlled reference run
independent, certify either upstream project, cover a complete relying-party flow or establish
corpus completeness.
