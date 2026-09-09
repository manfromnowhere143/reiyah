"""Records stay proposals: custody, missing inspection and authority are distinct."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.perception_decision.contract import Invalid, encoded
from tools.perception_discovery import records, custody
from tools.perception_observation import package
from tests.test_perception_observation import fixture


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.req=fixture(self.root);self.package=self.root/'package'
        self.delivery=package.build(self.req,self.package,self.root/'private-custody.json')
        self.sha=self.delivery['seal_sha256'];self.m=json.loads((self.package/'manifest.json').read_bytes())
        self.record=records.draft(self.m,self.sha,'b'*32)

    def rejected(self,fn,code):
        with self.assertRaises(Invalid) as caught:fn()
        self.assertEqual(caught.exception.code,code)

    def submit(self,reviewer='synthetic-reviewer-a',record_id=None):
        r=deepcopy(self.record);r['reviewer_id']=reviewer
        if record_id is not None:r['record_id']=record_id
        r['completed_at']={'state':'reported','utc':'2026-09-09T12:00:00Z'}
        r['reported_exposure']={k:'reported_not_exposed' for k in records.EXPOSURES}
        for row in r['capture_reviews']:row.update(state='inspected',limitations='')
        return r

    def seal(self,record,name='record'):
        path=self.root/(name+'.json');data=encoded(record);path.write_bytes(data);out=self.root/(name+'.sealed.json')
        result=custody.seal_record(path,hashlib.sha256(data).hexdigest(),self.package,self.sha,out)
        return out,result['sealed_record_sha256']

    def proposal(self,r,channel='CAM_FRONT',kind='capture'):
        cap=next(c for c in self.m['captures'] if c['channel']==channel);cid=cap['id']
        window=next(x['window_id'] for x in r['capture_reviews'] if x['capture_id']==cid)
        loc={'kind':kind}
        if kind=='image_region':loc['xyxy']=[0,0,4,3]
        if kind=='point_indices':loc['indices']=[0,1]
        r['proposals'].append({'id':f'proposal-{len(r["proposals"])+1:05d}','window_id':window,
            'description':'Synthetic ambiguous object proposal; no physical judgment.',
            'class_hypotheses':{'state':'unresolved'},'evidence':[{'capture_id':cid,'locator':loc}]})
        return r['proposals'][-1]

    def test_draft_is_unassigned_unreviewed_and_cannot_be_sealed(self):
        result=records.validate(self.record,self.m,self.sha)
        self.assertEqual(result['inspection_states'],{'not_inspected':70})
        self.assertEqual(result['blinding'],'unknown')
        self.assertEqual(result['physical_absence_from_zero_proposals'],'not_established')
        self.rejected(lambda:self.seal(self.record),'DISCOVERY_REVIEWER')
        self.assertFalse((self.root/'record.sealed.json').exists())

    def test_exact_draft_generation_is_deterministic(self):
        a=self.root/'a.json';b=self.root/'b.json'
        first=custody.make_draft(self.package,self.sha,'c'*32,a)
        second=custody.make_draft(self.package,self.sha,'c'*32,b)
        self.assertEqual(a.read_bytes(),b.read_bytes());self.assertEqual(first,second)
        self.assertEqual(first['submission_state'],'unassigned_draft')

    def test_inspection_accounting_requires_all_occurrences_once_and_in_order(self):
        for defect in ('omit','duplicate','order','window','capture'):
            r=self.submit()
            if defect=='omit':r['capture_reviews'].pop()
            if defect=='duplicate':r['capture_reviews'][1]=r['capture_reviews'][0]
            if defect=='order':r['capture_reviews'].reverse()
            if defect=='window':r['capture_reviews'][0]['window_id']='window-9999'
            if defect=='capture':r['capture_reviews'][0]['capture_id']='capture-999999'
            with self.subTest(defect=defect):self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_POPULATION')

    def test_empty_proposals_do_not_establish_empty_scene(self):
        r=self.submit();path,sha=self.seal(r);v=custody.verify_record(path,sha,self.package,self.sha)
        self.assertEqual(v['summary']['proposals'],0)
        self.assertEqual(v['summary']['recorded_capture_inspection'],'reported_complete')
        self.assertEqual(v['summary']['physical_absence_from_zero_proposals'],'not_established')
        self.assertEqual(v['summary']['physical_reference_coverage'],'not_established')

    def test_partial_unviewable_and_uninspected_remain_sealable_but_incomplete(self):
        r=self.submit()
        for row,state in zip(r['capture_reviews'],('partly_inspected','unviewable','not_inspected')):
            row.update(state=state,limitations='Synthetic reason')
        path,sha=self.seal(r);v=custody.verify_record(path,sha,self.package,self.sha)
        self.assertEqual(v['summary']['inspection_states'],{'inspected':67,'partly_inspected':1,'unviewable':1,'not_inspected':1})
        self.assertEqual(v['summary']['recorded_capture_inspection'],'incomplete')

    def test_unavailable_capture_cannot_be_inspected(self):
        r=self.submit();m=deepcopy(self.m);m['captures'][0]['evidence']={'state':'missing'}
        self.rejected(lambda:records.validate(r,m,self.sha),'DISCOVERY_UNAVAILABLE')
        r['capture_reviews'][0].update(state='unviewable',limitations='Missing source file')
        self.assertEqual(records.validate(r,m,self.sha)['recorded_capture_inspection'],'incomplete')

    def test_uninspected_capture_cannot_support_proposal(self):
        r=self.submit();p=self.proposal(r);cid=p['evidence'][0]['capture_id']
        row=next(x for x in r['capture_reviews'] if x['capture_id']==cid);row.update(state='not_inspected',limitations='Not viewed')
        self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_EVIDENCE')
        row['state']='partly_inspected';records.validate(r,self.m,self.sha)

    def test_capture_image_region_and_raw_point_locators_remain_proposals(self):
        r=self.submit();self.proposal(r);self.proposal(r,kind='image_region');self.proposal(r,'LIDAR_TOP','point_indices')
        path,sha=self.seal(r);v=custody.verify_record(path,sha,self.package,self.sha)
        self.assertEqual(v['summary']['proposals'],3);self.assertEqual(v['summary']['human_independence'],'not_established')

    def test_wrong_modality_boolean_and_out_of_range_locators_fail(self):
        for defect in ('lidar_rectangle','camera_points','bool','bounds','degenerate','unknown','extra'):
            r=self.submit();p=self.proposal(r,kind='image_region');e=p['evidence'][0]
            if defect=='lidar_rectangle':e['capture_id']=self.m['captures'][0]['id']
            if defect=='camera_points':e['locator']={'kind':'point_indices','indices':[0]}
            if defect=='bool':e['locator']['xyxy'][0]=False
            if defect=='bounds':e['locator']['xyxy'][2]=5
            if defect=='degenerate':e['locator']['xyxy'][2]=0
            if defect=='unknown':e['locator']={'kind':'world_object_truth'}
            if defect=='extra':e['locator']['object_center']=[1,2,3]
            with self.subTest(defect=defect):self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_LOCATOR')

    def test_point_indices_must_be_unique_sorted_and_within_original_records(self):
        for indices in ([0,0],[1,0],[2],[-1],[True],[],[0.0]):
            r=self.submit();p=self.proposal(r,'LIDAR_TOP','point_indices');p['evidence'][0]['locator']['indices']=indices
            self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_LOCATOR')

    def test_proposal_evidence_must_be_same_window_and_nonempty(self):
        for defect in ('other_window','missing','duplicate','unrecognized'):
            r=self.submit();p=self.proposal(r)
            if defect=='other_window':p['window_id']='window-0002'
            if defect=='missing':p['evidence']=[]
            if defect=='duplicate':p['evidence']*=2
            if defect=='unrecognized':p['evidence'][0]['capture_id']='x'
            self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_EVIDENCE')

    def test_unknown_class_is_not_an_empty_or_confident_label(self):
        r=self.submit();p=self.proposal(r);records.validate(r,self.m,self.sha)
        p['class_hypotheses']={'state':'proposed','values':['car','truck']};records.validate(r,self.m,self.sha)
        for value in ({'state':'proposed','values':[]},{'state':'proposed','values':['unknown']},
                      {'state':'proposed','values':['car','car']},{'state':'unresolved','values':['car']},{'state':'known','value':'car'}):
            p['class_hypotheses']=value;self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_CLASS')

    def test_exposure_unknown_and_contamination_are_retained(self):
        for exposure,expected in [('unknown','unknown'),('reported_exposed','contested')]:
            r=self.submit();r['reported_exposure']['predictions']=exposure
            path,sha=self.seal(r,exposure);v=custody.verify_record(path,sha,self.package,self.sha)
            self.assertEqual(v['summary']['blinding'],expected)
        r=self.submit();r['reported_exposure']['predictions']=False
        self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_EXPOSURE')

    def test_missing_and_unverifiable_time_are_not_replaced_with_sensor_time(self):
        r=self.submit();r['completed_at']={'state':'unrecorded'};records.validate(r,self.m,self.sha)
        for v in ({'state':'reported','utc':'2026-02-30T00:00:00Z'},{'state':'reported','utc':True},{'state':'unrecorded','utc':'2026-09-09T00:00:00Z'}):
            r['completed_at']=v;self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_TIME')

    def test_record_and_package_identity_cannot_be_substituted(self):
        for key,value in [('package_id','d'*32),('package_seal_sha256','e'*64)]:
            r=self.submit();r[key]=value;self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_BINDING')

    def test_pair_with_distinct_handles_does_not_certify_independence_or_release(self):
        p,s=self.seal(self.submit(),'a');q,t=self.seal(self.submit('synthetic-reviewer-b','d'*32),'b')
        result=custody.verify_pair(p,s,q,t,self.package,self.sha)
        self.assertEqual(result['structural_review'],'eligible_for_external_review')
        self.assertEqual(result['human_independence'],'not_established')
        self.assertEqual(result['sealing_before_assisted_exposure'],'not_established')
        self.assertEqual(result['phase_2_release'],'not_authorized_by_this_tool')

    def test_pair_rejects_duplicate_record_and_flags_same_handle(self):
        p,s=self.seal(self.submit(),'a')
        self.rejected(lambda:custody.verify_pair(p,s,p,s,self.package,self.sha),'DISCOVERY_PAIR')
        q,t=self.seal(self.submit(record_id='d'*32),'b');result=custody.verify_pair(p,s,q,t,self.package,self.sha)
        self.assertEqual(result['structural_review'],'needs_resolution')
        self.assertIn('reviewer_handles_not_distinct',result['reasons'])

    def test_pair_reports_incomplete_unknown_exposure_and_missing_completion(self):
        a=self.submit();b=self.submit('synthetic-reviewer-b','d'*32)
        a['capture_reviews'][0].update(state='not_inspected',limitations='Not reviewed')
        b['reported_exposure']['annotations']='unknown';b['completed_at']={'state':'unrecorded'}
        p,s=self.seal(a,'a');q,t=self.seal(b,'b');result=custody.verify_pair(p,s,q,t,self.package,self.sha)
        self.assertEqual(result['reasons'],['record_1_inspection_incomplete','record_2_blinding_unknown','record_2_completion_time_unrecorded'])

    def test_hash_mutation_and_forged_stored_summary_fail(self):
        path,sha=self.seal(self.submit());original=path.read_bytes();path.write_bytes(original+b' ')
        self.rejected(lambda:custody.verify_record(path,sha,self.package,self.sha),'INPUT_DIGEST_MISMATCH')
        v=json.loads(original);v['summary']['human_independence']='established';path.write_bytes(encoded(v));new=hashlib.sha256(path.read_bytes()).hexdigest()
        self.rejected(lambda:custody.verify_record(path,new,self.package,self.sha),'DISCOVERY_SEAL')

    def test_embedded_record_and_canonical_hash_must_agree(self):
        path,_=self.seal(self.submit());v=json.loads(path.read_bytes());v['record']['reviewer_id']='another';path.write_bytes(encoded(v))
        self.rejected(lambda:custody.verify_record(path,hashlib.sha256(path.read_bytes()).hexdigest(),self.package,self.sha),'DISCOVERY_SEAL')

    def test_tampered_package_prevents_record_sealing(self):
        p=next((self.package/'assets').iterdir());p.write_bytes(p.read_bytes()+b'x')
        self.rejected(lambda:self.seal(self.submit()),'OBS_FILE_IDENTITY')
        self.assertFalse((self.root/'record.sealed.json').exists())

    def test_unknown_fields_and_missing_limitations_fail(self):
        r=self.submit();r['approved_by']='someone';self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_SCHEMA')
        r=self.submit();r['capture_reviews'][0].update(state='not_inspected',limitations='')
        self.rejected(lambda:records.validate(r,self.m,self.sha),'DISCOVERY_TEXT')

    def test_source_or_runtime_change_leaves_no_sealed_output(self):
        with patch.object(custody,'source_digest',side_effect=['a'*64,'b'*64]):
            self.rejected(lambda:self.seal(self.submit()),'DISCOVERY_CODE_CHANGED')
        self.assertFalse((self.root/'record.sealed.json').exists())

    def test_existing_draft_or_seal_is_never_overwritten(self):
        path,sha=self.seal(self.submit());original=path.read_bytes()
        self.rejected(lambda:custody.make_draft(self.package,self.sha,'a'*32,path),'OUTPUT_EXISTS')
        self.rejected(lambda:self.seal(self.submit()),'OUTPUT_EXISTS');self.assertEqual(path.read_bytes(),original)


if __name__=='__main__':unittest.main()
