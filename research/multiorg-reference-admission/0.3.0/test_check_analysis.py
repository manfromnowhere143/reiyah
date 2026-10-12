"""Small authored ledger controls: no producer imports, models or TIFF reads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
import numpy as np
import check_analysis as c

OWNER=Path(__file__).resolve().parents[1]


def put_json(path,obj):
    path.write_text(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')


def fixture(root, *, partial=False):
    rawdir=root/'raw';rawdir.mkdir()
    image='authored-image';shape=[2,514];resized=[1,257];roster=[(0,0),(0,256)]
    ctx={'image_id':image,'shape':shape,'resized':resized,'roster':roster,
         'runner_sha256':'e'*64,'manifest':{'authored':True},'manifest_sha256':'f'*64,
         'bindings':{'image':'a'*64,'faster':'b'*64,'yolo':'c'*64}}
    receipt={'runner_sha256':'e'*64,'status':'failed' if partial else 'complete','returncode':1 if partial else 0,'termination_reason':None}
    observations=[];raw_bytes=0
    for model in ('faster','yolo'):
        stem=hashlib.sha256(c.canonical([image,model])).hexdigest();side=800 if model=='faster' else 416
        tiles=[]
        for ordinal,(row,column) in enumerate(roster):
            if partial and (model!='faster' or ordinal>0):break
            dets=np.array([[[0,0,0,0,.25],[0,0,10,10,.75]]],dtype=np.float32)
            if partial:dets[0,1,2]=0 # Explicit authored high-row geometry refusal.
            labels=np.zeros((1,2),dtype=np.int64);descriptors=[]
            for i,array in enumerate((dets,labels)):
                name=f'raw/{stem}-{ordinal}-{i}.npy';path=root/name
                with path.open('xb') as out:np.save(out,array,allow_pickle=False)
                data=path.read_bytes();raw_bytes+=len(data)
                descriptors.append({'file':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),
                                    'dtype':array.dtype.str,'shape':list(array.shape),'c_order_data_sha256':hashlib.sha256(array.tobytes()).hexdigest()})
            ledger={'image_id':image,'model':model,'ordinal':ordinal,'rescaled_row':row,'rescaled_column':column,
                    'image_shape_hw':shape,'rescaled_shape_hw':resized,'tile_count_expected':2,'resized_side':side,
                    'image_source_sha256':'a'*64,'model_source_sha256':ctx['bindings'][model],
                    'tensor':{'dtype':'<f4','shape':[1,3,side,side],'c_order_data_sha256':'d'*64,'observation_time':'before_session_run'},
                    'raw_outputs':descriptors,'all_raw_rows_completed_before_tile':ordinal*2,'observed_detection_rows':2,
                    'status':'raw_outputs_retained_before_projection'}
            put_json(rawdir/f'{stem}-{ordinal}.json',ledger)
            anomalies={'raw_nonfinite':[],'raw_nonpositive_extent':[0],'conversion_nonfinite':[],'finite_conversion_nonpositive_extent':[]}
            tiles.append({**ledger,'all_raw_rows':2,'high_rows':1,'low_rows':1,'storage_eligible_rows':2,'below_storage_floor_rows':0,
                          'raw_above_half_converted_not_above_half_rows':0,'analysis_original_row_indices':[1],
                          'low_geometry_anomaly_indices':anomalies,'storage_eligible_low_geometry_anomaly_indices':anomalies,
                          'low_transformed_geometry':'not_evaluated_not_claimed_valid'})
        if partial:continue
        extent=12 if model=='faster' else 24
        predictions=[{'id':1,'tile_ordinal':0,'original_row_index':1,'box_xyxy':[0,0,extent,extent],'score':.75},
                     {'id':3,'tile_ordinal':1,'original_row_index':1,'box_xyxy':[512,0,512+extent,extent],'score':.75}]
        image_result={'artifact_id':'reiyah.multiorg.analysis-projection.image','status':'complete','image_id':image,'model':model,
                      'image_shape_hw':shape,'rescaled_shape_hw':resized,'tile_count_expected':2,'tile_count_completed':2,
                      'raw_onnx_rows':4,'completion_scope':c.SCOPE,'storage_output_status':c.STORAGE,
                      'supplemental_protocol_sha256':c.CONTRACT_SHA,'projection_sha256':c.PROJECTION_SHA,
                      'original_worker_sha256':c.ORIGINAL_SHA,'tiles':tiles,'analysis_predictions':predictions,
                      'empty_analysis':False,'analysis_outside_image':2}
        path=root/(stem+'.json');put_json(path,image_result)
        observations.append({'image_id':image,'model':model,'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                             'bytes':path.stat().st_size,'analysis_count':2,'raw_onnx_rows':4,'completion_scope':c.SCOPE})
    if not partial:
        put_json(root/'result.json',{'artifact_id':'reiyah.multiorg.analysis-projection.run','status':'complete',
                                     'completion_scope':c.SCOPE,'storage_output_status':c.STORAGE,'config':c.FIXED_CONFIG,'manifest':ctx['manifest'],
                                     'manifest_sha256':ctx['manifest_sha256'],'runner_sha256':ctx['runner_sha256'],
                                     'original_worker_sha256':c.ORIGINAL_SHA,'projection_sha256':c.PROJECTION_SHA,
                                     'supplemental_protocol_sha256':c.CONTRACT_SHA,'observations':observations,
                                     'raw_array_files_bytes':raw_bytes})
    return ctx,receipt


class CheckerControls(unittest.TestCase):
    def test_complete_authored_pair_and_changed_prediction_rejected(self):
        with tempfile.TemporaryDirectory(dir=OWNER/'verification',prefix='authored-') as folder:
            root=Path(folder);context,receipt=fixture(root)
            result=c.verify_output(root,context,receipt,time.monotonic()+30)
            self.assertEqual(result['complete_pairs'],1)
            self.assertEqual([x['analysis_count'] for x in result['models']],[2,2])
            top=json.loads((root/'result.json').read_text());item=top['observations'][0];path=root/item['file']
            data=json.loads(path.read_text());data['analysis_predictions'][0]['score']=.8;put_json(path,data)
            item.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size);put_json(root/'result.json',top)
            with self.assertRaisesRegex(c.Refusal,'predictions mismatch'):c.verify_output(root,context,receipt,time.monotonic()+30)

    def test_partial_high_geometry_refusal_is_zero_complete(self):
        with tempfile.TemporaryDirectory(dir=OWNER/'verification',prefix='authored-') as folder:
            root=Path(folder);context,receipt=fixture(root,partial=True)
            result=c.verify_output(root,context,receipt,time.monotonic()+30)
            self.assertEqual(result['complete_pairs'],0)
            self.assertEqual(result['terminal_semantic_refusal']['independently_observed_violation'],'undefined high-score geometry')
            self.assertEqual(result['models'][0]['raw_rows_in_retained_tiles'],2)
            self.assertEqual(result['models'][0]['qualified_tiles'],0)
            self.assertEqual(result['models'][1]['retained_tiles'],0)

    def test_raw_tamper_missing_tile_and_wrong_anomaly_rejected(self):
        for mutation in ('raw','missing','anomaly'):
            with self.subTest(mutation=mutation),tempfile.TemporaryDirectory(dir=OWNER/'verification',prefix='authored-') as folder:
                root=Path(folder);context,receipt=fixture(root)
                if mutation=='raw':
                    path=next((root/'raw').glob('*.npy'));data=bytearray(path.read_bytes());data[-1]^=1;path.write_bytes(data)
                elif mutation=='missing':
                    path=next((root/'raw').glob('*-0.json'));path.unlink()
                else:
                    top=json.loads((root/'result.json').read_text());item=top['observations'][0];path=root/item['file'];obj=json.loads(path.read_text())
                    obj['tiles'][0]['low_geometry_anomaly_indices']['raw_nonpositive_extent']=[];put_json(path,obj)
                    item.update(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size);put_json(root/'result.json',top)
                with self.assertRaises(c.Refusal):c.verify_output(root,context,receipt,time.monotonic()+30)


if __name__=='__main__':unittest.main(verbosity=2)
