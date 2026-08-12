# Third-party notices

The Tyche-authored schemas, research profiles, tests, scripts and documentation in this repository
are released under the repository's MIT License. The packet interoperates with, cites or derives
limited test/build material from the following Apache-2.0 projects; their own copyright notices and
licences continue to apply to that material.

| Project | Pinned source used by the study | Licence |
|---|---|---|
| European Commission EUDI verifier endpoint | `db5442501ea06907e614377a20d802748e8bfddb` | [Apache-2.0](https://github.com/eu-digital-identity-wallet/eudi-srv-verifier-endpoint/blob/db5442501ea06907e614377a20d802748e8bfddb/LICENSE) |
| OpenWallet Foundation Multipaz | `570aa2475bd5b7e437d9041bf8ff1127bcf86cfb` | [Apache-2.0](https://github.com/openwallet-foundation/multipaz/blob/570aa2475bd5b7e437d9041bf8ff1127bcf86cfb/LICENSE) |
| walt.id identity | `f773918a3ad226ba7c0908d58941f18a3b89591d` | [Apache-2.0](https://github.com/walt-id/waltid-identity/blob/f773918a3ad226ba7c0908d58941f18a3b89591d/LICENSE) |

In particular:

- `real-stack-adapters/build-isolation/multipaz-jvm-only.patch` contains a minimal patch against the
  pinned Apache-2.0 Multipaz build configuration;
- the deterministic corpus generator uses synthetic test-only key/certificate material derived
  from the pinned Apache-2.0 walt.id test context; and
- the release does not redistribute the three upstream production source trees. The clean-clone
  runner obtains them from their canonical repositories at the exact commits above.

The named projects and their maintainers do not thereby endorse Tyche, this research package or its
results. Their names identify independently maintained source paths used in the recorded tests.
