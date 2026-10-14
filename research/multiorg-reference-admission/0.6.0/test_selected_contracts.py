"""Authored protocol rejection controls for the exact three-image extension."""
import copy
import hashlib
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import check_pair as c
import reconstruct_inputs as r


def protocol(image):
    facts=r.image_contract(image)
    pins={'original':c.ORIGINAL_SHA,'projection':c.PROJECTION_SHA,'taps':c.TAPS_SHA,'origin_reference':c.ADMISSION_SHA,'reference_core':c.CORE_SHA}
    p={'artifact_id':'reiyah.multiorg.complete-pair-protocol','version':'0.6.0','worker_contract':'selected_cohort_analysis_pair_v060','image_id':image,
       'shapes':copy.deepcopy(facts['shapes']),'tile_roster':copy.deepcopy(facts['tile_roster']),'model_variants':dict(c.VARIANTS),'model_order':['faster','yolo'],
       'config':dict(c.FIXED_CONFIG),'component_sha256':pins.copy(),'array_budget':dict(facts['array_budget']),'limits':dict(facts['limits'])}
    return facts,pins,p


class Tests(unittest.TestCase):
    def test_exact_three_positive_protocols(self):
        self.assertEqual(list(r.IMAGE_FACTS),['MultiOrg_v2/test/Macros/Plate_23/image_0/image_0.tiff','MultiOrg_v2/test/Normal/Plate_31/image_6/image_6.tiff','MultiOrg_v2/test/Macros/Plate_23/image_1/image_1.tiff'])
        for image in r.IMAGE_FACTS:
            facts,pins,p=protocol(image);c.validate_protocol(p,image,facts,pins)
            self.assertEqual(len(facts['tile_roster']),156);self.assertEqual(facts['array_budget']['derived_maximum_bytes'],66823136)
    def test_first_closed_image_unknown_and_nonstring_refused(self):
        for image in ('MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff','invented',None,False,1):
            with self.subTest(image=image),self.assertRaises(ValueError):r.image_contract(image)
    def test_cross_image_protocol_rebinding_refused(self):
        ids=list(r.IMAGE_FACTS)
        for image,other in zip(ids,ids[1:]+ids[:1]):
            facts,pins,p=protocol(image);p['image_id']=other
            with self.assertRaises(c.Refusal):c.validate_protocol(p,image,facts,pins)
    def test_missing_duplicate_reordered_shifted_roster(self):
        image=next(iter(r.IMAGE_FACTS));facts,pins,original=protocol(image)
        for kind in ('missing','duplicate','reordered','shifted','boolean'):
            p=copy.deepcopy(original)
            if kind=='missing':p['tile_roster'].pop()
            elif kind=='duplicate':p['tile_roster'][-1]=p['tile_roster'][0]
            elif kind=='reordered':p['tile_roster'].reverse()
            elif kind=='shifted':p['tile_roster'][9][1]+=1
            else:p['tile_roster'][0][0]=False
            with self.subTest(kind=kind),self.assertRaises(c.Refusal):c.validate_protocol(p,image,facts,pins)
    def test_shape_budget_version_variant_and_checker_dependencies(self):
        image=next(iter(r.IMAGE_FACTS));facts,pins,original=protocol(image)
        changes=[('shapes','original',[5720,6384]),('limits','wall_seconds',601),('limits','memory_bytes',3221225473),
           ('array_budget','total_bytes',268435456),('array_budget','derived_maximum_bytes',66823135),('array_budget','derivation_sha256','0'*64),
           ('component_sha256','origin_reference','0'*64),('model_variants','faster','original'),('config','analysis_score_gt',.49)]
        for section,key,value in changes:
            p=copy.deepcopy(original);p[section][key]=value
            with self.subTest(section=section,key=key),self.assertRaises(c.Refusal):c.validate_protocol(p,image,facts,pins)
        for key,value in [('version','0.5.0'),('worker_contract','complete_first_image_analysis_pair_v050'),('extra',True)]:
            p=copy.deepcopy(original);p[key]=value
            with self.assertRaises(c.Refusal):c.validate_protocol(p,image,facts,pins)
    def test_whole_source_bytes_not_header_prefix_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'image';p.write_bytes(b'abcX');rp=Path(tmp)/'roster';rp.write_bytes(b'{}')
            facts={'image_bytes':4,'image_sha256':hashlib.sha256(b'abcY').hexdigest(),'input_roster_sha256':hashlib.sha256(b'{}').hexdigest()}
            with patch.object(r,'image_contract',return_value=facts),self.assertRaisesRegex(ValueError,'image digest'):
                r.check(p,rp,time.monotonic()+30,'authored_source_control')
    def test_source_roster_hash_cannot_be_rebound(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'image';p.write_bytes(b'abcd');rp=Path(tmp)/'roster';rp.write_bytes(b'{} ')
            facts={'image_bytes':4,'image_sha256':hashlib.sha256(b'abcd').hexdigest(),'input_roster_sha256':hashlib.sha256(b'{}').hexdigest()}
            with patch.object(r,'image_contract',return_value=facts),self.assertRaisesRegex(ValueError,'prospective roster digest'):
                r.check(p,rp,time.monotonic()+30,'authored_source_control')
    def test_cross_image_output_metadata_refused(self):
        from test_check_pair import packet,write
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);ctx,process=packet(root);p=root/'result.json';original=json.loads(p.read_bytes())
            for key,value in [('image_id',list(r.IMAGE_FACTS)[1]),('image_contract_sha256','0'*64)]:
                obj=copy.deepcopy(original);obj[key]=value;write(p,obj);process['result_sha256']=c.digest(p.read_bytes())
                with self.subTest(key=key),self.assertRaises(c.Refusal):c.verify_output(root,ctx,process,time.monotonic()+30)

if __name__=='__main__':unittest.main()
