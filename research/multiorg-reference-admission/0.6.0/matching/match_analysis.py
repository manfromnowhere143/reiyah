#!/usr/bin/env python3
"""Twelve fixed cases and exact original G/P for the selected four-image cohort."""
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
    for index, identity in enumerate(gate.IMAGES):
        for procedure in gate.PROCEDURES:
            gate.require(time.monotonic() - started < 120, 'matching wall budget')
            source = admitted['references'][identity][procedure]
            references = native.references(source['value'], source['source_path'], audit)
            cell, case, proof = native.fixed_case(identity, procedure,
                admitted['predictions'][identity]['faster'], admitted['predictions'][identity]['yolo'], references,
                admitted['context_sha256'])
            files = {}
            for kind, value in [('input', case), ('proof', proof)]:
                raw = native.contract.encoded(value); path = output / ('image-' + str(index) + '-' + procedure + '-' + kind + '.json')
                with path.open('xb') as stream: stream.write(raw)
                files[kind] = {'file': path.name, 'sha256': gate.sha(raw), 'bytes': len(raw)}
            cells.append(cell); packets.append({'image_id': identity, 'procedure': procedure, **files})
    gate.require(len(cells) == 12, 'complete twelve-case census')
    composition = native.compose(cells, list(gate.IMAGES), True)
    gate.require(time.monotonic() - started < 120, 'matching wall budget')
    result = {'artifact_id': 'reiyah.multiorg.selected-cohort-matching-result', 'version': '0.6.0', 'status': 'complete',
        'input_sha256': input_sha, 'contract_sha256': gate.CONTRACT_SHA, 'context': admitted['context'],
        'context_sha256': admitted['context_sha256'], 'producer_sha256': gate.sha(Path(__file__).read_bytes()),
        'admission_sha256': gate.sha(Path(gate.__file__).read_bytes()), 'native_dependencies': admitted['native_dependencies'],
        'image_ids': list(gate.IMAGES), 'model_variants': gate.VARIANTS, 'n_images': 4, 'selected_cohort_images': 4,
        'cells': cells, 'native_packets': packets, **composition,
        'scope': 'All twelve fixed recorded-reference graphs on the original selected four images. Exact conditional G/P composition; not physical truth, cohort-generalized performance or work advantage.',
        'limits': {'wall_seconds': 120, 'sampled_rss_bytes': 3221225472},
        'wall_seconds': time.monotonic() - started}
    with (output / 'result.json').open('xb') as stream: stream.write(gate.canonical(result))
    return result


def main():
    p = argparse.ArgumentParser()
    for name in ('input', 'input-sha256', 'repository', 'output'): p.add_argument('--' + name, required=True)
    a = p.parse_args(); result = run(a.input, a.input_sha256, a.repository, a.output)
    print('{"status":"complete","recorded_reference_cases":12}')


if __name__ == '__main__': main()
