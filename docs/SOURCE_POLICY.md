# Gate A Source and Retention Policy

## Status and authority

This policy is normative for the proposed Gate A architecture packet. It governs static
evidence artifacts only. It does not authorize networked runtime behavior, data ingestion,
model activity, empirical publication, standards interpretation, or a scientific, safety,
legal, or compliance claim. Static public distribution is separately limited to the exact
payload and pointer boundary in the versioned public distribution inventory.

An external source is untrusted input. Publisher status, a signature, a checksum, agreement
between reviewers, or a passing validator may establish provenance or integrity; none makes a
claim true or gives the source Reiyah acceptance authority.

The current machine-readable record is
[`evidence/source-ledger-1.1.0.json`](../evidence/source-ledger-1.1.0.json), validated against
[`schemas/source-ledger-1.1.schema.json`](../schemas/source-ledger-1.1.schema.json). The
unversioned 1.0 ledger is retained as history only.

## Normative requirements

### 1. Eligibility and identity

Every retained source MUST have:

- a stable Reiyah `source_id` and version;
- an identified publisher represented as an explicit measurement state;
- an exact document identifier represented as an explicit measurement state;
- an exact document, protocol, dataset, or record version;
- an exact publication or issue date, or an explicit non-observed state with a reason;
- a source URL and retrieval timestamp;
- a custody state that distinguishes retained payload from pointer-only history;
- for a retained payload, a repository-relative path, byte count, media type, and SHA-256;
- scope, access constraints, licence constraints, and source-specific limitations; and
- an evidence class and an explicit `normative_text_available` value.

A title or URL without retained bytes is a discovery pointer, not retained evidence. A source
MUST NOT enter a crosswalk as positive evidence unless its versioned source reference resolves
to an eligible retained-payload record and its retained digest and size match. Pointer-only
records may appear only as discovery or custody references.

Gate A 1.1 freezes four retained payloads and four historical pointer-only records. For the four
ISO JSON Lines records, the validator derives document identifier, English title,
edition/version, and publication date directly from the retained object. The former NIST PDF,
NIST HTML, and two UN PDF identities are retained only as ineligible custody history. Their bytes
are absent from the public worktree. Changing any identity or custody state requires a reviewed,
versioned successor.

Project names and sibling repositories confer no source identity or authority. Reiyah MUST NOT
copy evidence, conclusions, configuration, or trust decisions from a sibling repository.

### 2. Evidence classes

The class controls what a mapping may say:

| Evidence class | Meaning | Permitted use | Prohibited use |
|---|---|---|---|
| `full_normative_text` | Exact complete normative bytes for the identified version are retained. | Locate and propose mappings to exact text, subject to applicability and expert-review gaps. | Treat retention as interpretation, applicability, conformity, certification, or compliance. |
| `official_regulatory_documentation` | Official bytes reproduce or explain regulatory material but the source itself disclaims authentic legal authority. | Identify scope, structure, dates, and the authentic-text pointer; corroborate document identity. | Cite the documentation copy as the legally binding text. |
| `official_catalog_metadata` | Official publisher metadata, abstract, scope, or publication record is retained. | Identify title, version, date, publisher scope, lifecycle stage, and access boundary. | Infer clauses, obligations, tests, satisfaction, or compliance. |
| `guidance_research` | Guidance or research bytes are retained but are not normative text. | Propose conceptual or methodological relevance with limitations. | Convert guidance, authorship, or publication into normative authority or scientific support. |

`normative_text_available` MUST be `false` for catalog metadata, guidance/research, and a
documentation copy that disclaims legal authenticity. It may be `true` only when the exact source
record retains the complete identified normative text. A `true` value still does not establish
applicability or correct interpretation.

### 3. Exact-byte retention

Source bytes MUST be stored without normalization, OCR replacement, reserialization, metadata
editing, or line-ending conversion. Any extraction, OCR output, annotation, translation, or
summary is a derived artifact and MUST NOT replace the retained source.

A byte-range response is acceptable only when all of these conditions hold:

1. the publisher makes a machine-readable aggregate dataset available;
2. the retained interval contains exactly one complete record, including its record terminator;
3. the retrieval is conditionally pinned to the aggregate object's observed ETag;
4. the record stores the exact `Content-Range`, total upstream size, ETag, URL, retrieval time,
   local byte count, and local digest; and
5. an offline check can parse the retained record independently.

The four ISO records in Gate A use this procedure. They are exact rows from ISO's daily
`iso_deliverables_metadata` JSON Lines object, not generated summaries and not ISO standards
text. The `_latest` endpoint is mutable; the ETag and byte range are therefore part of each
record's identity for this snapshot.

### 4. Access and licence states

Access and licence constraints MUST be recorded separately. Public download does not imply a
reuse licence. Government authorship, absence of a notice, or technical ability to download MUST
NOT be interpreted as permission.

If a licence is not present in the retained bytes, the record MUST say `unmeasured` unless a
publisher declaration was independently observed. When the declaration itself could not be
retained, that limitation MUST remain visible. The current ISO records therefore state both the
publisher-declared ODC-By 1.0 attribution term and the fact that the ISO landing-page HTML could
not be retained after an HTTP 403 response.

No validator determines copyright, licence validity, fair use, legal effect, jurisdiction, or
contracting-party adoption.

