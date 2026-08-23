# Evidence custody

This directory separates retained source bytes from source identity, discovery pointers, and
distribution authorization. None of these artifacts is scientific, safety, standards,
compliance, publication, or operator authority.

## Current Gate A 1.1 profile

The candidate public profile consists of these versioned artifacts:

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

## Historical records

[`source-ledger.json`](source-ledger.json) and
[`standards-crosswalk.json`](standards-crosswalk.json) are historical Gate A 1.0 artifacts.
They describe the prior local candidate and must not be used as the current evidence or
distribution profile. Historical visibility does not restore source eligibility or permission.

## Distribution state

The operator authorized public distribution of the exact static open source candidate within
the inventory boundary. Before the first push, `distribution_executed` remains false. The
mutable official rights pages must be observed again before each payload distribution event. An
unreachable page or contradiction fails closed. After an actual push, a separate append-only
receipt must bind the published commit, inventory, rights observation, and exact four payloads.
Such a receipt records transport only. It cannot evaluate GA-17, accept Gate A, support a claim,
or authorize runtime.

## Contributor rule

Do not add third-party bytes merely because they are publicly accessible. First record exact
identity, provenance, access terms, redistribution basis, attribution, limitations, digest, and
byte size. When permission or identity is unresolved, add pointer metadata only and keep the
record evidence-ineligible.
