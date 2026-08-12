# Decision-scope census v0.1

Status: **local experiment; not published; no official conformance or vulnerability claim**.

This experiment asks a narrower question than product comparison:

> When the exact same synthetic `dc+sd-jwt` presentation reaches each selected pinned entry point,
> which decision dimensions are enforced there, supplied by its caller, bypassed by the test
> configuration, or not representable at that entry point?

The corpus changes one property at a time: issuer signature, key-binding signature, nonce, audience
and key-binding issuance time. It deliberately excludes disclosure binding under
`../../fcaf-rp-sut-companion/disclosure-binding-hold.md`.

The matrix categories are:

- `IN_SCOPE` — the selected entry point itself represents the check;
- `CALLER_SUPPLIED_POLICY` — the entry point calls a predicate supplied by the test/caller;
- `BYPASSED_BY_TEST_CONFIGURATION` — the test deliberately neutralises that layer;
- `NOT_REPRESENTABLE_AT_ENTRY_POINT` — the selected API does not consume the relevant context.

Agreement outside `IN_SCOPE` is recorded but is not counted as an oracle match. This prevents a
caller callback from being mistaken for an implementation default and prevents a signature-only
policy from being labelled defective for not performing presentation-context checks.

Run the deterministic local checks with:

```sh
python3 generate_corpus.py
python3 verify_results.py
sha256sum -c SHA256SUMS
```

The source-pinned execution is performed by `run_census.sh` after setting
`TYCHE_ANDROID_SDK_ROOT`, `ANDROID_SDK_ROOT` or `ANDROID_HOME` to an installed Android SDK. All
executions remain Tyche-controlled unless a receipt explicitly says otherwise under receipt
schema 1.1.
