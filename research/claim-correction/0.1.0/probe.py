"""Exact controls for the H5 selection correction; no images or inference.

Authored counterexamples falsify a general bound. Historical transcript counts
only reproduce descriptive arithmetic, not data extraction or human awareness.
"""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
from statistics import median

ROOT = Path(__file__).resolve().parents[3]


def coefficient(counts):
    """Cell order: both, automation only, gaze proxy only, neither."""
    if len(counts) != 4 or any(type(n) is not int or n < 0 for n in counts):
        raise ValueError('Four nonnegative integer counts required')
    both, auto_only, gaze_only, neither = counts
    n = sum(counts)
    denominator = (both + auto_only) * (both + gaze_only)
    return Fraction(both * n, denominator) if denominator else None


def summarize(rows, threshold=None):
    if not rows:
        raise ValueError('An empty population is not a measured zero')
    if any(type(a) is not bool or type(g) is not Fraction or not 0 <= g <= 1
           for a, g in rows):
        raise ValueError('Require Boolean automation flags and exact gaze in [0,1]')
    if threshold is None:
        threshold = median([g for _, g in rows])
    if type(threshold) is not Fraction or not 0 <= threshold <= 1:
        raise ValueError('Require an exact threshold in [0,1]')
    counts = [0, 0, 0, 0]
    for automation_miss, gaze in rows:
        index = (0 if automation_miss else 2) + (0 if gaze < threshold else 1)
        counts[index] += 1
    value = coefficient(counts)
    return {'n': len(rows), 'threshold': str(threshold), 'counts': counts,
            'coefficient': None if value is None else str(value)}


def selection_controls():
    selected = list(zip([True, False, True, False], map(Fraction, ['2/5', '9/20', '11/20', '3/5'])))
    high = [(True, Fraction(g, 20)) for g in (16, 17, 18, 19)]
    low = [(True, Fraction(g, 20)) for g in (1, 2, 3, 4)]
    threshold = median([g for _, g in selected])
    return {'selected': summarize(selected),
            'augmented_high_recomputed_median': summarize(selected + high),
            'augmented_low_recomputed_median': summarize(selected + low),
            'augmented_high_fixed_threshold': summarize(selected + high, threshold),
            'augmented_low_fixed_threshold': summarize(selected + low, threshold)}


def historical_counts(root=ROOT):
    result = {}
    for key, name in [('H5', 'h5_cross_agent_joint.txt'), ('H5b', 'h5b_cross_agent_interval.txt')]:
        path = root / 'human-channel/evidence' / name
        data = path.read_bytes()
        text = data.decode('utf-8')
        cells = re.findall(r'2x2 counts \[both,autoOnly,humOnly,neither\]: (\d+), (\d+), (\d+), (\d+)', text)
        reported = re.findall(r'cross-agent coefficient c\s+: (\d+\.\d+)', text)
        if len(cells) != 1 or len(reported) != 1:
            raise ValueError('Historical transcript has missing or ambiguous operands')
        counts = list(map(int, cells[0]))
        value = coefficient(counts)
        if value is None or f'{float(value):.3f}' != reported[0]:
            raise ValueError('Historical point coefficient does not match retained counts')
        result[key] = {'path': str(path.relative_to(root)), 'sha256': hashlib.sha256(data).hexdigest(),
                       'counts': counts, 'n': sum(counts), 'coefficient': str(value),
                       'reported_rounded': reported[0], 'historical_inference_replayed': False,
                       'bootstrap_interval_replayed': False}
    return result


def verify_bindings(root=ROOT):
    manifest = json.loads((root / 'research/claim-correction/0.1.0/bindings.json').read_text())
    for row in manifest['preserved']:
        actual = hashlib.sha256((root / row['path']).read_bytes()).hexdigest()
        if actual != row['sha256']:
            raise ValueError('Preserved artifact changed: ' + row['path'])
    return len(manifest['preserved'])


def report(root=ROOT):
    controls = selection_controls()
    expected = ['1', '2/3', '4/3', '2/3', '10/9']
    if [row['coefficient'] for row in controls.values()] != expected:
        raise ValueError('Selection counterexample arithmetic changed')
    return {'artifact_id': 'reiyah.claim-correction.probe', 'version': '0.1.0',
            'status': 'passed', 'controls': controls, 'historical_counts': historical_counts(root),
            'preserved_bindings_checked': verify_bindings(root),
            'interpretation': 'Selected coincidence is neither a general lower nor upper population bound, including with a fixed threshold.',
            'scope': 'Authored exact counterexamples and retained-count arithmetic; no empirical population estimate, model run, bootstrap replay, or independent scientific replication.'}


if __name__ == '__main__':
    print(json.dumps(report(), indent=2, sort_keys=True))
