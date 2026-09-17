"""Development comparison with common information, explicit queries and checked stopping.

This is an offline experiment, not product runtime. Answers are synthetic premises.
No corrected-reference container is read. Run prepare.py before this file.
"""
from copy import deepcopy
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.perception_revision import audit, audit_checker, contract
from tools.perception_revision import localization, localization_checker
from tools.perception_revision import monotone_plan
from tools.perception_revision.monotone_checker import confirmation_lower_bound
from tools.perception_decision.kernel import _matching_certificate

VERSION = '0.1.0'


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def put(path, value):
    with Path(path).open('xb') as out:
        out.write(encoded(value))


def utc():
    return datetime.now(timezone.utc).isoformat()


def labels(case):
    return [(a['id'], o['id']) for a in case['anchors'] for o in a['reference']['objects']]


def additions(case):
    return all({d['id'] for d in a['output_a']['value']} <=
               {d['id'] for d in a['output_b']['value']} for a in case['anchors'])


def request_for(case, observations=()):
    return {'artifact_id': 'reiyah.perception-revision.audit-request', 'version': VERSION,
            'comparison_id': case['comparison_id'],
            'reference_context_sha256': case['reference_context_sha256'],
            'family': 'reference_deletions', 'deletion_budget': len(labels(case)),
            'observation_basis': 'hypothetical', 'observations': list(observations)}


def subject(case, key):
    anchor = next(a for a in case['anchors'] if a['id'] == key[0])
    obj = next(o for o in anchor['reference']['objects'] if o['id'] == key[1])
    return sha(encoded({'cohort': case['cohort_id'],
                        'context': case['reference_context_sha256'],
                        'anchor': key[0], 'object': obj}))


class ObservationService:
    """Only query() reveals an answer; policies receive no service or answer table."""
    def __init__(self, case, input_sha, answers):
        self.__case = case
        self.__answers = dict(answers)
        self.__input_sha = input_sha
        self.__seen = set()
        if set(self.__answers) != set(labels(case)):
            raise ValueError('Incomplete or unknown answer population')
        if any(v not in ('present', 'absent', 'unresolved') for v in answers.values()):
            raise ValueError('Invalid observation answer')

    def query(self, key, expected_subject, method):
        started = utc(); tick = time.perf_counter()
        if key in self.__seen or key not in self.__answers:
            raise ValueError('Repeated or unknown query')
        if expected_subject != subject(self.__case, key):
            raise ValueError('Observation subject/context mismatch')
        self.__seen.add(key)
        answer = self.__answers[key]
        event = {'sequence': len(self.__seen), 'anchor': key[0], 'object': key[1],
                 'subject_sha256': expected_subject, 'requested_precision': 'exact_presence',
                 'answer': answer, 'residual_uncertainty': 'none_within_declared_family' if answer != 'unresolved' else 'presence_unknown',
                 'basis': 'hypothetical', 'source_input_sha256': self.__input_sha,
                 'cohort_id': self.__case['cohort_id'],
                 'reference_context_sha256': self.__case['reference_context_sha256'],
                 'source_applicability': 'same_bound_development_reference_subject',
                 'method_version': method + ':' + VERSION,
                 'requested_utc': started, 'returned_utc': utc(),
                 'cost': {'observation_units': 1, 'human_seconds': None,
                          'human_cost': None, 'service_seconds': time.perf_counter() - tick}}
        event['evidence_sha256'] = sha(encoded(event))
        return event


def observation(event):
    if event['answer'] == 'unresolved':
        return None
    return {k: event[k] for k in ('anchor', 'object', 'evidence_sha256')} | {'outcome': event['answer']}


def rank(left, edges):
    """Conventional augmenting-path matcher, separate from Engine matching code."""
    adj = {d: [] for d in left}
    for d, o in sorted(edges):
        if d in adj:
            adj[d].append(o)
    owners = {}
    def augment(d, seen):
        for o in adj[d]:
            if o not in seen:
                seen.add(o)
                if o not in owners or augment(owners[o], seen):
                    owners[o] = d
                    return True
        return False
    for d in sorted(left):
        augment(d, set())
    return len(owners)


