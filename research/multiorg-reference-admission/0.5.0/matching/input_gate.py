"""Shared custody/analysis-endpoint admission, not an independent numeric oracle."""
from decimal import Decimal
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
CONTRACT_SHA = '1976a39b7b91dabd916f7aa253a6f65957cfbf1f9bc195e3388e6f3262a34854'
IMAGE = 'MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff'
PROCEDURES = ('t0', 't1_A', 't1_B')
COUNTS = {'t0': 88, 't1_A': 61, 't1_B': 64}
SCOPE = 'all_declared_tiles_analysis_score_float32_strictly_gt_0.5_only'
STORAGE = 'not_defined_or_exported_by_this_contract'
MODELS = ('faster', 'yolo')
VARIANTS = {'faster': 'reiyah.multiorg.validity-preserving-export.observation/0.4.0',
            'yolo': 'MultiOrg-2026-released-YOLO-unchanged'}
PINS = {'image': '8828e0a9f94d6c44ea03be2e62623e812830f339d9c905b7a368edcb7e821eb0',
        'faster': 'a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63',
        'yolo': '02ed40f0cbdcf9023390e9723a1c310d5dd3f4d18a3ad1c3774f71ff74969ee6'}
HEX = re.compile('[0-9a-f]{64}\\Z')


def require(value, message):
    if not value: raise ValueError(message)


def sha(raw): return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()


def read(path, digest=None, cap=64 * 1024 * 1024):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'bound regular file required')
    require(path.stat().st_size <= cap, 'bound file size cap')
    raw = path.read_bytes()
    if digest is not None:
        require(type(digest) is str and HEX.fullmatch(digest) and sha(raw) == digest, 'bound file digest')
    return raw


def decode(raw):
    def unique(items):
        result = {}
        for key, value in items:
            require(key not in result, 'duplicate JSON property')
            result[key] = value
        return result
    def bad(_): raise ValueError('nonfinite JSON number')
    return json.loads(raw, object_pairs_hook=unique, parse_float=Decimal, parse_constant=bad)


def keys(value, expected, message):
    require(type(value) is dict and set(value) == set(expected), message)


def equal(a, b, message):
    # Preserve booleans versus integers; JSON floats are parsed exactly as decimals.
    if type(a) is not type(b): raise ValueError(message)
    if isinstance(a, dict):
        require(set(a) == set(b), message)
        for key in a: equal(a[key], b[key], message)
    elif isinstance(a, list):
        require(len(a) == len(b), message)
        for left, right in zip(a, b): equal(left, right, message)
    else: require(a == b, message)


def descriptor(value, cap=64 * 1024 * 1024):
    keys(value, ('path', 'sha256'), 'file descriptor schema')
    require(type(value['path']) is str and Path(value['path']).is_absolute(), 'absolute bound path')
    return decode(read(value['path'], value['sha256'], cap))


def dependencies(repository):
    contract = decode(read(HERE / 'contract.json', CONTRACT_SHA))
    mapping = decode(read(HERE / 'DEPENDENCIES.json', contract['native_dependency_map_sha256']))
    repository = Path(repository).resolve(strict=True)
    for name, digest in mapping.items(): read(repository / name, digest)
    return contract, mapping


