# Evidence custody

This directory separates retained source bytes from source identity, discovery pointers, and
distribution authorization. None of these artifacts is scientific, safety, standards,
compliance, publication, or operator authority.

## Frozen Gate A 1.1.0 profile

The frozen public profile consists of these versioned artifacts:

- [`public-evidence-custody-profile-1.1.0.json`](public-evidence-custody-profile-1.1.0.json)
  defines the admissible custody states and authority limits.
- [`source-ledger-1.1.0.json`](source-ledger-1.1.0.json) records four retained payloads and
  four historical pointer-only records.
- [`standards-crosswalk-1.1.0.json`](standards-crosswalk-1.1.0.json) maps seven standards or
  guidance identities without claiming conformance or compliance.
- [`frontier-discovery-register-1.1.0.json`](frontier-discovery-register-1.1.0.json) records
  38 pointer-only research and company sources. Every pointer is evidence-ineligible.
- [`frontier-discovery-register-1.2.0.json`](frontier-discovery-register-1.2.0.json) exact-binds
  those 38 records as an unchanged prefix and appends 16 discovery records, for 54 total. The
  additions cover official Tesla, Mobileye, MOIA, NHTSA, Waymo, and Google material plus primary
  research pointers. They retain no source payload, admit no claim, and remain evidence-ineligible.
- [`public-distribution-inventory-1.1.0.json`](public-distribution-inventory-1.1.0.json)
  defines the exact public payload boundary.
- [`public-rights-revalidation-2026-08-23.json`](public-rights-revalidation-2026-08-23.json)
  records the time-bounded pre-distribution observation of the official ISO and NIST rights
  pages named by the inventory. It is an integrity observation, not legal review or clearance.

The four retained payloads are ISO Open Data catalog records. They are metadata, not normative
ISO text. The NIST AI RMF PDF is pointer-only because the general NIST rights statement leaves a
document-specific third-party-material caveat unresolved for this public release.

The prior NIST PDF, NIST publication-page capture, and two UN PDFs are not present in this
public worktree. Their former local identities and digests remain visible as historical custody
metadata, but they are inadmissible under the current profile and unauthorized for payload
distribution.

## Versioned transport observations

[`public-rights-revalidation-2026-08-24.json`](public-rights-revalidation-2026-08-24.json) is the
add-only Gate A `1.1.1` observation for the governance-correction distribution event. It binds
the earlier observation by exact path, digest, size, and version. It neither expands the frozen
`1.1.0` evidence profile nor independently authorizes or establishes distribution. Receipt
sequence two exact-binds this observation to the published `1.1.1` packet.

[`public-rights-revalidation-2026-08-24-1.1.2.json`](public-rights-revalidation-2026-08-24-1.1.2.json)
is the Gate A `1.1.2` same-event observation, recorded at `2026-08-24T10:16:56Z`. It
exact-binds the immutable `1.1.1` observation as its predecessor and records the preflight outcome
`included_iso_basis_consistent_nist_payload_excluded` with a maximum age of 3,600 seconds. It is an
observation only: it creates no distribution authority, legal conclusion, GA-17 evaluation, or
Gate A acceptance. Receipt sequence three exact-binds it to the same published `1.1.2` index,
canonical report, packet commit, and publisher readback assertion.

[`public-rights-revalidation-2026-08-25-gate-a-static-correction-1.2.0.json`](public-rights-revalidation-2026-08-25-gate-a-static-correction-1.2.0.json)
is the event-specific Gate A `1.2.0` rights record. It binds `C_packet`
`86409473c8fd1571236c849a6cc730db896465fb`, the exact index and canonical report, and both typed
official-page capture manifests. Receipt sequence four exact-binds that record to the public
packet. The rights record is not legal review, and the receipt's publisher readback is not
independent transport verification.

## Historical records

[`source-ledger.json`](source-ledger.json) and
[`standards-crosswalk.json`](standards-crosswalk.json) are historical Gate A 1.0 artifacts.
They describe the prior local candidate and must not be used as the current evidence or
distribution profile. Historical visibility does not restore source eligibility or permission.

## Distribution state

The operator authorized public distribution of the exact static open source Gate A `1.1.0`
candidate within the inventory boundary. The frozen packet was published at commit
`aa5f9b9b455219536183630b0be1e801a18a575e`. The publisher's remote readback assertion is recorded
in the append-only [public distribution
receipt](../gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.0.json),
which was added at commit `68854b474f7c4ebd95cc79ced56411c2d5935f78`.

The base custody and inventory records retain `distribution_executed: false` because they bind
the pre-transport packet. The receipt separately records that transport occurred. It cannot
evaluate GA-17, accept Gate A, support a claim, or authorize runtime.

Gate A `1.1.1` is a published governance correction and does not change the `1.1.0` evidence
profile, mission release, or protocol release. Its append-only sequence-two receipt records the
packet commit, exact index and report bytes, fresh rights observation, and publisher readback.
Gate A `1.1.2` is a documentation-and-continuity successor with the same evidence boundary; its
sequence-three receipt is retained. Gate A `1.2.0` is the completed public static correction. Its
packet commit is `86409473c8fd1571236c849a6cc730db896465fb`; its direct-child receipt commit is
`d42d4d298d515b59e9df15f2ba45572a91b9fab8`. Sequence four records
`transport_verification_state: asserted_unverified`, while independent transport remains
`not_evaluated`. All four packets remain operator-unaccepted and confer no scientific, safety,
standards, compliance, or runtime authority.

The `2026-08-24` observation remains a pre-transport input, not a transport receipt. Receipt
sequence two binds it to the exact `1.1.1` packet. A future distribution event requires another
versioned observation and receipt contract rather than reuse of this event-specific record.

The `1.2.1` continuity successor is tracked in
[GitHub issue #1](https://github.com/manfromnowhere143/reiyah/issues/1). This prose change does not
change source eligibility or distribution rights and cannot establish validation or publication.
Resolve those states only from exact versioned machine records; absent them, treat the successor
as proposed.

## Contributor rule

Do not add third-party bytes merely because they are publicly accessible. First record exact
identity, provenance, access terms, redistribution basis, attribution, limitations, digest, and
byte size. When permission or identity is unresolved, add pointer metadata only and keep the
record evidence-ineligible.
