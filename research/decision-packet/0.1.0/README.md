# Decision packet interface

Version: `0.1.0`

Lifecycle status: `proposed`

Operands that let another engineer verify one detector-addition decision without trusting the
producer and without running a matcher. See
[the findings](../../../docs/DECISION_EVIDENCE_2026-09-11.md) for why a silence table is not enough.

## Case

A case declares one anchor: the loss penalties, the base detections, the added detections, the
objects, and one or more reference interpretations. Each interpretation names the objects present in
it and the same-class edges admitted in it. Identifiers must be neutral: the producer refuses
anything that is not a short alphanumeric token, which is what keeps source identifiers out.

Base preservation is structural. A detection may not appear in both configurations, and the
augmented configuration is the base plus the additions.

## Report

For each interpretation the producer returns the certified matched counts, a matching and a vertex
cover of equal size for each configuration, and the loss difference
`delta = (a + b)(TP_augmented - TP_base) - b * r`. Across interpretations it returns the enclosure
and the coarse count bound `[-b*r, a*r]`, and refuses any world where the gain leaves `[0, r]`.

## Checking

[`check_decision_packet.py`](../../../tools/measure/check_decision_packet.py) imports nothing from
the producer and computes no matching. Every matching is at most every vertex cover, so a matching
and a cover of equal size force optimality, for any graph. The checker verifies the matching uses
declared edges and is one to one, that the cover covers every declared edge, that the sizes agree,
and that the reported edges equal the case edges, then recomputes the loss.

Shared trusted surface: the JSON module, the identifier and rational string conventions, and
Python's `Fraction` and integer arithmetic.

## Scope

A confirmation covers the arithmetic of a declared comparison inside declared interpretations. It
does not establish that those interpretations are right, that the graph reflects the recording, or
that the population is the intended one. It carries no physical, planner or risk consequence, and
the identity does not transfer to F1.

## Cases in this directory

`cases/` holds eight real anchors built by
[`build_decision_cases.py`](../../../tools/measure/build_decision_cases.py) from retained detector
outputs under one declared rule. They are not the Engine's anchors and must not be combined with
them; the correspondence gaps are listed in the findings document.
