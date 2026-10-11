"""Fixed conventional width-first order and a hindsight lower bound; simulated reveals."""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path, required=True)
    args = p.parse_args()
    rows = json.loads((args.run / 'private_witnesses.json').read_bytes())
    result = json.loads((args.run / 'result.json').read_bytes())
    verified = json.loads((args.run / 'verification.json').read_bytes())
    assert hashlib.sha256((args.run / 'result.json').read_bytes()).hexdigest() == verified['result_sha256']
    assert hashlib.sha256((args.run / 'private_counts.json').read_bytes()).hexdigest() == verified['private_counts_sha256']
    assert hashlib.sha256((args.run / 'private_witnesses.json').read_bytes()).hexdigest() == verified['private_witnesses_sha256']
    for row in rows:
        assert row['lower'] == min(row['delta'].values())
        assert row['upper'] == max(row['delta'].values())
    lower, upper = sum(r['lower'] for r in rows), sum(r['upper'] for r in rows)
    assert [lower, upper] == [-572, 432]
    ordered = sorted((r for r in rows if r['lower'] != r['upper']),
                     key=lambda r: (-(r['upper'] - r['lower']), r['image_id']))
    # Selection uses only known interval widths and IDs; outcomes enter after selection.
    trace = []
    for row in ordered:
        if lower > 0 or upper < 0:
            break
        value = row['delta']['revised']
        before = [lower, upper]
        lower += value - row['lower']
        upper += value - row['upper']
        trace.append({'image_id': row['image_id'], 'width': row['upper'] - row['lower'],
                      'observed_policy': 'revised', 'before': before, 'after': [lower, upper]})
    assert lower > 0 or upper < 0
    assert trace[-1]['before'][0] <= 0 <= trace[-1]['before'][1]
    # Independent minimality argument: no set of k reveals can reduce the upper bound
    # more than the k largest realized reductions. Reaching zero alone does not decide.
    gains = sorted((r['upper'] - r['delta']['revised'] for r in rows), reverse=True)
    required = result['delta_interval']['upper']
    oracle = result['delta_interval']['oracle_unit_cost_reveals']['minimum_reveals']
    assert sum(gains[:oracle - 1]) <= required < sum(gains[:oracle])
    count = len(trace)
    out = {'artifact_id': 'reiyah.threshold-reference-screen.conventional-result',
           'version': '0.1.0', 'lifecycle_status': 'exploratory',
           'conventional_reveals': count, 'oracle_minimum_reveals': oracle,
           'last_interval': [lower, upper], 'previous_interval': trace[-1]['before'],
           'choice': 'A' if upper < 0 else 'B',
           'oracle_previous_gain': sum(gains[:oracle - 1]),
           'oracle_sufficient_gain': sum(gains[:oracle]),
           'gain_needed_strictly_more_than': required,
           'maximum_observation_count_speedup': str(Fraction(count, oracle)),
           'possible_twofold_observation_reduction': count >= 2 * oracle,
           'possible_threefold_observation_reduction': count >= 3 * oracle,
           'protocol_sha256': hashlib.sha256(Path(__file__).with_name('conventional-protocol.json').read_bytes()).hexdigest(),
           'scope': 'Full-information ceiling for unit-cost policy reveals in this fixed all-revised world; not measured human work, a deployable oracle or a Reiyah performance result.'}
    for name, value in [('conventional-result.json', out), ('private_conventional_trace.json', trace)]:
        with (args.run / name).open('x') as f:
            json.dump(value, f, indent=2, sort_keys=True)
            f.write('\n')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    main()
