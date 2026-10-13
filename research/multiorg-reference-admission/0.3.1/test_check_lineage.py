import copy
import io
import json
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
import numpy as np
import check_lineage as c

def fixture(count=3,reverse=False):
    # A real pre-append row deliberately has all-zero coordinates, like the appended row.
    before=np.array([[float(i),float(i),float(i+1),float(i+1),float((i+1)/(count+2))] for i in range(count)],dtype=np.float32)
    before[0,:4]=0
    if reverse:before[:,4]=before[::-1,4]
    a={'rpn_before':before[None,:,:],'rpn_pad':np.zeros((1,1,5),np.float32)}
    a['rpn_concat']=np.concatenate((a['rpn_before'],a['rpn_pad']),axis=1)
    a['rpn_order']=np.argsort(-a['rpn_concat'][:,:,4],axis=1,kind='stable')[:,:1000].astype(np.int64)
    a['rpn_scores']=a['rpn_concat'][:,:,4][:,a['rpn_order'][0]]
    a['proposals']=a['rpn_concat'][:,a['rpn_order'][0],:]
    n=a['proposals'].shape[1]
    a['rois']=np.concatenate((np.zeros((n,1),np.float32),a['proposals'][0,:,:4]),axis=1)
    fg=np.linspace(.2,.95,n,dtype=np.float32)
    if reverse:fg=fg[::-1].copy()
    a['probabilities']=np.stack((fg,1-fg),axis=-1)[None,:,:]
    a['foreground']=a['probabilities'][:,:,:1].copy()
    a['decoded']=a['proposals'][:,:,:4].copy()
    a['pre_order']=np.argsort(-fg,kind='stable')[None,:].astype(np.int64)
    a['pre_scores']=fg[a['pre_order']]
    a['nms_boxes']=a['decoded'][:,a['pre_order'][0],:]
    a['nms_scores']=np.transpose(a['foreground'][:,a['pre_order'][0],:],(0,2,1))
    # This is an authored observed-NMS output, not an NMS algorithm fixture.
    a['nms_indices']=np.array([[0,0,i] for i in range(n)],dtype=np.int64)
    a['nms_dets']=np.concatenate((a['nms_boxes'],np.transpose(a['nms_scores'],(0,2,1))),axis=2)
    a['nms_labels']=np.zeros((1,n),np.int64)
    a['final_pad']=np.zeros((1,1,5),np.float32);a['final_label_pad']=np.zeros((1,1),np.int64)
    a['final_concat']=np.concatenate((a['nms_dets'],a['final_pad']),axis=1)
    a['label_concat']=np.concatenate((a['nms_labels'],a['final_label_pad']),axis=1)
    a['final_order']=np.argsort(-a['final_concat'][:,:,4],axis=1,kind='stable')[:,:100].astype(np.int64)
    a['final_scores']=a['final_concat'][:,:,4][:,a['final_order'][0]]
    a['dets']=a['final_concat'][:,a['final_order'][0],:].copy()
    a['labels']=a['label_concat'][:,a['final_order'][0]].copy()
    return {c.ALIASES[key]:value for key,value in a.items()}