def conventional_bounds(case, request):
    """Exact endpoints only for fixed-world, unrestricted-deletion additions."""
    if not additions(case) or case['model']['variables'] or case['model']['clauses']:
        raise ValueError('Conventional endpoint scope unavailable')
    if request['deletion_budget'] != len(labels(case)):
        raise ValueError('Unrestricted deletion required')
    domains = [((), {}, audit_checker.domain(case, request, {}))]
    if monotone_plan.admission(case, domains)['reason'] is not None:
        return None
    yes = {(o['anchor'], o['object']) for o in request['observations'] if o['outcome'] == 'present'}
    no = {(o['anchor'], o['object']) for o in request['observations'] if o['outcome'] == 'absent'}
    fn, fp = (contract.rational(case['loss'][k]) for k in ('false_negative', 'false_positive'))
    result = []
    for retained in (yes, set(labels(case)) - no):
        value = Fraction(0)
        for a in case['anchors']:
            aa, bb = ({d['id'] for d in a[r]['value']} for r in ('output_a', 'output_b'))
            edges = {(e['detection'], e['object']) for e in a['reference']['edges']
                     if (a['id'], e['object']) in retained}
            value += contract.rational(a['weight']) * ((fn + fp) * (rank(bb, edges) - rank(aa, edges)) - fp * (len(bb) - len(aa)))
        result.append(value)
    return tuple(result)


def decision(bounds, tolerance):
    if bounds is None:
        return 'unresolved'
    lo, hi = bounds
    if lo > tolerance:
        return 'supported'
    if hi <= tolerance:
        return 'excluded'
    return 'unresolved'


def can_stop(case, request, arm):
    """Selection never controls acceptance. A may use all published math cheaply."""
    start = time.perf_counter()
    payloads = []
    if arm == 'A' and additions(case):
        bounds = conventional_bounds(case, request)
    else:
        methods = ['monotone'] if additions(case) else ['legacy', 'components']
        intervals = []
        for method in methods:
            payload = audit.produce(case, request, method=method)
            # Producer's conclude already checks mathematical witnesses. B/C additionally
            # invoke the public consumer. A is allowed the same public replacement library.
            if arm != 'A':
                audit_checker.check(case, request, payload)
            payloads.append({'method': method, 'payload': payload})
            bound = payload['result'].get('bounds')
            if bound is not None:
                intervals.append(tuple(contract.rational(bound[k]) for k in ('lower', 'upper')))
        bounds = (max(v[0] for v in intervals), min(v[1] for v in intervals)) if intervals else None
    if bounds is not None and bounds[0] > bounds[1]:
        raise ValueError('Disagreeing valid bounds')
    return {'decision': decision(bounds, contract.rational(case['loss']['tolerance'])),
            'bounds': None if bounds is None else [str(v) for v in bounds],
            'proofs': payloads, 'stopping_seconds': time.perf_counter() - start}


def direct_order(case):
    pool, scored = [], []
    for a in case['anchors']:
        aa, bb = ({d['id'] for d in a[r]['value']} for r in ('output_a', 'output_b'))
        edges = {(e['detection'], e['object']) for e in a['reference']['edges']}
        adjacent_a = {o for d, o in edges if d in aa}
        if aa <= bb:
            cert = _matching_certificate(bb, {(d, o) for d, o in edges if o not in adjacent_a})
            pool += [(a['id'], o) for d, o in cert['matching']]
        for o in a['reference']['objects']:
            neighbours = {d for d, obj in edges if obj == o['id']}
            score = len(neighbours & (bb - aa)) if aa <= bb else len(neighbours & (aa ^ bb))
            scored.append((-score, -len(neighbours), a['id'], o['id']))
    pool.sort()
    rest = [(a, o) for _, _, a, o in sorted(scored) if (a, o) not in set(pool)]
    return pool + rest, len(pool)


