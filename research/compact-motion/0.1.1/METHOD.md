# Recorded precision and clock arithmetic

Document ID: `reiyah.compact-motion.method`. Version: `0.1.0`.
Status: exploratory. This is an input diagnostic, not a clearance monitor.

CSV and MAT must have the declared columns and finite timestamps. Empty numeric
cells, NaN and infinities remain explicitly counted. Malformed structure fails
the run; no row is silently discarded. Numeric summaries identify their finite
denominator. Duplicate and non-increasing timestamps remain reported.

For the two target representations, row index and exact `Time` string must
agree. The finite numeric difference is CSV value minus MAT value, retaining
absolute maximum, mean and exact binary-value difference count by column.
Coordinate decimal-place histograms describe the written tokens, not uncertainty.

For latitude/longitude pairs in radians, the producer computes

`a = sin²(Δφ/2) + cos(φ_csv) cos(φ_mat) sin²(Δλ/2)`

`d = 2 R asin(sqrt(a))`, with numerical clamping to `[0,1]` and
`R = 6,371,008.8 m`, a chosen spherical reporting convention.

The checker independently forms both three-dimensional unit vectors, takes
their Euclidean chord length, and applies `d = 2 R asin(chord/2)`. Agreement
tolerance is 0.000001 m absolute for distance and 1e-12 absolute for angular and
other numeric differences. This tolerance is numerical only. Neither formula
estimates the true position error or an uncertainty envelope. No ellipsoid,
altitude, datum transform or calibration is implied by the nominal metre figure.

Define `R_text` by interpreting the written ego calendar fields on a naive
Unix-like calendar axis, `H` from integer header seconds plus nanoseconds, and
`G` from the GPS epoch 1980-01-06 plus week and week-seconds. Report `R_text-H`
and `G-H` exactly as decimal seconds, along with each stream's increments.
Use exact decimal arithmetic in the producer and rational arithmetic in checking.
Do not silently interpret text as UTC, convert GPS to UTC, or subtract a fitted
offset. The USNO time page was found but its direct capture failed; it is not
retained input evidence. Source field differences alone cannot identify which
clock is physically correct or its error.

No mathematical conversion of a standard deviation into a deterministic bound
or simultaneous trajectory coverage is permitted. The reviewed NovAtel OEM7
documentation is current context, not proof that the older ProPak6 configuration
or target vehicle obeys the same uncertainty model. Geometry workbook dimensions
and offsets are documented values, with calibration and footprint residuals still
unqualified. The [physical contract](../../physical-source/0.1.0/CONTRACT.md)
remains the admission obligation for any later clearance comparison.
