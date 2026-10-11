"""Independent canonical-label, confusion-table and implication-rule replay."""
import argparse
import ast
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import yaml

HERE = Path(__file__).resolve().parent
PROTOCOL = '5310a0d30a763d7cb2ee8de11befe0d993dd4a4773fc56da3051d28ed711d18e'
INPUTS = '094894fd47aed0ba47baf302b4d5e5c8479cf78e5857f77773f61434cf7643fe'


def insist(ok, message):
    if not ok:
        raise ValueError(message)


def parse(raw):
    def pairs(items):
        out = {}
        for key, val in items:
            insist(key not in out, 'duplicate JSON key')
            out[key] = val
        return out
    def bad(value):
        raise ValueError('invalid numeric constant: ' + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def read_sources(directory):
    insist(hashlib.sha256((HERE / 'protocol.json').read_bytes()).hexdigest() == PROTOCOL, 'protocol binding')
    b = (HERE / 'inputs.json').read_bytes()
    insist(hashlib.sha256(b).hexdigest() == INPUTS, 'input manifest binding')
    bindings = parse(b)['files']
    blobs = {}
    for name in bindings:
        b = (directory / name).read_bytes()
        insist(len(b) == bindings[name]['bytes'] and hashlib.sha256(b).hexdigest() == bindings[name]['sha256'], 'source binding: ' + name)
        blobs[name] = b
    return blobs


def rule_edges(raw):
    tree = ast.parse(raw)
    nodes = [n for n in tree.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == 'CONSISTENCY_RULES']
    insist(len(nodes) == 1, 'rule declaration')
    rules = ast.literal_eval(nodes[0].value)
    insist(len(rules) == 10, 'rule roster')
    return rules


def trace(answers, rules):
    active, broken = [], []
    for r in rules:
        q1, op1, v1 = r['if']
        q2, op2, v2 = r['then']
        insist(op1 in ('==', '!=') and op2 in ('==', '!='), 'unsupported predicate')
        if answers.get(q1) is None or answers.get(q2) is None:
            continue
        truth = {True: {'==': True, '!=': False}, False: {'==': False, '!=': True}}
        triggered = truth[answers[q1] == v1][op1]
        satisfied = truth[answers[q2] == v2][op2]
        if triggered:
            active.append(r['name'])
            if not satisfied:
                broken.append(r['name'])
    return active, broken


def rounded(fraction):
    return round(float(fraction), 4)


def consistency(mapping, rules):
    traces = [trace(a, rules) for a in mapping.values()]
    evaluable = [(a, b) for a, b in traces if a]
    n = len(evaluable)
    consistent = sum(not b for a, b in evaluable)
    counts = {}
    for rule in rules:
        key = rule['name']
        na = sum(key in a for a, b in traces)
        nv = sum(key in b for a, b in traces)
        counts[key] = {'n_applicable': na, 'n_violations': nv, 'compliance': rounded(F(na - nv, na)) if na else 1.0}
    triggered = sum(c['n_applicable'] > 0 for c in counts.values())
    rate = rounded(F(consistent, n)) if n else 0.0
    return {'rate': rate, 'wemcr': round(rate * triggered / len(rules), 4),
            'mean_compliance': rounded(sum((F(len(a) - len(b), len(a)) for a, b in evaluable), F(0)) / n) if n else 0.0,
            'rule_coverage': rounded(F(triggered, len(rules))),
            'n_rules_triggered': triggered, 'n_rules_total': len(rules),
            'n_clips': len(mapping), 'n_evaluable': n, 'n_consistent': consistent,
            'consistency_coverage': rounded(F(n, len(mapping))) if mapping else 0.0,
            'mean_violations': rounded(F(sum(len(b) for a, b in evaluable), n)) if n else 0.0,
            'per_rule': counts}


def metrics(records, labels=None):
    # Each row is (oracle, prediction, clip, question, category, source).
    matrix = Counter((r[0], r[1]) for r in records)
    classes = list(labels) if labels is not None else sorted({x for pair in matrix for x in pair})
    recalls, f1s = [], []
    for c in classes:
        correct = matrix[c, c]
        actual = sum(n for (a, b), n in matrix.items() if a == c)
        predicted = sum(n for (a, b), n in matrix.items() if b == c)
        if actual:
            recalls.append(F(correct, actual))
        f1s.append(F(2 * correct, actual + predicted) if actual + predicted else F(0))
    return {'accuracy': rounded(F(sum(a == b for a, b, *_ in records), len(records))) if records else 0.0,
            'balanced_acc': rounded(sum(recalls, F(0)) / len(recalls)) if recalls else 0.0,
            'macro_f1': rounded(sum(f1s, F(0)) / len(f1s)) if f1s else 0.0,
            'n': len(records)}


def native_rebuild(records, clips, config, rules):
    mapping = {c: {} for c in clips}
    for a, b, c, q, cat, src in records:
        mapping[c][q] = b
    result = {'n_total': len(records), 'n_parsed': len(records), 'parsable_coverage': 1.0,
              'global': metrics(records),
              'temporal': metrics([r for r in records if config[r[3]].get('metadata', {}).get('temporal', False)]),
              'per_category': {}, 'per_question': {}, 'consistency': consistency(mapping, rules), 'per_source': {}}
    for category in sorted({r[4] for r in records}):
        result['per_category'][category] = metrics([r for r in records if r[4] == category])
    for q in sorted(config):
        subset = [r for r in records if r[3] == q]
        labels = config[q]['choices']
        table = Counter((r[0], r[1]) for r in subset)
        result['per_question'][q] = {**metrics(subset, labels), 'confusion_matrix': {
            'labels': labels, 'matrix': [[table[a, b] for b in labels] for a in labels]}}
    for source in ('nuscenes', 'carla'):
        result['per_source'][source] = {**metrics([r for r in records if r[5] == source]),
            'consistency': consistency({c: a for c, a in mapping.items() if clips[c]['source'] == source}, rules)}
    return result


def answer_counts(rows):
    n = len(rows)
    correct = sum(a == b for a, b, *_ in rows)
    # This verifier explicitly refuses noncanonical answers instead of guessing.
    return {'opportunities': n, 'correct': correct, 'incorrect': n - correct, 'unparsed': 0,
            'reference_agreement_fraction_bounds': [str(F(correct, n)), str(F(correct, n))] if n else None}


def clip_counts(rows):
    good = [r for r in rows if r['fully_parsed'] and r['active_rules'] and not r['violated_rules']]
    return {'clips': len(rows), 'fully_parsed': len(rows),
            'consistency_partition': {'no_applicable_rule': sum(not r['active_rules'] for r in rows),
                                      'rule_violation': sum(bool(r['violated_rules']) for r in rows),
                                      'zero_rule_violations': len(good)},
            'primary_denominator': len(good),
            'primary_disagree_on_rule_question': sum(len(r['known_wrong_rule_questions']) != 0 for r in good),
            'primary_disagree_on_any_question': sum(len(r['known_wrong_questions']) != 0 for r in good),
            'fully_parsed_all_reference_agree': sum(not r['known_wrong_questions'] for r in rows)}


def released_comparison(native, released):
    todo = [('', native, released)]
    errors, leaves = [], 0
    while todo:
        path, a, b = todo.pop()
        if isinstance(a, dict):
            for key in reversed(list(a)):
                if key not in b:
                    errors.append(path + '/' + key + ': absent')
                else:
                    todo.append((path + '/' + key, a[key], b[key]))
        else:
            leaves += 1
            if canonical(a) != canonical(b):
                errors.append(path)
    return {'compared_fields': leaves, 'differences': errors,
            'scope': 'All recomputed native fields; stored extra inference timing fields not reproduced.'}


def reconstruct(directory):
    raw = read_sources(directory)
    definitions = yaml.safe_load(raw['questions.yaml'])['questions']
    config = {q['question_id']: q for q in definitions}
    insist(len(config) == len(definitions) == 14, 'question uniqueness')
    roster = parse(raw['selected_clips.json'])
    clips = {c['id']: c for c in roster}
    insist(len(clips) == len(roster) == 1000, 'clip uniqueness')
    insist(Counter(c['source'] for c in roster) == {'nuscenes': 500, 'carla': 500}, 'domain membership')
    for clip in roster:
        insist(set(clip['answers']) == set(config), 'oracle membership')
    rules = rule_edges(raw['metrics.py'])
    covered = {part[0] for rule in rules for part in (rule['if'], rule['then'])}
    summaries, private, natives, states = {}, {}, {}, {}
    for arm in ('vision', 'trajectory'):
        lines = [parse(line) for line in raw[arm + '.jsonl'].splitlines()]
        seen, records, answers = set(), [], {c: {} for c in clips}
        for entry in lines:
            insist(set(entry) == {'qa_id', 'clip_id', 'question_id', 'category', 'oracle_label', 'model_answer'}, 'record fields')
            insist(all(type(v) is str for v in entry.values()), 'record types')
            c, q = entry['clip_id'], entry['question_id']
            insist(c in clips and q in config and (c, q) not in seen, 'opportunity join')
            seen.add((c, q))
            oracle = clips[c]['answers'][q]
            insist(oracle == entry['oracle_label'] and oracle in config[q]['choices'], 'oracle mismatch')
            insist(entry['category'] == config[q]['category'], 'category mismatch')
            predicted = entry['model_answer'].lower().strip()
            insist(predicted in config[q]['choices'], 'noncanonical answer: independent parser scope exceeded')
            answers[c][q] = predicted
            records.append((oracle, predicted, c, q, entry['category'], clips[c]['source']))
        insist(seen == {(c, q) for c in clips for q in config}, 'incomplete opportunity roster')
        rows = []
        for c in sorted(clips):
            active, broken = trace(answers[c], rules)
            wrong = sorted(q for q in config if answers[c][q] != clips[c]['answers'][q])
            rows.append({'clip': c, 'source': clips[c]['source'], 'fully_parsed': True,
                         'parsed_answers': answers[c], 'active_rules': active, 'violated_rules': broken,
                         'known_wrong_questions': wrong, 'known_wrong_rule_questions': sorted(covered.intersection(wrong)),
                         'consistency_state': 'no_applicable_rule' if not active else 'rule_violation' if broken else 'zero_rule_violations'})
        native = native_rebuild(records, clips, config, rules)
        summaries[arm] = {'answers': answer_counts(records), 'clips': clip_counts(rows),
                         'by_source': {src: {'answers': answer_counts([r for r in records if r[5] == src]),
                                            'clips': clip_counts([r for r in rows if r['source'] == src])} for src in ('nuscenes', 'carla')},
                         'by_question': {q: answer_counts([r for r in records if r[3] == q]) for q in sorted(config)},
                         'native': {'global': native['global'], 'parsable_coverage': native['parsable_coverage'], 'consistency': native['consistency']},
                         'published_replay': released_comparison(native, parse(raw['published-' + arm + '.json']))}
        private[arm], natives[arm] = rows, native
        states[arm] = {(c, q): 'correct' if a == b else 'incorrect' for a, b, c, q, *_ in records}
    counts = Counter((states['vision'][k], states['trajectory'][k]) for k in states['vision'])
    report = {'artifact_id': 'reiyah.motion-consistency-audit.result', 'version': '0.1.0',
              'lifecycle_status': 'exploratory', 'protocol_sha256': PROTOCOL, 'inputs_sha256': INPUTS,
              'runs': summaries, 'oracle_consistency': consistency({c: r['answers'] for c, r in clips.items()}, rules),
              'paired_answer_transitions': [{'vision': a, 'trajectory': b, 'opportunities': n} for (a, b), n in sorted(counts.items())],
              'scope': 'Saved-file comparison against released oracle; no causal, physical-truth, model-provenance, safety or work-saving claim.'}
    return report, private, natives


def verify(directory, result, rows, native):
    expected, expected_rows, expected_native = reconstruct(directory)
    insist(canonical(rows) == canonical(expected_rows), 'per-clip witness mismatch')
    insist(canonical(native) == canonical(expected_native), 'native metric reconstruction mismatch')
    insist(canonical(result) == canonical(expected), 'aggregate result mismatch')
    return {'result': 'pass', 'answers_checked': 28000, 'clip_records_checked': 2000,
            'native_results_reconstructed': 2, 'published_fields_per_run': 234,
            'parser_scope': 'All observed answers normalize directly to declared labels; no native free-text fallback needed or independently qualified.',
            'independent_scientific_review': False}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sources', type=Path, required=True)
    ap.add_argument('--run', type=Path, required=True)
    args = ap.parse_args()
    report = verify(args.sources, *(parse((args.run / name).read_bytes()) for name in ('result.json', 'private_rows.json', 'native.json')))
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
