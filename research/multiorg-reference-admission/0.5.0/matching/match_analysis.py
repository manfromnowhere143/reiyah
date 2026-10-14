#!/usr/bin/env python3
"""Three fixed reference cases from an admitted complete analysis-only pair."""
import argparse
from pathlib import Path
import time
import input_gate as gate


def run(input_path, input_sha, repository, output):
    started = time.monotonic()
    admitted = gate.load_inputs(input_path, input_sha, repository)
    native = gate.native(repository); audit = native.load_audit()
    output = Path(output); output.mkdir(mode=0o700, exist_ok=False)
    cells, packets = [], []
    for procedure in gate.PROCEDURES:
        gate.require(time.monotonic() - started < 120, 'matching wall budget')
        source = admitted['references'][procedure]
        references = native.references(source['value'], source['source_path'], audit)
        cell, case, proof = native.fixed_case(gate.IMAGE, procedure,
            admitted['predictions']['faster'], admitted['predictions']['yolo'], references,
            admitted['context_sha256'])
        files = {}
        for kind, value in [('input', case), ('proof', proof)]:
            raw = native.contract.encoded(value); path = output / (procedure + '-' + kind + '.json')
            with path.open('xb') as stream: stream.write(raw)
            files[kind] = {'file': path.name, 'sha256': gate.sha(raw), 'bytes': len(raw)}
        cells.append(cell); packets.append({'procedure': procedure, **files})
    composition = native.compose(cells, [gate.IMAGE], False)
    gate.require(composition['global']['lower'] == composition['imagewise']['lower']
                 and composition['global']['upper'] == composition['imagewise']['upper'], 'one-image G/P identity')
    gate.require(time.monotonic() - started < 120, 'matching wall budget')
    result = {'artifact_id': 'reiyah.multiorg.first-image-matching-result', 'version': '0.5.0', 'status': 'complete',
        'input_sha256': input_sha, 'contract_sha256': gate.CONTRACT_SHA, 'context': admitted['context'],
        'context_sha256': admitted['context_sha256'], 'producer_sha256': gate.sha(Path(__file__).read_bytes()),
        'admission_sha256': gate.sha(Path(gate.__file__).read_bytes()), 'native_dependencies': admitted['native_dependencies'],
        'image_id': gate.IMAGE, 'model_variants': gate.VARIANTS, 'n_images': 1, 'selected_cohort_images': 4,
        'cells': cells, 'native_packets': packets, **composition,
        'scope': 'Three fixed recorded-reference graphs on one complete image. Exact conditional arithmetic; not physical truth or complete four-image coupling evidence.',
        'limits': {'wall_seconds': 120, 'sampled_rss_bytes': 3221225472},
        'wall_seconds': time.monotonic() - started}
    with (output / 'result.json').open('xb') as stream: stream.write(gate.canonical(result))
    return result


def main():
    p = argparse.ArgumentParser()
    for name in ('input', 'input-sha256', 'repository', 'output'): p.add_argument('--' + name, required=True)
    a = p.parse_args(); result = run(a.input, a.input_sha256, a.repository, a.output)
    print('{"status":"complete","recorded_reference_cases":3}')


if __name__ == '__main__': main()
