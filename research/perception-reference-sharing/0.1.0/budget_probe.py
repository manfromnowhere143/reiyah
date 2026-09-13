"""Measure a downstream resource counterexample; no reference admission."""
import hashlib
import json
from copy import deepcopy
from pathlib import Path
import sys
import time

sys.path.insert(0, sys.argv[1])
from tools import perception_reference as reference
from tools.perception_decision import contract, checker, kernel
from tests.test_perception_reference import inputs, object_at, world

out = Path(sys.argv[2]); out.mkdir()
args = inputs(2, base_duplicates=128)
# Anchor 1 needs only one base detection. Reuse separately normalized inputs.
small = inputs(2)
args[1]['anchors'][1] = small[1]['anchors'][1]
args[2][1] = small[2][1]
for k, value in [('comparison_sha256', args[1]), ('normalizations_sha256', args[2]), ('catalog_sha256', args[3])]:
    args[0]['inputs'][k] = hashlib.sha256(contract.encoded(value)).hexdigest()
objects = [object_at('object-'+str(i), 10) for i in range(128)]
for i in range(64):
    args[0]['worlds'].append(world('world-'+str(i), [deepcopy(objects), [object_at('known', 3, time=2_000_000)]]))
(out/'inputs.json').write_bytes(contract.encoded(args))
tic = time.perf_counter(); compiled, receipt = reference.compile_model(*args); compile_seconds = time.perf_counter()-tic
tic = time.perf_counter(); packet = kernel.produce(compiled); checker.check(compiled, packet); evaluation_seconds = time.perf_counter()-tic
# Declared synthetic geometry: A has no edge, delta_A=-1; B's addition alone
# matches its one object, delta_B=+1. Equal weights give zero in every world.
assert all(r['record']['xy'][0]['numerator'] in ('0', '3') for n in args[2] for r in n['qualified_records'])
summary = {'direct_expected': ['0','0'], 'result': packet['result'], 'core_capacity': kernel._capacity(compiled),
           'geometry_comparisons_budgeted': receipt['geometry_comparisons_budgeted'],
           'anchor_states': receipt['anchor_reference_states'],
           'sizes': {'input': len(contract.encoded(args)), 'compiled': len(contract.encoded(compiled)), 'receipt': len(contract.encoded(receipt))},
           'compile_seconds': compile_seconds, 'evaluation_seconds': evaluation_seconds}
(out/'compiled.json').write_bytes(contract.encoded(compiled))
(out/'compilation.json').write_bytes(contract.encoded(receipt))
(out/'packet.json').write_bytes(contract.encoded(packet))
(out/'summary.json').write_bytes(contract.encoded(summary))
print(json.dumps(summary,sort_keys=True))
