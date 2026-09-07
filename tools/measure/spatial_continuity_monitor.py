#!/usr/bin/env python3
"""Adaptive offline test of past-only spatial support, using a frozen baseline."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from threadpoolctl import threadpool_limits

from build_predictive_monitor_dataset import CLASSES, coverage, greedy_pairs, number, read_json, require
from evaluate_predictive_monitor import history_matrix, losses, metrics, nested_predict, paired_band
from replay_reference_population_audit import digest


def distances(a,b):
    result=np.full((len(a),len(b)),np.inf)
    for i,p in enumerate(a):
        for j,q in enumerate(b):
            if p[0]==q[0]: result[i,j]=math.hypot(p[2]-q[2],p[3]-q[3])
    return result


def paired_sites(camera,lidar):
    return [(camera[i][0],min(camera[i][1],lidar[j][1]),(camera[i][2]+lidar[j][2])/2,
             (camera[i][3]+lidar[j][3])/2) for i,j in greedy_pairs(camera,lidar)]


def velocity_sites(previous,older,past_dt,future_dt):
    require(past_dt>0 and future_dt>0,'invalid projection time')
    d=distances(previous,older)
    sites=[]
    for i,p in enumerate(previous):
        if not len(older): continue
        candidates=np.flatnonzero(d[i]==d[i].min())
        if len(candidates)!=1: continue
        j=int(candidates[0]);reverse=np.flatnonzero(d[:,j]==d[:,j].min())
        if d[i,j]>=10 or len(reverse)!=1 or reverse[0]!=i: continue
        q=older[j];ratio=future_dt/past_dt
        sites.append((p[0],min(p[1],q[1]),p[2]+ratio*(p[2]-q[2]),p[3]+ratio*(p[3]-q[3])))
    return sites


def support(sites,camera,lidar):
    ca,li=distances(sites,camera),distances(sites,lidar)
    nearest_a=np.min(ca,axis=1) if camera else np.full(len(sites),np.inf)
    nearest_b=np.min(li,axis=1) if lidar else np.full(len(sites),np.inf)
    f={'sites':float(len(sites)), 'site_score_mean':float(np.mean([p[1] for p in sites])) if sites else np.nan}
    for radius in (2,4):
        a,b=nearest_a<radius,nearest_b<radius
        silent=~a & ~b
        f.update({f'r{radius}.both_absent':float(silent.sum()),f'r{radius}.one_absent':float(np.count_nonzero(a!=b)),
                  f'r{radius}.both_present':float(np.count_nonzero(a & b)),
                  f'r{radius}.absent_fraction':float(silent.mean()) if len(sites) else np.nan,
                  f'r{radius}.high_score_both_absent':float(sum(p[1]>=.5 and silent[i] for i,p in enumerate(sites)))})
    return f


def geometry_rows(camera,lidar,frames,scenes,times):
    names=None;rows=[None]*len(frames)
    sample_template=support([],[],[])
    for scene in np.unique(scenes):
        ids=np.flatnonzero(scenes==scene);ids=ids[np.argsort(times[ids],kind='stable')]
        require(np.all(np.diff(times[ids])>0),'unordered scene clock')
        for position,index in enumerate(ids):
            token=str(frames[index]);cam,lid=camera[token],lidar[token]
            f={f'{prefix}.{k}':np.nan for prefix in ('stationary','velocity') for k in sample_template}
            f.update({f'{ch}.lost_r{r}':np.nan for ch in ('camera','lidar') for r in (2,4)})
            f.update({'previous_available':float(position>=1),'older_available':float(position>=2),
                      'previous_age_seconds':np.nan,'older_age_seconds':np.nan,'velocity_unassociated_sites':np.nan})
            if position>=1:
                pindex=ids[position-1];prev=str(frames[pindex]);prior=paired_sites(camera[prev],lidar[prev])
                f.update({f'stationary.{k}':v for k,v in support(prior,cam,lid).items()})
                f['previous_age_seconds']=float((times[index]-times[pindex])/1e6)
                for ch,now,old in (('camera',cam,camera[prev]),('lidar',lid,lidar[prev])):
                    d=distances(old,now)
                    nearest=d.min(axis=1) if now else np.full(len(old),np.inf)
                    for radius in (2,4): f[f'{ch}.lost_r{radius}']=float(np.count_nonzero(nearest>=radius))
                if position>=2:
                    oindex=ids[position-2];older=str(frames[oindex]);before=paired_sites(camera[older],lidar[older])
                    f['older_age_seconds']=float((times[index]-times[oindex])/1e6)
                    projected=velocity_sites(prior,before,float(times[pindex]-times[oindex]),float(times[index]-times[pindex]))
                    f.update({f'velocity.{k}':v for k,v in support(projected,cam,lid).items()})
                    f['velocity_unassociated_sites']=float(len(prior)-len(projected))
            if names is None: names=list(f)
            require(list(f)==names,'geometry feature schema changed')
            rows[index]=[f[k] for k in names]
    require(all(row is not None for row in rows),'missing geometry feature row')
    return np.asarray(rows,dtype=float),names


def log_resampled_scene_mean(rows,base,candidate,seed=20260909,repetitions=3000):
    per_scene={}
    for row in rows:
        key=row['log'],row['scene'];a,b,n=per_scene.get(key,(0.,0.,0))
        y=float(row['y'])
        def d(p): return 2*((y*math.log(y/p) if y else 0)-y+p)
        per_scene[key]=(a+d(row['prediction'][base]),b+d(row['prediction'][candidate]),n+1)
    logs=sorted({k[0] for k in per_scene});stats=[]
    for log in logs:
        vals=[(a/n,b/n) for (l,s),(a,b,n) in per_scene.items() if l==log]
        stats.append((sum(a for a,b in vals),sum(b for a,b in vals),len(vals)))
    a,b,n=np.asarray(stats).T
    ix=np.random.default_rng(seed).integers(len(logs),size=(repetitions,len(logs)))
    effect=(a[ix]-b[ix]).sum(axis=1)/n[ix].sum(axis=1)
    relative=1-b[ix].sum(axis=1)/a[ix].sum(axis=1)
    return {'sampling_unit':'collection_log','estimand':'equal_scene_mean_deviance','logs':len(logs),'scenes':int(n.sum()),
            'improvement':float((a-b).sum()/n.sum()),'percentile_95':np.quantile(effect,[.025,.975]).tolist(),
            'relative_improvement':float(1-b.sum()/a.sum()),'relative_percentile_95':np.quantile(relative,[.025,.975]).tolist(),
            'seed':seed,'resamples':repetitions,'conditional_on_fixed_predictions':True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--spec',type=Path,required=True);parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--data-root',type=Path,required=True);parser.add_argument('--baseline-run',type=Path,required=True)
    parser.add_argument('--output-dir',type=Path,required=True);a=parser.parse_args();spec=read_json(a.spec)
    root=Path(__file__).resolve().parents[2]
    require(not a.output_dir.exists(),'output identity already exists')
    require(digest(a.dataset)==spec['dataset_sha256'],'dataset changed')
    require(digest(a.baseline_run/'result.json')==spec['baseline_result_sha256'],'baseline result changed')
    baseline=read_json(a.baseline_run/'result.json');oldspec=read_json(a.baseline_run/'spec.json')
    require(digest(a.baseline_run/'spec.json')==baseline['spec_sha256'],'baseline specification changed')
    for p,record in baseline['private_outputs'].items(): require(digest(a.baseline_run/p)==record['sha256'],'baseline private rows changed')
    for p,expected in oldspec['source_sha256'].items(): require(digest(root/p)==expected,'baseline source changed: '+p)
    for p,expected in spec['source_sha256'].items(): require(digest(root/p)==expected,'source changed: '+p)
    for p,expected in spec['prediction_sha256'].items(): require(digest(a.data_root/p)==expected,'predictions changed: '+p)
    a.output_dir.mkdir();(a.output_dir/'spec.json').write_bytes(a.spec.read_bytes())
    with np.load(a.dataset,allow_pickle=False) as raw: data={k:raw[k] for k in raw.files}
    dets={}
    for channel,relative in spec['prediction_files'].items():
        raw=read_json(a.data_root/relative)['results'];coverage(raw,data['frames'])
        dets[channel]={t:[(b['detection_name'],number(b['detection_score']),number(b['translation'][0]),number(b['translation'][1]))
                          for b in boxes if b['detection_name'] in CLASSES and number(b['detection_score'])>=.3] for t,boxes in raw.items()}
        del raw
    geometry,names=geometry_rows(dets['camera'],dets['lidar'],data['frames'],data['scenes'],data['timestamps'])
    np.savez_compressed(a.output_dir/'geometry.private.npz',X=geometry,feature_names=np.asarray(names))
    rows=[read_json_line for line in (a.baseline_run/'predictions.private.jsonl').read_text().splitlines()
          if (read_json_line:=json.loads(line))['experiment']=='y_h1000000']
    frame={str(t):i for i,t in enumerate(data['frames'])};anchors=np.asarray([frame[r['frame']] for r in rows])
    require(len(rows)==5693 and len(set(anchors))==len(anchors),'baseline anchor population differs')
    X=np.column_stack([history_matrix(data['X'],data['scenes'],data['timestamps']),geometry])[anchors]
    y=np.asarray([r['y'] for r in rows],dtype=float);scenes=data['scenes'][anchors];logs=data['logs'][anchors]
    report=copy.deepcopy(baseline['experiments']['y_h1000000']);p=np.full(len(y),np.nan);threshold=np.full(len(y),np.nan)
    with threadpool_limits(limits=1):
        for fold in range(oldspec['outer_folds']):
            test=np.asarray([i for i,r in enumerate(rows) if r['fold']==fold]);train=np.asarray([i for i,r in enumerate(rows) if r['fold']!=fold])
            require(not set(logs[train]) & set(logs[test]),'baseline does not separate logs')
            pred,cutoff,fit=nested_predict(X,y,scenes,train,test,oldspec,oldspec['seed']+100*fold,logs)
            p[test]=pred;threshold[test]=cutoff
            report['folds'][fold]['models']['spatial_history']={**fit,'alert_threshold':cutoff,
                'test':metrics(y[test],pred,scenes[test],pred>cutoff,y[test]>=rows[int(test[0])]['high_count_threshold'])}
            print('spatial fold',fold,'scene deviance',report['folds'][fold]['models']['spatial_history']['test']['deviance_scene_mean'],flush=True)
    require(np.isfinite(p).all(),'incomplete spatial predictions')
    q=np.asarray([r['high_count_threshold'] for r in rows])
    report['models']['spatial_history']=metrics(y,p,scenes,p>threshold,y>=q)
    report['paired_scene_comparisons']={};report['paired_log_comparisons']={}
    for i,row in enumerate(rows): row['prediction']['spatial_history']=float(p[i]);row['alert_threshold']['spatial_history']=float(threshold[i])
    for base in ('joint_history','marginal_history'):
        base_p=np.asarray([r['prediction'][base] for r in rows]);key='spatial_history_vs_'+base
        report['paired_scene_comparisons'][key]=paired_band(losses(y,base_p),losses(y,p),scenes,oldspec['bootstrap_seed'],oldspec['bootstrap_resamples'])
        report['paired_log_comparisons'][key]=paired_band(losses(y,base_p),losses(y,p),logs,oldspec['bootstrap_seed'],oldspec['bootstrap_resamples'],unit='collection_log')
    report['log_resampled_equal_scene_comparison']=log_resampled_scene_mean(rows,'joint_history','spatial_history')
    with (a.output_dir/'predictions.private.jsonl').open('w') as stream:
        for row in rows: stream.write(json.dumps(row,sort_keys=True,allow_nan=False)+'\n')
    (a.output_dir/'folds.private.jsonl').write_bytes((a.baseline_run/'folds.private.jsonl').read_bytes())
    result={'artifact_id':'reiyah.predictive-monitor-spatial-evaluation.0.2.0','version':'0.2.0','lifecycle_status':'exploratory',
            'spec_sha256':digest(a.spec),'baseline_result_sha256':digest(a.baseline_run/'result.json'),'split_unit':'logs',
            'experiments':{'y_h1000000':report},'spatial_feature_names':names,
            'private_outputs':{p.name:{'sha256':digest(p),'bytes':p.stat().st_size} for p in a.output_dir.glob('*.private.*')},
            'physical_failure_rate':None,'online_warning_lead_time':None,'safety_benefit':None,
            'limits':['Adaptive exploratory follow-up after observing the 0.1.0 log-holdout results',
                      'Associations and projected sites are output hypotheses, not confirmed tracks or physical objects',
                      'Collection-log resampling does not establish independent deployments or capture refitting uncertainty']}
    for p,expected in spec['source_sha256'].items(): require(digest(root/p)==expected,'source changed during fitting: '+p)
    for p,expected in spec['prediction_sha256'].items(): require(digest(a.data_root/p)==expected,'predictions changed during fitting')
    require(digest(a.dataset)==spec['dataset_sha256'],'dataset changed during fitting')
    (a.output_dir/'result.json').write_text(json.dumps(result,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'completed','comparison':report['log_resampled_equal_scene_comparison']}),flush=True)


if __name__=='__main__':
    try: main()
    except (ValueError,KeyError,TypeError,OSError) as exc:
        print(json.dumps({'status':'invalid','diagnostic':str(exc)}),file=sys.stderr);raise SystemExit(2)
