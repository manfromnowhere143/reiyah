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

## Gate A 1.1.1 pre-transport observation

[`public-rights-revalidation-2026-08-24.json`](public-rights-revalidation-2026-08-24.json) is the
add-only Gate A `1.1.1` observation for the governance-correction distribution event. It binds
the earlier observation by exact path, digest, size, and version. It neither expands the frozen
`1.1.0` evidence profile nor authorizes or establishes distribution.

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

Gate A `1.1.1` is a governance-correction candidate and does not change the `1.1.0` evidence
profile, mission release, or protocol release. Its indexed bytes cannot contain their own later
transport commit or remote readback. Inspect the latest valid append-only receipt for those facts;
without a receipt binding the `1.1.1` index, transport is unverified. Mutable official rights
pages must be observed again before each later payload distribution event; an unreachable page or
contradiction fails closed.

The `2026-08-24` observation is therefore a pre-transport input, not a transport receipt. Only a
valid receipt sequence two can bind it to the exact successor index, validation report, published
commit, and verified remote readback. A future distribution event requires another versioned
observation and receipt contract rather than reuse of this event-specific record.

## Contributor rule

Do not add third-party bytes merely because they are publicly accessible. First record exact
identity, provenance, access terms, redistribution basis, attribution, limitations, digest, and
byte size. When permission or identity is unresolved, add pointer metadata only and keep the
record evidence-ineligible.
