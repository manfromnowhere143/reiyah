"""Offline integrity and scientific-state checks for the reference-study revision.

This is a research development check, not a Gate A release launcher or an
independent validation of the physical world. Private inputs are optional and
their absence is explicitly reported, never represented as replay evidence.
"""
import argparse
import json
import pathlib

from reference_study import STRATA, bound_protocol, digest, read_json, safe_asset
from reference_study_analysis import stratified_srs_bounds

ROOT = pathlib.Path(__file__).resolve().parents[2]


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root', type=pathlib.Path)
    args = parser.parse_args()
    evidence = ROOT / 'evidence/reference-study'
    old, old_freeze = bound_protocol(ROOT / 'research/reference-study/0.1.0')
    new, new_freeze = bound_protocol(ROOT / 'research/reference-study/0.2.0')
    require(new['supersedes_protocol_sha256'] == old_freeze['protocol_sha256'], 'Broken protocol lineage')
    require(old['version'] == '0.1.0' and new['version'] == '0.2.0', 'Released protocol identity changed')
    failed = read_json(evidence / 'design-0.1.0-precision-check.json')
    require(failed['lifecycle_status'] == 'failed', 'Failed design was promoted')
    require(all(v['scene_sampling_margin'] + v['within_scene_sampling_margin'] > 1
                for v in failed['groups'].values()), 'Design failure not supported by retained calculation')
    selected = read_json(evidence / 'selection-aggregate-0.2.0.json')
    repeated = read_json(evidence / 'selection-replay-0.2.0.json')
    ready = read_json(evidence / 'readiness-aggregate-0.2.0.json')
    closure = read_json(evidence / 'run-closure-0.2.0.json')
    require(selected['protocol_sha256'] == ready['protocol_sha256'] == new_freeze['protocol_sha256'],
            'Protocol, sample and readiness do not agree')
    require(selected['selection_sha256'] == ready['selection_sha256'] == repeated['first_sha256'] ==
            repeated['second_sha256'], 'Selection replay chain mismatch')
    require(selected['selection_key_sha256'] == new_freeze['selection_key_sha256'], 'Wrong randomization commitment')
    require(selected['selected_cases'] == ready['cases'] == 240, 'Frozen sample count changed')
    require(sum(g['selected_n'] for g in selected['groups'].values()) == 240, 'Strata do not partition sample')
    require(selected['sampling_design'] == 'within_stratum_srs', 'Wrong analysis design')
    for group in STRATA:
        g = selected['groups'][group]
        calculated = stratified_srs_bounds(g['population_n'], list(range(g['selected_n'])), {})
        require(calculated == ready['estimates'][group], 'Unreviewed analysis did not preserve unknowns')
    require(ready['reviews_received'] == 0 and ready['physical_performance_point_estimate'] is None,
            'This preparation record cannot claim collected review outcomes')
    for collection in ('code', 'public_artifacts'):
        for path, expected in closure[collection].items():
            require(digest(ROOT / path) == expected, 'Changed retained operand: ' + path)
    import jsonschema
    schema = read_json(ROOT / 'research/reference-study/0.2.0/review.schema.json')
    jsonschema.Draft202012Validator.check_schema(schema)
    require(digest(ROOT / 'research/reference-study/0.2.0/review.schema.json') == ready['review_schema_sha256'],
            'Review schema changed after preparation')
    private_checks = 'not_executed'
    if args.private_root:
        p = args.private_root
        chosen_path = p / 'selection-v2-run-1/selection.private.json'
        packets_path = p / 'review-packets-v2/packets.private.json'
        require(digest(chosen_path) == selected['selection_sha256'], 'Private selection changed')
        require(digest(packets_path) == ready['bound_packets_sha256'], 'Private evidence packets changed')
        require(digest(p / 'selection-v2.key') == new_freeze['selection_key_sha256'], 'Private selection key changed')
        chosen, packets = read_json(chosen_path), read_json(packets_path)
        require({c['case_id'] for c in chosen['cases']} == {c['case_id'] for c in packets}, 'Case populations differ')
        forbidden = {'detection_score', 'detection_name', 'stratum', 'cache_distance_m',
                     'complete_reference_distance_m', 'source_detection_id', 'prediction'}
        def inspect(value):
            if isinstance(value, dict):
                require(not (set(value) & forbidden), 'Reference or detector label leaked into reviewer packet')
                for v in value.values(): inspect(v)
            elif isinstance(value, list):
                for v in value: inspect(v)
        inspect(packets)
        assets = {}
        for packet in packets:
            require(packet['candidate_motion'] == 'unknown', 'Missing motion coerced into a trajectory')
            require(len({x['evidence_id'] for x in packet['evidence']}) == len(packet['evidence']),
                    'Duplicate evidence identifier')
            for item in packet['evidence']:
                if item['state'] == 'available':
                    assets[item['relative_asset_path']] = item['asset_sha256']
        for path, expected in assets.items():
            require(digest(safe_asset(p / 'raw-assets', path)) == expected, 'Raw sensor asset changed: ' + path)
        require(len(assets) == ready['unique_available_assets'], 'Available asset count differs')
        private_checks = 'passed_packet_blinding_and_raw_asset_hashes'
    print(json.dumps({'tool': 'verify_reference_study', 'version': '0.1.0', 'status': 'pass',
                      'input_closure_sha256': digest(evidence / 'run-closure-0.2.0.json'),
                      'protocol_lineage': 'failed_design_retained_and_superseded_before_judgments',
                      'selection_replay': 'same_implementation_identical_bytes', 'private_checks': private_checks,
                      'independent_judgments': 0, 'scientific_truth_verification': False,
                      'gate_a_release_validation': False}, sort_keys=True))


if __name__ == '__main__':
    main()
