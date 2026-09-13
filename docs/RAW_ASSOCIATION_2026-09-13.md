# What raw detections support when the annotation is inaccessible

Document ID: `reiyah.raw-association.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no common operand,
no admission, viewer, shared handoff or main. Gate A remains unaccepted.

## The result, stated first

**On raw two channel detections with the annotation inaccessible, the sign of the dependence
coefficient is not identified.** The threshold that decides it moves by about fourteen times across
defensible preparation choices, and at one of them positive coupling would require more unseen
objects than the public annotation records at all. The honest output is an identified set and a
threshold, never a number, and that is what this module returns.

## The information boundary

Every real measurement this lane had made used caches containing only detections already matched to
annotated objects, so annotation based membership, correspondence and unmatched detection filtering
were inside the inputs. This constructor goes to the original submitted detector outputs instead.

It opens two files and nothing else: `megvii_val.json` and `mapillary_val.json`, both verified
against their recorded digests. Excluded by declaration and by test: any annotation or ground truth
file, any `matched_*` cache, any frame list, class filter or score threshold chosen by inspecting
annotations, and any association rule tuned against them. A test reads the constructor's own source
and asserts those names do not appear in it.

The annotated population of `134,565` appears once, after the table is built, only to express a
threshold as a fraction. It enters no filter, no threshold and no association.

## The association rule, and that it is a choice

Two detections in one frame become one candidate when they carry the same class label and lie within
`tau` metres of each other in the submitted global frame, matched one to one, nearest first. **A
joined pair is a candidate under a declared rule, not a physical object.** Unmatched detections stay
visible rather than being discarded or promoted.

## Why the sign cannot be identified here

Two channels give no third observer, so the cell counting objects both channels missed is empty by
construction. The sign then turns entirely on the unseen count `m`, through `c > 1` exactly when
`m * w > x * y`, so it is decided only above

```
m_star  =  x * y / w.
```

That threshold is not stable under choices nobody can fix without annotations:

| score cutoff | radius | both channels | first only | second only | `m_star` | against 134,565 annotated |
|---|---|---|---|---|---|---|
| 0.2 | 1 m | 63,836 | 127,465 | 81,142 | **162,021** | **1.20x, more unseen than annotated** |
| 0.2 | 2 m | 85,845 | 105,456 | 59,133 | 72,642 | 0.54x |
| 0.3 | 1 m | 50,614 | 69,258 | 52,416 | 71,724 | 0.53x |
| 0.3 | 2 m | 65,889 | 53,983 | 37,141 | 30,430 | 0.23x |
| 0.3 | 4 m | 73,846 | 46,026 | 29,184 | 18,190 | 0.14x |
| 0.5 | 4 m | 33,494 | 26,373 | 14,949 | **11,771** | 0.09x |

`m_star` spans `11,771` to `162,021`, a ratio of `13.8`. Every cell is a defensible preparation. The
conclusion they support is not the same conclusion.

## This is not a defect of one statistic

The intersection count `w` is exactly the quantity the ordinary Jaccard baseline uses, so its
ordering moves with the association radius in the same way. **This is a property of the setting, not
of the coefficient.** A competent analyst given the same raw outputs and the same overlap faces the
same problem, and neither method can resolve it without a third observer or an externally justified
association rule.

That matters for where this lane goes next. The parity result showed the coefficient earns nothing
over overlap for ordering. This result shows that on raw inputs neither earns a sign. Value has to
come from somewhere that is not a better scalar.

## Exposure

These are exposed nuScenes validation submissions. Any comparison against the annotation afterwards
is a **reproducible retrospective falsification**, not a blind validation, and hiding a file does not
undo previous exposure.

## What is out of reach here, and is declared rather than approximated

The five channel modality comparison needs channels this input set does not contain. Two submissions
give no third observer. That comparison is **unresolved on raw inputs** and is not approximated with
a substitute.

## Reproduce

```sh
python3 -B tools/measure/raw_association.py
python3 -B -m unittest discover -s tools/measure -p 'test_raw_association.py'
```

Eighteen tests, standard library only, exact integer counts with rational thresholds. The retained
counts carry the digests of both submissions. No payload is redistributed and no source identifier
is retained.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. No physical object is declared
to exist, no statistical uncertainty or sampling model is computed, and no safety conclusion about
any vehicle follows.
