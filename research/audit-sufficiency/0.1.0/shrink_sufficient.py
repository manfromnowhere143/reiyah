"""Shrink a sufficient confirmed set to an inclusion-minimal sufficient set.

Each removal is accepted only if the solver-tier certificate still reports sufficiency.
The result is a local minimum (no single label can be dropped), which is an upper bound on the
minimum sufficient audit; the implicit hitting set lower bound closes the interval from below.

Usage: python -B shrink_sufficient.py CASE_JSON POLICY_RESULT_JSON PRIVATE_OUT_JSON PUBLIC_OUT_JSON
"""
import json
import sys
import time

from sufficiency import Case

case = Case(json.load(open(sys.argv[1])))
record = json.load(open(sys.argv[2]))
confirmed = set(tuple(l) for l in record['_confirmed'])
started = time.perf_counter()
assert case.certificate(frozenset(confirmed))['solver'] == 'sufficient'
start_size = len(confirmed)
# try dropping labels with the fewest augmented edges first (least likely to be needed)
order = sorted(confirmed, key=lambda l: (len(case.by_id[l[0]].object_edges.get(l[1], ())), l))
checks = 0
removed = 0
for label in order:
    trial = frozenset(confirmed - {label})
    checks += 1
    if case.certificate(trial)['solver'] == 'sufficient':
        confirmed = set(trial)
        removed += 1
final = case.certificate(frozenset(confirmed))
b49 = case.certificate(frozenset(confirmed), budget=49)
out = {'policy_source': record['policy'], 'start_size': start_size, 'minimal_size': len(confirmed),
       'removed': removed, 'certificate_checks': checks, 'solver': final['solver'], 'sound': final['sound'],
       'budget_49': b49['solver'], 'seconds': round(time.perf_counter() - started, 1),
       'note': 'inclusion-minimal sufficient set under the unbounded deletion family; a local minimum, not proved global'}
json.dump({**out, '_set': sorted(confirmed)}, open(sys.argv[3], 'w'), indent=1)
json.dump(out, open(sys.argv[4], 'w'), indent=1)
print(json.dumps(out, indent=1))
