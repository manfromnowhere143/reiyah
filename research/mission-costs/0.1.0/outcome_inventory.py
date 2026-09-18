"""Check published outcome inventories without opening private scientific inputs."""
import argparse
from collections import Counter
import csv
from fractions import Fraction
import hashlib
import io
import json
from pathlib import Path
import subprocess
import time

SOURCE_COMMIT = 'cc59ec6ed9befe657712b7565ee175fb35cb066b'
DECISIONS = {'supported', 'excluded', 'unresolved', 'input_blocked'}
TABLES = [
    ('public-predictions', 'results.csv', ('arm', 'family', 'case_id'), (204, 192, 480, 0), 'lower', 'upper'),
    ('public-predictions', 'analysis.csv', ('family', 'case_id'), (51, 48, 120, 0), 'lower', 'upper'),
    ('reference-translation', 'results.csv', ('radius', 'case_id'), (176, 201, 207, 0), 'lower', 'upper'),
    ('translation-2d', 'results.csv', ('radius', 'case_id'), (164, 190, 230, 0), 'universal_bounds_lower', 'universal_bounds_upper'),
    ('loss-tradeoff', 'results.csv', ('family', 'share', 'case_id'), (2901, 4763, 4819, 0), 'lower', 'upper'),
    ('loss-tradeoff', 'continuum.csv', ('family', 'cell', 'case_id'), (1119, 2184, 1834, 0), 'lower_at_representative', 'upper_at_representative'),
    ('reference-timing', 'results.csv', ('contract', 'case_id'), (63, 91, 57, 81), 'mean_lower', 'mean_upper'),
    ('reference-witness', 'results.csv', ('contract', 'case_id'), (63, 91, 57, 81), 'mean_lower', 'mean_upper'),
    ('operating-policy', 'primary-thresholds.csv', ('family', 'cell_id'), (344, 681, 1043, 1551), 'mean_lower', 'mean_upper'),
    ('operating-policy', 'anchor-cases.csv', ('family', 'threshold', 'case_id'), (298, 2395, 747, 648), 'mean_lower', 'mean_upper'),
]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def inventory(root):
    tick = time.perf_counter()
    bindings, retained, results = [], {}, []

    def source(study, filename):
        relative = f'research/{study}/0.1.0/{filename}'
        raw = (root / relative).read_bytes()
        committed = subprocess.run(['git', '-C', str(root), 'show', SOURCE_COMMIT + ':' + relative],
                                   capture_output=True, check=True).stdout
        need(raw == committed, 'Source differs from selected commit: ' + relative)
        bindings.append({'path': relative, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        return raw.decode()

    summaries = {name: json.loads(source(name, 'summary.json')) for name in
                 dict.fromkeys([r[0] for r in TABLES] + ['cached-packet-audit', 'policy-loss-envelope'])}
    for study, filename, keys, expected, lower, upper in TABLES:
        rows = list(csv.DictReader(io.StringIO(source(study, filename))))
        identities = [tuple(r[k] for k in keys) for r in rows]
        need(len(set(identities)) == len(rows), 'Duplicate allocated result identity')
        counts = Counter(r['decision'] for r in rows)
        need(set(counts) <= DECISIONS, 'Unknown outcome label')
        need(tuple(counts[k] for k in ('supported', 'excluded', 'unresolved', 'input_blocked')) == expected,
             'Outcome count differs: ' + study + '/' + filename)
        for row in rows:
            if row['decision'] == 'input_blocked':
                need(row[lower] == row[upper] == '', 'Blocked result has numeric bounds')
                continue
            a, b = Fraction(row[lower]), Fraction(row[upper])
            need(a <= b, 'Reversed interval')
            actual = 'supported' if a > 0 else ('excluded' if b <= 0 else 'unresolved')
            need(row['decision'] == actual, 'Decision does not follow its reported bounds')
        evidence = Counter(r.get('evidence', r.get('unresolved_reason', 'not_in_this_table'))
                           for r in rows if r['decision'] == 'unresolved')
        results.append({'study': study, 'file': filename, 'rows': len(rows),
                        'identity_fields': list(keys), 'decisions': dict(sorted(counts.items())),
                        'unresolved_evidence': dict(sorted(evidence.items()))})
        retained[(study, filename)] = rows

    cases = {r['case_id'] for r in retained[('public-predictions', 'analysis.csv')]}
    need(len(cases) == 73, 'Original case membership differs')
    for (study, filename), rows in retained.items():
        if filename == 'primary-thresholds.csv':
            need({r['case_id'] for r in rows} == {'all-64'}, 'Unexpected primary case')
        else:
            need({r['case_id'] for r in rows} == cases, 'Cross-study case membership differs')

    comparison = retained[('public-predictions', 'results.csv')]
    answers = {(r['family'], r['case_id']): r for r in retained[('public-predictions', 'analysis.csv')]}
    arms = {arm: {(r['family'], r['case_id']): r for r in comparison if r['arm'] == arm} for arm in 'ABCD'}
    need(all(set(rows) == set(answers) for rows in arms.values()), 'Incomplete arm allocation')
    need(all(row['decision'] == answers[key]['decision'] for rows in arms.values() for key, row in rows.items()),
         'Stopping and full-answer decisions differ')
    need(all(arms[a][key]['queries'] == arms[b][key]['queries'] for a, b in [('A', 'B'), ('C', 'D')]
             for key in answers), 'Conventional/native query counts differ')
    query_totals = {arm: sum(int(row['queries']) for row in rows.values()) for arm, rows in arms.items()}
    need(query_totals == {'A': 502, 'B': 502, 'C': 511, 'D': 511}, 'Query totals differ')
    resolved = [r for r in answers.values() if r['decision'] in ('supported', 'excluded')]
    need(len(resolved) == 99 and all(r['A_queries'] == r['minimum_queries'] for r in resolved),
         'Conventional selector misses a retained query floor')
    need(all(r['opposite_decisions_witnessed'] == 'True' for r in answers.values()
             if r['decision'] == 'unresolved'), 'Full-answer unresolved world pair absent')

    timing = {(r['contract'], r['case_id']): r for r in retained[('reference-timing', 'results.csv')]}
    witness = {(r['contract'], r['case_id']): r for r in retained[('reference-witness', 'results.csv')]}
    need(set(timing) == set(witness), 'Witness study changes allocation')
    need(all(all(timing[key][field] == witness[key][field] for field in
                 ('decision', 'mean_lower', 'mean_upper', 'blocked_image_count')) for key in timing),
         'Witness search changed the prior universal result')
    need(sum(row['evidence'] == 'bound_gap' for row in timing.values()) == 7, 'Prior gap count differs')
    need(all(row['evidence'] == 'opposite_worlds' for row in witness.values() if row['decision'] == 'unresolved'),
         'Timing witness result lacks a world pair')

    policy = summaries['operating-policy']
    for filename, key in [('primary-thresholds.csv', 'primary_continuum'), ('anchor-cases.csv', 'diagnostic_anchors')]:
        rows = retained[('operating-policy', filename)]
        for family, published in policy['counts'][key].items():
            selected = [r for r in rows if r['family'] == family]
            need(dict(Counter(r['decision'] for r in selected)) == published['decisions'], 'Policy summary count differs')
            need(dict(Counter(r['evidence'] for r in selected if r['evidence'])) == published['evidence'],
                 'Policy evidence count differs')

    cached = summaries['cached-packet-audit']
    need(cached['fully_admitted_cached_packets'] == 0, 'Cached admission changed')
    need(sum(r['rows'] for r in cached['files']) == 2063562 == cached['all_logical_rows_checked_with_both_decoders'],
         'Cached row coverage differs')
    cached_rows = []
    for file in cached['files']:
        need(sum(file['states'].values()) == file['observed_images'] == file['expected_images'] == 5000,
             'Cached membership incomplete')
        need(file['rows'] == file['prediction_rows'] + file['empty_placeholder_rows'], 'Empty rows collapsed')
        need(file['experiment_admission'] == 'blocked' and file['content_contract_passed'] is False,
             'Invalid cached packet admitted')
        cached_rows.append({key: file[key] for key in ('session', 'rows', 'prediction_rows', 'states',
                                                      'empty_placeholder_rows', 'row_errors', 'blockers')})

    local = json.loads(source('public-predictions', 'sources.json'))
    need(local['local_fully_qualified_packets'] == 2 and local['cached_fully_qualified_packets'] == 0,
         'Admission inventory differs')
    local_rows = []
    for file in local['local_candidates']:
        admission = file['admission']
        need(admission['allocated_images'] == sum(admission['states'].values()) == 64
             and admission['blocked_images'] == [] and admission['complete_usable_export'], 'Local packet incomplete')
        local_rows.append({'model': file['model'], 'packet_sha256': file['packet_sha256'],
                           'states': admission['states'], 'detections': admission['detections']})

    partition = list(csv.DictReader(io.StringIO(source('policy-loss-envelope', 'penalty-partition.csv'))))
    counts = Counter(r['envelope_comparison'] for r in partition)
    need(len(partition) == 51 and dict(counts) == {'tie': 2, 'new_lower': 3, 'old_lower': 46},
         'Envelope partition differs')
    need(len({r['id'] for r in partition}) == 51, 'Repeated penalty cell')
    for kind, published in summaries['policy-loss-envelope']['decisions_by_partition_kind'].items():
        need(dict(Counter(r['envelope_comparison'] for r in partition if r['kind'] == kind)) == published,
             'Envelope summary differs')
    need(all(d.get('reserved_outcomes_accessed', d.get('reserved_outcome_images_accessed', 0)) == 0
             and d['independent_scientific_replication'] is False for d in summaries.values()),
         'Exposure or replication assertion changed')
    return {'artifact_id': 'reiyah.mission-costs.outcome-inventory', 'version': '0.1.0',
            'status': 'exploratory', 'source_commit': SOURCE_COMMIT, 'sources': bindings, 'tables': results,
            'local_packets': local_rows, 'cached_packets': cached_rows,
            'query_totals_by_arm': query_totals, 'resolved_baseline_floors_attained': len(resolved),
            'same_timing_decisions_after_witness_search': len(timing), 'penalty_partition': dict(counts),
            'overlapping_rows_must_not_be_summed_as_independent_evidence': True,
            'reserved_images_closed': 1433, 'private_input_reads': 0,
            'scientific_reexecution': False, 'independent_scientific_replication': False,
            'seconds': time.perf_counter() - tick}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    result = inventory(args.candidate.resolve())
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print(json.dumps({key: result[key] for key in ('source_commit', 'query_totals_by_arm',
                     'resolved_baseline_floors_attained', 'same_timing_decisions_after_witness_search', 'seconds')}))


if __name__ == '__main__': main()
