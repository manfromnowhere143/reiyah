# Copyright 2026 Daniel Wahnich
# SPDX-License-Identifier: Apache-2.0
"""Pure deterministic semantic predicates for Reiyah Gate A 1.2.0 fixtures.

This module is loaded from the validator's immutable/in-memory repository
snapshot.  It validates static contract examples only.  It does not execute a
model, estimator, intervention, product runtime, or scientific claim.
"""

from __future__ import annotations

import copy
import math
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence


TOLERANCE = 1e-12
UNKNOWN_STATES = {
    "missing",
    "unmeasured",
    "out_of_distribution",
    "sensor_invalid",
    "abstained",
}
COVERAGE_STATES = (
    "observed",
    "missing",
    "unmeasured",
    "out_of_distribution",
    "sensor_invalid",
    "abstained",
)

HUMAN_SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.2.0/human-automation-assessment.schema.json"
JOINT_SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.2.0/joint-performance-evaluation.schema.json"
STUDY_SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.2.0/study-design-preregistration.schema.json"
OPE_SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.2.0/sequential-off-policy-evaluation.schema.json"
ASSURANCE_SCHEMA_ID = "https://schemas.reiyah.invalid/scientific-contract/1.2.0/evaluation-assurance-bundle.schema.json"
PROTOCOL_RELEASE_ID = "reiyah.protocol.harbor-gate-a@1.2.0"
SCIENCE_SCHEMA_VERSION = "1.2.0"

# Independently reviewed digest of the exact executable reference-path dispatch
# owned by this science module.  The main validator derives the candidate rows
# from the five bound application-schema graphs and refuses to execute unless
# their canonical rows match this byte-frozen contract.  Keeping this value in
# the separately hash-bound science module prevents a schema-derived inventory
# from being copied back as its own purported handler proof.
REFERENCE_PATH_HANDLER_CONTRACT: Mapping[str, Any] = {
    "contract_version": SCIENCE_SCHEMA_VERSION,
    "binding_count": 345,
    "bindings_sha256": "sha256:dfaa744abee5f88dae813c6fdb11b624e9cc43725f401ddec47312b6aff436d0",
    "handler_counts": {
        "assumption_evidence_violations": 1,
        "classified_reference_path_violations": 217,
        "evidence_gap_reference_violations": 6,
        "lifecycle_policy_violations": 5,
        "schema_reference_violations": 5,
        "typed_reference_violations": 111,
    },
    "classification_counts": {
        "actor_reference": 9,
        "artifact_reference": 5,
        "document_local_identifier": 31,
        "explicit_evidence_gap": 6,
        "identity_declaration": 32,
        "registry_bare_identifier": 154,
        "rule_reference": 47,
        "schema_reference": 5,
        "versioned_reference": 56,
    },
}


