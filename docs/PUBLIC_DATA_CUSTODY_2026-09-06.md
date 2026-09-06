# Public data custody, 2026-09-06

Document ID: `reiyah.gate-b.public-data-custody-2026-09-06`

Version: `0.1.0`

Lifecycle status: `proposed`

The source policy requires that a source be characterized only from retained bytes, metadata,
access terms, redistribution terms, and digest. A URL alone is not retained evidence, and a source
held only as a pointer may not be described as if retained. This record states the custody state of
every public data source the human-channel and LLM threads use, as found on 2026-09-06, and names
the gaps. It creates no rights, no permission, and no claim.

## Custody states

| Source | Used by | Bytes in public Git | Origin recorded in repo | Terms as asserted by the result | Terms retained | Custody state |
|---|---|---|---|---|---|---|
| nuScenes trainval metadata (Motional) | Results A through R, S | no, gitignored | yes, S3 URL and SHA-256 in the handoff | nuScenes terms of use, non-commercial | no | `primary_pointer_only`, digest pinned |
| Detector prediction files (Megvii, Mapillary, PointPillars, FCOS3D run for Result Q) | Results A through R | no, gitignored | yes, `tools/measure/fetch_predictions.py` | per-detector release terms | no | `third_party_unretained` |
| 100-Car Naturalistic Driving Study (VTTI) | H1, H2, H3 | no, gitignored | yes, dataverse DOI `10.15787/VTT1/CEU6RB` and file ids in `human-channel/README.md` | CC0 1.0 | no | `primary_pointer_only` |
| DCPT L3 takeover dataset | H4 | **yes**: `human-channel/dcpt/README.md`, `TakeoverTime.xlsx`, `information.xlsx`, committed at `215b3b0` | **no** | CC BY 4.0, asserted in H4 | **no** | `third_party_retained_terms_unverified` |
| BDD-A driver attention (Xia et al. 2018) | H5, H6 | no, gitignored | **no** | research-use, asserted in H5 and H6 | no | `third_party_unretained_pointer_unrecorded` |
| Open LLM Leaderboard v1 per-question results (`open-llm-leaderboard-old`, Hugging Face) | T, U, V, W | no, downloaded at run time | yes, dataset id in the tools | per-model and per-dataset terms on the Hub | no | `third_party_unretained` |

## Open findings

1. **DCPT payload in public history without recorded permission.** Three third-party files are in
   public Git. The repository contract permits a third-party payload in public history only when
   redistribution permission and every required attribution are recorded. Neither the licence bytes
   nor the origin are retained, so the CC BY 4.0 assertion in H4 is a pointer-grade statement. The
   payload is already published and history is append-only, so the gap is recorded rather than
   rewritten. Closing it requires retaining the licence text and origin with digests, and adding the
   attribution the licence requires to `NOTICE`. Removal from history, if chosen, is an operator
   decision.
2. **BDD-A origin unrecorded.** The data are not committed, which is correct for a research-use
   source, but no pointer record names where the bytes came from or under what terms. H5 and H6 may
   describe the data only as research-use public data pending a retained pointer record.
3. **No licence bytes retained for any source.** Every terms statement above is asserted from
   memory of the source page, not from retained bytes. That is sufficient for a descriptive
   `proposed` result on public data and insufficient for any publication or redistribution claim.

## Non-claims

A custody inventory, not a rights determination. It asserts no licence, permission, compliance, or
publication authority, and it modifies no released `1.2` byte.
