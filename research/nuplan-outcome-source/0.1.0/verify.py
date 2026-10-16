"""Separate finite source checks using Git's blob hashing; no producer import."""
from pathlib import Path
from fractions import Fraction
import argparse
import hashlib
import json
import subprocess


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('sources', 'inputs', 'findings', 'result', 'output'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    manifest = json.loads(a.inputs.read_bytes())
    result = json.loads(a.result.read_bytes())
    findings = json.loads(a.findings.read_bytes())
    tree = json.loads((a.sources / 'metadata/tree.json').read_bytes())
    groups = {}
    entries = {row['path']: row for row in tree['tree']}
    for name, row in entries.items():
        parent, _, base = name.rpartition('/')
        groups.setdefault(parent, []).append((base, row))
    for parent, children in groups.items():
        children.sort(key=lambda pair: (pair[0] + ('/' if pair[1]['type'] == 'tree' else '')).encode())
        payload = b''.join(format(int(row['mode'], 8), 'o').encode() + b' ' + base.encode()
                           + b'\0' + bytes.fromhex(row['sha']) for base, row in children)
        actual = subprocess.check_output(['git', 'hash-object', '-t', 'tree', '--stdin'], input=payload).decode().strip()
        require(actual == (entries[parent]['sha'] if parent else manifest['release']['tree']), 'git_tree')
    total = 0
    for row in manifest['metadata'] + manifest['files']:
        raw = (a.sources / row['path']).read_bytes()
        require(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'], 'input_digest')
        total += len(raw)
        if 'git_blob' in row:
            blob = subprocess.check_output(['git', 'hash-object', '--stdin'], input=raw).decode().strip()
            require(blob == row['git_blob'], 'git_blob')
    spans = []
    for note in findings['notes']:
        lines = (a.sources / note['path']).read_bytes().splitlines(keepends=True)
        raw = b''.join(lines[note['first_line'] - 1:note['last_line']])
        require(hashlib.sha256(raw).hexdigest() == note['span_sha256'], 'source_span')
        spans.append(note['id'])
    expected = [(2, 1, 0, 0, 100000), (3, 2, 1, 100000, 200000),
                (4, 3, 2, 250000, 450000), (151, 150, 149, 14900000, 15000000)]
    observed = [(x['scenario_points'], x['history_samples'], x['last_history_index'],
                 x['history_span_us'], x['last_scenario_time_us']) for x in result['authored_boundary_examples']]
    require(observed == expected and all(x['last_scenario_point_in_history'] is False
                                        for x in result['authored_boundary_examples']), 'boundary_examples')
    require(Fraction(result['one_at_fault_object_score_fraction']) == Fraction(1, 2), 'score_fraction')
    require(result['input_files_checked'] == 37 and result['upstream_files_checked'] == 33
            and result['input_bytes_checked'] == total and result['source_spans_checked'] == len(spans) == 21, 'counts')
    require(result['upstream_code_executed'] is False and result['native_behavior_verified'] is False
            and result['interpretation_automatically_proved'] is False and result['trials_acquired'] == 0
            and result['Gate_A_accepted'] is False, 'claim_scope')
    output = {'artifact_id': 'reiyah.nuplan-outcome-source.verification', 'version': '0.1.0', 'passed': True,
              'input_files_checked': 37, 'git_blob_checks': 33, 'git_tree_checks': len(groups), 'bound_spans': 21,
              'authored_boundary_examples_checked': 4, 'upstream_code_executed': False,
              'native_behavior_verified': False, 'independent_scientific_replication': False}
    with a.output.open('x') as stream:
        json.dump(output, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
