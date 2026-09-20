# Corrected MATLAB numeric-cell decoding

Document ID: `reiyah.compact-motion.correction`. Version: `0.1.1`.
Status: corrected implementation; physical findings remain exploratory.

The [initial release](../0.1.0/README.md) failed during its first actual audit.
The decoder required every MATLAB numeric cell to be a binary64 float. A
subsequent type-only investigation found 4,437 floating cells in each of the
latitude, longitude and two standard-deviation columns. Heading had 4,436
floating cells and one unsigned eight-bit integer. Numeric integer cells are
legitimate in this MATLAB cell array; the first-row schema sample missed that
heterogeneity. No missing value is converted to zero.

Only the shared decoder and its controls change. It now accepts Python float
or integer scalar values, excluding booleans and integers outside the exactly
representable binary64 integer range. Three actual MAT-container controls prove
acceptance of a uint8 scalar and continued rejection of text and an integer that
would lose precision. The producer/reference arithmetic, population, ordering,
decision, formulas and thresholds are unchanged. Their interface schemas remain
version 0.1.0; this correction is an append-only packet/freeze release.

The failed audit cost 0.699638250 outer-process seconds. It computed intermediate
census/clock values but failed before serializing the result; those intermediate
values are unavailable, not a successful retained run. The source bytes, original
code, two original freezes, twenty passing initial diagnostic controls, seven
passing initial decision controls and complete private failed-command receipt
remain. No actual decision method had run before this correction.

Both new freezes name their predecessors. The source selection and decision
question stay unchanged. The supervisor's artifact accounting now includes both
packet versions; its original bytes are retained privately and the new bytes are
bound in the corrected freeze. Cumulative execution/checking budgets are not reset.
The command that created this correction used the prior supervisor; subsequent
measurements include both versions. No resource ceiling was approached.