class Controls(unittest.TestCase):
    def test_equal_geometry_is_not_origin(self):
        r=c.verify(fixture()); zeros=[x for x in r['all_final_rows'] if x['zero_coordinates']]
        self.assertEqual({x['origin'] for x in zeros},{'pre_append_rpn_candidate','rpn_appended_row_through_roi_head','final_appended_padding'})
        self.assertEqual(r['counts'],{'pre_append_rpn_candidate':3,'rpn_appended_row_through_roi_head':1,'final_appended_padding':1})
    def test_reordering_uses_indices(self):
        a,b=c.verify(fixture()),c.verify(fixture(reverse=True))
        self.assertNotEqual(a['all_final_rows'][0]['rpn_concat_row'],b['all_final_rows'][0]['rpn_concat_row'])
        for result in (a,b):
            for row in result['all_final_rows']:
                if row['origin']=='rpn_appended_row_through_roi_head':self.assertEqual(row['rpn_concat_row'],3)
    def test_last_row_not_padding(self):
        r=c.verify(fixture(count=110))
        self.assertEqual(r['final_rows'],100);self.assertEqual(r['counts']['final_appended_padding'],0)
        self.assertEqual(r['all_final_rows'][-1]['origin'],'pre_append_rpn_candidate')
    def test_bad_indices_refused(self):
        for key in ('rpn_order','pre_order','final_order'):
            for value in (-1,100000):
                with self.subTest(key=key,value=value):
                    x=fixture();x[c.ALIASES[key]][0,0]=value
                    with self.assertRaises(c.Refusal):c.verify(x)
        x=fixture();x[c.ALIASES['nms_indices']][0,1]=1
        with self.assertRaises(c.Refusal):c.verify(x)
    def test_duplicate_indices_refused(self):
        x=fixture();x[c.ALIASES['rpn_order']][0,0]=x[c.ALIASES['rpn_order']][0,1]
        with self.assertRaises(c.Refusal):c.verify(x)
    def test_changed_gather_refused(self):
        for key in ('proposals','rois','nms_boxes','nms_dets','dets','labels'):
            with self.subTest(key=key):
                x=fixture();x[c.ALIASES[key]]=x[c.ALIASES[key]].copy();x[c.ALIASES[key]].flat[0]+=1
                with self.assertRaises(c.Refusal):c.verify(x)
    def test_missing_tap_refused(self):
        x=fixture();del x[c.ALIASES['rpn_order']]
        with self.assertRaises(c.Refusal):c.verify(x)
    def test_no_unknown_dtypes(self):
        x=fixture();x[c.ALIASES['rpn_order']]=x[c.ALIASES['rpn_order']].astype(np.float32)
        with self.assertRaises(c.Refusal):c.verify(x)
    def test_graph_binding(self):
        owner=Path(__file__).resolve().parents[1]
        self.assertEqual(c.graph_contract((owner/'graph/GRAPH.json').read_bytes())['model_sha256'],c.MODEL_SHA)
        with self.assertRaises(c.Refusal):c.graph_contract(b'{}')
    def test_reader_bytes_paths_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);a=np.arange(6,dtype=np.float32).reshape(1,6)
            b=io.BytesIO();np.save(b,a,allow_pickle=False);raw=b.getvalue();(root/'a.npy').write_bytes(raw)
            d={'file':'a.npy','bytes':len(raw),'sha256':c.hashlib.sha256(raw).hexdigest(),'dtype':'<f4','shape':[1,6],
                'c_order_data_sha256':c.hashlib.sha256(a.tobytes()).hexdigest()}
            c.same(c.Reader().array(root,d),a,'valid NPY');r=c.Reader();r.array(root,d);self.assertEqual(len(r.unchanged()),1)
            for key,value in [('sha256','0'*64),('shape',[1,7]),('file','../a.npy')]:
                bad=dict(d);bad[key]=value
                with self.assertRaises(c.Refusal):c.Reader().array(root,bad)
            (root/'alias.npy').symlink_to(root/'a.npy');bad=dict(d,file='alias.npy')
            with self.assertRaises(c.Refusal):c.Reader().array(root,bad)
            (root/'a.npy').write_bytes(raw+b'\0')
            with self.assertRaises(c.Refusal):r.unchanged()
    def test_json_duplicate_nan_refused(self):
        for raw in (b'{"a":1,"a":2}',b'{"a":NaN}'):
            with self.assertRaises(c.Refusal):c.json_bytes(raw)
    def test_source_arrays_unchanged(self):
        x=fixture();before={name:array.tobytes() for name,array in x.items()};c.verify(x)
        self.assertEqual(before,{name:array.tobytes() for name,array in x.items()})
    def test_file_integration_completion_and_parity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);tapdata=fixture();descs=[];prior=[]
            def dump(name,value):
                p=root/name;p.write_bytes(json.dumps(value).encode());return {'path':str(p),'sha256':c.hashlib.sha256(p.read_bytes()).hexdigest()}
            def save(name,array):
                p=root/name
                with p.open('wb') as f:np.save(f,array,allow_pickle=False)
                return {'file':name,'bytes':p.stat().st_size,'sha256':c.hashlib.sha256(p.read_bytes()).hexdigest(),
                    'dtype':array.dtype.str,'shape':list(array.shape),'c_order_data_sha256':c.hashlib.sha256(array.tobytes()).hexdigest()}
            for name in ('dets','labels'):prior.append(save('prior-'+name+'.npy',tapdata[name]))
            ledger={'model_source_sha256':c.MODEL_SHA,'tensor':{'c_order_data_sha256':c.TENSOR_SHA},'raw_outputs':prior}
            ledgerref=dump('ledger.json',ledger)
            for stage,names in [('baseline',['dets','labels']),('tapped',list(tapdata))]:
                for ordinal,name in enumerate(names):descs.append(dict(save(stage+str(ordinal)+'.npy',tapdata[name]),name=name,stage=stage))
            roster=[{'name':name,'rank':array.ndim,'elem_type':1 if array.dtype.kind=='f' else 7} for name,array in tapdata.items() if name not in ('dets','labels')]
            result={'status':'complete','stage':'complete','forward_passes_started':2,'forward_passes_completed':2,
                'runner_sha256':'a'*64,'manifest_sha256':'b'*64,'arrays':descs,'saved_array_bytes':sum(d['bytes'] for d in descs),
                'source_bindings':{'baseline':{'sha256':c.MODEL_SHA},'tensor':{'sha256':c.TENSOR_NPY_SHA},
                    'protocol':dump('protocol.json',{'tensor':{'dtype':'<f4','shape':[1,3,800,800],'c_order_data_sha256':c.TENSOR_SHA}}),
                    'taps':dump('taps.json',roster)}}
            def process_for(value):
                resultref=dump('result.json',value)
                return dump('process.json',{'status':'complete','returncode':0,'termination_reason':None,
                    'runner_sha256':value['runner_sha256'],'manifest_sha256':value['manifest_sha256'],'result_sha256':resultref['sha256']})
            process_for(result);graph=Path(__file__).resolve().parents[1]/'graph/GRAPH.json'
            args=(graph,root/'result.json',root/'process.json',root/'ledger.json',root)
            with patch.object(c,'RETAINED_SHA',ledgerref['sha256']):
                self.assertTrue(c.check_files(*args)['prior_baseline_tapped_byte_parity'])
                bad=copy.deepcopy(result);bad['forward_passes_completed']=1;process_for(bad)
                with self.assertRaises(c.Refusal):c.check_files(*args)
                bad=copy.deepcopy(result);bad['source_bindings']['tensor']['sha256']='0'*64;process_for(bad)
                with self.assertRaises(c.Refusal):c.check_files(*args)
                bad=copy.deepcopy(result);desc=next(x for x in bad['arrays'] if x['stage']=='tapped' and x['name']=='dets')
                altered=tapdata['dets'].copy();altered[0,0,4]=.99;desc.update(save(desc['file'],altered));process_for(bad)
                with self.assertRaisesRegex(c.Refusal,'tapped/prior'):c.check_files(*args)

if __name__=='__main__':unittest.main()