Immediately before a public distribution event, the mutable official ISO Open Data and NIST
Technical Series rights pages MUST be observed again. The observation MUST be a separate,
digest-bound artifact covering all four included payloads, must preserve the observer's lack of
legal and operator authority, and must fail closed on an unreachable page or an observed
contradiction. This preflight is an integrity observation only. It is not qualified legal review,
legal clearance, or a new distribution authorization.

Gate A 1.2 retains two typed capture manifests inside the packet before creating the post-packet
rights wrapper. Each manifest records the exact official URL, observation times, predeclared
capture mode, bounded observer-authored paraphrases, and an explicit metadata-only extent. A direct
HTTP mode records the requested and final URL, response status and media type, and an asserted
digest over response-body octets after HTTP transfer decoding and before text decoding. It also
records the unretained body's byte size. An adapter-observation mode is permitted only when the
predeclared official page blocks the separately recorded direct attempt. That mode records the
adapter and its visible observation, leaves unavailable response status, body digest, and byte size
unasserted, and exposes any adapter crawl-freshness limitation. Reiyah supplies no credential
material; cookie state that an adapter does not expose remains `unobserved`, never assumed absent.
The protocol fixes one mode for each page so a failure cannot silently downgrade the capture.

No response body or adapter snapshot is retained or redistributed when a document-specific
redistribution basis is not established. These locally authored manifest bytes are not a substitute
for the unretained page, do not prove authenticity or legal effect, and remain evidence-ineligible.
The rights wrapper resolves both manifests and binds the already committed packet, index, and
report. Publication freshness is derived from both observation completion times and requires
ordered capture, manifest, rights, and publication timestamps. An expired capture requires a new
packet and may not be refreshed under an immutable path.

### 5. Version and amendment control

Every mapping is dated. A current-stage flag, successor identifier, amendment, or draft MUST NOT
silently mutate an existing source record. Review creates a new source-record version and retains
the earlier record. Corrections and retractions remain discoverable and use their distinct
lifecycle states.

A crosswalk MUST expose when:

- a retained edition is under revision or lists a successor;
- only one part of a multipart series is retained;
- a documentation copy points to a separate authentic text;
- amendments or jurisdictional applicability have not been reviewed; or
- the selected source is informative, voluntary, generic, or otherwise narrower or broader than
  Reiyah's proposed research scope.

### 6. Mapping rule

A standards or guidance mapping MUST identify the exact publisher, title, document identifier,
version, publication date, scope, comparator, requirement locator, versioned identity source,
proposed relevance, open gap, closure requirements, and lifecycle status. Its
`identity_source_ref` MUST resolve exactly to the named source-ledger version. Positive
`evidence_source_refs` MUST resolve only to eligible retained payloads. Pointer-only records may
appear only in `discovery_source_refs`. The five external identity fields MUST equal the selected
ledger record exactly. Substring, fuzzy, or composite identity matching is prohibited. The
mapping MUST use `proposed`, `partial_mapping`, or `evidence_gap` language and carry this
prohibition:

> This mapping is not a legal, safety, conformance, certification, or compliance conclusion.

Catalog metadata has no requirement locator beyond its exact record fields. A scope resemblance
MUST NOT be promoted to a clause-level mapping. No mapping may treat a standard's term as ground
truth for a Reiyah latent construct without an independently reviewed and empirically valid
measurement argument.

### 7. Unknowns and negative evidence

Missing, unmeasured, out-of-distribution, sensor-invalid, abstained, inaccessible, and
licence-unknown are distinct. They MUST NOT be encoded as `false`, `zero`, normal, compliant, or
not relevant. Failed retrieval is an access observation, not evidence that a source does not
exist. Lack of retained evidence is not evidence of absence.

### 8. Offline validation

The Gate A validator MAY check schemas, internal references, digests, byte sizes, media
signatures, exact byte-range metadata, and prohibited conclusion strings. It MUST run offline and
fail closed. It MUST NOT refetch a source, decide scientific merit, interpret a standard, resolve
licensing, or create operator acceptance.

## Retention procedure

For a future source update, the reviewer MUST:

1. resolve the exact publisher artifact and version from a primary source;
2. record the intended scope and why it is relevant before interpreting content;
3. retrieve public bytes without credentials unless separate operator authority permits access;
4. preserve the response bytes and acquisition metadata exactly;
5. compute SHA-256 and byte size locally;
6. record access and licence constraints as observed or explicitly non-observed states;
7. classify the evidence without overstating normative authority;
8. add or revise mappings with exact locators and open gaps;
9. obtain independent subject-matter review for substantive use; and
10. keep operator acceptance separate and hash-bound to the complete Gate A evidence index.

## Current retained-source boundary

As of 2026-08-23, Gate A 1.1 retains exactly four payloads:

- four official ISO Open Data catalog records for ISO 26262-1:2018, ISO 21448:2022,
  ISO/TR 21959-1:2020, and ISO/PAS 8800:2024.

The former NIST PDF, NIST publication-page HTML, and two UN PDFs are absent from the public
worktree. Their exact prior paths, hashes, byte sizes, and source identities remain as four
pointer-only, evidence-ineligible custody records. The distribution inventory authorizes four
payloads only.

Full ISO normative publications, an eligible current UN regulatory text, empirical benchmark
sources, a current NHTSA human-factors source, SAE taxonomy text, independent scientific review,
qualified legal or standards review, and operator acceptance are not retained. Those absences
remain evidence gaps, not negative findings.
