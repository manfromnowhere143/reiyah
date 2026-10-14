#!/usr/bin/env python3
"""Separate documented preprocessing reconstruction; no producer/model imports."""
import argparse
import hashlib
import json
import time
from pathlib import Path
import numpy as np

IMAGE_SHA='8828e0a9f94d6c44ea03be2e62623e812830f339d9c905b7a368edcb7e821eb0'
ROSTER_SHA='7de68d1d0f6ca67d143c3db3a40efa3d4d4d70f657d031371229262483a1ce35'
TILE9_SHA='675a5f2aba2565e568feeb93fddc20aaed89a43a9bbeea393bf6336b84ae49d1'

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

def check(image_path,roster_path,deadline):
    import tifffile
    start=time.monotonic();ip=Path(image_path);rp=Path(roster_path)
    need(ip.is_file() and not ip.is_symlink() and ip.stat().st_size==42627969,'image file identity/size')
    image_hash=sha(ip.read_bytes());need(image_hash==IMAGE_SHA,'image digest')
    roster_raw=rp.read_bytes();need(sha(roster_raw)==ROSTER_SHA,'prospective roster digest');r=json_read(rp)
    with tifffile.TiffFile(ip) as tf:
        need(len(tf.series)==1 and np.prod(tf.series[0].shape)<=80000000,'TIFF series/domain')
        data=tf.series[0].asarray()
    q,resized,shape=pixels(data);del data
    rows=[(i,j) for i in range(0,resized[0],256) for j in range(0,resized[1],256)]
    need(len(rows)==156 and r['roster']==[list(x) for x in rows],'full independent tile roster')
    need(r['image_shape_hw']==list(shape) and r['rescaled_shape_hw']==list(resized) and r['padded_shape_hw']==list(q.shape),'image dimensions')
    need(sha(q.tobytes(order='C'))==r['quantized_pixels_c_order_sha256'],'full quantized pixel digest')
    expected=[]
    for model in ('faster','yolo'):
        for ordinal,(row,col) in enumerate(rows):
            need(time.monotonic()<deadline,'reconstruction wall cap')
            td=tensor(q[row:row+512,col:col+512],model)
            if model=='faster' and ordinal==9:need(td['c_order_data_sha256']==TILE9_SHA,'exposed tile9 regression')
            expected.append({'model':model,'ordinal':ordinal,'rescaled_row':row,'rescaled_column':col,'resized_side':800 if model=='faster' else 416,'tensor':td})
    need(expected==r['tensors'],'all312 independently reconstructed tensor identities')
    need(sha(ip.read_bytes())==IMAGE_SHA and sha(rp.read_bytes())==ROSTER_SHA,'source changed during reconstruction')
    return {'status':'all312_tensor_identities_reconstructed','image_sha256':IMAGE_SHA,'input_roster_sha256':ROSTER_SHA,
        'reconstructor_sha256':sha(Path(__file__).read_bytes()),'tensor_count':len(expected),'tiles_per_model':len(rows),
        'quantized_pixels_c_order_sha256':sha(q.tobytes(order='C')),'wall_seconds':time.monotonic()-start,
        'scope':'Separate source-derived pixel implementation, same pinned numerical libraries; zero model inference, not independent scientific replication.'}

def main():
    p=argparse.ArgumentParser()
    for key in ('image','roster','output'):p.add_argument('--'+key,type=Path,required=True)
    a=p.parse_args();need(not a.output.exists(),'new output required');report=check(a.image,a.roster,time.monotonic()+300)
    with a.output.open('x') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report))

if __name__=='__main__':main()
