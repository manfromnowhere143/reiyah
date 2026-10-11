"""Critical membership, unknown-state and forged-result rejection checks."""
import argparse
import copy
import json
from pathlib import Path
import reproduce as producer
import verify as checker


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sources', type=Path, required=True)
    ap.add_argument('--run', type=Path, required=True)
    args = ap.parse_args()
    blobs = producer.sources(args.sources)
    parser, metric = producer.native_modules(blobs)
    cfg = parser.load_question_config(args.sources / 'questions.yaml')
    roster = producer.load(blobs['selected_clips.json'])
    records = [producer.load(l) for l in blobs['vision.jsonl'].splitlines()]
    result, rows, native = [checker.parse((args.run / n).read_bytes()) for n in ('result.json', 'private_rows.json', 'native.json')]
    checker.verify(args.sources, result, rows, native)
    rejected = []

    def reject(name, fn):
        try:
            fn()
        except ValueError as exc:
            rejected.append({'control': name, 'diagnostic': str(exc)})
        else:
            raise AssertionError('invalid control accepted: ' + name)

    for name, change in [
        ('missing opportunity', lambda r: r.pop()),
        ('duplicated opportunity', lambda r: r.append(r[0])),
        ('unknown clip', lambda r: r[0].update(clip_id='unknown')),
        ('unknown question', lambda r: r[0].update(question_id='unknown')),
        ('embedded oracle changed', lambda r: r[0].update(oracle_label='unknown')),
        ('category changed', lambda r: r[0].update(category='unknown')),
        ('missing output field', lambda r: r[0].pop('model_answer')),
        ('unknown output field', lambda r: r[0].update(unqualified=True)),
        ('numeric response', lambda r: r[0].update(model_answer=0)),
    ]:
        changed = copy.deepcopy(records)
        change(changed)
        reject(name, lambda: producer.qualify(roster, changed, cfg))
    changed_roster = copy.deepcopy(roster)
    changed_roster[0]['source'] = 'unknown'
    reject('domain membership changed', lambda: producer.qualify(changed_roster, records, cfg))
    for name, change in [
        ('omitted clip witness', lambda r: r['vision'].pop()),
        ('duplicate clip witness', lambda r: r['vision'].append(r['vision'][0])),
        ('forged wrong-question witness', lambda r: r['vision'][0].update(known_wrong_questions=[])),
        ('unqualified consistency state', lambda r: r['vision'][0].update(consistency_state='safe')),
        ('unknown witness field', lambda r: r['vision'][0].update(extra=True)),
    ]:
        changed = copy.deepcopy(rows)
        change(changed)
        reject(name, lambda: checker.verify(args.sources, result, changed, native))
    for name, change in [
        ('erased primary disagreement', lambda r: r['runs']['vision']['clips'].update(primary_disagree_on_rule_question=0)),
        ('float opportunity count', lambda r: r['runs']['vision']['answers'].update(opportunities=14000.0)),
        ('boolean zero count', lambda r: r['runs']['vision']['answers'].update(unparsed=False)),
        ('forged protocol binding', lambda r: r.update(protocol_sha256='0' * 64)),
        ('unknown result field', lambda r: r.update(extra=True)),
        ('missing result run', lambda r: r['runs'].pop('trajectory')),
    ]:
        changed = copy.deepcopy(result)
        change(changed)
        reject(name, lambda: checker.verify(args.sources, changed, rows, native))
    changed = copy.deepcopy(native)
    changed['vision']['global']['accuracy'] = 1.0
    reject('forged native score', lambda: checker.verify(args.sources, result, rows, changed))
    reject('duplicate JSON key', lambda: checker.parse('{"x":1,"x":2}'))
    reject('nonfinite JSON', lambda: checker.parse('{"x":NaN}'))
    # A missing response remains unknown and cannot activate an implication.
    rule = {'name': 'control', 'if': ('x', '==', 'yes'), 'then': ('y', '==', 'no')}
    examples = [({}, ([], [])), ({'x': 'yes'}, ([], [])),
                ({'x': 'no', 'y': 'yes'}, ([], [])),
                ({'x': 'yes', 'y': 'no'}, (['control'], [])),
                ({'x': 'yes', 'y': 'yes'}, (['control'], ['control']))]
    for responses, expected in examples:
        checker.insist(checker.trace(responses, [rule]) == expected, 'implication control')
    empty = producer.count_states([{'state': 'unparsed'}])
    checker.insist(empty['incorrect'] == 0 and empty['unparsed'] == 1 and empty['reference_agreement_fraction_bounds'] == ['0', '1'], 'unknown answer must not become incorrect')
    print(json.dumps({'artifact_id': 'reiyah.motion-consistency-audit.controls', 'version': '0.1.0',
                      'result': 'pass', 'state_controls': 6, 'rejections': rejected,
                      'scope': 'Software verification only; not additional benchmark cases or independent review.'}, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
