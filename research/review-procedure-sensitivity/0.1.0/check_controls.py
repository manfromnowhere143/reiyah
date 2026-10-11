"""Focused paired-set controls and adversarial result verification."""
import argparse
import copy
import itertools
import json
from pathlib import Path
import reproduce
import verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, required=True)
    parser.add_argument('--rows', type=Path, required=True)
    parser.add_argument('--result', type=Path, required=True)
    args = parser.parse_args()
    raw = args.data.read_bytes()
    rows = verify.parse(args.rows.read_bytes())
    result = verify.parse(args.result.read_bytes())
    verify.verify(raw, rows, result)
    vocabulary = ('person', 'car', 'cantsolve', 'no_strict_majority')
    supports = [{vocabulary[i] for i in range(4) if mask & (1 << i)} for mask in range(1, 16)]
    checked = 0
    for left in supports:
        for right in supports:
            got = reproduce.classify(left, right)
            pairs = list(itertools.product(left, right))
            ordinary = {'person', 'car'}
            want = {
                'agreement': 'guaranteed_same' if all(a == b for a, b in pairs) else 'forced_difference' if all(a != b for a, b in pairs) else 'ambiguous',
                'forced_ordinary_switch': all(a in ordinary and b in ordinary and a != b for a, b in pairs),
                'possible_ordinary_switch': any(a in ordinary and b in ordinary and a != b for a, b in pairs),
                'forced_ordinary_to_unresolved': all(a in ordinary and b not in ordinary for a, b in pairs),
                'forced_unresolved_to_ordinary': all(a not in ordinary and b in ordinary for a, b in pairs),
                'forced_distinct_unresolved': all(a not in ordinary and b not in ordinary and a != b for a, b in pairs),
            }
            verify.demand(verify.encoded(got) == verify.encoded(want), 'paired-set control disagreement')
            checked += 1
    rejected = []

    def expect_reject(name, operation):
        try:
            operation()
        except ValueError as error:
            rejected.append({'control': name, 'diagnostic': str(error)})
        else:
            raise AssertionError('accepted invalid control: ' + name)

    expect_reject('changed source bytes', lambda: verify.verify(raw + b' ', rows, result))
    expect_reject('producer changed source bytes', lambda: reproduce.analyze(raw + b' '))
    for label, operation in [
        ('omitted object', lambda v: v.pop()),
        ('duplicate object', lambda v: v.append(v[0])),
        ('reordered objects', lambda v: v.reverse()),
        ('changed object join', lambda v: v[0].update(object_id='forged')),
        ('forged outcome support', lambda v: v[0]['proposed'].update(attainable=['cantsolve'])),
        ('empty outcome support', lambda v: v[0]['proposed'].update(attainable=[])),
        ('forged agreement', lambda v: v[0].update(agreement='unqualified')),
        ('bool in integer field', lambda v: v[0].update(object_index=False)),
        ('float in integer field', lambda v: v[0].update(object_index=0.0)),
        ('unknown row field', lambda v: v[0].update(unqualified=True)),
        ('unresolved winner count zero', lambda v: next(r for r in v if r['proposed']['raw_winning_votes'] is None)['proposed'].update(raw_winning_votes=0)),
    ]:
        changed = copy.deepcopy(rows)
        operation(changed)
        expect_reject(label, lambda: verify.verify(raw, changed, result))
    for label, operation in [
        ('changed aggregate', lambda v: v['summary']['agreement'].update(forced_difference=0)),
        ('float aggregate count', lambda v: v['summary'].update(objects=1000.0)),
        ('unknown result field', lambda v: v.update(unqualified=True)),
        ('source binding', lambda v: v.update(source_sha256='0' * 64)),
        ('protocol binding', lambda v: v.update(protocol_sha256='0' * 64)),
    ]:
        changed = copy.deepcopy(result)
        operation(changed)
        expect_reject(label, lambda: verify.verify(raw, rows, changed))
    expect_reject('empty pair support', lambda: reproduce.classify(set(), {'car'}))
    expect_reject('undeclared pair outcome', lambda: reproduce.classify({'invalid'}, {'car'}))
    expect_reject('duplicate JSON property', lambda: verify.parse('{"a": 1, "a": 2}'))
    expect_reject('nonfinite JSON', lambda: verify.parse('{"a": NaN}'))
    print(json.dumps({'artifact_id': 'reiyah.review-procedure-sensitivity.controls',
                      'version': '0.1.0', 'result': 'pass',
                      'paired_set_controls': checked, 'rejected': rejected,
                      'scope': 'Software controls only, not additional empirical observations.'}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
