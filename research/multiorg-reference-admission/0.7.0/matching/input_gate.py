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
CONTRACT_SHA = '258d970b52a35f4b6ce0f4589608247b74cd1552175ae39dd9edbab4a0e25850'
IMAGES = ('MultiOrg_v2/test/Macros/Plate_4/image_7/image_7.tiff',
          'MultiOrg_v2/test/Macros/Plate_23/image_0/image_0.tiff',
          'MultiOrg_v2/test/Normal/Plate_31/image_6/image_6.tiff',
          'MultiOrg_v2/test/Macros/Plate_23/image_1/image_1.tiff')
PROCEDURES = ('t0', 't1_A', 't1_B')
COUNTS = dict(zip(IMAGES, ({'t0':88,'t1_A':61,'t1_B':64}, {'t0':72,'t1_A':27,'t1_B':82}, {'t0':76,'t1_A':33,'t1_B':69}, {'t0':88,'t1_A':27,'t1_B':73})))
SCOPE = 'all_declared_tiles_analysis_score_float32_strictly_gt_0.5_only'
STORAGE = 'not_defined_or_exported_by_this_contract'
MODELS = ('faster', 'yolo')
VARIANTS = {'faster': 'reiyah.multiorg.validity-preserving-export.observation/0.4.0',
            'yolo': 'MultiOrg-2026-released-YOLO-unchanged'}
