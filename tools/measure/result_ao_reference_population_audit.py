"""Offline reanalysis of existing public-data caches, with input hashes.

No model execution, source writes, or Git operation. This is an exploratory
research-board sensitivity check, not a preregistered result or acceptance.
"""
import collections
import argparse
import hashlib
import json
import math
import pathlib
import tarfile
import sys
import codecs

import numpy as np
import scipy
from scipy.spatial import cKDTree

VERSION = '0.1.0'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def stream_array(f):
    """Stream one complete JSON array, rejecting malformed or truncated input."""
    decoder = json.JSONDecoder()
    utf8 = codecs.getincrementaldecoder('utf-8')()
    buf = ''
    eof = False

    def refill():
        nonlocal buf, eof
        chunk = f.read(1024 * 1024)
        eof = not chunk
        buf += utf8.decode(chunk, final=eof)

    while not buf.strip() and not eof:
        refill()
    buf = buf.lstrip()
    if not buf.startswith('['):
        raise ValueError('Metadata must be a JSON array')
    buf = buf[1:]
    need_separator = False
    after_comma = False
    while True:
        while not buf.strip() and not eof:
            refill()
        buf = buf.lstrip()
        if not buf:
            raise ValueError('Truncated metadata array')
        if buf.startswith(']'):
            if after_comma:
                raise ValueError('Trailing comma in metadata array')
            buf = buf[1:]
            while not eof:
                refill()
            if buf.strip():
                raise ValueError('Unexpected content after metadata array')
            return
        if need_separator:
            if not buf.startswith(','):
                raise ValueError('Missing separator in metadata array')
            buf = buf[1:]
            need_separator, after_comma = False, True
            continue
        try:
            value, end = decoder.raw_decode(buf)
        except json.JSONDecodeError:
            if eof:
                raise
            refill()
            continue
        yield value
        buf = buf[end:]
        need_separator, after_comma = True, False


def require_sample_coverage(predictions, samples):
    """An absent sample is an unavailable input, not an empty detection list."""
    missing = samples - set(predictions)
    if missing:
        raise ValueError(f'Prediction input omits {len(missing)} required samples')


def reference_distances(points, reference):
    """A reference must exist before an absence-based label can be calculated."""
    if len(reference) == 0:
        raise ValueError('Reference annotations unavailable for this sample')
    return cKDTree(reference).query(points)


def count_coincidence(a, b):
    if len(a) == 0 or len(b) == 0:
        return 0
    return int(np.count_nonzero(cKDTree(b).query(a)[0] <= 2.))


