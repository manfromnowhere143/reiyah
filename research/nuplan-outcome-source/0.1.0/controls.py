"""Eleven authored source-custody rejection controls; no native simulator behavior."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import shutil
import tempfile
from audit import audit


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ('sources', 'inputs', 'findings', 'qualification'):
        p.add_argument('--' + key, type=Path, required=True)
    a = p.parse_args()
    original = json.loads(a.inputs.read_bytes())
    notes = json.loads(a.findings.read_bytes())
    decision = json.loads(a.qualification.read_bytes())
    if not audit(a.sources, original, notes, decision)['passed']:
        raise ValueError('positive_source_control')
    cases = [('omit_source', 'missing_source'), ('substitute_source', 'source_identity'),
             ('rebound_source', 'git_blob_binding'), ('duplicate', 'duplicate_source'),
             ('traversal', 'unsafe_path'), ('wrong_tag', 'release_binding'), ('wrong_tree', 'tree_object_binding'),
             ('wrong_span', 'span_identity'), ('bad_range', 'span_range'),
             ('claim_acceptance', 'unsupported_qualification'), ('unknown_as_zero', 'unknown_as_zero')]
    checked = []
    for name, reason in cases:
        with tempfile.TemporaryDirectory(prefix='nuplan-source-control-') as temporary:
            root = Path(temporary) / 'sources'
            shutil.copytree(a.sources, root)
            m, f, q = copy.deepcopy(original), copy.deepcopy(notes), copy.deepcopy(decision)
            row = next(x for x in m['files'] if x['path'].endswith('/step_simulation_time_controller.py'))
            path = root / row['path']
            if name == 'omit_source':
                path.unlink()
            elif name in ('substitute_source', 'rebound_source'):
                path.write_bytes(path.read_bytes() + b'\n')
                if name == 'rebound_source':
                    row.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            elif name == 'duplicate':
                m['files'].append(copy.deepcopy(row))
            elif name == 'traversal':
                row['path'] = '../outside.py'
            elif name == 'wrong_tag':
                path = root / 'metadata/tag.json'
                obj = json.loads(path.read_bytes())
                obj['object']['sha'] = '0' * 40
                path.write_text(json.dumps(obj))
                row = next(x for x in m['metadata'] if x['path'] == 'metadata/tag.json')
                row.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            elif name == 'wrong_tree':
                path = root / 'metadata/tree.json'
                obj = json.loads(path.read_bytes())
                next(x for x in obj['tree'] if x['type'] == 'blob')['sha'] = '0' * 40
                path.write_text(json.dumps(obj))
                row = next(x for x in m['metadata'] if x['path'] == 'metadata/tree.json')
                row.update(bytes=path.stat().st_size, sha256=hashlib.sha256(path.read_bytes()).hexdigest())
            elif name == 'wrong_span':
                f['notes'][0]['span_sha256'] = '0' * 64
            elif name == 'bad_range':
                f['notes'][0]['byte_start'] = -1
            elif name == 'claim_acceptance':
                q['Gate_A_accepted'] = True
            else:
                q['unqualified']['physical_clock_error_bound_us'] = 0
            try:
                audit(root, m, f, q)
            except ValueError as exc:
                if str(exc) != reason:
                    raise ValueError((name, reason, str(exc))) from exc
                checked.append({'case': name, 'rejected_for': reason})
            else:
                raise ValueError('incorrectly accepted ' + name)
    print(json.dumps({'artifact_id': 'reiyah.nuplan-outcome-source.controls', 'version': '0.1.0',
                      'passed': len(checked), 'checks': checked, 'native_controls_executed': False}, indent=2))


if __name__ == '__main__':
    main()
