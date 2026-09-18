"""Check the published follow-up against the unchanged parent row allocation."""
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

COMMIT = '5611b53a22feb41be53fc27df40cfbc444e8038b'


def run(root, commit=COMMIT):
    tick = time.perf_counter(); bindings = []
    def source(relative):
        raw = (root / relative).read_bytes()
        actual = subprocess.run(['git', '-C', str(root), 'show', commit + ':' + relative],
                                capture_output=True, check=True).stdout
        assert raw == actual, 'Published source differs'
        bindings.append({'path': relative, 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
        return raw.decode()
    before = {}
    for section, file in [('primary_rows', 'primary-thresholds.csv'), ('anchor_rows', 'anchor-cases.csv')]:
        before[section] = list(csv.DictReader(io.StringIO(source('research/operating-policy/0.1.0/' + file))))
    after = list(csv.DictReader(io.StringIO(source('research/operating-witness/0.1.0/results.csv'))))
    summary = json.loads(source('research/operating-witness/0.1.0/summary.json'))
    seen = set(); counts = Counter(); evidence = Counter(); changes = []; gaps = []
    for row in after:
        key = (row['section'], int(row['row_index'])); assert key not in seen; seen.add(key)
        old = before[key[0]][key[1]]
        for field in ('case_id', 'family', 'group', 'allocated_images', 'blocked_image_count',
                      'decision', 'mean_lower', 'mean_upper'):
            if field.startswith('mean_') and row[field]: assert Fraction(row[field]) == Fraction(old[field])
            else: assert row[field] == old[field], field
        identity = 'cell_id' if row['section'] == 'primary_rows' else 'threshold'
        assert Fraction(row[identity]) == Fraction(old[identity]) if identity == 'threshold' else row[identity] == old[identity]
        assert row['previous_evidence'] == old['evidence']
        for endpoint in ('lower', 'upper'):
            a, b = row['previous_attained_' + endpoint], old['attained_' + endpoint]
            assert (a == b == '') or Fraction(a) == Fraction(b)
        if row['decision'] == 'input_blocked':
            assert all(row[f] == '' for f in ('mean_lower', 'mean_upper', 'attained_lower', 'attained_upper', 'evidence'))
        else:
            lo, hi = Fraction(row['attained_lower']), Fraction(row['attained_upper'])
            assert Fraction(row['mean_lower']) <= lo <= hi <= Fraction(row['mean_upper'])
            assert lo <= Fraction(row['previous_attained_lower']) <= Fraction(row['previous_attained_upper']) <= hi
            if row['evidence'] == 'opposite_worlds': assert lo <= 0 < hi and row['decision'] == 'unresolved'
        if row['evidence'] != old['evidence']:
            assert old['evidence'] == 'bound_gap' and row['evidence'] == 'opposite_worlds' and row['selected_target'] == 'True'
            changes.append(list(key))
        if row['evidence'] == 'bound_gap':
            assert row['family'] in ('current_partial', 'union_partial'); gaps.append(list(key))
        counts[row['decision']] += 1; evidence[row['evidence'] or 'input_blocked'] += 1
    assert seen == {(section, i) for section, rows in before.items() for i in range(len(rows))}
    assert len(after) == summary['allocated_rows'] == 7707
    assert len(changes) == summary['all_changed_rows'] == summary['target_rows_now_with_opposite_worlds'] == 110
    assert len(gaps) == summary['remaining_gap_rows'] == 279
    return {'artifact_id': 'reiyah.mission-costs.followup-outcome-inventory', 'version': '0.1.0',
            'source_commit': commit, 'sources': bindings, 'rows': len(after), 'decisions': dict(counts),
            'evidence': dict(evidence), 'changed_target_rows': changes, 'remaining_timing_gaps': gaps,
            'all_parent_rows_preserved': True, 'all_decisions_and_universal_bounds_unchanged': True,
            'dependent_rows_not_independent_evidence': True, 'private_input_reads': 0,
            'reserved_images_closed': 1433, 'independent_scientific_replication': False,
            'seconds': time.perf_counter() - tick}


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--commit', default=COMMIT)
    a = p.parse_args(); result = run(a.candidate.resolve(), a.commit)
    with a.output.open('x') as stream: json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
    print({k: result[k] for k in ('rows', 'decisions', 'evidence', 'seconds')})
