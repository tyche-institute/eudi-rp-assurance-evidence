# Decision-provenance receipt schema 1.1 candidate

Status: **local research candidate; not published; not evidence of another execution**.

This candidate repairs a structural limitation found in receipt schema 1.0. The published schema
hard-codes Tyche control, an accepting baseline, a rejecting mutation and one normalized reason.
That makes its three existing receipts easy to validate, but prevents the same format from recording
an independently controlled run, an error, an indeterminate decision or disagreement with the
research oracle.

Schema 1.1 therefore separates:

- the research oracle from the observed verdict;
- the entry point from the implementation identity;
- checks exercised from checks bypassed or supplied by the caller;
- execution controller from evidence custodian;
- production-source status from build-isolation material; and
- a normalized reason category from the implementation's raw reason.

It does not replace or mutate schema 1.0. Existing receipts remain immutable and validate only
against `../decision-provenance-receipt.schema.json`.

## Files

- `decision-provenance-receipt-1.1.schema.json` — candidate JSON Schema;
- `fixtures/tyche-match.schema-example.json` — a non-evidentiary matching example;
- `fixtures/independent-disagreement.schema-example.json` — proves that independent disagreement is
  representable rather than rejected by construction;
- `verify_schema.py` — schema and semantic self-test;
- `SHA256SUMS` — local integrity manifest.

Run:

```sh
python3 verify_schema.py
sha256sum -c SHA256SUMS
```

The fixtures are schema examples only. They are not executions, receipts, implementation findings
or evidence that an independent reproducer exists.
