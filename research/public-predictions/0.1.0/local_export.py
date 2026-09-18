"""One frozen local development export, launched with networking denied.

Only the separately bound 64-image allocation and two named public checkpoints
are accepted. The cumulative cap charges the whole prediction call, including
preparation and the decoder cross-check, conservatively to inference time.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import time

from admission import admit, digest, encoded, require, validate_configuration

MODELS = {
    'yolo11n': ('0ebbc80d4a7680d14987a577cd21342b65ecfd94632bd9a8da63ae6417644ee1', 5613764, False),
    'yolo26n': ('9b09cc8bf347f0fc8a5f7657480587f25db09b34bf33b0652110fb03a8ad4fef', 5544453, True),
}
ALLOCATION_SHA256 = 'a565710df8c3253c2fd629776cef0fdd2d39c267575555c1bb40ca1aea0c5acd'
CAP_SECONDS = 3600


def utc():
    return datetime.now(timezone.utc).isoformat()


def file_digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_bound(binding):
    path = Path(binding['path'])
    require(path.is_absolute() and path.is_file() and not path.is_symlink(), 'SOURCE', 'Regular absolute source required')
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == binding['sha256'], 'SOURCE', 'Source digest differs')
    if 'bytes' in binding:
        require(len(raw) == binding['bytes'], 'SOURCE', 'Source byte length differs')
    return raw


def put(path, value):
    with Path(path).open('xb') as handle:
        handle.write(encoded(value))


def elapsed_limit(signum, frame):
    raise TimeoutError('Cumulative prediction-call budget reached')


def run(request_path, expected, output):
    started, tick = utc(), time.perf_counter()
    request = json.loads(read_bound({'path': str(Path(request_path).resolve()), 'sha256': expected}))
    require(request['artifact_id'] == 'reiyah.public-predictions.local-export-request' and request['version'] == '0.1.0',
            'REQUEST', 'Unknown export request')
    require(request['model_id'] in MODELS, 'MODEL', 'Checkpoint outside bounded fallback')
    checkpoint_sha, checkpoint_bytes, end_to_end = MODELS[request['model_id']]
    require(request['checkpoint']['sha256'] == checkpoint_sha and request['checkpoint']['bytes'] == checkpoint_bytes,
            'MODEL', 'Wrong frozen checkpoint')
    read_bound(request['checkpoint'])
    require(request['allocation_freeze']['sha256'] == ALLOCATION_SHA256, 'ALLOCATION', 'Allocation changed')
    frozen = json.loads(read_bound(request['allocation_freeze']))
    require(len(frozen['images']) == 64 and frozen['inference_before_this_freeze'] is False,
            'ALLOCATION', 'Frozen development population differs')
    all_images = {image['id']: image for image in frozen['images']}
    selected = request['image_ids']
    require(type(selected) is list and 0 < len(selected) <= 64 and len(set(selected)) == len(selected)
            and set(selected) <= set(all_images), 'ALLOCATION', 'Unknown, repeated or excessive image selection')
    output = Path(output).resolve()
    require(not output.exists() and output.parent.is_dir(), 'OUTPUT', 'Fresh owned output required')
    output.mkdir()
    configuration = request['configuration']; validate_configuration(configuration)
    require(configuration['checkpoint_sha256'] == checkpoint_sha and configuration['batch_size'] == 1
            and configuration['runtime']['device'] == 'cpu' and configuration['runtime']['precision'] == 'float32',
            'CONFIGURATION', 'Only frozen CPU FP32 batch-one export is in scope')
    post = configuration['postprocessing']
    require(post['confidence'] == 0.25 and post['maximum_detections'] == 300 and not post['multi_label']
            and not post['class_agnostic'] and post['method'] == ('end_to_end' if end_to_end else 'nms')
            and post['iou_threshold'] == (None if end_to_end else 0.7), 'CONFIGURATION', 'Postprocessing policy changed')
    for binding in request['code_bindings']:
        read_bound(binding)
    require(configuration['implementation_sha256'] == file_digest(__file__),
            'CONFIGURATION', 'Exporter implementation differs from configuration')
    require(configuration['rounding'] == 'none_source_float'
            and configuration['preprocessing']['color'] == 'BGR_decode_to_RGB_tensor'
            and configuration['preprocessing']['resize'] == '640_square_linear_center_pad_114_scaleup'
            and configuration['preprocessing']['normalization'] == 'float32_divide_255',
            'CONFIGURATION', 'Preprocessing or rounding policy changed')
    require(os.environ.get('YOLO_OFFLINE') == 'true' and os.environ.get('YOLO_AUTOINSTALL') == 'false',
            'ENVIRONMENT', 'Offline and no-install flags required before runtime import')
    # The launcher retains the actual sandbox-exec invocation. This environment
    # check is not itself proof of OS isolation.
    require(os.environ.get('REIYAH_EXPORT_NETWORK_POLICY') == 'deny-network',
            'ENVIRONMENT', 'Use the retained network-denied launcher')
    for directory in reversed(request['runtime_import_paths']):
        require(Path(directory).is_absolute() and Path(directory).is_dir(), 'RUNTIME', 'Explicit local imports required')
        sys.path.insert(0, directory)
    import cv2
    import numpy as np
    import torch
    import torchvision
    import ultralytics
    from ultralytics import YOLO
    from ultralytics.models.yolo.detect import DetectionPredictor
    from decode_check import compare, decode, letterbox_input

    require(torch.__version__ == '2.10.0' and torchvision.__version__ == '0.25.0'
            and ultralytics.__version__ == '8.4.155' and cv2.__version__ == '4.13.0',
            'RUNTIME', 'Pinned runtime versions differ')
    require(ultralytics.settings['sync'] is False and not ultralytics.settings['api_key']
            and not ultralytics.settings['openai_api_key'], 'RUNTIME', 'Private no-integration settings required')
    require(all(ultralytics.settings[name] is False for name in
                ('clearml', 'comet', 'dvc', 'mlflow', 'raytune', 'tensorboard', 'wandb')),
            'RUNTIME', 'External integrations must be disabled')
    torch.set_num_threads(2); torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True); torch.set_grad_enabled(False)
    # Zero disables OpenCV parallel regions and makes getNumThreads report one
    # on this GCD build; setting one does not change GCD's reported CPU count.
    torch.manual_seed(0); np.random.seed(0); cv2.setNumThreads(0)
    torch.set_float32_matmul_precision('highest')
    require(torch.get_num_threads() == 2 and cv2.getNumThreads() == 1, 'RUNTIME', 'Thread policy differs')

    class CheckedPredictor(DetectionPredictor):
        def preprocess(self, originals):
            value = super().preprocess(originals)
            separate = letterbox_input(originals[0], cv2)
            actual = value.detach().cpu().numpy()
            require(actual.shape == (1, 3, 640, 640) and actual.dtype == np.float32,
                    'PREPROCESS', 'Unexpected input tensor')
            difference = float(np.max(np.abs(actual - separate)))
            require(difference <= 1e-7, 'PREPROCESS', 'Separate letterbox construction differs')
            self.input_check = {'maximum_absolute_error': difference, 'tolerance': 1e-7,
                                'tensor_sha256': hashlib.sha256(actual.tobytes()).hexdigest()}
            return value

        def inference(self, value, *args, **kwargs):
            start = time.perf_counter()
            try:
                return super().inference(value, *args, **kwargs)
            finally:
                self.forward_seconds = time.perf_counter() - start

        def postprocess(self, predictions, image, originals, **kwargs):
            raw = predictions[0] if isinstance(predictions, (tuple, list)) else predictions
            self.raw = raw.detach().clone().cpu().numpy()
            require(self.model.end2end is end_to_end and not self.model.fp16
                    and str(self.model.device) == 'cpu', 'RUNTIME', 'Actual decoding mode/device/precision differs')
            results = super().postprocess(predictions, image, originals, **kwargs)
            require(len(results) == 1, 'BATCH', 'Exactly one result required')
            height, width = originals[0].shape[:2]
            check_start = time.perf_counter()
            separate = decode(self.raw, end_to_end=end_to_end, width=width, height=height)
            self.decode_check = compare(results[0].boxes.data.detach().cpu().numpy(), separate)
            self.decode_check['seconds'] = time.perf_counter() - check_start
            return results

    ledger = Path(request['budget_ledger'])
    require(ledger.is_absolute() and ledger.parent.is_dir(), 'BUDGET', 'Owned persistent budget ledger required')
    rows, evidence, fatal = [], [], None
    config_sha = digest(configuration)
    allocation = {'artifact_id': 'reiyah.public-predictions.allocation', 'version': '0.1.0',
        'exposure': 'development', 'population_id': request['allocation_id'],
        'membership_basis': 'retained_image_bytes', 'source_binding_sha256': ALLOCATION_SHA256,
        'images': [{key: all_images[iid][key] for key in ('id', 'width', 'height', 'image_sha256')} for iid in selected]}
    put(output / 'REQUEST.json', request); put(output / 'ALLOCATION.json', allocation)
    put(output / 'CONFIGURATION.json', configuration)
    with ledger.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        prior = [json.loads(line) for line in ledger.read_text().splitlines()] if ledger.exists() else []
        used = sum(row['prediction_call_seconds'] for row in prior)
        require(used < CAP_SECONDS, 'BUDGET', 'Prediction budget exhausted')
        setup_tick = time.perf_counter()
        model = YOLO(request['checkpoint']['path'], task='detect', verbose=False)
        model.model.eval()
        expected_names = {row['id']: row['name'] for row in configuration['categories']}
        require(model.names == expected_names, 'CATEGORIES', 'Checkpoint names differ from frozen class map')
        setup_seconds = time.perf_counter() - setup_tick
        kwargs = {'imgsz': 640, 'conf': 0.25, 'iou': 0.7, 'max_det': 300, 'device': 'cpu',
            'quantize': 32, 'batch': 1, 'rect': False, 'augment': False, 'agnostic_nms': False,
            'classes': None, 'nms': False if end_to_end else None, 'channels_last': False, 'compile': False,
            'data': None, 'save': False, 'save_txt': False, 'save_conf': False, 'save_crop': False,
            'show': False, 'visualize': False, 'verbose': False, 'stream': False}
        put(output / 'PREDICT_ARGUMENTS.json', kwargs)
        for iid in selected:
            source = all_images[iid]
            base = {key: source[key] for key in ('id', 'width', 'height', 'image_sha256')}
            base['configuration_sha256'] = config_sha
            if fatal is not None:
                rows.append({**base, 'state': 'missing', 'reason': 'Not executed after retained stage failure: ' + fatal})
                continue
            raw_bytes = read_bound({'path': source['image_path'], 'sha256': source['image_sha256'], 'bytes': source['bytes']})
            pixels = cv2.imdecode(np.frombuffer(raw_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
            require(pixels is not None and pixels.shape == (source['height'], source['width'], 3),
                    'IMAGE', 'Decoded image dimensions differ')
            remaining = CAP_SECONDS - used
            if remaining <= 0:
                fatal = 'Cumulative prediction-call cap reached'
                rows.append({**base, 'state': 'missing', 'reason': fatal})
                continue
            signal.signal(signal.SIGALRM, elapsed_limit)
            began = utc(); prediction_tick = time.perf_counter()
            event = {'model_id': request['model_id'], 'image_id': iid, 'request_sha256': expected,
                     'started_utc': began, 'state': 'running'}
            try:
                signal.setitimer(signal.ITIMER_REAL, remaining)
                results = model.predict(source=pixels, predictor=CheckedPredictor, **kwargs)
                predictor = model.predictor
                values = results[0].boxes.data.detach().cpu().numpy()
                require(np.isfinite(values).all() and np.equal(values[:, 5], np.floor(values[:, 5])).all(),
                        'OUTPUT', 'Nonfinite output or noninteger category')
                detections = [{'id': 'detection-' + str(n).zfill(3), 'category_id': int(value[5]),
                    'category_name': model.names[int(value[5])], 'score': float(value[4]),
                    'xyxy': [float(x) for x in value[:4]]} for n, value in enumerate(values)]
                row = {**base, 'state': 'processed' if detections else 'empty', 'detections': detections,
                       'source_detection_count': len(detections),
                       'empty_basis': None if detections else 'publisher_explicit_empty'}
                np.save(output / (iid + '.raw.npy'), predictor.raw, allow_pickle=False)
                event.update(state='exported', forward_seconds=predictor.forward_seconds,
                             preprocess_check=predictor.input_check, decode_check=predictor.decode_check,
                             publisher_speed_ms=results[0].speed,
                             raw_output_sha256=file_digest(output / (iid + '.raw.npy')))
                rows.append(row)
            except Exception as exc:
                fatal = type(exc).__name__ + ': ' + str(exc)
                event.update(state='failed', error=fatal)
                predictor = model.predictor
                if predictor is not None and hasattr(predictor, 'raw'):
                    np.save(output / (iid + '.failed.raw.npy'), predictor.raw, allow_pickle=False)
                    event['failed_raw_output_sha256'] = file_digest(output / (iid + '.failed.raw.npy'))
                if predictor is not None and hasattr(predictor, 'input_check'):
                    event['preprocess_check'] = predictor.input_check
                if predictor is not None and hasattr(predictor, 'forward_seconds'):
                    event['forward_seconds'] = predictor.forward_seconds
                rows.append({**base, 'state': 'failed', 'reason': fatal})
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                event['prediction_call_seconds'] = time.perf_counter() - prediction_tick
                event['finished_utc'] = utc()
                used += event['prediction_call_seconds']; event['cumulative_charged_seconds'] = used
                with ledger.open('ab') as log:
                    log.write(encoded(event)); log.flush(); os.fsync(log.fileno())
                evidence.append(event)
                put(output / (iid + '.json'), rows[-1])
                print(json.dumps({'image_id': iid, 'state': rows[-1]['state'],
                                  'prediction_call_seconds': event['prediction_call_seconds']}), flush=True)
    binding = {'request_sha256': expected, 'events': evidence}
    put(output / 'EXPORT_EVENTS.json', binding)
    packet = {'artifact_id': 'reiyah.public-predictions.packet', 'version': '0.1.0',
        'allocation_sha256': digest(allocation), 'configuration_sha256': config_sha,
        'checkpoint_sha256': checkpoint_sha, 'source_binding_sha256': digest(binding), 'images': rows}
    put(output / 'PACKET.json', packet)
    admission = admit(allocation, configuration, packet)
    put(output / 'ADMISSION.json', admission)
    result = {'artifact_id': 'reiyah.public-predictions.local-export-result', 'version': '0.1.0',
        'started_utc': started, 'finished_utc': utc(), 'seconds': time.perf_counter() - tick,
        'model_load_seconds': setup_seconds, 'cumulative_charged_prediction_seconds': used,
        'fatal_error': fatal, 'admission': admission,
        'scope': 'Public frozen model on already exposed development images. No training, human review or reserved outcomes.',
        'human_seconds': None, 'economic_cost': None}
    put(output / 'RESULT.json', result)
    print(json.dumps({'complete_usable_export': admission['complete_usable_export'], 'images': len(rows),
                      'cumulative_charged_prediction_seconds': used}), flush=True)
    return 0 if admission['complete_usable_export'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    parser.add_argument('--request-sha256', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    sys.exit(run(args.request, args.request_sha256, args.output))
