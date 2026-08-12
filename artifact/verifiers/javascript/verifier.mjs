#!/usr/bin/env node
import fs from "node:fs";

const IMPLEMENTATION = "javascript-functional/0.1.0";
const corpus = JSON.parse(fs.readFileSync(0, "utf8"));
const subset = (left, right) => left.every((item) => right.includes(item));

function evaluate(tx) {
  const { rp, presentation: p, reliance: r } = tx;
  const age = p.evaluated_at_epoch - p.issued_at;
  const rules = [
    [!p.parse_ok, "R_PARSE_INVALID"],
    [!rp.registered, "R_RP_UNREGISTERED"],
    [rp.registration_status !== "active", "R_RP_SUSPENDED"],
    [rp.authenticated_rp_id !== rp.registered_rp_id, "R_RP_IDENTITY_MISMATCH"],
    [!rp.registered_purposes.includes(rp.transaction_purpose), "R_PURPOSE_MISMATCH"],
    [!subset(rp.requested_attributes, rp.registered_attributes), "R_ATTRIBUTE_OVER_REQUEST"],
    [!p.issuer_signature_valid, "R_ISSUER_SIGNATURE_INVALID"],
    [!p.all_disclosures_bound, "R_DISCLOSURE_UNBOUND"],
    [!p.holder_binding_valid, "R_HOLDER_BINDING_INVALID"],
    [p.audience !== p.expected_audience, "R_AUDIENCE_MISMATCH"],
    [p.nonce !== p.expected_nonce, "R_NONCE_MISMATCH"],
    [age < 0 || age > p.max_age_seconds, "R_PRESENTATION_STALE"],
    [p.credential_status !== "active", "R_CREDENTIAL_INACTIVE"],
    [!p.issuer_trusted, "R_ISSUER_UNTRUSTED"],
    [!subset(r.used_attributes, r.approved_attributes), "R_USE_EXCEEDS_APPROVAL"],
    [!r.lawful_basis_recorded, "R_LAWFUL_BASIS_UNRECORDED"],
    [!r.decision_log_complete || !r.verifier_version || !r.policy_version, "R_AUDIT_EVIDENCE_INCOMPLETE"],
  ];
  return rules.find(([failed]) => failed)?.[1] ?? "A_PROFILE_CONFORMANT";
}

const results = corpus.vectors.map((vector) => {
  const reason = evaluate(vector.transaction);
  return {
    id: vector.id,
    implementation: IMPLEMENTATION,
    verdict: reason.startsWith("A_") ? "ACCEPT" : "REJECT",
    reason,
  };
});

process.stdout.write(`${JSON.stringify({ implementation: IMPLEMENTATION, results })}\n`);
