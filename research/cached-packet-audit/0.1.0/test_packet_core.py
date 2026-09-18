import copy
import math
import unittest

from packet_core import audit, canonical, encoded, image_state, row_issues


def row(**updates):
    return {'name':'a', 'size':[100,80], 'group':'val', 'label':'car', 'label_index':2,
            'box2d':[.5,.5,.2,.2], 'box2d_score':.7, 'mask':None, 'timing':{'load':10},
            'capture_ms':1., 'e2e_ms':2., 'emit_ts_ns':10, 'sahi_tiles':0,
            'sahi_overlap':None, 'sahi_e2e_ms':None, 'sahi_merge_ms':None, **updates}


EXPECTED={'a':[100,80], 'b':[100,80]}


class LogicalControls(unittest.TestCase):
    def test_missing_is_not_empty(self):
        result=audit([row()],EXPECTED,lambda _:None)
        self.assertEqual(result['states'],{'missing':1,'predictions_present':1})

    def test_explicit_null_placeholder(self):
        empty=row(name='b',label=None,label_index=None,box2d=None,box2d_score=None)
        result=audit([row(),empty],EXPECTED,lambda _:None)
        self.assertEqual(result['states'],{'predictions_present':1,'publisher_empty_placeholder':1})

    def test_every_partial_null_is_invalid(self):
        for key in ('label','label_index','box2d','box2d_score'):
            self.assertIn('partial_null_annotation',row_issues(row(**{key:None}),EXPECTED)[1])

    def test_mixed_empty_and_predictions(self):
        empty=row(label=None,label_index=None,box2d=None,box2d_score=None)
        result=audit([row(),empty],EXPECTED,lambda _:None)
        self.assertEqual(result['images'][0]['state'],'invalid')
        self.assertIn('mixed_empty_and_predictions',result['image_errors'])

    def test_duplicate_empty_is_invalid(self):
        empty=row(label=None,label_index=None,box2d=None,box2d_score=None)
        result=audit([empty,empty],EXPECTED,lambda _:None)
        self.assertEqual(result['images'][0]['state'],'invalid')

    def test_duplicates_are_retained(self):
        result=audit([row(),row()],EXPECTED,lambda _:None)
        self.assertEqual(result['prediction_rows'],2);self.assertEqual(result['duplicates_retained'],1)

    def test_bad_scores(self):
        for v in [float('nan'),float('inf'),-1,1.01,True,'0.4']:
            self.assertIn('invalid_score',row_issues(row(box2d_score=v),EXPECTED)[1])

    def test_invalid_box_length_components_and_extent(self):
        for v in [[0,0,1],[0,0,1,float('nan')],[True,0,1,1]]:
            self.assertIn('invalid_box_tuple',row_issues(row(box2d=v),EXPECTED)[1])
        for v in [[0,0,0,1],[0,0,1,-1]]:
            self.assertIn('nonpositive_box_extent',row_issues(row(box2d=v),EXPECTED)[1])

    def test_outside_is_recorded_without_clipping(self):
        source=row(box2d=[0,.5,.5,.5]);before=copy.deepcopy(source)
        kind,errors,notes=row_issues(source,EXPECTED)
        self.assertEqual(errors,[]);self.assertEqual(source,before)
        self.assertIn('box_extends_outside_normalized_canvas',notes)

    def test_wrong_membership_and_dimensions(self):
        self.assertIn('unknown_image',row_issues(row(name='x'),EXPECTED)[1])
        self.assertIn('image_size_mismatch',row_issues(row(size=[99,80]),EXPECTED)[1])
        self.assertIn('invalid_image_size',row_issues(row(size=[True,80]),EXPECTED)[1])

    def test_index_and_name_bijection(self):
        result=audit([row(),row(label='bus'),row(label_index=9)],EXPECTED,lambda _:None)
        self.assertIn('index_has_multiple_labels',result['row_errors'])
        self.assertIn('label_has_multiple_indices',result['row_errors'])
        self.assertEqual(result['observed_label_indices'],[
            {'index':2,'label':'bus'},{'index':2,'label':'car'},{'index':9,'label':'car'}])

    def test_class_correspondence_keeps_conflicting_pairs(self):
        from packet_run import class_correspondence
        result=class_correspondence([{'index':0,'label':'car'},{'index':0,'label':'bus'}],
                                    [{'id':2,'name':'car'}])
        self.assertEqual(result['observed_indices'],1)
        self.assertEqual(result['observed_index_name_pairs'],2)
        self.assertEqual(result['dense_sorted_categories'],{'matched':1,'mismatched':1})

    def test_metadata_disagreement_is_not_silently_collapsed(self):
        result=audit([row(),row(emit_ts_ns=11)],EXPECTED,lambda _:None)
        self.assertIn('inconsistent_image_metadata',result['row_errors'])

    def test_nonfinite_optional_measurement_is_retained_without_zero(self):
        result=audit([row(capture_ms=float('nan'))],EXPECTED,lambda _:None)
        self.assertIn('nonfinite_float64_bits',result['images'][0]['metadata']['capture_ms'])
        self.assertIn('nonfinite_optional_metadata_retained',result['row_diagnostics'])
        self.assertEqual(result['images'][0]['state'],'predictions_present')

    def test_canonical_preserves_null_float_bits_and_order(self):
        self.assertNotEqual(encoded(0.),encoded(-0.));self.assertNotEqual(encoded(None),encoded(0.))
        self.assertEqual(encoded({'b':1,'a':2}),encoded({'a':2,'b':1}))
        self.assertNotEqual(encoded([1,2]),encoded([2,1]))
        self.assertEqual(canonical(b'\x00\xff'),{'bytes_hex':'00ff'})

    def test_row_cap_failure(self):
        with self.assertRaisesRegex(ValueError,'cap'):audit([row(),row()],EXPECTED,lambda _:None,maximum_rows=1)


if __name__=='__main__':unittest.main()