def native(repository):
    _, mapping = dependencies(repository)
    repository = Path(repository).resolve(strict=True)
    sys.path.insert(0, str(repository))
    path = repository / 'research/multiorg-reference-admission/0.2.0/compare.py'
    spec = importlib.util.spec_from_file_location('_bound_fixed_case', path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    for name, loaded in list(sys.modules.items()):
        if name.startswith(('tools.perception_revision.', 'tools.perception_decision.')):
            actual = Path(loaded.__file__).resolve()
            require(actual.is_relative_to(repository), 'mixed native module roots')
            relative = str(actual.relative_to(repository))
            require(relative in mapping, 'unbound native module')
            read(actual, mapping[relative])
    return module


def analysis_rows(image, model):
    require(image.get('artifact_id') == 'reiyah.multiorg.complete-analysis-image'
            and image.get('version') == '0.5.0' and image.get('status') == 'complete', 'complete image required')
    require(image.get('image_id') == IMAGE and image.get('model') == model, 'image/model identity')
    require(image.get('model_variant') == VARIANTS[model]
            and image.get('model_source_sha256') == PINS[model], 'model variant/source binding')
    require(image.get('completion_scope') == SCOPE and image.get('storage_output_status') == STORAGE
            and 'storage_predictions' not in image, 'explicit analysis-only endpoint')
    equal([image.get('tile_count_expected'), image.get('tile_count_completed')], [156, 156], 'complete tile counts')
    equal(image.get('image_shape_hw'), [5720, 6385], 'source image shape')
    equal(image.get('rescaled_shape_hw'), [2860, 3192], 'rescaled image shape')
    raw_count = image.get('raw_onnx_rows')
    require(type(raw_count) is int and 0 <= raw_count <= 200000, 'raw row cap')
    rows = image.get('analysis_predictions')
    require(type(rows) is list and len(rows) <= 1024, 'analysis detections missing or native detection cap')
    require(type(image.get('empty_analysis')) is bool and image['empty_analysis'] == (not rows), 'empty versus missing')
    seen = set(); result = []
    for row in rows:
        keys(row, ('id', 'tile_ordinal', 'original_row_index', 'box_xyxy', 'score'), 'analysis row schema')
        require(type(row['id']) is int and 0 <= row['id'] < raw_count and row['id'] not in seen, 'analysis identity')
        seen.add(row['id'])
        require(type(row['tile_ordinal']) is int and 0 <= row['tile_ordinal'] < 156
                and type(row['original_row_index']) is int and row['original_row_index'] >= 0, 'analysis tile/row identity')
        box = row['box_xyxy']
        require(type(box) is list and len(box) == 4 and all(type(v) is int and abs(v) <= 10000000 for v in box), 'native coordinate domain')
        require(box[0] < box[2] and box[1] < box[3], 'positive exact analysis geometry')
        score = row['score']
        require(type(score) in (int, Decimal) and Fraction(1, 2) < Fraction(score) <= 1, 'strict analysis score')
        identity = {'image': IMAGE, 'model': model, 'variant': VARIANTS[model], 'model_sha256': PINS[model],
                    'id': row['id'], 'tile': row['tile_ordinal'], 'row': row['original_row_index'],
                    'xyxy': box, 'score': str(Fraction(score))}
        result.append((model + '-' + str(row['id']), tuple(Fraction(v) for v in box), sha(canonical(identity))))
    return result


def load_inputs(input_path, input_sha, repository):
    contract, deps = dependencies(repository)
    m = decode(read(input_path, input_sha, 1048576))
    keys(m, ('artifact_id', 'version', 'contract_sha256', 'pair', 'supervisor', 'pair_checker',
             'checker_execution', 'reference_manifest', 'reference_root'), 'matching input schema')
    require(m['artifact_id'] == 'reiyah.multiorg.analysis-matching-input' and m['version'] == '0.5.0'
            and m['contract_sha256'] == CONTRACT_SHA, 'matching input contract')
    pair = descriptor(m['pair']); process = descriptor(m['supervisor'], 1048576)
    check = descriptor(m['pair_checker']); execution = descriptor(m['checker_execution'], 1048576)
    require(pair.get('artifact_id') == 'reiyah.multiorg.complete-analysis-pair' and pair.get('version') == '0.5.0'
            and pair.get('status') == 'complete' and pair.get('stage') == 'complete', 'complete pair required')
    require(pair.get('completion_scope') == SCOPE and pair.get('storage_output_status') == STORAGE, 'pair analysis scope')
    equal(pair.get('model_variants'), VARIANTS, 'pair variant identities')
    equal([pair.get('forward_passes_started'), pair.get('forward_passes_completed')], [312, 312], 'complete forward roster')
    equal(pair.get('tile_coverage'), {k: {'captured': 156, 'admitted': 156, 'complete': True} for k in MODELS}, 'complete pair coverage')
    require(process.get('status') == 'complete' and type(process.get('returncode')) is int and process['returncode'] == 0
            and process.get('termination_reason') is None and process.get('runner_sha256') == pair.get('runner_sha256'), 'successful supervisor')
    require(pair.get('runner_sha256') == contract['qualified_pair_worker_sha256'], 'qualified pair worker')
    require(process.get('result_sha256') == m['pair']['sha256']
            and process.get('manifest_sha256') == pair.get('manifest_sha256'), 'supervisor result/manifest binding')
    require(check.get('status') == 'complete_pair_verified' and type(check.get('complete_pairs')) is int and check['complete_pairs'] == 1,
            'whole-pair checker complete state')
    require(check.get('checker_sha256') == contract['qualified_pair_checker_sha256'], 'qualified pair checker')
    require(check.get('result_sha256') == m['pair']['sha256']
            and check.get('process_receipt_sha256') == m['supervisor']['sha256']
            and check.get('manifest_sha256') == pair.get('manifest_sha256'), 'checker pair/process/manifest binding')
    require(type(execution.get('returncode')) is int and execution['returncode'] == 0
            and execution.get('report_sha256') == m['pair_checker']['sha256']
            and execution.get('checker_sha256') == check.get('checker_sha256'), 'checker execution binding')
    for key, digest in PINS.items():
        require(check.get('source_bindings', {}).get(key) == digest
                and pair.get('source_bindings', {}).get(key, {}).get('sha256') == digest, 'qualified model/image source')
    equal(check.get('observations'), pair.get('observations'), 'checker observation bytes')
    observed = pair['observations']; require(type(observed) is list and len(observed) == 2, 'complete model observation count')
    images, converted = {}, {}
    root = Path(m['pair']['path']).parent
    for model, obs in zip(MODELS, observed):
        require(obs.get('model') == model and obs.get('image_id') == IMAGE and obs.get('model_variant') == VARIANTS[model], 'observation roster')
        filename = obs.get('file')
        require(type(filename) is str and Path(filename).name == filename and filename.endswith('.json'), 'local observation path')
        raw = read(root / filename, obs.get('sha256')); require(type(obs.get('bytes')) is int and len(raw) == obs['bytes'], 'observation byte count')
        image = decode(raw); converted[model] = analysis_rows(image, model); images[model] = image
        require(type(obs.get('analysis_count')) is int and obs['analysis_count'] == len(converted[model]), 'observation analysis count')
    require(m['reference_manifest']['sha256'] == contract['reference_manifest_sha256'], 'original reference manifest required')
    manifest = descriptor(m['reference_manifest'])
    require(manifest.get('artifact_id') == 'reiyah.multiorg.annotation-manifest' and manifest.get('version') == '0.1.0', 'reference manifest identity')
    require(type(manifest.get('images')) is list and len(manifest['images']) == 55, 'whole reference manifest roster')
    matches = [v for v in manifest['images'] if v['tiff_path'] == IMAGE]; require(len(matches) == 1, 'first image reference membership')
    root = Path(m['reference_root']).resolve(strict=True); references = {}
    for d in matches[0]['annotations']:
        procedure = d['procedure']; require(procedure in PROCEDURES and procedure not in references and d['transport_valid'] is True, 'reference procedure/transport')
        path = root / d['local_path']; require(path.resolve(strict=True).is_relative_to(root), 'reference path confinement')
        raw = read(path, d['sha256']); require(len(raw) == d['byte_size'], 'reference byte count')
        value = decode(raw); require(type(value) is dict and len(value) == COUNTS[procedure], 'recorded reference count')
        references[procedure] = {'raw': raw, 'value': value, 'source_path': d['source_path'], 'sha256': d['sha256']}
    require(set(references) == set(PROCEDURES), 'three complete recorded procedures')
    context = {'contract_sha256': CONTRACT_SHA, 'input_sha256': input_sha, 'pair_sha256': m['pair']['sha256'],
               'reference_manifest_sha256': m['reference_manifest']['sha256'], 'model_variants': VARIANTS,
               'references': {p: {'source_path': references[p]['source_path'], 'sha256': references[p]['sha256']} for p in PROCEDURES}}
    return {'manifest': m, 'context': context, 'context_sha256': sha(canonical(context)), 'images': images,
            'predictions': converted, 'references': references, 'native_dependencies': deps}
