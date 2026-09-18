"""Check copied identities and independently enumerate every appendix timer."""
from copy import deepcopy
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import sys
import time


def need(ok, message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path): return json.loads(path.read_text(), parse_float=Fraction)


def collect(value):
    found = {}; stack = [('', value)]
    while stack:
        prefix, node = stack.pop()
        if isinstance(node, list):
            stack.extend((prefix + '/' + str(i), v) for i, v in enumerate(node))
        elif isinstance(node, dict):
            for key, child in node.items():
                pointer = prefix + '/' + key
                if isinstance(child, (list, dict)): stack.append((pointer, child))
                elif 'seconds' in key and child is not None:
                    need(type(child) in (Fraction, str, int), 'Unexpected timer type')
                    number = Fraction(child); need(number >= 0, 'Negative timer'); found[pointer] = number
    return found


def compare(expected, rows):
    actual = {}
    for row in rows:
        key = (row['source'], row['field']); need(key not in actual, 'Duplicate timer reference')
        actual[key] = (Fraction(row['seconds']), row['accounting'])
    need(actual == expected, 'Missing, changed or extra source timer')


root = Path(sys.argv[1]).resolve(); output = Path(sys.argv[2]); tick = time.perf_counter()
public = root / 'candidate/research/mission-costs/0.1.0'; index = read(public / 'sources.json')
need(len({r['public_file'] for r in index['copies']}) == len(index['copies']), 'Duplicate public copy identity')
for row in index['copies']:
    target = public / row['public_file']; source = root / row['private_source']
    need(target.is_file() and not target.is_symlink() and sha(target) == sha(source) == row['sha256']
         and target.stat().st_size == row['bytes'], 'Public copy or source changed')
for report, verification in [('reconciliation.json', 'verification.json'),
                             ('supplement.json', 'supplement-verification.json'),
                             ('final-appendix.json', 'final-appendix-verification.json')]:
    need(read(public / verification)['report_sha256'] == sha(public / report), 'Report verification mismatch')
area = root / 'private/mission-costs-01/final-appendix-01'; frozen = read(area / 'FREEZE.json')
expected = {}; selected_sources = set()
for entry in frozen['inputs']:
    source = area / 'inputs' / entry['path']; need(sha(source) == entry['sha256'], 'Frozen timer source changed')
    if entry['role'].startswith(('nested:', 'nested_or_copied:')) or entry['role'] == 'published_snapshot_alias':
        selected_sources.add(entry['path'])
        expected.update({(entry['path'], field): (number, entry['role']) for field, number in collect(read(source)).items()})
parent = read(area / 'inputs/private/operating-witness-01/analysis/RESULTS.json')
required_states = {Path(row['path']).relative_to(root).as_posix() for section in ('refined_states', 'new_proofs')
                   for row in parent[section]}
need(required_states <= selected_sources and len(required_states) == 381, 'State/proof timer inventory omitted')
actual = read(public / 'final-appendix.json')['nested_new_study_timer_references']; compare(expected, actual)
faults = [actual[:-1], actual + actual[:1], deepcopy(actual), actual + [{**actual[0], 'field': '/invented_seconds'}]]
faults[2][0]['seconds'] = '999999999'
for bad in faults:
    try: compare(expected, bad)
    except ValueError: pass
    else: raise ValueError('Faulty timer inventory passed')
for path in public.iterdir():
    text = path.read_text()
    if path.suffix in ('.json', '.md'):
        need(all(secret not in text for secret in ('/Users/', 'X-Amz-', 'x-amz-', 'BEGIN PRIVATE KEY')),
             'Private path or credential marker in public text')
    if path.suffix == '.md':
        for link in re.findall(r'\]\(([^)]+)\)', text):
            if not link.startswith(('http://', 'https://', '#')):
                need((path.parent / link.split('#')[0]).is_file(), 'Broken local link: ' + link)
result = {'artifact_id': 'reiyah.mission-costs.publication-check', 'version': '0.1.0',
          'exact_public_copies': len(index['copies']), 'all_381_new_state_and_proof_sources_included': True,
          'independently_enumerated_nested_timers': len(expected), 'missing_duplicate_changed_extra_timer_controls': 4,
          'all_declared_timer_references_match': True, 'local_links_and_private_path_screen_passed': True,
          'checker_sha256': sha(Path(__file__)), 'seconds': time.perf_counter() - tick,
          'independent_scientific_replication': False}
with output.open('x') as stream: json.dump(result, stream, indent=2, sort_keys=True); stream.write('\n')
print(json.dumps(result))
