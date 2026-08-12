# ARF Iteration 5 companion — lifecycle evidence for Topics L and M

Version: **0.1 research proposal, 2026-08-12**

This packet turns one ambiguity in the current Topic L/M material into three executable research
vectors: a wallet can prove that it initiated a deletion request or DPA report, but initiation must
not be displayed or exported as proof that the external recipient received, acknowledged or
completed it.

The current official material deliberately reuses external browser, email and phone interfaces.
TS7 therefore puts final handling by the relying party outside its scope, while `DATA_DLT_06` and
`RPT_DPA_05` record initiation. This companion proposes an explicit lifecycle state plus a separate
evidence basis so later states cannot be inferred from initiation alone.

## Executable corpus

`lifecycle-vectors.json` contains two valid synthetic baselines and three single-purpose negative
mutations:

1. `L_CONTACT_NOT_REGISTRATION_BOUND_001` — selected support endpoint differs from the registered
   endpoint commitment;
2. `LM_INITIATED_REPRESENTED_AS_COMPLETED_001` — the record claims completion with only initiation
   evidence and no successful requester authentication;
3. `M_REPORT_EVIDENCE_OVER_COLLECTION_001` — a DPA report embeds a raw credential where the profile
   permits only bounded commitments and a machine-readable claim.

Run:

```sh
python3 verify_vectors.py
sha256sum -c SHA256SUMS
```

The first two cases isolate current technical/accountability boundaries. The third is a Tyche
data-minimisation proposal, not a quoted ARF requirement. All data are synthetic. The packet does
not decide whether a deletion request is legally valid, whether erasure is required, or whether a
relying party acted unlawfully.

## Upstream state

The official refinement discussions already exist:

- [Topic L discussion 691](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/discussions/691)
- [Topic M discussion 692](https://github.com/eu-digital-identity-wallet/eudi-doc-architecture-and-reference-framework/discussions/692)

`upstream-candidate-lm.md` is ready but not posted. Publication requires a stable public artifact
URL and a final comparison against any new Iteration 5 paper.

