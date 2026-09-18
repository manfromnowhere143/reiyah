"""Reconstruct the report and check occupied time with a separate endpoint sweep."""
import argparse
from collections import Counter
from datetime import datetime
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
import json
import time

from cost_collect import digest, lines, put, read, reconcile, source_root, verify_bindings
from cost_math import require


def sweep_seconds(events):
    endpoints = Counter()
    for row in events:
        a, b = (datetime.fromisoformat(row[key]) for key in ('started_utc', 'finished_utc'))
        require(b >= a, 'Reversed interval in verifier')
        endpoints[a] += 1; endpoints[b] -= 1
    active, prior, total = 0, None, Decimal(0)
    for point, change in sorted(endpoints.items()):
        if active and prior is not None:
            d = point - prior
            total += Decimal(d.days * 86400 + d.seconds) + Decimal(d.microseconds) / 1000000
        active += change; require(active >= 0, 'Negative active event count')
        prior = point
    require(active == 0, 'Unclosed events')
    return total


def verify(root, freeze_path, report_path):
    tick = time.perf_counter()
    frozen, retained = read(freeze_path), read(report_path)
    verify_bindings(root, frozen)
    rebuilt = reconcile(root, frozen); rebuilt['freeze_sha256'] = digest(freeze_path)
    require(retained == rebuilt, 'Reconstructed report differs')
    occupied = sweep_seconds(retained['events'])
    require(occupied == Decimal(retained['outer_totals']['interval_union_seconds']), 'Independent interval sweep differs')
    projection = source_root(root, frozen)
    transfers = lines(projection / 'logs/downloads.jsonl')
    physical = sum(row['received_bytes'] for row in transfers)
    unique = {row['sha256']: row['received_bytes'] for row in transfers}
    require(physical == retained['downloads']['physical_received_body_bytes'], 'Physical byte sum differs')
    require(sum(unique.values()) == retained['downloads']['unique_content_bytes'], 'Unique byte sum differs')
    calls = lines(projection / 'private/FALLBACK_INFERENCE.jsonl')
    charge = sum((Fraction(row['prediction_call_seconds']) for row in calls), Fraction(0))
    require(charge == Fraction(retained['inference']['charged_prediction_seconds']), 'Independent charge sum differs')
    for row in calls:
        require(Fraction(row['forward_seconds']) + Fraction(row['decode_check']['seconds'])
                <= Fraction(row['prediction_call_seconds']) + Fraction(1, 10**9), 'Nested call bound differs')
    public_text = json.dumps(retained)
    require(all(value not in public_text for value in ('/Users/', 'X-Amz-', 'x-amz-', 'https://', 'http://')),
            'Report contains a private path or unsanitized URL')
    return {'artifact_id': 'reiyah.mission-costs.verification', 'version': '0.1.0',
            'report_sha256': digest(report_path), 'freeze_sha256': digest(freeze_path),
            'source_bindings_checked': sum(len(frozen[k]) for k in ('sources', 'download_payloads', 'implementation')),
            'report_reconstructed': True, 'independent_interval_sweep_matches': True,
            'physical_and_unique_download_totals_match': True, 'rational_inference_sum_matches': True,
            'private_path_and_url_screen_passed': True, 'seconds': time.perf_counter() - tick,
            'independent_scientific_replication': False, 'complete_economic_accounting': False}


def main():
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    p.add_argument('--freeze', type=Path, required=True); p.add_argument('--report', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); args = p.parse_args()
    result = verify(args.root.resolve(), args.freeze, args.report)
    put(args.output, result); print(json.dumps(result, sort_keys=True))


if __name__ == '__main__': main()
