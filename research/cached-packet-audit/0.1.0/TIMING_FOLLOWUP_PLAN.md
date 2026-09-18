# Follow up the chart component mismatch

Version `0.1.0`, exploratory. The original frozen audit and its no-match result
remain immutable. All 36 declared trials per file compare separate capture,
preprocessing, inference and decoding values; none match all chart tuples.

Inspection of the first two v-e89 chart rows and the first seven prediction
metadata records suggests one concrete alternate interpretation: the chart's
preprocessing component includes capture/load time. For example, 3.895 ms
capture plus 2.249 ms preprocessing corresponds to the first chart's rounded
6.144 ms value. This is an outcome-informed diagnostic hypothesis, not an
original preregistration, a measured warmup policy or a historical build ID.

Freeze this follow-up before full-population checking. Use the original
retained chart and decoded image metadata, with the same three orderings,
offsets 0..5 and direct/float32 stage conversions. Replace only preprocessing
with (integer load + integer preprocessing) nanoseconds / 1,000,000. Record
all component matches and all complete-tuple trials, including failures and
ambiguity. Check the separate exact relationship capture_ms = load / 1e6.
Do not fit a tolerance, learn a permutation or add more transformations.

Separately verify every matched chart vector by reading original Parquet
metadata with Polars and reconstructing the declared formula. Check that the
same five omitted members are identified and retain their private IDs.
An exact artifact relationship still cannot establish the publisher's reason
for omission, intent, total latency accounting or model quality.

Also characterize the already flagged box extents: zero versus negative width
and height, score ranges and boundary-center counts. Read only those retained
prediction rows through the checked physical-list view; separately compare
the exact diagnostic row identities and original Polars values. No clipping,
repair, row dropping, image access or reference-accuracy scoring is allowed.

Maximum three files, one million rows each and 1,200 seconds per phase. No
new inference, training, dependency installation, downloads or reserved access.
Keep all failures and costs; retain the original audit's 500-bound freeze.
