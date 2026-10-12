# Source attribution and artifact terms

MultiOrg: Christina Bukas and coauthors, *MultiOrg: A multi-rater organoid-detection
dataset*, NeurIPS 2024, [arXiv 2410.14612v2](https://arxiv.org/html/2410.14612v2).
Dataset: [DOI 10.34740/kaggle/ds/5097172](https://doi.org/10.34740/kaggle/ds/5097172),
Kaggle platform version 6, internal release `MultiOrg_v2`.

The dataset notice specifies
[Creative Commons Attribution–NonCommercial–ShareAlike 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
The finite study is noncommercial research. Raw annotations and images remain
private; they are not relicensed or distributed by this repository.

MultiOrg-derived annotation counts and per-image summaries in `result.json`,
`verification.json` and the corresponding README table are distributed under
CC BY-NC-SA 4.0. Reiyah's changes consist of structural validation, source-qualified
identity hashing, capacity summaries and recorded selection/admission decisions.
No endorsement by the source authors is implied. Source metadata and integrity
descriptors do not grant additional rights over the referenced payloads.

Model files are separately published by the source under CC BY 4.0 at
[Zenodo 18700540](https://zenodo.org/records/18700540); the compared publication
[18710714](https://zenodo.org/records/18710714) lists matching lengths and MD5s.
Weights remain private. Do not infer weight identity from filename alone.

The maintained method was inspected at
[`napari-organoid-counter` f0866f25](https://github.com/HelmholtzAI-Consultants-Munich/napari-organoid-counter/tree/f0866f254d48099e33b189f4196fcde3ac5408c1).
Its exact LICENSE payload was not retained in this bounded review. No upstream
implementation was copied into this repository; Reiyah code is independently
authored from the stated method and retains the repository's code license.
Numeric tie behavior is specified separately; bitwise upstream parity is not claimed.

Other papers and source bodies remain private. Their descriptors and the original
method synthesis do not redistribute the manuscripts or executable implementations.
