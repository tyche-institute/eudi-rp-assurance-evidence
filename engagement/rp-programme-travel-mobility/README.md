# Travel and mobility RP assurance field packet

Status: **ready for a Commission programme session; no attendance or observation claimed**

This packet expresses the relying-party assurance problem through one simple cross-border mobility
journey. It is designed for a 15-minute conversation with a service operator, wallet implementer or
public authority, without requiring them to understand the paper's terminology.

The four cards ask:

1. Who is asking the wallet?
2. Are the requested facts necessary for this service?
3. Is the answer bound to this exact transaction?
4. What evidence remains for the decision and later user rights?

`assurance-cards.json` is the canonical structured version. `travel-mobility-field-brief.pdf` is the
one-page participant-facing version.

The packet contains no traveller data, production credential, contact list or respondent data. It
is not a compliance checklist. If a programme participant is invited to run a synthetic case and
permit a research observation, use the already frozen consent and evidence instrument under
`meetings/2026-09-29-etsi-cen-eudi-wallet-workshop/interop-field-instrument/`; otherwise treat the
conversation as unrecorded programme engagement.

Build and validate:

```sh
./build.sh
```

