"""Offline research-candidate bindings; this is not a Gate A release validator."""
import argparse
import hashlib
import json
import pathlib
import re
import sys

VERSION = '0.1.0'
ROOT = pathlib.Path(__file__).resolve().parents[2]


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-dir', type=pathlib.Path, required=True,
                        help='Read-only export of the declared Gate B baseline commit')
    args = parser.parse_args()
    baseline = args.baseline_dir.resolve()
    checks = []

    def check(name, ok, detail):
        checks.append({'check': name, 'state': 'pass' if ok else 'fail', 'detail': detail})

    old_manifest = json.loads((baseline / 'validation/gate-b-replay-manifest.json').read_text())
    manifest = json.loads((ROOT / 'validation/gate-b-replay-manifest.json').read_text())
    predecessor = manifest['predecessor']
    check('manifest_predecessor',
          sha(ROOT / predecessor['path']) == predecessor['sha256'] ==
          sha(baseline / 'validation/gate-b-replay-manifest.json'), predecessor['path'])
    check('all_inherited_replay_rows_preserved',
          manifest['transcripts'][:-1] == old_manifest['transcripts'],
          {'inherited': len(old_manifest['transcripts']), 'current': len(manifest['transcripts'])})
    changed_transcripts = [row['transcript'] for row in old_manifest['transcripts']
                           if sha(ROOT / row['transcript']) != sha(baseline / row['transcript'])]
    check('inherited_transcript_bytes_preserved', not changed_transcripts, changed_transcripts)

    result_path = ROOT / 'evidence/measurement/result_ao.json'
    result = json.loads(result_path.read_text())
    check('ao_tool_and_transcript_bindings',
          'sha256:' + result['tool_sha256'] == sha(ROOT / 'tools/measure/result_ao_reference_population_audit.py')
          and sha(result_path) == manifest['transcripts'][-1]['sha256'],
          {'transcript': sha(result_path), 'tool': result['tool_sha256']})
    replay = json.loads((ROOT / 'evidence/research-board/ao-replay-capture.json').read_text())
    check('ao_repeated_successful_exact_bytes',
          len(replay['runs']) == 2 and all(row['returncode'] == 0 and
          'sha256:' + row['sha256'] == sha(result_path) and row['bytes'] == result_path.stat().st_size
          for row in replay['runs']), 'Two local executions; not independent scientific replication')
    check('ao_source_stability_and_public_aggregate', result['input_hashes_unchanged_after_read']
          and all('examples' not in x for x in result['ghost_reference_population'].values()),
          'Original input hashes retained; source-derived cases remain private')

    register = json.loads((ROOT / 'evidence/claim-status-register-2026-09-07.json').read_text())
    previous = register['predecessor']
    check('register_predecessor', sha(ROOT / previous['path']) == previous['sha256'] ==
          sha(baseline / previous['path']), previous['path'])
    before_ids = {c['claim_id'] for c in json.loads((baseline / previous['path']).read_text())['claims']}
    after_ids = [c['claim_id'] for c in register['claims']]
    check('claim_ids_preserved_unique', before_ids.issubset(after_ids) and
          len(set(after_ids)) == len(after_ids), {'before': len(before_ids), 'after': len(after_ids)})

    regression = json.loads((ROOT / 'evidence/research-board/regression-capture.json').read_text())
    check('regression_tool_bytes_and_exit', regression['returncode'] == 0 and all(
        'sha256:' + digest == sha(ROOT / 'tools/measure' / name)
        for name, digest in regression['tool_hashes'].items()),
        'Recorded regression process must bind current tested tools')

    protected = []
    for directory in ['schemas', 'fixtures', 'manifests', 'missions', 'protocols', 'gate']:
        old = baseline / directory
        if not old.exists():
            continue
        old_files = {p.relative_to(baseline) for p in old.rglob('*') if p.is_file()}
        new_files = {p.relative_to(ROOT) for p in (ROOT / directory).rglob('*') if p.is_file()}
        protected.extend(str(p) for p in old_files ^ new_files)
        protected.extend(str(p) for p in old_files & new_files if sha(baseline / p) != sha(ROOT / p))
    check('released_contract_directories_unchanged', not protected, protected)

    changed_markdown = [p for p in ROOT.rglob('*.md') if 'history' not in p.relative_to(ROOT).parts
                        and (not (baseline / p.relative_to(ROOT)).exists() or
                             sha(p) != sha(baseline / p.relative_to(ROOT)))]
    broken = []
    for p in changed_markdown:
        for target in re.findall(r'\]\(([^\s)]+)\)', p.read_text()):
            if target.startswith(('https://', 'http://', '#')):
                continue
            path = target.split('#', 1)[0]
            if path and not (p.parent / path).exists():
                broken.append(str(p.relative_to(ROOT)) + ': ' + path)
    check('changed_document_relative_links', not broken,
          {'documents': len(changed_markdown), 'broken': broken})

    result = {'artifact_id': 'reiyah.research-board-candidate-verification.2026-09-07',
              'version': VERSION, 'lifecycle_status': 'exploratory',
              'scope': 'Offline development bindings, not scientific support or Gate A release validation',
              'checks': checks, 'result': 'pass' if all(c['state'] == 'pass' for c in checks) else 'fail'}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result['result'] == 'pass' else 1


if __name__ == '__main__':
    sys.exit(main())
