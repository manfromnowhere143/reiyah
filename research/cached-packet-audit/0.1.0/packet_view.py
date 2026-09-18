"""A retained physical-list view; source data pages are never rewritten."""
import hashlib
from pathlib import Path
import struct

from packet_core import encoded, require
from compact_footer import remove_arrow_schema


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def split_footer(raw):
    require(len(raw) >= 12 and raw[:4] == raw[-4:] == b'PAR1', 'Unsupported Parquet framing')
    length = struct.unpack('<I', raw[-8:-4])[0]
    require(0 < length <= len(raw)-12, 'Invalid footer length')
    return raw[:-length-8], raw[-length-8:]


def physical_identity(metadata):
    return {'num_rows': metadata.num_rows, 'num_columns': metadata.num_columns,
            'num_row_groups': metadata.num_row_groups, 'format_version': metadata.format_version,
            'row_groups': [metadata.row_group(i).to_dict() for i in range(metadata.num_row_groups)]}


def check_view(source, derived):
    import pyarrow.parquet as pq
    raw, view = source.read_bytes(), derived.read_bytes()
    prefix, footer = split_footer(raw); other_prefix, other_footer = split_footer(view)
    require(prefix == other_prefix, 'Data prefix changed')
    expected_footer, patch = remove_arrow_schema(footer[:-8])
    require(other_footer==expected_footer+struct.pack('<I',len(expected_footer))+b'PAR1',
            'Footer changes exceed the declared schema-hint removal')
    old, new = pq.ParquetFile(source), pq.ParquetFile(derived)
    require(old.schema.equals(new.schema), 'Physical schema changed')
    require(encoded(physical_identity(old.metadata)) == encoded(physical_identity(new.metadata)),
            'Row-group or column-chunk metadata changed')
    original_kv = old.metadata.metadata or {}
    require(b'ARROW:schema' in original_kv, 'Original serialized Arrow schema absent')
    require((new.metadata.metadata or {}) == {k:v for k,v in original_kv.items() if k != b'ARROW:schema'},
            'Non-Arrow metadata changed')
    for i in range(old.metadata.num_row_groups):
        group = old.metadata.row_group(i)
        for j in range(group.num_columns):
            column = group.column(j)
            require(column.file_path in ('', None), 'External column chunks are unsupported')
            start = column.dictionary_page_offset if column.has_dictionary_page else column.data_page_offset
            require(type(start) is int and 4 <= start < len(prefix)
                    and start + column.total_compressed_size <= len(prefix), 'Chunk outside retained prefix')
    return {'source_sha256': sha(source), 'derived_sha256': sha(derived),
            'source_bytes': len(raw), 'derived_bytes': len(view),
            'unchanged_data_prefix_bytes': len(prefix),
            'unchanged_data_prefix_sha256': hashlib.sha256(prefix).hexdigest(),
            'original_footer_bytes_including_trailer': len(footer),
            'derived_footer_bytes_including_trailer': len(other_footer),
            'removed_schema_sha256': hashlib.sha256(original_kv[b'ARROW:schema']).hexdigest(),
            'source_created_by': old.metadata.created_by, 'derived_created_by': new.metadata.created_by,
            'footer_patch':patch,
            'physical_schema_and_row_groups_equal': True, 'all_other_metadata_preserved': True,
            'original_file_was_not_modified': True}


def make_view(source, output):
    import pyarrow.parquet as pq
    require(not output.exists(), 'Derived output already exists')
    output.mkdir(parents=True)
    original_hash = sha(source); original = pq.ParquetFile(source)
    original_kv = original.metadata.metadata or {}
    require(b'ARROW:schema' in original_kv, 'Original serialized Arrow schema absent')
    for i in range(original.metadata.num_row_groups):
        require(all(original.metadata.row_group(i).column(j).file_path in ('', None)
                    for j in range(original.metadata.row_group(i).num_columns)), 'External chunk path')
    prefix, original_footer = split_footer(source.read_bytes())
    patched, _ = remove_arrow_schema(original_footer[:-8])
    footer = patched+struct.pack('<I',len(patched))+b'PAR1'
    derived = output/'physical-list-view.parquet'
    with derived.open('xb') as handle: handle.write(prefix); handle.write(footer)
    require(sha(source) == original_hash, 'Original changed during derivation')
    return derived, check_view(source, derived)
