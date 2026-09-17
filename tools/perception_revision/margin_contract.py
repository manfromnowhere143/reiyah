"""Scope and wire format for fixed-world deletion-margin proofs (0.1.0)."""
from .contract import MAX_WORK, ROLES, capacity, rational


def unavailable(case):
    missing = [{'anchor': a['id'], 'role': r, 'state': a[r]['state']}
               for a in case['anchors'] for r in ROLES if a[r]['state'] != 'observed']
    if missing:
        return 'input_blocked', {'kind': 'input_blocked', 'unavailable': missing}
    reasons = []
    if case['model']['variables'] or case['model']['clauses']:
        reasons.append('requires_one_unconditional_reference_world')
    if any(a['reference']['state'] != 'finite' for a in case['anchors']):
        reasons.append('requires_finite_references')
    if len({rational(a['weight']) for a in case['anchors']}) != 1:
        reasons.append('requires_uniform_anchor_weights')
    if sum(rational(case['loss'][k]) for k in ('false_negative', 'false_positive')) == 0:
        reasons.append('requires_positive_loss_step')
    if reasons:
        return 'unsupported_scope', {'kind': 'unsupported_scope', 'reasons': reasons}
    # Retain the matcher screening rule and charge the additional cover traversal.
    _, work = capacity(case)
    work += sum(len(a['output_b']['value']) + len(a['reference']['objects'])
                + len(a['reference']['edges']) for a in case['anchors'])
    if work > MAX_WORK:
        return 'resource_limited', {'kind': 'resource_limit', 'work_bound': work}
    return None


def result_template(case):
    return {'execution_status': 'succeeded', 'model_status': 'not_checked',
            'margin_status': 'not_evaluated', 'baseline_delta': None,
            'baseline_criterion': 'not_evaluated', 'per_deletion_bound': None,
            'deletion_lower_bound': None, 'minimum_adverse_deletions': None,
            'robust_through': None, 'pool_size': None, 'witness_delta': None,
            'necessary_confirmations': None,
            'error_family': 'reference_deletions_fixed_world',
            'audit_sufficiency': 'not_established',
            'reference_scope': case['evidence_kind'],
            'physical_coverage': 'not_established', 'authority_state': 'research_only'}
