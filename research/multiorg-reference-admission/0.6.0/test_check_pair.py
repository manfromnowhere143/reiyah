"""Authored saved-pair controls: no models, producer imports, or external I/O."""
import copy
import json
from pathlib import Path
import tempfile
import time
import unittest
import numpy as np
import check_pair as c
from test_admit_tile import fixture


def write(path,obj):path.write_bytes(c.canonical(obj)+b'\n')
def descriptor(path,array,name,root):
    with path.open('wb') as f:np.save(f,array,allow_pickle=False)
    return {'name':name,'file':str(path.relative_to(root)),'sha256':c.digest(path.read_bytes()),'bytes':path.stat().st_size,
            'dtype':array.dtype.str,'shape':list(array.shape),'c_order_data_sha256':c.digest(array.tobytes(order='C'))}
def ptr(root,path):return {'file':str(path.relative_to(root)),'sha256':c.digest(path.read_bytes()),'bytes':path.stat().st_size}

def packet(root,empty=False):
    (root/'raw').mkdir();(root/'admissions').mkdir();helper=c.admission_module()
    context={'manifest':{'authored_control_only':True},'manifest_sha256':'1'*64,'protocol_sha256':'2'*64,
        'source_bindings':{'authored_control_only':True},'bindings':{k:'3'*64 for k in ('image','faster','yolo')},
        'shape':[2000,2000],'resized':[1000,1000],'padded':[1536,1536],'roster':[(0,0),(0,256)],
        'image_id':c.IMAGE_ID,'runner_sha256':'4'*64,'admission':helper,'tensors':[],'limits':c.LIMITS,'image_contract_sha256':'9'*64}
    for model in ('faster','yolo'):
        for i in range(2):context['tensors'].append({'tensor':{'dtype':'<f4','shape':[1,3,800 if model=='faster' else 416,800 if model=='faster' else 416],'c_order_data_sha256':str(i+5)*64}})
    obs=[];all_desc=[]
    for mi,model in enumerate(('faster','yolo')):
        stem=c.digest(c.canonical([c.IMAGE_ID,model]));side=800 if mi==0 else 416;traces=[];predictions=[];total=0
        for ordinal,col in enumerate((0,256)):
            arrays=fixture(0 if empty else 3) if mi==0 else {'dets':np.array([[[0,0,10,10,.5 if empty else .9],[0,0,0,0,0]]],np.float32),'labels':np.zeros((1,2),np.int64)}
            raw=[descriptor(root/'raw'/f'{stem}-{ordinal}-{i}.npy',a,n,root) for i,(n,a) in enumerate(arrays.items())];all_desc+=raw
            count=1 if empty and mi==0 else 4 if mi==0 else 2
            lows=[0] if empty and mi==0 else [3] if mi==0 else [1]
            highrows=[] if empty else [0,1] if mi==0 else [0]
            lowcount=count-len(highrows);storage=0 if empty and mi==0 else 3 if mi==0 else 1
            ledger={'image_id':c.IMAGE_ID,'model':model,'model_variant':c.VARIANTS[model],'ordinal':ordinal,'rescaled_row':0,'rescaled_column':col,
                'image_shape_hw':context['shape'],'rescaled_shape_hw':context['resized'],'tile_count_expected':2,'resized_side':side,
                'image_source_sha256':'3'*64,'model_source_sha256':'3'*64,'tensor':{**context['tensors'][mi*2+ordinal]['tensor'],'observation_time':'before_session_run'},
                'raw_outputs':raw,'all_raw_rows_completed_before_tile':total,'observed_detection_rows':count,'status':'raw_outputs_retained_before_admission'}
            rp=root/'raw'/f'{stem}-{ordinal}.json';write(rp,ledger)
            anomaly={k:[] for k in ('raw_nonfinite','raw_nonpositive_extent','conversion_nonfinite','finite_conversion_nonpositive_extent')};anomaly['raw_nonpositive_extent']=lows
            trace={**ledger,'status':'tile_analysis_projection_defined','all_raw_rows':count,'high_rows':len(highrows),'low_rows':lowcount,'storage_eligible_rows':storage,
                'below_storage_floor_rows':count-storage,'raw_above_half_converted_not_above_half_rows':0,
                'origin_admission':helper.validate_tile(arrays) if mi==0 else None,'analysis_original_row_indices':highrows,
                'low_geometry_anomaly_indices':anomaly,'storage_eligible_low_geometry_anomaly_indices':{k:[] for k in anomaly},'low_transformed_geometry':'not_evaluated_not_claimed_valid'}
            ap=root/'admissions'/f'{stem}-{ordinal}.json';write(ap,trace);traces.append(trace)
            if not empty:
                for ri in highrows:
                    box=([0,0,12,12] if ri==0 else [25,25,38,38]) if mi==0 else [0,0,24,24]
                    box=[box[0]+2*col,box[1],box[2]+2*col,box[3]]
                    predictions.append({'id':total+ri,'tile_ordinal':ordinal,'original_row_index':ri,'box_xyxy':box,'score':float(np.float32((.8 if ri==0 else .7) if mi==0 else .9))})
            total+=count
        predictions.sort(key=lambda x:(-x['score'],x['id']))
        img={'artifact_id':'reiyah.multiorg.complete-analysis-image','version':'0.6.0','status':'complete','completion_scope':c.SCOPE,'storage_output_status':c.STORAGE,
            'image_id':c.IMAGE_ID,'model':model,'model_variant':c.VARIANTS[model],'model_source_sha256':'3'*64,
            'image_shape_hw':context['shape'],'rescaled_shape_hw':context['resized'],'tile_count_expected':2,'tile_count_completed':2,'raw_onnx_rows':total,
            'protocol_sha256':'2'*64,'projection_sha256':c.PROJECTION_SHA,'original_worker_sha256':c.ORIGINAL_SHA,'providers':['CPUExecutionProvider'],
            'onnx_output_names':list(arrays),'tiles':traces,'analysis_predictions':predictions,'empty_analysis':empty,'analysis_outside_image':0}
        ip=root/(stem+'.json');write(ip,img)
        obs.append({**ptr(root,ip),'image_id':c.IMAGE_ID,'model':model,'model_variant':c.VARIANTS[model],'analysis_count':len(predictions),'raw_onnx_rows':total,'completion_scope':c.SCOPE})
    record={'artifact_id':'reiyah.multiorg.complete-analysis-pair','version':'0.6.0','status':'complete','stage':'complete','completion_scope':c.SCOPE,'storage_output_status':c.STORAGE,
        'image_id':c.IMAGE_ID,'image_contract_sha256':'9'*64,'config':c.FIXED_CONFIG,'manifest':context['manifest'],'manifest_sha256':'1'*64,'source_bindings':context['source_bindings'],'runner_sha256':'4'*64,'protocol_sha256':'2'*64,
        'original_worker_sha256':c.ORIGINAL_SHA,'projection_sha256':c.PROJECTION_SHA,'model_variants':c.VARIANTS,'expected_tiles_per_model':2,
        'actual_tile_roster':[[0,0],[0,256]],'actual_image_shapes':{'original':context['shape'],'rescaled':context['resized'],'padded':context['padded']},
        'fallback_policy':'constructor_enable_fallback_false_and_session_disable_fallback; no hidden retry','observations':obs,
        'tile_coverage':{m:{'captured':2,'admitted':2,'complete':True} for m in ('faster','yolo')},'last_raw_receipt':ptr(root,rp),'last_admission_receipt':ptr(root,ap),
        'wall_seconds':1.0,'forward_passes_started':4,'forward_passes_completed':4,'raw_array_files_bytes':sum(x['bytes'] for x in all_desc),'raw_array_file_count':len(all_desc)}
    write(root/'result.json',record)
    return context,{'status':'complete','returncode':0,'termination_reason':None,'runner_sha256':'4'*64,'manifest_sha256':'1'*64,'result_sha256':c.digest((root/'result.json').read_bytes()),'network_boundary':'worker_only_host_observer_outside_sandbox','policy_sha256':'5c358b8d847211333e7ba22df82d84f796b5f30a41a2682209a949d783adbd08','wall_seconds':1.5,'peak_sampled_rss_bytes':1000000}

