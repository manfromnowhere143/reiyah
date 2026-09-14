# Ordinary comparator, corrected

Version: `0.2.0`

Lifecycle status: `proposed`

Successor to `0.1.0`, which is retained unchanged. Seven statements in 0.1.0 were wrong. Each was
found by the Engine consumer review of 14 September 2026, reproduced here on the exact selected
source before anything changed, and is recorded in `CORRECTIONS.json` with its evidence and its
repair.

| artifact | what it holds |
|---|---|
| `end-to-end.json` | the eight selected cases, 1400 synthetic conformance instances, the traced checking cost, the six measured costs, and a compatibility record for the Engine's real source bound comparison |
| `CORRECTIONS.json` | the seven corrections, each with what 0.1.0 said, what is true, the evidence and the repair |

Read [`docs/COMPARATOR_CORRECTIONS_2026-09-14.md`](../../../docs/COMPARATOR_CORRECTIONS_2026-09-14.md).

## What changed in the numbers

- **378** of 717 cases needing a list carry a minimum size certificate. 8 more have a searched
  optimum the packing does not force, and 331 are bracketed. 0.1.0 reported 386 certified.
- The checker performs **36, 136 and 528** pair comparisons on the 8, 16 and 32 discordant pair
  controls. Linear checking describes a supplied cover and its sets, not this implementation.
- A cohort with an open reference and an already determined criterion now reports
  `already_decided` and asks for nothing. 0.1.0 said it was waiting.

## The Engine's real comparison

Bound by SHA-256 `8e79f3636ef337d7ea2f12ec213e67106d7d4afce55bdafb6c63ba10d667f299`. Two open
anchors, 85 base detections, 16 additions, zero admitted readings, enclosure `[-8, 8]`. The bytes
belong to another owner and are not copied here; the compatibility record carries the digest, the
structure in counts and the checked result, with no detection identifier reproduced.

## Scope

A corrected consumer procedure is an engineering result. It is not independent scientific review,
not human reference admission, and not evidence of decision value. No person has run either
method, so every human cost remains `unmeasured`.
