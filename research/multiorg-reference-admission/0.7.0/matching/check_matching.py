#!/usr/bin/env python3
"""Separate exact-area/Edmonds–Karp check; shared explicit custody gate only."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import time
import types
import input_gate as gate


def oracle():
    contract = gate.decode(gate.read(gate.HERE / 'contract.json', gate.CONTRACT_SHA))
    path = gate.HERE / 'maxflow_reference.py'
    raw = gate.read(path, contract['independent_reference_sha256'])
    module = types.ModuleType('_bound_maxflow'); exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def reference_boxes(raw):
    # Independent numeric parsing and source [row,column] -> XYXY conversion.
    source = json.loads(raw, parse_float=Fraction)
    gate.require(type(source) is dict and len(source) <= 128, 'reference domain')
    boxes = []
    for key in sorted(source):
        corners = source[key]
        gate.require(type(key) is str and type(corners) is list and len(corners) == 4, 'reference source identity/rectangle')
        points = []
        for point in corners:
            gate.require(type(point) is list and len(point) == 2 and all(type(v) in (int, Fraction) for v in point), 'reference coordinate type')
            gate.require(all(abs(v) <= 10000000 for v in point), 'reference coordinate bound')
            points.append(tuple(Fraction(v) for v in point))
        rows, cols = {p[0] for p in points}, {p[1] for p in points}
        gate.require(len(set(points)) == 4 and len(rows) == len(cols) == 2
                     and set(points) == {(r, c) for r in rows for c in cols}, 'complete positive Cartesian rectangle')
        boxes.append((min(cols), min(rows), max(cols), max(rows)))
    return boxes


def compose(cells):
    values = {}
    for cell in cells:
        key = (cell['tiff_path'], cell['procedure'])
        gate.require(key not in values, 'duplicate composition cell')
        values[key] = Fraction(cell['delta'])
    gate.require(set(values) == {(i,p) for i in gate.IMAGES for p in gate.PROCEDURES}, 'complete four-by-three composition')
    totals = {p: sum((values[i,p] for i in gate.IMAGES),Fraction())/4 for p in gate.PROCEDURES}
    lp = min(gate.PROCEDURES,key=lambda p:(totals[p],p))
    up = min(gate.PROCEDURES,key=lambda p:(-totals[p],p))
    lower_choices = [{'tiff_path':i,'procedure':min(gate.PROCEDURES,key=lambda p:(values[i,p],p))} for i in gate.IMAGES]
    upper_choices = [{'tiff_path':i,'procedure':min(gate.PROCEDURES,key=lambda p:(-values[i,p],p))} for i in gate.IMAGES]
    glo,ghi = totals[lp],totals[up]
    plo = sum((values[x['tiff_path'],x['procedure']] for x in lower_choices),Fraction())/4
    phi = sum((values[x['tiff_path'],x['procedure']] for x in upper_choices),Fraction())/4
    gate.require(plo <= glo <= ghi <= phi,'nested reference families')
    def decide(lo,hi): return 'prefer_b' if lo>0 else 'prefer_a' if hi<0 else 'unresolved'
    gd,pd = decide(glo,ghi),decide(plo,phi)
    gate.require(pd == 'unresolved' or pd == gd,'opposite resolved family direction')
    primary = 'inconclusive_global_unresolved' if gd == 'unresolved' else 'coupling_fragility' if pd == 'unresolved' else 'no_observed_fragility'
    ratio = lambda v: str(v.numerator)+'/'+str(v.denominator)
    return {'global':{'lower':ratio(glo),'upper':ratio(ghi),'decision':gd,'lower_procedure':lp,'upper_procedure':up},
            'imagewise':{'lower':ratio(plo),'upper':ratio(phi),'decision':pd,'lower_choices':lower_choices,'upper_choices':upper_choices},
            'primary_status':primary}


def derive(admitted):
    reference = oracle(); cells = []
    for identity in gate.IMAGES:
        aa=[tuple(Fraction(v) for v in row['box_xyxy']) for row in admitted['images'][identity]['faster']['analysis_predictions']]
        bb=[tuple(Fraction(v) for v in row['box_xyxy']) for row in admitted['images'][identity]['yolo']['analysis_predictions']]
        for procedure in gate.PROCEDURES:
            refs=reference_boxes(admitted['references'][identity][procedure]['raw'])
            ta,tb=reference.matching(aa,refs),reference.matching(bb,refs)
            delta=len(aa)-len(bb)+2*(tb-ta)
            cells.append({'tiff_path':identity,'procedure':procedure,'reference_count':len(refs),
                'detections_a':len(aa),'detections_b':len(bb),'tp_a':ta,'tp_b':tb,
                'fp_a':len(aa)-ta,'fp_b':len(bb)-tb,'fn_a':len(refs)-ta,'fn_b':len(refs)-tb,
                'delta':str(delta)+'/1'})
    return {'cells':cells,**compose(cells)}


def run(input_path, input_sha, repository, result_path, result_sha):
    started = time.monotonic(); admitted = gate.load_inputs(input_path, input_sha, repository)
    report = gate.decode(gate.read(result_path, result_sha)); expected = derive(admitted)
    gate.require(report.get('artifact_id') == 'reiyah.multiorg.selected-cohort-matching-result'
                 and report.get('version') == '0.7.0' and report.get('status') == 'complete', 'matching result state')
    gate.require(report.get('producer_sha256') == gate.sha((gate.HERE / 'match_analysis.py').read_bytes())
                 and report.get('admission_sha256') == gate.sha(Path(gate.__file__).read_bytes()), 'matching implementation provenance')
    for key, value in [('input_sha256', input_sha), ('contract_sha256', gate.CONTRACT_SHA),
            ('context', admitted['context']), ('context_sha256', admitted['context_sha256']),
            ('image_ids', list(gate.IMAGES)), ('model_variants', gate.VARIANTS), ('n_images', 4), ('selected_cohort_images', 4),
            ('native_dependencies', admitted['native_dependencies'])]: gate.equal(report.get(key), value, 'result ' + key)
    for key in ('global', 'imagewise', 'primary_status'): gate.equal(report.get(key), expected[key], key + ' exact arithmetic')
    gate.require(type(report.get('cells')) is list and len(report['cells']) == 12, 'twelve result cells')
    for actual, correct in zip(report['cells'], expected['cells']):
        gate.require(set(actual) == set(correct) | {'native_input_sha256', 'native_proof_sha256', 'native_work_units'}, 'cell schema')
        for key, value in correct.items(): gate.equal(actual.get(key), value, 'independent cell ' + key)
        gate.require(type(actual['native_work_units']) is int and 0 < actual['native_work_units'] <= 2000000, 'native work accounting')
    packets = report.get('native_packets'); gate.require(type(packets) is list and len(packets) == 12, 'twelve native packets')
    for (index,identity,procedure),cell,packet in zip([(n,i,p) for n,i in enumerate(gate.IMAGES) for p in gate.PROCEDURES],report['cells'],packets):
        gate.keys(packet, ('image_id','procedure','input','proof'), 'packet schema'); gate.require(packet['procedure']==procedure and packet['image_id']==identity,'packet order')
        for kind, limit in [('input', 4194304), ('proof', 16777216)]:
            d = packet[kind]; gate.keys(d, ('file', 'sha256', 'bytes'), 'native file descriptor')
            gate.require(d['file'] == 'image-' + str(index) + '-' + procedure + '-' + kind + '.json' and d['sha256'] == cell['native_' + kind + '_sha256'], 'native packet binding')
            raw = gate.read(Path(result_path).parent / d['file'], d['sha256'], limit)
            gate.require(type(d['bytes']) is int and len(raw) == d['bytes'], 'native packet size')
    gate.require(time.monotonic() - started < 120, 'checker wall budget')
    return {'artifact_id': 'reiyah.multiorg.selected-cohort-matching-check', 'version': '0.7.0', 'status': 'passed',
        'input_sha256': input_sha, 'result_sha256': result_sha, 'contract_sha256': gate.CONTRACT_SHA,
        'checker_sha256': gate.sha(Path(__file__).read_bytes()), 'admission_sha256': gate.sha(Path(gate.__file__).read_bytes()),
        'independent_reference_sha256': gate.sha((gate.HERE / 'maxflow_reference.py').read_bytes()),
        **expected, 'wall_seconds': time.monotonic() - started,
        'scope': 'Same investigation. Shared custody/endpoint gate; independent source-coordinate parsing, exact-area matching via unchanged Edmonds-Karp, and complete four-by-three composition. Native proof bytes are bound, not separately reexecuted by this checker. No physical truth or work advantage.'}


def main():
    p = argparse.ArgumentParser()
    for name in ('input', 'input-sha256', 'repository', 'result', 'result-sha256', 'output'): p.add_argument('--' + name, required=True)
    a = p.parse_args(); result = run(a.input, a.input_sha256, a.repository, a.result, a.result_sha256)
    with Path(a.output).open('xb') as stream: stream.write(gate.canonical(result))
    print('{"status":"passed","recorded_reference_cases":12}')


if __name__ == '__main__': main()
