"""Exercise output/package separation on fresh synthetic packages only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, required=True)
    parser.add_argument('--custody-sha256', required=True)
    parser.add_argument('--expect', choices=('vulnerable', 'protected'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.source_root.resolve()
    code = root/'tools/perception_discovery/custody.py'
    if digest(code.read_bytes()) != args.custody_sha256:
        raise SystemExit('Selected custody source identity differs')
    args.output.mkdir()  # Fresh capture identity; never edit retained packages.
    sys.path.insert(0, str(root))
    from tools.perception_discovery import custody, records
    from tools.perception_observation import package
    from tools.perception_decision.contract import Invalid, encoded
    from tests.test_perception_observation import fixture, tree

    reports, skipped = [], []
    with tempfile.TemporaryDirectory(prefix='synthetic-custody-', dir=args.output) as td:
        working = Path(td)
        request = fixture(working)
        original = working/'original'
        delivery = package.build(request, original, working/'synthetic-custody.json')
        seal = delivery['seal_sha256']
        manifest = json.loads((original/'manifest.json').read_bytes())
        record = records.draft(manifest, seal, 'b'*32)
        record['reviewer_id'] = 'synthetic-reviewer-for-custody-control'
        # Unknown exposure, unrecorded completion and not-inspected captures stay
        # explicit. No false assertion of a completed human review is needed.
        submitted = working/'synthetic-submission.json'
        submitted.write_bytes(encoded(record))
        for action in ('draft', 'seal'):
            for form in ('root', 'assets', 'alias', 'case_alias'):
                name = action+'-'+form
                evidence = working/name
                shutil.copytree(original, evidence)
                output = (evidence/'assets' if form == 'assets' else evidence)/'review.json'
                if form == 'alias':
                    alias = working/(name+'-alias'); alias.symlink_to(evidence, target_is_directory=True)
                    output = alias/'review.json'
                if form == 'case_alias':
                    alias = evidence.with_name(evidence.name.upper())
                    if not alias.exists() or not alias.samefile(evidence):
                        skipped.append({'case': name, 'reason': 'Filesystem does not resolve this case alias'})
                        continue
                    output = alias/'review.json'
                before = tree(evidence)
                package.verify(evidence, seal)
                operation = 'succeeded'
                try:
                    if action == 'draft':
                        custody.make_draft(evidence, seal, 'c'*32, output)
                    else:
                        custody.seal_record(submitted, digest(submitted.read_bytes()), evidence, seal, output)
                except Invalid as exc:
                    operation = exc.code
                after = tree(evidence)
                validation = 'verified'
                try:
                    package.verify(evidence, seal)
                except Invalid as exc:
                    validation = exc.code
                added = sorted(set(after)-set(before))
                changed = sorted(k for k in before if k not in after or before[k] != after[k])
                if output.exists():
                    (args.output/(name+'-unexpected-output.json')).write_bytes(output.read_bytes())
                reports.append({'case': name, 'operation': operation, 'package_after': validation,
                    'original_file_count': len(before), 'added_files': added, 'changed_original_files': changed,
                    'source_package_seal_sha256': seal, 'package_unchanged': before == after})
        (args.output/'manifest-input.json').write_bytes(encoded(manifest))
        (args.output/'synthetic-submission.json').write_bytes(submitted.read_bytes())
    expected = ('succeeded', 'OBS_FILE_SET', False) if args.expect == 'vulnerable' else (
        'DISCOVERY_PRIVATE_OUTPUT', 'verified', True)
    matches = all((r['operation'], r['package_after'], r['package_unchanged']) == expected
                  and not r['changed_original_files'] for r in reports)
    result = {'artifact_id': 'reiyah.discovery-custody.reproduction', 'version': '0.1.0',
        'custody_source_sha256': args.custody_sha256, 'expected_state': args.expect,
        'expectation_met': matches, 'cases': reports, 'skipped_cases': skipped, 'actual_human_records_created': 0,
        'scope': 'Synthetic package mutation/rejection controls, not a human review or admission'}
    (args.output/'RESULTS.json').write_bytes(encoded(result))
    if digest(code.read_bytes()) != args.custody_sha256:
        raise SystemExit('Custody source changed during reproduction')
    print(json.dumps({'cases': len(reports), 'skipped_cases': len(skipped), 'expectation_met': matches,
                      'results_sha256': digest((args.output/'RESULTS.json').read_bytes())}, sort_keys=True))
    return 0 if matches else 1


if __name__ == '__main__':
    raise SystemExit(main())
