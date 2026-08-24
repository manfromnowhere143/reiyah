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
is the present Gate A `1.1.2` same-event observation, recorded at `2026-08-24T10:16:56Z`. It
exact-binds the immutable `1.1.1` observation as its predecessor and records the preflight outcome
`included_iso_basis_consistent_nist_payload_excluded` with a maximum age of 3,600 seconds. It is an
observation only: it creates no distribution authority, legal conclusion, GA-17 evaluation, or
Gate A acceptance. A sequence-three receipt must exact-bind it to the same published `1.1.2`
index, canonical report, packet commit, and remote readback within that freshness window;
otherwise transport is unverified and a new observation is required.

## Historical records

[`source-ledger.json`](source-ledger.json) and
[`standards-crosswalk.json`](standards-crosswalk.json) are historical Gate A 1.0 artifacts.
They describe the prior local candidate and must not be used as the current evidence or
distribution profile. Historical visibility does not restore source eligibility or permission.

## Distribution state

The operator authorized public distribution of the exact static open source Gate A `1.1.0`
candidate within the inventory boundary. The frozen packet was published at commit
`aa5f9b9b455219536183630b0be1e801a18a575e`. Verified remote readback is recorded in the
append-only [public distribution
receipt](../gate/public-distribution-receipts/reiyah.public-distribution-receipt-1.1.0.json),
which was added at commit `68854b474f7c4ebd95cc79ced56411c2d5935f78`.

The base custody and inventory records retain `distribution_executed: false` because they bind
the pre-transport packet. The receipt separately records that transport occurred. It cannot
evaluate GA-17, accept Gate A, support a claim, or authorize runtime.

Gate A `1.1.1` is a published governance correction and does not change the `1.1.0` evidence
profile, mission release, or protocol release. Its append-only sequence-two receipt records the
packet commit, exact index and report bytes, fresh rights observation, and remote readback. Gate A
`1.1.2` is a documentation-and-continuity successor with the same evidence boundary. Its indexed
bytes cannot contain their own later transport commit or remote readback. Without a valid
sequence-three receipt binding the `1.1.2` packet, its transport remains unverified. Mutable
official rights pages must be observed again before each payload distribution event; an
unreachable page or contradiction fails closed.

The `2026-08-24` observation remains a pre-transport input, not a transport receipt. Receipt
sequence two binds it to the exact `1.1.1` packet. A future distribution event requires another
versioned observation and receipt contract rather than reuse of this event-specific record.

## Contributor rule

Do not add third-party bytes merely because they are publicly accessible. First record exact
identity, provenance, access terms, redistribution basis, attribution, limitations, digest, and
byte size. When permission or identity is unresolved, add pointer metadata only and keep the
record evidence-ineligible.
