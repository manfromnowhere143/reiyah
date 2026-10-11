"""Offline fixed-file audit of rule consistency versus recorded-reference agreement."""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import platform
import sys
import time
import types

HERE = Path(__file__).resolve().parent
PROTOCOL = '5310a0d30a763d7cb2ee8de11befe0d993dd4a4773fc56da3051d28ed711d18e'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def unique(pairs):
    d = {}
    for k, v in pairs:
        need(k not in d, 'duplicate JSON key')
        d[k] = v
    return d


def load(raw):
    def bad(value):
        raise ValueError('nonfinite JSON: ' + value)
    return json.loads(raw, object_pairs_hook=unique, parse_constant=bad)


def dump(value):
    return json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'


def sources(directory):
    need(hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest() == PROTOCOL, 'changed frozen protocol')
    need(hashlib.sha256((HERE / 'inputs.json').read_bytes()).hexdigest() == '094894fd47aed0ba47baf302b4d5e5c8479cf78e5857f77773f61434cf7643fe', 'changed input bindings')
    bindings = load((HERE / 'inputs.json').read_bytes())
    need(bindings['protocol_sha256'] == PROTOCOL, 'input/protocol binding')
    result = {}
    for name, spec in bindings['files'].items():
        path = directory / name
        need(path.stat().st_size == spec['bytes'], 'input size: ' + name)
        raw = path.read_bytes()
        need(hashlib.sha256(raw).hexdigest() == spec['sha256'], 'input digest: ' + name)
        result[name] = raw
    return result


def native_modules(raw):
    """Execute reviewed exact private source bytes; no inference modules imported."""
    pkg = types.ModuleType('evaluation')
    pkg.__path__ = []
    sys.modules['evaluation'] = pkg
    out = {}
    for name in ('parsers', 'metrics'):
        mod = types.ModuleType('evaluation.' + name)
        sys.modules[mod.__name__] = mod
        exec(compile(raw[name + '.py'], name + '.py', 'exec'), mod.__dict__)
        out[name] = mod
    return out['parsers'], out['metrics']


def qualify(roster, records, config):
    need(type(roster) is list and len(roster) == 1000, 'clip count')
    clips = {r['id']: r for r in roster}
    need(len(clips) == 1000, 'duplicate clip')
    need(Counter(r['source'] for r in roster) == {'nuscenes': 500, 'carla': 500}, 'domain roster')
    need(len(config) == 14, 'question roster')
    for r in roster:
        need(set(r['answers']) == set(config), 'oracle question membership')
        need(('nuscenes' if r['id'].startswith('clip_') else 'carla') == r['source'], 'native domain identity mismatch')
        for q, answer in r['answers'].items():
            need(type(answer) is str and answer in config[q]['choices'], 'invalid canonical oracle')
    expected = {(c, q) for c in clips for q in config}
    seen = set()
    for r in records:
        need(set(r) == {'qa_id', 'clip_id', 'question_id', 'category', 'oracle_label', 'model_answer'}, 'changed prediction shape')
        need(all(type(v) is str for v in r.values()), 'non-string prediction field')
        key = r['clip_id'], r['question_id']
        need(key in expected, 'unknown opportunity')
        need(key not in seen, 'duplicate opportunity')
        seen.add(key)
        need(r['oracle_label'] == clips[key[0]]['answers'][key[1]], 'embedded oracle mismatch')
        need(r['category'] == config[key[1]]['category'], 'category mismatch')
    need(seen == expected, 'missing opportunities')
    return clips


def count_states(rows):
    counts = Counter(r['state'] for r in rows)
    correct, wrong, unknown = (counts[k] for k in ('correct', 'incorrect', 'unparsed'))
    n = len(rows)
    return {'opportunities': n, 'correct': correct, 'incorrect': wrong, 'unparsed': unknown,
            'reference_agreement_fraction_bounds': [str(Fraction(correct, n)), str(Fraction(correct + unknown, n))] if n else None}


