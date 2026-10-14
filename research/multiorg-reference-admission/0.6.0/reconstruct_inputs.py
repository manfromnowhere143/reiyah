#!/usr/bin/env python3
"""Separate documented preprocessing reconstruction; no producer/model imports."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np

ORIGINAL_SHA='9a708bf6a22e9350980e0d08d0e90c2c56f7b9cc4a73b7fd55f22c9ef3f33e0c'
SHAPES={'original':[5720,6385],'rescaled':[2860,3192],'padded':[3328,3584]}
ROSTER=[[row,col] for row in range(0,2860,256) for col in range(0,3192,256)]
LIMITS={'wall_seconds':600,'memory_bytes':3221225472,'max_tiles_per_image':156,'max_raw_boxes_per_image':200000,'max_array_file_bytes':67108864,'max_array_total_bytes':134217728}
ARRAY_BUDGET={'per_file_bytes':67108864,'total_bytes':134217728,'derived_maximum_bytes':66823136}
# Exact three remaining selected identities. No fallback to another image or cohort.
IMAGE_FACTS={
    'MultiOrg_v2/test/Macros/Plate_23/image_0/image_0.tiff':{
        'image_id':'MultiOrg_v2/test/Macros/Plate_23/image_0/image_0.tiff','image_sha256':'c597643323054fca5152530baf43260661f44c3bd8ef1b69d6c2fce1ca0540e0','image_bytes':44321876,
        'shapes':SHAPES,'tile_roster':ROSTER,'input_roster_sha256':'efa3908afab616f71758433d138943248355b9ad0cd796d7f34c11d2e86971b4','limits':LIMITS,'array_budget':{**ARRAY_BUDGET,'derivation_sha256':'361efd3ad50848ff33ea08b85a283fac9c5254b3af958533fe851872913735db'}},
    'MultiOrg_v2/test/Normal/Plate_31/image_6/image_6.tiff':{
        'image_id':'MultiOrg_v2/test/Normal/Plate_31/image_6/image_6.tiff','image_sha256':'2a690a65a48b6370076758dc2f1af845ea492df6ba3492ba52637362c4d34281','image_bytes':44374655,
        'shapes':SHAPES,'tile_roster':ROSTER,'input_roster_sha256':'6a0cb26a7d367f835963aef22de1760f041bb3e018bf5044defb95993410ed0a','limits':LIMITS,'array_budget':{**ARRAY_BUDGET,'derivation_sha256':'7f10643b61d1ca980614a3fb50c0cbb4fd55143db22d4221bf0306cb95df48d3'}},
    'MultiOrg_v2/test/Macros/Plate_23/image_1/image_1.tiff':{
        'image_id':'MultiOrg_v2/test/Macros/Plate_23/image_1/image_1.tiff','image_sha256':'951baa66c25581f312fe79f592a4b664a5a5d13cb62ffc4ffc5e47e9b1f2a47f','image_bytes':44085526,
        'shapes':SHAPES,'tile_roster':ROSTER,'input_roster_sha256':'238c775a6f209899d17187f2e1e3fedd26b07d3de89af475d147109c80db3cad','limits':LIMITS,'array_budget':{**ARRAY_BUDGET,'derivation_sha256':'7ed00fddf47995cc96040c33e7632484883ce8932094546db9e154f131a7275b'}}}

def image_contract(image_id):
    need(type(image_id) is str and image_id in IMAGE_FACTS,'exact remaining selected image required')
    return IMAGE_FACTS[image_id]

def sha(value):return hashlib.sha256(value).hexdigest()
def need(ok,message):
    if not ok:raise ValueError(message)

def json_read(path):
    def pairs(items):
        out={}
        for k,v in items:need(k not in out,'duplicate JSON key');out[k]=v
        return out
    raw=Path(path).read_bytes();need(len(raw)<=1048576,'JSON byte cap')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))

def pixels(data):
    from skimage.transform import rescale
    plane=np.squeeze(data)
    need(plane.ndim==2 and plane.size<=80000000 and np.isfinite(plane).all(),'image plane domain')
    half=rescale(plane,scale=.5,order=1,mode='reflect',preserve_range=True,anti_aliasing=True,channel_axis=None)
    need(np.isfinite(half).all() and half.max()>half.min(),'nonconstant finite rescale')
    h,w=half.shape;ph=256*(h//256)+512;pw=256*(w//256)+512
    edge=np.pad(half,((0,ph-h),(0,pw-w)),mode='edge')
    lo,hi=edge.min(),edge.max()
    return (255*((edge-lo)/(hi-lo))).astype(np.uint8),(h,w),tuple(plane.shape)

def tensor(tile,model):
    import cv2
    need(tile.shape==(512,512) and tile.dtype==np.uint8,'tile shape/dtype')
    side=800 if model=='faster' else 416
    need(model in ('faster','yolo'),'model identity')
    intermediate=(tile.astype(np.float32)/np.float32(255))*np.float32(255)
    resized=cv2.resize(intermediate.astype(np.uint8),(side,side),interpolation=cv2.INTER_LINEAR)
    channels=np.repeat(resized[None,:,:],3,axis=0).astype(np.float32)[None,:,:,:]
    means=(123.675,116.28,103.53) if model=='faster' else (0,0,0)
    stds=(58.395,57.12,57.375) if model=='faster' else (255,255,255)
    result=np.ascontiguousarray((channels-np.array(means,np.float32).reshape(1,3,1,1))/np.array(stds,np.float32).reshape(1,3,1,1))
    return {'dtype':result.dtype.str,'shape':list(result.shape),'c_order_data_sha256':sha(result.tobytes(order='C'))}

def check(image_path,roster_path,deadline,image_id):
    import tifffile
    start=time.monotonic();ip=Path(image_path);rp=Path(roster_path);facts=image_contract(image_id)
    image_sha=facts['image_sha256'];roster_sha=facts['input_roster_sha256']
    need(ip.is_file() and not ip.is_symlink() and ip.stat().st_size==facts['image_bytes'],'image file identity/size')
    image_hash=sha(ip.read_bytes());need(image_hash==image_sha,'image digest')
    roster_raw=rp.read_bytes();need(sha(roster_raw)==roster_sha,'prospective roster digest');r=json_read(rp)
    need(r.get('artifact_id')=='reiyah.multiorg.complete-pair.input-roster' and r.get('version')=='0.6.0' and r.get('status')=='complete','input roster release')
    need(r.get('image_id')==image_id and r.get('image_source_sha256')==image_sha and r.get('original_worker_sha256')==ORIGINAL_SHA,'input roster source identity')
    with tifffile.TiffFile(ip) as tf:
        need(len(tf.series)==1 and np.prod(tf.series[0].shape)<=80000000,'TIFF series/domain')
        data=tf.series[0].asarray()
    q,resized,shape=pixels(data);del data
    rows=[(i,j) for i in range(0,resized[0],256) for j in range(0,resized[1],256)]
    need(len(rows)==facts['limits']['max_tiles_per_image'] and r['roster']==facts['tile_roster']==[list(x) for x in rows],'full independent tile roster')
    need(list(shape)==facts['shapes']['original'] and list(resized)==facts['shapes']['rescaled'] and list(q.shape)==facts['shapes']['padded'],'fixed image contract shapes')
    need(r['image_shape_hw']==list(shape) and r['rescaled_shape_hw']==list(resized) and r['padded_shape_hw']==list(q.shape),'image dimensions')
    need(sha(q.tobytes(order='C'))==r['quantized_pixels_c_order_sha256'],'full quantized pixel digest')
    expected=[]
    for model in ('faster','yolo'):
        for ordinal,(row,col) in enumerate(rows):
            need(time.monotonic()<deadline,'reconstruction wall cap')
            td=tensor(q[row:row+512,col:col+512],model)
            expected.append({'model':model,'ordinal':ordinal,'rescaled_row':row,'rescaled_column':col,'resized_side':800 if model=='faster' else 416,'tensor':td})
    need(json.dumps(expected,sort_keys=True,separators=(',',':'))==json.dumps(r['tensors'],sort_keys=True,separators=(',',':')),'complete independently reconstructed tensor identities')
    need(sha(ip.read_bytes())==image_sha and sha(rp.read_bytes())==roster_sha,'source changed during reconstruction')
    return {'status':'all_declared_tensor_identities_reconstructed','version':'0.6.0','image_id':image_id,'image_sha256':image_sha,'input_roster_sha256':roster_sha,
        'reconstructor_sha256':sha(Path(__file__).read_bytes()),'tensor_count':len(expected),'tiles_per_model':len(rows),
        'quantized_pixels_c_order_sha256':sha(q.tobytes(order='C')),'wall_seconds':time.monotonic()-start,
        'scope':'Separate source-derived pixel implementation, same pinned numerical libraries; zero model inference, not independent scientific replication.'}

def main():
    p=argparse.ArgumentParser()
    for key in ('image','roster','output'):p.add_argument('--'+key,type=Path,required=True)
    p.add_argument('--image-id',required=True)
    a=p.parse_args();need(not a.output.exists(),'new output required');report=check(a.image,a.roster,time.monotonic()+300,a.image_id)
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))

if __name__=='__main__':main()