def ego_relocate(points, source_origin, target_origin, source_heading, target_heading):
    """Preserve a donor's ego-relative arrangement, not its static world location."""
    angle = target_heading - source_heading
    co, si = math.cos(angle), math.sin(angle)
    return (points - source_origin) @ np.array([[co, si], [-si, co]]) + target_origin


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data-root',type=pathlib.Path,required=True)
    ap.add_argument('--output',default='-',help='JSON output path, or - for stdout')
    ap.add_argument('--private-cases-output',type=pathlib.Path,
                    help='Optional local adjudication cases; not part of the public aggregate report')
    args=ap.parse_args()
    DATA=args.data_root.resolve()
    paths = ['gt_val_cache.json', 'matched_mapillary.json', 'matched_megvii.json',
             'meta.tgz', 'predictions/mapillary_val.json', 'predictions/megvii_val.json']
    inputs = {(DATA / path).resolve() for path in paths}
    outputs = ([pathlib.Path(args.output).resolve()] if args.output != '-' else [])
    if args.private_cases_output:
        outputs.append(args.private_cases_output.resolve())
    if inputs.intersection(outputs) or len(set(outputs)) != len(outputs):
        raise ValueError('Outputs must be distinct from every input and each other')
    before = {s: {'bytes': (DATA/s).stat().st_size, 'sha256': digest(DATA/s)} for s in paths}
    print('Inputs hashed; reading ground truth and full reference annotations.', file=sys.stderr, flush=True)
    gt = json.loads((DATA/'gt_val_cache.json').read_bytes())
    wanted_samples = {g['sample_token'] for g in gt}
    bysample = collections.defaultdict(list)
    for g in gt:
        bysample[g['sample_token']].append(g['xy'])
    scene_of = {}
    full_reference = collections.defaultdict(list)
    full_annotation_tokens = collections.defaultdict(list)
    wanted_names = {'sample.json', 'sample_annotation.json'}
    with tarfile.open(DATA/'meta.tgz', mode='r|gz') as tar:
        for member in tar:
            name = member.name.rsplit('/', 1)[-1]
            if name not in wanted_names or not member.isfile():
                continue
            for row in stream_array(tar.extractfile(member)):
                if name == 'sample.json' and row['token'] in wanted_samples:
                    scene_of[row['token']] = row['scene_token']
                elif name == 'sample_annotation.json' and row['sample_token'] in wanted_samples:
                    full_reference[row['sample_token']].append(row['translation'][:2])
                    full_annotation_tokens[row['sample_token']].append(row['token'])
            wanted_names.remove(name)
            print('Read', name, file=sys.stderr, flush=True)
            if not wanted_names:
                break
    if set(scene_of) != wanted_samples or set(full_reference) != wanted_samples:
        raise ValueError('Metadata does not cover the cache sample population')
    tracks = collections.defaultdict(list)
    for g in gt:
        tracks[g['instance_token']].append((g['ts_us'], g['xy']))
    motion = {}
    for token, track in tracks.items():
        track.sort()
        dt = (track[-1][0]-track[0][0])/1e6
        motion[token] = 'unknown_motion' if len(track)<2 or dt<=0 else (
            'moving' if math.dist(track[0][1],track[-1][1])/dt>=1 else 'static')
    def band(d):
        return '0-20' if d<20 else '20-30' if d<30 else '30-40' if d<40 else '40-50'
    keys = [(g['cls'], band(g['dist']), g['vis'], g['cond'], motion[g['instance_token']]) for g in gt]
    strata = {key:i for i,key in enumerate(sorted(set(keys)))}
    sid = np.array([strata[k] for k in keys])
    counts = np.bincount(sid)
    support = counts[sid]>=30
    matched=[]
    for name in ['matched_mapillary.json','matched_megvii.json']:
        obj=json.loads((DATA/name).read_bytes())['matched_at_2m']
        m={int(k):v for values in obj.values() for k,v in values.items()}
        matched.append(np.array([m.get(i,-1.)<.3 for i in range(len(gt))]))
    a,b=matched
    # Cells: neither, B-only, A-only, both. Derived independently of production encoding.
    cell=2*a.astype(int)+b.astype(int)
    scene_keys=sorted(set(scene_of.values())); scene_idx={s:i for i,s in enumerate(scene_keys)}
    gids=np.array([scene_idx[scene_of[g['sample_token']]] for g in gt])
    cube=np.zeros((len(scene_keys),len(strata),4))
    np.add.at(cube,(gids[support],sid[support],cell[support]),1)
    def estimate(c):
        total=c.sum(axis=-1)
        pa=c[...,2]+c[...,3]; pb=c[...,1]+c[...,3]
        exp=np.divide(pa*pb,total,out=np.zeros_like(total),where=total>0).sum(axis=-1)
        return c[...,3].sum(axis=-1)/exp
    point=float(estimate(cube.sum(axis=0)))
    rng=np.random.default_rng(20260907)
    weights=rng.multinomial(len(scene_keys),np.full(len(scene_keys),1/len(scene_keys)),size=2000)
    boots=estimate(np.einsum('bg,gsk->bsk',weights,cube))
    scene_check={'score_threshold':.3,'support_rows':int(support.sum()),'total_rows':len(gt),
        'tracked_instances':len(tracks),'scenes':len(scene_keys),'conditional_ratio':point,
        'scene_bootstrap_percentile_95':np.percentile(boots,[2.5,97.5]).tolist(),
        'seed':20260907,'replicates':2000,'note':'Fixed original deepest-stratum support; scenes are bootstrap units, not assumed fully independent geography samples.'}
    print(json.dumps(scene_check),file=sys.stderr,flush=True)

    # This checks the exact reference population; it does not relabel unmatched detections as known ghosts.
    classes={'car','truck','bus','trailer','construction_vehicle','pedestrian','motorcycle','bicycle','traffic_cone','barrier'}
    reference_check={}
    private_cases={}
    ghost_sets={'filtered_cache':{},'full_annotations':{}}
    for channel,path in [('camera','predictions/mapillary_val.json'),('lidar','predictions/megvii_val.json')]:
        preds=json.loads((DATA/path).read_bytes())['results']
        require_sample_coverage(preds, wanted_samples)
        n_det=n_flag=n_reclassified=0; examples=[]
        for mode in ghost_sets:ghost_sets[mode][channel]={}
        for sample in sorted(wanted_samples):
            det=[d for d in preds[sample] if d['detection_name'] in classes and d['detection_score']>=.3]
            if not det:continue
            pos=np.array([d['translation'][:2] for d in det])
            dist_cache=reference_distances(pos, bysample[sample])[0]
            dist_full, nearest=reference_distances(pos, full_reference[sample])
            flagged=dist_cache>2.; changed=flagged & (dist_full<=2.)
            ghost_sets['filtered_cache'][channel][sample]=pos[flagged]
            ghost_sets['full_annotations'][channel][sample]=pos[dist_full>2.]
            n_det+=len(det); n_flag+=int(flagged.sum());n_reclassified+=int(changed.sum())
            for i in np.flatnonzero(changed)[:max(0,5-len(examples))]:
                examples.append({'sample_token':sample,'predicted_class':det[i]['detection_name'],
                    'predicted_xy':pos[i].tolist(),'score':det[i]['detection_score'],
                    'cache_reference_distance':float(dist_cache[i]),'full_annotation_distance':float(dist_full[i]),
                    'excluded_annotation_token':full_annotation_tokens[sample][int(nearest[i])],
                    'excluded_annotation_xy':full_reference[sample][int(nearest[i])]})
        reference_check[channel]={'detections_at_0_30':n_det,'flagged_as_ghost_by_cache':n_flag,
            'within_2m_of_excluded_annotation':n_reclassified,
            'fraction_of_original_ghost_flags_reclassified':n_reclassified/n_flag if n_flag else None}
        private_cases[channel]=examples
        print(channel, n_flag, 'cache ghost flags;',n_reclassified,'near excluded annotations',file=sys.stderr,flush=True)

    # Reconstruct the historical ego-relative null, then vary the reference and
    # the donor support separately. An empty donor is information, not missingness.
    ego={g['sample_token']:np.array(g['ego_xy']) for g in gt}
    timestamp={g['sample_token']:g['ts_us'] for g in gt}
    scene_samples=collections.defaultdict(list)
    for s in wanted_samples:scene_samples[scene_of[s]].append(s)
    headings={};partners={}
    for sc,tokens in scene_samples.items():
        tokens.sort(key=lambda s:timestamp[s])
        for i,s in enumerate(tokens):
            if i+1<len(tokens):delta=ego[tokens[i+1]]-ego[s]
            elif i>0:delta=ego[s]-ego[tokens[i-1]]
            else:continue
            if np.linalg.norm(delta)>=.5:headings[s]=math.atan2(delta[1],delta[0])
            partners[s]=[tokens[j] for j in (i+10,i-10) if 0<=j<len(tokens)]
    empty=np.empty((0,2))
    null_results={}
    for mode,channels in ghost_sets.items():
        null_results[mode]={}
        for rule in ['historical_nonempty_donors','fixed_heading_support']:
            rows=np.zeros((len(scene_keys),4))
            for s in sorted(wanted_samples):
                if s not in headings:continue
                cam=channels['camera'].get(s,empty)
                eligible=[q for q in partners.get(s,[]) if q in headings]
                if rule=='historical_nonempty_donors':
                    eligible=[q for q in eligible if len(channels['lidar'].get(q,empty))]
                if not eligible or len(cam)==0:continue
                observed=count_coincidence(cam,channels['lidar'].get(s,empty))
                moved=[];world=[]
                for q in eligible:
                    points=channels['lidar'].get(q,empty)
                    moved.append(count_coincidence(cam,ego_relocate(points,ego[q],ego[s],headings[q],headings[s])))
                    world.append(count_coincidence(cam,points))
                rows[scene_idx[scene_of[s]]]+=[observed,np.mean(moved),np.mean(world),len(cam)]
            total=rows.sum(axis=0)
            draws=weights@rows
            entry={'observed_coincidence_count':int(total[0]),'ego_relative_null_expected_count':float(total[1]),
                   'world_fixed_null_expected_count':float(total[2]),'camera_candidate_opportunities':int(total[3]),
                   'scope':'Unmatched detections; reference absence does not prove physical nonexistence'}
            for col,name in [(1,'ego_relative'),(2,'world_fixed')]:
                valid=draws[:,col]>0
                ratios=draws[valid,0]/draws[valid,col]
                entry[name+'_ratio']=float(total[0]/total[col]) if total[col]>0 else None
                entry[name+'_scene_bootstrap_percentile_95']=np.percentile(ratios,[2.5,97.5]).tolist() if len(ratios) else None
                entry[name+'_undefined_bootstrap_replicates']=int((~valid).sum())
            null_results[mode][rule]=entry
    after={s:digest(DATA/s) for s in paths}
    stable=all(after[s]==before[s]['sha256'] for s in paths)
    result={'artifact_id':'reiyah.gate-b.result-ao-reference-population-audit','version':VERSION,
        'lifecycle_status':'exploratory','kind':'exploratory_offline_sensitivity',
        'tool_sha256':digest(pathlib.Path(__file__)),
        'environment':{'python':sys.version.split()[0],'numpy':np.__version__,'scipy':scipy.__version__},
        'inputs':before,'input_hashes_unchanged_after_read':stable,
        'scene_clustering':scene_check,'ghost_reference_population':reference_check,'temporal_null_sensitivity':null_results,
        'nonclaims':['No new model execution','No independent physical adjudication','No safety or causal conclusion','No operator acceptance']}
    if not stable:
        raise RuntimeError('Inputs changed during analysis; discard as a fixed-input result.')
    if args.private_cases_output:
        args.private_cases_output.write_text(json.dumps({
            'artifact_id':'reiyah.gate-b.result-ao-private-cases','version':VERSION,
            'lifecycle_status':'exploratory','inputs':before,'cases':private_cases,
            'custody':'Local source-derived cases; redistribution permission is not established here'
        },indent=2,sort_keys=True,allow_nan=False)+'\n')
    payload=json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+'\n'
    if args.output=='-':sys.stdout.write(payload)
    else:pathlib.Path(args.output).write_text(payload)
    print('Source hashes stable; exploratory report emitted.',file=sys.stderr,flush=True)


if __name__=='__main__':
    main()
