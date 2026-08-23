# Contributing to Reiyah

Reiyah welcomes precise, reviewable contributions to its static research architecture. Gate A does not authorize product runtime, model execution, private data, vehicle integration, or empirical performance claims.

## Before proposing a change

1. Read `AGENTS.md` and `docs/SESSION_HANDOFF.md`.
2. Confirm the change stays inside the current Gate A boundary.
3. Identify whether it changes a normative contract, retained evidence, an immutable release, or only explanatory prose.
4. Preserve all explicit epistemic and lifecycle states.
5. Keep observation, latent belief, decision, intervention, outcome, and evidence separate.

## Evidence contributions

A source URL alone is not evidence. A proposed retained source must include exact publisher identity, version, publication date, retrieval provenance, byte count, SHA 256 digest, access terms, redistribution terms, scope, limitations, and an eligible source ledger record.

Do not place material in `evidence/sources` unless public redistribution authority has been observed and recorded. If redistribution is not authorized, contribute a pointer only record with no payload. Do not submit personal, proprietary, credentialed, or sensitive data.

Standards mappings must remain mappings of relevance and evidence gaps. They must not claim legal applicability, conformity, certification, compliance, or safety.

## Schema and fixture contributions

Normative JSON uses JSON Schema Draft 2020 12. New fields require explicit semantics, bounded identifiers, and `additionalProperties: false` where the contract is intended to be closed.

Every material rejection rule needs:

1. one valid positive example;
2. one minimal known bad example;
3. an exact expected diagnostic identifier; and
4. replay through the same validator path used for the full packet.

Never weaken a schema, validator, fixture expectation, or evidence rule solely to make validation pass.

## Immutable releases

Mission and protocol release identifiers are never edited or reused. A correction creates a successor with an exact predecessor digest and an explicit relation. Earlier releases remain discoverable. Operator acceptance remains external to the offline validator.

## Local checks

Run these commands from the canonical Reiyah root:

```sh
python3 tools/build_gate_a_index.py > /tmp/reiyah-index.json
python3 tools/validate_gate_a.py
git diff --check
```

When a change intentionally updates indexed bytes, follow `docs/VALIDATION.md` to regenerate the canonical index and retained report. Do not hand edit derived hashes or reports.

## Contribution terms

Unless stated otherwise in the contribution, material intentionally submitted for inclusion in Reiyah is provided under Apache License 2.0. This does not apply to third party evidence, which must retain its original terms and attribution.