class Tests(unittest.TestCase):
    def setUp(self):self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name);self.ctx,self.process=packet(self.root)
    def tearDown(self):self.temp.cleanup()
    def check(self):return c.verify_output(self.root,self.ctx,self.process,time.monotonic()+30)
    def test_hand_calculated_complete_pair(self):
        r=self.check();self.assertEqual(r['complete_pairs'],1);self.assertEqual([x['analysis_count'] for x in r['models']],[4,2]);self.assertEqual(r['raw_array_files_checked'],70)
    def test_missing_raw_and_admission(self):
        for folder,pattern in [('raw','*.npy'),('admissions','*.json')]:
            path=next((self.root/folder).glob(pattern));data=path.read_bytes();path.unlink()
            with self.subTest(folder=folder),self.assertRaises((ValueError,OSError)):self.check()
            path.write_bytes(data)
    def test_orphan_duplicate_file(self):
        p=next((self.root/'raw').glob('*.npy'));(p.parent/'duplicate.npy').write_bytes(p.read_bytes())
        with self.assertRaisesRegex(c.Refusal,'orphan'):self.check()
    def test_reordered_names_shifted_tensor_origin_score(self):
        path=sorted((self.root/'raw').glob('*.json'))[0];original=json.loads(path.read_bytes())
        for mode in ('names','descriptors','tensor','origin','boolordinal','score'):
            data=copy.deepcopy(original)
            if mode=='names':data['raw_outputs'][0]['name']='different'
            elif mode=='descriptors':data['raw_outputs'].reverse()
            elif mode=='tensor':data['tensor']['c_order_data_sha256']='f'*64
            elif mode=='origin':data['rescaled_column']+=1
            elif mode=='boolordinal':data['ordinal']=False
            else:
                d=data['raw_outputs'][0];p=self.root/d['file'];old=p.read_bytes();a=np.load(p);a[0,0,4]=.99;data['raw_outputs'][0]=descriptor(p,a,d['name'],self.root)
            write(path,data)
            with self.subTest(mode=mode),self.assertRaises(c.Refusal):self.check()
            write(path,original)
            if mode=='score':p.write_bytes(old)
    def test_reordered_complete_tiles(self):
        p=next(x for x in self.root.glob('*.json') if x.name!='result.json');obj=json.loads(p.read_bytes());obj['tiles'].reverse();write(p,obj)
        with self.assertRaises(c.Refusal):self.check()
    def test_altered_raw_bytes(self):
        p=next((self.root/'raw').glob('*.npy'));raw=bytearray(p.read_bytes());raw[-1]^=1;p.write_bytes(raw)
        with self.assertRaisesRegex(c.Refusal,'digest'):self.check()
    def test_false_zero_and_row_identity(self):
        p=next(x for x in self.root.glob('*.json') if x.name!='result.json');old=json.loads(p.read_bytes())
        for mode in ('falsezero','rowid'):
            obj=copy.deepcopy(old)
            if mode=='falsezero':obj['empty_analysis']=True;obj['analysis_predictions']=[]
            else:obj['analysis_predictions'][0]['id']+=1
            write(p,obj)
            with self.subTest(mode=mode),self.assertRaises(c.Refusal):self.check()
        write(p,old)
    def test_true_complete_empty(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);ctx,receipt=packet(root,True);r=c.verify_output(root,ctx,receipt,time.monotonic()+30)
            self.assertEqual(r['complete_pairs'],1);self.assertEqual([x['analysis_count'] for x in r['models']],[0,0])
    def test_high_invalid_partial_not_empty(self):
        stem=c.digest(c.canonical([c.IMAGE_ID,'yolo']));rp=self.root/'raw'/f'{stem}-0.json';ledger=json.loads(rp.read_bytes());desc=ledger['raw_outputs'][0];p=self.root/desc['file'];a=np.load(p);a[0,0,:4]=0
        ledger['raw_outputs'][0]=descriptor(p,a,'dets',self.root);write(rp,ledger)
        for p in (self.root/'raw').glob(stem+'-1*'):p.unlink()
        for p in (self.root/'admissions').glob(stem+'-*'):p.unlink()
        (self.root/(stem+'.json')).unlink()
        result=json.loads((self.root/'result.json').read_bytes());(self.root/'result.json').unlink()
        result.update(status='failed',stage='tile_admission',active_model='yolo',active_tile_ordinal=0,forward_passes_started=3,forward_passes_completed=3)
        result['observations']=result['observations'][:1];result['tile_coverage']['yolo']={'captured':1,'admitted':0,'complete':False};result['last_raw_receipt']=ptr(self.root,rp)
        fs=c.digest(c.canonical([c.IMAGE_ID,'faster']));result['last_admission_receipt']=ptr(self.root,self.root/'admissions'/f'{fs}-1.json')
        write(self.root/'failure.json',result);self.process.update(status='failed',returncode=1)
        r=self.check();self.assertEqual(r['complete_pairs'],0);self.assertEqual(r['terminal_semantic_refusal']['model'],'yolo');self.assertEqual(r['models'][1]['qualified_tiles'],0)
    def test_duplicate_json_keys(self):
        (self.root/'result.json').write_text('{"status":"complete","status":"failed"}')
        with self.assertRaisesRegex(c.Refusal,'duplicate'):self.check()
    def test_process_bindings_policy_and_resource_mutations(self):
        old=copy.deepcopy(self.process)
        mutations={'manifest_sha256':'0'*64,'result_sha256':'0'*64,'policy_sha256':'0'*64,
            'network_boundary':'unconfined','peak_sampled_rss_bytes':3221225473,'wall_seconds':float('inf'),'returncode':False}
        for key,value in mutations.items():
            self.process={**old,key:value}
            with self.subTest(key=key),self.assertRaises(c.Refusal):self.check()
        self.process=old
    def test_worker_wall_bound_and_outer_preflight_difference(self):
        self.process['wall_seconds']=601.5
        self.assertEqual(self.check()['complete_pairs'],1)
        path=self.root/'result.json';r=json.loads(path.read_bytes());r['wall_seconds']=600.001;write(path,r)
        self.process['result_sha256']=c.digest(path.read_bytes())
        with self.assertRaisesRegex(c.Refusal,'worker wall'):self.check()
    def test_symlink_raw_directory(self):
        raw=self.root/'raw';raw.rename(self.root/'original_raw');raw.symlink_to(self.root/'original_raw',target_is_directory=True)
        with self.assertRaises(c.Refusal):self.check()
    def test_global_cross_tile_nms_tie_and_threshold(self):
        rows=[{'box':list(map(np.float32,b)),'score':np.float32(s),'id':i} for i,(b,s) in enumerate([([0,0,10,10],.8),([0,0,10,10],.8),([0,0,5,10],.7)])]
        self.assertEqual([r['id'] for r in c.scalar_nms(rows,time.monotonic()+30)],[0,2])
    def test_finite_low_vs_high_geometry(self):
        d=np.array([[[0,0,0,0,.5],[0,0,1,1,.6]]],np.float32);labels=np.zeros((1,2),np.int64)
        self.assertEqual(c.scalar_tile(d,labels,0,0,416,20)['high_rows'],1)
        d[0,0,4]=np.nextafter(np.float32(.5),np.float32(1))
        with self.assertRaisesRegex(c.Refusal,'high-score'):c.scalar_tile(d,labels,0,0,416,20)

if __name__=='__main__':unittest.main()
