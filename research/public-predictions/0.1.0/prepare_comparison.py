"""Admit the fixed exports and construct separate visible and oracle packets."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import time

from admission import AVAILABLE, admit, digest, encoded, number, require
from compare_math import subject, validate_canvas, validate_image, validate_rows, w
from local_export import ALLOCATION_SHA256, MODELS, read_bound
from project_reference import classify_projection


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_binding(path):
    path = Path(path).resolve(); raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def put(path, value):
    with path.open('xb') as handle:
        handle.write(encoded(value))


def prediction_operand(row):
    """Keep duplicate occurrences; share IDs only for exactly equal metric operands."""
    if row['state'] not in AVAILABLE:
        return {'state': 'unavailable', 'reason': row['state'] + ': ' + row['reason']}, []
    records, custody, occurrences = [], [], Counter()
    for detection in row['detections']:
        geometry = [w(number(value)) for value in detection['xyxy']]
        reason = 'category_outside_car' if detection['category_id'] != 2 else (
            'height_below_25' if number(detection['xyxy'][3]) - number(detection['xyxy'][1]) < 25 else None)
        if reason is not None:
            custody.append({'source_detection': detection, 'state': 'excluded', 'reason': reason})
            continue
        require(detection['category_name'] == 'car', 'CATEGORY', 'Frozen car mapping differs')
        signature = digest({'category': 'car', 'xyxy': geometry})
        occurrence = occurrences[signature]; occurrences[signature] += 1
        identity = 'prediction:' + digest({'signature': signature, 'occurrence': occurrence})
        record = {'id': identity, 'record_sha256': digest({'id': identity, 'xyxy': geometry}), 'xyxy': geometry}
        records.append(record)
        custody.append({'source_detection': detection, 'state': 'eligible', 'record': record})
    validate_rows(records)
    return {'state': 'observed', 'value': records}, custody


def reference_operand(source, image):
    if source['state'] != 'observed':
        require(source['state'] == 'unavailable' and source['reason'], 'STATE', 'Reference failure must be explicit')
        return None, {'state': 'unavailable', 'reason': source['reason']}
    eligible, exclusions = classify_projection(source['all_projection_rows'], image)
    # The first projection artifact used floating subtraction at the height
    # cutoff. Requalify every actual record under the frozen decimal policy.
    # Keep any changed selection explicit; never rewrite the original artifact.
    selection_changed = eligible != source['answer'] or exclusions != source['exclusions']
    answer = [{**row, 'xyxy': [w(number(value)) for value in row['xyxy']]} for row in eligible]
    validate_rows(answer); validate_canvas(answer, image)
    return answer, {'state': 'available', 'eligible_count': len(answer),
                    'exact_decimal_selection_changed': selection_changed,
                    'eligible': eligible, 'exclusions': exclusions}


def export(area, stage, expected_model, bindings):
    directory = area / 'results' / stage
    values = {}
    for key in ('ALLOCATION', 'CONFIGURATION', 'PACKET', 'REQUEST', 'EXPORT_EVENTS', 'RESULT'):
        path = directory / (key + '.json'); bindings.append(file_binding(path)); values[key] = json.loads(path.read_text())
    require(values['REQUEST']['model_id'] == expected_model, 'MODEL', 'Comparison direction changed')
    require(values['CONFIGURATION']['checkpoint_sha256'] == MODELS[expected_model][0], 'MODEL', 'Checkpoint changed')
    read_bound(values['REQUEST']['checkpoint'])
    require(values['CONFIGURATION'] == values['REQUEST']['configuration'], 'CONFIGURATION', 'Export configuration changed')
    require(values['EXPORT_EVENTS']['request_sha256'] == digest(values['REQUEST']), 'EXPORT', 'Request binding differs')
    require(values['PACKET']['source_binding_sha256'] == digest(values['EXPORT_EVENTS']), 'EXPORT', 'Event binding differs')
    require(values['RESULT']['admission'] == admit(values['ALLOCATION'], values['CONFIGURATION'], values['PACKET']),
            'ADMISSION', 'Retained packet admission differs')
    require(len(values['ALLOCATION']['images']) == 64 and values['ALLOCATION']['source_binding_sha256'] == ALLOCATION_SHA256,
            'ALLOCATION', 'The complete frozen image allocation is required')
    for event in values['EXPORT_EVENTS']['events']:
        if event['state'] == 'exported':
            require(event['preprocess_check']['maximum_absolute_error'] <= event['preprocess_check']['tolerance']
                    and event['decode_check']['maximum_coordinate_error_pixels'] <= event['decode_check']['coordinate_tolerance_pixels']
                    and event['decode_check']['scores_and_classes_exact'] is True
                    and event['decode_check']['order_equal'] is True, 'DECODER', 'Exporter comparison did not qualify')
            raw = directory / (event['image_id'] + '.raw.npy')
            read_bound({'path': str(raw), 'sha256': event['raw_output_sha256']})
            bindings.append(file_binding(raw))
    return values


def run(area):
    area = Path(area).resolve(); started, tick = utc(), time.perf_counter()
    output = area / 'private/comparison-01'
    require(not output.exists(), 'OUTPUT', 'Fresh comparison preparation required')
    output.mkdir(); (output / 'inputs').mkdir(); (output / 'oracle').mkdir(); (output / 'custody').mkdir()
    bindings = []
    def read(path):
        bindings.append(file_binding(path)); return json.loads(path.read_text())
    freeze = read(area / 'private/PROTOCOL_FREEZE.json')
    protocol = Path(__file__).with_name('PROTOCOL.md')
    require(file_binding(protocol)['sha256'] == freeze['protocol_sha256'], 'PROTOCOL', 'Frozen protocol changed')
    bindings.append(file_binding(protocol))
    allocation_path = area / 'private/FALLBACK_ALLOCATION_FREEZE.json'
    require(file_binding(allocation_path)['sha256'] == ALLOCATION_SHA256, 'ALLOCATION', 'Frozen exposure allocation changed')
    allocation = read(allocation_path)
    aa = export(area, 'export-06-64', 'yolo11n', bindings)
    bb = export(area, 'export-07-64', 'yolo26n', bindings)
    require(aa['ALLOCATION'] == bb['ALLOCATION'], 'ALLOCATION', 'Model populations differ')
    exports = [{row['id']: row for row in value['PACKET']['images']} for value in (aa, bb)]
    projection = area / 'private/projection-01'; projection_result = read(projection / 'RESULT.json')
    source_index = {row['image_id']: row for row in projection_result['images']}
    require(set(source_index) == {image['id'] for image in allocation['images']}, 'COVERAGE', 'Reference allocation differs')
    images, reviews, source_map = [], [], []
    for ordinal, allocated in enumerate(allocation['images']):
        iid = allocated['id']; source_path = projection / (iid + '.json'); source = read(source_path)
        require(digest(source) == source_index[iid]['record_sha256'], 'SOURCE', 'Projection bytes changed')
        require(source['image_id'] == iid and source['image_sha256'] == allocated['image_sha256'],
                'SOURCE', 'Projection and prediction image identity differ')
        operands, custody = [], {}
        for role, packet in zip(('output_a', 'output_b'), exports):
            operand, rows = prediction_operand(packet[iid]); operands.append(operand); custody[role] = rows
        answer, review = reference_operand(source, allocated)
        image = {'id': iid, 'ordinal': ordinal, 'width': allocated['width'], 'height': allocated['height'],
            'image_sha256': allocated['image_sha256'], 'policy_sha256': freeze['protocol_sha256'],
            'output_a': operands[0], 'output_b': operands[1], 'reference_input_state': review['state']}
        validate_image(image); images.append(image)
        reviews.append({'image_id': iid, **review})
        put(output / 'custody' / (iid + '.json'), {'predictions': custody, 'reference': review})
        if answer is not None:
            put(output / 'oracle' / (iid + '.json'), {'subject_sha256': subject(image), 'answer': answer,
                'source_sha256': file_binding(source_path)['sha256'], 'source_applicability': source['source_applicability']})
        source_map.append({'image_id': iid, 'source_applicability': source['source_applicability'],
                           'projection_binding': file_binding(source_path)})
    cases = [{'id': image['id'], 'group': 'singleton', 'images': [image['id']]} for image in images]
    cases += [{'id': 'block-' + str(index // 8).zfill(2), 'group': 'block',
               'images': [image['id'] for image in images[index:index + 8]]} for index in range(0, 64, 8)]
    cases.append({'id': 'all-64', 'group': 'primary', 'images': [image['id'] for image in images]})
    visible = {'artifact_id': 'reiyah.public-predictions.visible', 'version': '0.1.0',
        'images': images, 'cases': cases,
        'information': 'Fixed eligible prediction operands and source availability only. No reference count, digest, geometry or loss hint.'}
    put(output / 'inputs/visible.json', visible)
    put(output / 'custody/SOURCE_MAP.json', source_map)
    put(output / 'custody/REFERENCE_QUALIFICATION.json', {'images': reviews,
        'earlier_numeric_boundary_counterexample_retained': True,
        'actual_changed_selections': sum(row.get('exact_decimal_selection_changed', False) for row in reviews)})
    put(output / 'custody/SOURCE_BINDINGS.json', bindings)
    result = {'artifact_id': 'reiyah.public-predictions.comparison-preparation', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': utc(), 'seconds': time.perf_counter() - tick,
        'visible_sha256': digest(visible), 'images': len(images), 'cases': len(cases),
        'reference_available': sum(image['reference_input_state'] == 'available' for image in images),
        'prediction_available': [sum(image[role]['state'] == 'observed' for image in images) for role in ('output_a', 'output_b')],
        'source_bindings': len(bindings), 'scored_comparisons': 0, 'human_preparation_seconds': None,
        'rec_d_outcomes_accessed': 0}
    put(output / 'PREPARATION.json', result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    run(sys.argv[1])
