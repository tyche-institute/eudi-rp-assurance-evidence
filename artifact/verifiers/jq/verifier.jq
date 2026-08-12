def subset($xs; $ys): all($xs[]; . as $x | $ys | index($x) != null);

def reason($t):
  ($t.rp) as $rp |
  ($t.presentation) as $p |
  ($t.reliance) as $r |
  if ($p.parse_ok | not) then "R_PARSE_INVALID"
  elif ($rp.registered | not) then "R_RP_UNREGISTERED"
  elif $rp.registration_status != "active" then "R_RP_SUSPENDED"
  elif $rp.authenticated_rp_id != $rp.registered_rp_id then "R_RP_IDENTITY_MISMATCH"
  elif ($rp.registered_purposes | index($rp.transaction_purpose)) == null then "R_PURPOSE_MISMATCH"
  elif (subset($rp.requested_attributes; $rp.registered_attributes) | not) then "R_ATTRIBUTE_OVER_REQUEST"
  elif ($p.issuer_signature_valid | not) then "R_ISSUER_SIGNATURE_INVALID"
  elif ($p.all_disclosures_bound | not) then "R_DISCLOSURE_UNBOUND"
  elif ($p.holder_binding_valid | not) then "R_HOLDER_BINDING_INVALID"
  elif $p.audience != $p.expected_audience then "R_AUDIENCE_MISMATCH"
  elif $p.nonce != $p.expected_nonce then "R_NONCE_MISMATCH"
  elif (($p.evaluated_at_epoch - $p.issued_at) < 0 or ($p.evaluated_at_epoch - $p.issued_at) > $p.max_age_seconds) then "R_PRESENTATION_STALE"
  elif $p.credential_status != "active" then "R_CREDENTIAL_INACTIVE"
  elif ($p.issuer_trusted | not) then "R_ISSUER_UNTRUSTED"
  elif (subset($r.used_attributes; $r.approved_attributes) | not) then "R_USE_EXCEEDS_APPROVAL"
  elif ($r.lawful_basis_recorded | not) then "R_LAWFUL_BASIS_UNRECORDED"
  elif (($r.decision_log_complete | not) or $r.verifier_version == "" or $r.policy_version == "") then "R_AUDIT_EVIDENCE_INCOMPLETE"
  else "A_PROFILE_CONFORMANT"
  end;

"jq-declarative/0.1.0" as $implementation |
{
  implementation: $implementation,
  results: [.vectors[] | reason(.transaction) as $reason | {
    id: .id,
    implementation: $implementation,
    verdict: (if ($reason | startswith("A_")) then "ACCEPT" else "REJECT" end),
    reason: $reason
  }]
}