# This is the executable semantic authority copied from the byte-bound v1.2
# definition registry.  The validator compares the complete definition
# association and payload before a domain handler may use it.  This prevents a
# schema-valid (or direct-call) last-write/swap/operand mutation from silently
# changing the scientific program implemented by this release.
FROZEN_EXECUTABLE_CONTRACT_DEFINITIONS: Mapping[str, Mapping[str, Any]] = {
    "reiyah.rule.ope-policy-distribution": {
        "kind": "rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.ope-policy-distribution",
            "contract_kind": "policy_distribution",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "normalization_tolerance": 1e-12,
            "normalization_comparison": "absolute_error_lte",
            "relative_tolerance": 0,
            "logged_propensity_reconciliation": "exact_within_normalization_tolerance",
            "support_scope": "every_target_supported_action_per_history",
            "weight_scope": "cumulative_trajectory_by_horizon",
            "ess_unit": "trajectory",
            "horizon_coverage": "every_declared_horizon_exactly_once",
            "terminal_reconciliation": "exact_trajectory_terminal_or_max_horizon_truncation",
            "weight_transformation_policy": "declared_recomputed_before_normalization_and_ess",
            "normalized_weight_policy": "sum_one_when_positive_raw_weight_exists_otherwise_explicit_unknown",
            "minimum_effective_sample_size": 2,
            "ess_disposition_policy": "exact_threshold_from_recomputed_ess",
            "history_identity_policy": "globally_unique_per_step",
            "support_cell_identity_policy": "exact_once_history_action",
            "trajectory_set_record_kind": "reiyah.kind.trajectory_set",
            "trajectory_manifest_resolution_policy": "exact_ordered_registry_members_bound_to_artifact",
            "policy_table_record_kind": "reiyah.kind.policy_table",
            "policy_table_resolution_policy": "exact_policy_role_history_action_probabilities_bound_to_artifact",
            "behavior_policy_ref": {
                "record_id": "reiyah.policy.synthetic_behavior",
                "record_kind": "reiyah.kind.policy",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "target_policy_ref": {
                "record_id": "reiyah.policy.synthetic_target",
                "record_kind": "reiyah.kind.policy",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        },
    },
    "reiyah.rule.causal-identification": {
        "kind": "rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.causal-identification",
            "contract_kind": "causal_identification",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "identification_strategy": "backdoor_adjustment",
            "requires_pre_treatment": True,
            "requires_observed": True,
            "prohibited_roles": [
                "treatment",
                "outcome",
                "mediator",
                "post_treatment_descendant",
                "collider",
                "selection",
            ],
            "acyclicity_sufficient": False,
            "query_binding": "exact_treatment_outcome_estimand_graph_and_selected_set",
            "selected_set_reconciliation": "exact_query_selected_adjustment_ids",
            "analysis_unit_id": "reiyah.unit.synthetic-encounter",
            "split_unit_id": "reiyah.unit.subject",
            "analysis_unit_set_ref": {
                "record_id": "reiyah.analysis-unit-set.synthetic-study-1.2",
                "record_kind": "reiyah.kind.analysis_unit_set",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "analysis_unit_member_ids": [
                "reiyah.subject.synthetic_001",
                "reiyah.subject.synthetic_002",
                "reiyah.subject.synthetic_003",
                "reiyah.subject.synthetic_004",
                "reiyah.subject.synthetic_005",
                "reiyah.subject.synthetic_006",
            ],
            "split_partition_policy": "ordered_exact_member_rows_pairwise_disjoint_complete_union",
            "split_freeze_policy": "every_manifest_strictly_before_first_outcome_access",
            "stratification_input_policy": "exact_observed_pre_treatment_graph_node_role_available_by_manifest_freeze",
        },
    },
    "reiyah.rule.readiness-unknown-propagation": {
        "kind": "aggregation_rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.readiness-unknown-propagation",
            "contract_kind": "readiness_aggregation",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "required_unknown_policy": "propagate_nonobserved_state",
            "safety_critical_compensation_allowed": False,
            "unresolved_set_policy": "exact_required_or_safety_critical_or_positively_weighted_unknown_capability_ids",
            "capability_set_record_kind": "reiyah.kind.capability_set",
            "capability_manifest_resolution_policy": "exact_registry_members_bound_to_artifact",
            "capability_criterion_rule_ref": {
                "rule_id": "reiyah.rule.capability_threshold",
                "rule_kind": "reiyah.kind.readiness_criterion",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        },
    },
    "reiyah.rule.recovery-event-derivation": {
        "kind": "decision_rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.recovery-event-derivation",
            "contract_kind": "recovery_event_derivation",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "event_selection": "earliest_qualifying_inside_frozen_window",
            "elapsed_time_origin": "index_event",
            "absence_in_valid_complete_window": "right_censored",
            "nonobserved_input_policy": "propagate_explicit_nonobserved_or_invalid",
            "no_qualifying_event_policy": "right_censored_only_for_complete_valid_window",
            "event_manifest_resolution_policy": "exact_registry_event_members_completeness_and_artifact_binding",
            "recovery_criterion_ref": {
                "rule_id": "reiyah.rule.recovery_event",
                "rule_kind": "reiyah.kind.recovery_criterion",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "censoring_policy_ref": {
                "rule_id": "reiyah.rule.recovery_censoring",
                "rule_kind": "reiyah.kind.censoring_policy",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "competing_event_policy_ref": {
                "rule_id": "reiyah.rule.recovery_competing",
                "rule_kind": "reiyah.kind.competing_policy",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "event_type_role_bindings": [
                {"event_type": "reiyah.event_type.capability_restored", "role": "recovery"},
                {"event_type": "reiyah.event_type.observation_censored", "role": "censoring"},
                {"event_type": "reiyah.event_type.readiness_loss", "role": "competing"},
            ],
        },
    },
    "reiyah.rule.transfer-eligibility": {
        "kind": "transfer_rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.transfer-eligibility",
            "contract_kind": "transfer_eligibility",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "required_conditions": [
                "metric_identity",
                "metric_direction",
                "population_harmonization",
                "support_overlap",
                "measurement_invariance",
                "access_chronology",
                "adaptation_disclosure",
                "target_tuning_disclosure",
            ],
            "failed_condition_policy": "unqualified_result_ineligible",
            "minimum_observed_count": 1,
            "estimate_observability_policy": "observed_requires_minimum_observed_count",
            "metric_direction": "lower_is_better",
            "source_domain_id": "reiyah.domain.synthetic_source",
            "target_domain_id": "reiyah.domain.synthetic_target",
            "domain_role_binding_policy": "exact_distinct_source_and_target_domain_ids",
            "arithmetic_comparison": "absolute_error_lte",
            "arithmetic_absolute_tolerance": 1e-12,
            "relative_tolerance": 0,
        },
    },
    "reiyah.rule.conformal-guarantee-disposition": {
        "kind": "conformal_rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.conformal-guarantee-disposition",
            "contract_kind": "conformal_guarantee",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "guarantee_separate_from_empirical_coverage": True,
            "required_assumption_failure_policy": "guarantee_not_supported",
            "empirical_coverage_policy": "exact_covered_over_evaluated_with_nonobserved_zero_or_unknown",
            "group_scope_policy": "registry_bound_group_set_with_declared_disjoint_or_overlapping_aggregation",
            "calibration_set_ref": {
                "record_id": "reiyah.split.synthetic_calibration",
                "record_kind": "reiyah.kind.split",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "test_set_ref": {
                "record_id": "reiyah.split.synthetic_test",
                "record_kind": "reiyah.kind.split",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "split_role_binding_policy": "exact_calibration_and_test_split_ids_roles_and_versions",
            "arithmetic_comparison": "absolute_error_lte",
            "arithmetic_absolute_tolerance": 1e-12,
            "relative_tolerance": 0,
        },
    },
    "reiyah.rule.ood-population-partition": {
        "kind": "ood_rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.ood-population-partition",
            "contract_kind": "population_partition",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "states": list(COVERAGE_STATES),
            "disjoint_required": True,
            "exhaustive_required": True,
            "derived_rates_required": True,
            "joint_axis_cells": [
                "reference_ood_detector_ood",
                "reference_ood_detector_in_distribution",
                "reference_ood_detector_unknown",
                "reference_in_distribution_detector_ood",
                "reference_in_distribution_detector_in_distribution",
                "reference_in_distribution_detector_unknown",
                "reference_unknown_detector_ood",
                "reference_unknown_detector_in_distribution",
                "reference_unknown_detector_unknown",
            ],
            "reference_detector_axes_disjoint": True,
            "unknown_axis_policy": "retain_unknowns_as_atomic_partition_cells",
        },
    },
    "reiyah.rule.worst-group-eligibility": {
        "kind": "minimum_information_rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.worst-group-eligibility",
            "contract_kind": "minimum_information",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "minimum_count": 30,
            "minimum_coverage": 0.8,
            "minimum_effective_sample_size": 20,
            "maximum_interval_width": 0.25,
            "ineligible_group_policy": "complete_worst_group_unknown",
            "arithmetic_comparison": "absolute_error_lte",
            "arithmetic_absolute_tolerance": 1e-12,
            "relative_tolerance": 0,
            "tie_comparison": "absolute_error_lte",
            "tie_absolute_tolerance": 1e-12,
        },
    },
    "reiyah.rule.human-belief-observation-decision-reconciliation": {
        "kind": "rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.human-belief-observation-decision-reconciliation",
            "contract_kind": "human_information_reconciliation",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "belief_state_space_coverage": "every_registry_state_exactly_once",
            "belief_probability_policy": "sum_one_within_protocol_tolerance",
            "belief_normalization_policy_binding": "exact_policy_identity_release_scope_operands_and_runtime_boundary",
            "observation_validity_value_policy": "independent_compatible_axes",
            "object_reconciliation": "exact_record_id_kind_and_version",
            "information_set_reconciliation": "exact_membership_and_freeze",
            "observation_time_policy": "event_lte_measured_lte_available",
            "availability_boundary_policy": "available_lte_belief_as_of_and_information_freeze",
            "temporal_reconciliation": "event_measurement_availability_belief_decision_exact_chain",
        },
    },
    "reiyah.rule.joint-silent-miss-identifiability": {
        "kind": "rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.joint-silent-miss-identifiability",
            "contract_kind": "joint_silent_miss_identifiability",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "common_opportunity_cells": [
                "both_miss",
                "human_only_miss",
                "automation_only_miss",
                "neither_miss",
            ],
            "marginal_derivation": "exact_from_disjoint_common_opportunity_cells",
            "identifiability_policy": "observed_common_cells_or_nonidentifiable",
            "joint_unknown_propagation": "nonobserved_operand_forces_nonidentified_nonobserved_summary",
            "opportunity_set_record_kind": "reiyah.kind.opportunity_set",
            "opportunity_manifest_resolution_policy": "exact_ordered_registry_rows_bound_to_artifact",
            "opportunity_set_ids": [
                "reiyah.opportunity-set.synthetic-joint-observed",
                "reiyah.opportunity-set.synthetic-joint-nonobserved",
                "reiyah.opportunity-set.synthetic-joint-empty",
            ],
            "opportunity_rule_ref": {
                "rule_id": "reiyah.rule.joint_miss_opportunity",
                "rule_kind": "reiyah.kind.event_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "object_ref": {
                "record_id": "reiyah.object.synthetic_vehicle",
                "record_kind": "reiyah.kind.vehicle_object",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "human_channel_ref": {
                "record_id": "reiyah.channel.synthetic_human_observation",
                "record_kind": "reiyah.kind.observation_channel",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "automation_channel_ref": {
                "record_id": "reiyah.channel.synthetic_automation_observation",
                "record_kind": "reiyah.kind.observation_channel",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "warning_rule_ref": {
                "rule_id": "reiyah.rule.joint_warning_observation",
                "rule_kind": "reiyah.kind.event_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "fallback_rule_ref": {
                "rule_id": "reiyah.rule.joint_fallback_observation",
                "rule_kind": "reiyah.kind.event_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "clock_id": "reiyah.clock.synthetic-utc",
            "window_id": "reiyah.window.joint-opportunity-001",
            "row_derivation_policy": "exact_reference_validity_channel_warning_fallback_rows_to_disjoint_cells",
            "silent_joint_miss_policy": "both_channels_miss_and_warning_not_issued_and_fallback_not_activated",
        },
    },
    "reiyah.rule.assumption-evidence-eligibility": {
        "kind": "rule",
        "executable_contract": {
            "contract_id": "reiyah.executable-contract.assumption-evidence-eligibility",
            "contract_kind": "assumption_evidence_eligibility",
            "version": SCIENCE_SCHEMA_VERSION,
            "derivation_authority": "offline_validator",
            "eligible_evidence_basis": "independently_retained_exact_references",
            "empty_evidence_policy": "assumption_unknown",
            "self_evidence_policy": "ineligible",
            "assumption_consumer_scope": "conformal_exchangeability_and_transfer_overlap_invariance",
        },
    },
}

EXECUTABLE_CONTRACTS_BY_SCHEMA = {
    HUMAN_SCHEMA_ID: (
        "reiyah.rule.readiness-unknown-propagation",
        "reiyah.rule.recovery-event-derivation",
        "reiyah.rule.human-belief-observation-decision-reconciliation",
    ),
    STUDY_SCHEMA_ID: ("reiyah.rule.causal-identification",),
    OPE_SCHEMA_ID: ("reiyah.rule.ope-policy-distribution",),
    JOINT_SCHEMA_ID: (
        "reiyah.rule.transfer-eligibility",
        "reiyah.rule.conformal-guarantee-disposition",
        "reiyah.rule.ood-population-partition",
        "reiyah.rule.worst-group-eligibility",
        "reiyah.rule.joint-silent-miss-identifiability",
        "reiyah.rule.assumption-evidence-eligibility",
    ),
}

EXECUTABLE_CONTRACT_DIAGNOSTICS = {
    "reiyah.rule.ope-policy-distribution": ("GA-OPE-ACTION-DISTRIBUTION", "/policy_bindings"),
    "reiyah.rule.causal-identification": ("GA-CAUSAL-IDENTIFICATION-DISPOSITION", "/identification_queries"),
    "reiyah.rule.readiness-unknown-propagation": ("GA-READINESS-UNKNOWN-PROPAGATION", "/readiness"),
    "reiyah.rule.recovery-event-derivation": ("GA-RECOVERY-EVENT-DERIVATION", "/recovery"),
    "reiyah.rule.transfer-eligibility": ("GA-TRANSFER-DISPOSITION", "/transfer_evaluation"),
    "reiyah.rule.conformal-guarantee-disposition": ("GA-CONFORMAL-GUARANTEE-ASSUMPTION", "/conformal_evaluation/guarantee"),
    "reiyah.rule.ood-population-partition": ("GA-OOD-DISJOINT-PARTITION", "/ood_evaluation"),
    "reiyah.rule.worst-group-eligibility": ("GA-WORST-GROUP-INFORMATION", "/worst_group_evaluation"),
    "reiyah.rule.human-belief-observation-decision-reconciliation": ("GA-HUMAN-INFORMATION-SET-RECONCILIATION", "/belief/information_set"),
    "reiyah.rule.joint-silent-miss-identifiability": ("GA-JOINT-COMMON-OPPORTUNITY-DERIVATION", "/joint_silent_miss"),
    "reiyah.rule.assumption-evidence-eligibility": ("GA-ASSUMPTION-EVIDENCE-ELIGIBILITY", "/transfer_evaluation/invariance/evidence_refs"),
}

SUPPORTED_RULE_IDS = frozenset(
    {
        "GA-ASSURANCE-NO-DEPLOYMENT",
        "GA-ASSURANCE-NONCLAIM",
        "GA-ASSURANCE-LICENSE-DISPOSITION",
        "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY",
        "GA-ASSUMPTION-SELF-EVIDENCE",
        "GA-ARTIFACT-REFERENCE-RESOLUTION",
        "GA-BELIEF-DISTRIBUTION-SUM",
        "GA-BELIEF-NORMALIZATION-POLICY-BINDING",
        "GA-BELIEF-STATE-SPACE-COVERAGE",
        "GA-CAUSAL-BACKDOOR-OPEN",
        "GA-CAUSAL-DAG-CYCLE",
        "GA-CAUSAL-ESTIMAND-BINDING",
        "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
        "GA-CAUSAL-PROHIBITED-ADJUSTMENT",
        "GA-CAUSAL-QUERY-ROLE",
        "GA-CAUSAL-SELECTED-SET-RECONCILIATION",
        "GA-CAUSAL-ANALYSIS-UNIT-SET-BINDING",
        "GA-CAUSAL-SPLIT-FREEZE",
        "GA-CAUSAL-SPLIT-MEMBERSHIP",
        "GA-CAUSAL-SPLIT-REFERENCE",
        "GA-CAUSAL-STRATIFICATION-INPUT",
        "GA-CAUSAL-TEMPORAL-ORDER",
        "GA-STUDY-DESIGN-CHRONOLOGY",
        "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
        "GA-EVIDENCE-GAP-REFERENCE-DISPOSITION",
        "GA-ESTIMAND-REFERENCE-BINDING",
        "GA-CONFORMAL-COVERAGE-DISPOSITION",
        "GA-CONFORMAL-EMPIRICAL-DERIVATION",
        "GA-CONFORMAL-GROUP-SCOPE",
        "GA-CONFORMAL-GUARANTEE-ASSUMPTION",
        "GA-CONFORMAL-TARGET",
        "GA-HUMAN-INFORMATION-SET-RECONCILIATION",
        "GA-HUMAN-OBJECT-RECONCILIATION",
        "GA-HUMAN-SUBJECT-RECONCILIATION",
        "GA-HUMAN-TEMPORAL-RECONCILIATION",
        "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
        "GA-JOINT-OPPORTUNITY-CHRONOLOGY",
        "GA-JOINT-OPPORTUNITY-MANIFEST-BINDING",
        "GA-JOINT-OPPORTUNITY-ROW-BINDING",
        "GA-JOINT-SILENT-ROW-DERIVATION",
        "GA-JOINT-SILENT-MISS-DERIVATION",
        "GA-JOINT-UNKNOWN-PROPAGATION",
        "GA-LIFECYCLE-CURRENT-HISTORY",
        "GA-LIFECYCLE-CHRONOLOGY",
        "GA-LIFECYCLE-EVIDENCE-ELIGIBILITY",
        "GA-OBSERVATION-VALIDITY-STATE",
        "GA-OOD-DERIVATION",
        "GA-OOD-DISJOINT-PARTITION",
        "GA-OOD-SELECTIVE-BINDING",
        "GA-OPE-ACTION-DISTRIBUTION",
        "GA-OPE-CUMULATIVE-WEIGHT",
        "GA-OPE-ESS-ALL-ZERO",
        "GA-OPE-ESS-CUMULATIVE",
        "GA-OPE-ESS-HORIZON-COVERAGE",
        "GA-OPE-ESTIMATOR-BINDING",
        "GA-OPE-ESTIMATOR-SELECTION-TIME",
        "GA-OPE-HISTORY-SUPPORT",
        "GA-OPE-HISTORY-INFORMATION-SET",
        "GA-OPE-LOGGED-PROPENSITY",
        "GA-OPE-STEP-HORIZON-COMPLETENESS",
        "GA-OPE-STEP-RATIO",
        "GA-OPE-TERMINAL-COMPLETENESS",
        "GA-OPE-TRAJECTORY-MANIFEST-BINDING",
        "GA-OPE-WEIGHT-NORMALIZATION",
        "GA-OPE-WEIGHT-TRANSFORMATION",
        "GA-OPE-POLICY-TABLE-BINDING",
        "GA-READINESS-AGGREGATION-MISMATCH",
        "GA-READINESS-CAPABILITY-MANIFEST-BINDING",
        "GA-READINESS-CAPABILITY-DIMENSION",
        "GA-READINESS-CRITERION-MISMATCH",
        "GA-READINESS-TEMPORAL-RECONCILIATION",
        "GA-READINESS-UNKNOWN-PROPAGATION",
        "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
        "GA-REFERENCE-KIND",
        "GA-REFERENCE-VERSION",
        "GA-SCHEMA-REFERENCE-RESOLUTION",
        "GA-ACTOR-REFERENCE-TYPE",
        "GA-RECOVERY-CENSORING-DISPOSITION",
        "GA-RECOVERY-COMPETING-EVENT",
        "GA-RECOVERY-EVENT-CLASSIFICATION",
        "GA-RECOVERY-EVENT-DERIVATION",
        "GA-RECOVERY-EVENT-MANIFEST-BINDING",
        "GA-RECOVERY-INPUT-UNKNOWN-PROPAGATION",
        "GA-RECOVERY-NO-EVENT-CENSORING",
        "GA-RECOVERY-WINDOW-MISMATCH",
        "GA-SELECTIVE-DERIVATION",
        "GA-SELECTIVE-PARTITION",
        "GA-TRANSFER-ADAPTATION-DISCLOSURE",
        "GA-TRANSFER-DISPOSITION",
        "GA-TRANSFER-DOMAIN-ROLE-BINDING",
        "GA-TRANSFER-COVERAGE",
        "GA-TRANSFER-GAP",
        "GA-TRANSFER-METRIC-CONTRACT",
        "GA-TRANSFER-TARGET-ACCESS",
        "GA-WORST-GROUP-COVERAGE",
        "GA-WORST-GROUP-DISPOSITION",
        "GA-WORST-GROUP-ELIGIBILITY",
        "GA-WORST-GROUP-INFORMATION",
        "GA-WORST-GROUP-TIE",
        "GA-WORST-GROUP-UNKNOWN",
    }
)

# Frozen production ordering for primary semantic diagnostics.  Secondary
# diagnostics are retained, but a fixture closes only when its complete
# declared tuple is first under this order.
RULE_PRIORITY_ORDER = (
    "GA-LIFECYCLE-CURRENT-HISTORY",
    "GA-LIFECYCLE-CHRONOLOGY",
    "GA-LIFECYCLE-EVIDENCE-ELIGIBILITY",
    "GA-ARTIFACT-REFERENCE-RESOLUTION",
    "GA-SCHEMA-REFERENCE-RESOLUTION",
    "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
    "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
    "GA-EVIDENCE-GAP-REFERENCE-DISPOSITION",
    "GA-ESTIMAND-REFERENCE-BINDING",
    "GA-ACTOR-REFERENCE-TYPE",
    "GA-REFERENCE-KIND",
    "GA-REFERENCE-VERSION",
    "GA-ASSURANCE-NO-DEPLOYMENT",
    "GA-ASSURANCE-NONCLAIM",
    "GA-ASSURANCE-LICENSE-DISPOSITION",
    "GA-BELIEF-NORMALIZATION-POLICY-BINDING",
    "GA-BELIEF-STATE-SPACE-COVERAGE",
    "GA-BELIEF-DISTRIBUTION-SUM",
    "GA-OBSERVATION-VALIDITY-STATE",
    "GA-HUMAN-OBJECT-RECONCILIATION",
    "GA-HUMAN-INFORMATION-SET-RECONCILIATION",
    "GA-HUMAN-SUBJECT-RECONCILIATION",
    "GA-HUMAN-TEMPORAL-RECONCILIATION",
    "GA-READINESS-CAPABILITY-DIMENSION",
    "GA-READINESS-CRITERION-MISMATCH",
    "GA-READINESS-TEMPORAL-RECONCILIATION",
    "GA-READINESS-UNKNOWN-PROPAGATION",
    "GA-READINESS-AGGREGATION-MISMATCH",
    "GA-READINESS-CAPABILITY-MANIFEST-BINDING",
    "GA-RECOVERY-WINDOW-MISMATCH",
    "GA-RECOVERY-INPUT-UNKNOWN-PROPAGATION",
    "GA-RECOVERY-CENSORING-DISPOSITION",
    "GA-RECOVERY-COMPETING-EVENT",
    "GA-RECOVERY-NO-EVENT-CENSORING",
    "GA-RECOVERY-EVENT-DERIVATION",
    "GA-RECOVERY-EVENT-CLASSIFICATION",
    "GA-RECOVERY-EVENT-MANIFEST-BINDING",
    "GA-CAUSAL-DAG-CYCLE",
    "GA-CAUSAL-TEMPORAL-ORDER",
    "GA-STUDY-DESIGN-CHRONOLOGY",
    "GA-CAUSAL-ANALYSIS-UNIT-SET-BINDING",
    "GA-CAUSAL-SPLIT-REFERENCE",
    "GA-CAUSAL-SPLIT-MEMBERSHIP",
    "GA-CAUSAL-SPLIT-FREEZE",
    "GA-CAUSAL-STRATIFICATION-INPUT",
    "GA-CAUSAL-QUERY-ROLE",
    "GA-CAUSAL-ESTIMAND-BINDING",
    "GA-CAUSAL-SELECTED-SET-RECONCILIATION",
    "GA-CAUSAL-PROHIBITED-ADJUSTMENT",
    "GA-CAUSAL-BACKDOOR-OPEN",
    "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
    "GA-OPE-STEP-HORIZON-COMPLETENESS",
    "GA-OPE-TERMINAL-COMPLETENESS",
    "GA-OPE-HISTORY-INFORMATION-SET",
    "GA-OPE-ACTION-DISTRIBUTION",
    "GA-OPE-LOGGED-PROPENSITY",
    "GA-OPE-STEP-RATIO",
    "GA-OPE-CUMULATIVE-WEIGHT",
    "GA-OPE-WEIGHT-TRANSFORMATION",
    "GA-OPE-HISTORY-SUPPORT",
    "GA-OPE-ESS-HORIZON-COVERAGE",
    "GA-OPE-ESS-ALL-ZERO",
    "GA-OPE-ESS-CUMULATIVE",
    "GA-OPE-WEIGHT-NORMALIZATION",
    "GA-OPE-ESTIMATOR-SELECTION-TIME",
    "GA-OPE-ESTIMATOR-BINDING",
    "GA-OPE-TRAJECTORY-MANIFEST-BINDING",
    "GA-OPE-POLICY-TABLE-BINDING",
    "GA-JOINT-OPPORTUNITY-ROW-BINDING",
    "GA-JOINT-OPPORTUNITY-CHRONOLOGY",
    "GA-JOINT-SILENT-ROW-DERIVATION",
    "GA-JOINT-UNKNOWN-PROPAGATION",
    "GA-JOINT-OPPORTUNITY-MANIFEST-BINDING",
    "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
    "GA-JOINT-SILENT-MISS-DERIVATION",
    "GA-SELECTIVE-PARTITION",
    "GA-SELECTIVE-DERIVATION",
    "GA-OOD-DISJOINT-PARTITION",
    "GA-OOD-DERIVATION",
    "GA-OOD-SELECTIVE-BINDING",
    "GA-ASSUMPTION-SELF-EVIDENCE",
    "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY",
    "GA-CONFORMAL-TARGET",
    "GA-CONFORMAL-GROUP-SCOPE",
    "GA-CONFORMAL-EMPIRICAL-DERIVATION",
    "GA-CONFORMAL-COVERAGE-DISPOSITION",
    "GA-CONFORMAL-GUARANTEE-ASSUMPTION",
    "GA-TRANSFER-DOMAIN-ROLE-BINDING",
    "GA-TRANSFER-METRIC-CONTRACT",
    "GA-TRANSFER-COVERAGE",
    "GA-TRANSFER-GAP",
    "GA-TRANSFER-TARGET-ACCESS",
    "GA-TRANSFER-ADAPTATION-DISCLOSURE",
    "GA-TRANSFER-DISPOSITION",
    "GA-WORST-GROUP-COVERAGE",
    "GA-WORST-GROUP-INFORMATION",
    "GA-WORST-GROUP-UNKNOWN",
    "GA-WORST-GROUP-DISPOSITION",
    "GA-WORST-GROUP-ELIGIBILITY",
    "GA-WORST-GROUP-TIE",
)
RULE_PRIORITY = {rule_id: index for index, rule_id in enumerate(RULE_PRIORITY_ORDER)}

CANONICAL_RULE_REASONS = {
    "GA-ACTOR-REFERENCE-TYPE": "An actor reference must resolve an actor definition whose actor_type and exact version match the reference.",
    "GA-ASSUMPTION-SELF-EVIDENCE": "An assumption assessment cannot establish itself or treat self-authored evidence as independent.",
    "GA-ARTIFACT-REFERENCE-RESOLUTION": "A lifecycle predecessor artifact must resolve exact non-self snapshot bytes, identity, kind, schema, logical record, and an older semantic version.",
    "GA-ASSURANCE-NO-DEPLOYMENT": "A Gate A static assurance bundle cannot authorize deployment.",
    "GA-ASSURANCE-NONCLAIM": "A Gate A assurance claim with only an evidence-gap binding must remain proposed and cannot be labeled supported.",
    "GA-ASSURANCE-LICENSE-DISPOSITION": "A synthetic-only Gate A assurance bundle must retain the exact synthetic-original license disposition and cannot claim verified retained permission.",
    "GA-BELIEF-DISTRIBUTION-SUM": "An observed belief distribution must sum to one within the exact record-bound protocol tolerance.",
    "GA-BELIEF-NORMALIZATION-POLICY-BINDING": "The belief normalization binding must exactly equal every protocol-owned normalization policy field.",
    "GA-BELIEF-STATE-SPACE-COVERAGE": "Belief probability rows must cover every declared state exactly once without duplicate or extraneous state identifiers.",
    "GA-CAUSAL-BACKDOOR-OPEN": "An identification query cannot be identified while a backdoor path remains open under its selected adjustment set.",
    "GA-CAUSAL-DAG-CYCLE": "The declared causal graph must be acyclic.",
    "GA-CAUSAL-ESTIMAND-BINDING": "Every identification query must resolve one declared estimand and exact-bind its treatment and outcome nodes.",
    "GA-CAUSAL-IDENTIFICATION-DISPOSITION": "A complete back-door query must report identified if and only if its eligible adjustment set d-separates treatment and outcome; complete open paths must report not_identified.",
    "GA-CAUSAL-SELECTED-SET-RECONCILIATION": "Selected adjustment-set identifiers must exactly equal the distinct non-null adjustment sets bound by identification queries.",
    "GA-CAUSAL-ANALYSIS-UNIT-SET-BINDING": "The study analysis unit, split unit, protocol-owned synthetic analysis-unit-set reference, and complete ordered member universe must exact-bind the executable causal contract.",
    "GA-CAUSAL-SPLIT-FREEZE": "Every retained split manifest must be frozen before first outcome access.",
    "GA-CAUSAL-SPLIT-MEMBERSHIP": "Train, calibration, and test member IDs must exact-bind the registry-owned manifest rows, remain unique and pairwise disjoint, and have an exact union equal to the bound analysis-unit universe.",
    "GA-CAUSAL-SPLIT-REFERENCE": "Train, calibration, and test manifests must exact-bind three distinct protocol-owned split identities in their declared roles.",
    "GA-CAUSAL-STRATIFICATION-INPUT": "Every stratification input must resolve a matching observed pre-treatment graph-node role, be available by its manifest freeze, and cannot be an outcome or post-treatment operand.",
    "GA-CAUSAL-TEMPORAL-ORDER": "Each directed edge must respect the declared temporal order.",
    "GA-STUDY-DESIGN-CHRONOLOGY": "The root and nested design freezes must be identical, precede feature and outcome access, and bound every adjustment-set freeze.",
    "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION": "A document-local identifier must resolve exactly once in its explicitly owned collection and may not be inferred by naming convention.",
    "GA-EVIDENCE-GAP-REFERENCE-DISPOSITION": "An explicit evidence gap must remain unavailable and non-supporting, retain no evidence references, and state a substantive reason.",
    "GA-ESTIMAND-REFERENCE-BINDING": "Each estimand reference must exact-bind the protocol-owned estimand assigned to its application section by the scientific contract profile.",
    "GA-CONFORMAL-COVERAGE-DISPOSITION": "Each observed group coverage disposition must be derived from empirical coverage and the declared target.",
    "GA-CONFORMAL-EMPIRICAL-DERIVATION": "Empirical conformal coverage must equal covered count divided by evaluated count, with zero or nonobserved denominators propagating explicit unknown.",
    "GA-CONFORMAL-GROUP-SCOPE": "Conformal group results must cover the declared group universe exactly without omission or addition.",
    "GA-CONFORMAL-GUARANTEE-ASSUMPTION": "A finite-sample conformal guarantee cannot be asserted when exchangeability is unmeasured.",
    "GA-CONFORMAL-TARGET": "The declared conformal target coverage must equal one minus alpha.",
    "GA-HUMAN-INFORMATION-SET-RECONCILIATION": "The frozen decision information set must contain exact typed references to both the observation and the belief.",
    "GA-HUMAN-OBJECT-RECONCILIATION": "Observation, belief, and decision must bind the same exact object reference.",
    "GA-HUMAN-SUBJECT-RECONCILIATION": "Belief holder, decision actor, and readiness subject must exact-bind one assessed human identity, type, and version.",
    "GA-HUMAN-TEMPORAL-RECONCILIATION": "Observation event, measurement, availability, belief freeze, decision information freeze, and decision time must respect the declared epistemic chronology.",
    "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION": "Joint silent-miss marginals and intersection must derive from one disjoint common-opportunity contingency partition.",
    "GA-JOINT-OPPORTUNITY-CHRONOLOGY": "Every synthetic opportunity time must be observed inside the exact common clock and window, and ordered member rows must not move across that frozen interval.",
    "GA-JOINT-OPPORTUNITY-MANIFEST-BINDING": "The complete ordered opportunity identities and typed rows must exact-bind one artifact-bound protocol-owned synthetic manifest; it is static resolver evidence, not a real population.",
    "GA-JOINT-OPPORTUNITY-ROW-BINDING": "Every opportunity row must exact-bind the common object, clock, window, reference operands, role-typed human and automation channels, and warning and fallback rules.",
    "GA-JOINT-SILENT-ROW-DERIVATION": "A joint silent miss requires both channels to miss while warning is not issued and fallback is not activated; nonobserved row operands must propagate to the affected cell and summary.",
    "GA-JOINT-SILENT-MISS-DERIVATION": "Observed joint-miss risk must equal joint misses divided by declared opportunities, and joint misses cannot exceed either marginal miss count.",
    "GA-JOINT-UNKNOWN-PROPAGATION": "A nonobserved common-opportunity operand must force nonidentifiable status and nonobserved derived summaries.",
    "GA-LIFECYCLE-CURRENT-HISTORY": "Current lifecycle status must equal the terminal ordered lifecycle event and may not be changed without an appended event.",
    "GA-LIFECYCLE-CHRONOLOGY": "A record's created_at must equal the first lifecycle event time, and every appended lifecycle event must be strictly later while immutable successors preserve the original creation time.",
    "GA-LIFECYCLE-EVIDENCE-ELIGIBILITY": "A lifecycle status requiring scientific evidence or experiment binding cannot be asserted from Gate A evidence gaps and unresolved scientific dependencies.",
    "GA-OBSERVATION-VALIDITY-STATE": "Observation validity must be valid exactly for an observed value and otherwise equal the value epistemic state.",
    "GA-OOD-DISJOINT-PARTITION": "The nine disjoint reference-by-detector cells must exhaust the OOD population exactly once.",
    "GA-OOD-SELECTIVE-BINDING": "The selective OOD count and reference OOD count must reconcile over the same declared population.",
    "GA-OPE-ACTION-DISTRIBUTION": "Every policy distribution must cover the exact action space once and sum to one.",
    "GA-OPE-CUMULATIVE-WEIGHT": "A horizon weight must be the product of all history-local step ratios through that horizon.",
    "GA-OPE-ESS-ALL-ZERO": "All-zero cumulative weights make Kish ESS undefined and must not retain an observed ESS or ordinary sufficiency disposition.",
    "GA-OPE-ESS-CUMULATIVE": "Horizon ESS must use cumulative trajectory weights, not per-step ratios or a trusted scalar.",
    "GA-OPE-ESS-HORIZON-COVERAGE": "ESS rows must cover every horizon index from zero through maximum_steps minus one exactly once.",
    "GA-OPE-ESTIMATOR-BINDING": "Every estimator must bind the exact declared cumulative weight set and evaluated horizon.",
    "GA-OPE-ESTIMATOR-SELECTION-TIME": "Estimator selection must be frozen before first outcome access.",
    "GA-OPE-HISTORY-SUPPORT": "Every history-action cell with positive target probability must have positive behavior support; the assessment cannot remain supported otherwise.",
    "GA-OPE-HISTORY-INFORMATION-SET": "Every trajectory, history, and information-set identity must be unique, and each frozen information set must exact-bind the policy schema and the complete ordered prior-action history before outcome access.",
    "GA-OPE-LOGGED-PROPENSITY": "The logged behavior propensity must equal the probability assigned to the logged action in the full behavior distribution.",
    "GA-OPE-POLICY-TABLE-BINDING": "Every behavior and target distribution must exact-bind the artifact-bound protocol-owned synthetic policy table selected for its role and history; the table is static resolver evidence, not an executed policy.",
    "GA-OPE-STEP-RATIO": "Each step ratio must equal target logged propensity divided by behavior logged propensity.",
    "GA-OPE-TRAJECTORY-MANIFEST-BINDING": "The retained trajectory identities must exact-bind the complete ordered artifact-bound protocol-owned synthetic trajectory manifest; the manifest is static resolver evidence, not a real dataset population.",
    "GA-OPE-WEIGHT-NORMALIZATION": "Every ESS horizon row must reconcile its normalization mode, denominator, and resulting weight sum with the declared construction.",
    "GA-OPE-WEIGHT-TRANSFORMATION": "Upper clipping requires each transformed cumulative weight to equal min(raw cumulative weight, threshold).",
    "GA-READINESS-AGGREGATION-MISMATCH": "The observed aggregate must equal the declared normalized weighted construction from observed capability estimates.",
    "GA-READINESS-CAPABILITY-MANIFEST-BINDING": "The application capability rows must exact-bind the protocol-owned synthetic capability manifest selected for this artifact; the manifest is static resolver evidence, not a real capability inventory.",
    "GA-READINESS-CAPABILITY-DIMENSION": "Each required readiness dimension must have one unambiguous capability binding in this contract.",
    "GA-READINESS-CRITERION-MISMATCH": "An observed capability disposition must be derived from its declared operator, threshold, and estimate.",
    "GA-READINESS-TEMPORAL-RECONCILIATION": "Observed readiness time must lie inside its ordered window and follow every observation, belief, and decision input available to the assessment.",
    "GA-READINESS-UNKNOWN-PROPAGATION": "Any required or positively weighted unresolved capability must appear in the unresolved set and force a nonobserved aggregate with unknown disposition.",
    "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION": "A registry-owned scalar identifier must resolve exactly once to the required definition kind, version, and owning protocol release.",
    "GA-RECOVERY-CENSORING-DISPOSITION": "A censoring event cannot support a recovered disposition.",
    "GA-RECOVERY-COMPETING-EVENT": "A competing event must propagate the competing-event disposition rather than recovery.",
    "GA-RECOVERY-EVENT-CLASSIFICATION": "Recovery, censoring, and competing-event policy identities and each synthetic event type-to-role classification must exact-bind the executable recovery contract.",
    "GA-RECOVERY-EVENT-MANIFEST-BINDING": "The application recovery-event rows and completeness boundary must exact-bind the protocol-owned synthetic event manifest selected for this artifact; the manifest is static resolver evidence, not a real event log.",
    "GA-RECOVERY-NO-EVENT-CENSORING": "A complete observed window with no qualifying event must be right censored, bind an explicit absent event, and use close minus index elapsed time.",
    "GA-RECOVERY-WINDOW-MISMATCH": "A qualifying recovery event must occur within the declared recovery window.",
    "GA-REFERENCE-VERSION": "A protocol-owned versioned reference must exactly match the resolved definition version.",
    "GA-SCHEMA-REFERENCE-RESOLUTION": "A schema reference must resolve the exact local schema identifier and version in the immutable repository snapshot.",
    "GA-SELECTIVE-DERIVATION": "Accepted error risk and coverage must be derived from the declared accepted and population counts.",
    "GA-SELECTIVE-PARTITION": "Selective accepted, ambiguous, and every explicit non-observed count must partition the population exactly.",
    "GA-TRANSFER-ADAPTATION-DISCLOSURE": "Target tuning requires a non-none adaptation mode, an exact procedure binding, and truthful target-label disclosure.",
    "GA-TRANSFER-COVERAGE": "Transfer coverage must reconcile exactly, and observed estimates or uncertainty operands require the registry-owned minimum observed count.",
    "GA-TRANSFER-DISPOSITION": "Transfer disposition must be unknown for unresolved operands and not_identified only for complete operands proving a non-applicable eligibility condition.",
    "GA-TRANSFER-DOMAIN-ROLE-BINDING": "Transfer source and target results must exact-bind the distinct protocol-owned synthetic domain identities assigned to their roles.",
    "GA-TRANSFER-GAP": "An observed transfer gap must equal target estimate minus source estimate under the exact shared metric contract.",
    "GA-TRANSFER-METRIC-CONTRACT": "Source and target results must bind the exact same metric, estimator, population, outcome window, unit, direction, and version contract.",
    "GA-TRANSFER-TARGET-ACCESS": "The transfer analysis contract must be frozen before any target-domain data access.",
    "GA-WORST-GROUP-COVERAGE": "Each group's coverage states must reconcile to its sample count and total.",
    "GA-WORST-GROUP-DISPOSITION": "Worst-group disposition must be identified for a resolved nonempty eligible set, no_eligible_groups for a resolved empty eligible set, and unknown for any unresolved required operand.",
    "GA-WORST-GROUP-ELIGIBILITY": "Eligible group IDs must equal exactly the observed groups satisfying the executable minimum-information rule.",
    "GA-WORST-GROUP-INFORMATION": "Group information disposition must be computed from all executable minimum-information thresholds.",
    "GA-WORST-GROUP-TIE": "All eligible groups tied at the observed extremum must be reported.",
    "GA-WORST-GROUP-UNKNOWN": "Unresolved group membership must not coexist with observed performance, eligibility, or a confident worst-group extremum.",
}


class ScienceContractError(Exception):
    pass


def close(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return False
    if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
        return False
    # Count/cardinality operands are exact.  Continuous derived quantities use
    # the Gate A absolute-error contract only; a relative tolerance would make
    # an off-by-one error pass at sufficiently large magnitude.
    if isinstance(left, int) and isinstance(right, int):
        return left == right
    left_value = float(left)
    right_value = float(right)
    return (
        math.isfinite(left_value)
        and math.isfinite(right_value)
        and abs(left_value - right_value) <= TOLERANCE
    )


def absolute_close(left: object, right: object, tolerance: object) -> bool:
    if (
        isinstance(left, bool)
        or isinstance(right, bool)
        or isinstance(tolerance, bool)
        or not isinstance(left, (int, float))
        or not isinstance(right, (int, float))
        or not isinstance(tolerance, (int, float))
    ):
        return False
    left_value = float(left)
    right_value = float(right)
    tolerance_value = float(tolerance)
    return (
        math.isfinite(left_value)
        and math.isfinite(right_value)
        and math.isfinite(tolerance_value)
        and tolerance_value >= 0
        and abs(left_value - right_value) <= tolerance_value
    )


def observed(measurement: object) -> object | None:
    if isinstance(measurement, dict) and measurement.get("state") == "observed":
        return measurement.get("value")
    return None


def executable_contract(
    registry: Mapping[str, Any], contract_id: str
) -> Mapping[str, Any]:
    matches = [
        item.get("executable_contract")
        for item in registry.get("definitions", [])
        if isinstance(item, Mapping)
        and isinstance(item.get("executable_contract"), Mapping)
        and item["executable_contract"].get("contract_id") == contract_id
    ]
    if len(matches) != 1:
        raise ScienceContractError(
            f"executable contract must resolve exactly once: {contract_id}"
        )
    return matches[0]


def executable_contract_binding_violations(
    schema_id: object, registry: Mapping[str, Any]
) -> list[dict[str, str]]:
    """Reject any drift in an application handler's complete contract closure.

    The comparison intentionally happens in the production semantic path as
    well as at the registry-schema boundary.  Direct callers therefore cannot
    bypass operand ownership by handing a schema-invalid or swapped registry to
    ``semantic_violations``.
    """
    definitions_by_id: dict[str, list[Mapping[str, Any]]] = {}
    for item in registry.get("definitions", []):
        if isinstance(item, Mapping) and isinstance(item.get("definition_id"), str):
            definitions_by_id.setdefault(item["definition_id"], []).append(item)
    output: list[dict[str, str]] = []
    for definition_id in EXECUTABLE_CONTRACTS_BY_SCHEMA.get(schema_id, ()):
        matches = definitions_by_id.get(definition_id, [])
        expected = FROZEN_EXECUTABLE_CONTRACT_DEFINITIONS[definition_id]
        valid = (
            len(matches) == 1
            and matches[0].get("kind") == expected["kind"]
            and matches[0].get("version") == SCIENCE_SCHEMA_VERSION
            and matches[0].get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
            and matches[0].get("executable_contract")
            == expected["executable_contract"]
        )
        rule_id, pointer = EXECUTABLE_CONTRACT_DIAGNOSTICS[definition_id]
        add_if(
            output,
            not valid,
            rule_id,
            pointer,
            "The complete versioned executable-contract definition and every normative operand must exact-bind the frozen offline production handler.",
        )
    return output


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith(("Z", "z")) else value)


def exact_elapsed_seconds(start: datetime, end: datetime) -> Decimal:
    delta = end - start
    return (
        Decimal(delta.days * 86400 + delta.seconds)
        + Decimal(delta.microseconds) / Decimal(1_000_000)
    )


def exact_decimal_equal(value: object, expected: Decimal) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return Decimal(str(value)) == expected
    except InvalidOperation:
        return False


def violation(rule_id: str, pointer: str, reason: str) -> dict[str, str]:
    return {"rule_id": rule_id, "instance_pointer": pointer, "reason": reason}


def add_if(
    output: list[dict[str, str]],
    condition: bool,
    rule_id: str,
    pointer: str,
    reason: str,
) -> None:
    if condition:
        output.append(violation(rule_id, pointer, reason))


def canonicalize_violation(
    instance: Mapping[str, Any], item: Mapping[str, str]
) -> dict[str, str]:
    rule_id = item["rule_id"]
    pointer = item["instance_pointer"]
    reason = CANONICAL_RULE_REASONS.get(rule_id)
    if rule_id == "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY":
        tokens = decode_pointer(pointer)
        section: object = instance
        try:
            for token in tokens[:-1] if tokens and tokens[-1] == "evidence_refs" else tokens:
                section = section[int(token)] if isinstance(section, list) else section[token]
        except (IndexError, KeyError, TypeError, ValueError):
            section = {}
        evidence = section.get("evidence_refs", []) if isinstance(section, Mapping) else []
        if pointer.startswith("/transfer_evaluation/") and not evidence:
            reason = "Empty evidence arrays cannot establish overlap or invariance or admit a comparable transfer disposition."
        elif evidence:
            reason = "Gate A 1.2 cannot establish or contradict a scientific assumption from inline evidence because no independently retained evidence resolver exists."
        else:
            reason = "An established assumption requires at least one exact eligible, independent, scope-matched, retained evidence binding that supports establishment."
    elif rule_id == "GA-CAUSAL-PROHIBITED-ADJUSTMENT":
        reason = "Mediator, post-treatment, collider, selection, treatment, and outcome nodes are prohibited adjustment variables."
        try:
            tokens = decode_pointer(pointer)
            set_index = int(tokens[1])
            node_index = int(tokens[3])
            node_id = instance["adjustment_sets"][set_index]["node_ids"][node_index]
            node = next(
                candidate
                for candidate in instance["causal_graph"]["nodes"]
                if candidate["node_id"] == node_id
            )
            if node["observability"] != "observed":
                reason = "An unmeasured node cannot be claimed as an applied adjustment variable."
            elif node["role"] == "collider":
                reason = "Conditioning on the declared collider opens a noncausal path and is prohibited."
        except (IndexError, KeyError, StopIteration, TypeError, ValueError):
            pass
    elif rule_id == "GA-CAUSAL-QUERY-ROLE":
        if pointer == "/causal_graph/nodes":
            reason = "The causal graph must declare exactly one treatment-role node and one outcome-role node."
        else:
            reason = (
                "A query treatment identifier must resolve to the graph's unique treatment-role node."
                if pointer.endswith("/treatment_node_id")
                else "A query outcome identifier must resolve to the graph's unique outcome-role node."
            )
    elif rule_id == "GA-CONFORMAL-GROUP-SCOPE" and pointer.endswith("/group_set_ref"):
        reason = "Conformal calibration and test refs must be distinct, and the declared group universe must exact-bind the registry-owned group set."
    elif rule_id == "GA-OOD-DERIVATION":
        if pointer.endswith("/detected_ood_count/value"):
            reason = "Detected OOD count must equal true positives plus false positives."
        elif pointer.endswith("/reference_unknown_count/value"):
            reason = "Reference-unknown and detector-unknown marginals must each derive from the corresponding rows and columns of the disjoint joint-state cells."
        else:
            reason = "OOD rates and declared OOD counts must be derived from the confusion matrix with explicit unknown exclusions."
    elif rule_id == "GA-OPE-STEP-HORIZON-COMPLETENESS":
        if pointer == "/horizon/maximum_steps":
            reason = "No observed trajectory may contain more steps than the declared maximum horizon."
        elif pointer.endswith("/observed_horizon"):
            reason = "Observed horizon must equal the exact number of contiguous recorded steps."
        else:
            reason = "Step indices must be the contiguous zero-based sequence through the observed trajectory horizon."
    elif rule_id == "GA-OPE-TERMINAL-COMPLETENESS":
        reason = "A terminal-event trajectory must end in a terminal step; a nonterminal final step is valid only with maximum-horizon truncation at the exact maximum."
        try:
            tokens = decode_pointer(pointer)
            trajectory_index = int(tokens[1])
            step_index = int(tokens[3])
            if step_index < len(instance["trajectories"][trajectory_index]["steps"]) - 1:
                reason = "No step before the final recorded step may be terminal."
        except (IndexError, KeyError, TypeError, ValueError):
            pass
    elif rule_id == "GA-RECOVERY-EVENT-DERIVATION":
        if pointer == "/recovery/outcome":
            reason = "An earliest cross-role event tie must propagate an invalid outcome with the exact ambiguous-event-tie absent reason."
        else:
            reason = (
                "Elapsed recovery time must equal the qualifying event time minus the index event time on the declared clock."
                if pointer.endswith("/elapsed_seconds/value")
                else "The outcome must bind the earliest qualifying recovery event inside the frozen window."
            )
    elif rule_id == "GA-RECOVERY-INPUT-UNKNOWN-PROPAGATION":
        if any(
            event.get("role") in {"recovery", "censoring", "competing"}
            and observed(event.get("occurred_at")) is None
            for event in instance["recovery"]["events"]
        ):
            reason = "A qualifying event with nonobserved time makes event selection unresolved and must force a nonobserved outcome."
        else:
            reason = (
                "An incompletely observed recovery window cannot retain a confident recovered, censored, or competing-event outcome."
                if observed(instance["recovery"]["window_observation_complete"]) is False
                else "A nonobserved recovery index or window input must force a nonobserved outcome, absent event binding, and nonobserved elapsed time."
            )
    elif rule_id == "GA-RECOVERY-WINDOW-MISMATCH" and pointer == "/recovery/outcome":
        reason = "An invalid observed recovery window must propagate an invalid outcome with the exact invalid-window absent reason."
    elif rule_id == "GA-REFERENCE-KIND":
        reason = (
            "A rule reference kind must resolve through its exact registry kind contract to a compatible definition kind."
            if pointer.endswith("/rule_kind")
            else "A versioned reference kind must have a registry contract compatible with the resolved definition and exact record_identity record_kind."
        )
    return {
        "rule_id": rule_id,
        "instance_pointer": pointer,
        "reason": reason if reason is not None else item["reason"],
    }


def decode_pointer(pointer: str) -> list[str]:
    if not pointer.startswith("/"):
        raise ScienceContractError(f"mutation pointer must be non-root: {pointer!r}")
    output: list[str] = []
    for token in pointer[1:].split("/"):
        index = 0
        decoded = ""
        while index < len(token):
            if token[index] != "~":
                decoded += token[index]
                index += 1
                continue
            if index + 1 >= len(token) or token[index + 1] not in {"0", "1"}:
                raise ScienceContractError(f"invalid JSON Pointer escape: {pointer!r}")
            decoded += "~" if token[index + 1] == "0" else "/"
            index += 2
        output.append(decoded)
    return output


def apply_mutations(base: Any, mutations: Sequence[Mapping[str, Any]]) -> Any:
    result = copy.deepcopy(base)
    for mutation in mutations:
        operation = mutation["operation"]
        tokens = decode_pointer(mutation["json_pointer"])
        parent = result
        for token in tokens[:-1]:
            if isinstance(parent, list):
                if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                    raise ScienceContractError(f"invalid list index {token!r}")
                index = int(token)
                if index >= len(parent):
                    raise ScienceContractError(f"list index outside base fixture: {index}")
                parent = parent[index]
            elif isinstance(parent, dict) and token in parent:
                parent = parent[token]
            else:
                raise ScienceContractError(f"mutation parent is absent at {mutation['json_pointer']}")
        token = tokens[-1]
        if isinstance(parent, list):
            if operation == "add" and token == "-":
                parent.append(copy.deepcopy(mutation["value"]))
                continue
            if not token.isdigit() or (len(token) > 1 and token.startswith("0")):
                raise ScienceContractError(f"invalid list index {token!r}")
            index = int(token)
            if operation == "add":
                if index > len(parent):
                    raise ScienceContractError(f"add index outside list: {index}")
                parent.insert(index, copy.deepcopy(mutation["value"]))
            elif operation == "replace":
                if index >= len(parent):
                    raise ScienceContractError(f"replace index outside list: {index}")
                parent[index] = copy.deepcopy(mutation["value"])
            elif operation == "remove":
                if index >= len(parent):
                    raise ScienceContractError(f"remove index outside list: {index}")
                del parent[index]
            else:
                raise ScienceContractError(f"unsupported mutation operation: {operation}")
        elif isinstance(parent, dict):
            if operation == "add":
                parent[token] = copy.deepcopy(mutation["value"])
            elif operation == "replace":
                if token not in parent:
                    raise ScienceContractError(f"replace property is absent: {token}")
                parent[token] = copy.deepcopy(mutation["value"])
            elif operation == "remove":
                if token not in parent:
                    raise ScienceContractError(f"remove property is absent: {token}")
                del parent[token]
            else:
                raise ScienceContractError(f"unsupported mutation operation: {operation}")
        else:
            raise ScienceContractError(f"mutation target parent is scalar: {mutation['json_pointer']}")
    return result


def lifecycle_violations(instance: Mapping[str, Any]) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    history = instance.get("lifecycle_history", [])
    if isinstance(history, list) and history:
        ordered = sorted(history, key=lambda event: event.get("sequence", -1))
        terminal = ordered[-1].get("status")
        sequences = [event.get("sequence") for event in ordered]
        timestamps = [
            parse_time(event["recorded_at"])
            for event in ordered
            if isinstance(event.get("recorded_at"), str)
        ]
        prior_statuses_valid = all(
            event.get("prior_status") in ({None} if index == 0 else {ordered[index - 1].get("status")})
            for index, event in enumerate(ordered)
        )
        invalid = (
            instance.get("lifecycle_status") != terminal
            or sequences != list(range(1, len(sequences) + 1))
            or len({event.get("event_id") for event in ordered}) != len(ordered)
            or len(timestamps) != len(ordered)
            or any(left >= right for left, right in zip(timestamps, timestamps[1:]))
            or not prior_statuses_valid
        )
        add_if(
            output,
            invalid,
            "GA-LIFECYCLE-CURRENT-HISTORY",
            "/lifecycle_status",
            "current lifecycle status and ordered append-only history do not reconcile",
        )
        created_at = instance.get("created_at")
        first_recorded_at = ordered[0].get("recorded_at")
        add_if(
            output,
            not isinstance(created_at, str)
            or not isinstance(first_recorded_at, str)
            or created_at != first_recorded_at,
            "GA-LIFECYCLE-CHRONOLOGY",
            "/created_at",
            "created_at must exact-bind logical record inception at the first lifecycle event",
        )
    return output


def parse_semver(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value)
    return tuple(int(match[index]) for index in range(1, 4)) if match else None


LOGICAL_RECORD_ID_FIELDS = {
    ASSURANCE_SCHEMA_ID: "bundle_id",
    HUMAN_SCHEMA_ID: "assessment_id",
    JOINT_SCHEMA_ID: "evaluation_id",
    OPE_SCHEMA_ID: "evaluation_id",
    STUDY_SCHEMA_ID: "study_id",
}


def lifecycle_policy_violations(
    instance: Mapping[str, Any],
    policy: Mapping[str, Any],
    resolution_context: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    """Apply only the exact lifecycle status/transition authority in the protocol."""
    output: list[dict[str, str]] = []
    record_kind = instance.get("record_kind")
    scopes = {
        scope.get("record_kind"): set(scope.get("allowed_statuses", []))
        for scope in policy.get("entity_scopes", [])
        if isinstance(scope, Mapping)
    }
    allowed_statuses = scopes.get(record_kind)
    history = instance.get("lifecycle_history", [])
    invalid = not isinstance(allowed_statuses, set) or not isinstance(history, list) or not history
    if not invalid:
        invalid = history[0].get("status") != policy.get("initial_status")
    if not invalid:
        invalid = any(event.get("status") not in allowed_statuses for event in history)
    allowed_transitions = {
        (transition.get("from_status"), transition.get("to_status"))
        for transition in policy.get("transitions", [])
        if isinstance(transition, Mapping)
        and record_kind in transition.get("entity_kinds", [])
    }
    correction = policy.get("correction_retraction_rule", {})
    eligible_prior = set(correction.get("eligible_prior_statuses", []))
    correction_status = correction.get("correction_status")
    retraction_status = correction.get("retraction_status")
    inventory = (
        resolution_context.get("artifact_inventory", {})
        if isinstance(resolution_context, Mapping)
        else {}
    )
    instance_path = (
        resolution_context.get("instance_path")
        if isinstance(resolution_context, Mapping)
        else None
    )
    logical_field = LOGICAL_RECORD_ID_FIELDS.get(instance.get("schema_id"))
    current_version = parse_semver(instance.get("version"))
    for event_index, (previous, current) in enumerate(zip(history, history[1:]), start=1):
        pair = (previous.get("status"), current.get("status"))
        transition_valid = pair in allowed_transitions or (
            pair[0] in eligible_prior
            and pair[1] in {correction_status, retraction_status}
        )
        if not transition_valid:
            invalid = True
        reference = current.get("prior_artifact")
        target = (
            inventory.get(reference.get("path"))
            if isinstance(reference, Mapping) and isinstance(inventory, Mapping)
            else None
        )
        target_version = parse_semver(target.get("version")) if isinstance(target, Mapping) else None
        reference_valid = (
            isinstance(reference, Mapping)
            and isinstance(target, Mapping)
            and isinstance(instance_path, str)
            and reference.get("path") != instance_path
            and reference.get("artifact_id") != instance.get("artifact_id")
            and reference.get("artifact_id") == target.get("artifact_id")
            and reference.get("artifact_kind") == target.get("artifact_kind")
            and reference.get("version") == target.get("version")
            and reference.get("sha256") == target.get("sha256")
            and reference.get("byte_size") == target.get("byte_size")
            and target.get("schema_id") == instance.get("schema_id")
            and target.get("record_kind") == record_kind
            and target.get("lifecycle_status") == previous.get("status")
            and target.get("lifecycle_history") == history[:event_index]
            and target.get("created_at") == instance.get("created_at")
            and logical_field is not None
            and target.get("logical_record_id") == instance.get(logical_field)
            and target_version is not None
            and current_version is not None
            and current_version > target_version
        )
        add_if(
            output,
            not reference_valid,
            "GA-ARTIFACT-REFERENCE-RESOLUTION",
            f"/lifecycle_history/{event_index}/prior_artifact/path",
            "lifecycle predecessor reference does not resolve exact compatible older non-self snapshot bytes",
        )
    if history and history[0].get("prior_artifact") is not None:
        output.append(
            violation(
                "GA-ARTIFACT-REFERENCE-RESOLUTION",
                "/lifecycle_history/0/prior_artifact",
                "the initial proposed event cannot reference a predecessor artifact",
            )
        )
    if any(
        event.get("status") == retraction_status
        for event in history[:-1]
    ):
        invalid = True
    add_if(
        output,
        invalid,
        "GA-LIFECYCLE-CURRENT-HISTORY",
        "/lifecycle_history",
        "lifecycle history must follow the protocol's exact kind-specific status and transition policy",
    )
    return output


def lifecycle_evidence_violations(
    instance: Mapping[str, Any], protocol: Mapping[str, Any]
) -> list[dict[str, str]]:
    """Keep lifecycle status effects behind the protocol's unavailable evidence resolvers."""
    evidence_policy = protocol.get("evidence_binding_policy", {})
    result_policy = protocol.get("result_binding_policy", {})
    dependency_policy = protocol.get("scientific_dependency_policy", {})
    expected_headers = (
        (
            evidence_policy,
            "reiyah.evidence-binding-policy.harbor-gate-a",
        ),
        (
            result_policy,
            "reiyah.result-binding-policy.harbor-gate-a",
        ),
        (
            dependency_policy,
            "reiyah.scientific-dependency-policy.harbor-gate-a",
        ),
    )
    if any(
        not isinstance(policy, Mapping)
        or policy.get("policy_id") != policy_id
        or policy.get("version") != SCIENCE_SCHEMA_VERSION
        or policy.get("protocol_release_id") != PROTOCOL_RELEASE_ID
        or policy.get("runtime_execution_authorized") is not False
        for policy, policy_id in expected_headers
    ):
        raise ScienceContractError(
            "lifecycle evidence/result/dependency policies are not exact Gate A 1.2 operands"
        )
    if (
        dependency_policy.get("global_acyclicity_required") is not True
        or not isinstance(dependency_policy.get("record_kind_rules"), list)
    ):
        raise ScienceContractError(
            "scientific dependency policy does not retain its fail-closed static boundary"
        )
    evidence_required = set(evidence_policy.get("terminal_consumer_statuses", []))
    result_required = set(result_policy.get("scientific_disposition_result_statuses", [])) | set(
        result_policy.get("metric_derived_result_statuses", [])
    )
    status = instance.get("lifecycle_status")
    requires_unavailable_binding = status in evidence_required or (
        instance.get("record_kind") == "result" and status in result_required
    )
    evidence_binding = instance.get("evidence_binding")
    only_gap = (
        isinstance(evidence_binding, Mapping)
        and evidence_binding.get("state") == "evidence_gap"
        and evidence_binding.get("evidence_refs") == []
    )
    event_refs = [
        reference
        for event in instance.get("lifecycle_history", [])
        if isinstance(event, Mapping)
        for reference in event.get("evidence_refs", [])
    ]
    if requires_unavailable_binding:
        # Even a non-empty inline event reference is not eligible evidence in
        # 1.2: no exact retained-evidence or experiment-head resolver exists.
        return [
            violation(
                "GA-LIFECYCLE-EVIDENCE-ELIGIBILITY",
                "/lifecycle_status",
                "the asserted lifecycle status requires evidence or result bindings unavailable to Gate A 1.2",
            )
        ]
    if not only_gap or event_refs:
        # Nonterminal candidate states retain a closed evidence-gap boundary.
        return [
            violation(
                "GA-LIFECYCLE-EVIDENCE-ELIGIBILITY",
                "/evidence_binding",
                "a Gate A application record cannot introduce inline scientific evidence or dependency authority",
            )
        ]
    return []


def typed_reference_violations(
    instance: Mapping[str, Any], registry: Mapping[str, Any]
) -> list[dict[str, str]]:
    """Resolve every typed reference through the registry's exact contracts."""
    output: list[dict[str, str]] = []
    definitions = {
        item.get("definition_id"): item
        for item in registry.get("definitions", [])
        if isinstance(item, Mapping) and isinstance(item.get("definition_id"), str)
    }
    contracts = {
        item.get("reference_kind_id"): item
        for item in registry.get("reference_kind_contracts", [])
        if isinstance(item, Mapping) and isinstance(item.get("reference_kind_id"), str)
    }
    actor_contract = registry.get("actor_reference_contract", {})

    def pointer_token(value: object) -> str:
        return str(value).replace("~", "~0").replace("/", "~1")

    def visit(value: object, pointer: str) -> None:
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}/{index}")
            return
        if not isinstance(value, Mapping):
            return
        if "/evidence_refs/" in pointer and pointer.endswith("/evidence_ref"):
            # Gate A 1.2 has no retained scientific-assumption evidence resolver.
            # The containing assumption contract rejects these inline operands;
            # treating their self-declared kind as resolvable would invert that
            # evidence boundary and obscure the primary assumption diagnostic.
            return
        keys = set(value)
        if {"rule_id", "rule_kind", "version"}.issubset(keys):
            reference_kind = value["rule_kind"]
            contract = contracts.get(reference_kind)
            definition = definitions.get(value["rule_id"])
            incompatible = (
                contract is None
                or contract.get("reference_shape") != "rule_reference"
                or definition is None
                or definition.get("kind") not in set(contract.get("compatible_definition_kinds", []))
                or (
                    definition.get("kind") == "record_identity"
                    and contract.get("record_identity_requires_exact_record_kind") is True
                    and definition.get("record_kind") != reference_kind
                )
            )
            add_if(
                output,
                incompatible,
                "GA-REFERENCE-KIND",
                f"{pointer}/rule_kind",
                "rule reference kind and resolved definition kind must satisfy the exact registry contract",
            )
            add_if(
                output,
                contract is not None
                and definition is not None
                and contract.get("version_must_match") is True
                and value["version"] != definition.get("version"),
                "GA-REFERENCE-VERSION",
                f"{pointer}/version",
                "rule reference version must equal the resolved definition version",
            )
        elif {"record_id", "record_kind", "version"}.issubset(keys):
            reference_kind = value["record_kind"]
            contract = contracts.get(reference_kind)
            definition = definitions.get(value["record_id"])
            incompatible = (
                contract is None
                or contract.get("reference_shape") != "versioned_reference"
                or definition is None
                or definition.get("kind") not in set(contract.get("compatible_definition_kinds", []))
                or (
                    definition.get("kind") == "record_identity"
                    and contract.get("record_identity_requires_exact_record_kind") is True
                    and definition.get("record_kind") != reference_kind
                )
            )
            add_if(
                output,
                incompatible,
                "GA-REFERENCE-KIND",
                f"{pointer}/record_kind",
                "versioned reference kind and resolved definition kind must satisfy the exact registry contract",
            )
            add_if(
                output,
                contract is not None
                and definition is not None
                and contract.get("version_must_match") is True
                and value["version"] != definition.get("version"),
                "GA-REFERENCE-VERSION",
                f"{pointer}/version",
                "versioned reference version must equal the resolved definition version",
            )
        elif {"actor_id", "actor_type", "version", "role"}.issubset(keys):
            definition = definitions.get(value["actor_id"])
            incompatible = (
                actor_contract.get("reference_shape") != "actor_reference"
                or actor_contract.get("required_definition_kind") != "actor"
                or definition is None
                or definition.get("kind") != "actor"
                or (
                    actor_contract.get("actor_type_must_match") is True
                    and value["actor_type"] != definition.get("actor_type")
                )
            )
            add_if(
                output,
                incompatible,
                "GA-ACTOR-REFERENCE-TYPE",
                f"{pointer}/actor_type",
                "actor reference identity, definition kind, and actor type must reconcile exactly",
            )
            add_if(
                output,
                definition is not None
                and actor_contract.get("version_must_match") is True
                and value["version"] != definition.get("version"),
                "GA-REFERENCE-VERSION",
                f"{pointer}/version",
                "actor reference version must equal the resolved definition version",
            )
        for key, child in value.items():
            visit(child, f"{pointer}/{pointer_token(key)}")

    visit(instance, "")
    return output


def schema_reference_violations(
    instance: Mapping[str, Any], resolution_context: Mapping[str, Any] | None
) -> list[dict[str, str]]:
    """Bind the instance to the exact schema selected by the immutable validator."""
    expected_schema_id = (
        resolution_context.get("expected_schema_id")
        if isinstance(resolution_context, Mapping)
        else None
    )
    invalid = (
        not isinstance(expected_schema_id, str)
        or instance.get("schema_id") != expected_schema_id
        or instance.get("schema_version") != SCIENCE_SCHEMA_VERSION
    )
    return (
        [
            violation(
                "GA-SCHEMA-REFERENCE-RESOLUTION",
                "/schema_id"
                if instance.get("schema_id") != expected_schema_id
                else "/schema_version",
                "the application schema identity does not resolve the exact locally validated Gate A 1.2 schema",
            )
        ]
        if invalid
        else []
    )


def registry_bare_identifier_violations(
    instance: Mapping[str, Any],
    registry: Mapping[str, Any],
    resolution_context: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    """Resolve explicitly classified scalar identifiers without naming inference."""
    output: list[dict[str, str]] = []
    definitions: dict[str, list[Mapping[str, Any]]] = {}
    for item in registry.get("definitions", []):
        if isinstance(item, Mapping) and isinstance(item.get("definition_id"), str):
            definitions.setdefault(item["definition_id"], []).append(item)

    def require(pointer: str, identifier: object, kind: str) -> Mapping[str, Any] | None:
        matches = definitions.get(identifier, []) if isinstance(identifier, str) else []
        valid = (
            len(matches) == 1
            and matches[0].get("kind") == kind
            and matches[0].get("version") == SCIENCE_SCHEMA_VERSION
            and matches[0].get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
        )
        add_if(
            output,
            not valid,
            "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
            pointer,
            "the scalar identifier does not resolve exactly once to the required registry kind, version, and protocol owner",
        )
        return matches[0] if valid else None

    schema_id = (
        resolution_context.get("expected_schema_id")
        if isinstance(resolution_context, Mapping)
        and isinstance(resolution_context.get("expected_schema_id"), str)
        else instance.get("schema_id")
    )
    if schema_id == ASSURANCE_SCHEMA_ID:
        require("/bundle_id", instance.get("bundle_id"), "assurance_bundle")
        dataset = instance.get("dataset_governance", {})
        require(
            "/dataset_governance/dataset_id",
            dataset.get("dataset_id") if isinstance(dataset, Mapping) else None,
            "dataset",
        )
        ethics_review = (
            dataset.get("ethics_review") if isinstance(dataset, Mapping) else {}
        )
        require(
            "/dataset_governance/ethics_review/assumption_id",
            ethics_review.get("assumption_id")
            if isinstance(ethics_review, Mapping)
            else None,
            "assumption",
        )
        odd = instance.get("odd_contract", {})
        require(
            "/odd_contract/odd_id",
            odd.get("odd_id") if isinstance(odd, Mapping) else None,
            "odd",
        )
        scenario = instance.get("scenario_contract", {})
        require(
            "/scenario_contract/scenario_set_id",
            scenario.get("scenario_set_id") if isinstance(scenario, Mapping) else None,
            "scenario_set",
        )
        benchmark = instance.get("benchmark_contract", {})
        require(
            "/benchmark_contract/benchmark_id",
            benchmark.get("benchmark_id") if isinstance(benchmark, Mapping) else None,
            "benchmark",
        )
        safety = instance.get("safety_case", {})
        require(
            "/safety_case/case_id",
            safety.get("case_id") if isinstance(safety, Mapping) else None,
            "safety_case",
        )
    elif schema_id == HUMAN_SCHEMA_ID:
        belief = instance.get("belief", {})
        normalization_policy = (
            belief.get("normalization_policy_binding")
            if isinstance(belief, Mapping)
            else {}
        )
        require(
            "/belief/normalization_policy_binding/policy_id",
            normalization_policy.get("policy_id")
            if isinstance(normalization_policy, Mapping)
            else None,
            "constraint",
        )
        state_space = belief.get("state_space", {}) if isinstance(belief, Mapping) else {}
        state_definition = require(
            "/belief/state_space/state_space_id",
            state_space.get("state_space_id"),
            "state_space",
        )
        if state_definition is not None and (
            state_space.get("version") != state_definition.get("version")
            or state_space.get("state_ids") != state_definition.get("member_ids")
        ):
            output.append(
                violation(
                    "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                    "/belief/state_space/state_ids",
                    "the declared state-space version and ordered member identifiers must exact-bind the resolved registry definition",
                )
            )
        decision = instance.get("decision", {})
        action_space_definition = require(
            "/decision/action_space_id",
            decision.get("action_space_id") if isinstance(decision, Mapping) else None,
            "action_space",
        )
        if action_space_definition is not None:
            selected_action = (
                observed(decision.get("selected_action"))
                if isinstance(decision, Mapping)
                else None
            )
            if selected_action is not None and selected_action not in action_space_definition.get(
                "member_ids", []
            ):
                output.append(
                    violation(
                        "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                        "/decision/selected_action/value",
                        "the observed decision action must be an exact member of the resolved registry action space",
                    )
                )
        readiness = instance.get("readiness", {})
        if isinstance(readiness, Mapping):
            window = readiness.get("window", {})
            require(
                "/readiness/window/window_id",
                window.get("window_id") if isinstance(window, Mapping) else None,
                "window",
            )
            require(
                "/readiness/window/clock_id",
                window.get("clock_id") if isinstance(window, Mapping) else None,
                "clock",
            )
            for index, capability in enumerate(readiness.get("capabilities", [])):
                if not isinstance(capability, Mapping):
                    continue
                require(
                    f"/readiness/capabilities/{index}/capability_id",
                    capability.get("capability_id"),
                    "capability",
                )
                require(
                    f"/readiness/capabilities/{index}/dimension_id",
                    capability.get("dimension_id"),
                    "dimension",
                )
        recovery = instance.get("recovery", {})
        if isinstance(recovery, Mapping):
            window = recovery.get("window", {})
            require(
                "/recovery/window/window_id",
                window.get("window_id") if isinstance(window, Mapping) else None,
                "window",
            )
            require(
                "/recovery/window/clock_id",
                window.get("clock_id") if isinstance(window, Mapping) else None,
                "clock",
            )
            index_event = recovery.get("index_event", {})
            require(
                "/recovery/index_event/event_type",
                index_event.get("event_type") if isinstance(index_event, Mapping) else None,
                "event_type",
            )
            for index, event in enumerate(recovery.get("events", [])):
                require(
                    f"/recovery/events/{index}/event_type",
                    event.get("event_type") if isinstance(event, Mapping) else None,
                    "event_type",
                )
    elif schema_id == STUDY_SCHEMA_ID:
        require("/study_id", instance.get("study_id"), "record_identity")
        require("/unit_of_analysis", instance.get("unit_of_analysis"), "unit")
        graph = instance.get("causal_graph", {})
        if isinstance(graph, Mapping):
            require("/causal_graph/graph_id", graph.get("graph_id"), "graph")
            for index, node in enumerate(graph.get("nodes", [])):
                require(
                    f"/causal_graph/nodes/{index}/node_id",
                    node.get("node_id") if isinstance(node, Mapping) else None,
                    "graph_node",
                )
        for index, estimand in enumerate(instance.get("estimands", [])):
            require(
                f"/estimands/{index}/estimand_id",
                estimand.get("estimand_id") if isinstance(estimand, Mapping) else None,
                "estimand",
            )
        for index, adjustment in enumerate(instance.get("adjustment_sets", [])):
            require(
                f"/adjustment_sets/{index}/adjustment_set_id",
                adjustment.get("adjustment_set_id") if isinstance(adjustment, Mapping) else None,
                "adjustment_set",
            )
    elif schema_id == OPE_SCHEMA_ID:
        for section_name in ("behavior_policy", "target_policy"):
            section = instance.get(section_name, {})
            action_space = section.get("action_space", {}) if isinstance(section, Mapping) else {}
            definition = require(
                f"/{section_name}/action_space/action_space_id",
                action_space.get("action_space_id"),
                "action_space",
            )
            if definition is not None and (
                action_space.get("version") != definition.get("version")
                or action_space.get("action_ids") != definition.get("member_ids")
            ):
                output.append(
                    violation(
                        "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                        f"/{section_name}/action_space/action_ids",
                        "the declared action-space version and ordered member identifiers must exact-bind the resolved registry definition",
                    )
                )
        for index, estimator in enumerate(instance.get("estimators", [])):
            definition = require(
                f"/estimators/{index}/estimator_id",
                estimator.get("estimator_id") if isinstance(estimator, Mapping) else None,
                "estimator",
            )
            if (
                definition is not None
                and isinstance(estimator, Mapping)
                and estimator.get("version") != definition.get("version")
            ):
                output.append(
                    violation(
                        "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                        f"/estimators/{index}/version",
                        "the scalar estimator identifier and version must exact-bind its registry definition",
                    )
                )
        construction = instance.get("weight_construction", {})
        require(
            "/weight_construction/weight_set_id",
            construction.get("weight_set_id") if isinstance(construction, Mapping) else None,
            "weight_set",
        )
        for index, row in enumerate(instance.get("effective_sample_size_by_horizon", [])):
            require(
                f"/effective_sample_size_by_horizon/{index}/weight_set_id",
                row.get("weight_set_id") if isinstance(row, Mapping) else None,
                "weight_set",
            )
        for index, estimator in enumerate(instance.get("estimators", [])):
            require(
                f"/estimators/{index}/weight_set_id",
                estimator.get("weight_set_id") if isinstance(estimator, Mapping) else None,
                "weight_set",
            )
    elif schema_id == JOINT_SCHEMA_ID:
        transfer = instance.get("transfer_evaluation", {})
        metric_contract = transfer.get("metric_contract", {}) if isinstance(transfer, Mapping) else {}
        metric_definition = require(
            "/transfer_evaluation/metric_contract/metric_contract_id",
            metric_contract.get("metric_contract_id"),
            "metric",
        )
        if metric_definition is not None and metric_contract.get("version") != metric_definition.get("version"):
            output.append(
                violation(
                    "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                    "/transfer_evaluation/metric_contract/version",
                    "the scalar metric identifier and version must exact-bind its registry definition",
                )
            )
        for result_name in ("source_result", "target_result"):
            result = transfer.get(result_name, {}) if isinstance(transfer, Mapping) else {}
            require(
                f"/transfer_evaluation/{result_name}/domain_id",
                result.get("domain_id") if isinstance(result, Mapping) else None,
                "domain",
            )
            metric_definition = require(
                f"/transfer_evaluation/{result_name}/metric_contract_id",
                result.get("metric_contract_id") if isinstance(result, Mapping) else None,
                "metric",
            )
            if (
                metric_definition is not None
                and isinstance(result, Mapping)
                and result.get("metric_contract_version") != metric_definition.get("version")
            ):
                output.append(
                    violation(
                        "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                        f"/transfer_evaluation/{result_name}/metric_contract_version",
                        "the scalar metric identifier and version must exact-bind its registry definition",
                    )
                )
        for section_name in ("conformal_evaluation", "worst_group_evaluation"):
            section = instance.get(section_name, {})
            if not isinstance(section, Mapping):
                continue
            for index, group_id in enumerate(section.get("group_universe", [])):
                require(
                    f"/{section_name}/group_universe/{index}",
                    group_id,
                    "group",
                )

    def visit_closed_scalar_owners(value: Any, pointer: str) -> None:
        if isinstance(value, Mapping):
            for key, child in value.items():
                token = str(key).replace("~", "~0").replace("/", "~1")
                child_pointer = f"{pointer}/{token}"
                if key == "assumption_id":
                    require(child_pointer, child, "assumption")
                elif key == "basis_ids" and isinstance(child, list):
                    # The readiness aggregate names its unresolved capability
                    # declarations directly; every other nonobserved basis is
                    # a protocol-owned, explicitly non-supporting constraint.
                    if child_pointer != "/readiness/aggregate/estimate/basis_ids":
                        for index, identifier in enumerate(child):
                            require(f"{child_pointer}/{index}", identifier, "constraint")
                visit_closed_scalar_owners(child, child_pointer)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit_closed_scalar_owners(child, f"{pointer}/{index}")

    visit_closed_scalar_owners(instance, "")
    return output


def classified_reference_path_violations(
    instance: Mapping[str, Any],
    registry: Mapping[str, Any],
    resolution_context: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    """Execute the exact schema-derived scalar path dispatch supplied by the validator."""
    bindings = (
        resolution_context.get("reference_path_bindings")
        if isinstance(resolution_context, Mapping)
        else None
    )
    if bindings is None:
        # Direct unit calls retain the explicit per-domain resolvers above.
        # The release validator always supplies its independently derived path
        # inventory and separately proves profile/handler equality.
        return []
    if not isinstance(bindings, list):
        raise ScienceContractError("reference path bindings must be an ordered array")
    if (
        not isinstance(resolution_context, Mapping)
        or resolution_context.get("reference_path_handler_contract")
        != REFERENCE_PATH_HANDLER_CONTRACT
    ):
        raise ScienceContractError(
            "reference path bindings do not carry the independently frozen handler contract"
        )
    schema_id = (
        resolution_context.get("expected_schema_id")
        if isinstance(resolution_context, Mapping)
        else instance.get("schema_id")
    )
    definitions: dict[str, list[Mapping[str, Any]]] = {}
    for item in registry.get("definitions", []):
        if isinstance(item, Mapping) and isinstance(item.get("definition_id"), str):
            definitions.setdefault(item["definition_id"], []).append(item)

    def pointer_tokens(pointer_glob: object) -> list[str]:
        if not isinstance(pointer_glob, str) or not pointer_glob.startswith("/"):
            raise ScienceContractError("reference path binding has an invalid pointer glob")
        return [
            token.replace("~1", "/").replace("~0", "~")
            for token in pointer_glob[1:].split("/")
        ]

    def materialize(pointer_glob: object) -> list[tuple[str, Any]]:
        values: list[tuple[str, Any]] = []

        def visit(value: Any, tokens: Sequence[str], pointer: str) -> None:
            if not tokens:
                values.append((pointer, value))
                return
            token, *remaining = tokens
            if token == "*":
                if isinstance(value, list):
                    for index, child in enumerate(value):
                        visit(child, remaining, f"{pointer}/{index}")
                return
            if isinstance(value, Mapping) and token in value:
                encoded = token.replace("~", "~0").replace("/", "~1")
                visit(value[token], remaining, f"{pointer}/{encoded}")

        visit(instance, pointer_tokens(pointer_glob), "")
        return values

    relevant: list[Mapping[str, Any]] = []
    expected_handlers = {
        ("rule_reference", "typed_registry_reference"): "typed_reference_violations",
        ("versioned_reference", "typed_registry_reference"): "typed_reference_violations",
        ("versioned_reference", "assumption_evidence_fail_closed"): "assumption_evidence_violations",
        ("actor_reference", "typed_registry_reference"): "typed_reference_violations",
        ("artifact_reference", "exact_snapshot_artifact"): "lifecycle_policy_violations",
        ("explicit_evidence_gap", "explicit_non_supporting_gap"): "evidence_gap_reference_violations",
        ("schema_reference", "exact_local_schema"): "schema_reference_violations",
        ("registry_bare_identifier", "exact_registry_definition"): "classified_reference_path_violations",
        ("document_local_identifier", "exact_document_member"): "classified_reference_path_violations",
        ("identity_declaration", "unique_identity_declaration"): "classified_reference_path_violations",
    }
    for row in bindings:
        if not isinstance(row, Mapping):
            raise ScienceContractError("reference path binding row must be an object")
        dispatch_key = (row.get("classification"), row.get("resolution_policy"))
        if row.get("handler") != expected_handlers.get(dispatch_key):
            raise ScienceContractError(
                "reference path binding does not name the exact handler for its class and resolution policy"
            )
        if row.get("schema_id") == schema_id:
            relevant.append(row)
    output: list[dict[str, str]] = []
    identity_values: dict[object, str] = {}
    for row in relevant:
        classification = row.get("classification")
        values = materialize(row.get("pointer_glob"))
        if classification == "registry_bare_identifier":
            expected_kind = row.get("expected_registry_kind")
            if not isinstance(expected_kind, str):
                raise ScienceContractError(
                    "registry-bare path binding lacks an exact expected definition kind"
                )
            for pointer, identifier in values:
                matches = definitions.get(identifier, []) if isinstance(identifier, str) else []
                valid = (
                    len(matches) == 1
                    and matches[0].get("kind") == expected_kind
                    and matches[0].get("version") == SCIENCE_SCHEMA_VERSION
                    and matches[0].get("owner_protocol_release_id")
                    == PROTOCOL_RELEASE_ID
                )
                add_if(
                    output,
                    not valid,
                    "GA-REGISTRY-BARE-IDENTIFIER-RESOLUTION",
                    pointer,
                    "the scalar identifier does not resolve exactly once to the required registry kind, version, and protocol owner",
                )
        elif classification == "document_local_identifier":
            collection_pointer = row.get("local_collection_pointer")
            members = [value for _, value in materialize(collection_pointer)]
            for pointer, identifier in values:
                add_if(
                    output,
                    sum(1 for member in members if member == identifier) != 1,
                    "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
                    pointer,
                    "the identifier does not resolve exactly once in its explicitly owned document collection",
                )
        elif classification == "identity_declaration":
            for pointer, identifier in values:
                if identifier in identity_values:
                    output.append(
                        violation(
                            "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
                            pointer,
                            "document-local identity declarations must be unique across identity kinds and collections",
                        )
                    )
                else:
                    identity_values[identifier] = pointer
    return output


def document_local_identifier_violations(
    instance: Mapping[str, Any], resolution_context: Mapping[str, Any] | None = None
) -> list[dict[str, str]]:
    """Resolve identifiers against explicit owning collections in the same document."""
    output: list[dict[str, str]] = []

    def require(pointer: str, identifier: object, members: Sequence[object]) -> None:
        add_if(
            output,
            sum(1 for member in members if member == identifier) != 1,
            "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
            pointer,
            "the identifier does not resolve exactly once in its explicitly owned document collection",
        )

    schema_id = (
        resolution_context.get("expected_schema_id")
        if isinstance(resolution_context, Mapping)
        and isinstance(resolution_context.get("expected_schema_id"), str)
        else instance.get("schema_id")
    )
    declarations: list[tuple[str, object]] = [
        ("/artifact_id", instance.get("artifact_id")),
        *(
            (f"/lifecycle_history/{index}/event_id", event.get("event_id"))
            for index, event in enumerate(instance.get("lifecycle_history", []))
            if isinstance(event, Mapping)
        ),
    ]
    if schema_id == ASSURANCE_SCHEMA_ID:
        declarations.extend(
            (f"/test_contracts/{index}/test_id", item.get("test_id"))
            for index, item in enumerate(instance.get("test_contracts", []))
            if isinstance(item, Mapping)
        )
        safety = instance.get("safety_case", {})
        for collection, identity_field in (("hazards", "hazard_id"), ("claims", "claim_id")):
            declarations.extend(
                (f"/safety_case/{collection}/{index}/{identity_field}", item.get(identity_field))
                for index, item in enumerate(
                    safety.get(collection, []) if isinstance(safety, Mapping) else []
                )
                if isinstance(item, Mapping)
            )
    elif schema_id == HUMAN_SCHEMA_ID:
        declarations.extend(
            (
                ("/assessment_id", instance.get("assessment_id")),
                ("/observation/observation_id", instance.get("observation", {}).get("observation_id")),
                ("/belief/belief_id", instance.get("belief", {}).get("belief_id")),
                ("/belief/information_set/information_set_id", instance.get("belief", {}).get("information_set", {}).get("information_set_id")),
                ("/decision/decision_id", instance.get("decision", {}).get("decision_id")),
                ("/decision/information_set/information_set_id", instance.get("decision", {}).get("information_set", {}).get("information_set_id")),
                ("/readiness/readiness_id", instance.get("readiness", {}).get("readiness_id")),
                ("/recovery/recovery_id", instance.get("recovery", {}).get("recovery_id")),
                ("/recovery/index_event/event_id", instance.get("recovery", {}).get("index_event", {}).get("event_id")),
            )
        )
        declarations.extend(
            (f"/recovery/events/{index}/event_id", event.get("event_id"))
            for index, event in enumerate(instance.get("recovery", {}).get("events", []))
            if isinstance(event, Mapping)
        )
    elif schema_id == JOINT_SCHEMA_ID:
        declarations.append(("/evaluation_id", instance.get("evaluation_id")))
    elif schema_id == OPE_SCHEMA_ID:
        declarations.append(("/evaluation_id", instance.get("evaluation_id")))
        for trajectory_index, trajectory in enumerate(instance.get("trajectories", [])):
            if not isinstance(trajectory, Mapping):
                continue
            declarations.append(
                (f"/trajectories/{trajectory_index}/trajectory_id", trajectory.get("trajectory_id"))
            )
            for step_index, step in enumerate(trajectory.get("steps", [])):
                if not isinstance(step, Mapping):
                    continue
                declarations.extend(
                    (
                        (f"/trajectories/{trajectory_index}/steps/{step_index}/history_id", step.get("history_id")),
                        (f"/trajectories/{trajectory_index}/steps/{step_index}/information_set/information_set_id", step.get("information_set", {}).get("information_set_id")),
                    )
                )
    elif schema_id == STUDY_SCHEMA_ID:
        declarations.extend(
            (f"/identification_queries/{index}/query_id", item.get("query_id"))
            for index, item in enumerate(instance.get("identification_queries", []))
            if isinstance(item, Mapping)
        )
        declarations.extend(
            (f"/deviations/{index}/deviation_id", item.get("deviation_id"))
            for index, item in enumerate(instance.get("deviations", []))
            if isinstance(item, Mapping)
        )
    seen_declarations: dict[object, str] = {}
    for pointer, identifier in declarations:
        if identifier in seen_declarations:
            diagnostic_pointer = (
                "/deviations"
                if schema_id == STUDY_SCHEMA_ID and pointer.startswith("/deviations/")
                else pointer
            )
            output.append(
                violation(
                    "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
                    diagnostic_pointer,
                    "document-local identity declarations must be unique across identity kinds and collections",
                )
            )
            break
        seen_declarations[identifier] = pointer
    if schema_id == ASSURANCE_SCHEMA_ID:
        test_contracts = instance.get("test_contracts", [])
        test_ids = [item.get("test_id") for item in test_contracts if isinstance(item, Mapping)]
        safety = instance.get("safety_case", {})
        hazards = safety.get("hazards", []) if isinstance(safety, Mapping) else []
        hazard_ids = [item.get("hazard_id") for item in hazards if isinstance(item, Mapping)]
        claims = safety.get("claims", []) if isinstance(safety, Mapping) else []
        claim_ids = [item.get("claim_id") for item in claims if isinstance(item, Mapping)]
        for pointer, identifiers in (
            ("/test_contracts", test_ids),
            ("/safety_case/hazards", hazard_ids),
            ("/safety_case/claims", claim_ids),
        ):
            if (
                any(not isinstance(identifier, str) for identifier in identifiers)
                or len(identifiers) != len(set(identifiers))
            ):
                output.append(
                    violation(
                        "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
                        pointer,
                        "the local identity collection contains an absent or duplicate declaration",
                    )
                )
        for claim_index, claim in enumerate(claims):
            if not isinstance(claim, Mapping):
                continue
            for reference_index, hazard_id in enumerate(claim.get("hazard_refs", [])):
                require(
                    f"/safety_case/claims/{claim_index}/hazard_refs/{reference_index}",
                    hazard_id,
                    hazard_ids,
                )
    elif schema_id == HUMAN_SCHEMA_ID:
        belief = instance.get("belief", {})
        state_space = belief.get("state_space", {}) if isinstance(belief, Mapping) else {}
        states = state_space.get("state_ids", []) if isinstance(state_space, Mapping) else []
        distribution = belief.get("distribution", {}) if isinstance(belief, Mapping) else {}
        for index, row in enumerate(distribution.get("probabilities", [])):
            require(
                f"/belief/distribution/probabilities/{index}/state_id",
                row.get("state_id") if isinstance(row, Mapping) else None,
                states,
            )
        readiness = instance.get("readiness", {})
        capabilities = readiness.get("capabilities", []) if isinstance(readiness, Mapping) else []
        capability_ids = [
            item.get("capability_id") for item in capabilities if isinstance(item, Mapping)
        ]
        for index, capability_id in enumerate(
            readiness.get("unresolved_capability_ids", []) if isinstance(readiness, Mapping) else []
        ):
            require(f"/readiness/unresolved_capability_ids/{index}", capability_id, capability_ids)
        aggregate = readiness.get("aggregate", {}) if isinstance(readiness, Mapping) else {}
        estimate = aggregate.get("estimate", {}) if isinstance(aggregate, Mapping) else {}
        for index, capability_id in enumerate(
            estimate.get("basis_ids", []) if isinstance(estimate, Mapping) else []
        ):
            require(f"/readiness/aggregate/estimate/basis_ids/{index}", capability_id, capability_ids)
        recovery = instance.get("recovery", {})
        events = recovery.get("events", []) if isinstance(recovery, Mapping) else []
        event_ids = [item.get("event_id") for item in events if isinstance(item, Mapping)]
        index_event = recovery.get("index_event", {}) if isinstance(recovery, Mapping) else {}
        complete_event_ids = [
            index_event.get("event_id") if isinstance(index_event, Mapping) else None,
            *event_ids,
        ]
        seen_event_ids: set[object] = set()
        for index, event_id in enumerate(complete_event_ids):
            if not isinstance(event_id, str) or event_id in seen_event_ids:
                output.append(
                    violation(
                        "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
                        "/recovery/index_event/event_id"
                        if index == 0
                        else f"/recovery/events/{index - 1}/event_id",
                        "the recovery timeline contains an absent or duplicate local event identity",
                    )
                )
                break
            seen_event_ids.add(event_id)
        outcome = recovery.get("outcome", {}) if isinstance(recovery, Mapping) else {}
        qualifying = outcome.get("qualifying_event_id", {}) if isinstance(outcome, Mapping) else {}
        if isinstance(qualifying, Mapping) and qualifying.get("state") == "observed":
            require(
                "/recovery/outcome/qualifying_event_id/value",
                qualifying.get("value"),
                event_ids,
            )
    elif schema_id == STUDY_SCHEMA_ID:
        graph = instance.get("causal_graph", {})
        nodes = graph.get("nodes", []) if isinstance(graph, Mapping) else []
        node_ids = [node.get("node_id") for node in nodes if isinstance(node, Mapping)]
        for edge_index, edge in enumerate(graph.get("edges", []) if isinstance(graph, Mapping) else []):
            if not isinstance(edge, Mapping):
                continue
            require(f"/causal_graph/edges/{edge_index}/from_node_id", edge.get("from_node_id"), node_ids)
            require(f"/causal_graph/edges/{edge_index}/to_node_id", edge.get("to_node_id"), node_ids)
        estimands = instance.get("estimands", [])
        estimand_ids = [item.get("estimand_id") for item in estimands if isinstance(item, Mapping)]
        for index, estimand in enumerate(estimands):
            if not isinstance(estimand, Mapping):
                continue
            require(
                f"/estimands/{index}/treatment_node_id",
                estimand.get("treatment_node_id"),
                node_ids,
            )
            require(
                f"/estimands/{index}/outcome_node_id",
                estimand.get("outcome_node_id"),
                node_ids,
            )
        adjustment_sets = instance.get("adjustment_sets", [])
        adjustment_ids = [item.get("adjustment_set_id") for item in adjustment_sets if isinstance(item, Mapping)]
        for set_index, adjustment in enumerate(adjustment_sets):
            if not isinstance(adjustment, Mapping):
                continue
            for node_index, node_id in enumerate(adjustment.get("node_ids", [])):
                require(f"/adjustment_sets/{set_index}/node_ids/{node_index}", node_id, node_ids)
        queries = instance.get("identification_queries", [])
        query_ids = [item.get("query_id") for item in queries if isinstance(item, Mapping)]
        for index, query in enumerate(queries):
            if not isinstance(query, Mapping):
                continue
            require(f"/identification_queries/{index}/query_id", query.get("query_id"), query_ids)
            require(f"/identification_queries/{index}/estimand_id", query.get("estimand_id"), estimand_ids)
            require(f"/identification_queries/{index}/treatment_node_id", query.get("treatment_node_id"), node_ids)
            require(f"/identification_queries/{index}/outcome_node_id", query.get("outcome_node_id"), node_ids)
            if query.get("adjustment_set_id") is not None:
                require(f"/identification_queries/{index}/adjustment_set_id", query.get("adjustment_set_id"), adjustment_ids)
        control = instance.get("control_strategy", {})
        for index, adjustment_id in enumerate(
            control.get("selected_adjustment_set_ids", []) if isinstance(control, Mapping) else []
        ):
            require(f"/control_strategy/selected_adjustment_set_ids/{index}", adjustment_id, adjustment_ids)
        deviation_ids = [
            item.get("deviation_id")
            for item in instance.get("deviations", [])
            if isinstance(item, Mapping)
        ]
        if len(deviation_ids) != len(set(deviation_ids)):
            output.append(
                violation(
                    "GA-DOCUMENT-LOCAL-REFERENCE-RESOLUTION",
                    "/deviations",
                    "deviation identity declarations must be unique within the study record",
                )
            )
    elif schema_id == OPE_SCHEMA_ID:
        behavior = instance.get("behavior_policy", {})
        action_space = behavior.get("action_space", {}) if isinstance(behavior, Mapping) else {}
        action_ids = action_space.get("action_ids", []) if isinstance(action_space, Mapping) else []
        histories: list[object] = []
        for trajectory_index, trajectory in enumerate(instance.get("trajectories", [])):
            if not isinstance(trajectory, Mapping):
                continue
            for step_index, step in enumerate(trajectory.get("steps", [])):
                if not isinstance(step, Mapping):
                    continue
                histories.append(step.get("history_id"))
                require(
                    f"/trajectories/{trajectory_index}/steps/{step_index}/logged_action_id",
                    step.get("logged_action_id"),
                    action_ids,
                )
                for distribution_name in ("behavior_distribution", "target_distribution"):
                    for row_index, row in enumerate(step.get(distribution_name, [])):
                        require(
                            f"/trajectories/{trajectory_index}/steps/{step_index}/{distribution_name}/{row_index}/action_id",
                            row.get("action_id") if isinstance(row, Mapping) else None,
                            action_ids,
                        )
        support = instance.get("support_assessment", {})
        for collection_name in ("required_cells", "unsupported_cells"):
            for index, cell in enumerate(support.get(collection_name, []) if isinstance(support, Mapping) else []):
                if not isinstance(cell, Mapping):
                    continue
                require(f"/support_assessment/{collection_name}/{index}/history_id", cell.get("history_id"), histories)
                require(f"/support_assessment/{collection_name}/{index}/action_id", cell.get("action_id"), action_ids)
        estimators = instance.get("estimators", [])
        estimator_ids = [item.get("estimator_id") for item in estimators if isinstance(item, Mapping)]
        selection = instance.get("estimator_selection", {})
        for collection_name in ("candidate_estimator_ids", "selected_estimator_ids"):
            for index, estimator_id in enumerate(
                selection.get(collection_name, []) if isinstance(selection, Mapping) else []
            ):
                require(f"/estimator_selection/{collection_name}/{index}", estimator_id, estimator_ids)
    elif schema_id == JOINT_SCHEMA_ID:
        conformal = instance.get("conformal_evaluation", {})
        conformal_groups = conformal.get("group_universe", []) if isinstance(conformal, Mapping) else []
        for index, result in enumerate(conformal.get("group_results", []) if isinstance(conformal, Mapping) else []):
            require(
                f"/conformal_evaluation/group_results/{index}/group_id",
                result.get("group_id") if isinstance(result, Mapping) else None,
                conformal_groups,
            )
        worst = instance.get("worst_group_evaluation", {})
        worst_groups = worst.get("group_universe", []) if isinstance(worst, Mapping) else []
        for index, result in enumerate(worst.get("group_results", []) if isinstance(worst, Mapping) else []):
            require(
                f"/worst_group_evaluation/group_results/{index}/group_id",
                result.get("group_id") if isinstance(result, Mapping) else None,
                worst_groups,
            )
        for collection_name in (
            "eligible_group_ids",
            "unknown_group_ids",
            "insufficient_group_ids",
            "worst_group_ids",
        ):
            for index, group_id in enumerate(
                worst.get(collection_name, []) if isinstance(worst, Mapping) else []
            ):
                require(f"/worst_group_evaluation/{collection_name}/{index}", group_id, worst_groups)
    return output


def evidence_gap_reference_violations(instance: Mapping[str, Any]) -> list[dict[str, str]]:
    """Enforce the closed non-supporting explicit-gap reference shape."""
    output: list[dict[str, str]] = []
    placeholders = {"tbd", "todo", "unknown", "n/a", "none", "publisher self-assertion"}

    def token(value: object) -> str:
        return str(value).replace("~", "~0").replace("/", "~1")

    def visit(value: object, pointer: str) -> None:
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}/{index}")
            return
        if not isinstance(value, Mapping):
            return
        if value.get("state") == "evidence_gap" or {"evidence_refs", "gap_reason"}.issubset(value):
            reason = value.get("gap_reason")
            invalid = (
                value.get("state") != "evidence_gap"
                or value.get("evidence_refs") != []
                or not isinstance(reason, str)
                or len(reason.strip()) < 40
                or reason.strip().casefold().rstrip(".") in placeholders
            )
            add_if(
                output,
                invalid,
                "GA-EVIDENCE-GAP-REFERENCE-DISPOSITION",
                f"{pointer}/gap_reason",
                "the evidence-gap object is not an explicit unavailable, non-supporting, empty-reference disposition with a substantive reason",
            )
        for key, child in value.items():
            visit(child, f"{pointer}/{token(key)}")

    visit(instance, "")
    return output


ESTIMAND_CONTRACTS = {
    "reiyah.estimand.object-belief-quality": {
        "metric_class": "object_belief_quality",
        "application_role": "object_belief_scoring",
        "direction": "lower_is_better",
        "operand_contract": {
            "application_schema_id": HUMAN_SCHEMA_ID,
            "application_pointer": "/belief",
            "primary_measure_id": "reiyah.measure.proper-score-loss",
            "unit_contract_id": "reiyah.unit.scoring-rule-specific",
            "population_contract_id": "reiyah.population.encounter-object-time",
            "outcome_contract_id": "reiyah.outcome.independently-valid-reference-state",
            "comparator_contract_id": "reiyah.comparator.exact-scoring-rule-reference-method",
            "aggregation_contract_id": "reiyah.aggregation.population-mean-loss-with-coverage",
            "evidence_boundary_id": "reiyah.evidence-boundary.scoring-reference-not-retained",
            "required_operand_paths": [
                "/belief/as_of",
                "/belief/calibration_target",
                "/belief/distribution",
                "/belief/information_set",
                "/belief/normalization_policy_binding",
                "/belief/object_ref",
                "/belief/scoring_contract",
                "/belief/state_space",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.readiness": {
        "metric_class": "readiness",
        "application_role": "readiness_functional",
        "direction": "higher_is_better",
        "operand_contract": {
            "application_schema_id": HUMAN_SCHEMA_ID,
            "application_pointer": "/readiness",
            "primary_measure_id": "reiyah.measure.readiness-population-probability",
            "unit_contract_id": "reiyah.unit.probability",
            "population_contract_id": "reiyah.population.encounter-at-index-time",
            "outcome_contract_id": "reiyah.outcome.required-readiness-capabilities-met",
            "comparator_contract_id": "reiyah.comparator.declared-capability-thresholds",
            "aggregation_contract_id": "reiyah.aggregation.readiness-proportion-with-coverage",
            "evidence_boundary_id": "reiyah.evidence-boundary.record-contribution-only",
            "required_operand_paths": [
                "/readiness/aggregate",
                "/readiness/aggregation",
                "/readiness/as_of",
                "/readiness/capabilities",
                "/readiness/coverage_counts",
                "/readiness/unresolved_capability_ids",
                "/readiness/window",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.recoverability": {
        "metric_class": "recoverability",
        "application_role": "recovery_cdf",
        "direction": "higher_is_better",
        "operand_contract": {
            "application_schema_id": HUMAN_SCHEMA_ID,
            "application_pointer": "/recovery",
            "primary_measure_id": "reiyah.measure.recovery-cdf-by-horizon",
            "unit_contract_id": "reiyah.unit.probability",
            "population_contract_id": "reiyah.population.valid-challenge-encounter",
            "outcome_contract_id": "reiyah.outcome.recovered-by-frozen-horizon",
            "comparator_contract_id": "reiyah.comparator.versioned-policy-or-control",
            "aggregation_contract_id": "reiyah.aggregation.recovery-cdf-with-censoring",
            "evidence_boundary_id": "reiyah.evidence-boundary.record-contribution-only",
            "required_operand_paths": [
                "/recovery/censoring_policy",
                "/recovery/competing_event_policy",
                "/recovery/event_tie_policy",
                "/recovery/events",
                "/recovery/index_event",
                "/recovery/outcome",
                "/recovery/recovery_criterion",
                "/recovery/window",
                "/recovery/window_observation_complete",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.synthetic-risk-difference": {
        "metric_class": "causal_policy_effect",
        "application_role": "causal_policy_contrast",
        "direction": "signed_contrast",
        "operand_contract": {
            "application_schema_id": STUDY_SCHEMA_ID,
            "application_pointer": "/control_strategy",
            "primary_measure_id": "reiyah.measure.treatment-minus-comparator-risk-difference",
            "unit_contract_id": "reiyah.unit.probability-point-difference",
            "population_contract_id": "reiyah.population.exact-preregistered-causal-population",
            "outcome_contract_id": "reiyah.outcome.exact-node-window-and-intercurrent-rule",
            "comparator_contract_id": "reiyah.comparator.exact-preregistered-policy-text",
            "aggregation_contract_id": "reiyah.aggregation.average-potential-outcome-risk-difference",
            "evidence_boundary_id": "reiyah.evidence-boundary.study-design-no-effect-estimate",
            "required_operand_paths": [
                "/adjustment_sets",
                "/causal_graph",
                "/data_access_chronology",
                "/design_frozen_at",
                "/control_strategy/selected_adjustment_set_ids",
                "/estimands",
                "/identification_queries",
                "/split_policy",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.sequential-policy-value": {
        "metric_class": "sequential_policy_value",
        "application_role": "target_policy_value",
        "direction": "higher_is_better",
        "operand_contract": {
            "application_schema_id": OPE_SCHEMA_ID,
            "application_pointer": "/estimand_ref",
            "primary_measure_id": "reiyah.measure.expected-discounted-target-policy-return",
            "unit_contract_id": "reiyah.unit.bound-reward-contract",
            "population_contract_id": "reiyah.population.exact-trajectory-history-population",
            "outcome_contract_id": "reiyah.outcome.discounted-reward-sequence",
            "comparator_contract_id": "reiyah.comparator.frozen-behavior-policy",
            "aggregation_contract_id": "reiyah.aggregation.expected-discounted-return",
            "evidence_boundary_id": "reiyah.evidence-boundary.no-policy-value-output-at-gate-a",
            "required_operand_paths": [
                "/behavior_policy",
                "/effective_sample_size_by_horizon",
                "/estimator_selection",
                "/estimators",
                "/horizon",
                "/reward_contract",
                "/support_assessment",
                "/target_policy",
                "/trajectories",
                "/weight_construction",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.joint-silent-miss": {
        "metric_class": "joint_silent_miss",
        "application_role": "common_opportunity_joint_risk",
        "direction": "lower_is_better",
        "operand_contract": {
            "application_schema_id": JOINT_SCHEMA_ID,
            "application_pointer": "/joint_silent_miss",
            "primary_measure_id": "reiyah.measure.joint-silent-miss-probability",
            "unit_contract_id": "reiyah.unit.probability",
            "population_contract_id": "reiyah.population.exact-common-opportunity-set",
            "outcome_contract_id": "reiyah.outcome.both-miss-without-warning-or-fallback",
            "comparator_contract_id": "reiyah.comparator.human-automation-fallback-configuration",
            "aggregation_contract_id": "reiyah.aggregation.joint-silent-rows-over-opportunities",
            "evidence_boundary_id": "reiyah.evidence-boundary.synthetic-opportunity-rows-only",
            "required_operand_paths": [
                "/joint_silent_miss/automation_misses",
                "/joint_silent_miss/common_opportunity_cells",
                "/joint_silent_miss/human_misses",
                "/joint_silent_miss/identifiability",
                "/joint_silent_miss/joint_miss_risk",
                "/joint_silent_miss/joint_misses",
                "/joint_silent_miss/opportunities",
                "/joint_silent_miss/opportunity_rows",
                "/joint_silent_miss/opportunity_rule_ref",
                "/joint_silent_miss/opportunity_set_ref",
                "/joint_silent_miss/opportunity_window",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.conformal-coverage": {
        "metric_class": "conformal_coverage",
        "application_role": "coverage_constraint",
        "direction": "target_constraint",
        "operand_contract": {
            "application_schema_id": JOINT_SCHEMA_ID,
            "application_pointer": "/conformal_evaluation",
            "primary_measure_id": "reiyah.measure.empirical-set-coverage-constraint",
            "unit_contract_id": "reiyah.unit.probability",
            "population_contract_id": "reiyah.population.exact-conformal-test-and-group-set",
            "outcome_contract_id": "reiyah.outcome.reference-outcome-in-prediction-set",
            "comparator_contract_id": "reiyah.comparator.one-minus-alpha-target",
            "aggregation_contract_id": "reiyah.aggregation.covered-over-evaluated-count",
            "evidence_boundary_id": "reiyah.evidence-boundary.efficiency-out-of-scope-guarantee-unasserted",
            "required_operand_paths": [
                "/conformal_evaluation/alpha",
                "/conformal_evaluation/calibration_sample_count",
                "/conformal_evaluation/calibration_set_ref",
                "/conformal_evaluation/empirical_coverage",
                "/conformal_evaluation/exchangeability",
                "/conformal_evaluation/group_results",
                "/conformal_evaluation/group_universe",
                "/conformal_evaluation/guarantee",
                "/conformal_evaluation/guarantee_contract_ref",
                "/conformal_evaluation/method_ref",
                "/conformal_evaluation/target_coverage",
                "/conformal_evaluation/test_sample_count",
                "/conformal_evaluation/test_set_ref",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.ood-selective-risk-coverage": {
        "metric_class": "ood_selective_risk_coverage",
        "application_role": "joint_ood_selective_operating_point",
        "direction": "vector_tradeoff",
        "operand_contract": {
            "application_schema_id": JOINT_SCHEMA_ID,
            "application_pointer": "/ood_evaluation",
            "primary_measure_id": "reiyah.measure.ood-selective-risk-coverage-vector",
            "unit_contract_id": "reiyah.unit.rate-vector",
            "population_contract_id": "reiyah.population.exact-ood-selective-population",
            "outcome_contract_id": "reiyah.outcome.ood-detection-and-accepted-error-vector",
            "comparator_contract_id": "reiyah.comparator.pareto-operating-point-no-scalarization",
            "aggregation_contract_id": "reiyah.aggregation.disjoint-ood-and-selective-partitions",
            "evidence_boundary_id": "reiyah.evidence-boundary.prevalence-descriptive-unknown-mass-retained",
            "required_operand_paths": [
                "/ood_evaluation/detected_ood_count",
                "/ood_evaluation/detector_rule_ref",
                "/ood_evaluation/detector_unknown_count",
                "/ood_evaluation/false_positive_rate",
                "/ood_evaluation/joint_state_cells",
                "/ood_evaluation/partition_contract_ref",
                "/ood_evaluation/population_count",
                "/ood_evaluation/prevalence",
                "/ood_evaluation/prevalence_denominator",
                "/ood_evaluation/reference_ood_count",
                "/ood_evaluation/reference_rule_ref",
                "/ood_evaluation/reference_unknown_count",
                "/ood_evaluation/true_positive_rate",
                "/selective_evaluation",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.transfer": {
        "metric_class": "transfer",
        "application_role": "domain_gap",
        "direction": "signed_contrast",
        "operand_contract": {
            "application_schema_id": JOINT_SCHEMA_ID,
            "application_pointer": "/transfer_evaluation",
            "primary_measure_id": "reiyah.measure.target-minus-source-metric-gap",
            "unit_contract_id": "reiyah.unit.bound-base-metric",
            "population_contract_id": "reiyah.population.source-target-with-harmonization",
            "outcome_contract_id": "reiyah.outcome.exact-bound-transfer-metric",
            "comparator_contract_id": "reiyah.comparator.source-domain-same-metric",
            "aggregation_contract_id": "reiyah.aggregation.target-minus-source",
            "evidence_boundary_id": "reiyah.evidence-boundary.no-comparability-without-retained-assumption-evidence",
            "required_operand_paths": [
                "/transfer_evaluation/adaptation",
                "/transfer_evaluation/disposition",
                "/transfer_evaluation/gap",
                "/transfer_evaluation/invariance",
                "/transfer_evaluation/metric_contract",
                "/transfer_evaluation/overlap",
                "/transfer_evaluation/population_harmonization",
                "/transfer_evaluation/source_result",
                "/transfer_evaluation/target_data_access",
                "/transfer_evaluation/target_result",
            ],
            "runtime_output_authorized": False,
        },
    },
    "reiyah.estimand.worst-group": {
        "metric_class": "worst_group",
        "application_role": "maximum_eligible_group_loss",
        "direction": "lower_is_better",
        "operand_contract": {
            "application_schema_id": JOINT_SCHEMA_ID,
            "application_pointer": "/worst_group_evaluation",
            "primary_measure_id": "reiyah.measure.maximum-eligible-group-loss",
            "unit_contract_id": "reiyah.unit.error-probability",
            "population_contract_id": "reiyah.population.exact-protocol-group-set",
            "outcome_contract_id": "reiyah.outcome.shared-group-loss-metric",
            "comparator_contract_id": "reiyah.comparator.all-preregistered-groups",
            "aggregation_contract_id": "reiyah.aggregation.maximum-loss-with-all-ties",
            "evidence_boundary_id": "reiyah.evidence-boundary.synthetic-group-results-only",
            "required_operand_paths": [
                "/worst_group_evaluation/direction",
                "/worst_group_evaluation/disposition",
                "/worst_group_evaluation/eligible_group_ids",
                "/worst_group_evaluation/group_results",
                "/worst_group_evaluation/group_set_ref",
                "/worst_group_evaluation/group_universe",
                "/worst_group_evaluation/insufficient_group_ids",
                "/worst_group_evaluation/minimum_information_rule",
                "/worst_group_evaluation/omission_prohibited",
                "/worst_group_evaluation/shared_metric_contract",
                "/worst_group_evaluation/unknown_group_ids",
                "/worst_group_evaluation/worst_group_ids",
                "/worst_group_evaluation/worst_value",
            ],
            "runtime_output_authorized": False,
        },
    },
}

ESTIMAND_ORDER = (
    "reiyah.estimand.object-belief-quality",
    "reiyah.estimand.readiness",
    "reiyah.estimand.recoverability",
    "reiyah.estimand.joint-silent-miss",
    "reiyah.estimand.synthetic-risk-difference",
    "reiyah.estimand.sequential-policy-value",
    "reiyah.estimand.conformal-coverage",
    "reiyah.estimand.ood-selective-risk-coverage",
    "reiyah.estimand.transfer",
    "reiyah.estimand.worst-group",
)

# Canonicalize the mapping's observable iteration order to the protocol-owned
# order above.  Order is part of the closed v1.2 authority surface and is not
# inferred from the location of literal definitions in this source file.
ESTIMAND_CONTRACTS = {
    estimand_id: ESTIMAND_CONTRACTS[estimand_id] for estimand_id in ESTIMAND_ORDER
}


ESTIMAND_REFERENCE_PATHS = {
    HUMAN_SCHEMA_ID: (
        ("/belief/estimand_ref", ("belief", "estimand_ref"), "reiyah.estimand.object-belief-quality"),
        ("/readiness/estimand_ref", ("readiness", "estimand_ref"), "reiyah.estimand.readiness"),
        ("/recovery/estimand_ref", ("recovery", "estimand_ref"), "reiyah.estimand.recoverability"),
    ),
    STUDY_SCHEMA_ID: (
        ("/control_strategy/estimand_ref", ("control_strategy", "estimand_ref"), "reiyah.estimand.synthetic-risk-difference"),
    ),
    OPE_SCHEMA_ID: (
        ("/estimand_ref", ("estimand_ref",), "reiyah.estimand.sequential-policy-value"),
    ),
    JOINT_SCHEMA_ID: (
        ("/joint_silent_miss/estimand_ref", ("joint_silent_miss", "estimand_ref"), "reiyah.estimand.joint-silent-miss"),
        ("/conformal_evaluation/estimand_ref", ("conformal_evaluation", "estimand_ref"), "reiyah.estimand.conformal-coverage"),
        ("/ood_evaluation/estimand_ref", ("ood_evaluation", "estimand_ref"), "reiyah.estimand.ood-selective-risk-coverage"),
        ("/transfer_evaluation/estimand_ref", ("transfer_evaluation", "estimand_ref"), "reiyah.estimand.transfer"),
        ("/worst_group_evaluation/estimand_ref", ("worst_group_evaluation", "estimand_ref"), "reiyah.estimand.worst-group"),
    ),
}


def estimand_reference_violations(
    instance: Mapping[str, Any],
    registry: Mapping[str, Any],
    protocol: Mapping[str, Any],
    resolution_context: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    """Exact-bind every application estimand operand to protocol and registry authority."""
    schema_id = (
        resolution_context.get("expected_schema_id")
        if isinstance(resolution_context, Mapping)
        and isinstance(resolution_context.get("expected_schema_id"), str)
        else instance.get("schema_id")
    )
    raw_protocol_estimands = protocol.get("estimands", [])
    protocol_estimands: dict[str, list[Mapping[str, Any]]] = {}
    for item in raw_protocol_estimands:
        if isinstance(item, Mapping) and isinstance(item.get("estimand_id"), str):
            protocol_estimands.setdefault(item["estimand_id"], []).append(item)
    registry_estimands: dict[str, list[Mapping[str, Any]]] = {}
    for item in registry.get("definitions", []):
        if (
            isinstance(item, Mapping)
            and item.get("kind") == "estimand"
            and isinstance(item.get("definition_id"), str)
        ):
            registry_estimands.setdefault(item["definition_id"], []).append(item)
    output: list[dict[str, str]] = []

    protocol_order = tuple(
        item.get("estimand_id") if isinstance(item, Mapping) else None
        for item in raw_protocol_estimands
    )
    authority_valid = protocol_order == ESTIMAND_ORDER and set(registry_estimands) == set(
        ESTIMAND_ORDER
    )
    for estimand_id in ESTIMAND_ORDER:
        expected_contract = ESTIMAND_CONTRACTS[estimand_id]
        protocol_matches = protocol_estimands.get(estimand_id, [])
        registry_matches = registry_estimands.get(estimand_id, [])
        authority_valid = authority_valid and (
            len(protocol_matches) == 1
            and len(registry_matches) == 1
            and {
                key: protocol_matches[0].get(key)
                for key in ("metric_class", "application_role", "direction", "operand_contract")
            }
            == expected_contract
            and registry_matches[0].get("estimand_contract") == expected_contract
            and registry_matches[0].get("version") == SCIENCE_SCHEMA_VERSION
            and registry_matches[0].get("owner_protocol_release_id") == PROTOCOL_RELEASE_ID
        )

    missing = object()

    def resolve_pointer(pointer: str) -> object:
        value: object = instance
        for raw_token in pointer.split("/")[1:]:
            token = raw_token.replace("~1", "/").replace("~0", "~")
            if isinstance(value, Mapping):
                value = value.get(token, missing)
            elif isinstance(value, list) and token.isdigit() and int(token) < len(value):
                value = value[int(token)]
            else:
                return missing
            if value is missing:
                return missing
        return value

    for pointer, tokens, expected_id in ESTIMAND_REFERENCE_PATHS.get(schema_id, ()):
        value: object = instance
        for token in tokens:
            value = value.get(token) if isinstance(value, Mapping) else None
        protocol_matches = protocol_estimands.get(expected_id, [])
        registry_matches = registry_estimands.get(expected_id, [])
        invalid = (
            not authority_valid
            or not isinstance(value, Mapping)
            or value.get("record_id") != expected_id
            or value.get("record_kind") != "reiyah.kind.estimand"
            or value.get("version") != SCIENCE_SCHEMA_VERSION
            or len(protocol_matches) != 1
            or len(registry_matches) != 1
            or registry_matches[0].get("kind") != "estimand"
            or registry_matches[0].get("version") != SCIENCE_SCHEMA_VERSION
            or registry_matches[0].get("owner_protocol_release_id") != PROTOCOL_RELEASE_ID
            or any(
                resolve_pointer(operand_pointer) is missing
                for operand_pointer in ESTIMAND_CONTRACTS[expected_id]["operand_contract"][
                    "required_operand_paths"
                ]
            )
        )
        add_if(
            output,
            invalid,
            "GA-ESTIMAND-REFERENCE-BINDING",
            pointer,
            "application estimand reference does not exact-bind its profile and protocol assignment",
        )

    if schema_id == HUMAN_SCHEMA_ID:
        scoring = instance.get("belief", {}).get("scoring_contract", {})
        reference_outcome = (
            scoring.get("reference_outcome", {})
            if isinstance(scoring, Mapping)
            else {}
        )
        score_output = (
            scoring.get("score_output", {})
            if isinstance(scoring, Mapping)
            else {}
        )
        add_if(
            output,
            not isinstance(scoring, Mapping)
            or scoring.get("scoring_rule_ref") is not None
            or not isinstance(reference_outcome, Mapping)
            or reference_outcome.get("state") != "unmeasured"
            or reference_outcome.get("basis_ids")
            != ["reiyah.evidence_gap.reference_outcome"]
            or not isinstance(score_output, Mapping)
            or score_output.get("state") != "unmeasured"
            or score_output.get("basis_ids") != ["reiyah.gate.runtime_prohibited"]
            or scoring.get("aggregate_scoring_authorized") is not False,
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/belief/scoring_contract",
            "Gate A lacks an independently retained reference outcome and scoring rule, so belief quality scoring and aggregate output must remain explicitly nonobserved",
        )
        expected_readiness_rule = {
            "rule_id": "reiyah.rule.capability_threshold",
            "rule_kind": "reiyah.kind.readiness_criterion",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        for capability_index, capability in enumerate(
            instance.get("readiness", {}).get("capabilities", [])
        ):
            add_if(
                output,
                capability.get("criterion", {}).get("rule_ref")
                != expected_readiness_rule,
                "GA-ESTIMAND-REFERENCE-BINDING",
                f"/readiness/capabilities/{capability_index}/criterion/rule_ref",
                "the readiness functional must consume the exact protocol-owned criterion rule for every capability",
            )
        add_if(
            output,
            instance.get("recovery", {}).get("recovery_criterion")
            != {
                "rule_id": "reiyah.rule.recovery_event",
                "rule_kind": "reiyah.kind.recovery_criterion",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/recovery/recovery_criterion",
            "the recovery-CDF contribution must consume the exact protocol-owned recovery criterion",
        )
    elif schema_id == OPE_SCHEMA_ID:
        behavior_ref = instance.get("behavior_policy", {}).get("policy_ref")
        target_ref = instance.get("target_policy", {}).get("policy_ref")
        policy_binding_invalid = (
            behavior_ref
            != {
                "record_id": "reiyah.policy.synthetic_behavior",
                "record_kind": "reiyah.kind.policy",
                "version": SCIENCE_SCHEMA_VERSION,
            }
            or target_ref
            != {
                "record_id": "reiyah.policy.synthetic_target",
                "record_kind": "reiyah.kind.policy",
                "version": SCIENCE_SCHEMA_VERSION,
            }
            or behavior_ref == target_ref
        )
        add_if(
            output,
            policy_binding_invalid,
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/behavior_policy/policy_ref",
            "sequential policy value requires distinct exact behavior and target policy identities with frozen roles",
        )
        reward = instance.get("reward_contract", {})
        expected_reward = {
            "reward_signal_id": "reiyah.reward.synthetic-utility",
            "version": SCIENCE_SCHEMA_VERSION,
            "unit": "synthetic utility",
            "orientation": "higher_utility_is_better",
            "minimum": 0,
            "maximum": 1,
            "discounted_return_definition": "sum_discount_factor_power_step_index_times_reward",
        }
        reward_valid = reward == expected_reward
        for trajectory in instance.get("trajectories", []):
            for step in trajectory.get("steps", []) if isinstance(trajectory, Mapping) else []:
                measurement = step.get("reward", {}) if isinstance(step, Mapping) else {}
                if not isinstance(measurement, Mapping):
                    reward_valid = False
                elif measurement.get("state") == "observed":
                    value = measurement.get("value")
                    reward_valid = reward_valid and (
                        measurement.get("unit") == expected_reward["unit"]
                        and isinstance(value, (int, float))
                        and not isinstance(value, bool)
                        and expected_reward["minimum"] <= value <= expected_reward["maximum"]
                    )
        add_if(
            output,
            not reward_valid,
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/reward_contract",
            "sequential policy value requires one exact higher-utility reward signal, unit, range, and discounted-return definition across every trajectory reward operand",
        )
    elif schema_id == JOINT_SCHEMA_ID:
        add_if(
            output,
            instance.get("joint_silent_miss", {}).get("opportunity_rule_ref")
            != {
                "rule_id": "reiyah.rule.joint_miss_opportunity",
                "rule_kind": "reiyah.kind.event_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/joint_silent_miss/opportunity_rule_ref",
            "joint silent-miss risk must consume the exact common-opportunity rule",
        )
        add_if(
            output,
            instance.get("conformal_evaluation", {}).get("method_ref")
            != {
                "rule_id": "reiyah.rule.split_conformal",
                "rule_kind": "reiyah.kind.conformal_method",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/conformal_evaluation/method_ref",
            "conformal coverage must consume the exact protocol-owned method definition",
        )
        ood_section = instance.get("ood_evaluation", {})
        add_if(
            output,
            ood_section.get("reference_rule_ref")
            != {
                "rule_id": "reiyah.rule.ood_reference",
                "rule_kind": "reiyah.kind.ood_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            }
            or ood_section.get("detector_rule_ref")
            != {
                "rule_id": "reiyah.rule.ood_detector",
                "rule_kind": "reiyah.kind.ood_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/ood_evaluation/reference_rule_ref",
            "the OOD-selective vector must exact-bind distinct protocol-owned reference and detector rules",
        )
        expected_transfer_metric = {
            "metric_contract_id": "reiyah.metric.transfer_error",
            "version": SCIENCE_SCHEMA_VERSION,
            "unit": "error probability",
            "direction": "lower_is_better",
            "estimator_ref": {
                "rule_id": "reiyah.rule.transfer_estimator",
                "rule_kind": "reiyah.kind.estimator",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "population_rule_ref": {
                "rule_id": "reiyah.rule.transfer_population",
                "rule_kind": "reiyah.kind.population_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "outcome_window_rule_ref": {
                "rule_id": "reiyah.rule.transfer_window",
                "rule_kind": "reiyah.kind.outcome_window",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        }
        add_if(
            output,
            instance.get("transfer_evaluation", {}).get("metric_contract")
            != expected_transfer_metric,
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/transfer_evaluation/metric_contract",
            "the transfer estimand must exact-bind one metric identity, unit, direction, estimator, population, and outcome window",
        )
        worst_section = instance.get("worst_group_evaluation", {})
        worst_universe = ["reiyah.group.synthetic_a", "reiyah.group.synthetic_b"]
        worst_result_ids = [
            item.get("group_id")
            for item in worst_section.get("group_results", [])
            if isinstance(item, Mapping)
        ]
        add_if(
            output,
            worst_section.get("group_universe") != worst_universe
            or worst_result_ids != worst_universe,
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/worst_group_evaluation/group_universe",
            "worst-group evaluation must cover the exact protocol-owned group population without coordinated omission or substitution",
        )
        worst = instance.get("worst_group_evaluation", {})
        shared = worst.get("shared_metric_contract", {}) if isinstance(worst, Mapping) else {}
        expected_shared = {
            "metric_id": "reiyah.metric.synthetic-worst-group",
            "version": SCIENCE_SCHEMA_VERSION,
            "unit": "error probability",
            "direction": "lower_is_better",
            "population_rule_ref": {
                "rule_id": "reiyah.rule.worst_group_population",
                "rule_kind": "reiyah.kind.population_rule",
                "version": SCIENCE_SCHEMA_VERSION,
            },
            "outcome_window_rule_ref": {
                "rule_id": "reiyah.rule.worst_group_window",
                "rule_kind": "reiyah.kind.outcome_window",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        }
        shared_valid = shared == expected_shared and worst.get("direction") == shared.get("direction")
        for result in worst.get("group_results", []) if isinstance(worst, Mapping) else []:
            performance = result.get("performance", {}) if isinstance(result, Mapping) else {}
            if isinstance(performance, Mapping) and performance.get("state") == "observed":
                shared_valid = shared_valid and performance.get("unit") == shared.get("unit")
        worst_value = worst.get("worst_value", {}) if isinstance(worst, Mapping) else {}
        if isinstance(worst_value, Mapping) and worst_value.get("state") == "observed":
            shared_valid = shared_valid and worst_value.get("unit") == shared.get("unit")
        add_if(
            output,
            not shared_valid,
            "GA-ESTIMAND-REFERENCE-BINDING",
            "/worst_group_evaluation/shared_metric_contract",
            "worst-group direction, population, window, and every result unit must exact-bind one shared lower-is-better loss metric contract",
        )
    return output


def coverage_valid(counts: Mapping[str, Any], total: int | float) -> bool:
    return counts.get("total") == total and sum(counts.get(state, 0) for state in COVERAGE_STATES) == total


def assumption_evidence_violations(
    instance: Mapping[str, Any], contract: Mapping[str, Any] | None
) -> list[dict[str, str]]:
    """Validate every structured assumption assessment without treating it as evidence."""
    output: list[dict[str, str]] = []
    if contract is not None and not (
        contract.get("eligible_evidence_basis")
        == "independently_retained_exact_references"
        and contract.get("empty_evidence_policy") == "assumption_unknown"
        and contract.get("self_evidence_policy") == "ineligible"
        and contract.get("assumption_consumer_scope")
        == "conformal_exchangeability_and_transfer_overlap_invariance"
    ):
        raise ScienceContractError(
            "assumption-evidence executable contract has an unrecognized operand"
        )
    root_ids = {
        value
        for value in (
            instance.get("artifact_id"),
            instance.get("fixture_id"),
            instance.get("record_id"),
        )
        if isinstance(value, str)
    }

    def token(value: object) -> str:
        return str(value).replace("~", "~0").replace("/", "~1")

    def visit(value: object, pointer: str) -> None:
        if isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{pointer}/{index}")
            return
        if not isinstance(value, Mapping):
            return
        if {"assumption_id", "disposition", "evidence_refs"}.issubset(value):
            disposition = value.get("disposition")
            evidence = value.get("evidence_refs")
            if not isinstance(evidence, list):
                evidence = []
            self_references = []
            eligible = []
            for index, item in enumerate(evidence):
                if not isinstance(item, Mapping):
                    continue
                reference = item.get("evidence_ref")
                record_id = reference.get("record_id") if isinstance(reference, Mapping) else None
                is_self = record_id in root_ids or record_id == value.get("assumption_id")
                if is_self:
                    self_references.append(index)
                scope_match = observed(item.get("scope_match"))
                if (
                    not is_self
                    and item.get("eligibility") == "eligible"
                    and item.get("independence") == "independent"
                    and scope_match is True
                    and item.get("retained_source_eligible") is True
                    and item.get("supports_disposition") == disposition
                ):
                    eligible.append(index)
            add_if(
                output,
                bool(self_references),
                "GA-ASSUMPTION-SELF-EVIDENCE",
                f"{pointer}/evidence_refs/{self_references[0] if self_references else 0}",
                "an assumption cannot use its containing record or itself as independent evidence",
            )
            add_if(
                output,
                disposition in {"established", "contradicted"},
                "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY",
                f"{pointer}/evidence_refs",
                "Gate A 1.2 has no independently retained scientific-assumption evidence resolver",
            )
            add_if(
                output,
                not evidence and disposition not in {"unmeasured", "not_applicable"},
                "GA-ASSUMPTION-EVIDENCE-ELIGIBILITY",
                f"{pointer}/disposition",
                "an evidence-free assumption must remain unmeasured or not applicable",
            )
        for key, child in value.items():
            visit(child, f"{pointer}/{token(key)}")

    visit(instance, "")
    return output


def human_chain_violations(
    instance: Mapping[str, Any],
    belief_policy: Mapping[str, Any],
    contract: Mapping[str, Any],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    recognized_policies = (
        contract.get("belief_state_space_coverage")
        == "every_registry_state_exactly_once"
        and contract.get("belief_probability_policy")
        == "sum_one_within_protocol_tolerance"
        and contract.get("belief_normalization_policy_binding")
        == "exact_policy_identity_release_scope_operands_and_runtime_boundary"
        and contract.get("observation_validity_value_policy")
        == "independent_compatible_axes"
        and contract.get("object_reconciliation")
        == "exact_record_id_kind_and_version"
        and contract.get("information_set_reconciliation")
        == "exact_membership_and_freeze"
        and contract.get("observation_time_policy")
        == "event_lte_measured_lte_available"
        and contract.get("availability_boundary_policy")
        == "available_lte_belief_as_of_and_information_freeze"
        and contract.get("temporal_reconciliation")
        == "event_measurement_availability_belief_decision_exact_chain"
    )
    if not recognized_policies:
        raise ScienceContractError(
            "human reconciliation executable contract has an unrecognized operand"
        )
    observation = instance["observation"]
    belief = instance["belief"]
    decision = instance["decision"]

    distribution = belief["distribution"]
    distribution_observed = distribution.get("state") == "observed"
    probabilities = distribution.get("probabilities", []) if distribution_observed else []
    normalization_binding = belief["normalization_policy_binding"]
    binding_invalid = normalization_binding != belief_policy
    add_if(
        output,
        binding_invalid,
        "GA-BELIEF-NORMALIZATION-POLICY-BINDING",
        "/belief/normalization_policy_binding/absolute_tolerance",
        "the belief normalization binding must exactly match the protocol policy",
    )
    declared_states = list(belief["state_space"]["state_ids"])
    probability_states = [row.get("state_id") for row in probabilities]
    add_if(
        output,
        distribution_observed
        and (
            len(probability_states) != len(set(probability_states))
            or set(probability_states) != set(declared_states)
        ),
        "GA-BELIEF-STATE-SPACE-COVERAGE",
        "/belief/distribution/probabilities",
        "belief probability rows must cover each declared state exactly once",
    )
    probability_values = [row.get("probability") for row in probabilities]
    sum_target = normalization_binding.get("sum_target")
    absolute_tolerance = normalization_binding.get("absolute_tolerance")
    policy_invalid = (
        binding_invalid
        or normalization_binding.get("version") != "1.2.0"
        or normalization_binding.get("comparison") != "absolute_error_lte"
        or normalization_binding.get("record_tolerance_must_equal_policy") is not True
        or isinstance(sum_target, bool)
        or not isinstance(sum_target, (int, float))
        or isinstance(absolute_tolerance, bool)
        or not isinstance(absolute_tolerance, (int, float))
        or float(absolute_tolerance) < 0.0
    )
    probability_sum = sum(
        float(value) for value in probability_values if isinstance(value, (int, float))
    )
    distribution_invalid = distribution_observed and (
        not probability_values
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or float(value) < 0.0
            or float(value) > 1.0
            for value in probability_values
        )
        or (
            not policy_invalid
            and abs(probability_sum - float(sum_target)) > float(absolute_tolerance)
        )
    )
    add_if(
        output,
        distribution_invalid,
        "GA-BELIEF-DISTRIBUTION-SUM",
        "/belief/distribution/probabilities",
        "belief probabilities must be finite probabilities summing to one",
    )

    observation_state = observation["value"]["state"]
    expected_validity = "valid" if observation_state == "observed" else observation_state
    add_if(
        output,
        observation.get("validity") != expected_validity,
        "GA-OBSERVATION-VALIDITY-STATE",
        "/observation/validity",
        "observation validity must exactly propagate its epistemic value state",
    )

    object_invalid = not (
        observation.get("object_ref") == belief.get("object_ref") == decision.get("object_ref")
    )
    add_if(
        output,
        object_invalid,
        "GA-HUMAN-OBJECT-RECONCILIATION",
        "/decision/object_ref",
        "observation, belief, and decision must bind the exact same typed object reference",
    )

    def actor_identity(reference: object) -> tuple[object, object, object] | None:
        if not isinstance(reference, Mapping):
            return None
        return (
            reference.get("actor_id"),
            reference.get("actor_type"),
            reference.get("version"),
        )

    belief_holder = actor_identity(belief.get("holder"))
    decision_actor = actor_identity(decision.get("actor"))
    readiness_subject = actor_identity(instance.get("readiness", {}).get("subject_ref"))
    subject_invalid = (
        belief_holder is None
        or belief_holder[1] != "human"
        or not (belief_holder == decision_actor == readiness_subject)
    )
    subject_pointer = "/readiness/subject_ref"
    if belief_holder != decision_actor and decision_actor == readiness_subject:
        subject_pointer = "/belief/holder"
    elif decision_actor != belief_holder and belief_holder == readiness_subject:
        subject_pointer = "/decision/actor"
    add_if(
        output,
        subject_invalid,
        "GA-HUMAN-SUBJECT-RECONCILIATION",
        subject_pointer,
        "belief holder, decision actor, and readiness subject do not identify the same assessed human",
    )

    observation_ref = {
        "record_id": observation["observation_id"],
        "record_kind": "reiyah.kind.observation",
        "version": "1.2.0",
    }
    belief_ref = {
        "record_id": belief["belief_id"],
        "record_kind": "reiyah.kind.belief",
        "version": "1.2.0",
    }
    information_invalid = (
        belief["information_set"].get("items") != [observation_ref]
        or decision["information_set"].get("items") != [observation_ref, belief_ref]
    )
    add_if(
        output,
        information_invalid,
        "GA-HUMAN-INFORMATION-SET-RECONCILIATION",
        "/decision/information_set/items",
        "belief and decision information sets must exactly bind their antecedent records",
    )

    event = observed(observation["event_at"])
    measured = observed(observation["measured_at"])
    available = observed(observation["available_at"])
    belief_as_of = observed(belief["as_of"])
    decided = observed(decision["decided_at"])
    temporal_values = (event, measured, available, belief_as_of, decided)
    temporal_pointer = "/decision/decided_at/value"
    if event is None:
        temporal_pointer = "/observation/event_at"
    elif measured is None:
        temporal_pointer = "/observation/measured_at"
    elif available is None:
        temporal_pointer = "/observation/available_at"
    elif belief_as_of is None:
        temporal_pointer = "/belief/as_of"
    elif decided is None:
        temporal_pointer = "/decision/decided_at"
    temporal_invalid = any(value is None for value in temporal_values)
    if not temporal_invalid:
        event_at = parse_time(str(event))
        measured_at = parse_time(str(measured))
        available_at = parse_time(str(available))
        belief_at = parse_time(str(belief_as_of))
        belief_frozen = parse_time(belief["information_set"]["frozen_at"])
        decision_frozen = parse_time(decision["information_set"]["frozen_at"])
        decided_at = parse_time(str(decided))
        if event_at > measured_at:
            temporal_invalid = True
            temporal_pointer = "/observation/measured_at/value"
        elif measured_at > available_at:
            temporal_invalid = True
            temporal_pointer = "/observation/available_at/value"
        elif available_at > belief_at:
            temporal_invalid = True
            temporal_pointer = "/belief/as_of/value"
        elif belief_at != belief_frozen:
            temporal_invalid = True
            temporal_pointer = "/belief/information_set/frozen_at"
        elif belief_frozen > decision_frozen:
            temporal_invalid = True
            temporal_pointer = "/decision/information_set/frozen_at"
        elif decision_frozen > decided_at:
            temporal_invalid = True
            temporal_pointer = "/decision/decided_at/value"
    add_if(
        output,
        temporal_invalid,
        "GA-HUMAN-TEMPORAL-RECONCILIATION",
        temporal_pointer,
        "observed human-chain times must respect event, measurement, availability, belief freeze, decision freeze, and decision order",
    )
    return output


def readiness_violations(
    instance: Mapping[str, Any],
    belief_policy: Mapping[str, Any],
    readiness_contract: Mapping[str, Any],
    recovery_contract: Mapping[str, Any],
    human_contract: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    output = lifecycle_violations(instance)
    output.extend(human_chain_violations(instance, belief_policy, human_contract))
    readiness = instance["readiness"]
    expected_criterion_ref = readiness_contract.get("capability_criterion_rule_ref")
    if not (
        readiness_contract.get("required_unknown_policy")
        == "propagate_nonobserved_state"
        and readiness_contract.get("unresolved_set_policy")
        == "exact_required_or_safety_critical_or_positively_weighted_unknown_capability_ids"
        and readiness_contract.get("safety_critical_compensation_allowed") is False
        and readiness_contract.get("capability_set_record_kind")
        == "reiyah.kind.capability_set"
        and readiness_contract.get("capability_manifest_resolution_policy")
        == "exact_registry_members_bound_to_artifact"
        and expected_criterion_ref
        == {
            "rule_id": "reiyah.rule.capability_threshold",
            "rule_kind": "reiyah.kind.readiness_criterion",
            "version": SCIENCE_SCHEMA_VERSION,
        }
    ):
        raise ScienceContractError(
            "readiness executable contract is not the exact Gate A 1.2 manifest and unknown policy"
        )
    manifest_ref = readiness.get("capability_set_ref")
    manifest_matches = [
        definition
        for definition in definition_registry.get("definitions", [])
        if isinstance(definition, Mapping)
        and isinstance(manifest_ref, Mapping)
        and definition.get("definition_id") == manifest_ref.get("record_id")
    ]
    capability_projection = [
        {
            "capability_id": capability.get("capability_id"),
            "dimension_id": capability.get("dimension_id"),
            "required": capability.get("required"),
            "safety_critical": capability.get("safety_critical"),
            "weight": capability.get("weight"),
            "criterion_rule_id": capability.get("criterion", {})
            .get("rule_ref", {})
            .get("rule_id"),
            "threshold_operator": capability.get("criterion", {})
            .get("threshold", {})
            .get("operator"),
            "threshold_value": capability.get("criterion", {})
            .get("threshold", {})
            .get("value"),
        }
        for capability in readiness.get("capabilities", [])
        if isinstance(capability, Mapping)
    ]
    manifest_definition = manifest_matches[0] if len(manifest_matches) == 1 else None
    manifest_reference_valid = (
        isinstance(manifest_ref, Mapping)
        and manifest_ref.get("record_kind")
        == readiness_contract["capability_set_record_kind"]
        and manifest_ref.get("version") == SCIENCE_SCHEMA_VERSION
    )
    manifest_definition_valid = (
        isinstance(manifest_definition, Mapping)
        and manifest_definition.get("kind") == "capability_set"
        and manifest_definition.get("version") == SCIENCE_SCHEMA_VERSION
        and manifest_definition.get("owner_protocol_release_id")
        == PROTOCOL_RELEASE_ID
        and manifest_definition.get("synthetic_fixture_only") is True
        and manifest_definition.get("evidence_eligible") is False
        and manifest_definition.get("real_data_resolution_authorized") is False
        and instance.get("artifact_id")
        in manifest_definition.get("bound_artifact_ids", [])
        and manifest_definition.get("capability_contracts")
        == capability_projection
        and all(
            capability.get("criterion", {}).get("rule_ref")
            == expected_criterion_ref
            for capability in readiness.get("capabilities", [])
            if isinstance(capability, Mapping)
        )
    )
    manifest_pointer = (
        "/readiness/capabilities"
        if manifest_reference_valid and isinstance(manifest_definition, Mapping)
        else "/readiness/capability_set_ref"
    )
    add_if(
        output,
        not manifest_reference_valid or not manifest_definition_valid,
        "GA-READINESS-CAPABILITY-MANIFEST-BINDING",
        manifest_pointer,
        "readiness capability identities, roles, weights, criteria, and thresholds must exact-bind the artifact-bound protocol-owned synthetic capability manifest",
    )
    readiness_as_of_value = observed(readiness["as_of"])
    readiness_opens_value = observed(readiness["window"]["opens_at"])
    readiness_closes_value = observed(readiness["window"]["closes_at"])
    prior_values = (
        observed(instance["observation"]["available_at"]),
        observed(instance["belief"]["as_of"]),
        observed(instance["decision"]["decided_at"]),
    )
    readiness_temporal_invalid = any(
        value is None
        for value in (
            readiness_as_of_value,
            readiness_opens_value,
            readiness_closes_value,
            *prior_values,
        )
    )
    temporal_pointer = "/readiness/as_of/value"
    if not readiness_temporal_invalid:
        readiness_as_of = parse_time(str(readiness_as_of_value))
        readiness_opens = parse_time(str(readiness_opens_value))
        readiness_closes = parse_time(str(readiness_closes_value))
        prior_times = [parse_time(str(value)) for value in prior_values]
        if readiness_opens > readiness_closes:
            temporal_pointer = "/readiness/window"
            readiness_temporal_invalid = True
        elif not readiness_opens <= readiness_as_of <= readiness_closes:
            readiness_temporal_invalid = True
        elif any(value > readiness_as_of for value in prior_times):
            readiness_temporal_invalid = True
    add_if(
        output,
        readiness_temporal_invalid,
        "GA-READINESS-TEMPORAL-RECONCILIATION",
        temporal_pointer,
        "readiness time does not reconcile with its ordered assessment window and prior observed inputs",
    )
    capabilities = readiness["capabilities"]
    capability_ids = [item["capability_id"] for item in capabilities]
    dimension_ids = [item["dimension_id"] for item in capabilities]
    duplicate_pointer = "/readiness/capabilities"
    seen_capabilities: set[str] = set()
    seen_dimensions: set[str] = set()
    for index, capability in enumerate(capabilities):
        if capability["capability_id"] in seen_capabilities:
            duplicate_pointer = f"/readiness/capabilities/{index}/capability_id"
            break
        if capability["dimension_id"] in seen_dimensions:
            duplicate_pointer = f"/readiness/capabilities/{index}/dimension_id"
            break
        seen_capabilities.add(capability["capability_id"])
        seen_dimensions.add(capability["dimension_id"])
    add_if(
        output,
        len(set(capability_ids)) != len(capability_ids) or len(set(dimension_ids)) != len(dimension_ids),
        "GA-READINESS-CAPABILITY-DIMENSION",
        duplicate_pointer,
        "capability and dimension identifiers must each be unique",
    )
    unresolved: set[str] = set()
    observed_estimates: list[tuple[float, float]] = []
    all_required_met = True
    state_counts = {state: 0 for state in COVERAGE_STATES}
    for index, capability in enumerate(capabilities):
        estimate = capability["estimate"]
        state = estimate["state"]
        state_counts[state] = state_counts.get(state, 0) + 1
        disposition = capability["criterion_disposition"]
        expected = "unknown"
        value = observed(estimate)
        if value is not None:
            threshold = capability["criterion"]["threshold"]
            operator = threshold["operator"]
            bound = threshold["value"]
            comparisons = {
                "gt": float(value) > float(bound) and not close(value, bound),
                "gte": float(value) > float(bound) or close(value, bound),
                "lt": float(value) < float(bound) and not close(value, bound),
                "lte": float(value) < float(bound) or close(value, bound),
                "eq": close(value, bound),
            }
            expected = "met" if comparisons[operator] else "not_met"
            observed_estimates.append((float(capability["weight"]), float(value)))
        if disposition != expected:
            output.append(
                violation(
                    "GA-READINESS-CRITERION-MISMATCH",
                    f"/readiness/capabilities/{index}/criterion_disposition",
                    "criterion disposition is not derived from estimate, operator, and threshold",
                )
            )
        if value is None and (
            capability["required"]
            or capability["safety_critical"]
            or float(capability["weight"]) > 0.0
        ):
            unresolved.add(capability["capability_id"])
        if capability["required"] and expected != "met":
            all_required_met = False
    declared_unresolved = set(readiness["unresolved_capability_ids"])
    counts = readiness["coverage_counts"]
    coverage_mismatch = counts.get("total") != len(capabilities) or any(
        counts.get(state) != state_counts.get(state, 0) for state in COVERAGE_STATES
    )
    aggregate = readiness["aggregate"]
    aggregate_value = observed(aggregate["estimate"])
    weights = [float(item["weight"]) for item in capabilities]
    weight_sum_invalid = (
        readiness["aggregation"].get("weights_normalized") is not True
        or abs(sum(weights) - 1.0) > TOLERANCE
    )
    add_if(
        output,
        weight_sum_invalid,
        "GA-READINESS-AGGREGATION-MISMATCH",
        "/readiness/capabilities",
        "declared normalized readiness weights must sum to one independently of capability observability",
    )
    if unresolved:
        basis = set(aggregate["estimate"].get("basis_ids", []))
        unknown_invalid = (
            declared_unresolved != unresolved
            or coverage_mismatch
            or aggregate_value is not None
            or aggregate["disposition"] != "unknown"
            or basis != unresolved
        )
        add_if(
            output,
            unknown_invalid,
            "GA-READINESS-UNKNOWN-PROPAGATION",
            "/readiness/aggregate",
            "required unresolved capabilities must propagate an explicit unknown aggregate",
        )
    else:
        add_if(
            output,
            bool(declared_unresolved) or coverage_mismatch,
            "GA-READINESS-UNKNOWN-PROPAGATION",
            "/readiness/unresolved_capability_ids",
            "unresolved IDs and coverage must equal capability states",
        )
        mode = readiness["aggregation"]["mode"]
        expected_value = (
            sum(weight * value for weight, value in observed_estimates)
            if mode == "weighted_continuous"
            else (1.0 if all_required_met else 0.0)
        )
        invalid_aggregate = (
            aggregate_value is None
            or not close(aggregate_value, expected_value)
            or aggregate["disposition"] != ("ready" if all_required_met else "not_ready")
        )
        add_if(
            output,
            invalid_aggregate,
            "GA-READINESS-AGGREGATION-MISMATCH",
            "/readiness/aggregate/estimate/value",
            "observed readiness aggregate is not the declared normalized construction",
        )
    output.extend(
        recovery_violations(
            instance["recovery"],
            recovery_contract,
            definition_registry,
            instance.get("artifact_id"),
        )
    )
    return output


def recovery_violations(
    recovery: Mapping[str, Any],
    contract: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
    artifact_id: object,
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    expected_recovery_ref = {
        "rule_id": "reiyah.rule.recovery_event",
        "rule_kind": "reiyah.kind.recovery_criterion",
        "version": SCIENCE_SCHEMA_VERSION,
    }
    expected_censoring_ref = {
        "rule_id": "reiyah.rule.recovery_censoring",
        "rule_kind": "reiyah.kind.censoring_policy",
        "version": SCIENCE_SCHEMA_VERSION,
    }
    expected_competing_ref = {
        "rule_id": "reiyah.rule.recovery_competing",
        "rule_kind": "reiyah.kind.competing_policy",
        "version": SCIENCE_SCHEMA_VERSION,
    }
    expected_event_type_roles = [
        {"event_type": "reiyah.event_type.capability_restored", "role": "recovery"},
        {"event_type": "reiyah.event_type.observation_censored", "role": "censoring"},
        {"event_type": "reiyah.event_type.readiness_loss", "role": "competing"},
    ]
    if not (
        contract.get("event_selection")
        == "earliest_qualifying_inside_frozen_window"
        and contract.get("elapsed_time_origin") == "index_event"
        and contract.get("absence_in_valid_complete_window") == "right_censored"
        and contract.get("nonobserved_input_policy")
        == "propagate_explicit_nonobserved_or_invalid"
        and contract.get("no_qualifying_event_policy")
        == "right_censored_only_for_complete_valid_window"
        and contract.get("event_manifest_resolution_policy")
        == "exact_registry_event_members_completeness_and_artifact_binding"
        and contract.get("recovery_criterion_ref") == expected_recovery_ref
        and contract.get("censoring_policy_ref") == expected_censoring_ref
        and contract.get("competing_event_policy_ref") == expected_competing_ref
        and contract.get("event_type_role_bindings") == expected_event_type_roles
    ):
        raise ScienceContractError(
            "recovery executable contract has an unrecognized derivation operand"
        )
    classification_pointer = "/recovery/recovery_criterion"
    classification_invalid = recovery.get("recovery_criterion") != expected_recovery_ref
    if not classification_invalid and recovery.get("censoring_policy") != expected_censoring_ref:
        classification_invalid = True
        classification_pointer = "/recovery/censoring_policy"
    if not classification_invalid and recovery.get("competing_event_policy") != expected_competing_ref:
        classification_invalid = True
        classification_pointer = "/recovery/competing_event_policy"
    event_type_roles = {
        binding["event_type"]: binding["role"] for binding in expected_event_type_roles
    }
    for event_index, event in enumerate(recovery.get("events", [])):
        if not isinstance(event, Mapping):
            continue
        expected_role = event_type_roles.get(event.get("event_type"))
        if expected_role is None or event.get("role") != expected_role:
            classification_invalid = True
            classification_pointer = f"/recovery/events/{event_index}/event_type"
            break
    add_if(
        output,
        classification_invalid,
        "GA-RECOVERY-EVENT-CLASSIFICATION",
        classification_pointer,
        "recovery policy references and synthetic event type-to-role classifications must exact-bind the executable contract",
    )

    manifest_ref = recovery.get("event_manifest_ref")
    manifest_matches = [
        definition
        for definition in definition_registry.get("definitions", [])
        if isinstance(definition, Mapping)
        and isinstance(manifest_ref, Mapping)
        and definition.get("definition_id") == manifest_ref.get("record_id")
    ]
    manifest_definition = manifest_matches[0] if len(manifest_matches) == 1 else None
    event_projection = [
        {
            "event_id": event.get("event_id"),
            "event_type": event.get("event_type"),
            "role": event.get("role"),
        }
        for event in recovery.get("events", [])
        if isinstance(event, Mapping)
    ]
    completeness_value = observed(recovery.get("window_observation_complete"))
    complete_through = (
        observed(recovery.get("window", {}).get("closes_at"))
        if completeness_value is True
        else None
    )
    manifest_reference_valid = (
        isinstance(manifest_ref, Mapping)
        and manifest_ref.get("record_kind")
        == "reiyah.kind.recovery_event_manifest"
        and manifest_ref.get("version") == SCIENCE_SCHEMA_VERSION
    )
    manifest_definition_valid = (
        isinstance(manifest_definition, Mapping)
        and manifest_definition.get("kind") == "recovery_event_manifest"
        and manifest_definition.get("version") == SCIENCE_SCHEMA_VERSION
        and manifest_definition.get("owner_protocol_release_id")
        == PROTOCOL_RELEASE_ID
        and manifest_definition.get("synthetic_fixture_only") is True
        and manifest_definition.get("evidence_eligible") is False
        and manifest_definition.get("real_data_resolution_authorized") is False
        and artifact_id in manifest_definition.get("bound_artifact_ids", [])
        and manifest_definition.get("event_contracts") == event_projection
        and completeness_value in {True, False}
        and manifest_definition.get("window_observation_complete")
        is completeness_value
        and manifest_definition.get("complete_through") == complete_through
    )
    manifest_pointer = "/recovery/event_manifest_ref"
    if manifest_reference_valid and isinstance(manifest_definition, Mapping):
        if manifest_definition.get("event_contracts") != event_projection:
            manifest_pointer = "/recovery/events"
        elif (
            manifest_definition.get("window_observation_complete")
            is not completeness_value
            or manifest_definition.get("complete_through") != complete_through
        ):
            manifest_pointer = "/recovery/window_observation_complete"
    add_if(
        output,
        not manifest_reference_valid or not manifest_definition_valid,
        "GA-RECOVERY-EVENT-MANIFEST-BINDING",
        manifest_pointer,
        "recovery event identities, type roles, completeness, and complete-through boundary must exact-bind the artifact-bound protocol-owned synthetic event manifest",
    )
    absent_complete_disposition = contract["absence_in_valid_complete_window"]
    index_value = observed(recovery["index_event"]["occurred_at"])
    opens_value = observed(recovery["window"]["opens_at"])
    closes_value = observed(recovery["window"]["closes_at"])
    complete = observed(recovery["window_observation_complete"])
    outcome = recovery["outcome"]

    def exact_absent_outcome(disposition: str, reason: str) -> bool:
        qualifying_id = outcome.get("qualifying_event_id")
        elapsed = outcome.get("elapsed_seconds")
        return (
            outcome.get("disposition") == disposition
            and isinstance(qualifying_id, Mapping)
            and qualifying_id.get("state") == "absent"
            and qualifying_id.get("reason") == reason
            and isinstance(elapsed, Mapping)
            and elapsed.get("state") != "observed"
        )

    unresolved_event_time = any(
        event.get("role") in {"recovery", "censoring", "competing"}
        and observed(event.get("occurred_at")) is None
        for event in recovery["events"]
    )
    input_nonobserved = any(
        value is None for value in (index_value, opens_value, closes_value, complete)
    ) or unresolved_event_time
    if input_nonobserved:
        unknown_invalid = not exact_absent_outcome(
            "nonobserved", "input_nonobserved"
        )
        add_if(
            output,
            unknown_invalid,
            "GA-RECOVERY-INPUT-UNKNOWN-PROPAGATION",
            "/recovery/outcome",
            "non-observed or incomplete recovery-window inputs must propagate a non-observed outcome",
        )
        return output

    if complete is False:
        incomplete_invalid = not exact_absent_outcome(
            "nonobserved", "window_incomplete"
        )
        add_if(
            output,
            incomplete_invalid,
            "GA-RECOVERY-INPUT-UNKNOWN-PROPAGATION",
            "/recovery/outcome",
            "an incomplete recovery window must use the exact window-incomplete absent-event disposition",
        )
        return output

    index_time = parse_time(str(index_value))
    opens = parse_time(str(opens_value))
    closes = parse_time(str(closes_value))
    invalid_window = opens != index_time or closes < opens
    add_if(
        output,
        invalid_window
        and not exact_absent_outcome("invalid", "invalid_window"),
        "GA-RECOVERY-WINDOW-MISMATCH",
        "/recovery/outcome",
        "an invalid observed recovery window must propagate the exact invalid-window outcome",
    )
    if invalid_window:
        return output
    qualifying: list[tuple[datetime, Mapping[str, Any]]] = []
    for event_index, event in enumerate(recovery["events"]):
        time_value = observed(event["occurred_at"])
        if time_value is None:
            continue
        event_time = parse_time(str(time_value))
        if event["role"] in {"recovery", "censoring", "competing"}:
            if event_time < index_time or event_time < opens or event_time > closes:
                output.append(
                    violation(
                        "GA-RECOVERY-WINDOW-MISMATCH",
                        f"/recovery/events/{event_index}/occurred_at/value",
                        "qualifying event falls outside the inclusive frozen recovery window",
                    )
                )
            else:
                qualifying.append((event_time, event))
    qualifying.sort(key=lambda item: (item[0], item[1]["event_id"]))
    if qualifying:
        first_time = qualifying[0][0]
        tied = [event for event_time, event in qualifying if event_time == first_time]
        roles = {event["role"] for event in tied}
        if len(roles) > 1:
            add_if(
                output,
                not exact_absent_outcome("invalid", "ambiguous_event_tie"),
                "GA-RECOVERY-EVENT-DERIVATION",
                "/recovery/outcome",
                "an earliest cross-role event tie must propagate the exact ambiguous-event invalid outcome",
            )
            return output
        selected = tied[0]
        expected_disposition = {
            "recovery": "recovered",
            "censoring": "right_censored",
            "competing": "competing_event",
        }[selected["role"]]
        if selected["role"] == "censoring" and outcome["disposition"] != expected_disposition:
            output.append(
                violation(
                    "GA-RECOVERY-CENSORING-DISPOSITION",
                    "/recovery/outcome/disposition",
                    "censoring event cannot support recovered disposition",
                )
            )
        if selected["role"] == "competing" and outcome["disposition"] != expected_disposition:
            output.append(
                violation(
                    "GA-RECOVERY-COMPETING-EVENT",
                    "/recovery/outcome/disposition",
                    "competing event must produce competing-event disposition",
                )
            )
        event_id = observed(outcome["qualifying_event_id"])
        elapsed_measurement = outcome["elapsed_seconds"]
        elapsed = observed(elapsed_measurement)
        expected_elapsed = exact_elapsed_seconds(index_time, first_time)
        add_if(
            output,
            event_id != selected["event_id"],
            "GA-RECOVERY-EVENT-DERIVATION",
            "/recovery/outcome/qualifying_event_id/value",
            "outcome must bind the earliest qualifying event and exact elapsed duration",
        )
        add_if(
            output,
            elapsed is None
            or elapsed_measurement.get("unit") != "seconds"
            or not exact_decimal_equal(elapsed, expected_elapsed),
            "GA-RECOVERY-EVENT-DERIVATION",
            "/recovery/outcome/elapsed_seconds/value",
            "elapsed recovery time must derive from the selected event and index event",
        )
        add_if(
            output,
            outcome["disposition"] != expected_disposition,
            "GA-RECOVERY-EVENT-DERIVATION",
            "/recovery/outcome/disposition",
            "outcome disposition must derive from the selected event role",
        )
    else:
        qualifying_id = outcome.get("qualifying_event_id", {})
        elapsed_measurement = outcome.get("elapsed_seconds", {})
        elapsed = observed(elapsed_measurement)
        no_event_invalid = (
            outcome.get("disposition") != absent_complete_disposition
            or not isinstance(qualifying_id, Mapping)
            or qualifying_id.get("state") != "absent"
            or qualifying_id.get("reason") != "no_qualifying_event"
            or elapsed is None
            or elapsed_measurement.get("unit") != "seconds"
            or not exact_decimal_equal(
                elapsed, exact_elapsed_seconds(index_time, closes)
            )
        )
        add_if(
            output,
            no_event_invalid,
            "GA-RECOVERY-NO-EVENT-CENSORING",
            "/recovery/outcome",
            "a complete observed window with no qualifying event must be explicitly right censored at window close",
        )
    return output


def directed_descendants(start: str, edges: Sequence[Mapping[str, str]]) -> set[str]:
    children: dict[str, set[str]] = {}
    for edge in edges:
        children.setdefault(edge["from_node_id"], set()).add(edge["to_node_id"])
    output: set[str] = set()
    frontier = list(children.get(start, set()))
    while frontier:
        node = frontier.pop()
        if node in output:
            continue
        output.add(node)
        frontier.extend(children.get(node, set()))
    return output


def has_cycle(node_ids: set[str], edges: Sequence[Mapping[str, str]]) -> bool:
    children = {node: [] for node in node_ids}
    for edge in edges:
        if edge["from_node_id"] in children:
            children[edge["from_node_id"]].append(edge["to_node_id"])
    colors: dict[str, int] = {node: 0 for node in node_ids}

    def visit(node: str) -> bool:
        colors[node] = 1
        for child in children[node]:
            if colors.get(child) == 1 or (colors.get(child) == 0 and visit(child)):
                return True
        colors[node] = 2
        return False

    return any(colors[node] == 0 and visit(node) for node in sorted(node_ids))


def backdoor_open(
    treatment: str,
    outcome: str,
    adjusted: set[str],
    node_ids: set[str],
    edges: Sequence[Mapping[str, str]],
) -> bool:
    # Ancestral moral-graph d-separation in G with outgoing treatment edges removed.
    retained_edges = [edge for edge in edges if edge["from_node_id"] != treatment]
    parents: dict[str, set[str]] = {node: set() for node in node_ids}
    for edge in retained_edges:
        parents[edge["to_node_id"]].add(edge["from_node_id"])
    ancestors = {treatment, outcome, *adjusted}
    frontier = list(ancestors)
    while frontier:
        node = frontier.pop()
        for parent in parents.get(node, set()):
            if parent not in ancestors:
                ancestors.add(parent)
                frontier.append(parent)
    undirected: dict[str, set[str]] = {node: set() for node in ancestors}
    for edge in retained_edges:
        left, right = edge["from_node_id"], edge["to_node_id"]
        if left in ancestors and right in ancestors:
            undirected[left].add(right)
            undirected[right].add(left)
    for child in ancestors:
        child_parents = sorted(parent for parent in parents.get(child, set()) if parent in ancestors)
        for index, left in enumerate(child_parents):
            for right in child_parents[index + 1 :]:
                undirected[left].add(right)
                undirected[right].add(left)
    blocked = set(adjusted)
    if treatment in blocked or outcome in blocked:
        return True
    seen = set(blocked)
    frontier = [treatment]
    while frontier:
        node = frontier.pop()
        if node == outcome:
            return True
        if node in seen:
            continue
        seen.add(node)
        frontier.extend(sorted(undirected.get(node, set()) - seen))
    return False


def study_violations(
    instance: Mapping[str, Any],
    protocol_estimands: Sequence[Mapping[str, Any]],
    contract: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    output = lifecycle_violations(instance)
    if not (
        contract.get("identification_strategy") == "backdoor_adjustment"
        and contract.get("requires_pre_treatment") is True
        and contract.get("requires_observed") is True
        and contract.get("acyclicity_sufficient") is False
        and contract.get("query_binding")
        == "exact_treatment_outcome_estimand_graph_and_selected_set"
        and contract.get("selected_set_reconciliation")
        == "exact_query_selected_adjustment_ids"
        and contract.get("analysis_unit_id") == "reiyah.unit.synthetic-encounter"
        and contract.get("split_unit_id") == "reiyah.unit.subject"
        and isinstance(contract.get("analysis_unit_set_ref"), Mapping)
        and isinstance(contract.get("analysis_unit_member_ids"), list)
        and contract.get("split_partition_policy")
        == "ordered_exact_member_rows_pairwise_disjoint_complete_union"
        and contract.get("split_freeze_policy")
        == "every_manifest_strictly_before_first_outcome_access"
        and contract.get("stratification_input_policy")
        == "exact_observed_pre_treatment_graph_node_role_available_by_manifest_freeze"
        and isinstance(contract.get("prohibited_roles"), list)
    ):
        raise ScienceContractError(
            "causal executable contract has an unrecognized identification operand"
        )
    contract_prohibited_roles = list(contract["prohibited_roles"])
    control_prohibited_roles = instance["control_strategy"]["prohibited_roles"]
    prohibited_binding_invalid = control_prohibited_roles != contract_prohibited_roles
    add_if(
        output,
        prohibited_binding_invalid,
        "GA-CAUSAL-PROHIBITED-ADJUSTMENT",
        "/control_strategy/prohibited_roles",
        "the application prohibited-role list must exact-bind the executable causal contract",
    )
    chronology = instance["data_access_chronology"]
    design_frozen_at = parse_time(instance["design_frozen_at"])
    first_feature_access_at = parse_time(chronology["first_feature_access_at"])
    first_outcome_access_at = parse_time(chronology["first_outcome_access_at"])
    chronology_invalid = (
        instance["design_frozen_at"] != chronology["design_frozen_at"]
        or not (
            design_frozen_at < first_feature_access_at <= first_outcome_access_at
        )
        or any(
            parse_time(adjustment["frozen_at"]) > design_frozen_at
            for adjustment in instance["adjustment_sets"]
        )
    )
    add_if(
        output,
        chronology_invalid,
        "GA-STUDY-DESIGN-CHRONOLOGY",
        "/data_access_chronology",
        "design and adjustment freezes must exact-bind and precede feature and outcome access",
    )
    split_policy = instance["split_policy"]
    split_manifests = split_policy["split_manifests"]
    contract_analysis_unit_set_ref = dict(contract["analysis_unit_set_ref"])
    contract_analysis_unit_ids = list(contract["analysis_unit_member_ids"])
    registry_definitions = definition_registry.get("definitions", [])
    registry_definitions_by_id = {
        definition.get("definition_id"): definition
        for definition in registry_definitions
        if isinstance(definition, Mapping)
        and isinstance(definition.get("definition_id"), str)
    }
    analysis_unit_set_definition = registry_definitions_by_id.get(
        contract_analysis_unit_set_ref["record_id"]
    )
    analysis_unit_ids = split_policy["analysis_unit_ids"]
    unit_pointer = "/split_policy/analysis_unit_set_ref"
    if instance.get("unit_of_analysis") != contract["analysis_unit_id"]:
        unit_pointer = "/unit_of_analysis"
    elif split_policy.get("split_unit") != contract["split_unit_id"]:
        unit_pointer = "/split_policy/split_unit"
    analysis_unit_binding_invalid = (
        instance.get("unit_of_analysis") != contract["analysis_unit_id"]
        or split_policy.get("split_unit") != contract["split_unit_id"]
        or split_policy.get("analysis_unit_set_ref")
        != contract_analysis_unit_set_ref
        or analysis_unit_ids != contract_analysis_unit_ids
        or not isinstance(analysis_unit_set_definition, Mapping)
        or analysis_unit_set_definition.get("kind") != "analysis_unit_set"
        or analysis_unit_set_definition.get("version") != SCIENCE_SCHEMA_VERSION
        or analysis_unit_set_definition.get("owner_protocol_release_id")
        != PROTOCOL_RELEASE_ID
        or analysis_unit_set_definition.get("member_ids")
        != contract_analysis_unit_ids
    )
    add_if(
        output,
        analysis_unit_binding_invalid,
        "GA-CAUSAL-ANALYSIS-UNIT-SET-BINDING",
        unit_pointer
        if unit_pointer != "/split_policy/analysis_unit_set_ref"
        or split_policy.get("analysis_unit_set_ref")
        != contract_analysis_unit_set_ref
        else "/split_policy/analysis_unit_ids",
        "the application analysis and split units plus analysis-unit universe must exact-bind the executable contract and its protocol-owned synthetic set definition",
    )
    expected_split_bindings = (
        (
            "train",
            {
                "record_id": "reiyah.split.synthetic_train",
                "record_kind": "reiyah.kind.split",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        ),
        (
            "calibration",
            {
                "record_id": "reiyah.split.synthetic_calibration",
                "record_kind": "reiyah.kind.split",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        ),
        (
            "test",
            {
                "record_id": "reiyah.split.synthetic_test",
                "record_kind": "reiyah.kind.split",
                "version": SCIENCE_SCHEMA_VERSION,
            },
        ),
    )
    split_reference_invalid = len(split_manifests) != 3 or any(
        manifest.get("split_role") != expected_role
        or manifest.get("split_ref") != expected_ref
        for manifest, (expected_role, expected_ref) in zip(
            split_manifests, expected_split_bindings, strict=True
        )
    )
    split_reference_ids = [
        manifest.get("split_ref", {}).get("record_id")
        for manifest in split_manifests
    ]
    split_reference_invalid = split_reference_invalid or len(
        split_reference_ids
    ) != len(set(split_reference_ids))
    add_if(
        output,
        split_reference_invalid,
        "GA-CAUSAL-SPLIT-REFERENCE",
        "/split_policy/split_manifests",
        "split roles must exact-bind three distinct protocol-owned split identities",
    )
    member_rows = [manifest["member_ids"] for manifest in split_manifests]
    flattened_members = [member_id for members in member_rows for member_id in members]
    registry_split_member_rows = [
        registry_definitions_by_id.get(manifest["split_ref"]["record_id"], {}).get(
            "member_ids"
        )
        for manifest in split_manifests
    ]
    split_membership_invalid = (
        analysis_unit_binding_invalid
        or len(analysis_unit_ids) != len(set(analysis_unit_ids))
        or any(len(members) != len(set(members)) for members in member_rows)
        or len(flattened_members) != len(set(flattened_members))
        or set(flattened_members) != set(analysis_unit_ids)
        or member_rows != registry_split_member_rows
    )
    add_if(
        output,
        split_membership_invalid and not analysis_unit_binding_invalid,
        "GA-CAUSAL-SPLIT-MEMBERSHIP",
        "/split_policy/split_manifests",
        "split member sets must be unique, disjoint, and exactly complete for the declared analysis-unit universe",
    )
    split_freeze_invalid = any(
        parse_time(manifest["frozen_at"]) >= first_outcome_access_at
        for manifest in split_manifests
    )
    add_if(
        output,
        split_freeze_invalid,
        "GA-CAUSAL-SPLIT-FREEZE",
        "/split_policy/split_manifests",
        "every retained split manifest must freeze before first outcome access",
    )
    graph = instance["causal_graph"]
    nodes = graph["nodes"]
    edges = graph["edges"]
    node_map = {node["node_id"]: node for node in nodes}
    node_ids = set(node_map)
    treatment_nodes = [node for node in nodes if node.get("role") == "treatment"]
    outcome_nodes = [node for node in nodes if node.get("role") == "outcome"]
    endpoint_role_count_invalid = len(treatment_nodes) != 1 or len(outcome_nodes) != 1
    add_if(
        output,
        endpoint_role_count_invalid,
        "GA-CAUSAL-QUERY-ROLE",
        "/causal_graph/nodes",
        "the causal graph must declare exactly one treatment-role node and one outcome-role node",
    )
    allowed_stratification_roles = {
        "pre_treatment_confounder",
        "instrument",
        "other",
    }
    treatment_time = (
        treatment_nodes[0].get("time_order") if len(treatment_nodes) == 1 else None
    )
    stratification_invalid = False
    stratification_pointer = "/split_policy/split_manifests"
    for manifest_index, manifest in enumerate(split_manifests):
        for input_index, input_ref in enumerate(
            manifest["stratification_input_refs"]
        ):
            node = node_map.get(input_ref.get("node_id"))
            if not endpoint_role_count_invalid and (
                node is None
                or input_ref.get("node_role") != node.get("role")
                or node.get("role") not in allowed_stratification_roles
                or node.get("observability") != "observed"
                or parse_time(input_ref["available_at"])
                > parse_time(manifest["frozen_at"])
                or not isinstance(treatment_time, int)
                or not isinstance(node.get("time_order"), int)
                or node["time_order"] >= treatment_time
            ):
                stratification_invalid = True
                stratification_pointer = (
                    f"/split_policy/split_manifests/{manifest_index}"
                    f"/stratification_input_refs/{input_index}"
                )
                break
        if stratification_invalid:
            break
    add_if(
        output,
        stratification_invalid,
        "GA-CAUSAL-STRATIFICATION-INPUT",
        stratification_pointer,
        "stratification inputs must exact-resolve observed pre-treatment node roles and exclude outcomes and post-treatment operands",
    )
    malformed = len(node_ids) != len(nodes) or any(
        edge["from_node_id"] not in node_ids
        or edge["to_node_id"] not in node_ids
        or edge["from_node_id"] == edge["to_node_id"]
        for edge in edges
    )
    graph_structure_invalid = malformed or has_cycle(node_ids, edges)
    add_if(
        output,
        graph_structure_invalid,
        "GA-CAUSAL-DAG-CYCLE",
        "/causal_graph/edges",
        "causal graph must have unique nodes, valid endpoints, no self-edge, and no directed cycle",
    )
    temporal_pointer = "/causal_graph/edges"
    temporal_invalid = False
    node_index = {node["node_id"]: index for index, node in enumerate(nodes)}
    for edge in edges:
        if (
            edge["from_node_id"] in node_map
            and edge["to_node_id"] in node_map
            and node_map[edge["from_node_id"]]["time_order"]
            >= node_map[edge["to_node_id"]]["time_order"]
        ):
            temporal_invalid = True
            temporal_pointer = (
                f"/causal_graph/nodes/{node_index[edge['to_node_id']]}/time_order"
            )
            break
    add_if(
        output,
        temporal_invalid,
        "GA-CAUSAL-TEMPORAL-ORDER",
        temporal_pointer,
        "every directed edge must strictly increase declared time order",
    )
    adjustment_sets = {item["adjustment_set_id"]: item for item in instance["adjustment_sets"]}
    declared_adjustment_ids = [item["adjustment_set_id"] for item in instance["adjustment_sets"]]
    queried_adjustment_ids = [
        query.get("adjustment_set_id")
        for query in instance["identification_queries"]
        if isinstance(query.get("adjustment_set_id"), str)
    ]
    selected_adjustment_ids = instance["control_strategy"]["selected_adjustment_set_ids"]
    selected_invalid = (
        len(declared_adjustment_ids) != len(set(declared_adjustment_ids))
        or len(queried_adjustment_ids) != len(set(queried_adjustment_ids))
        or len(selected_adjustment_ids) != len(set(selected_adjustment_ids))
        or set(selected_adjustment_ids) != set(queried_adjustment_ids)
        or any(item not in adjustment_sets for item in selected_adjustment_ids)
    )
    add_if(
        output,
        selected_invalid,
        "GA-CAUSAL-SELECTED-SET-RECONCILIATION",
        "/control_strategy/selected_adjustment_set_ids",
        "selected adjustment sets must exactly equal the distinct resolved sets used by identification queries",
    )
    estimands = {item["estimand_id"]: item for item in instance["estimands"]}
    protocol_causal_ids = [
        item.get("estimand_id")
        for item in protocol_estimands
        if item.get("metric_class") == "causal_policy_effect"
    ]
    protocol_binding_invalid = (
        len(protocol_causal_ids) != 1
        or len(estimands) != len(instance["estimands"])
        or set(estimands) != set(protocol_causal_ids)
    )
    add_if(
        output,
        protocol_binding_invalid,
        "GA-CAUSAL-ESTIMAND-BINDING",
        "/estimands/0/estimand_id",
        "the study's causal estimand must resolve exactly to the protocol causal-policy-effect estimand",
    )
    prohibited_roles = set(contract_prohibited_roles)
    for query_index, query in enumerate(instance["identification_queries"]):
        if query["strategy"] != "backdoor":
            output.append(
                violation(
                    "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
                    f"/identification_queries/{query_index}/strategy",
                    "unsupported identification strategy cannot bypass the Gate A 1.2 back-door contract",
                )
            )
            continue
        treatment = query["treatment_node_id"]
        outcome = query["outcome_node_id"]
        treatment_role_invalid = (
            treatment not in node_map
            or node_map.get(treatment, {}).get("role") != "treatment"
        )
        outcome_role_invalid = (
            outcome not in node_map
            or node_map.get(outcome, {}).get("role") != "outcome"
        )
        add_if(
            output,
            treatment_role_invalid,
            "GA-CAUSAL-QUERY-ROLE",
            f"/identification_queries/{query_index}/treatment_node_id",
            "identification query endpoints must resolve to treatment and outcome graph-node roles",
        )
        add_if(
            output,
            outcome_role_invalid,
            "GA-CAUSAL-QUERY-ROLE",
            f"/identification_queries/{query_index}/outcome_node_id",
            "identification query endpoints must resolve to treatment and outcome graph-node roles",
        )
        estimand = estimands.get(query["estimand_id"])
        estimand_invalid = (
            estimand is None
            or estimand.get("treatment_node_id") != treatment
            or estimand.get("outcome_node_id") != outcome
        )
        add_if(
            output,
            estimand_invalid,
            "GA-CAUSAL-ESTIMAND-BINDING",
            f"/identification_queries/{query_index}/estimand_id",
            "each identification query must resolve and exactly bind its estimand endpoints",
        )
        query_prerequisite_invalid = (
            graph_structure_invalid
            or temporal_invalid
            or endpoint_role_count_invalid
            or treatment_role_invalid
            or outcome_role_invalid
            or estimand_invalid
            or selected_invalid
            or prohibited_binding_invalid
        )
        endpoint_observability_unknown = (
            not treatment_role_invalid
            and not outcome_role_invalid
            and (
                node_map[treatment].get("observability") != "observed"
                or node_map[outcome].get("observability") != "observed"
            )
        )
        if endpoint_observability_unknown:
            add_if(
                output,
                query.get("disposition") != "unknown",
                "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
                f"/identification_queries/{query_index}/disposition",
                "non-observed treatment or outcome identification operands must propagate an unknown disposition",
            )
            continue
        adjustment = adjustment_sets.get(query.get("adjustment_set_id"))
        if adjustment is None:
            if not query_prerequisite_invalid:
                output.append(
                    violation(
                        "GA-CAUSAL-BACKDOOR-OPEN",
                        f"/identification_queries/{query_index}/adjustment_set_id",
                        "backdoor query references no declared adjustment set",
                    )
                )
            continue
        descendants = directed_descendants(treatment, edges) if not query_prerequisite_invalid else set()
        adjusted = set(adjustment["node_ids"])
        eligibility_invalid = False
        ineligible_pointer = "/adjustment_sets"
        if not query_prerequisite_invalid:
            for adjusted_index, node_id in enumerate(adjustment["node_ids"]):
                node = node_map.get(node_id)
                if (
                    node is None
                    or node_id in {treatment, outcome}
                    or node_id in descendants
                    or node["role"] in prohibited_roles
                    or node["observability"] != "observed"
                    or node["time_order"] >= node_map[treatment]["time_order"]
                ):
                    eligibility_invalid = True
                    ineligible_pointer = (
                        f"/adjustment_sets/{list(adjustment_sets).index(query['adjustment_set_id'])}"
                        f"/node_ids/{adjusted_index}"
                    )
                    break
            add_if(
                output,
                eligibility_invalid,
                "GA-CAUSAL-PROHIBITED-ADJUSTMENT",
                ineligible_pointer,
                "adjustment set contains an ineligible, unobserved, post-treatment, or prohibited-role node",
            )
        if query_prerequisite_invalid or eligibility_invalid:
            continue
        open_path = backdoor_open(treatment, outcome, adjusted, node_ids, edges)
        add_if(
            output,
            query["disposition"] == "identified" and open_path,
            "GA-CAUSAL-BACKDOOR-OPEN",
            f"/identification_queries/{query_index}/disposition",
            "identified backdoor query is not d-separated by its eligible adjustment set",
        )
        expected_disposition = "not_identified" if open_path else "identified"
        add_if(
            output,
            query["disposition"] != expected_disposition
            and not (open_path and query["disposition"] == "identified"),
            "GA-CAUSAL-IDENTIFICATION-DISPOSITION",
            f"/identification_queries/{query_index}/disposition",
            "a complete back-door query disposition must be the exact result of eligible-set d-separation",
        )
    expected_estimand = {
        "estimand_id": "reiyah.estimand.synthetic-risk-difference",
        "population_rule_ref": {
            "rule_id": "reiyah.rule.synthetic_population",
            "rule_kind": "reiyah.kind.population_rule",
            "version": SCIENCE_SCHEMA_VERSION,
        },
        "treatment_node_id": "reiyah.node.intervention",
        "comparator": "No synthetic intervention under the same declared ODD.",
        "outcome_node_id": "reiyah.node.outcome",
        "outcome_window_rule_ref": {
            "rule_id": "reiyah.rule.outcome_window",
            "rule_kind": "reiyah.kind.outcome_window",
            "version": SCIENCE_SCHEMA_VERSION,
        },
        "effect_measure": "risk_difference",
        "intercurrent_event_rule_ref": {
            "rule_id": "reiyah.rule.intercurrent_events",
            "rule_kind": "reiyah.kind.intercurrent_rule",
            "version": SCIENCE_SCHEMA_VERSION,
        },
    }
    add_if(
        output,
        instance.get("estimands") != [expected_estimand],
        "GA-CAUSAL-ESTIMAND-BINDING",
        "/estimands/0",
        "the preregistered causal contrast must exact-bind population, treatment, comparator, outcome, window, effect measure, and intercurrent-event rule",
    )
    return output


def distribution_map(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    return {row["action_id"]: float(row["probability"]) for row in rows}


def ope_violations(
    instance: Mapping[str, Any],
    contract: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    output = lifecycle_violations(instance)
    normalization_tolerance = contract.get("normalization_tolerance")
    if not (
        isinstance(normalization_tolerance, (int, float))
        and not isinstance(normalization_tolerance, bool)
        and float(normalization_tolerance) > 0
        and contract.get("normalization_comparison") == "absolute_error_lte"
        and contract.get("relative_tolerance") == 0
        and contract.get("logged_propensity_reconciliation")
        == "exact_within_normalization_tolerance"
        and contract.get("support_scope")
        == "every_target_supported_action_per_history"
        and contract.get("weight_scope") == "cumulative_trajectory_by_horizon"
        and contract.get("ess_unit") == "trajectory"
        and contract.get("horizon_coverage")
        == "every_declared_horizon_exactly_once"
        and contract.get("terminal_reconciliation")
        == "exact_trajectory_terminal_or_max_horizon_truncation"
        and contract.get("weight_transformation_policy")
        == "declared_recomputed_before_normalization_and_ess"
        and contract.get("normalized_weight_policy")
        == "sum_one_when_positive_raw_weight_exists_otherwise_explicit_unknown"
        and contract.get("minimum_effective_sample_size") == 2
        and contract.get("ess_disposition_policy")
        == "exact_threshold_from_recomputed_ess"
        and contract.get("history_identity_policy") == "globally_unique_per_step"
        and contract.get("support_cell_identity_policy")
        == "exact_once_history_action"
        and contract.get("trajectory_set_record_kind")
        == "reiyah.kind.trajectory_set"
        and contract.get("trajectory_manifest_resolution_policy")
        == "exact_ordered_registry_members_bound_to_artifact"
        and contract.get("policy_table_record_kind")
        == "reiyah.kind.policy_table"
        and contract.get("policy_table_resolution_policy")
        == "exact_policy_role_history_action_probabilities_bound_to_artifact"
        and contract.get("behavior_policy_ref")
        == {
            "record_id": "reiyah.policy.synthetic_behavior",
            "record_kind": "reiyah.kind.policy",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and contract.get("target_policy_ref")
        == {
            "record_id": "reiyah.policy.synthetic_target",
            "record_kind": "reiyah.kind.policy",
            "version": SCIENCE_SCHEMA_VERSION,
        }
    ):
        raise ScienceContractError(
            "OPE executable contract has an unrecognized distribution or weight operand"
        )

    def ope_close(left: object, right: object) -> bool:
        return absolute_close(left, right, normalization_tolerance)

    minimum_effective_sample_size = float(
        contract["minimum_effective_sample_size"]
    )

    registry_definitions: dict[str, list[Mapping[str, Any]]] = {}
    for definition in definition_registry.get("definitions", []):
        if isinstance(definition, Mapping) and isinstance(
            definition.get("definition_id"), str
        ):
            registry_definitions.setdefault(
                definition["definition_id"], []
            ).append(definition)
    trajectories = instance["trajectories"]
    trajectory_ids = [trajectory["trajectory_id"] for trajectory in trajectories]
    trajectory_ref = instance.get("trajectory_set_ref")
    trajectory_matches = (
        registry_definitions.get(trajectory_ref.get("record_id"), [])
        if isinstance(trajectory_ref, Mapping)
        else []
    )
    trajectory_definition = (
        trajectory_matches[0] if len(trajectory_matches) == 1 else None
    )
    trajectory_members_resolve = all(
        len(registry_definitions.get(trajectory_id, [])) == 1
        and registry_definitions[trajectory_id][0].get("kind") == "trajectory"
        and registry_definitions[trajectory_id][0].get("version")
        == SCIENCE_SCHEMA_VERSION
        and registry_definitions[trajectory_id][0].get("owner_protocol_release_id")
        == PROTOCOL_RELEASE_ID
        for trajectory_id in trajectory_ids
    )
    trajectory_manifest_invalid = not (
        isinstance(trajectory_ref, Mapping)
        and trajectory_ref.get("record_kind")
        == contract["trajectory_set_record_kind"]
        and trajectory_ref.get("version") == SCIENCE_SCHEMA_VERSION
        and isinstance(trajectory_definition, Mapping)
        and trajectory_definition.get("kind") == "trajectory_set"
        and trajectory_definition.get("version") == SCIENCE_SCHEMA_VERSION
        and trajectory_definition.get("owner_protocol_release_id")
        == PROTOCOL_RELEASE_ID
        and trajectory_definition.get("synthetic_fixture_only") is True
        and trajectory_definition.get("evidence_eligible") is False
        and trajectory_definition.get("real_data_resolution_authorized") is False
        and instance.get("artifact_id")
        in trajectory_definition.get("bound_artifact_ids", [])
        and trajectory_definition.get("member_ids") == trajectory_ids
        and trajectory_members_resolve
    )
    add_if(
        output,
        trajectory_manifest_invalid,
        "GA-OPE-TRAJECTORY-MANIFEST-BINDING",
        "/trajectories"
        if isinstance(trajectory_definition, Mapping)
        else "/trajectory_set_ref",
        "trajectory identities must exact-bind the ordered artifact-bound protocol-owned synthetic trajectory manifest",
    )

    flattened_steps = [
        (trajectory_index, step_index, step)
        for trajectory_index, trajectory in enumerate(trajectories)
        for step_index, step in enumerate(trajectory["steps"])
    ]
    for policy_role, distribution_key in (
        ("behavior", "behavior_distribution"),
        ("target", "target_distribution"),
    ):
        policy = instance[f"{policy_role}_policy"]
        table_ref = policy.get("policy_table_ref")
        table_matches = (
            registry_definitions.get(table_ref.get("record_id"), [])
            if isinstance(table_ref, Mapping)
            else []
        )
        table_definition = table_matches[0] if len(table_matches) == 1 else None
        projected_rows = [
            {
                "history_id": step.get("history_id"),
                "probabilities": step.get(distribution_key),
            }
            for _, _, step in flattened_steps
        ]
        table_invalid = not (
            isinstance(table_ref, Mapping)
            and table_ref.get("record_kind") == contract["policy_table_record_kind"]
            and table_ref.get("version") == SCIENCE_SCHEMA_VERSION
            and isinstance(table_definition, Mapping)
            and table_definition.get("kind") == "policy_table"
            and table_definition.get("version") == SCIENCE_SCHEMA_VERSION
            and table_definition.get("owner_protocol_release_id")
            == PROTOCOL_RELEASE_ID
            and table_definition.get("synthetic_fixture_only") is True
            and table_definition.get("evidence_eligible") is False
            and table_definition.get("real_data_resolution_authorized") is False
            and instance.get("artifact_id")
            in table_definition.get("bound_artifact_ids", [])
            and table_definition.get("policy_ref")
            == contract[f"{policy_role}_policy_ref"]
            and policy.get("policy_ref") == contract[f"{policy_role}_policy_ref"]
            and table_definition.get("policy_role") == policy_role
            and table_definition.get("action_space_id")
            == policy.get("action_space", {}).get("action_space_id")
            and table_definition.get("action_ids")
            == policy.get("action_space", {}).get("action_ids")
            and table_definition.get("history_probability_rows") == projected_rows
        )
        table_pointer = f"/{policy_role}_policy/policy_table_ref"
        if isinstance(table_definition, Mapping) and table_definition.get(
            "history_probability_rows"
        ) != projected_rows:
            first_mismatch = next(
                (
                    (trajectory_index, step_index)
                    for row_index, (trajectory_index, step_index, _) in enumerate(
                        flattened_steps
                    )
                    if row_index >= len(
                        table_definition.get("history_probability_rows", [])
                    )
                    or table_definition.get("history_probability_rows", [])[row_index]
                    != projected_rows[row_index]
                ),
                (0, 0),
            )
            table_pointer = (
                f"/trajectories/{first_mismatch[0]}/steps/{first_mismatch[1]}/"
                f"{distribution_key}"
            )
        add_if(
            output,
            table_invalid,
            "GA-OPE-POLICY-TABLE-BINDING",
            table_pointer,
            "each per-history policy distribution must exact-bind the artifact-bound protocol-owned synthetic table selected for its behavior or target role",
        )

    behavior_space = instance["behavior_policy"]["action_space"]
    target_space = instance["target_policy"]["action_space"]
    actions = list(behavior_space["action_ids"])
    action_set = set(actions)
    maximum_steps = instance["horizon"]["maximum_steps"]
    construction = instance["weight_construction"]
    transformation = construction["transformation"]
    clipping = construction["clipping"]
    clip_threshold = clipping.get("threshold")
    transformation_contract_invalid = (
        transformation == "none"
        and (clipping.get("enabled") is not False or clip_threshold is not None)
    ) or (
        transformation == "upper_clip"
        and (
            clipping.get("enabled") is not True
            or isinstance(clip_threshold, bool)
            or not isinstance(clip_threshold, (int, float))
            or float(clip_threshold) <= 0.0
        )
    )
    add_if(
        output,
        transformation_contract_invalid,
        "GA-OPE-WEIGHT-TRANSFORMATION",
        "/weight_construction",
        "weight transformation and clipping operands must form the exact declared construction",
    )
    global_binding_invalid = (
        len(action_set) != len(actions)
        or behavior_space != target_space
        or instance["behavior_policy"]["information_set_schema_ref"]
        != instance["target_policy"]["information_set_schema_ref"]
    )
    outcome_at = parse_time(instance["estimator_selection"]["first_outcome_accessed_at"])
    top_freeze_invalid = parse_time(instance["frozen_at"]) >= outcome_at
    add_if(
        output,
        top_freeze_invalid,
        "GA-OPE-HISTORY-INFORMATION-SET",
        "/frozen_at",
        "the OPE contract and every policy information set must be frozen before first outcome access",
    )
    trajectory_ids = [trajectory["trajectory_id"] for trajectory in trajectories]
    history_ids = [
        step["history_id"]
        for trajectory in trajectories
        for step in trajectory["steps"]
    ]
    information_set_ids = [
        step["information_set"]["information_set_id"]
        for trajectory in trajectories
        for step in trajectory["steps"]
    ]
    identity_invalid = (
        len(trajectory_ids) != len(set(trajectory_ids))
        or len(history_ids) != len(set(history_ids))
        or len(information_set_ids) != len(set(information_set_ids))
    )
    add_if(
        output,
        identity_invalid,
        "GA-OPE-HISTORY-INFORMATION-SET",
        "/trajectories",
        "trajectory, history, and information-set identifiers must be globally unique before aggregation",
    )
    support_rows: dict[tuple[str, str], tuple[float, float, bool]] = {}
    trajectory_transformed_weights: list[list[float]] = []
    for trajectory_index, trajectory in enumerate(trajectories):
        steps = trajectory["steps"]
        observed_horizon = trajectory["observed_horizon"]
        maximum_invalid = len(steps) > maximum_steps or observed_horizon > maximum_steps
        observed_horizon_invalid = observed_horizon != len(steps)
        step_indexes = [step["step_index"] for step in steps]
        step_index_invalid = step_indexes != list(range(len(steps)))
        add_if(
            output,
            maximum_invalid,
            "GA-OPE-STEP-HORIZON-COMPLETENESS",
            "/horizon/maximum_steps",
            "trajectory steps must be contiguous and exactly match the observed horizon within the maximum horizon",
        )
        add_if(
            output,
            observed_horizon_invalid,
            "GA-OPE-STEP-HORIZON-COMPLETENESS",
            f"/trajectories/{trajectory_index}/observed_horizon",
            "trajectory steps must be contiguous and exactly match the observed horizon within the maximum horizon",
        )
        first_bad_step = next(
            (
                index
                for index, declared in enumerate(step_indexes)
                if declared != index
            ),
            0,
        )
        add_if(
            output,
            step_index_invalid,
            "GA-OPE-STEP-HORIZON-COMPLETENESS",
            f"/trajectories/{trajectory_index}/steps/{first_bad_step}/step_index",
            "trajectory steps must be contiguous and exactly match the observed horizon within the maximum horizon",
        )
        terminal_disposition = trajectory["termination_disposition"]
        for step_index, step in enumerate(steps[:-1]):
            add_if(
                output,
                step["terminal"] is not False,
                "GA-OPE-TERMINAL-COMPLETENESS",
                f"/trajectories/{trajectory_index}/steps/{step_index}/terminal",
                "terminal flags must exactly reconcile with terminal-event or maximum-horizon truncation disposition",
            )
        final_terminal_invalid = (
            terminal_disposition == "terminal_event" and steps[-1]["terminal"] is not True
        ) or (
            terminal_disposition == "maximum_horizon_truncation"
            and (steps[-1]["terminal"] is not False or observed_horizon != maximum_steps)
        )
        add_if(
            output,
            final_terminal_invalid,
            "GA-OPE-TERMINAL-COMPLETENESS",
            f"/trajectories/{trajectory_index}/steps/{len(steps) - 1}/terminal",
            "terminal flags must exactly reconcile with terminal-event or maximum-horizon truncation disposition",
        )

        prior_steps: list[dict[str, object]] = []
        prior_information_freeze: datetime | None = None
        for step_index, step in enumerate(steps):
            information = step["information_set"]
            information_freeze = parse_time(information["frozen_at"])
            expected_item_ids = {str(item["logged_action_id"]) for item in prior_steps}
            items = information["items"]
            actual_item_ids = {
                item.get("record_id")
                for item in items
                if isinstance(item, Mapping)
                and item.get("record_kind") == "reiyah.kind.prior_action"
                and item.get("version") == SCIENCE_SCHEMA_VERSION
            }
            information_invalid = (
                step.get("information_set_schema_ref")
                != instance["behavior_policy"]["information_set_schema_ref"]
                or step.get("information_set_schema_ref")
                != instance["target_policy"]["information_set_schema_ref"]
                or step.get("history_prefix") != prior_steps
                or len(actual_item_ids) != len(items)
                or actual_item_ids != expected_item_ids
                or information_freeze >= outcome_at
                or (
                    prior_information_freeze is not None
                    and information_freeze <= prior_information_freeze
                )
            )
            add_if(
                output,
                information_invalid,
                "GA-OPE-HISTORY-INFORMATION-SET",
                f"/trajectories/{trajectory_index}/steps/{step_index}/history_prefix",
                "the step information set does not exact-bind its schema, ordered history prefix, prior-action set, and outcome-blind freeze chronology",
            )
            prior_steps.append(
                {
                    "step_index": step["step_index"],
                    "logged_action_id": step["logged_action_id"],
                }
            )
            prior_information_freeze = information_freeze

        cumulative = 1.0
        transformed_weights: list[float] = []
        for step_index, step in enumerate(steps):
            pointer = f"/trajectories/{trajectory_index}/steps/{step_index}"
            behavior_rows = step["behavior_distribution"]
            target_rows = step["target_distribution"]
            behavior = distribution_map(behavior_rows)
            target = distribution_map(target_rows)
            distribution_invalid = (
                global_binding_invalid
                or len(behavior) != len(behavior_rows)
                or len(target) != len(target_rows)
                or set(behavior) != action_set
                or set(target) != action_set
                or any(not math.isfinite(value) or value < 0 or value > 1 for value in [*behavior.values(), *target.values()])
                or not ope_close(sum(behavior.values()), 1.0)
                or not ope_close(sum(target.values()), 1.0)
                or step["logged_action_id"] not in action_set
            )
            add_if(
                output,
                distribution_invalid,
                "GA-OPE-ACTION-DISTRIBUTION",
                f"{pointer}/behavior_distribution",
                "behavior and target distributions must exactly cover the common action space and sum to one",
            )
            if distribution_invalid:
                continue
            action = step["logged_action_id"]
            behavior_logged = behavior[action]
            target_logged = target[action]
            logged_invalid = (
                behavior_logged <= 0
                or not ope_close(step["behavior_logged_propensity"], behavior_logged)
                or not ope_close(step["target_logged_propensity"], target_logged)
            )
            add_if(
                output,
                logged_invalid,
                "GA-OPE-LOGGED-PROPENSITY",
                f"{pointer}/behavior_logged_propensity",
                "logged propensities must equal row probabilities and behavior propensity must be positive",
            )
            expected_ratio = target_logged / behavior_logged if behavior_logged > 0 else math.nan
            ratio_invalid = not math.isfinite(expected_ratio) or not ope_close(
                step["step_importance_ratio"], expected_ratio
            )
            add_if(
                output,
                ratio_invalid,
                "GA-OPE-STEP-RATIO",
                f"{pointer}/step_importance_ratio",
                "step ratio must equal target logged propensity divided by positive behavior propensity",
            )
            cumulative *= expected_ratio
            cumulative_invalid = not ope_close(step["cumulative_importance_weight"], cumulative)
            add_if(
                output,
                cumulative_invalid,
                "GA-OPE-CUMULATIVE-WEIGHT",
                f"{pointer}/cumulative_importance_weight",
                "cumulative importance weight must equal the product of all ratios through this step",
            )
            expected_transformed = (
                cumulative
                if transformation == "none" or not isinstance(clip_threshold, (int, float))
                else min(cumulative, float(clip_threshold))
            )
            transformed_invalid = not ope_close(
                step["transformed_cumulative_importance_weight"], expected_transformed
            )
            add_if(
                output,
                transformed_invalid,
                "GA-OPE-WEIGHT-TRANSFORMATION",
                f"{pointer}/transformed_cumulative_importance_weight",
                "transformed cumulative weight must equal the declared none or upper-clip transformation",
            )
            transformed_weights.append(expected_transformed)
            for action_id in actions:
                support_rows[(step["history_id"], action_id)] = (
                    behavior[action_id],
                    target[action_id],
                    target[action_id] <= 0 or behavior[action_id] > 0,
                )
        add_if(
            output,
            not ope_close(trajectory["final_cumulative_weight"], cumulative),
            "GA-OPE-CUMULATIVE-WEIGHT",
            f"/trajectories/{trajectory_index}/final_cumulative_weight",
            "final cumulative weight must equal the final step cumulative weight",
        )
        final_transformed = transformed_weights[-1] if transformed_weights else math.nan
        add_if(
            output,
            not math.isfinite(final_transformed)
            or not ope_close(trajectory["final_transformed_cumulative_weight"], final_transformed),
            "GA-OPE-WEIGHT-TRANSFORMATION",
            f"/trajectories/{trajectory_index}/final_transformed_cumulative_weight",
            "final transformed weight must equal the final step transformed cumulative weight",
        )
        trajectory_transformed_weights.append(transformed_weights)
    assessment = instance["support_assessment"]
    required_cells = assessment["required_cells"]
    unsupported_cells = assessment["unsupported_cells"]
    required_keys = [(cell["history_id"], cell["action_id"]) for cell in required_cells]
    unsupported_keys = [
        (cell["history_id"], cell["action_id"]) for cell in unsupported_cells
    ]
    support_identity_invalid = (
        len(required_keys) != len(set(required_keys))
        or len(unsupported_keys) != len(set(unsupported_keys))
    )
    declared_cells: dict[tuple[str, str], tuple[float, float, bool]] = {}
    for cell in required_cells:
        declared_cells[(cell["history_id"], cell["action_id"])] = (
            float(cell["behavior_probability"]),
            float(cell["target_probability"]),
            bool(cell["supported"]),
        )
    support_mismatch = support_identity_invalid or set(declared_cells) != set(support_rows)
    if not support_mismatch:
        support_mismatch = any(
            not ope_close(declared_cells[key][0], expected[0])
            or not ope_close(declared_cells[key][1], expected[1])
            or declared_cells[key][2] != expected[2]
            for key, expected in support_rows.items()
        )
    unsupported = sorted(key for key, value in support_rows.items() if not value[2])
    declared_unsupported = sorted(
        (item["history_id"], item["action_id"])
        for item in unsupported_cells
    )
    support_mismatch = support_mismatch or declared_unsupported != unsupported or (
        assessment["support_disposition"] == "supported"
    ) != (not unsupported)
    add_if(
        output,
        support_mismatch,
        "GA-OPE-HISTORY-SUPPORT",
        "/support_assessment",
        "required history-action support cells and positivity disposition do not reconcile",
    )
    weight_set_id = construction["weight_set_id"]
    records = instance["effective_sample_size_by_horizon"]
    record_horizons = [record["horizon_index"] for record in records]
    expected_horizons = set(range(maximum_steps))
    horizon_coverage_invalid = (
        len(record_horizons) != len(set(record_horizons))
        or set(record_horizons) != expected_horizons
        or len(trajectory_transformed_weights) != len(instance["trajectories"])
        or any(not weights for weights in trajectory_transformed_weights)
    )
    add_if(
        output,
        horizon_coverage_invalid,
        "GA-OPE-ESS-HORIZON-COVERAGE",
        "/effective_sample_size_by_horizon",
        "ESS rows must cover every declared horizon exactly once with every trajectory represented",
    )
    record_by_horizon = {record["horizon_index"]: (index, record) for index, record in enumerate(records)}
    normalization = construction["normalization"]
    for horizon in range(maximum_steps):
        if horizon not in record_by_horizon:
            continue
        index, record = record_by_horizon[horizon]
        weights = [
            values[horizon] if horizon < len(values) else values[-1]
            for values in trajectory_transformed_weights
            if values
        ]
        total = sum(weights)
        squares = sum(weight * weight for weight in weights)
        declared_ess = observed(record["kish_effective_sample_size"])
        base_invalid = (
            record["weight_set_id"] != weight_set_id
            or record["included_trajectory_count"] != len(weights)
            or not ope_close(record["sum_cumulative_weights"], total)
            or not ope_close(record["sum_squared_cumulative_weights"], squares)
        )
        if normalization == "none":
            normalization_denominator: float | None = 1.0
            normalized_total: float | None = total
        elif total > 0.0:
            normalization_denominator = total
            normalized_total = 1.0
        else:
            normalization_denominator = None
            normalized_total = None
        declared_normalized_total = observed(record["normalized_weight_sum"])
        normalization_invalid = (
            record["normalization_mode"] != normalization
            or (
                normalization_denominator is None
                and record["normalization_denominator"] is not None
            )
            or (
                normalization_denominator is not None
                and not ope_close(record["normalization_denominator"], normalization_denominator)
            )
            or (
                normalized_total is None
                and declared_normalized_total is not None
            )
            or (
                normalized_total is not None
                and (declared_normalized_total is None or not ope_close(declared_normalized_total, normalized_total))
            )
        )
        add_if(
            output,
            normalization_invalid,
            "GA-OPE-WEIGHT-NORMALIZATION",
            f"/effective_sample_size_by_horizon/{index}/normalization_mode",
            "per-horizon normalization mode, denominator, and normalized sum must reconcile with transformed weights",
        )
        if squares == 0.0:
            invalid = base_invalid or declared_ess is not None or record["disposition"] != "undefined_all_zero"
            add_if(
                output,
                invalid,
                "GA-OPE-ESS-ALL-ZERO",
                f"/effective_sample_size_by_horizon/{index}",
                "all-zero cumulative weights require undefined non-observed Kish ESS",
            )
        else:
            expected_ess = total * total / squares
            expected_disposition = (
                "sufficient"
                if expected_ess >= minimum_effective_sample_size
                else "insufficient"
            )
            invalid = (
                base_invalid
                or declared_ess is None
                or not ope_close(declared_ess, expected_ess)
                or record["disposition"] != expected_disposition
            )
            add_if(
                output,
                invalid,
                "GA-OPE-ESS-CUMULATIVE",
                f"/effective_sample_size_by_horizon/{index}/kish_effective_sample_size/value",
                "Kish ESS must use one cumulative trajectory weight per declared horizon",
            )
    horizon_ids = set(record_horizons)
    selection = instance["estimator_selection"]
    selected_at = parse_time(selection["selected_at"])
    add_if(
        output,
        selected_at >= outcome_at,
        "GA-OPE-ESTIMATOR-SELECTION-TIME",
        "/estimator_selection/selected_at",
        "estimator selection must be strictly outcome blind",
    )
    estimators = {item["estimator_id"]: item for item in instance["estimators"]}
    candidate_ids = set(selection["candidate_estimator_ids"])
    selected_ids = set(selection["selected_estimator_ids"])
    estimator_invalid = candidate_ids != set(estimators) or not selected_ids.issubset(candidate_ids)
    estimator_pointer = "/estimators"
    for estimator_index, (estimator_id, estimator) in enumerate(estimators.items()):
        allowed_disposition = "selected" if estimator_id in selected_ids else "sensitivity_only"
        if (
            estimator["weight_set_id"] != weight_set_id
            or estimator["horizon_index"] not in horizon_ids
            or estimator["selection_disposition"] != allowed_disposition
            or observed(estimator["estimate"]) is not None
            or observed(estimator["uncertainty"]["lower"]) is not None
            or observed(estimator["uncertainty"]["upper"]) is not None
        ):
            estimator_invalid = True
            estimator_pointer = f"/estimators/{estimator_index}/weight_set_id"
            break
    add_if(
        output,
        estimator_invalid,
        "GA-OPE-ESTIMATOR-BINDING",
        estimator_pointer,
        "estimators must bind declared candidates, selection, horizon, and cumulative weight set",
    )
    return output


def measurement_count(section: Mapping[str, Any], key: str) -> int | float | None:
    value = observed(section[key])
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def derived_rate_valid(measurement: Mapping[str, Any], numerator: float, denominator: float) -> bool:
    value = observed(measurement)
    if denominator == 0:
        return value is None
    return value is not None and close(value, numerator / denominator)


def joint_violations(
    instance: Mapping[str, Any],
    contracts: Mapping[str, Mapping[str, Any]],
    definition_registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    output = lifecycle_violations(instance)
    joint_contract = contracts[
        "reiyah.executable-contract.joint-silent-miss-identifiability"
    ]
    joint_cell_names = list(joint_contract.get("common_opportunity_cells", []))
    if not (
        joint_cell_names
        == ["both_miss", "human_only_miss", "automation_only_miss", "neither_miss"]
        and joint_contract.get("marginal_derivation")
        == "exact_from_disjoint_common_opportunity_cells"
        and joint_contract.get("identifiability_policy")
        == "observed_common_cells_or_nonidentifiable"
        and joint_contract.get("joint_unknown_propagation")
        == "nonobserved_operand_forces_nonidentified_nonobserved_summary"
        and joint_contract.get("opportunity_set_record_kind")
        == "reiyah.kind.opportunity_set"
        and joint_contract.get("opportunity_manifest_resolution_policy")
        == "exact_ordered_registry_rows_bound_to_artifact"
        and joint_contract.get("opportunity_set_ids")
        == [
            "reiyah.opportunity-set.synthetic-joint-observed",
            "reiyah.opportunity-set.synthetic-joint-nonobserved",
            "reiyah.opportunity-set.synthetic-joint-empty",
        ]
        and joint_contract.get("opportunity_rule_ref")
        == {
            "rule_id": "reiyah.rule.joint_miss_opportunity",
            "rule_kind": "reiyah.kind.event_rule",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and joint_contract.get("object_ref")
        == {
            "record_id": "reiyah.object.synthetic_vehicle",
            "record_kind": "reiyah.kind.vehicle_object",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and joint_contract.get("human_channel_ref")
        == {
            "record_id": "reiyah.channel.synthetic_human_observation",
            "record_kind": "reiyah.kind.observation_channel",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and joint_contract.get("automation_channel_ref")
        == {
            "record_id": "reiyah.channel.synthetic_automation_observation",
            "record_kind": "reiyah.kind.observation_channel",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and joint_contract.get("warning_rule_ref")
        == {
            "rule_id": "reiyah.rule.joint_warning_observation",
            "rule_kind": "reiyah.kind.event_rule",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and joint_contract.get("fallback_rule_ref")
        == {
            "rule_id": "reiyah.rule.joint_fallback_observation",
            "rule_kind": "reiyah.kind.event_rule",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and joint_contract.get("clock_id") == "reiyah.clock.synthetic-utc"
        and joint_contract.get("window_id")
        == "reiyah.window.joint-opportunity-001"
        and joint_contract.get("row_derivation_policy")
        == "exact_reference_validity_channel_warning_fallback_rows_to_disjoint_cells"
        and joint_contract.get("silent_joint_miss_policy")
        == "both_channels_miss_and_warning_not_issued_and_fallback_not_activated"
    ):
        raise ScienceContractError(
            "joint silent-miss executable contract has an unrecognized operand"
        )
    ood_contract = contracts["reiyah.executable-contract.ood-population-partition"]
    ood_cell_names = list(ood_contract.get("joint_axis_cells", []))
    if not (
        list(ood_contract.get("states", [])) == list(COVERAGE_STATES)
        and ood_contract.get("disjoint_required") is True
        and ood_contract.get("exhaustive_required") is True
        and ood_contract.get("derived_rates_required") is True
        and ood_contract.get("reference_detector_axes_disjoint") is True
        and ood_contract.get("unknown_axis_policy")
        == "retain_unknowns_as_atomic_partition_cells"
        and len(ood_cell_names) == 9
        and len(set(ood_cell_names)) == 9
    ):
        raise ScienceContractError(
            "OOD population executable contract has an unrecognized operand"
        )
    joint = instance["joint_silent_miss"]
    registry_definitions: dict[str, list[Mapping[str, Any]]] = {}
    for definition in definition_registry.get("definitions", []):
        if isinstance(definition, Mapping) and isinstance(
            definition.get("definition_id"), str
        ):
            registry_definitions.setdefault(
                definition["definition_id"], []
            ).append(definition)

    opportunity_ref = joint.get("opportunity_set_ref")
    opportunity_matches = (
        registry_definitions.get(opportunity_ref.get("record_id"), [])
        if isinstance(opportunity_ref, Mapping)
        else []
    )
    opportunity_definition = (
        opportunity_matches[0] if len(opportunity_matches) == 1 else None
    )
    opportunity_rows = joint.get("opportunity_rows", [])
    opportunity_ids = [row.get("opportunity_id") for row in opportunity_rows]
    manifest_invalid = not (
        isinstance(opportunity_ref, Mapping)
        and opportunity_ref.get("record_kind")
        == joint_contract["opportunity_set_record_kind"]
        and opportunity_ref.get("version") == SCIENCE_SCHEMA_VERSION
        and opportunity_ref.get("record_id")
        in joint_contract["opportunity_set_ids"]
        and isinstance(opportunity_definition, Mapping)
        and opportunity_definition.get("kind") == "opportunity_set"
        and opportunity_definition.get("version") == SCIENCE_SCHEMA_VERSION
        and opportunity_definition.get("owner_protocol_release_id")
        == PROTOCOL_RELEASE_ID
        and opportunity_definition.get("synthetic_fixture_only") is True
        and opportunity_definition.get("evidence_eligible") is False
        and opportunity_definition.get("real_data_resolution_authorized") is False
        and instance.get("artifact_id")
        in opportunity_definition.get("bound_artifact_ids", [])
        and opportunity_definition.get("member_ids") == opportunity_ids
        and opportunity_definition.get("object_ref")
        == joint_contract["object_ref"]
        and opportunity_definition.get("opportunity_window")
        == joint.get("opportunity_window")
        and opportunity_definition.get("opportunity_contracts")
        == opportunity_rows
    )
    add_if(
        output,
        manifest_invalid,
        "GA-JOINT-OPPORTUNITY-MANIFEST-BINDING",
        "/joint_silent_miss/opportunity_set_ref"
        if not isinstance(opportunity_definition, Mapping)
        or instance.get("artifact_id")
        not in opportunity_definition.get("bound_artifact_ids", [])
        else "/joint_silent_miss/opportunity_rows",
        "opportunity identities and rows must exact-bind the ordered artifact-bound protocol-owned synthetic manifest",
    )

    opportunity_window = joint.get("opportunity_window", {})
    window_open = parse_time(opportunity_window.get("opened_at"))
    window_close = parse_time(opportunity_window.get("closed_at"))
    duplicate_opportunity_ids = len(opportunity_ids) != len(set(opportunity_ids))
    row_binding_invalid = (
        joint.get("opportunity_rule_ref") != joint_contract["opportunity_rule_ref"]
        or opportunity_window.get("clock_id") != joint_contract["clock_id"]
        or opportunity_window.get("window_id") != joint_contract["window_id"]
        or duplicate_opportunity_ids
    )
    row_binding_pointer = (
        "/joint_silent_miss/opportunity_rows"
        if duplicate_opportunity_ids
        else "/joint_silent_miss/opportunity_window"
    )
    chronology_invalid = window_open > window_close
    chronology_pointer = "/joint_silent_miss/opportunity_window/closed_at"
    previous_time: datetime | None = None
    expected_cells = {key: 0 for key in joint_cell_names}
    unknown_cells: set[str] = set()
    summary_unknown = False
    expected_silent_misses = 0
    silent_row_invalid = False
    silent_pointer = "/joint_silent_miss/joint_misses"

    for row_index, row in enumerate(opportunity_rows):
        row_pointer = f"/joint_silent_miss/opportunity_rows/{row_index}"
        row_binding = (
            row.get("object_ref") == joint_contract["object_ref"]
            and row.get("clock_id") == joint_contract["clock_id"]
            and row.get("window_id") == joint_contract["window_id"]
            and row.get("human_channel", {}).get("channel_ref")
            == joint_contract["human_channel_ref"]
            and row.get("automation_channel", {}).get("channel_ref")
            == joint_contract["automation_channel_ref"]
            and row.get("warning", {}).get("rule_ref")
            == joint_contract["warning_rule_ref"]
            and row.get("fallback", {}).get("rule_ref")
            == joint_contract["fallback_rule_ref"]
        )
        if not row_binding and not row_binding_invalid:
            row_binding_invalid = True
            row_binding_pointer = row_pointer

        occurred_at_value = observed(row.get("occurred_at", {}))
        occurred_at = (
            parse_time(occurred_at_value)
            if isinstance(occurred_at_value, str)
            else None
        )
        if occurred_at is not None:
            if (
                occurred_at < window_open
                or occurred_at > window_close
                or (previous_time is not None and occurred_at <= previous_time)
            ) and not chronology_invalid:
                chronology_invalid = True
                chronology_pointer = f"{row_pointer}/occurred_at"
            previous_time = occurred_at

        human_outcome = observed(row.get("human_channel", {}).get("outcome", {}))
        automation_outcome = observed(
            row.get("automation_channel", {}).get("outcome", {})
        )
        if human_outcome in {"miss", "detected"} and automation_outcome in {
            "miss",
            "detected",
        }:
            cell_name = (
                "both_miss"
                if human_outcome == "miss" and automation_outcome == "miss"
                else "human_only_miss"
                if human_outcome == "miss"
                else "automation_only_miss"
                if automation_outcome == "miss"
                else "neither_miss"
            )
        else:
            cell_name = None
            unknown_cells.update(joint_cell_names)
            summary_unknown = True

        reference_state = observed(row.get("reference_state", {}))
        reference_validity = observed(row.get("reference_validity", {}))
        row_common_operands_observed = (
            occurred_at is not None
            and reference_state == "opportunity_present"
            and reference_validity == "valid"
            and cell_name is not None
        )
        if cell_name is not None:
            if row_common_operands_observed:
                expected_cells[cell_name] += 1
            else:
                unknown_cells.add(cell_name)
                summary_unknown = True

        if cell_name == "both_miss" and row_common_operands_observed:
            warning_outcome = observed(row.get("warning", {}).get("outcome", {}))
            fallback_outcome = observed(row.get("fallback", {}).get("outcome", {}))
            if warning_outcome is None or fallback_outcome is None:
                summary_unknown = True
            elif (
                warning_outcome == "not_issued"
                and fallback_outcome == "not_activated"
            ):
                expected_silent_misses += 1
            elif warning_outcome not in {"issued", "not_issued"} or fallback_outcome not in {
                "activated",
                "not_activated",
            }:
                silent_row_invalid = True
                silent_pointer = row_pointer

    add_if(
        output,
        row_binding_invalid,
        "GA-JOINT-OPPORTUNITY-ROW-BINDING",
        row_binding_pointer,
        "opportunity rows must exact-bind the common object, clock, window, role-typed channels, and warning and fallback rules",
    )
    add_if(
        output,
        chronology_invalid,
        "GA-JOINT-OPPORTUNITY-CHRONOLOGY",
        chronology_pointer,
        "observed opportunity times must be strictly ordered inside the exact common window",
    )

    cells = {
        key: observed(joint["common_opportunity_cells"].get(key))
        for key in joint_cell_names
    }
    cell_derivation_invalid = any(
        (cells[key] is not None)
        if key in unknown_cells
        else not close(cells[key], expected_cells[key])
        for key in joint_cell_names
    )
    add_if(
        output,
        cell_derivation_invalid,
        "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
        "/joint_silent_miss/common_opportunity_cells",
        "disjoint common-opportunity cells must derive exactly from the complete ordered typed opportunity rows",
    )

    opportunities = measurement_count(joint, "opportunities")
    human = measurement_count(joint, "human_misses")
    automation = measurement_count(joint, "automation_misses")
    misses = measurement_count(joint, "joint_misses")
    expected_opportunities = sum(expected_cells.values())
    expected_human = expected_cells["both_miss"] + expected_cells["human_only_miss"]
    expected_automation = (
        expected_cells["both_miss"] + expected_cells["automation_only_miss"]
    )
    if summary_unknown:
        unknown_invalid = (
            joint["identifiability"] != "nonidentifiable_unknown"
            or any(
                value is not None
                for value in (opportunities, human, automation, misses)
            )
            or observed(joint["joint_miss_risk"]) is not None
        )
        add_if(
            output,
            unknown_invalid,
            "GA-JOINT-UNKNOWN-PROPAGATION",
            "/joint_silent_miss",
            "a nonobserved required opportunity-row operand must make every joint-miss summary nonobserved and nonidentifiable",
        )
    else:
        marginal_invalid = (
            joint["identifiability"]
            != "identified_from_common_opportunities"
            or opportunities is None
            or human is None
            or automation is None
            or not close(opportunities, expected_opportunities)
            or not close(human, expected_human)
            or not close(automation, expected_automation)
        )
        add_if(
            output,
            marginal_invalid,
            "GA-JOINT-COMMON-OPPORTUNITY-DERIVATION",
            "/joint_silent_miss/common_opportunity_cells",
            "complete opportunity rows must derive opportunities and both channel-miss marginals",
        )
        silent_row_invalid = silent_row_invalid or (
            misses is None or not close(misses, expected_silent_misses)
        )
        add_if(
            output,
            silent_row_invalid,
            "GA-JOINT-SILENT-ROW-DERIVATION",
            silent_pointer,
            "joint misses must count exactly the both-miss rows with no warning and no activated fallback",
        )
        invalid_joint = (
            misses is None
            or misses > expected_human
            or misses > expected_automation
            or expected_human > expected_opportunities
            or expected_automation > expected_opportunities
            or not derived_rate_valid(
                joint["joint_miss_risk"],
                float(expected_silent_misses),
                float(expected_opportunities),
            )
        )
        add_if(
            output,
            invalid_joint,
            "GA-JOINT-SILENT-MISS-DERIVATION",
            "/joint_silent_miss/joint_miss_risk/value",
            "joint-silent count bounds and risk must derive from silent rows over the complete opportunity set",
        )
    selective = instance["selective_evaluation"]
    population = measurement_count(selective, "population_count")
    partition = selective["partition_counts"]
    partition_values = {key: observed(value) for key, value in partition.items()}
    partition_invalid = population is None or any(value is None for value in partition_values.values()) or sum(
        float(value or 0) for value in partition_values.values()
    ) != population
    add_if(
        output,
        partition_invalid,
        "GA-SELECTIVE-PARTITION",
        "/selective_evaluation/partition_counts",
        "selective states must exactly partition the declared population",
    )
    accepted = float(partition_values.get("accepted") or 0)
    errors = measurement_count(selective, "accepted_error_count")
    chronology_invalid = parse_time(selective["threshold_frozen_at"]) > parse_time(selective["evaluation_started_at"])
    selective_derived_invalid = (
        errors is None
        or errors > accepted
        or not derived_rate_valid(selective["accepted_error_risk"], float(errors or 0), accepted)
        or not derived_rate_valid(selective["coverage"], accepted, float(population or 0))
        or chronology_invalid
    )
    add_if(
        output,
        selective_derived_invalid,
        "GA-SELECTIVE-DERIVATION",
        "/selective_evaluation/accepted_error_risk/value",
        "selective risk, coverage, count bounds, or freeze chronology do not reconcile",
    )
    ood = instance["ood_evaluation"]
    ood_population = measurement_count(ood, "population_count")
    joint_states = {
        key: observed(ood["joint_state_cells"].get(key)) for key in ood_cell_names
    }
    partition_invalid = (
        ood_population is None
        or any(value is None for value in joint_states.values())
        or not close(
            sum(float(value or 0) for value in joint_states.values()),
            float(ood_population or 0),
        )
    )
    add_if(
        output,
        partition_invalid,
        "GA-OOD-DISJOINT-PARTITION",
        "/ood_evaluation/joint_state_cells",
        "the nine reference-by-detector state cells must exactly partition the OOD population",
    )
    tp = float(joint_states.get("reference_ood_detector_ood") or 0)
    fn = float(joint_states.get("reference_ood_detector_in_distribution") or 0)
    reference_ood_detector_unknown = float(joint_states.get("reference_ood_detector_unknown") or 0)
    fp = float(joint_states.get("reference_in_distribution_detector_ood") or 0)
    tn = float(joint_states.get("reference_in_distribution_detector_in_distribution") or 0)
    reference_in_detector_unknown = float(joint_states.get("reference_in_distribution_detector_unknown") or 0)
    reference_unknown_detector_ood = float(joint_states.get("reference_unknown_detector_ood") or 0)
    reference_unknown_detector_in = float(joint_states.get("reference_unknown_detector_in_distribution") or 0)
    both_unknown = float(joint_states.get("reference_unknown_detector_unknown") or 0)
    reference_ood = measurement_count(ood, "reference_ood_count")
    detected_ood = measurement_count(ood, "detected_ood_count")
    reference_unknown = measurement_count(ood, "reference_unknown_count")
    detector_unknown = measurement_count(ood, "detector_unknown_count")
    expected_reference_ood = tp + fn + reference_ood_detector_unknown
    expected_detected_ood = tp + fp + reference_unknown_detector_ood
    expected_reference_unknown = reference_unknown_detector_ood + reference_unknown_detector_in + both_unknown
    expected_detector_unknown = reference_ood_detector_unknown + reference_in_detector_unknown + both_unknown
    reference_known = expected_reference_ood + fp + tn + reference_in_detector_unknown
    add_if(
        output,
        not partition_invalid
        and (detected_ood is None or not close(detected_ood, expected_detected_ood)),
        "GA-OOD-DERIVATION",
        "/ood_evaluation/detected_ood_count/value",
        "OOD counts and rates are not derived from the explicit disjoint reference-by-detector partition",
    )
    add_if(
        output,
        not partition_invalid
        and (
            reference_unknown is None
            or detector_unknown is None
            or not close(reference_unknown, expected_reference_unknown)
            or not close(detector_unknown, expected_detector_unknown)
        ),
        "GA-OOD-DERIVATION",
        "/ood_evaluation/reference_unknown_count/value",
        "OOD unknown marginals are not derived from the explicit disjoint partition",
    )
    add_if(
        output,
        not partition_invalid
        and (
            reference_ood is None
            or not close(reference_ood, expected_reference_ood)
        ),
        "GA-OOD-DERIVATION",
        "/ood_evaluation/reference_ood_count/value",
        "reference OOD count is not derived from all detector states",
    )
    add_if(
        output,
        not partition_invalid
        and not derived_rate_valid(ood["true_positive_rate"], tp, tp + fn),
        "GA-OOD-DERIVATION",
        "/ood_evaluation/true_positive_rate/value",
        "OOD rates are not derived from the explicit known-reference confusion cells",
    )
    add_if(
        output,
        not partition_invalid
        and not derived_rate_valid(ood["false_positive_rate"], fp, fp + tn),
        "GA-OOD-DERIVATION",
        "/ood_evaluation/false_positive_rate/value",
        "OOD rates are not derived from the explicit known-reference confusion cells",
    )
    add_if(
        output,
        not partition_invalid
        and (
            not derived_rate_valid(ood["prevalence"], expected_reference_ood, reference_known)
            or ood["prevalence_denominator"] != "reference_known"
        ),
        "GA-OOD-DERIVATION",
        "/ood_evaluation/prevalence/value",
        "OOD prevalence is not derived over the declared reference-known denominator",
    )
    binding_invalid = (
        population != ood_population
        or reference_ood is None
        or partition_values.get("out_of_distribution") != reference_ood
    )
    add_if(
        output,
        binding_invalid,
        "GA-OOD-SELECTIVE-BINDING",
        "/selective_evaluation/partition_counts/out_of_distribution/value",
        "selective OOD count and reference OOD count must share one population and reconcile",
    )
    output.extend(
        conformal_violations(
            instance["conformal_evaluation"],
            contracts["reiyah.executable-contract.conformal-guarantee-disposition"],
            definition_registry,
        )
    )
    output.extend(
        transfer_violations(
            instance["transfer_evaluation"],
            contracts["reiyah.executable-contract.transfer-eligibility"],
        )
    )
    output.extend(
        worst_group_violations(
            instance["worst_group_evaluation"],
            contracts["reiyah.executable-contract.worst-group-eligibility"],
            definition_registry,
        )
    )
    return output


def conformal_violations(
    section: Mapping[str, Any],
    contract: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    if not (
        contract.get("guarantee_separate_from_empirical_coverage") is True
        and contract.get("required_assumption_failure_policy")
        == "guarantee_not_supported"
        and contract.get("empirical_coverage_policy")
        == "exact_covered_over_evaluated_with_nonobserved_zero_or_unknown"
        and contract.get("group_scope_policy")
        == "registry_bound_group_set_with_declared_disjoint_or_overlapping_aggregation"
        and contract.get("calibration_set_ref")
        == {
            "record_id": "reiyah.split.synthetic_calibration",
            "record_kind": "reiyah.kind.split",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and contract.get("test_set_ref")
        == {
            "record_id": "reiyah.split.synthetic_test",
            "record_kind": "reiyah.kind.split",
            "version": SCIENCE_SCHEMA_VERSION,
        }
        and contract.get("split_role_binding_policy")
        == "exact_calibration_and_test_split_ids_roles_and_versions"
        and contract.get("arithmetic_comparison") == "absolute_error_lte"
        and contract.get("arithmetic_absolute_tolerance") == 1e-12
        and contract.get("relative_tolerance") == 0
    ):
        raise ScienceContractError(
            "conformal executable contract has an unrecognized guarantee operand"
        )
    arithmetic_tolerance = contract["arithmetic_absolute_tolerance"]

    def conformal_close(left: object, right: object) -> bool:
        return absolute_close(left, right, arithmetic_tolerance)

    target = float(section["target_coverage"])
    add_if(
        output,
        not conformal_close(target, 1.0 - float(section["alpha"])),
        "GA-CONFORMAL-TARGET",
        "/conformal_evaluation/target_coverage",
        "conformal target coverage must equal one minus alpha",
    )
    guarantee = section["guarantee"]
    assumption = section["exchangeability"]["disposition"]
    guarantee_invalid = (
        guarantee
        != {"kind": "none", "disposition": "not_asserted", "scope": "none"}
        or assumption not in {"unmeasured", "not_applicable"}
    )
    add_if(
        output,
        guarantee_invalid,
        "GA-CONFORMAL-GUARANTEE-ASSUMPTION",
        "/conformal_evaluation/guarantee/disposition",
        "conformal guarantee disposition must propagate exchangeability status and typed scope",
    )
    definitions = [
        item
        for item in definition_registry.get("definitions", [])
        if isinstance(item, Mapping)
        and item.get("definition_id") == section["group_set_ref"].get("record_id")
    ]
    group_set = definitions[0] if len(definitions) == 1 else None
    declared_universe = list(section["group_universe"])
    universe = set(declared_universe)
    expected_universe = (
        list(group_set.get("member_ids", []))
        if isinstance(group_set, Mapping)
        else []
    )
    split_role_invalid = (
        section["calibration_set_ref"] != contract["calibration_set_ref"]
        or section["test_set_ref"] != contract["test_set_ref"]
        or section["calibration_set_ref"] == section["test_set_ref"]
    )
    group_binding_invalid = (
        split_role_invalid
        or not isinstance(group_set, Mapping)
        or group_set.get("kind") != "group_set"
        or group_set.get("version") != SCIENCE_SCHEMA_VERSION
        or group_set.get("owner_protocol_release_id") != PROTOCOL_RELEASE_ID
        or section["group_set_ref"].get("record_kind") != "reiyah.kind.group_set"
        or section["group_set_ref"].get("version") != SCIENCE_SCHEMA_VERSION
        or len(expected_universe) != len(set(expected_universe))
        or declared_universe != expected_universe
    )
    add_if(
        output,
        group_binding_invalid,
        "GA-CONFORMAL-GROUP-SCOPE",
        (
            "/conformal_evaluation/calibration_set_ref"
            if split_role_invalid
            else "/conformal_evaluation/group_set_ref"
        ),
        "conformal calibration/test and group-universe operands must exact-bind distinct splits and the registry-owned group set",
    )
    result_ids = [item["group_id"] for item in section["group_results"]]
    add_if(
        output,
        len(set(result_ids)) != len(result_ids) or set(result_ids) != universe,
        "GA-CONFORMAL-GROUP-SCOPE",
        "/conformal_evaluation/group_results",
        "conformal group results must cover the declared group universe exactly once",
    )

    def count_value(measurement: object) -> int | None:
        value = observed(measurement)
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    def empirical_invalid(
        covered_measurement: Mapping[str, Any],
        evaluated_measurement: Mapping[str, Any],
        coverage_measurement: Mapping[str, Any],
    ) -> tuple[bool, float | None]:
        covered = count_value(covered_measurement)
        evaluated = count_value(evaluated_measurement)
        coverage = observed(coverage_measurement)
        if covered is None or evaluated is None or evaluated == 0:
            return coverage is not None, None
        if covered < 0 or evaluated < 0 or covered > evaluated:
            return True, None
        expected = covered / evaluated
        return (
            coverage is None or not conformal_close(coverage, expected),
            expected,
        )

    aggregate_invalid, _aggregate_expected = empirical_invalid(
        section["covered_count"],
        section["evaluated_count"],
        section["empirical_coverage"],
    )
    aggregate_covered = count_value(section["covered_count"])
    aggregate_evaluated = count_value(section["evaluated_count"])
    test_count = count_value(section["test_sample_count"])
    aggregate_invalid = aggregate_invalid or (
        aggregate_evaluated is not None
        and test_count is not None
        and aggregate_evaluated != test_count
    )
    group_counts: list[tuple[int | None, int | None]] = []
    group_derivation_invalid = False
    group_derivation_pointer = "/conformal_evaluation/group_results"
    for index, result in enumerate(section["group_results"]):
        covered = count_value(result["covered_count"])
        evaluated = count_value(result["evaluated_count"])
        group_counts.append((covered, evaluated))
        invalid, expected_coverage = empirical_invalid(
            result["covered_count"],
            result["evaluated_count"],
            result["empirical_coverage"],
        )
        if invalid and not group_derivation_invalid:
            group_derivation_invalid = True
            group_derivation_pointer = (
                f"/conformal_evaluation/group_results/{index}/empirical_coverage"
            )
        expected = (
            "unknown"
            if expected_coverage is None
            else (
                "meets_target"
                if expected_coverage >= target
                or conformal_close(expected_coverage, target)
                else "below_target"
            )
        )
        add_if(
            output,
            result["coverage_disposition"] != expected,
            "GA-CONFORMAL-COVERAGE-DISPOSITION",
            f"/conformal_evaluation/group_results/{index}/coverage_disposition",
            "group coverage disposition must be derived from empirical coverage and target",
        )
    if section["group_scope_mode"] == "disjoint_exhaustive" and all(
        covered is not None and evaluated is not None
        for covered, evaluated in group_counts
    ):
        if (
            aggregate_covered is None
            or aggregate_evaluated is None
            or sum(covered for covered, _ in group_counts if covered is not None)
            != aggregate_covered
            or sum(evaluated for _, evaluated in group_counts if evaluated is not None)
            != aggregate_evaluated
        ):
            aggregate_invalid = True
    add_if(
        output,
        aggregate_invalid,
        "GA-CONFORMAL-EMPIRICAL-DERIVATION",
        "/conformal_evaluation/empirical_coverage",
        "aggregate conformal coverage must derive from exact covered and evaluated counts and reconcile with the test population and declared group scope",
    )
    add_if(
        output,
        group_derivation_invalid,
        "GA-CONFORMAL-EMPIRICAL-DERIVATION",
        group_derivation_pointer,
        "group conformal coverage must derive from exact covered and evaluated counts, with zero or nonobserved denominators propagating unknown",
    )
    return output


def transfer_violations(
    section: Mapping[str, Any], contract_definition: Mapping[str, Any]
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    required_conditions = list(contract_definition.get("required_conditions", []))
    if not (
        required_conditions
        == [
            "metric_identity",
            "metric_direction",
            "population_harmonization",
            "support_overlap",
            "measurement_invariance",
            "access_chronology",
            "adaptation_disclosure",
            "target_tuning_disclosure",
        ]
        and contract_definition.get("failed_condition_policy")
        == "unqualified_result_ineligible"
        and contract_definition.get("minimum_observed_count") == 1
        and contract_definition.get("estimate_observability_policy")
        == "observed_requires_minimum_observed_count"
        and contract_definition.get("metric_direction") == "lower_is_better"
        and contract_definition.get("source_domain_id")
        == "reiyah.domain.synthetic_source"
        and contract_definition.get("target_domain_id")
        == "reiyah.domain.synthetic_target"
        and contract_definition.get("domain_role_binding_policy")
        == "exact_distinct_source_and_target_domain_ids"
        and contract_definition.get("arithmetic_comparison")
        == "absolute_error_lte"
        and contract_definition.get("arithmetic_absolute_tolerance") == 1e-12
        and contract_definition.get("relative_tolerance") == 0
    ):
        raise ScienceContractError(
            "transfer executable contract has an unrecognized eligibility operand"
        )
    minimum_observed_count = int(contract_definition["minimum_observed_count"])
    arithmetic_tolerance = float(
        contract_definition["arithmetic_absolute_tolerance"]
    )

    def transfer_close(actual: float, expected: float) -> bool:
        return abs(actual - expected) <= arithmetic_tolerance

    contract = section["metric_contract"]
    source = section["source_result"]
    target = section["target_result"]

    domain_role_invalid = (
        source.get("domain_id") != contract_definition["source_domain_id"]
        or target.get("domain_id") != contract_definition["target_domain_id"]
        or source.get("domain_id") == target.get("domain_id")
    )
    add_if(
        output,
        domain_role_invalid,
        "GA-TRANSFER-DOMAIN-ROLE-BINDING",
        "/transfer_evaluation/source_result/domain_id",
        "source and target domain identifiers must exact-bind their distinct synthetic roles",
    )

    def measurement_unit_invalid(measurement: Mapping[str, Any]) -> bool:
        return (
            measurement.get("state") == "observed"
            and measurement.get("unit") != contract["unit"]
        )

    metric_direction_invalid = (
        contract.get("direction") != contract_definition["metric_direction"]
    )
    metric_invalid = metric_direction_invalid or any(
        result["metric_contract_id"] != contract["metric_contract_id"]
        or result["metric_contract_version"] != contract["version"]
        or measurement_unit_invalid(result["estimate"])
        or measurement_unit_invalid(result["uncertainty"]["lower"])
        or measurement_unit_invalid(result["uncertainty"]["upper"])
        for result in (source, target)
    )
    add_if(
        output,
        metric_invalid,
        "GA-TRANSFER-METRIC-CONTRACT",
        (
            "/transfer_evaluation/metric_contract/direction"
            if metric_direction_invalid
            else "/transfer_evaluation/target_result/metric_contract_id"
        ),
        "source and target results must bind the exact metric contract and unit",
    )
    coverage_invalid = False
    coverage_pointer = "/transfer_evaluation/source_result/coverage_counts"
    domain_complete: dict[str, bool] = {}
    for result_name, result in (("source_result", source), ("target_result", target)):
        counts = result["coverage_counts"]
        estimate_observed = observed(result["estimate"]) is not None
        interval_operands = (
            result["uncertainty"]["confidence_level"],
            result["uncertainty"]["lower"],
            result["uncertainty"]["upper"],
        )
        interval_observed = [observed(item) is not None for item in interval_operands]
        counts_invalid = not coverage_valid(counts, counts["total"])
        below_minimum = counts["observed"] < minimum_observed_count
        observability_invalid = below_minimum and (
            estimate_observed or any(interval_observed)
        )
        if not coverage_invalid and (counts_invalid or observability_invalid):
            coverage_invalid = True
            coverage_pointer = (
                f"/transfer_evaluation/{result_name}/coverage_counts"
                if counts_invalid
                else f"/transfer_evaluation/{result_name}/estimate"
            )
        domain_complete[result_name] = (
            not counts_invalid
            and not below_minimum
            and estimate_observed
            and all(interval_observed)
        )
    add_if(
        output,
        coverage_invalid,
        "GA-TRANSFER-COVERAGE",
        coverage_pointer,
        "transfer coverage and observed result operands must reconcile with the executable minimum observed count",
    )
    source_value = observed(source["estimate"])
    target_value = observed(target["estimate"])
    gap_value = observed(section["gap"])
    gap_invalid = gap_value is not None and (
        source_value is None
        or target_value is None
        or not transfer_close(
            float(gap_value), float(target_value) - float(source_value)
        )
        or section["gap"].get("unit") != contract["unit"]
    )
    add_if(
        output,
        gap_invalid,
        "GA-TRANSFER-GAP",
        "/transfer_evaluation/gap/value",
        "transfer gap must equal target estimate minus source estimate",
    )
    access = section["target_data_access"]
    first = parse_time(access["first_accessed_at"])
    frozen = parse_time(access["analysis_frozen_at"])
    labels = parse_time(access["labels_first_accessed_at"]) if access.get("labels_first_accessed_at") else None
    chronology_invalid = frozen >= first or (labels is not None and labels < first)
    add_if(
        output,
        chronology_invalid,
        "GA-TRANSFER-TARGET-ACCESS",
        "/transfer_evaluation/target_data_access/first_accessed_at",
        "analysis must freeze before target access and label access cannot precede target access",
    )
    adaptation = section["adaptation"]
    mode = adaptation["mode"]
    tuning = adaptation["tuning_performed"]
    labels_used = adaptation["target_labels_used"]
    procedure = adaptation["procedure_ref"]
    adaptation_invalid = (
        (mode == "none" and (tuning or labels_used or procedure is not None))
        or (
            mode == "unsupervised"
            and (not tuning or labels_used or procedure is None)
        )
        or (
            mode == "supervised"
            and (not tuning or not labels_used or procedure is None or labels is None)
        )
        or (labels_used and labels is None)
    )
    add_if(
        output,
        adaptation_invalid,
        "GA-TRANSFER-ADAPTATION-DISCLOSURE",
        "/transfer_evaluation/adaptation",
        "adaptation mode, tuning, target-label use, and procedure binding are inconsistent",
    )
    assumptions = (
        ("overlap", "reiyah.assumption.transfer_overlap"),
        ("invariance", "reiyah.assumption.transfer_invariance"),
        (
            "population_harmonization",
            "reiyah.assumption.transfer_population_harmonization",
        ),
    )
    assumption_identity_invalid = any(
        section[name]["assumption_id"] != expected_id
        for name, expected_id in assumptions
    )
    prerequisite_invalid = (
        domain_role_invalid
        or metric_invalid
        or coverage_invalid
        or gap_invalid
        or chronology_invalid
        or adaptation_invalid
        or assumption_identity_invalid
    )
    if not prerequisite_invalid:
        unresolved = (
            any(
                section[name]["disposition"] == "unmeasured"
                for name, _ in assumptions
            )
            or not domain_complete["source_result"]
            or not domain_complete["target_result"]
            or gap_value is None
        )
        expected_disposition = "unknown" if unresolved else "not_identified"
    else:
        expected_disposition = section["disposition"]
    add_if(
        output,
        assumption_identity_invalid
        or (
            not prerequisite_invalid
            and section["disposition"] != expected_disposition
        ),
        "GA-TRANSFER-DISPOSITION",
        "/transfer_evaluation/disposition",
        "transfer disposition must derive exactly from operand observability and the three non-favorable assumption states",
    )
    return output


def worst_group_violations(
    section: Mapping[str, Any],
    contract: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    ineligible_group_policy = contract.get("ineligible_group_policy")
    if not (
        ineligible_group_policy == "complete_worst_group_unknown"
        and contract.get("arithmetic_comparison") == "absolute_error_lte"
        and contract.get("arithmetic_absolute_tolerance") == 1e-12
        and contract.get("relative_tolerance") == 0
        and contract.get("tie_comparison") == "absolute_error_lte"
        and contract.get("tie_absolute_tolerance") == 1e-12
    ):
        raise ScienceContractError(
            "worst-group executable contract has an unrecognized partition or arithmetic policy"
        )
    arithmetic_tolerance = float(contract["arithmetic_absolute_tolerance"])
    tie_tolerance = float(contract["tie_absolute_tolerance"])
    rule = section["minimum_information_rule"]
    expected_rule = {
        "rule_ref": {
            "rule_id": "reiyah.rule.worst-group-eligibility",
            "rule_kind": "reiyah.kind.minimum_information_rule",
            "version": SCIENCE_SCHEMA_VERSION,
        },
        "operator": "all",
        "sample_count_min": contract["minimum_count"],
        "coverage_fraction_min": contract["minimum_coverage"],
        "effective_sample_size_min": contract["minimum_effective_sample_size"],
        "interval_width_max": contract["maximum_interval_width"],
    }
    rule_binding_invalid = rule != expected_rule
    add_if(
        output,
        rule_binding_invalid,
        "GA-WORST-GROUP-INFORMATION",
        "/worst_group_evaluation/minimum_information_rule",
        "the complete application minimum-information rule must exact-bind every executable threshold and policy operand",
    )
    if rule_binding_invalid:
        return output

    matching_group_sets = [
        item
        for item in definition_registry.get("definitions", [])
        if isinstance(item, Mapping)
        and item.get("definition_id") == section["group_set_ref"].get("record_id")
    ]
    group_set = matching_group_sets[0] if len(matching_group_sets) == 1 else None
    expected_universe = (
        list(group_set.get("member_ids", []))
        if isinstance(group_set, Mapping)
        else []
    )
    declared_universe = list(section["group_universe"])
    results = section["group_results"]
    ids = [result["group_id"] for result in results]
    group_binding_invalid = (
        not isinstance(group_set, Mapping)
        or group_set.get("kind") != "group_set"
        or group_set.get("version") != SCIENCE_SCHEMA_VERSION
        or group_set.get("owner_protocol_release_id") != PROTOCOL_RELEASE_ID
        or section["group_set_ref"].get("record_kind") != "reiyah.kind.group_set"
        or section["group_set_ref"].get("version") != SCIENCE_SCHEMA_VERSION
        or len(expected_universe) != len(set(expected_universe))
        or declared_universe != expected_universe
        or ids != expected_universe
        or len(ids) != len(set(ids))
    )
    add_if(
        output,
        group_binding_invalid,
        "GA-WORST-GROUP-ELIGIBILITY",
        "/worst_group_evaluation/group_set_ref",
        "worst-group universe and results must exact-bind the registry-owned group set without omission or substitution",
    )
    if group_binding_invalid:
        return output

    universe = set(expected_universe)
    sufficient: set[str] = set()
    insufficient: set[str] = set()
    unknown: set[str] = set()
    performance: dict[str, float] = {}
    for index, result in enumerate(results):
        sample = observed(result["sample_count"])
        ess = observed(result["effective_sample_size"])
        width = observed(result["interval_width"])
        performance_value = observed(result["performance"])
        counts = result["coverage_counts"]
        coverage_mismatch = sample is not None and not coverage_valid(
            counts, int(sample)
        )
        add_if(
            output,
            coverage_mismatch,
            "GA-WORST-GROUP-COVERAGE",
            f"/worst_group_evaluation/group_results/{index}/coverage_counts",
            "group coverage states must sum to sample count and total",
        )
        observed_fraction = (
            counts["observed"] / counts["total"] if counts["total"] else 0.0
        )
        unresolved_information = (
            result["membership_state"] != "observed"
            or sample is None
            or ess is None
            or width is None
        )
        qualifies = (
            not unresolved_information
            and not coverage_mismatch
            and float(sample) >= float(contract["minimum_count"])
            and observed_fraction + arithmetic_tolerance
            >= float(contract["minimum_coverage"])
            and float(ess) >= float(contract["minimum_effective_sample_size"])
            and float(width)
            <= float(contract["maximum_interval_width"]) + arithmetic_tolerance
        )
        expected_disposition = (
            "unknown"
            if unresolved_information
            else ("sufficient" if qualifies else "insufficient")
        )
        add_if(
            output,
            result["information_disposition"] != expected_disposition,
            "GA-WORST-GROUP-INFORMATION",
            f"/worst_group_evaluation/group_results/{index}/information_disposition",
            "group information disposition must be derived from every frozen threshold",
        )
        if expected_disposition == "sufficient":
            sufficient.add(result["group_id"])
            if performance_value is not None:
                performance[result["group_id"]] = float(performance_value)
        elif expected_disposition == "insufficient":
            insufficient.add(result["group_id"])
        else:
            unknown.add(result["group_id"])
            add_if(
                output,
                performance_value is not None
                or result["information_disposition"] == "sufficient"
                or result["group_id"] in section["eligible_group_ids"]
                or result["group_id"] in section["worst_group_ids"],
                "GA-WORST-GROUP-UNKNOWN",
                f"/worst_group_evaluation/group_results/{index}",
                "unresolved membership cannot coexist with confident performance or extremum",
            )
    eligible = set(section["eligible_group_ids"])
    declared_unknown = set(section["unknown_group_ids"])
    declared_insufficient = set(section["insufficient_group_ids"])
    eligibility_invalid = (
        eligible != sufficient
        or declared_unknown != unknown
        or declared_insufficient != insufficient
        or eligible & declared_unknown
        or eligible & declared_insufficient
        or declared_unknown & declared_insufficient
        or eligible | declared_unknown | declared_insufficient != universe
    )
    add_if(
        output,
        eligibility_invalid,
        "GA-WORST-GROUP-ELIGIBILITY",
        "/worst_group_evaluation/eligible_group_ids",
        "eligible, unknown, and insufficient IDs must exactly partition the registry-owned group universe",
    )
    unresolved_performance = any(group_id not in performance for group_id in sufficient)
    if unknown or unresolved_performance:
        add_if(
            output,
            observed(section["worst_value"]) is not None
            or bool(section["worst_group_ids"])
            or section["disposition"] != "unknown",
            "GA-WORST-GROUP-DISPOSITION",
            "/worst_group_evaluation",
            "any unresolved membership, minimum-information operand, or eligible performance makes the complete worst-group result unknown",
        )
    elif not sufficient:
        add_if(
            output,
            observed(section["worst_value"]) is not None
            or bool(section["worst_group_ids"])
            or section["disposition"] != "no_eligible_groups",
            "GA-WORST-GROUP-DISPOSITION",
            "/worst_group_evaluation",
            "a complete universe with every group deterministically insufficient must report no eligible groups",
        )
    else:
        worst = (
            min(performance.values())
            if section["direction"] == "higher_is_better"
            else max(performance.values())
        )
        tied = {
            group_id
            for group_id, value in performance.items()
            if abs(value - worst) <= tie_tolerance
        }
        worst_value = observed(section["worst_value"])
        tie_invalid = (
            set(section["worst_group_ids"]) != tied
            or worst_value is None
            or abs(float(worst_value) - worst) > tie_tolerance
            or section["worst_value"].get("unit")
            != section["shared_metric_contract"]["unit"]
            or section["disposition"] != "identified"
        )
        add_if(
            output,
            tie_invalid,
            "GA-WORST-GROUP-TIE",
            "/worst_group_evaluation/worst_group_ids",
            "complete worst-group extremum must include every exact-tolerance tie",
        )
    return output


def assurance_violations(instance: Mapping[str, Any]) -> list[dict[str, str]]:
    output = lifecycle_violations(instance)
    add_if(
        output,
        instance["dataset_governance"].get("synthetic_only") is not True
        or instance["dataset_governance"].get("license_disposition")
        != "synthetic_original",
        "GA-ASSURANCE-LICENSE-DISPOSITION",
        "/dataset_governance/license_disposition",
        "synthetic-only assurance data cannot claim retained permission or an ambiguous license disposition",
    )
    add_if(
        output,
        instance["deployment_authorized"] is not False,
        "GA-ASSURANCE-NO-DEPLOYMENT",
        "/deployment_authorized",
        "Gate A assurance architecture cannot authorize deployment",
    )
    nonclaim = (
        instance["scientific_claim_authorized"] is not False
        or instance["safety_claim_authorized"] is not False
        or instance["compliance_claim_authorized"] is not False
        or instance["safety_case"]["status"] != "proposed"
        or any(claim["status"] != "proposed" for claim in instance["safety_case"]["claims"])
    )
    nonclaim_pointer = "/safety_case/claims"
    for index, claim in enumerate(instance["safety_case"]["claims"]):
        if claim["status"] != "proposed":
            nonclaim_pointer = f"/safety_case/claims/{index}/status"
            break
    add_if(
        output,
        nonclaim,
        "GA-ASSURANCE-NONCLAIM",
        nonclaim_pointer,
        "Gate A assurance structures remain proposed nonclaims",
    )
    return output


def semantic_violations(
    instance: Mapping[str, Any],
    lifecycle_policy: Mapping[str, Any],
    definition_registry: Mapping[str, Any],
    protocol: Mapping[str, Any],
    resolution_context: Mapping[str, Any] | None = None,
) -> list[dict[str, str]]:
    expected_schema_id = (
        resolution_context.get("expected_schema_id")
        if isinstance(resolution_context, Mapping)
        else None
    )
    schema_id = expected_schema_id if isinstance(expected_schema_id, str) else instance.get("schema_id")
    contract_binding_errors = executable_contract_binding_violations(
        schema_id, definition_registry
    )
    if contract_binding_errors:
        # Domain derivations may only consume a fully recognized contract.  In
        # particular, do not let a mutated tolerance or policy cascade into
        # misleading instance diagnostics.
        canonical_contract_errors = [
            canonicalize_violation(instance, item)
            for item in contract_binding_errors
        ]
        return sorted(
            canonical_contract_errors,
            key=lambda item: RULE_PRIORITY.get(
                item["rule_id"], len(RULE_PRIORITY)
            ),
        )[:1]
    elif schema_id == HUMAN_SCHEMA_ID:
        result = readiness_violations(
            instance,
            protocol["belief_normalization_policy"],
            executable_contract(
                definition_registry,
                "reiyah.executable-contract.readiness-unknown-propagation",
            ),
            executable_contract(
                definition_registry,
                "reiyah.executable-contract.recovery-event-derivation",
            ),
            executable_contract(
                definition_registry,
                "reiyah.executable-contract.human-belief-observation-decision-reconciliation",
            ),
            definition_registry,
        )
    elif schema_id == STUDY_SCHEMA_ID:
        result = study_violations(
            instance,
            protocol["estimands"],
            executable_contract(
                definition_registry,
                "reiyah.executable-contract.causal-identification",
            ),
            definition_registry,
        )
    elif schema_id == OPE_SCHEMA_ID:
        result = ope_violations(
            instance,
            executable_contract(
                definition_registry,
                "reiyah.executable-contract.ope-policy-distribution",
            ),
            definition_registry,
        )
    elif schema_id == JOINT_SCHEMA_ID:
        result = joint_violations(
            instance,
            {
                contract_id: executable_contract(definition_registry, contract_id)
                for contract_id in (
                    "reiyah.executable-contract.transfer-eligibility",
                    "reiyah.executable-contract.conformal-guarantee-disposition",
                    "reiyah.executable-contract.ood-population-partition",
                    "reiyah.executable-contract.worst-group-eligibility",
                    "reiyah.executable-contract.joint-silent-miss-identifiability",
                    "reiyah.executable-contract.assumption-evidence-eligibility",
                )
            },
            definition_registry,
        )
    elif schema_id == ASSURANCE_SCHEMA_ID:
        result = assurance_violations(instance)
    else:
        raise ScienceContractError(f"no semantic handler for schema_id {schema_id!r}")
    result.extend(lifecycle_policy_violations(instance, lifecycle_policy, resolution_context))
    result.extend(lifecycle_evidence_violations(instance, protocol))
    result.extend(schema_reference_violations(instance, resolution_context))
    result.extend(
        registry_bare_identifier_violations(instance, definition_registry, resolution_context)
    )
    result.extend(document_local_identifier_violations(instance, resolution_context))
    result.extend(
        classified_reference_path_violations(
            instance, definition_registry, resolution_context
        )
    )
    result.extend(evidence_gap_reference_violations(instance))
    result.extend(
        estimand_reference_violations(
            instance, definition_registry, protocol, resolution_context
        )
    )
    result.extend(typed_reference_violations(instance, definition_registry))
    result.extend(
        assumption_evidence_violations(
            instance,
            executable_contract(
                definition_registry,
                "reiyah.executable-contract.assumption-evidence-eligibility",
            )
            if schema_id == JOINT_SCHEMA_ID
            else None,
        )
    )
    canonical = [canonicalize_violation(instance, item) for item in result]
    deduplicated: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for item in canonical:
        key = (item["rule_id"], item["instance_pointer"], item["reason"])
        if key not in seen:
            seen.add(key)
            deduplicated.append(item)
    ordered = sorted(
        deduplicated,
        key=lambda item: RULE_PRIORITY.get(item["rule_id"], len(RULE_PRIORITY)),
    )
    # The public production diagnostic contract is primary-only.  Handlers
    # still compute all independent predicates above, but callers receive one
    # frozen-priority tuple, which prevents prerequisite cascades from being
    # misrepresented as separate isolated evidence.
    return ordered[:1]
