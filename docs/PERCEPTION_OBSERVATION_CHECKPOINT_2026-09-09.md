# Raw observation disclosure checkpoint

Document ID: `reiyah.perception-observation.checkpoint-note`

Version: `0.1.0`

Lifecycle status: `exploratory`

The Engine can now assemble and verify a restricted raw-evidence package for unassisted
object discovery. Source identifiers and method/reference hints stay in separate private
custody. The package contains permitted raw evidence, neutral identifiers, relative times,
nominal coordinate operands and explicit unavailable states.

The two previously exposed development windows produced **725 delivered captures: 566 camera
images and 159 lidar files**. Every JPEG is byte-identical to its verified source. Each lidar
export prepends a fixed PLY header to the unchanged five-float point records. The total
delivered asset size is 187,657,462 bytes, including 26,076 bytes of headers. No study cohort,
human observation, object label or new detector evaluation was generated.

See the [interface and failure semantics](../research/perception-observation/0.1.0/README.md),
[machine checkpoint](../research/perception-observation/0.1.0/checkpoint.json) and
[implementation](../tools/perception_observation/package.py). The preceding
[geometry checkpoint](PERCEPTION_GEOMETRY_CHECKPOINT_2026-09-09.md) supplies the bound nominal
transforms and their physical limits.

The disclosure contract is closed. Unknown upstream prose is never copied through. All
required captures retain their place when a file is missing, unavailable, corrupt, undecoded
or outside the camera metadata profile. Camera metadata checks cover the entire scan envelope,
not just the header exposed by an image library. Extra application data, comments, thumbnails
or trailing payloads are withheld without modifying the source image.

The completion seal is written last and its expected digest is retained separately. A fresh
verifier process checks the exact package tree and every delivered file. The known-bad checks
include changing source paths/clocks without changing permitted evidence, hidden post-scan
metadata, raw mutation after prior decoding, symlinks, unexpected files, malformed geometry,
incomplete construction and attempted output reuse.

This is engineering evidence about disclosure, identity and decoding. It is not evidence of
complete physical visibility, independent reviewers, successful object discovery or scientific
efficacy. Public-source images and geometry may still identify the source dataset. Blinding
remains a declared information restriction and human procedure, not an anonymity guarantee.
The two open-reference paired-loss enclosures remain [-8,8] under unit penalties.

Next: bind unassisted discovery records to the exact package, preserving unviewed and unresolved
observations, and seal both reviewers' records before any assisted information is released.
Structural validation must not manufacture reviewer independence or physical completeness.
Independent reviewers, comparator, adjudication and the complete freeze precede the proposed
60-scene study. Gate A remains unaccepted. Console work and the separate research lane retain
their owners; no claim-register entries or historical empirical transcripts change here.
