# Fixed navigation-tail source record

Document: reiyah.navigation-measurement.sources, version 0.2.0.
Status: retained partial numeric source and reused private documentation.

The primary [manufacturer repository](https://github.com/OxfordTechnicalSolutions/NCOMdecoder/tree/6bd95e9a5f826556e1c4c0bc586fec3f973c76e3)
at commit 6bd95e9a5f826556e1c4c0bc586fec3f973c76e3, dated 26 November 2020,
supplies example/171019_031603.ncom, decoder sources and source instructions.
The retained tree declares 8,205,840 bytes and Git blob
1f0f7cce3dac5776c2924305cd33cd2bd7b3fd04. Exact HTTP range 8,133,840 through
8,205,839 provides the last 72,000 bytes. Its SHA-256 identifies only that slice;
the full Git blob and physical collection provenance are not verified.

The [official NCOM manual](https://www.oxts.com/software/navsuite/documentation/manuals/NCOM_man.pdf),
revision 260702, and unchanged manufacturer C decoder are reused from the
closed first attempt, with exact body identities and original capture receipts.
Use stored reported GPS minutes and millisecond fields literally. Do not infer
UTC, clock calibration, vehicle geometry, physical accuracy or uncertainty coverage.
The source status, clock, checksum and signed-value sentinel rules remain those
of the inherited method, checked separately against the vendor implementation.

All emitted decoder row indices and byte offsets are slice-relative. Add
112,970 to a packet index or 8,133,840 to its byte offset to obtain the original
file location. The question was frozen before this tail capture and its values
remain uninspected until frozen execution. The initial mode-2-only prefix and
all failures stay retained in versions 0.1.0/0.1.1. This exploratory follow-up
does not erase that blocked selection or authorize a further window search.
See [the ledger](sources.json), [question](QUESTION.md) and
[distribution boundary](DISTRIBUTION.md). All payloads stay private.
