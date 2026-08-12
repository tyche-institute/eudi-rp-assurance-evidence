# Draft contribution for ARF Topics L and M — lifecycle semantics

Status: **prepared, not posted**

The current L/M paper and TS7 carefully describe the wallet-side event as initiation: the wallet
opens an external browser, email client or phone application and records that initiation, while the
relying party's final handling is outside TS7. That boundary is useful, but it creates an
interoperability risk if a dashboard or exported log presents `initiated` as `sent`, `received`,
`acknowledged` or `completed`.

Would the refinement round consider an explicit lifecycle field with evidence semantics such as:

`INITIATED -> HANDED_OFF -> DELIVERY_CONFIRMED -> ACKNOWLEDGED -> COMPLETED | REFUSED`

Only `INITIATED` is asserted by the wallet action alone. Every later state would require a distinct
evidence reference and named evidence source. This preserves the current external-interface design
while preventing a wallet-generated record from overstating what happened at the relying party or
DPA.

A small synthetic companion corpus exercises three boundaries:

1. reject a selected support endpoint that is not bound to the registered RP contact;
2. reject a record marked `COMPLETED` when its only event is `INITIATED`;
3. reject a report package that embeds a raw credential where bounded RP/request commitments and a
   machine-readable user claim suffice.

The first two are proposed testable consequences of the current contact-source and initiation
language. The third is explicitly a data-minimisation research proposal, not a claim that current
ARF text mandates commitment-only evidence.

Questions for the refinement round:

1. Should the shared log vocabulary distinguish initiation from later externally evidenced states?
2. Should TS7/Topic 19 identify which actor may assert each state and the evidence required?
3. Should a DPA export separate the user's allegation from verifier-generated facts so neither is
   mistaken for a supervisory finding?

The linked packet is synthetic and privacy-minimised. It makes no claim about a named wallet, RP or
DPA and does not decide entitlement to erasure or unlawfulness.

## Publication gate

Post only after the release archive has a stable public URL, all links resolve, and any new
Iteration 5 discussion paper has been diffed against the pinned 2026-08-12 sources. Do not post a
second comment to Topic I; Tyche already contributed there on 2026-07-22.

