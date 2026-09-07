#!/usr/bin/env python3
"""Revisit the retained conditional coefficient's resampling unit, not its truth."""
import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path

import numpy as np


def coefficient(cells):
    n = cells.sum(axis=-1)
    a, b = cells[..., 2] + cells[..., 3], cells[..., 1] + cells[..., 3]
    expected = np.divide(a*b, n, out=np.zeros_like(n, dtype=float), where=n>0).sum(axis=-1)
    joint = cells[..., 3].sum(axis=-1)
    return np.divide(joint, expected, out=np.full_like(expected, np.nan, dtype=float), where=expected>0)


def bootstrap(cube, seed, repetitions):
    rng = np.random.default_rng(seed)
    values = []
    for start in range(0,repetitions,100):
        n = min(100,repetitions-start)
        w = rng.multinomial(len(cube), np.full(len(cube),1/len(cube)), size=n)
        values.extend(coefficient(np.einsum('bg,gsk->bsk',w,cube)).tolist())
    defined = [v for v in values if math.isfinite(v)]
    return {"groups":len(cube),"resamples":repetitions,"seed":seed,"undefined_resamples":len(values)-len(defined),
            "percentile_95": np.quantile(defined,[.025,.975]).tolist() if len(defined)==len(values) else None}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,required=True)
    p.add_argument('--dataset',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError('output identity already exists')
    gt=json.loads(a.cache.read_bytes())
    with np.load(a.dataset,allow_pickle=False) as raw:
        data={k:raw[k] for k in raw.files}
    if len(gt)!=len(data['camera_match']): raise ValueError('cache row count differs')
    frame={str(t):i for i,t in enumerate(data['frames'])}
    tracks=defaultdict(list)
    for g in gt: tracks[g['instance_token']].append((g['ts_us'],g['xy']))
    motion={}
    for token,values in tracks.items():
        values.sort(); dt=(values[-1][0]-values[0][0])/1e6
        motion[token]='unknown_motion' if len(values)<2 or dt<=0 else ('moving' if math.dist(values[-1][1],values[0][1])/dt>=1 else 'static')
    def band(d): return '0-20' if d<20 else '20-30' if d<30 else '30-40' if d<40 else '40-50'
    keys=[(g['cls'],band(g['dist']),g['vis'],g['cond'],motion[g['instance_token']]) for g in gt]
    encoding={k:i for i,k in enumerate(sorted(set(keys)))}
    strata=np.asarray([encoding[k] for k in keys]);counts=np.bincount(strata);support=counts[strata]>=30
    cells=2*(~data['camera_match']).astype(int)+(~data['lidar_match']).astype(int)
    results={}
    for unit in ('scenes','logs'):
        labels=np.asarray([data[unit][frame[g['sample_token']]] for g in gt])
        identities=sorted(set(labels));index={v:i for i,v in enumerate(identities)}
        groups=np.asarray([index[g] for g in labels])
        cube=np.zeros((len(index),len(encoding),4),dtype=np.float64)
        np.add.at(cube,(groups[support],strata[support],cells[support]),1)
        full=cube.sum(axis=0)
        leave=[float(coefficient(full-one)) for one in cube]
        results[unit]={"coefficient":float(coefficient(full)),**bootstrap(cube,20260907,2000),
                       "leave_one_group_out_min":min(leave),"leave_one_group_out_max":max(leave),
                       "scene_or_log_independence_established":False}
    if not math.isclose(results['scenes']['coefficient'],1.151053,abs_tol=5e-7):
        raise ValueError('does not reproduce the retained AO coefficient to its reported precision')
    report={"artifact_id":"reiyah.collection-log-coefficient-sensitivity.0.1.0","version":"0.1.0","lifecycle_status":"exploratory",
            "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "input_sha256":{"cache":hashlib.sha256(a.cache.read_bytes()).hexdigest(),"dataset":hashlib.sha256(a.dataset.read_bytes()).hexdigest()},
            "support_rows":int(support.sum()),"strata":int(np.count_nonzero(counts>=30)),
            "resampling":results,"physical_coefficient":None,
            "limits":["Same selected reference, deepest retrospective covariates, score .30 and fixed full-population support as AO",
                      "Changes the uncertainty sensitivity, not the conditional aggregate estimand or reference validity",
                      "Eighteen collection logs are not eighteen proven independent deployments",
                      "Neither bootstrap includes benchmark selection, detector training or reference-model uncertainty"]}
    a.output.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    print(json.dumps(report,sort_keys=True))


if __name__=='__main__': main()
