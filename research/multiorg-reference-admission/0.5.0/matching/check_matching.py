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


def derive(admitted):
    reference = oracle(); cells = []
    # Use the source prediction records again, not the producer's converted tuples.
    aa = [tuple(Fraction(v) for v in row['box_xyxy']) for row in admitted['images']['faster']['analysis_predictions']]
    bb = [tuple(Fraction(v) for v in row['box_xyxy']) for row in admitted['images']['yolo']['analysis_predictions']]
    for procedure in gate.PROCEDURES:
        refs = reference_boxes(admitted['references'][procedure]['raw'])
        ta, tb = reference.matching(aa, refs), reference.matching(bb, refs)
        delta = len(aa) - len(bb) + 2 * (tb - ta)
        cells.append({'tiff_path': gate.IMAGE, 'procedure': procedure, 'reference_count': len(refs),
            'detections_a': len(aa), 'detections_b': len(bb), 'tp_a': ta, 'tp_b': tb,
            'fp_a': len(aa) - ta, 'fp_b': len(bb) - tb, 'fn_a': len(refs) - ta, 'fn_b': len(refs) - tb,
            'delta': str(delta) + '/1'})
    values = {row['procedure']: Fraction(row['delta']) for row in cells}
    low = min(gate.PROCEDURES, key=lambda p: (values[p], p)); high = min(gate.PROCEDURES, key=lambda p: (-values[p], p))
    lo, hi = values[low], values[high]
    decision = 'prefer_b' if lo > 0 else 'prefer_a' if hi < 0 else 'unresolved'
    ratio = lambda v: str(v.numerator) + '/' + str(v.denominator)
    return {'cells': cells, 'global': {'lower': ratio(lo), 'upper': ratio(hi), 'decision': decision,
            'lower_procedure': low, 'upper_procedure': high},
        'imagewise': {'lower': ratio(lo), 'upper': ratio(hi), 'decision': decision,
            'lower_choices': [{'tiff_path': gate.IMAGE, 'procedure': low}],
            'upper_choices': [{'tiff_path': gate.IMAGE, 'procedure': high}]},
        'primary_status': 'inconclusive_incomplete_selected_cohort'}


def run(input_path, input_sha, repository, result_path, result_sha):
    started = time.monotonic(); admitted = gate.load_inputs(input_path, input_sha, repository)
    report = gate.decode(gate.read(result_path, result_sha)); expected = derive(admitted)
    gate.require(report.get('artifact_id') == 'reiyah.multiorg.first-image-matching-result'
                 and report.get('version') == '0.5.0' and report.get('status') == 'complete', 'matching result state')
    gate.require(report.get('producer_sha256') == gate.sha((gate.HERE / 'match_analysis.py').read_bytes())
                 and report.get('admission_sha256') == gate.sha(Path(gate.__file__).read_bytes()), 'matching implementation provenance')
    for key, value in [('input_sha256', input_sha), ('contract_sha256', gate.CONTRACT_SHA),
            ('context', admitted['context']), ('context_sha256', admitted['context_sha256']),
            ('image_id', gate.IMAGE), ('model_variants', gate.VARIANTS), ('n_images', 1), ('selected_cohort_images', 4),
            ('native_dependencies', admitted['native_dependencies'])]: gate.equal(report.get(key), value, 'result ' + key)
    for key in ('global', 'imagewise', 'primary_status'): gate.equal(report.get(key), expected[key], key + ' exact arithmetic')
    gate.require(type(report.get('cells')) is list and len(report['cells']) == 3, 'three result cells')
    for actual, correct in zip(report['cells'], expected['cells']):
        gate.require(set(actual) == set(correct) | {'native_input_sha256', 'native_proof_sha256', 'native_work_units'}, 'cell schema')
        for key, value in correct.items(): gate.equal(actual.get(key), value, 'independent cell ' + key)
        gate.require(type(actual['native_work_units']) is int and 0 < actual['native_work_units'] <= 2000000, 'native work accounting')
    packets = report.get('native_packets'); gate.require(type(packets) is list and len(packets) == 3, 'three native packets')
    for procedure, cell, packet in zip(gate.PROCEDURES, report['cells'], packets):
        gate.keys(packet, ('procedure', 'input', 'proof'), 'packet schema'); gate.require(packet['procedure'] == procedure, 'packet order')
        for kind, limit in [('input', 4194304), ('proof', 16777216)]:
            d = packet[kind]; gate.keys(d, ('file', 'sha256', 'bytes'), 'native file descriptor')
            gate.require(d['file'] == procedure + '-' + kind + '.json' and d['sha256'] == cell['native_' + kind + '_sha256'], 'native packet binding')
            raw = gate.read(Path(result_path).parent / d['file'], d['sha256'], limit)
            gate.require(type(d['bytes']) is int and len(raw) == d['bytes'], 'native packet size')
    gate.require(time.monotonic() - started < 120, 'checker wall budget')
    return {'artifact_id': 'reiyah.multiorg.first-image-matching-check', 'version': '0.5.0', 'status': 'passed',
        'input_sha256': input_sha, 'result_sha256': result_sha, 'contract_sha256': gate.CONTRACT_SHA,
        'checker_sha256': gate.sha(Path(__file__).read_bytes()), 'admission_sha256': gate.sha(Path(gate.__file__).read_bytes()),
        'independent_reference_sha256': gate.sha((gate.HERE / 'maxflow_reference.py').read_bytes()),
        **expected, 'wall_seconds': time.monotonic() - started,
        'scope': 'Same investigation. Shared custody/endpoint gate; independent source-coordinate parsing, exact-area matching via unchanged Edmonds-Karp, and one-image composition. Native proof bytes are bound, not separately reexecuted by this checker. No physical truth or work advantage.'}


def main():
    p = argparse.ArgumentParser()
    for name in ('input', 'input-sha256', 'repository', 'result', 'result-sha256', 'output'): p.add_argument('--' + name, required=True)
    a = p.parse_args(); result = run(a.input, a.input_sha256, a.repository, a.result, a.result_sha256)
    with Path(a.output).open('xb') as stream: stream.write(gate.canonical(result))
    print('{"status":"passed","recorded_reference_cases":3}')


if __name__ == '__main__': main()
