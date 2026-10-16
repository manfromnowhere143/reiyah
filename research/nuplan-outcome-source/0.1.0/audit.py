"""Offline source identity and bounded static-contract checks; no upstream execution."""
from pathlib import Path, PurePosixPath
import argparse
import ast
import hashlib
import json
import re
from fractions import Fraction


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit(root, manifest, findings, qualification):
    require(set(manifest) == {'artifact_id', 'version', 'release', 'metadata', 'files'}, 'manifest_schema')
    require(manifest['artifact_id'] == 'reiyah.nuplan-outcome-source.inputs' and manifest['version'] == '0.1.0', 'manifest_schema')
    data = {}
    for group in ('metadata', 'files'):
        for row in manifest[group]:
            expected = {'path', 'bytes', 'sha256'} | ({'git_blob', 'url'} if group == 'files' else set())
            require(set(row) == expected, 'manifest_row_schema')
            name = row['path']
            require(type(name) is str and not PurePosixPath(name).is_absolute()
                    and '..' not in PurePosixPath(name).parts and str(PurePosixPath(name)) == name
                    and name.startswith('upstream/' if group == 'files' else 'metadata/'), 'unsafe_path')
            require(name not in data, 'duplicate_source')
            path = root / name
            require(path.is_file() and not path.is_symlink(), 'missing_source')
            raw = path.read_bytes()
            require(type(row['bytes']) is int and len(raw) == row['bytes'] and sha(raw) == row['sha256'], 'source_identity')
            data[name] = raw
    require(len(manifest['files']) == 33 and set(r['path'] for r in manifest['metadata']) ==
            {'metadata/releases.json', 'metadata/tag.json', 'metadata/commit.json', 'metadata/tree.json'}, 'source_inventory')
    obj = lambda name: json.loads(data['metadata/' + name + '.json'])
    release = manifest['release']
    require(release['commit'] == 'ce3c323af01c0d7ec5672f7832ef53f9c679aab0'
            and release['tag'] == 'nuplan-devkit-v1.2', 'release_binding')
    tag, commit, tree = obj('tag'), obj('commit'), obj('tree')
    require(tag['ref'] == 'refs/tags/' + release['tag'] and tag['object']['type'] == 'commit'
            and tag['object']['sha'] == commit['sha'] == release['commit']
            and commit['tree']['sha'] == release['tree'] and tree['sha'] == release['commit']
            and tree['truncated'] is False, 'release_binding')
    releases = [r for r in obj('releases') if r['tag_name'] == release['tag']]
    require(len(releases) == 1 and releases[0]['published_at'] == release['published_at'], 'release_binding')
    entries = {r['path']: r for r in tree['tree']}
    require(len(entries) == len(tree['tree']), 'tree_duplicate')
    # The captured /trees/{commit} response echoes the requested commit in sha.
    # Reconstruct every tree object; do not confuse that envelope with a tree ID.
    groups = {}
    for path, entry in entries.items():
        parent, _, name = path.rpartition('/')
        groups.setdefault(parent, []).append((name, entry))
    for parent, children in groups.items():
        ordered = sorted(children, key=lambda pair: (pair[0] + ('/' if pair[1]['type'] == 'tree' else '')).encode())
        payload = b''.join(format(int(entry['mode'], 8), 'o').encode() + b' ' + name.encode() + b'\0'
                           + bytes.fromhex(entry['sha']) for name, entry in ordered)
        tree_digest = hashlib.sha1(b'tree ' + str(len(payload)).encode() + b'\0' + payload).hexdigest()
        expected = entries[parent]['sha'] if parent else release['tree']
        require(tree_digest == expected, 'tree_object_binding')
    for row in manifest['files']:
        raw = data[row['path']]
        upstream_path = row['path'].removeprefix('upstream/')
        entry = entries[upstream_path]
        blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        require(blob == row['git_blob'] == entry['sha'] and entry['size'] == len(raw)
                and entry['type'] == 'blob', 'git_blob_binding')
        require(row['url'] == release['repository'] + '/blob/' + release['commit'] + '/' + upstream_path, 'source_url')
    ids = []
    for note in findings['notes']:
        raw = data[note['path']]
        a, z = note['byte_start'], note['byte_end_exclusive']
        first, last = note['first_line'], note['last_line']
        lines = raw.splitlines(keepends=True)
        require(all(type(v) is int for v in (a, z, first, last))
                and 0 <= a < z <= len(raw) and 1 <= first <= last <= len(lines), 'span_range')
        require(sha(raw) == note['source_sha256'] and sha(raw[a:z]) == note['span_sha256']
                and a == sum(map(len, lines[:first - 1])) and z == sum(map(len, lines[:last])), 'span_identity')
        ids.append(note['id'])
    require(len(ids) == len(set(ids)) == 21, 'span_inventory')
    for key in ('native_execution_verified', 'upstream_tests_executed', 'empirical_outcome_admitted',
                'readiness_model_admitted', 'Gate_A_accepted'):
        require(qualification[key] is False, 'unsupported_qualification')
    require(qualification['new_trials_acquired'] == 0, 'unsupported_qualification')
    require(all(v is None for v in qualification['unqualified'].values()), 'unknown_as_zero')
    require(qualification['source_release'] == release, 'qualification_source')

    def source(basename):
        matches = [raw for name, raw in data.items() if name.endswith('/' + basename)]
        require(len(matches) == 1, 'source_name')
        return matches[0].decode()

    def method(filename, name):
        matches = [n for n in ast.walk(ast.parse(source(filename))) if isinstance(n, ast.FunctionDef) and n.name == name]
        require(len(matches) == 1, 'source_symbol')
        return matches[0]

    def expr(node):
        return ast.dump(node, include_attributes=False)

    end = method('step_simulation_time_controller.py', 'reached_end').body[-1]
    require(isinstance(end, ast.Return) and expr(end.value) == expr(ast.parse(
        'self.current_iteration_index >= self.number_of_iterations() - 1', mode='eval').body), 'end_rule')
    advance = method('step_simulation_time_controller.py', 'next_iteration')
    increments = [n for n in advance.body if isinstance(n, ast.AugAssign)]
    require(len(increments) == 1 and isinstance(increments[0].op, ast.Add)
            and expr(increments[0].target) == expr(ast.parse('self.current_iteration_index = 1').body[0].targets[0])
            and isinstance(increments[0].value, ast.Constant) and increments[0].value.value == 1, 'increment_rule')
    prop = method('simulation.py', 'propagate')
    calls = [n for n in ast.walk(prop) if isinstance(n, ast.Call)]
    locations = {ast.unparse(n.func): n.lineno for n in calls}
    require(locations['self._history.add_sample'] < locations['self._time_controller.next_iteration'], 'history_order')
    score = method('no_ego_at_fault_collisions.py', '_compute_collision_score').body[-1]
    require(expr(score.value) == expr(ast.parse('max(0.0, 1.0 - (number_of_collisions / (max_violation_threshold + 1)))', mode='eval').body), 'score_rule')
    config = source('no_ego_at_fault_collisions_statistics.yaml')
    thresholds = {k: int(v) for k, v in re.findall(r'max_violation_threshold_(\w+): (\d+)', config)}
    require(thresholds == {'vru': 0, 'vehicle': 0, 'object': 1}, 'score_defaults')

    # Authored deductions from the inspected normal path, not native simulator runs.
    cases = []
    for label, times in [('two', [0, 100000]), ('three', [0, 100000, 200000]),
                         ('irregular', [0, 100000, 250000, 450000]),
                         ('fifteen_second_requested_grid', list(range(0, 15000001, 100000)))]:
        n, index, visited = len(times), 0, []
        while index < n - 1:
            visited.append(index)
            index += 1
        require(visited == list(range(n - 1)) and visited[-1] == n - 2, 'authored_boundary')
        cases.append({'case': label, 'scenario_points': n, 'history_samples': len(visited),
                      'last_history_index': visited[-1], 'history_span_us': times[visited[-1]] - times[0],
                      'last_scenario_time_us': times[-1], 'last_scenario_point_in_history': False})
    native_tests = sorted(n.name for n in ast.parse(source('test_no_ego_at_fault_collisions.py')).body
                          if isinstance(n, ast.FunctionDef) and n.name.startswith('test_'))
    require(len(native_tests) == 7, 'native_test_inventory')
    return {'artifact_id': 'reiyah.nuplan-outcome-source.audit', 'version': '0.1.0', 'passed': True,
            'input_files_checked': len(data), 'upstream_files_checked': 33,
            'input_bytes_checked': sum(map(len, data.values())), 'source_spans_checked': len(ids),
            'tree_entries': len(entries), 'tree_objects_reconstructed': len(groups),
            'static_ast_checks': ['end_rule', 'increment_rule', 'history_order', 'score_rule'],
            'authored_boundary_examples': cases, 'default_score_thresholds': thresholds,
            'one_at_fault_object_score_fraction': str(max(Fraction(0), 1 - Fraction(1, thresholds['object'] + 1))),
            'upstream_test_functions_identified': native_tests,
            'upstream_code_executed': False, 'native_behavior_verified': False,
            'interpretation_automatically_proved': False, 'trials_acquired': 0, 'Gate_A_accepted': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for flag in ('sources', 'inputs', 'findings', 'qualification', 'output'):
        p.add_argument('--' + flag, type=Path, required=True)
    a = p.parse_args()
    result = audit(a.sources, json.loads(a.inputs.read_bytes()), json.loads(a.findings.read_bytes()),
                   json.loads(a.qualification.read_bytes()))
    with a.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()