class Selector:
    def __init__(self, case, arm, source_dir):
        self.case, self.arm = case, arm
        self.order, self.pool_size = direct_order(case)
        self.floor = confirmation_lower_bound(case, request_for(case)) if additions(case) else None
        self.families = []
        self.mode = 'direct_matching_then_adjacency'
        self.research_case = None
        if arm == 'C' and additions(case) and self.floor is not None and self.pool_size < self.floor:
            sys.path.insert(0, str(source_dir))
            import sufficiency
            import ihs
            self.ihs = ihs
            # Bound the existing optimizer call; no source file is edited.
            if not getattr(ihs.milp, '_bounded_by_experiment', False):
                original = ihs.milp
                def bounded(*args, **kwargs):
                    kwargs['options'] = dict(kwargs.get('options', {}), time_limit=10)
                    return original(*args, **kwargs)
                bounded._bounded_by_experiment = True
                ihs.milp = bounded
            raw = deepcopy(case)
            for a in raw['anchors']:
                aa = {d['id'] for d in a['output_a']['value']}
                a['base'] = a.pop('output_a')
                a['additions'] = a.pop('output_b')
                a['additions']['value'] = [d for d in a['additions']['value'] if d['id'] not in aa]
            self.research_case = sufficiency.Case(raw)
            self.mode = 'pinned_ihs_with_monotone_adversary'

    def select_next(self, public_observations, queried, count):
        if self.research_case is None or any(o['outcome'] == 'absent' for o in public_observations):
            return [key for key in self.order if key not in queried][:count]
        confirmed = frozenset((o['anchor'], o['object']) for o in public_observations if o['outcome'] == 'present')
        case = self.research_case
        removed = [key for key in case.labels if key not in confirmed]
        fam = self.ihs.minimal_adverse(case, removed, case.delta() - case.tolerance)
        if not fam:
            return []
        self.families.append(fam)
        selected, _ = self.ihs.min_hitting_set(case.labels, self.families)
        picks = [key for key in sorted(selected) if key not in queried][:count]
        return picks or [key for key in sorted(fam) if key not in queried][:count]


def run_deletion(spec, case, arm, area, outdir, plan):
    started = utc(); start = time.perf_counter(); queried = set(); observations = []
    # Deliberately synthetic: this constructor is the only answer-table creation.
    oracle = ObservationService(case, spec['input_sha256'], {key: 'present' for key in labels(case)})
    select_start = time.perf_counter()
    selector = Selector(case, arm, area / 'sources')
    selection_seconds = time.perf_counter() - select_start
    stopping_seconds = 0.0; checks = []; history = []
    cap = min(plan['budgets']['max_queries'], len(labels(case)))
    status = 'unresolved'; error = None
    while True:
        request = request_for(case, observations)
        contract.validate_request(case, request)
        check = can_stop(case, request, arm)
        stopping_seconds += check['stopping_seconds']
        check['after_queries'] = len(history)
        check['request_sha256'] = sha(encoded(request))
        put(outdir / ('check-%04d.json' % len(checks)), {'request': request, **check})
        checks.append({k: v for k, v in check.items() if k != 'proofs'})
        if check['decision'] != 'unresolved':
            status = check['decision']; break
        if len(history) >= cap:
            status = 'query_budget_exhausted'; break
        if time.perf_counter() - start >= plan['budgets']['seconds_per_arm_case']:
            status = 'time_budget_exhausted'; break
        count = min(plan['budgets']['batch'], cap - len(history))
        # A, B and C may all inspect the necessary floor and stop at it exactly.
        if selector.floor is not None and len(history) < selector.floor:
            count = min(count, selector.floor - len(history))
        tick = time.perf_counter()
        try:
            picks = selector.select_next(tuple(observations), frozenset(queried), count)
        except (AssertionError, RuntimeError) as exc:
            status = 'selection_resource_failure'; error = str(exc); break
        finally:
            selection_seconds += time.perf_counter() - tick
        if not picks:
            status = 'no_candidates'; break
        if len(picks) > count or len(set(picks)) != len(picks) or set(picks) & queried:
            raise ValueError('Selector violated query budget or repeated a query')
        for key in picks:
            event = oracle.query(key, subject(case, key), selector.mode)
            history.append(event); queried.add(key)
            observed = observation(event)
            if observed is not None:
                observations.append(observed)
            with (outdir / 'history.jsonl').open('ab') as log:
                log.write(encoded(event))
    # An empty history is also a retained artifact.
    (outdir / 'history.jsonl').touch(exist_ok=True)
    return {'case': spec['id'], 'arm': arm, 'family': spec['family'],
            'status': status, 'queries': len(history), 'labels': len(labels(case)),
            'selector': selector.mode, 'necessary_confirmation_floor': selector.floor,
            'direct_isolated_matching_size': selector.pool_size,
            'final_bounds': checks[-1]['bounds'], 'stopping_calls': len(checks),
            'selection_seconds': selection_seconds, 'stopping_seconds': stopping_seconds,
            'wall_seconds': time.perf_counter() - start, 'started_utc': started,
            'completed_utc': utc(), 'error': error,
            'human_observation_seconds': None, 'full_economic_cost': None,
            'history_sha256': sha((outdir / 'history.jsonl').read_bytes())}


