"""Pure qualification model for a NEW analysis-only projection contract.

Not a worker, model runner, storage export, or replacement for a failed protocol.
Callers must bind decoder/NMS implementations and retain original raw arrays.
"""
from __future__ import annotations
import numpy as np

ANALYSIS_THRESHOLD = np.float32(0.5)
STORAGE_FLOOR = np.float32(0.05)
MAX_RAW_ROWS = 200000


def project_tile(outputs, row, column, side, *, decoder, remaining_raw_rows):
    """Project defined high rows; never describe malformed lows as valid rows."""
    if type(remaining_raw_rows) is not int or not 0 <= remaining_raw_rows <= MAX_RAW_ROWS:
        raise ValueError('raw work budget')
    if not isinstance(outputs, (list, tuple)) or len(outputs) != 2:
        raise ValueError('two observed output arrays required')
    dets, labels = [np.asarray(value) for value in outputs]
    if dets.ndim != 3 or dets.shape[0] != 1 or dets.shape[2] != 5:
        raise ValueError('detection shape')
    if not np.issubdtype(dets.dtype, np.floating):
        raise ValueError('real floating detection output required')
    if labels.shape != dets.shape[:2] or not np.issubdtype(labels.dtype, np.integer):
        raise ValueError('observed integer labels required')
    n = dets.shape[1]
    if n > remaining_raw_rows:
        raise ValueError('all-raw-row work cap')
    raw = dets[0]
    scores = raw[:, 4]
    if not np.isfinite(scores).all() or (scores < 0).any() or (scores > 1).any():
        raise ValueError('unknown nonfinite or invalid score')
    if not np.isfinite(raw[:, :4]).all():
        raise ValueError('nonfinite raw coordinate in any row')
    with np.errstate(over='ignore', invalid='ignore'):
        converted = raw.astype(np.float32, copy=True)
    if not np.isfinite(converted[:, :4]).all():
        raise ValueError('nonfinite float32 coordinate conversion in any row')
    scores32 = converted[:, 4]
    high = scores32 > ANALYSIS_THRESHOLD
    storage = scores32 >= STORAGE_FLOOR
    # Preserve the original one-class obligation on storage-eligible rows.
    if (labels[0][storage] != 0).any():
        raise ValueError('invalid required foreground label')
    raw_finite = np.isfinite(raw[:, :4]).all(axis=1)
    converted_finite = np.isfinite(converted[:, :4]).all(axis=1)
    raw_positive = (raw[:, 2] > raw[:, 0]) & (raw[:, 3] > raw[:, 1])
    converted_positive = (converted[:, 2] > converted[:, 0]) & (converted[:, 3] > converted[:, 1])
    if (high & (~raw_finite | ~converted_finite | ~raw_positive | ~converted_positive)).any():
        raise ValueError('undefined high-score geometry')
    high_indices = np.flatnonzero(high)
    # The bound original decoder supplies the unchanged coordinate operations and
    # its post-floor guard. Its subset count is NOT the original work count.
    boxes, retained_scores, subset_counts = decoder(
        [dets[:, high, :], labels[:, high]], row, column, side)
    if len(boxes) != len(high_indices) or len(retained_scores) != len(high_indices):
        raise ValueError('decoder changed high-row membership')
    low = ~high
    anomaly_masks = {
        'raw_nonfinite': low & ~raw_finite,
        'raw_nonpositive_extent': low & raw_finite & ~raw_positive,
        'conversion_nonfinite': low & raw_finite & ~converted_finite,
        'finite_conversion_nonpositive_extent': low & raw_finite & raw_positive & converted_finite & ~converted_positive,
    }
    return {
        'status': 'tile_analysis_projection_defined',
        'boxes': boxes, 'scores': retained_scores, 'original_row_indices': high_indices,
        'all_raw_rows': int(n), 'high_rows': int(high.sum()), 'low_rows': int(low.sum()),
        'storage_eligible_rows': int(storage.sum()), 'below_storage_floor_rows': int((~storage).sum()),
        'raw_above_half_converted_not_above_half_rows': int(((scores > 0.5) & ~high).sum()),
        'low_geometry_anomalies': {key: np.flatnonzero(mask) for key, mask in anomaly_masks.items()},
        'storage_eligible_low_geometry_anomalies': {key: np.flatnonzero(mask & storage) for key, mask in anomaly_masks.items()},
        'low_anomaly_scope': 'all_raw_low_rows_including_expected_below_floor_padding; not_a_model_bug_label',
        'low_transformed_geometry': 'not_evaluated_not_claimed_valid',
        'decoder_subset_counts': subset_counts,
        'storage_output_status': 'not_defined_or_exported_by_this_contract',
    }


def complete_projection(tile_results, *, expected_tiles, raw_cap, nms):
    """Authored composition check; real tile/input provenance is a future worker duty."""
    if type(expected_tiles) is not int or not 1 <= expected_tiles <= 512:
        raise ValueError('expected tile count')
    if type(raw_cap) is not int or not 1 <= raw_cap <= MAX_RAW_ROWS:
        raise ValueError('raw cap')
    if len(tile_results) != expected_tiles:
        raise ValueError('incomplete tile population')
    if [item['ordinal'] for item in tile_results] != list(range(expected_tiles)):
        raise ValueError('tile ordinal coverage or order')
    if any(item['projection']['status'] != 'tile_analysis_projection_defined' for item in tile_results):
        raise ValueError('undefined tile')
    total = sum(item['projection']['all_raw_rows'] for item in tile_results)
    if total > raw_cap:
        raise ValueError('all-raw-row work cap')
    boxes = np.concatenate([item['projection']['boxes'] for item in tile_results], axis=0)
    scores = np.concatenate([item['projection']['scores'] for item in tile_results], axis=0)
    ids = [(item['ordinal'], int(row)) for item in tile_results for row in item['projection']['original_row_indices']]
    keep = nms(boxes, scores, 0.5)
    return {'status': 'complete_analysis_projection', 'analysis_row_ids': [ids[int(i)] for i in keep],
            'analysis_boxes': boxes[keep], 'analysis_scores': scores[keep],
            'all_raw_rows': total, 'completed_tiles': expected_tiles,
            'storage_output_status': 'not_defined_or_exported_by_this_contract'}
