"""Logical prediction checks without inference, repair or reference scoring."""
from collections import Counter
import hashlib
import json
import math
import struct


class PacketError(ValueError):
    pass


def require(ok, message):
    if not ok: raise PacketError(message)


def canonical(value):
    if isinstance(value, float): return {'float64_bits': struct.pack('>d', value).hex()}
    if isinstance(value, bytes): return {'bytes_hex': value.hex()}
    if isinstance(value, dict): return {k: canonical(v) for k, v in sorted(value.items())}
    if isinstance(value, (list, tuple)): return [canonical(v) for v in value]
    require(value is None or type(value) in (int, bool, str), 'Unexpected logical value')
    return value


def encoded(value):
    return json.dumps(canonical(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def retained_metadata(value):
    """Keep nonfinite optional measurements explicit and JSON-replayable."""
    if isinstance(value,float) and not math.isfinite(value):
        return {'nonfinite_float64_bits':struct.pack('>d',value).hex()}
    if isinstance(value,dict):return {k:retained_metadata(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [retained_metadata(v) for v in value]
    return value


def row_issues(row, expected):
    errors, diagnostics = [], []
    name = row.get('name')
    if name not in expected: errors.append('unknown_image')
    size = row.get('size')
    if (not isinstance(size, (list, tuple)) or len(size) != 2
            or any(type(v) is not int or v <= 0 for v in size)):
        errors.append('invalid_image_size')
    elif name in expected and list(size) != expected[name]: errors.append('image_size_mismatch')
    if row.get('group') != 'val': errors.append('unexpected_group')
    annotation = [row.get(k) for k in ('label', 'label_index', 'box2d', 'box2d_score')]
    nulls = sum(v is None for v in annotation)
    if nulls == 4:
        if row.get('mask') is not None: errors.append('empty_placeholder_has_mask')
        return 'publisher_empty_placeholder', errors, diagnostics
    if nulls:
        return 'invalid_annotation', errors + ['partial_null_annotation'], diagnostics
    if not isinstance(row['label'], str) or not row['label']: errors.append('invalid_label')
    if type(row['label_index']) is not int or row['label_index'] < 0: errors.append('invalid_label_index')
    if not finite(row['box2d_score']) or not 0 <= row['box2d_score'] <= 1: errors.append('invalid_score')
    box = row['box2d']
    if not isinstance(box, (list, tuple)) or len(box) != 4 or not all(finite(v) for v in box):
        errors.append('invalid_box_tuple')
    else:
        cx, cy, width, height = box
        if width <= 0 or height <= 0: errors.append('nonpositive_box_extent')
        if cx-width/2 < 0 or cy-height/2 < 0 or cx+width/2 > 1 or cy+height/2 > 1:
            diagnostics.append('box_extends_outside_normalized_canvas')
    return 'prediction', errors, diagnostics


def image_state(rows, predictions, placeholders, errors):
    if rows == 0: return 'missing'
    if errors or placeholders > 1 or (placeholders and predictions): return 'invalid'
    if placeholders == 1: return 'publisher_empty_placeholder'
    return 'predictions_present'


def audit(rows, expected, emit_issue, maximum_rows=1000000):
    images = {key: {'image_id': key, 'expected_size': expected[key], 'rows': 0, 'predictions': 0,
                   'placeholders': 0, 'errors': Counter(), 'diagnostics': Counter(), 'first_row': None,
                   'metadata': None, 'duplicate_predictions': 0} for key in expected}
    total_errors, diagnostics, labels, inverse_labels = Counter(), Counter(), {}, {}
    label_pairs = set()
    seen, metadata_bytes, digest, count = {}, {}, hashlib.sha256(), 0
    low_score = high_score = None
    for ordinal, row in enumerate(rows):
        require(ordinal < maximum_rows, 'Row cap reached')
        count += 1; digest.update(encoded(row)); digest.update(b'\n')
        kind, errors, notes = row_issues(row, expected)
        name = row.get('name'); image = images.get(name)
        if image is None:
            image = images.setdefault(str(name), {'image_id': str(name), 'expected_size': None, 'rows': 0,
                'predictions': 0, 'placeholders': 0, 'errors': Counter(), 'diagnostics': Counter(),
                'first_row': None, 'metadata': None, 'duplicate_predictions': 0})
        image['rows'] += 1
        metadata = {key: row.get(key) for key in ('size', 'group', 'timing', 'capture_ms', 'e2e_ms',
                    'emit_ts_ns', 'sahi_tiles', 'sahi_overlap', 'sahi_e2e_ms', 'sahi_merge_ms')}
        retained=retained_metadata(metadata)
        if retained!=metadata:notes.append('nonfinite_optional_metadata_retained')
        metadata=retained
        current_metadata_bytes=encoded(metadata)
        if image['first_row'] is None:
            image['first_row'] = ordinal; image['metadata'] = metadata
            metadata_bytes[name]=current_metadata_bytes
        elif metadata_bytes[name] != current_metadata_bytes: errors.append('inconsistent_image_metadata')
        if kind == 'publisher_empty_placeholder': image['placeholders'] += 1
        elif kind == 'prediction':
            image['predictions'] += 1
            label, index = row['label'], row['label_index']
            if isinstance(label, str) and type(index) is int:
                label_pairs.add((index,label))
                if index in labels and labels[index] != label: errors.append('index_has_multiple_labels')
                if label in inverse_labels and inverse_labels[label] != index: errors.append('label_has_multiple_indices')
                labels.setdefault(index, label); inverse_labels.setdefault(label, index)
            score = row['box2d_score']
            if finite(score):
                low_score = score if low_score is None else min(low_score, score)
                high_score = score if high_score is None else max(high_score, score)
            pred_digest = hashlib.sha256(encoded({key: row.get(key) for key in
                ('label', 'label_index', 'box2d', 'box2d_score', 'mask')})).digest()
            entries = seen.setdefault(name, set())
            if pred_digest in entries:
                image['duplicate_predictions'] += 1; notes.append('exact_duplicate_prediction_retained')
            entries.add(pred_digest)
        for issue in errors:
            image['errors'][issue] += 1; total_errors[issue] += 1
            emit_issue({'row': ordinal, 'image_id': name, 'kind': 'invalid', 'issue': issue})
        for issue in notes:
            image['diagnostics'][issue] += 1; diagnostics[issue] += 1
            emit_issue({'row': ordinal, 'image_id': name, 'kind': 'diagnostic', 'issue': issue})
    for image in images.values():
        if image['placeholders'] > 1: image['errors']['duplicate_empty_placeholder'] += 1
        if image['placeholders'] and image['predictions']: image['errors']['mixed_empty_and_predictions'] += 1
        image['state'] = image_state(image['rows'], image['predictions'], image['placeholders'], image['errors'])
        image['errors'] = dict(sorted(image['errors'].items())); image['diagnostics'] = dict(sorted(image['diagnostics'].items()))
    return {'rows': count, 'logical_rows_sha256': digest.hexdigest(), 'expected_images': len(expected),
            'observed_images': sum(r['rows'] > 0 for r in images.values()),
            'states': dict(sorted(Counter(r['state'] for r in images.values()).items())),
            'prediction_rows': sum(r['predictions'] for r in images.values()),
            'empty_placeholder_rows': sum(r['placeholders'] for r in images.values()),
            'row_errors': dict(sorted(total_errors.items())), 'row_diagnostics': dict(sorted(diagnostics.items())),
            'image_errors': dict(sorted(sum((Counter(r['errors']) for r in images.values()), Counter()).items())),
            'images_with_each_error':dict(sorted(Counter(issue for r in images.values() for issue in r['errors']).items())),
            'observed_label_indices': [{'index': k, 'label': v} for k, v in sorted(label_pairs)],
            'minimum_score': low_score, 'maximum_score': high_score,
            'maximum_prediction_rows_per_image': max((r['predictions'] for r in images.values()), default=0),
            'images_at_300_predictions': sum(r['predictions'] == 300 for r in images.values()),
            'duplicates_retained': sum(r['duplicate_predictions'] for r in images.values()),
            'images': [images[key] for key in sorted(images)]}
