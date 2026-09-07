#!/usr/bin/env python3
"""Metadata-only training/test provenance census and proposed disjoint splits."""
import argparse
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import random
import tarfile


def literal(tree,name):
    nodes=[node.value for node in tree.body if isinstance(node,ast.Assign)
           and any(isinstance(target,ast.Name) and target.id==name for target in node.targets)]
    if len(nodes)!=1:raise ValueError('ambiguous split assignment')
    if name=='train' and ast.unparse(nodes[0])=='list(sorted(set(train_detect + train_track)))':
        return literal(tree,'train_detect') | literal(tree,'train_track')
    values=ast.literal_eval(nodes[0])
    if len(values)!=len(set(values)):raise ValueError('duplicate split member')
    return set(values)


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--meta',type=Path,required=True);p.add_argument('--splits',type=Path,required=True)
    p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args()
    if a.output_dir.exists():raise ValueError('output identity already exists')
    expected={'meta':'db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b',
              'splits':'eab6fa5e2536a2a85bd9451fb35771833e262b4b96319a6b26fee1dce8f4e2cd'}
    if sha(a.meta)!=expected['meta'] or sha(a.splits)!=expected['splits']:raise ValueError('input identity differs')
    tree=ast.parse(a.splits.read_text());train,val=literal(tree,'train'),literal(tree,'val')
    if train & val: raise ValueError('official scene overlap')
    tables={}
    with tarfile.open(a.meta,mode='r|gz') as archive:
        for member in archive:
            name=member.name.rsplit('/',1)[-1]
            if name in ('scene.json','sample.json','log.json'):
                if name in tables or not member.isfile():raise ValueError('duplicate metadata table')
                tables[name]=json.load(archive.extractfile(member))
    scenes={r['name']:r for r in tables['scene.json']};logs={r['token']:r for r in tables['log.json']}
    if not train|val <= set(scenes):raise ValueError('official scenes absent from metadata')
    tr_logs={scenes[n]['log_token'] for n in train};va_logs={scenes[n]['log_token'] for n in val}
    shared=tr_logs & va_logs;eligible=tr_logs-va_logs
    scene_samples=Counter(r['scene_token'] for r in tables['sample.json'])
    if any(scene_samples[r['token']]!=r['nbr_samples'] for r in scenes.values()):raise ValueError('sample count differs')
    a.output_dir.mkdir();proposals=[]
    for seed in (20260910,20260911,20260912):
        rng=random.Random(seed);sets=[set(),set()]
        for location in sorted({logs[l]['location'] for l in eligible}):
            ordered=sorted(l for l in eligible if logs[l]['location']==location);rng.shuffle(ordered)
            # Assignment uses metadata alone. Unequal sample budgets stay explicit.
            for i,log in enumerate(ordered):sets[i%2].add(log)
        if not all(sets) or sets[0]&sets[1] or (sets[0]|sets[1]) & va_logs:raise ValueError('invalid disjoint split')
        parts=[]
        for i,part in enumerate(sets):
            names=sorted(n for n in train if scenes[n]['log_token'] in part)
            parts.append({'partition':i+1,'logs':sorted(part),'scene_names':names,
                          'scene_count':len(names),'sample_count':sum(scenes[n]['nbr_samples'] for n in names),
                          'locations':dict(Counter(logs[l]['location'] for l in part))})
        record={'seed':seed,'lifecycle_status':'proposed','partitions':parts,'validation_logs':sorted(va_logs),
                'excluded_train_logs_shared_with_validation':sorted(shared),
                'raw_sensor_payload_coverage':'not_checked','model_training':'not_started',
                'equal_training_steps_and_calibration_policy':'not_yet_specified'}
        path=a.output_dir/f'split-{seed}.private.json';path.write_text(json.dumps(record,sort_keys=True,indent=2)+'\n')
        proposals.append({'seed':seed,'sha256':sha(path),'partition_sizes':[{k:v for k,v in part.items() if k not in ('logs','scene_names')} for part in parts]})
    report={'artifact_id':'reiyah.training-overlap-probe-preflight.0.1.0','version':'0.1.0','lifecycle_status':'exploratory',
            'input_sha256':expected,'source_sha256':sha(Path(__file__)),
            'official_train_scenes':len(train),'official_validation_scenes':len(val),'train_logs':len(tr_logs),
            'validation_logs':len(va_logs),'shared_train_validation_logs':len(shared),'remaining_training_logs':len(eligible),
            'excluded_training_scenes':sum(scenes[n]['log_token'] in shared for n in train),
            'proposed_partitions':proposals,'training_effect_on_dependence':None,
            'limits':['Metadata group partitions only; not four trained models, fresh predictions or an overlap intervention result',
                      'All proposed training groups exclude every official validation log; sample budgets remain unequal',
                      'Pretraining data provenance and raw training sensor availability remain unchecked']}
    (a.output_dir/'result.json').write_text(json.dumps(report,sort_keys=True,indent=2)+'\n');print(json.dumps(report,sort_keys=True))


if __name__=='__main__':main()
