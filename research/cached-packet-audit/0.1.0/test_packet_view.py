import json
from pathlib import Path
import tempfile
import unittest

import polars as pl
import pyarrow as pa
import pyarrow.parquet as pq

from packet_core import encoded
from packet_view import check_view, make_view, sha, split_footer


class PhysicalViewControls(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def source(self,extra=False):
        path=self.root/'source.parquet'
        schema=pa.schema([('name',pa.string()),('box2d',pa.list_(pa.float32(),4)),
                          ('score',pa.float32())],metadata={b'kept':b'opaque-value'} if extra else None)
        data=pa.Table.from_pylist([{'name':'a','box2d':[.5,.5,.2,.2],'score':.7},
                                  {'name':'b','box2d':None,'score':None}],schema=schema)
        pq.write_table(data,path)
        return path

    def test_direct_failure_retained_and_complete_view_matches_polars(self):
        source=self.source();before=sha(source)
        with self.assertRaisesRegex(pa.ArrowInvalid,'lists to be of size=4'):
            pq.read_table(source,use_threads=False)
        view,record=make_view(source,self.root/'view')
        self.assertEqual(sha(source),before)
        self.assertEqual(encoded(pl.read_parquet(source).to_dicts()),encoded(pq.read_table(view).to_pylist()))
        self.assertTrue(record['physical_schema_and_row_groups_equal'])

    def test_other_metadata_is_preserved(self):
        source=self.source(extra=True);view,record=make_view(source,self.root/'view')
        self.assertEqual(pq.ParquetFile(view).metadata.metadata,{b'kept':b'opaque-value'})

    def test_prefix_mutation_is_rejected_before_decode(self):
        source=self.source();view,_=make_view(source,self.root/'view')
        value=bytearray(view.read_bytes());value[8]^=1;view.write_bytes(value)
        with self.assertRaisesRegex(ValueError,'prefix changed'):check_view(source,view)

    def test_row_group_change_is_rejected(self):
        source=self.source();view,_=make_view(source,self.root/'view');p=pq.ParquetFile(source)
        altered=self.root/'altered-footer.parquet'
        pq.write_metadata(p.schema_arrow,altered,metadata_collector=[p.metadata,p.metadata],store_schema=False)
        prefix,_=split_footer(source.read_bytes());_,footer=split_footer(altered.read_bytes())
        view.write_bytes(prefix+footer)
        with self.assertRaisesRegex(ValueError,'Footer changes|Row-group'):check_view(source,view)

    def test_external_chunks_rejected(self):
        source=self.source();p=pq.ParquetFile(source);metadata=p.metadata;metadata.set_file_path('/unread/external.parquet')
        external=self.root/'external-metadata.parquet'
        pq.write_metadata(p.schema_arrow,external,metadata_collector=[metadata])
        prefix,_=split_footer(source.read_bytes());_,footer=split_footer(external.read_bytes());source.write_bytes(prefix+footer)
        with self.assertRaisesRegex(ValueError,'External'):make_view(source,self.root/'view')

    def test_missing_serialized_schema_is_not_silently_accepted(self):
        source=self.source();view,_=make_view(source,self.root/'view')
        with self.assertRaisesRegex(ValueError,'schema absent'):make_view(view,self.root/'second')

    def test_existing_output_and_invalid_framing_rejected(self):
        source=self.source();make_view(source,self.root/'view')
        with self.assertRaisesRegex(ValueError,'already exists'):make_view(source,self.root/'view')
        for bad in (b'',b'PAR1'+b'\x00'*4+b'PAR1',b'PAR1'+b'\xff'*4+b'PAR1'):
            with self.assertRaises(ValueError):split_footer(bad)


if __name__=='__main__':unittest.main()
