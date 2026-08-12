# Common SD-JWT presentation corpus

This directory contains one deterministic `dc+sd-jwt` presentation baseline
and one single-property negative mutation. The complete compact presentation,
not merely an equivalent locally issued credential, is supplied to every
adapter.

The negative case changes one character of the issuer-JWS signature. Its
key-binding JWT is then regenerated so `sd_hash`, nonce, audience, holder key
and key-binding signature remain valid. This makes issuer authentication the
only intended failing property.

The fixture is synthetic and uses test-only key material already present in
the pinned walt.id test suite. It must never be used as a production
credential or trust anchor.

Regenerate and verify determinism:

```sh
python3 generate_fixture.py
sha256sum -c SHA256SUMS
```

The corpus supports a cross-implementation research comparison. It is not an
EUDIW or FCAF conformance certificate.
