"""Replay all allocated rows against frozen inputs and the queried source answers."""
from fractions import Fraction
import json
from pathlib import Path
import sys
import time
from common import (ARMS, FAMILIES, VERSION, checker, conventional_measure, decision, digest,
                    file_digest, linked, native_graph, need, open_interval, put, q, ranking,
                    subject, validate_event, wire_interval)


def independent_interval(images, measured, family):
    if any(not linked(im) for im in images):
        return None
    lows, highs, losses, gains = [], [], [], []
    for im in images:
        lo, hi = open_interval(im)
        if im['id'] in measured:
            a, b = measured[im['id']]['ranks']
            na, nb = (len(im[r]['value']) for r in ('output_a', 'output_b'))
            center = Fraction(2*(b-a) - nb + na)
            if family == 'exact_publisher':
                lo = hi = center
            else:
                low = max(lo, 2*(max(0, b-1)-min(na, a+1))-nb+na)
                high = min(hi, 2*(min(nb, b+1)-max(0, a-1))-nb+na)
                if family == 'one_edit_per_image':
                    lo, hi = low, high
                else:
                    lo = hi = center
                    losses.append(center-low); gains.append(high-center)
        lows.append(lo); highs.append(hi)
    return ((sum(lows)-max(losses, default=0))/len(images),
            (sum(highs)+max(gains, default=0))/len(images))


def main(area):
    tick = time.perf_counter(); area = Path(area).resolve()
    freeze = json.loads((area/'FREEZE.json').read_text())
    for entry in freeze['bindings']:
        path = area/entry['path']
        need(file_digest(path) == entry['sha256'] and path.stat().st_size == entry['bytes'], 'Frozen file changed: '+entry['path'])
    bindings = json.loads((area/'sources/BINDINGS.json').read_text())
    for entry in bindings['reads']:
        need(file_digest(entry['path']) == entry['sha256'], 'Retained source changed')
    visible = json.loads((area/'inputs/visible.json').read_text())
    images = {im['id']: im for im in visible['images']}
    cases = {case['id']: case for case in visible['cases']}
    run_dir = area/'runs/assay-01'
    results = json.loads((run_dir/'RESULTS.json').read_text())
    need(results['visible_sha256'] == file_digest(area/'inputs/visible.json') and
         results['freeze_sha256'] == file_digest(area/'FREEZE.json'), 'Run context changed')
    allocated = {(arm, family, cid) for arm in ARMS for family in FAMILIES for cid in cases}
    seen_rows = set(); checkpoints = events = proofs = measurements_count = 0
    parity = {}; native_seconds = 0
    for entry in results['rows']:
        path = run_dir/entry['path']
        need(file_digest(path) == entry['sha256'], 'Run row bytes changed')
        row = json.loads(path.read_text()); result = row['result']; begin = row['begin']
        need(result == entry['result'], 'Result index changed')
        key = (result['arm'], result['family'], result['case_id'])
        need(key in allocated and key not in seen_rows, 'Unallocated or repeated result')
        seen_rows.add(key)
        arm, family, cid = key
        case_images = [images[i] for i in cases[cid]['images']]
        order = ranking(case_images, ARMS[arm][0])
        need(begin['ranking'] == order and begin['query_budget'] == len(order), 'Policy changed')
        need(begin['case_id'] == cid and begin['family'] == family and begin['arm'] == arm
             and begin['group'] == cases[cid]['group'], 'Case context mismatch')
        measured = {}; used = []; pending = None; latest = None; expect = 'checkpoint'
        for frame in row['history']:
            need(frame['type'] == expect, 'Reordered/missing query-check-measure history')
            if frame['type'] == 'checkpoint':
                bounds = independent_interval(case_images, measured, family)
                need(frame['sequence'] == len(used) and frame['bounds'] == wire_interval(bounds)
                     and frame['decision'] == decision(bounds), 'Stopping result not entailed')
                latest = frame; checkpoints += 1
                expect = 'observation'
            elif frame['type'] == 'observation':
                need(latest['decision'] == 'unresolved' and len(used) < len(order), 'Queried after stop or budget')
                iid = order[len(used)]; im = images[iid]
                request = {'case_id': cid, 'arm': arm, 'family': family, 'sequence': len(used)+1,
                           'image_id': iid, 'subject_sha256': subject(im),
                           'precision': 'whole_image_reference', 'method_version': VERSION}
                refs = validate_event(frame['event'], request)
                source = json.loads((area/'oracle'/(iid+'.json')).read_text())
                need(refs == source['answer'] and frame['event']['source_sha256'] == source['source_sha256']
                     and source['subject_sha256'] == request['subject_sha256'], 'Source answer or context changed')
                pending = (iid, refs); used.append(iid); events += 1
                expect = 'measurement'
            else:
                iid, refs = pending
                need(frame['image_id'] == iid and iid not in measured, 'Unqueried or duplicate measurement')
                actual = conventional_measure(images[iid], refs)
                supplied = frame['value']
                need(actual['ranks'] == supplied['ranks'] and actual['delta'] == supplied['delta'], 'Independent matching disagreement')
                if ARMS[arm][1] == 'native':
                    graph = native_graph(images[iid], refs)
                    need(digest(graph) == supplied['graph_sha256'], 'Native source applicability changed')
                    start = time.perf_counter(); checker.check(graph, supplied['payload'])
                    native_seconds += time.perf_counter()-start; proofs += 1
                measured[iid] = actual; measurements_count += 1; pending = None
                expect = 'checkpoint'
        need(expect == 'observation' and pending is None and latest is not None, 'Incomplete final checkpoint')
        need(result['queries'] == len(used) and result['query_order'] == used and result['query_budget'] == len(order), 'Incomplete query cost')
        need(result['decision'] == latest['decision'] and result['bounds'] == latest['bounds'], 'Final decision mismatch')
        need(latest['decision'] != 'unresolved' or len(used) == len(order), 'Premature unresolved stop')
        need(result['human_seconds'] is None and result['total_cost'] is None, 'Invented human economics')
        parity[key] = {'order': used, 'decision': result['decision'], 'bounds': result['bounds']}
    need(seen_rows == allocated, 'Allocated rows omitted')
    pairs = []
    for pair in [('A','B'), ('C','D')]:
        count = 0
        for family in FAMILIES:
            for cid in cases:
                need(parity[(pair[0],family,cid)] == parity[(pair[1],family,cid)], 'Conventional/native parity failed')
                count += 1
        pairs.append({'arms': list(pair), 'exact_query_order_and_result_agreements': count})
    report = {'artifact_id':'reiyah.correction-observation.replay','version':VERSION,
              'rows':len(seen_rows),'checkpoints':checkpoints,'observation_events':events,
              'independent_matching_checks':measurements_count,'native_proofs':proofs,
              'frozen_bindings':len(freeze['bindings']),'retained_source_bindings':len(bindings['reads']),
              'parity':pairs,'native_check_seconds':native_seconds,'seconds':time.perf_counter()-tick,
              'accepted_invalid_results_observed':0,'false_reuse_observed':0,
              'scope':'Fixed development replay, not independent scientific replication or physical validity.'}
    put(run_dir/'REPLAY.json',report)
    print(json.dumps(report))


if __name__ == '__main__':
    main(sys.argv[1])
