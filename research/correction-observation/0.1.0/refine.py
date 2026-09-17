"""Declared post-assay check: tighter full-audit bounds and geometric witnesses.

No selector is run or changed. The original assay and query histories are retained.
"""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import sys
import time
from common import (FAMILIES, ROLES, VERSION, decision, digest, file_digest, flow_rank,
                    iou, linked, native_measure, need, open_interval, put, q, w, wire_interval)


def graph_measure(image, right, edges):
    sizes = [flow_rank({d['id'] for d in image[role]['value']}, right, edges &
                      {(d['id'], r) for d in image[role]['value'] for r in right}) for role in ROLES]
    counts = [len(image[role]['value']) for role in ROLES]
    return {'ranks':sizes,'delta':w(2*(sizes[1]-sizes[0])-counts[1]+counts[0])}


def graph_edit_bounds(image, bases):
    """Each base is the original graph or one reference deletion, with exact ranks."""
    aa, bb = (len(image[role]['value']) for role in ROLES)
    lower, upper = [], []
    for measured in bases:
        ma, mb = measured['ranks']
        lower.append(2*(mb-min(aa,ma+1))-bb+aa)
        upper.append(2*(min(bb,mb+1)-ma)-bb+aa)
    initial = open_interval(image)
    return max(initial[0],min(lower)), min(initial[1],max(upper))


def rectangles(image):
    found = {}
    for role in ROLES:
        for row in image[role]['value']:
            x,y,z,t = [q(v) for v in row['xyxy']]; width, height = z-x,t-y
            choices = [(x,y,z,t), (x-width/3,y,z-width/3,t), (x+width/3,y,z+width/3,t),
                       (x,y-height/3,z,t-height/3), (x,y+height/3,z,t+height/3),
                       (x,y,x+width/2,t), (x+width/2,y,z,t),
                       (x,y,z,y+height/2), (x,y+height/2,z,t),
                       (x-width,y,z,t), (x,y,z+width,t), (x,y-height,z,t), (x,y,z,t+height)]
            for values in choices:
                if values[3]-values[1] >= 25 and all(abs(v)<=10_000_000 for v in values):
                    found.setdefault(values,[w(v) for v in values])
    need(len(found)<=2048,'Geometric followup limit')
    return list(found.values())


def aggregate(members, records, family):
    if any(not linked(im) for im in members):
        return None
    centers = [q(records[im['id']]['nominal']['delta']) for im in members]
    lows = [q(records[im['id']]['edit_bounds'][0]) for im in members]
    highs = [q(records[im['id']]['edit_bounds'][1]) for im in members]
    total, size = sum(centers),len(members)
    if family=='exact_publisher':
        return total/size,total/size
    if family=='one_edit_per_image':
        return sum(lows)/size,sum(highs)/size
    need(family=='one_edit_global','Unknown family')
    return ((total-max(c-lo for c,lo in zip(centers,lows)))/size,
            (total+max(hi-c for c,hi in zip(centers,highs)))/size)


