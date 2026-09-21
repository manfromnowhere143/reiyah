# Clock and reference evidence

Document ID: `reiyah.clock-alignment.sources`. Version: `0.1.0`.
Research cutoff: 21 September 2026. Exact bytes and terms are in sources.json.

The retained [author paper](https://architect-eca2030.eu/images/pdfs/Online_Publishable_Version.pdf)
is Haas, Solmaz, Reckenzaun and Genser, *ViF-GTAD*, IJRR, DOI
10.1177/02783649231188146 (2023). Its template copyright/date is not publication
metadata. Sections 3.2/3.3.4 put the ego GPS at the rear-axle origin. Section
3.3.6 describes a shared RTK service and a ground-mark/number-plate calibration.
Tables 12–14 describe clock fields and vehicle offsets, but do not establish
the target Time scale or a calibrated inter-vehicle timing residual. No retained
per-run residual record is supplied by those passages. Their absence there is
not proof that no such record exists elsewhere.

The scenario-3 archive PDF describes targets moving away while the ego follows
slowly on the curved road. The paper's shorter scenario summary allows a
stationary ego or the converse. Retain this description difference; neither is
a substitute for measured trajectories or a guaranteed maneuver outcome.

The [ViF-GTAD v2 record](https://doi.org/10.5281/zenodo.7808255), 7 April 2023,
and its README/XLSX/numeric members were retained in compact-motion. Reuse their
exact hashes without copying the bodies. The README identifies the first ego
CSV column as ROS time and describes the target CSV/MAT time as GPS time. This
supports the explicit recorded-label interpretation in PLAN. It does not supply
hardware synchronization accuracy. Workbook antenna offsets and dimensions are
nominal geometry, not footprint/error bounds. The current experiment uses no
coordinates, dimensions, standard deviations or inferred physical offsets.

Public web searches for the exact `novatel_gps_eth`/`InsPvax` driver naming did
not locate an applicable pinned acquisition implementation. A current OEM7
driver or manual would not establish the 2020 ProPak6 configuration. No guessed
driver conversion, GPS-to-UTC adjustment or fitted physical alignment is adopted.
Search results alone remain discovery, not retained scientific evidence.

The compact-motion CSV coordinate discrepancy remains: use MAT values for later
geometry. This experiment consumes only MAT Time and the two ego clock columns.
Physical clearance remains unresolved. A concrete missing record is a paired
hardware timestamp/calibration log naming the target clock scale and the
remaining ego–target timing error for this run. For example, it must say which
ego physical instant corresponds to a particular target Time label, with a
justified residual—not merely make the trajectories overlap.
