"""CPU-only controls; run with unittest discovery in this directory."""
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

import probe


class CorrectionTests(unittest.TestCase):
    def test_counterexample_recomputed_threshold(self):
        rows = probe.selection_controls()
        self.assertEqual(rows['selected']['coefficient'], '1')
        self.assertEqual(rows['augmented_high_recomputed_median']['coefficient'], '2/3')
        self.assertEqual(rows['augmented_low_recomputed_median']['coefficient'], '4/3')

    def test_fixed_threshold_does_not_rescue_bound(self):
        rows = probe.selection_controls()
        self.assertEqual(rows['augmented_high_fixed_threshold']['coefficient'], '2/3')
        self.assertEqual(rows['augmented_low_fixed_threshold']['coefficient'], '10/9')

    def test_cells_and_median_match_historical_definition(self):
        row = probe.selection_controls()['selected']
        self.assertEqual(row['counts'], [1, 1, 1, 1])
        self.assertEqual(row['threshold'], '1/2')
        self.assertEqual(probe.summarize([(True, Fraction(1, 2))])['counts'], [0, 1, 0, 0])

    def test_zero_marginal_is_undefined(self):
        for counts in ([0, 0, 0, 0], [0, 0, 1, 3], [0, 1, 0, 3]):
            self.assertIsNone(probe.coefficient(counts))

    def test_invalid_counts_reject(self):
        for counts in ([1, 2, 3], [True, 0, 0, 0], [-1, 1, 1, 1], [1.0, 1, 1, 1]):
            with self.assertRaises(ValueError):
                probe.coefficient(counts)

    def test_unobserved_or_inexact_inputs_reject(self):
        for rows in ([], [(None, Fraction(1, 2))], [(True, 0.5)], [(False, Fraction(2))]):
            with self.assertRaises(ValueError):
                probe.summarize(rows)

    def test_historical_point_arithmetic(self):
        rows = probe.historical_counts()
        self.assertEqual(rows['H5']['n'], 13904)
        self.assertEqual(rows['H5b']['n'], 11104)
        self.assertEqual(rows['H5']['reported_rounded'], '0.972')
        self.assertEqual(rows['H5b']['reported_rounded'], '0.962')

    def test_transcript_missing_and_forged_values_reject(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            dest = root / 'human-channel/evidence'
            dest.mkdir(parents=True)
            for body in ('no operands', '2x2 counts [both,autoOnly,humOnly,neither]: 1, 1, 1, 1\ncross-agent coefficient c : 0.500\n'):
                (dest / 'h5_cross_agent_joint.txt').write_text(body)
                with self.assertRaises(ValueError):
                    probe.historical_counts(root)

    def test_preserved_bytes_and_tamper_rejection(self):
        self.assertGreater(probe.verify_bindings(), 0)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'research/claim-correction/0.1.0').mkdir(parents=True)
            (root / 'artifact.txt').write_text('changed')
            (root / 'research/claim-correction/0.1.0/bindings.json').write_text(json.dumps(
                {'preserved': [{'path': 'artifact.txt', 'sha256': '0' * 64}]}))
            with self.assertRaises(ValueError):
                probe.verify_bindings(root)

    def test_report_limits_are_explicit(self):
        output = probe.report()
        self.assertEqual(output['status'], 'passed')
        for row in output['historical_counts'].values():
            self.assertFalse(row['historical_inference_replayed'])
            self.assertFalse(row['bootstrap_interval_replayed'])

    def test_register_preserves_claims_and_withdraws_only_inferences(self):
        root = probe.ROOT
        current = json.loads((root / 'evidence/claim-status-register-2026-10-10.json').read_text())
        previous = json.loads((root / current['predecessor']['path']).read_text())
        rows = {c['claim_id'].rsplit('.', 1)[-1]: c for c in current['claims']}
        self.assertEqual(len(rows), len(current['claims']))
        self.assertTrue({c['claim_id'] for c in previous['claims']} <=
                        {c['claim_id'] for c in current['claims']})
        for name in ('selected-coincidence-population-bound', 'universal-kind-independence-law',
                     'cross-agent-safety-evidence-credit'):
            self.assertEqual(rows[name]['status'], 'withdrawn_as_stated')
            self.assertEqual(rows[name]['current_scientific_use'], 'forbidden')
        for name in ('cross-agent-coincidence-detectable-set', 'cross-agent-total-miss-coincidence'):
            self.assertEqual(rows[name]['status'], 'narrowed')
            self.assertEqual(rows[name]['current_scientific_use'], 'permitted')


if __name__ == '__main__':
    unittest.main()
