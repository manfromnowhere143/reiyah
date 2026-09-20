# Source custody and interpretation

Document ID: `reiyah.compact-motion.sources`. Version: `0.1.0`.
Review cutoff: 20 September 2026. All captured bodies remain outside public Git.
Exact byte counts, SHA-256 digests and retrieval scope are in [sources.json](sources.json).

## ViF-GTAD v2

Sarah Haas, Selim Solmaz, Jakob Reckenzaun and Simon Genser, Virtual Vehicle
Research GmbH: [ViF-GTAD v2, Zenodo record 7808255](https://zenodo.org/records/7808255),
published 7 April 2023. The retained record assigns CC BY 4.0. The public archive
is `GTAD_Dataset_v2.zip`, 6,745,997,573 bytes, publisher MD5
`82be53b91b4deafb80c8111acd7dd34e`. The full archive was not downloaded and that
whole-archive checksum was not verified.

The public archive endpoint honored HTTP Range. ZIP directory, local headers and
compressed bytes were retrieved under explicit length caps, with exact HTTP 206
Content-Range checks and retained response identities. ZIP member CRCs were
checked by the standard library; each extracted member has its own local SHA-256.
These checks establish retained byte identity, not publisher authenticity or
measurement accuracy. No bag, image or video member was retrieved.

The retained `ReadMe.txt` describes target CSV and MAT as the same GPS data,
ego `GPS_ROS.csv` as a GPS/ROS mapping, and the first ego column as ROS time.
It warns that standard deviations may be NaN or absent in some vehicles.
The notebook was read as source only; it was not executed and its output cells
were not inspected. Its ROS topic example is not a calibration record.

The workbook `LicensePlate_To_GPS_Offset.xlsx`, sheet `Munka1`, gives the front
offset in centimetres (D2), lateral offset in centimetres (E2), and width/length/
height in metres (G2). Ego Ford Fusion is row 16: front offset 399 cm, lateral
offset 0, dimensions 1.853 / 4.871 / 1.474 m. BME Honda CRZ is row 17: 338 cm,
0, and 1.74 / 4.08 / 1.395 m. These are documented values. They do not establish
where every GNSS output has already been lever-arm corrected, a calibrated body
footprint, or a residual pose/geometry error envelope. No workbook cell was edited.

The exact scenario-3 ego CSV and Honda CSV were chosen before numeric retrieval.
After first-row schema exposure, the exact Honda MAT companion was selected
separately to test representation agreement. Its `BME_HondaCorr` cell array has
six columns and an explicit header. Preserve that outcome-informed supplement;
do not describe it as an independent source or a held-out comparison.

## Navigation documentation

[NovAtel INSPVAX documentation](https://docs.novatel.com/OEM7/Content/SPAN_Logs/INSPVAX.htm),
OEM7 D100402 v6, July 2026, was retained as manufacturer context. It describes
position and orientation standard-deviation fields, validity/status fields,
and limitations of filter-reported uncertainty. This is not the older ProPak6
configuration record and does not establish the Honda uncertainty units or
calibrated whole-trajectory coverage. No manufacturer statistics become a
deterministic bound in this analysis.

## Discovery material and limits

The [author-hosted paper](https://architect-eca2030.eu/images/pdfs/Online_Publishable_Version.pdf)
and [published article](https://journals.sagepub.com/doi/abs/10.1177/02783649231188146)
were discovered. The PDF HEAD response declares 5,063,065 bytes. Retaining it
alongside the numeric source would exceed this increment's 8 MiB source budget;
no PDF body was fetched. Its web-rendered text is discovery context, not locally
retained source evidence for this packet. The author PDF's template date is not
treated as its publication date.

The [USNO time-conversion page](https://maia.usno.navy.mil/information/eo-values)
was found, but direct capture ended with a connection reset and zero body bytes.
That failure remains. No GPS-to-UTC conversion depends on this unretained page.
The Ulm two-automobile dataset was another public lead; no payload was fetched
or evaluated. Empty narrow web searches for mirrored ViF files do not establish
that no mirror or additional calibration evidence exists.

The compact capture does not inspect the remaining archive. Calibration and
timestamp records not obtained here are not asserted absent everywhere.