def run_position(spec, case, arm, area, outdir):
    start = time.perf_counter()
    data = {}
    for key in ('geometry', 'linear'):
        raw = (area / spec[key]).read_bytes()
        if sha(raw) != spec[key + '_sha256']:
            raise ValueError('Position operand binding changed')
        data[key] = json.loads(raw)
    geometry, linear = data['geometry'], data['linear']
    rows = []
    for method, coeff in [('ordinary', None), ('shared_linear', linear)]:
        payload = localization.produce(case, geometry, linear_certificate=coeff)
        localization_checker.check(case, geometry, payload)
        put(outdir / (method + '.json'), payload)
        rows.append(payload['result'])
    intervals = [(contract.rational(r['bounds']['lower']), contract.rational(r['bounds']['upper'])) for r in rows]
    bounds = (max(v[0] for v in intervals), min(v[1] for v in intervals))
    result = decision(bounds, contract.rational(case['loss']['tolerance']))
    (outdir / 'history.jsonl').touch()
    return {'case': spec['id'], 'arm': arm, 'family': spec['family'], 'queries': 0,
            'status': result if result != 'unresolved' else 'zero_query_control_unresolved',
            'final_bounds': [str(v) for v in bounds], 'wall_seconds': time.perf_counter() - start,
            'ordinary_bounds': [str(v) for v in intervals[0]],
            'selector': 'not_entered_zero_query_bound_check',
            'human_observation_seconds': None, 'full_economic_cost': None,
            'history_sha256': sha(b'')}


def main():
    area, destination = (Path(v).resolve() for v in sys.argv[1:3])
    plan_bytes = (area / 'PLAN.json').read_bytes(); plan = json.loads(plan_bytes)
    freeze = json.loads((area / 'FREEZE.json').read_bytes())
    if sha(plan_bytes) != freeze['plan_sha256'] or sha(Path(__file__).read_bytes()) != freeze['driver_sha256']:
        raise ValueError('Frozen plan or driver changed; retain failure and create a successor run')
    session = json.loads((area / 'SESSION.json').read_bytes())
    for row in session['research_bindings']:
        if sha(Path(row['local']).read_bytes()) != row['sha256']:
            raise ValueError('Pinned research source changed')
    destination.mkdir()
    start = time.perf_counter(); rows = []
    for spec in plan['cases']:
        data = (area / spec['input']).read_bytes()
        if sha(data) != spec['input_sha256']:
            raise ValueError('Input binding changed')
        case = contract.parse(data); contract.validate(case)
        for arm in plan['arms']:
            outdir = destination / (spec['id'] + '--' + arm); outdir.mkdir()
            tick = time.perf_counter()
            try:
                if spec['family'] == 'deletion':
                    row = run_deletion(spec, case, arm, area, outdir, plan)
                else:
                    row = run_position(spec, case, arm, area, outdir)
            except Exception as exc:
                import traceback
                (outdir / 'failure.txt').write_text(traceback.format_exc())
                row = {'case': spec['id'], 'arm': arm, 'status': 'implementation_failure',
                       'queries': sum(1 for _ in (outdir/'history.jsonl').open()) if (outdir/'history.jsonl').exists() else 0,
                       'wall_seconds': time.perf_counter()-tick, 'error': str(exc)}
            rows.append(row)
            print(json.dumps({k: row.get(k) for k in ('case', 'arm', 'status', 'queries', 'wall_seconds')}), flush=True)
            (destination / 'progress.json').write_bytes(encoded({'complete': False, 'rows': rows}))
    put(destination / 'RESULTS.json', {'artifact_id': 'reiyah.value-disproof.results', 'version': VERSION,
        'plan_sha256': sha(plan_bytes), 'driver_sha256': sha(Path(__file__).read_bytes()),
        'complete': len(rows) == len(plan['cases']) * len(plan['arms']),
        'rows': rows, 'campaign_seconds': time.perf_counter() - start,
        'human_costs': 'unmeasured', 'outcome_reserved_accessed': False})


if __name__ == '__main__':
    main()
