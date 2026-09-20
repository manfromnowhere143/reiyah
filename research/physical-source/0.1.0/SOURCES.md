# Primary-source review, 20 September 2026

Document ID: `reiyah.physical-source.review`. Version: `0.1.0`.
Scope: exposed development research, one source lead and its manufacturer context.
Exact captured bytes, dates, terms and private receipt digests are in
[sources.json](sources.json). A public pointer does not substitute for those bytes.

## Why this source

Berthold, Forkel and Maehlisch describe measured vehicle geometry with multi-actor
RTK/INS reference in [7V-Scanario, arXiv:2609.12871v1](https://arxiv.org/abs/2609.12871v1),
posted 11 September 2026; the work's venue is SDF 2025. Sections II-A, II-D and
III-D describe interpolation, calibration and an error chain. The paper reports
an accuracy check, but the inspected material supplies no underlying check
records. Its model-alignment discussion cites unpublished student work.
Those are concrete leads, not evidence that the records do not exist.

Reiyah's inference: this is a closer input match than bounding-box-only sources,
but the physical observation contract remains unresolved. Accurate navigation
and a visually aligned scan do not alone bound a bumper's position over time.
This is source qualification, not a dataset quality ranking or benchmark result.

## Pin data and documentation separately

The [GitHub documentation](https://github.com/UniBwTAS/7V-Scanario/tree/86d57969d6443740fac4177de3af8e6637f26dfa)
is pinned to `86d57969d6443740fac4177de3af8e6637f26dfa`, tree
`169b0f48832a6dec56dfef8630e6c6af17e87a79`. The nontruncated recursive tree has
17 entries and ten blobs. README and visualization source bytes match their
Git blob IDs; source code was inspected, never executed. The object stream is
asynchronous and WiFi-limited; the display is unsuitable for precise timing.
Meshes use the INS output reference, which need not be the IMU centre.

The [dataset host](https://huggingface.co/datasets/UniBw-AD/7V-Scanario/tree/c131d445f3ea51c9db6ed3e63c64eac762f01d6e)
is separately pinned to `c131d445f3ea51c9db6ed3e63c64eac762f01d6e`.
Its metadata enumerates 37 files: three small metadata files and 34 archives,
totalling 985,337,261,632 archive bytes. The smallest archive is the reduced
mesh bundle, 1,070,666,248 bytes. INS alone is 1,490,317,000 bytes. No listed
archive fits the 8 MiB source or 128 MiB artifact ceiling. This establishes an
access limit for these archives, not absence of other exports or archive members.
No archive bytes, media or mesh contents were acquired. The host's README and
license match their Git blob IDs. [Distribution scope](DISTRIBUTION.md) preserves
the custom terms and the GitHub license-on-request discrepancy.

## Precision and clock semantics

The retained [OxTS RT3000 v3 datasheet](https://www.oxts.com/software/navsuite/documentation/datasheets/RT3000v3_ds.pdf),
page 4, labels RTK position as CEP and angles as one-sigma. It lists 0.03 degrees
for roll/pitch and 0.1 degrees for heading in this edition. Neither is a guaranteed
all-time maximum. The PDF's publication version/date is unspecified; its HTTP
last-modified field is 26 June 2023, which is not a publication-date assertion.
It does not identify every dataset unit, firmware or acquisition configuration.

OxTS's [timing note](https://support.oxts.com/hc/en-us/articles/115005029989-Timing-with-RT-systems),
updated 18 October 2022, describes postprocessed packet timing relative to GPS
as below ten microseconds. That useful statement has narrower scope than an
end-to-end bound on this dataset's ROS message chain. The campaign's correction
settings, clock mapping and residuals still need binding. Do not substitute it
for the previous solver's single constant common-offset assumption.

## Preserve discrepancies and inspection limits

The paper and GitHub README differ on ego vehicle-bus rate (50 versus 20 Hz),
far radar model (UMRR-32 versus UMRR-11) and how INS variants are described.
README start times for scenarios 21 and 23 differ by one second from host
filenames. They are unresolved documentation differences; no timestamp or sensor
model was silently selected for a numerical comparison. The broad angular figure
in the paper also needs an axis- and unit-specific binding before use.

The GitHub tree-by-commit endpoint echoes the supplied commit in its root `sha`;
the separately captured tree-object endpoint names the actual tree digest.
Their entry arrays match. Both are retained, with distinct identifiers.
Remote HTTP Date fields are roughly 73 seconds ahead of the local receipt clock.
They are retained as observations, not used to adjust dataset clocks or claim
clock calibration; command durations use a monotonic clock.

The web renderer could not open the dataset landing page. Bounded direct public
API and metadata captures succeeded. One prematurely dispatched source command
was refused by the supervisor while another command was unfinished; its guard
failure and subsequent retry remain. Discovery-only alternatives, including
ViF-GTAD, were not admitted or presented as retained research evidence.

The [minimum extract specification](minimum-extract.json) names what could make
a later physical study possible. [CONTRACT.md](CONTRACT.md) explains why each
geometry, uncertainty, time and motion field matters. A larger download budget
by itself would not establish any of those scientific premises.