def main(area):
    area = Path(area).resolve(); tick = time.perf_counter()
    freeze = json.loads((area/'REFINEMENT_FREEZE.json').read_text())
    for row in freeze['bindings']:
        need(file_digest(area/row['path'])==row['sha256'],'Refinement bytes changed')
    visible = json.loads((area/'inputs/visible.json').read_text())
    images = {im['id']:im for im in visible['images']}
    out = area/'runs/refinement-01'; out.mkdir()
    records = {}; packets = candidates = geometry_count = patterns = 0
    for image in visible['images']:
        if not linked(image):
            continue
        iid = image['id']; refs = json.loads((area/'oracle'/(iid+'.json')).read_text())['answer']
        detectors = {d['id']:d for role in ROLES for d in image[role]['value']}
        edges = {(d['id'],r['id']) for d in detectors.values() for r in refs if iou(d,r)>=Fraction(1,2)}
        right = {r['id'] for r in refs}
        bases = []
        # Empty outputs have identically zero difference for every reference world.
        removals = [None]+[r['id'] for r in refs] if detectors else [None]
        for removed in removals:
            current_refs = [r for r in refs if r['id']!=removed]
            current_right = {r['id'] for r in current_refs}
            current_edges = {(d,r) for d,r in edges if r!=removed}
            measured = graph_measure(image,current_right,current_edges)
            checked = native_measure(image,current_refs)
            need(measured['ranks']==checked['ranks'] and measured['delta']==checked['delta'],'Base independent/native disagreement')
            bases.append({'removed':removed,'measurement':checked})
            packets += 1
        nominal = bases[0]['measurement']; low = high = q(nominal['delta'])
        low_world = high_world = None
        for base in bases:
            delta = q(base['measurement']['delta'])
            if delta<low:
                low,low_world = delta,{'removed':base['removed'],'added':None}
            if delta>high:
                high,high_world = delta,{'removed':base['removed'],'added':None}
        neighborhoods = {}
        for xyxy in rectangles(image):
            candidate = {'id':'edge-boundary:'+iid,'record_sha256':digest({'basis':'hypothetical', 'xyxy':xyxy}), 'xyxy':xyxy}
            neighbors = frozenset(d['id'] for d in detectors.values() if iou(d,candidate)>=Fraction(1,2))
            neighborhoods.setdefault(neighbors,candidate)
            geometry_count += 1
        patterns += len(neighborhoods)
        need(len(bases)*len(neighborhoods)<=10000,'Graph followup limit')
        for base in bases:
            removed = base['removed']; current_right = right-{removed}
            current_edges = {(d,r) for d,r in edges if r!=removed}
            for neighbors,added in neighborhoods.items():
                new_edges = current_edges | {(d,added['id']) for d in neighbors}
                measured = graph_measure(image,current_right|{added['id']},new_edges)
                delta = q(measured['delta']); candidates += 1
                if delta<low:
                    low,low_world = delta,{'removed':removed,'added':added}
                if delta>high:
                    high,high_world = delta,{'removed':removed,'added':added}
        witnesses = {}
        for direction,world,target in [('minimum',low_world,low),('maximum',high_world,high)]:
            if world is None:
                continue
            altered = [r for r in refs if r['id']!=world['removed']]
            if world['added'] is not None:
                altered.append(world['added'])
            checked = native_measure(image,altered)
            need(q(checked['delta'])==target,'Geometric witness not entailed by checked proof')
            witnesses[direction] = {'world':world,'altered_references':altered,'measurement':checked}
            packets += 1
        bound = graph_edit_bounds(image,[base['measurement'] for base in bases])
        need(bound[0]<=low<=high<=bound[1],'Found witness outside stated enclosure')
        record = {'image_id':iid,'subject_reference_sha256':digest(refs),'nominal':nominal,
                  'bases':bases,'edit_bounds':wire_interval(bound),'minimum_found':w(low),'maximum_found':w(high),
                  'witnesses':witnesses,'geometry_count':len(rectangles(image)),'neighborhood_count':len(neighborhoods)}
        put(out/(iid+'.json'),record); records[iid] = record
    earlier = {(r['case_id'],r['family']):r for r in json.loads((area/'runs/analysis-01/FULL_OBSERVATIONS.json').read_text())}
    full = []
    for case in visible['cases']:
        members = [images[i] for i in case['images']]
        for family in FAMILIES:
            bounds = aggregate(members,records,family)
            old = earlier[(case['id'],family)]['full_observation_bounds']
            if bounds is not None:
                need(q(old[0])<=bounds[0]<=bounds[1]<=q(old[1]),'Refined enclosure became weaker')
            row = {'case_id':case['id'],'group':case['group'],'family':family,'bounds':wire_interval(bounds),
                   'decision':decision(bounds),'nominal_delta':earlier[(case['id'],family)]['nominal_delta'],
                   'opposite_decision_witness':False,'alternative_delta':None,'edits':[]}
            if row['decision']=='unresolved':
                nominal = q(row['nominal_delta']); direction = 'minimum' if nominal>0 else 'maximum'
                effects = [(im['id'],q(records[im['id']][direction+'_found'])-q(records[im['id']]['nominal']['delta'])) for im in members]
                if family=='one_edit_global':
                    effects = [min(effects,key=lambda x:x[1]) if nominal>0 else max(effects,key=lambda x:x[1])]
                alternative = nominal+sum(value for _,value in effects)/len(members)
                if (alternative<=0 if nominal>0 else alternative>0):
                    row.update(opposite_decision_witness=True,alternative_delta=w(alternative),
                               edits=[{'image_id':iid,'direction':direction} for iid,effect in effects if effect])
            full.append(row)
    report = {'artifact_id':'reiyah.correction-observation.refinement','version':VERSION,
              'status':'exploratory_post_assay_full_observation_analysis','full_observation_rows':full,
              'native_checked_packets':packets,'geometries':geometry_count,'neighborhoods':patterns,
              'candidate_graph_worlds':candidates,'seconds':time.perf_counter()-tick,
              'freeze_sha256':file_digest(area/'REFINEMENT_FREEZE.json'),
              'summary':[{'family':family,'decisions':dict(Counter(r['decision'] for r in full if r['family']==family)),
                          'opposite_decision_witnesses':sum(r['opposite_decision_witness'] for r in full if r['family']==family)} for family in FAMILIES]}
    put(out/'RESULTS.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='full_observation_rows'}))


if __name__=='__main__':
    main(sys.argv[1])
