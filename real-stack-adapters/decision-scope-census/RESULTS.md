# Decision-scope census v0.1 — results

- **Executed:** 2026-08-12
- **Corpus SHA-256:** `30fab5ed86987c156480ce6f64b5f5fa7a489b289406fdaaab7178252ab661d9`
- **Source pins:** unchanged from the common-presentation experiment
- **Execution control:** Tyche-controlled
- **Independent executions:** 0
- **Disclosure binding:** excluded under the recorded hold

## Result

Eighteen observations were recorded across three selected entry points and six exact compact
presentations. Eleven observations were in the represented decision scope, three were enforced by
caller-supplied predicates, and four were not representable at the selected entry point. Every
in-scope observation matched the profile oracle. Observations outside scope were recorded without
being counted as oracle matches or implementation failures.

| Mutation axis | EC `SdJwtVcValidator.validate` | Multipaz `SdJwtKb.verify` | walt.id `CredentialSignaturePolicy.verify` |
|---|---|---|---|
| none | ACCEPT — in scope | ACCEPT — in scope | ACCEPT — in scope |
| issuer signature | REJECT — in scope | REJECT — in scope | REJECT — in scope |
| key-binding signature | REJECT — in scope | REJECT — in scope | ACCEPT — not representable at this entry point |
| nonce | REJECT — in scope | REJECT — caller predicate | ACCEPT — not representable at this entry point |
| audience | REJECT — in scope | REJECT — caller predicate | ACCEPT — not representable at this entry point |
| KB issuance time | REJECT — in scope | REJECT — caller predicate | ACCEPT — not representable at this entry point |

## Raw-reason observation

The selected EC path returned `ContainsInvalidKeyBindingJwt` for all four KB/context mutations. The
selected Multipaz path returned distinct messages for KB signature, nonce, audience and creation
time. The selected walt.id signature policy returned no failure for the four inputs outside its
represented scope. This is an entry-point reason-granularity observation, not a ranking of products.

## Interpretation

The original exact-object 3/3 result establishes a common issuer-signature lower bound. This census
adds the missing distinction between:

1. a check enforced by the selected implementation entry point;
2. a check whose decision is supplied by its caller; and
3. a property that the selected entry point does not consume.

It would be incorrect to say that walt.id “failed” nonce, audience, freshness or KB-signature tests:
the selected `CredentialSignaturePolicy` is a credential-signature policy, not the complete
presentation-context verifier. Likewise, the Multipaz rejections for nonce, audience and creation
time demonstrate that its callback surface was invoked with the study predicates, not that those
particular policies are hard-coded defaults.

## Claim boundary

- This is a selected-entry-point census, not a whole-product comparison.
- Trust resolution was not compared: the EC test neutralised it, Multipaz received an issuer key,
  and the walt.id policy resolved signature material through its parsed credential path.
- The fixtures are synthetic and the runs are Tyche-controlled.
- No deployment, certification, vulnerability, EUDIW conformance or FCAF adoption is claimed.
- No disclosure-binding result is present.

Machine-readable observations and v1.1 receipts are under `results/`.
