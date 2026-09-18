# Preserving a nullable-list prediction export

Version `0.1.0`. The original Parquet files are immutable evidence. The first
PyArrow failures remain failures, with diagnostics retained. A derived view
supports a separate decoder check without replacing those originals.

Parquet stores its physical schema and row-group metadata in a Thrift Compact
footer. An optional `ARROW:schema` key embeds a further Arrow schema hint.
The nullable fixed-size list hint is the compatibility issue reproduced by
the synthetic fixture. Explicit Arrow schema and list-type reader overrides
also failed. A first generic footer rewrite lost unrelated metadata; a later
complete synthetic run rejected a UInt32 physical-type change. Neither
rewrite was accepted for the actual audit.

The final operation locates only FileMetaData field 5, its key/value list.
It removes the one `ARROW:schema` entry, updates that list's element-count
encoding and copies every surviving list item and all other footer fields
verbatim. The field remains present even when its list becomes empty, so
later relative field identifiers remain valid. The original data prefix is
copied exactly; the footer byte length and final marker are recomputed.

The cursor rejects unsupported field types, duplicate field IDs or metadata
keys, absent schema hints, truncation, trailing bytes, overflows, collection
sizes above one million and nesting above 64. Its footer input cap is 64 MiB.
External column-chunk paths and chunks outside the preserved data prefix are
rejected. Surviving unknown fields of supported wire types retain their bytes.

The checker recomputes the exact allowed byte transformation and compares the
complete derived file against it. It also compares the physical schema, every
row-group and column-chunk record, statistics, offsets, row counts and every
other key/value entry through PyArrow metadata inspection. Original and
derived digests, prefix digest and footer sizes are retained separately.

Polars decodes the original. PyArrow decodes the derived view in a separate
phase. Both feed the same logical policy, preserving row order, nulls, byte
values and binary floating-point values in a canonical digest. The audit
checks all fixed list lengths after decoding; it never fills an empty/missing
box with zeros. Independent decoder agreement is a software cross-check,
not independent scientific replication or historical model provenance.

Synthetic controls cover compact collection-count boundaries, explicit and
relative field IDs, nested values, unsigned physical types, preserved unknown
metadata, source mutation and every truncation of a complete tiny footer.
The full synthetic pipeline contains 5,000 expected images in each of three
files and deliberately distinct missing, empty, invalid and duplicate rows.