def score_run(records, clips, config, parser, metric):
    questions_in_rules = {r[side][0] for r in metric.CONSISTENCY_RULES for side in ('if', 'then')}
    answers = defaultdict(dict)
    qa_rows = []
    for r in records:
        q, c = r['question_id'], r['clip_id']
        parsed = parser.parse_answer(r['model_answer'], config[q]['choices'], config[q]['answer_type'])
        state = 'unparsed' if parsed is None else 'correct' if parsed == clips[c]['answers'][q] else 'incorrect'
        answers[c][q] = parsed
        qa_rows.append({'clip': c, 'question': q, 'source': clips[c]['source'], 'state': state})
    clip_rows = []
    for c in sorted(clips):
        responses = answers[c]
        active, violated = [], []
        for rule in metric.CONSISTENCY_RULES:
            applies, fails = metric._check_rule(rule, responses)
            if applies:
                active.append(rule['name'])
            if fails:
                violated.append(rule['name'])
        known_wrong = sorted(q for q, a in responses.items() if a is not None and a != clips[c]['answers'][q])
        full = all(a is not None for a in responses.values())
        state = 'no_applicable_rule' if not active else 'rule_violation' if violated else 'zero_rule_violations'
        clip_rows.append({'clip': c, 'source': clips[c]['source'], 'fully_parsed': full,
                          'parsed_answers': responses, 'active_rules': active, 'violated_rules': violated,
                          'known_wrong_questions': known_wrong,
                          'known_wrong_rule_questions': sorted(set(known_wrong) & questions_in_rules),
                          'consistency_state': state})
    def clip_counts(rows):
        primary = [r for r in rows if r['fully_parsed'] and r['consistency_state'] == 'zero_rule_violations']
        return {'clips': len(rows), 'fully_parsed': sum(r['fully_parsed'] for r in rows),
                'consistency_partition': {k: sum(r['consistency_state'] == k for r in rows) for k in ('no_applicable_rule', 'rule_violation', 'zero_rule_violations')},
                'primary_denominator': len(primary),
                'primary_disagree_on_rule_question': sum(bool(r['known_wrong_rule_questions']) for r in primary),
                'primary_disagree_on_any_question': sum(bool(r['known_wrong_questions']) for r in primary),
                'fully_parsed_all_reference_agree': sum(r['fully_parsed'] and not r['known_wrong_questions'] for r in rows)}
    native = metric.evaluate(records, config)
    summary = {'answers': count_states(qa_rows), 'clips': clip_counts(clip_rows),
               'by_source': {s: {'answers': count_states([r for r in qa_rows if r['source'] == s]),
                                 'clips': clip_counts([r for r in clip_rows if r['source'] == s])} for s in ('nuscenes', 'carla')},
               'by_question': {q: count_states([r for r in qa_rows if r['question'] == q]) for q in sorted(config)},
               'native': {'global': native['global'], 'parsable_coverage': native['parsable_coverage'],
                          'consistency': native['consistency']}}
    return summary, clip_rows, qa_rows, native


def compare_published(actual, released):
    differences = []
    leaves = 0
    def walk(a, b, path):
        nonlocal leaves
        if type(a) is dict:
            for key, value in a.items():
                if key not in b:
                    differences.append(path + '/' + key + ': absent')
                else:
                    walk(value, b[key], path + '/' + key)
        else:
            leaves += 1
            if dump(a) != dump(b):
                differences.append(path)
    walk(actual, released, '')
    return {'compared_fields': leaves, 'differences': differences,
            'scope': 'All recomputed native fields; stored extra inference timing fields not reproduced.'}


def analyze(directory):
    raw = sources(directory)
    parser, metric = native_modules(raw)
    config = parser.load_question_config(directory / 'questions.yaml')
    roster = load(raw['selected_clips.json'])
    summaries, private, native_results, qa = {}, {}, {}, {}
    for label in ('vision', 'trajectory'):
        records = [load(line) for line in raw[label + '.jsonl'].splitlines()]
        clips = qualify(roster, records, config)
        summary, rows, answers, native = score_run(records, clips, config, parser, metric)
        summary['published_replay'] = compare_published(native, load(raw['published-' + label + '.json']))
        summaries[label], private[label], native_results[label] = summary, rows, native
        qa[label] = {(r['clip'], r['question']): r['state'] for r in answers}
    transitions = Counter((qa['vision'][k], qa['trajectory'][k]) for k in qa['vision'])
    oracle = metric.compute_consistency({r['id']: r['answers'] for r in roster})
    report = {'artifact_id': 'reiyah.motion-consistency-audit.result', 'version': '0.1.0',
              'lifecycle_status': 'exploratory', 'protocol_sha256': PROTOCOL,
              'inputs_sha256': hashlib.sha256((HERE / 'inputs.json').read_bytes()).hexdigest(),
              'runs': summaries, 'oracle_consistency': oracle,
              'paired_answer_transitions': [{'vision': a, 'trajectory': b, 'opportunities': n} for (a, b), n in sorted(transitions.items())],
              'scope': 'Saved-file comparison against released oracle; no causal, physical-truth, model-provenance, safety or work-saving claim.'}
    return report, private, native_results


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sources', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--expected', type=Path)
    args = ap.parse_args()
    need(not args.output.exists(), 'fresh output directory required')
    start = time.perf_counter()
    report, rows, native = analyze(args.sources)
    if args.expected:
        need(dump(report) == dump(load(args.expected.read_bytes())), 'expected result mismatch')
    args.output.mkdir(parents=True)
    for name, value in [('result.json', report), ('private_rows.json', rows), ('native.json', native)]:
        (args.output / name).write_text(dump(value))
    (args.output / 'execution.json').write_text(dump({'python': platform.python_version(), 'platform': platform.platform(),
        'wall_seconds': time.perf_counter() - start, 'scope': 'Local wall time excluding imports; not human effort or inference cost.'}))
    print(dump({'runs': {k: {'answers': v['answers'], 'clips': v['clips'], 'native_global': v['native']['global'], 'WPCR': v['native']['consistency']['wemcr'], 'published_replay': v['published_replay']} for k, v in report['runs'].items()}, 'oracle_consistency': report['oracle_consistency']}))


if __name__ == '__main__':
    main()
