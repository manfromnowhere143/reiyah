# Retained tables for the joint silent miss identification analysis

These are declared observed counts, not measurements. No population was sampled, no channel is
named, and no value of the coefficient is estimated from them.

A pattern names which channels detected an object. The all zero pattern never appears, because an
object that no channel reported leaves no trace in any channel's output. That absence is the subject
of the analysis, and supplying it as an input is refused by the module.

| table | what it shows |
|---|---|
| `two-channel-unidentified` | with two channels the coefficient ranges over `[0, 4/3]` on these counts, so the same observations are consistent with strong negative and strong positive coupling. A capture recapture fill returns exactly `1` |
| `three-channel-sign-settled` | with a third channel the threshold falls to `-491/27`, below zero, so the coefficient for the pair `(A, B)` exceeds `1` for every admissible joint silent miss count, with no reference annotation at all |

Collapsing the third channel of the second table back to two channels puts the threshold above zero
again, which is asserted as a test. The third channel is doing the work, not the arithmetic.
