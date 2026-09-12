"""Replay bounded consumer forgeries against a selected immutable Fable release.

This reproduces defects in pinned bytes. It neither implements nor repairs a planner,
admits references, or serves as a replacement checker for future releases.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

SOURCE_COMMIT = '81ba0c6c00a6e6b727aab5719b71c262c341c27e'
EXPECTED = {
    'tools/measure/cohort_packet.py': 'c991e79bfcd89f0d961393bc152f388b5f4d89f3cc2a030d02ad04fd26a71b9c',
    'tools/measure/resolution_plan.py': '4e095c2c52736ace213cd60d3adcaa66c6a35e163038fa15595e0a8a547c1fe0',
    'tools/measure/check_resolution_plan.py': '6a18f0256f9dc3b745817dfb65bcff8ed78859fcfe6ddc691df4f714894d673b',
    'research/cohort-packet/0.1.0/open-two-anchor.json': '895500939a7eda2a657e6a3ec9ee76b50c53828b856bfa21883763b1c3b374df',
    'research/cohort-packet/0.1.0/adaptive-beats-fixed-case.json': 'dd9e1e8225f5191d72fe492eac55147a9bc8591b5844f05181e96611980d30ec',
    'research/cohort-packet/0.1.0/geometry-ambiguity-plan-case.json': 'fd6fa172d85e9ea5d6a6398b20f65e192eb4fed3230ea7dd48197f2bd0ad2a67',
}


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def load_module(name, root):
    path = root / 'tools/measure' / (name + '.py')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def replay(source, output):
    selected = {path: (source / path).read_bytes() for path in EXPECTED}
    for path, data in selected.items():
        if hashlib.sha256(data).hexdigest() != EXPECTED[path]:
            raise ValueError('SELECTED_SOURCE_CHANGED: ' + path)
    if any(name in sys.modules for name in ('cohort_packet', 'resolution_plan', 'check_resolution_plan')):
        raise ValueError('Run the replay in a fresh Python process')
    # The six selected files are inspected code/fixtures, not newly acquired software.
    load_module('cohort_packet', source)
    planner = load_module('resolution_plan', source)
    checker = load_module('check_resolution_plan', source)
    output.mkdir()  # Preserve failed attempts; never reuse an output identity.

    def write(name, value):
        with (output / name).open('xb') as stream:
            stream.write(encoded(value))

    def case(name):
        return json.loads(selected['research/cohort-packet/0.1.0/' + name])

    cases = {'open': case('open-two-anchor.json'),
             'adaptive': case('adaptive-beats-fixed-case.json'),
             'geometry': case('geometry-ambiguity-plan-case.json')}
    honest = {name: planner.plan(value) for name, value in cases.items()}
    assert honest['open']['state'] == 'no_admitted_reference'
    assert honest['open']['enclosure'] == {'lower': '-8', 'upper': '8'}
    assert honest['adaptive']['worst_case_observations'] == 2
    assert honest['geometry']['state'] == 'unresolvable_by_declared_questions'
    accepted = {}
    for name, value in cases.items():
        accepted[name] = checker.check(value, honest[name])
        write(name + '-case.json', value)
        write(name + '-honest.json', honest[name])
        write(name + '-honest-check.json', accepted[name])
    assert accepted['adaptive']['minimum_fixed_resolving_set']['size'] == 3

    attacks = [
        ('open-forged-bound', 'open', {'enclosure': {'lower': '100', 'upper': '100'}}, True),
        ('open-forged-criterion', 'open', {'improvement_criterion': 'supported'}, True),
        ('adaptive-forged-criterion', 'adaptive', {'improvement_criterion': 'supported'}, True),
        ('geometry-invented-witness', 'geometry', {'witness_cell': ['invented_a', 'invented_b']}, True),
        ('geometry-false-single-world', 'geometry', {'state': 'undecided_single_world', 'witness_cell': []}, True),
        ('open-invented-ambiguity', 'open', {'state': 'unresolvable_by_declared_questions',
                                           'witness_cell': ['invented_a', 'invented_b']}, True),
        # These controls demonstrate that the selected correction does reject its
        # existing malformed examples. We are not substituting a dummy checker.
        ('control-open-empty-ambiguity', 'open', {'state': 'unresolvable_by_declared_questions',
                                                'witness_cell': []}, False),
        ('control-understated-depth', 'adaptive', {'worst_case_observations': 1}, False),
    ]
    results = []
    for name, key, changes, expected_acceptance in attacks:
        forged = deepcopy(honest[key])
        forged.update(changes)
        write(name + '.json', forged)
        try:
            findings = checker.check(cases[key], forged)
            was_accepted = True
        except checker.PlanRefused as exc:
            findings = {'refused': str(exc)}
            was_accepted = False
        write(name + '-check.json', findings)
        assert was_accepted == expected_acceptance, (name, was_accepted, findings)
        results.append({'case': name, 'changes': changes, 'checker_accepted': was_accepted,
                        'kind': 'forgery' if expected_acceptance else 'rejection_control'})
    for path, data in selected.items():
        assert (source / path).read_bytes() == data, ('source changed during replay', path)
    summary = {'artifact_id': 'reiyah.plan-consumption.replay', 'version': '0.1.0',
               'selected_fable_commit': SOURCE_COMMIT, 'sources': EXPECTED,
               'honest_controls': {'open': 'no_admitted_reference, [-8,8]',
                                   'adaptive': 'depth 2, minimum fixed set 3',
                                   'geometry': 'two declared indistinguishable worlds'},
               'results': results, 'accepted_forgeries': 6, 'refused_controls': 2,
               'consumer_decision': 'hold full report consumption pending correction in its owning lane',
               'scope': 'Pinned software failure reproduction; no replacement planner/checker, human evidence or scientific claim'}
    write('RESULTS.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(replay(args.source_root.resolve(), args.output.resolve()), sort_keys=True))
