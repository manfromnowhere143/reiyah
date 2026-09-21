# Retained navigation sources

Document: reiyah.navigation-measurement.sources-note, version 0.1.1.
Status: exploratory, 21 September 2026. Exact private bytes are bound in sources.json.

The prior 7V-Scanario record at Hugging Face revision
c131d445f3ea51c9db6ed3e63c64eac762f01d6e identifies INS/INS.tar.xz. Supported HTTP
Range access retained its 12-byte footer, 136-byte index and 65,536-byte prefix.
The .xz header/footer/index CRCs match; no data-block or whole-archive digest is
verified. The first member is a partial raw RD file. The inspected 126,263-byte
member prefix contains no complete NCOM packet under the stated framing probe.
This is a specific route limitation, not a claim that the whole dataset lacks
usable navigation. No physical cases or decoded vehicle positions ran there.

OxTS's [RD guide](https://support.oxts.com/hc/en-us/articles/360011021920-A-comprehensive-guide-about-RD-files)
describes processing raw logs into navigation outputs. The
[NCOM manual](https://www.oxts.com/software/navsuite/documentation/manuals/NCOM_man.pdf),
revision 260702, describes packet structure, statuses, clocks, scaling and
checksums. Reported accuracy estimates are not silently converted to deterministic
physical bounds. Manufacturer documentation is private; no manual redistribution.

The fallback is the manufacturer's [NCOMdecoder repository](https://github.com/OxfordTechnicalSolutions/NCOMdecoder/tree/6bd95e9a5f826556e1c4c0bc586fec3f973c76e3),
commit 6bd95e9a5f826556e1c4c0bc586fec3f973c76e3, dated 26 November 2020.
Pinned source/header/example/README bodies match their Git blob IDs. The sample
example/171019_031603.ncom is 8,205,840 bytes; only the first 72,000 bytes were
requested and received with an exact HTTP 206 range. The full example blob is
not checksum-verified. No physical collection provenance or calibration is
inferred from the example filename. QUESTION.md predates sample capture.

The [official .xz specification](https://tukaani.org/xz/xz-file-format.txt),
version 1.2.1 dated 8 April 2024, supports the archive format calculation. The
smallest compressed block is 82,328,652 bytes, exceeding the current source cap;
the successful prefix access remains recorded separately. Sources and vendor
code are untrusted adapters. No comparison to a company's private engineering
process, scientific novelty, frontier performance or economic advantage follows.