MODEL_PINS = {'faster': 'a26f494f548ed8410a809252b2acaae97e2efa189fcee963a5b8a09dd4c13b63',
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


def analysis_rows(image, model, profile):
    identity = profile['image_id']; tiles = profile['tiles']
    require(image.get('artifact_id') == 'reiyah.multiorg.complete-analysis-image'
            and image.get('version') == profile['version'] and image.get('status') == 'complete', 'complete image required')
    require(image.get('image_id') == identity and image.get('model') == model, 'image/model identity')
    require(image.get('model_variant') == VARIANTS[model]
            and image.get('model_source_sha256') == MODEL_PINS[model], 'model variant/source binding')
    require(image.get('completion_scope') == SCOPE and image.get('storage_output_status') == STORAGE
            and 'storage_predictions' not in image, 'explicit analysis-only endpoint')
    equal([image.get('tile_count_expected'), image.get('tile_count_completed')], [tiles, tiles], 'complete tile counts')
    equal(image.get('image_shape_hw'), profile['image_shape_hw'], 'source image shape')
    equal(image.get('rescaled_shape_hw'), profile['rescaled_shape_hw'], 'rescaled image shape')
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
        require(type(row['tile_ordinal']) is int and 0 <= row['tile_ordinal'] < tiles
                and type(row['original_row_index']) is int and row['original_row_index'] >= 0, 'analysis tile/row identity')
        box = row['box_xyxy']
        require(type(box) is list and len(box) == 4 and all(type(v) is int and abs(v) <= 10000000 for v in box), 'native coordinate domain')
        require(box[0] < box[2] and box[1] < box[3], 'positive exact analysis geometry')
        score = row['score']
        require(type(score) in (int, Decimal) and Fraction(1, 2) < Fraction(score) <= 1, 'strict analysis score')
        identity = {'image': profile['image_id'], 'model': model, 'variant': VARIANTS[model], 'model_sha256': MODEL_PINS[model],
                    'id': row['id'], 'tile': row['tile_ordinal'], 'row': row['original_row_index'],
                    'xyxy': box, 'score': str(Fraction(score))}
        result.append((model + '-' + str(row['id']), tuple(Fraction(v) for v in box), sha(canonical(identity))))
    return result


def validate_profiles(contract):
    require(contract.get('profiles_status') == 'complete_prospective_bindings', 'prospective profiles not complete')
    equal(contract.get('images'), list(IMAGES), 'original selected image order')
    equal(contract.get('reference_counts'), COUNTS, 'original recorded reference counts')
    profiles = contract.get('profiles')
    require(type(profiles) is list and len(profiles) == 4, 'four explicit pair profiles')
    for index, profile in enumerate(profiles):
        keys(profile, ('image_id','image_sha256','image_shape_hw','rescaled_shape_hw','tiles','version',
             'worker_sha256','protocol_sha256','manifest_sha256','image_contract_sha256',
             *(('checker_sha256',) if index == 0 else ('admission','consumer_sha256','resource_gate_sha256','numerical_checker_sha256','resource_contract_sha256'))), 'profile schema')
        require(profile['image_id'] == IMAGES[index] and profile['version'] == ('0.5.0' if index == 0 else '0.6.0'), 'explicit per-image version')
        for name in ('image_sha256','worker_sha256','protocol_sha256','manifest_sha256',
                     *(('checker_sha256',) if index == 0 else ('consumer_sha256','resource_gate_sha256','numerical_checker_sha256','resource_contract_sha256'))):
            require(type(profile[name]) is str and HEX.fullmatch(profile[name]), 'prospective digest '+name)
        if index > 0: require(profile['admission'] == 'resource_qualified', 'resource composition admission required')
        for name in ('image_shape_hw','rescaled_shape_hw'):
            require(type(profile[name]) is list and len(profile[name]) == 2
                    and all(type(v) is int and v > 0 for v in profile[name]), 'prospective image shape')
        h,w = profile['rescaled_shape_hw']
        require(type(profile['tiles']) is int and profile['tiles'] == len(range(0,h,256))*len(range(0,w,256))
                and 0 < profile['tiles'] <= 512, 'prospective complete lattice')
        equal(profile['rescaled_shape_hw'], [max(1,round(v/2)) for v in profile['image_shape_hw']], 'prospective rescale shape')
        require(profile['image_contract_sha256'] is None if index == 0 else
                type(profile['image_contract_sha256']) is str and HEX.fullmatch(profile['image_contract_sha256']), 'image contract digest')
    return profiles


def resource_module(profile):
    import types
    raw = read(HERE/'resource_gate.py', profile['resource_gate_sha256'])
    module = types.ModuleType('_bound_resource_gate')
    exec(compile(raw, str(HERE/'resource_gate.py'), 'exec'), module.__dict__)
    return module


def admit_resource(bundle, profile, check, process, execution):
    """Consume the wrapper explicitly; never manufacture a legacy checker report."""
    require(check.get('artifact_id') == 'reiyah.multiorg.resource-qualified-pair-check'
            and check.get('version') == '0.1.0', 'resource wrapper identity required')
    for name in ('consumer_sha256','resource_gate_sha256','numerical_checker_sha256'):
        require(check.get(name) == profile[name], 'qualified resource component '+name)
    require('checker_sha256' not in check, 'resource wrapper must not impersonate numerical checker')
    equal([check.get('status'),check.get('complete_pairs')],['complete_pair_verified',1], 'resource wrapper completion')
    require(bundle['resource_contract']['sha256'] == profile['resource_contract_sha256']
            and check.get('contract_sha256') == profile['resource_contract_sha256'], 'prospective resource contract')
    contract = descriptor(bundle['resource_contract']); sources = contract['sources']; paths = contract['paths']
    require(contract.get('artifact_id') == 'reiyah.multiorg.resource-consumer-contract' and contract.get('version') == '0.1.0', 'consumer contract identity')
    rg = resource_module(profile)
    for name,digest in {'worker':profile['worker_sha256'],'supervisor':rg.SUPERVISOR,
            'numerical_checker':profile['numerical_checker_sha256'],'manifest':profile['manifest_sha256'],
            'protocol':profile['protocol_sha256']}.items():
        require(sources[name]['sha256'] == digest, 'resource contract source '+name)
    for name in ('contract_sha256','freeze_sha256'):
        require(type(check.get(name)) is str and HEX.fullmatch(check[name]), 'wrapper digest '+name)
    root = Path(paths['output']); owner = Path(paths['freeze']).parent
    require(str(root/'result.json') == bundle['pair']['path']
            and str(root.with_suffix('.process.json')) == bundle['supervisor']['path'], 'resource output paths')
    observations = check.get('observations')
    keys(observations, ('outer','stdout','stderr','process_receipt','journal','policy','worker_log','runtime_after','result'), 'resource observation roster')
    expected_paths = {'outer':paths['outer'],'stdout':paths['stdout'],'stderr':paths['stderr'],
        'process_receipt':bundle['supervisor']['path'],'journal':str(root.with_suffix('.resources.jsonl')),
        'policy':str(root.with_suffix('.sandbox.sb')),'worker_log':str(root.with_suffix('.log')),
        'runtime_after':paths['runtime_after'],'result':bundle['pair']['path']}
    raw = {}
    for name,d in observations.items():
        keys(d,('path','sha256','bytes'),'resource observation descriptor')
        require(d['path'] == expected_paths[name], 'resource observation path '+name)
        raw[name] = read(d['path'],d['sha256'],16*1024*1024)
        require(type(d['bytes']) is int and len(raw[name]) == d['bytes'], 'resource observation length '+name)
    require(observations['process_receipt']['sha256'] == bundle['supervisor']['sha256']
            and observations['result']['sha256'] == bundle['pair']['sha256'], 'resource exact process/result identity')
    require(raw['stderr'] == b'' and sha(raw['policy']) == rg.POLICY, 'resource stderr/policy')
    outer = rg.parse(raw['outer']); returned = rg.parse(raw['stdout']); receipt = rg.parse(raw['process_receipt'])
    plan = rg.parse(read(sources['capacity_plan']['path'], sources['capacity_plan']['sha256'],1048576))
    command = [contract['python_entrypoint'],'-B',sources['supervisor']['path'],'--owner',str(owner),
        '--manifest',sources['manifest']['path'],'--runner',sources['worker']['path'],'--runner-sha256',profile['worker_sha256'],
        '--python',contract['python_entrypoint'],'--output',str(root),'--capacity-plan',sources['capacity_plan']['path'],
        '--capacity-plan-sha256',sources['capacity_plan']['sha256']]
    worker = ['/usr/bin/sandbox-exec','-f',expected_paths['policy'],contract['python_entrypoint'],'-B',sources['worker']['path'],
        '--worker','--manifest',sources['manifest']['path'],'--output',str(root)]
    expected = {'outer_wall_limit_seconds':float(contract['outer_wall_limit_seconds']),
        'outer':{'command':command,'freeze_sha256':check['freeze_sha256'],'supervisor_sha256':rg.SUPERVISOR,
            'manifest_sha256':profile['manifest_sha256'],'stdout_sha256':sha(raw['stdout']),'stderr_sha256':sha(raw['stderr']),
            'worker_log_sha256':sha(raw['worker_log']),'worker_log_bytes':len(raw['worker_log'])},
        'receipt':{'manifest_sha256':profile['manifest_sha256'],'capacity_plan_sha256':sources['capacity_plan']['sha256'],
            'capacity_plan':plan,'result_sha256':bundle['pair']['sha256'],'resource_samples_sha256':sha(raw['journal']),
            'sample_journal':Path(expected_paths['journal']).name,'log':Path(expected_paths['worker_log']).name,
            'command':worker,'limits':{'wall_seconds':600,'memory_bytes':3221225472}}}
    gate = rg.validate_success(receipt, returned, outer, rg.journal_rows(raw['journal']), expected)
    equal(check.get('resource_admission'), gate, 'resource gate recomputation')
    runtime = check.get('runtime')
    require(type(runtime) is dict and runtime.get('status') == 'runtime_report_and_current_declared_bytes_checked', 'qualified runtime report')
    reconstruction = check.get('input_reconstruction',{})
    require(reconstruction.get('status') == 'all_declared_tensor_identities_reconstructed', 'qualified input reconstruction')
    for name,value in {'image_id':profile['image_id'],'image_sha256':profile['image_sha256'],'version':'0.6.0',
            'tensor_count':2*profile['tiles'],'tiles_per_model':profile['tiles']}.items():
        equal(reconstruction.get(name),value,'input reconstruction '+name)
    freeze = descriptor({'path':paths['freeze'],'sha256':check['freeze_sha256']})
    bindings = freeze.get('bindings'); require(type(bindings) is dict, 'execution freeze bindings')
    required = {bundle['resource_contract']['path']:profile['resource_contract_sha256'],
        str(owner/'consumer/check_pair_resource.py'):profile['consumer_sha256'],str(owner/'consumer/resource_gate.py'):profile['resource_gate_sha256'],
        **{d['path']:d['sha256'] for d in sources.values()}}
    for path,digest in required.items():
        relative = str(Path(path).relative_to(owner)); require(bindings.get(relative,{}).get('sha256') == digest, 'frozen consumer component '+relative)
    require(type(check.get('frozen_files_checked_before_and_after')) is int
            and check['frozen_files_checked_before_and_after'] == len(bindings), 'complete checked freeze roster')
    keys(execution, ('artifact_id','version','returncode','timed_out','wall_seconds','report_sha256','consumer_sha256',
        'resource_gate_sha256','numerical_checker_sha256','contract_sha256','freeze_sha256','command'), 'resource consumer execution schema')
    equal([execution['artifact_id'],execution['version'],execution['returncode'],execution['timed_out']],
        ['reiyah.multiorg.resource-consumer-execution','0.1.0',0,False], 'successful resource consumer execution')
    require(type(execution['wall_seconds']) in (int,Decimal) and 0<=execution['wall_seconds']<=330, 'consumer execution wall bound')
    require(execution['report_sha256'] == bundle['pair_checker']['sha256'], 'consumer execution report binding')
    for name in ('consumer_sha256','resource_gate_sha256','numerical_checker_sha256','contract_sha256','freeze_sha256'):
        require(execution[name] == check[name], 'consumer execution component '+name)
    policy = owner/'execution/shared/check.sandbox.sb'; require(sha(read(policy,cap=4096)) == rg.POLICY, 'consumer network policy')
    expected_command = ['/usr/bin/sandbox-exec','-f',str(policy),contract['python_entrypoint'],'-B',str(owner/'consumer/check_pair_resource.py'),
        '--owner',str(owner),'--contract',bundle['resource_contract']['path'],'--contract-sha256',profile['resource_contract_sha256'],
        '--freeze-sha256',check['freeze_sha256'],'--report',bundle['pair_checker']['path']]
    equal(execution['command'],expected_command,'consumer execution command')
    numeric = check.get('numerical_result')
    require(type(numeric) is dict, 'nested numerical result required')
    equal([numeric.get('status'),numeric.get('complete_pairs'),numeric.get('failure_sha256'),numeric.get('unbound_partial_array_files'),numeric.get('terminal_semantic_refusal')],
        ['complete_pair_verified',1,None,[],None], 'nested complete numerical result')
    require(numeric.get('scope') == SCOPE and numeric.get('storage_output_status') == STORAGE, 'nested numerical endpoint scope')
    return numeric


def admit_pair(bundle, profile):
    resource = profile.get('admission') == 'resource_qualified'
    keys(bundle, ('image_id','pair','supervisor','pair_checker','checker_execution', *(('resource_contract',) if resource else ())), 'pair bundle schema')
    identity, tiles = profile['image_id'], profile['tiles']
    require(bundle['image_id'] == identity, 'pair bundle identity/order')
    pair = descriptor(bundle['pair']); process = descriptor(bundle['supervisor'],1048576)
    check = descriptor(bundle['pair_checker']); execution = descriptor(bundle['checker_execution'],1048576)
    if resource: numeric = admit_resource(bundle, profile, check, process, execution)
    else: numeric = check
    require(pair.get('artifact_id') == 'reiyah.multiorg.complete-analysis-pair'
            and pair.get('version') == profile['version'] and pair.get('status') == 'complete'
            and pair.get('stage') == 'complete', 'complete exact-version pair required')
    if profile['version'] == '0.6.0':
        require(pair.get('image_id') == identity and pair.get('image_contract_sha256') == profile['image_contract_sha256'], 'new selected-image contract')
        require(check.get('image_id') == identity and check.get('image_contract_sha256') == profile['image_contract_sha256'], 'new checker selected-image contract')
    require(pair.get('completion_scope') == SCOPE and pair.get('storage_output_status') == STORAGE
            and 'storage_predictions' not in pair, 'pair analysis-only scope')
    equal(pair.get('model_variants'),VARIANTS,'pair variants')
    equal([pair.get('forward_passes_started'),pair.get('forward_passes_completed')],[2*tiles,2*tiles],'complete forward roster')
    equal(pair.get('tile_coverage'),{k:{'captured':tiles,'admitted':tiles,'complete':True} for k in MODELS},'complete pair coverage')
    require(pair.get('runner_sha256') == profile['worker_sha256'] and (resource or check.get('checker_sha256') == profile['checker_sha256']), 'qualified pair worker/checker')
    require(pair.get('manifest_sha256') == profile['manifest_sha256']
            and pair.get('protocol_sha256') == profile['protocol_sha256'], 'prospective pair manifest/protocol')
    require(process.get('status') == 'complete' and type(process.get('returncode')) is int and process['returncode'] == 0
            and process.get('termination_reason') is None and process.get('runner_sha256') == profile['worker_sha256'], 'successful supervisor')
    require(process.get('result_sha256') == bundle['pair']['sha256']
            and process.get('manifest_sha256') == profile['manifest_sha256'], 'supervisor result/manifest binding')
    require(check.get('status') == 'complete_pair_verified' and type(check.get('complete_pairs')) is int
            and check['complete_pairs'] == 1, 'whole-pair checker complete state')
    require(numeric.get('result_sha256') == bundle['pair']['sha256']
            and (resource or check.get('process_receipt_sha256') == bundle['supervisor']['sha256'])
            and check.get('manifest_sha256') == profile['manifest_sha256'], 'checker pair/process/manifest binding')
    if not resource:
        require(type(execution.get('returncode')) is int and execution['returncode'] == 0
                and execution.get('report_sha256') == bundle['pair_checker']['sha256']
                and execution.get('checker_sha256') == profile['checker_sha256'], 'checker execution binding')
    pins = {'image':profile['image_sha256'],'protocol':profile['protocol_sha256'],**MODEL_PINS}
    for key,digest in pins.items():
        require(check.get('source_bindings',{}).get(key) == digest
                and pair.get('source_bindings',{}).get(key,{}).get('sha256') == digest, 'qualified pair source '+key)
    equal(numeric.get('observations'),pair.get('observations'),'checker exact observation files')
    observed = pair['observations']; require(type(observed) is list and len(observed) == 2,'complete model observation count')
    images,converted = {},{}; root=Path(bundle['pair']['path']).parent
    for model,obs in zip(MODELS,observed):
        require(obs.get('model') == model and obs.get('image_id') == identity and obs.get('model_variant') == VARIANTS[model], 'observation roster')
        filename=obs.get('file')
        require(type(filename) is str and Path(filename).name == filename and filename.endswith('.json'),'observation local filename')
        raw=read(root/filename,obs.get('sha256')); require(type(obs.get('bytes')) is int and len(raw)==obs['bytes'],'observation byte count')
        image=decode(raw); converted[model]=analysis_rows(image,model,profile); images[model]=image
        require(type(obs.get('analysis_count')) is int and obs['analysis_count']==len(converted[model]),'observation analysis count')
        require(image.get('protocol_sha256') == profile['protocol_sha256'],'image protocol identity')
    return images,converted


def load_inputs(input_path,input_sha,repository):
    contract,deps=dependencies(repository); profiles=validate_profiles(contract)
    m=decode(read(input_path,input_sha,1048576))
    keys(m,('artifact_id','version','contract_sha256','pairs','reference_manifest','reference_root'),'cohort matching input schema')
    require(m['artifact_id']=='reiyah.multiorg.selected-cohort-matching-input' and m['version']=='0.7.0'
            and m['contract_sha256']==CONTRACT_SHA,'matching input contract')
    require(type(m['pairs']) is list and len(m['pairs'])==4,'four complete pair bundles required')
    equal([b.get('image_id') for b in m['pairs']],list(IMAGES),'complete selected pair roster')
    images,predictions={},{}
    for bundle,profile in zip(m['pairs'],profiles):
        identity=profile['image_id'];images[identity],predictions[identity]=admit_pair(bundle,profile)
    require(m['reference_manifest']['sha256']==contract['reference_manifest_sha256'],'original reference manifest required')
    manifest=descriptor(m['reference_manifest'])
    require(manifest.get('artifact_id')=='reiyah.multiorg.annotation-manifest' and manifest.get('version')=='0.1.0','reference manifest identity')
    require(type(manifest.get('images')) is list and len(manifest['images'])==55,'whole reference manifest roster')
    root=Path(m['reference_root']).resolve(strict=True);references={}
    for identity in IMAGES:
        matches=[v for v in manifest['images'] if v['tiff_path']==identity];require(len(matches)==1,'selected reference image membership')
        refs={}
        for d in matches[0]['annotations']:
            proc=d['procedure'];require(proc in PROCEDURES and proc not in refs and d['transport_valid'] is True,'reference procedure/transport')
            path=root/d['local_path'];require(path.resolve(strict=True).is_relative_to(root),'reference path confinement')
            raw=read(path,d['sha256']);require(len(raw)==d['byte_size'],'reference byte count')
            value=decode(raw);require(type(value) is dict and len(value)==COUNTS[identity][proc],'original recorded reference count')
            refs[proc]={'raw':raw,'value':value,'source_path':d['source_path'],'sha256':d['sha256']}
        require(set(refs)==set(PROCEDURES),'three complete recorded procedures')
        references[identity]=refs
    context={'contract_sha256':CONTRACT_SHA,'input_sha256':input_sha,'reference_manifest_sha256':m['reference_manifest']['sha256'],
             'model_variants':VARIANTS,'pairs':[{'image_id':b['image_id'],'pair_sha256':b['pair']['sha256'],
                  'pair_check_report_sha256':b['pair_checker']['sha256'],
                  'admission':'legacy_complete_pair' if index==0 else 'resource_qualified_pair',
                  'report_producer_sha256':profiles[index].get('consumer_sha256',profiles[index].get('checker_sha256')),
                  'numerical_checker_sha256':profiles[index].get('numerical_checker_sha256',profiles[index].get('checker_sha256')),
                  'resource_gate_sha256':profiles[index].get('resource_gate_sha256')} for index,b in enumerate(m['pairs'])],
             'references':[{'image_id':i,'procedure':p,'source_path':references[i][p]['source_path'],
                  'sha256':references[i][p]['sha256']} for i in IMAGES for p in PROCEDURES]}
    return {'manifest':m,'context':context,'context_sha256':sha(canonical(context)),'images':images,
            'predictions':predictions,'references':references,'native_dependencies':deps}
