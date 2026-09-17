# A shared uncertain edge

Artifact: `reiyah.perception-revision.linear-example`, version `0.1.0`.
Basis: constructed hypothetical coordinates, not benchmark or physical observations.

A has detection a at (0,0). B retains a and adds b at (10,0). Reference x is at
(1.9,0) and y at (10,0); both may move within a closed 0.1 m ball. Matching requires
same class and distance strictly below 2 m. All objects have class car.

The edge a–x can disappear at the boundary, but it disappears for A and B together.
The guaranteed b–y edge contributes one extra match in every allowed realization.
With unit miss/false-positive penalties and one unit-weight anchor, improvement is
exactly 1. The ordinary matching/count bound gives [-1,1] and leaves the strict 0.1
criterion unresolved. The shared-edge certificate proves [1,1].

Run from the repository root using Python with `jsonschema` installed. The following
checks every source digest, produces both packets in a temporary directory and
verifies the linear packet in a fresh process. No dataset or optimizer is required.

```sh
python3 -B - <<'PY'
import hashlib, json, subprocess, sys, tempfile
from pathlib import Path

directory = Path('research/perception-revision/0.1.0/linear-example')
manifest = json.loads((directory / 'manifest.json').read_text())
for name, binding in manifest['files'].items():
    data = (directory / name).read_bytes()
    assert len(data) == binding['bytes']
    assert hashlib.sha256(data).hexdigest() == binding['sha256']

common = ['--input', str(directory / 'input.json'), '--input-sha256',
          manifest['files']['input.json']['sha256'],
          '--request', str(directory / 'geometry.json'), '--request-sha256',
          manifest['files']['geometry.json']['sha256']]
base = [sys.executable, '-B', '-m', 'tools.perception_revision']
with tempfile.TemporaryDirectory(prefix='reiyah-linear-example-') as work:
    ordinary, linear = Path(work) / 'ordinary.json', Path(work) / 'linear.json'
    subprocess.run(base + ['localization'] + common + ['--output', str(ordinary)], check=True)
    subprocess.run(base + ['localization'] + common + [
        '--linear-certificate', str(directory / 'coefficients.json'),
        '--linear-certificate-sha256', manifest['files']['coefficients.json']['sha256'],
        '--output', str(linear)], check=True)
    subprocess.run(base + ['verify-localization'] + common + [
        '--packet', str(linear), '--packet-sha256',
        hashlib.sha256(linear.read_bytes()).hexdigest()], check=True)
PY
```

The manifest records expected results and the exact input versions. This small
example illustrates the mechanism; it is not evidence of a typical speedup or an
economic advantage. See the [full method and limits](../../../../docs/PERCEPTION_LINEAR_BOUNDS_2026-09-17.md).
