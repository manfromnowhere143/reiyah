import copy
from decimal import Decimal
import hashlib
import itertools
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import cost_collect as collect
from cost_verify import sweep_seconds
from cost_math import (CostError, decimal, download_totals, event_totals,
                       inference_totals, micros, union, validate_interval)

START = '2026-01-01T00:00:00+00:00'
END = '2026-01-01T00:00:10+00:00'


def event(**changes):
    row = {'id': 'e1', 'source': 'receipt1', 'category': 'control', 'status': 'completed',
           'started_utc': START, 'finished_utc': END, 'seconds': '9.9'}
    return {**row, **changes}


def call_fixture():
    calls = [{'request_sha256': 'request1', 'image_id': 'i1', 'model_id': 'model1',
              'state': 'exported', 'started_utc': START, 'finished_utc': END,
              'prediction_call_seconds': '2', 'forward_seconds': '1',
              'decode_check': {'seconds': '.2'}, 'cumulative_charged_seconds': '2'}]
    requests = {'request1': {'model_id': 'model1', 'image_ids': ['i1']}}
    launches = {'request1': {'started_utc': START, 'finished_utc': END, 'exit_code': 0}}
    return calls, requests, launches


class ArithmeticControls(unittest.TestCase):
    def test_decimal_sum_is_exact(self):
        self.assertEqual(decimal('.1') + decimal('.2'), Decimal('.3'))

    def test_duration_faults(self):
        for value in [True, False, -1, '-.1', 'NaN', 'Infinity', 0.1, None, 'broken']:
            with self.subTest(value=value), self.assertRaises(CostError): decimal(value)

    def test_timestamp_precision_and_timezone(self):
        self.assertEqual(micros('2026-01-01T00:00:00.000001Z') - micros(START), 1)
        for value in [None, '2026-01-01T00:00:00', '2026-01-01T01:00:00+01:00',
                      '2026-01-01T00:00:00.0000001Z', '2026-02-30T00:00:00Z']:
            with self.subTest(value=value), self.assertRaises(CostError): micros(value)

    def test_reverse_interval(self):
        with self.assertRaises(CostError): validate_interval(END, START)

    def test_union_exhaustive_against_independent_unit_occupancy(self):
        intervals = [(a, b) for a in range(5) for b in range(a, 5)]
        for choice in itertools.product(intervals, repeat=3):
            occupied = {t for a, b in choice for t in range(a, b)}
            result, _ = union(choice)
            self.assertEqual(result * 1000000, len(occupied))

    def test_touching_nested_and_zero_intervals(self):
        self.assertEqual(union([(0, 4), (1, 2), (4, 8), (9, 9)])[0], Decimal('0.000008'))
        self.assertEqual(union([]), (Decimal(0), []))

    def test_separate_endpoint_sweep_matches_nested_and_disjoint_events(self):
        rows = [event(), event(id='e2', started_utc='2026-01-01T00:00:01Z'),
                event(id='e3', started_utc='2026-01-01T00:00:20Z', finished_utc='2026-01-01T00:00:21Z'),
                event(id='e4', started_utc=END)]
        self.assertEqual(sweep_seconds(rows), 11)

    def test_overlapping_events_are_not_added_as_elapsed(self):
        result = event_totals([event(), event(id='e2')], START, END)
        self.assertEqual(result['duration_sum_seconds'], '19.8')
        self.assertEqual(result['interval_union_seconds'], '10')
        self.assertEqual(result['timestamp_overlap_seconds'], '10')

    def test_duplicate_event(self):
        with self.assertRaisesRegex(CostError, 'Duplicate'): event_totals([event(), event()], START, END)

    def test_unknown_and_missing_properties(self):
        for row in [event(extra=1), {k: v for k, v in event().items() if k != 'seconds'}]:
            with self.assertRaisesRegex(CostError, 'fields'): event_totals([row], START, END)

    def test_unrecognized_status_and_outside_cutoff(self):
        with self.assertRaises(CostError): event_totals([event(status='pass')], START, END)
        with self.assertRaises(CostError): event_totals([event()], START, START)

    def test_unknown_status_is_not_success(self):
        self.assertEqual(event_totals([event(status='unknown')], START, END)['statuses'], {'unknown': 1})

    def test_physical_receipts_and_unique_bytes_differ(self):
        rows = [{'id': 'same', 'path': p, 'sha256': 'a'*64, 'received_bytes': 10} for p in ('a', 'b')]
        result = download_totals(rows)
        self.assertEqual(result['physical_received_body_bytes'], 20)
        self.assertEqual(result['unique_content_bytes'], 10)
        self.assertEqual(result['reused_receipt_ids'], {'same': 2})

    def test_duplicate_path_invalid_bytes_and_digest_conflict(self):
        base = {'id': 'r', 'path': 'a', 'sha256': 'b'*64, 'received_bytes': 10}
        for rows in [[base, base], [{**base, 'received_bytes': True}],
                     [base, {**base, 'path': 'b', 'received_bytes': 11}], [{**base, 'sha256': 'wrong'}]]:
            with self.assertRaises(CostError): download_totals(rows)


