#!/usr/bin/env python3
"""Independent private MultiOrg annotation checker; never imports producer code."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

PROTOCOL_SHA = 'c62b333937f168ec0a7ff4915c8eaf2f0cd49fa7ac88e11f78f39a371c49a670'
PROCEDURES = ('t0', 't1_A', 't1_B')
PREFIX = 'MultiOrg_v2/test/'

class Rejected(Exception): pass

def insist(condition, message):
    if not condition: raise Rejected(message)

def digest(data): return hashlib.sha256(data).hexdigest()

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        insist(key not in result, 'duplicate_json_key:'+key)
        result[key] = value
    return result

def invalid_constant(value): raise Rejected('nonfinite_json_constant:'+value)

def decode(data):
    return json.loads(data, object_pairs_hook=unique_object, parse_float=Fraction,
                      parse_constant=invalid_constant)

def exact_keys(obj, keys, label):
    insist(type(obj) is dict and set(obj)==set(keys), label+':keys')

def relative_path(value):
    insist(type(value) is str and value and '\\' not in value, 'path_type')
    p=PurePosixPath(value)
    insist(not p.is_absolute() and '..' not in p.parts and str(p)==value, 'path_not_canonical:'+value)
    return p

def rebuild_roster(listing_dir):
    names=['multiorg-file-list-200.json']+['multiorg-file-list-page%d.json'%n for n in range(2,6)]
    all_files={}
    source_bindings=[]
    previous=None
    for name in names:
        p=listing_dir/name;raw=p.read_bytes();obj=decode(raw)
        insist(obj.get('hasErrorMessage') is False, 'listing_source_error')
        items=obj['datasetFiles'];insist(type(items) is list and len(items)==200,'listing_page_count')
        source_bindings.append({'path':name,'sha256':digest(raw),'bytes':len(raw)})
        for item in items:
            path=item['name'];relative_path(path)
            insist(path not in all_files,'listing_duplicate:'+path)
            insist(previous is None or previous<path,'listing_order')
            previous=path
            all_files[path]=item['totalBytes']
    selected={k:v for k,v in all_files.items() if k.startswith(PREFIX)}
    insist(len(selected)==220,'listed_test_file_count')
    images=sorted(k for k in selected if k.endswith('.tiff'))
    insist(len(images)==55,'listed_image_count')
    expected={}
    for image in images:
        ip=PurePosixPath(image);stem=ip.stem
        insist(ip.parent.name==stem,'tiff_stem_directory')
        byproc={}
        for path,size in selected.items():
            ap=PurePosixPath(path)
            if ap.parent!=ip.parent or ap.suffix!='.json':continue
            match=re.fullmatch(re.escape(stem)+r'_(t0_[AB]|t1_A|t1_B)\.json',ap.name)
            insist(match is not None,'annotation_filename:'+path)
            suffix=match[1];proc='t0' if suffix.startswith('t0_') else suffix
            insist(proc not in byproc,'repeated_procedure:'+image)
            byproc[proc]=(path,size)
        insist(set(byproc)==set(PROCEDURES),'procedure_membership:'+image)
        expected[image]=byproc
    insist(sum(len(x) for x in expected.values())==165,'listed_annotation_count')
    return expected,source_bindings

def rectangle(value, location):
    insist(type(value) is list and len(value)==4, 'box_four_points:'+location)
    points=[]
    for point in value:
        insist(type(point) is list and len(point)==2, 'point_pair:'+location)
        insist(all(type(v) in (int,Fraction) for v in point), 'coordinate_number:'+location)
        points.append(tuple(Fraction(v) for v in point))
    unique=set(points)
    rows={p[0] for p in points};cols={p[1] for p in points}
    insist(len(unique)==4 and len(rows)==2 and len(cols)==2, 'rectangle_extents:'+location)
    insist(unique=={(r,c) for r in rows for c in cols}, 'rectangle_corners:'+location)
    # Preserve exact geometry, explicitly convert source(row,column) to X/Y bounds.
    return (min(cols),min(rows),max(cols),max(rows))

def perform(args):
    protocol_raw=args.protocol.read_bytes()
    insist(digest(protocol_raw)==PROTOCOL_SHA,'protocol_hash')
    decode(protocol_raw)
    expected,listings=rebuild_roster(args.listing_dir)
    manifest_raw=args.manifest.read_bytes()
    insist(digest(manifest_raw)==args.manifest_sha256,'manifest_hash')
    manifest=decode(manifest_raw)
    exact_keys(manifest,('artifact_id','version','images'),'manifest')
    insist(manifest['artifact_id']=='reiyah.multiorg.annotation-manifest' and manifest['version']=='0.1.0','manifest_identity')
    insist(type(manifest['images']) is list and len(manifest['images'])==55,'manifest_image_count')
    source_root=args.sources.resolve()
    observed_images=set();observed_sources=set();observed_local=set();objects=[]
    rows=[];total_bytes=0;procedure_totals=Counter();negative_totals=Counter();file_bindings=[]
    for entry in manifest['images']:
        exact_keys(entry,('tiff_path','annotations'),'image')
        image=entry['tiff_path'];relative_path(image)
        insist(image in expected and image not in observed_images,'manifest_image_membership:'+image)
        observed_images.add(image)
        insist(type(entry['annotations']) is list and len(entry['annotations'])==3,'manifest_reference_count')
        counts={};proc_seen=set();negative_counts={};source_ids={}
        for desc in entry['annotations']:
            exact_keys(desc,('procedure','source_path','local_path','byte_size','sha256','transport_valid'),'annotation_descriptor')
            insist(desc['transport_valid'] is True, 'transport_not_valid:'+str(desc.get('source_path')))
            proc=desc['procedure'];source=desc['source_path'];relative_path(source)
            insist(proc in PROCEDURES and proc not in proc_seen,'manifest_procedure')
            proc_seen.add(proc)
            insist(expected[image][proc]==(source,desc['byte_size']),'source_roster_size:'+source)
            insist(type(desc['byte_size']) is int and desc['byte_size']>=0,'source_size_type')
            insist(type(desc['sha256']) is str and re.fullmatch('[0-9a-f]{64}',desc['sha256']) is not None,'source_digest_type')
            local=relative_path(desc['local_path']);fp=(source_root/str(local)).resolve()
            insist(fp.is_relative_to(source_root),'source_escape')
            insist(source not in observed_sources and fp not in observed_local,'source_alias')
            observed_sources.add(source);observed_local.add(fp)
            raw=fp.read_bytes()
            insist(len(raw)==desc['byte_size'] and digest(raw)==desc['sha256'],'source_integrity:'+source)
            ann=decode(raw);insist(type(ann) is dict,'annotation_root:'+source)
            negative_counts[proc]=0;id_hashes=[]
            for boxid,value in ann.items():
                insist(type(boxid) is str and boxid!='','source_object_id')
                points=rectangle(value,source+'#'+boxid)
                objects.append({'source_path':source,'raw_id':boxid,'box':[str(v) for v in points]})
                negative_counts[proc]+=int(any(v<0 for v in points))
                id_hashes.append(digest(json.dumps([source,boxid],ensure_ascii=False,separators=(',',':')).encode()))
            source_ids[proc]=digest(('\n'.join(sorted(id_hashes))+('\n' if id_hashes else '')).encode())
            negative_totals[proc]+=negative_counts[proc]
            counts[proc]=len(ann);procedure_totals[proc]+=len(ann);total_bytes+=len(raw)
            file_bindings.append({'source_path':source,'sha256':desc['sha256'],'bytes':len(raw),'objects':len(ann)})
        count_sum=sum(counts.values())
        rows.append({'tiff_path':image,'selection_sha256':digest(('reiyah.multiorg.pilot.v1\n'+image).encode()),'annotation_counts':{k:counts[k] for k in PROCEDURES},'sum_reference_objects':count_sum,'native_object_cap_eligible':count_sum<=128,'annotation_set_complete':True,'annotation_states':{p:'validated_annotation' for p in PROCEDURES},'negative_coordinate_box_counts':{p:negative_counts[p] for p in PROCEDURES},'source_qualified_ids_sha256':{p:source_ids[p] for p in PROCEDURES}})
    insist(observed_images==set(expected),'complete_image_membership')
    insist(len(observed_sources)==165,'complete_reference_membership')
    rows.sort(key=lambda r:r['tiff_path'])
    eligible=sorted([r for r in rows if r['native_object_cap_eligible']],key=lambda r:(r['selection_sha256'],r['tiff_path']))
    selected=[r['tiff_path'] for r in eligible[:4]]
    rebuilt={'source_manifest_sha256':digest(manifest_raw),'image_count':55,'annotation_file_count':165,'total_annotation_bytes':total_bytes,'images':rows,'selected_images':selected,'feasibility_pilot':selected[0] if selected else None,'eligible_images':len(eligible),'annotation_counts_by_procedure':dict(sorted(procedure_totals.items())),'negative_coordinate_boxes_by_procedure':dict(sorted(negative_totals.items())),'valid_annotation_bytes':total_bytes,'valid_annotation_file_count':165,'failed_annotation_file_count':0,'native_reference_object_cap':128,'annotation_census':'complete','counts_scope':'complete_census','selection_state':'evaluated_complete_census','source_failures':[]}
    comparison=[]
    if args.report:
        result=decode(args.report.read_bytes())
        for key,value in rebuilt.items():
            insist(key in result,'producer_missing_field:'+key)
            # Canonical JSON encoding detects bool-for-int substitutions too.
            insist(json.dumps(result[key],sort_keys=True,separators=(',',':'))==json.dumps(value,sort_keys=True,separators=(',',':')),'producer_field_mismatch:'+key)
            comparison.append(key)
    out={'status':'passed','scope':'Separate same-investigation annotation checker; no model execution, TIFF-bound check or physical-truth validation','protocol_sha256':PROTOCOL_SHA,'checker_sha256':digest(Path(__file__).read_bytes()),'rebuilt':rebuilt,'procedure_object_totals':dict(sorted(procedure_totals.items())),'eligible_image_count':len(eligible),'complete_source_qualified_objects':len(objects),'negative_coordinate_object_count':sum(any(Fraction(v)<0 for v in ob['box']) for ob in objects),'image_bounds_checked':False,'canonical_geometry_sha256':digest(json.dumps(sorted(objects,key=lambda x:(x['source_path'],x['raw_id'])),sort_keys=True,separators=(',',':')).encode()),'listed_source_bindings':listings,'payload_bindings':sorted(file_bindings,key=lambda x:x['source_path']),'producer_fields_compared':comparison}
    return out

def main():
    p=argparse.ArgumentParser();p.add_argument('--protocol',required=True,type=Path);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--manifest-sha256',required=True);p.add_argument('--sources',required=True,type=Path);p.add_argument('--listing-dir',required=True,type=Path);p.add_argument('--report',type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    try: result=perform(a)
    except (Rejected,ValueError,OSError,KeyError,TypeError) as exc:
        result={'status':'rejected','diagnostic':str(exc),'exception':type(exc).__name__}
    with a.output.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps({'status':result['status'],'output':str(a.output)}));return 0 if result['status']=='passed' else 1
if __name__=='__main__':sys.exit(main())