class InferenceControls(unittest.TestCase):
    def test_complete_call_and_preinference_failure(self):
        calls, requests, launches = call_fixture()
        result = inference_totals(calls, requests, launches)
        self.assertEqual(result['charged_prediction_seconds'], '2')
        launches['unused'] = {**launches['request1'], 'exit_code': 1}
        requests['unused'] = requests['request1']
        self.assertEqual(inference_totals(calls, requests, launches)['calls'], 1)

    def test_missing_call_is_not_empty(self):
        calls, requests, launches = call_fixture()
        with self.assertRaisesRegex(CostError, 'missing'): inference_totals([], requests, launches)

    def test_duplicate_call(self):
        calls, requests, launches = call_fixture()
        with self.assertRaisesRegex(CostError, 'Duplicate'): inference_totals(calls*2, requests, launches)

    def test_wrong_model_image_or_request(self):
        for key, value in [('model_id', 'bad'), ('image_id', 'extra'), ('request_sha256', 'unbound')]:
            calls, requests, launches = call_fixture(); calls[0][key] = value
            with self.assertRaises(CostError): inference_totals(calls, requests, launches)

    def test_cumulative_drift_and_small_retained_roundoff(self):
        calls, requests, launches = call_fixture(); calls[0]['cumulative_charged_seconds'] = '2.0000000001'
        inference_totals(calls, requests, launches)
        calls[0]['cumulative_charged_seconds'] = '2.01'
        with self.assertRaisesRegex(CostError, 'Cumulative'): inference_totals(calls, requests, launches)

    def test_nested_time_exceeds_parent(self):
        calls, requests, launches = call_fixture(); calls[0]['forward_seconds'] = '3'
        with self.assertRaisesRegex(CostError, 'Nested'): inference_totals(calls, requests, launches)

    def test_interval_outside_launch(self):
        calls, requests, launches = call_fixture(); launches['request1']['finished_utc'] = START
        with self.assertRaisesRegex(CostError, 'nested'): inference_totals(calls, requests, launches)

    def test_failed_partial_run_needs_explicit_accounting(self):
        calls, requests, launches = call_fixture(); launches['request1']['exit_code'] = 1
        with self.assertRaisesRegex(CostError, 'partial'): inference_totals(calls, requests, launches)


class CustodyControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def write(self, relative, value):
        p = self.root / relative; p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value)); return p

    def test_source_escape_symlink_and_tampering(self):
        p = self.write('safe.json', {})
        row = collect.bind(self.root, p)
        frozen = {'sources': [row], 'download_payloads': [], 'implementation': []}
        collect.verify_bindings(self.root, frozen)
        p.write_text('changed')
        with self.assertRaisesRegex(CostError, 'changed'): collect.verify_bindings(self.root, frozen)
        (self.root/'link').symlink_to(p)
        with self.assertRaises(CostError): collect.safe(self.root, 'link')
        with self.assertRaises(CostError): collect.safe(self.root, str(p))

    def minimal_fixture(self):
        self.write('SESSION.json', {'started_utc': START, 'resource_limits': {'new_download_bytes': 100,
                   'cumulative_inference_seconds': 20}})
        self.write('checkpoints/INTERRUPTION_01.json', {})
        for name, extras in [('FALLBACK_RUNTIME_BINDING', {}), ('FALLBACK_ALLOCATION_FREEZE',
                    {'completed_utc': END, 'hash_verification_seconds': '.2'})]:
            self.write('private/'+name+'.json', {'started_utc': START, 'finished_utc': END, 'seconds': '.2', **extras})
        (self.root/'private/FALLBACK_INFERENCE.jsonl').write_text('')
        (self.root/'logs').mkdir()
        (self.root/'logs/downloads.jsonl').write_text('')
        start = {'stage': 'controls-1', 'started_utc': START, 'command': ['synthetic']}
        self.write('logs/controls-1-STARTED.json', start)
        self.write('logs/controls-1-COMPLETED.json', {**start, 'finished_utc': END, 'seconds': '9', 'exit_code': 1})
        for study in collect.STUDIES:
            self.write('candidate/research/'+study+'/0.1.0/summary.json', {'nested_seconds': '3'})
        self.write('candidate/research/public-predictions/0.1.0/costs.json', {'nested_seconds': '4'})
        here = self.root/'candidate/research/mission-costs/0.1.0'; here.mkdir(parents=True)
        (here/'PLAN.md').write_text('Synthetic plan')
        with patch.object(collect, 'HERE', here):
            collect.freeze(self.root, self.root/'snapshot')
        return collect.read(self.root/'snapshot/FREEZE.json')

    def test_full_synthetic_freeze_reconciliation(self):
        frozen = self.minimal_fixture(); collect.verify_bindings(self.root, frozen)
        report = collect.reconcile(self.root, frozen)
        self.assertEqual(report['outer_totals']['events'], 3)
        self.assertEqual(report['outer_totals']['statuses'], {'completed': 2, 'failed': 1})
        self.assertEqual(report['outer_totals']['interval_union_seconds'], '10')
        self.assertEqual(report['outer_totals']['duration_sum_seconds'], '9.4')
        self.assertIsNone(report['human_seconds'])
        self.assertIsNone(report['total_useful_work_seconds'])

    def test_missing_start_or_completion_rejected(self):
        frozen = self.minimal_fixture()
        for suffix in ['STARTED.json', 'COMPLETED.json']:
            changed = copy.deepcopy(frozen)
            changed['sources'] = [r for r in changed['sources'] if not r['path'].endswith(suffix)]
            with self.assertRaisesRegex(CostError, 'no retained start|no completion'):
                collect.reconcile(self.root, changed)

    def test_changed_start_fields_rejected(self):
        frozen = self.minimal_fixture()
        p = collect.source_root(self.root, frozen)/'logs/controls-1-STARTED.json'; row = collect.read(p); row['command'] = ['different']
        p.write_text(json.dumps(row))
        with self.assertRaisesRegex(CostError, 'fields differ'): collect.reconcile(self.root, frozen)

    def test_unknown_outer_timer_rejected(self):
        frozen = self.minimal_fixture()
        p = self.write('logs/unexpected.json', {'seconds': 1})
        frozen['sources'].append(collect.bind(self.root, p))
        target = collect.source_root(self.root, frozen)/'logs/unexpected.json'; target.write_bytes(p.read_bytes())
        with self.assertRaisesRegex(CostError, 'Unclassified'): collect.reconcile(self.root, frozen)

    def test_later_live_append_cannot_change_frozen_snapshot(self):
        frozen = self.minimal_fixture(); first = collect.reconcile(self.root, frozen)
        (self.root/'logs/downloads.jsonl').write_text('later receipt intentionally outside snapshot\n')
        collect.verify_bindings(self.root, frozen)
        self.assertEqual(collect.reconcile(self.root, frozen), first)


if __name__ == '__main__': unittest.main()
