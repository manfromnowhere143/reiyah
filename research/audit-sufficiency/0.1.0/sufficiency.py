"""Audit sufficiency for a paired detector comparison under reference deletion.

Question answered here. A comparison packet reports loss_base - loss_augmented as an exact
rational under one finite reference world. Some reference objects have been confirmed present
by an audit. Can any admissible deletion of the unconfirmed objects still overturn the
reported criterion? If not, the confirmed set is sufficient for that criterion under the
declared deletion family.

Three tiers are reported for every certificate, and they are never merged:

  sound     an exact-rational bound that needs no solver: per anchor the adversary can remove
            at most one gain unit per deleted object that has any edge, and never more than
            the anchor's whole gain. Loose, but a proof.
  solver    the exact per-anchor optimum of a mixed-integer program (HiGHS via scipy). The
            adversary's set is verified by exact recomputation; only the claim that nothing
            larger exists rests on the solver.
  achieved  an exact counterexample recomputed with the matcher below; a proof of
            insufficiency when it crosses.

Model. Within one anchor the paired difference is (a+b)*(TP_aug-TP_base) - b*r, so deleting
objects changes it only through gain = TP_aug - TP_base. An adversary deleting S seeks
min over S of nu_aug(S) - nu_base(S). By Konig, nu_aug(S) is a minimum vertex cover of the
augmented graph minus S, and -nu_base(S) is the minimum of minus a matching, so the whole
problem is a single minimisation with binary deletion variables x, binary cover variables c
and matching variables m:

  minimise  sum(c) - sum(m)
  subject   c_d + c_o + x_o >= 1        for every augmented edge (d,o)
            m_e <= 1 - x_o              for every base edge e=(d,o)
            sum_{e at v} m_e <= 1       for every vertex v of the base graph
            x_o = 0                     for confirmed o
            sum(x) <= budget            optional

Deleting an object with no edge changes nothing, so such objects carry x_o = 0.

Scope. One finite reference world, deletion of whole objects, fixed detections, fixed loss.
Insertion, class, geometry and time errors are outside this family. A sufficiency
certificate is conditional on the declared family and on the confirmed observations being
correct; it says nothing about physical truth. The matcher and the MILP share this module's
parser; the exact recomputation shares nothing with the Engine kernel.
"""
from collections import deque
from fractions import Fraction
import hashlib
import json
import math
import random
import time

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

__version__ = "0.1.0"


def rational(v):
    return Fraction(int(v['numerator']), int(v['denominator']))


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def hopcroft_karp(left, adjacency):
    """Maximum bipartite matching size. adjacency: left vertex -> iterable of right vertices."""
    inf = float('inf')
    pair_u = {u: None for u in left}
    pair_v = {}
    dist = {}

    def bfs():
        queue = deque()
        for u in left:
            if pair_u[u] is None:
                dist[u] = 0
                queue.append(u)
            else:
                dist[u] = inf
        found = False
        while queue:
            u = queue.popleft()
            for v in adjacency.get(u, ()):
                w = pair_v.get(v)
                if w is None:
                    found = True
                elif dist[w] == inf:
                    dist[w] = dist[u] + 1
                    queue.append(w)
        return found

    def dfs(u):
        for v in adjacency.get(u, ()):
            w = pair_v.get(v)
            if w is None or (dist[w] == dist[u] + 1 and dfs(w)):
                pair_u[u] = v
                pair_v[v] = u
                return True
        dist[u] = inf
        return False

    size = 0
    while bfs():
        for u in left:
            if pair_u[u] is None and dfs(u):
                size += 1
    return size


class Anchor:
    """One anchor of a comparison contract with a finite, variable-free reference."""

    def __init__(self, raw):
        ref = raw['reference']
        if ref['state'] != 'finite':
            raise ValueError('anchor %s is not finite' % raw['id'])
        for row in ref['objects'] + ref['edges']:
            if row['when']:
                raise ValueError('anchor %s has conditional reference rows' % raw['id'])
        self.id = raw['id']
        self.weight = rational(raw['weight'])
        self.base = [d['id'] for d in raw['base']['value']]
        self.additions = [d['id'] for d in raw['additions']['value']]
        self.objects = [o['id'] for o in ref['objects']]
        self.edges = [(e['detection'], e['object']) for e in ref['edges']]
        base_set = set(self.base)
        self.base_edges = [e for e in self.edges if e[0] in base_set]
        self.object_edges = {}
        for d, o in self.edges:
            self.object_edges.setdefault(o, []).append(d)
        self.objects_with_edge = [o for o in self.objects if o in self.object_edges]

    def matchings(self, removed=frozenset()):
        adjacency = {}
        for d, o in self.edges:
            if o not in removed:
                adjacency.setdefault(d, []).append(o)
        tp_base = hopcroft_karp(self.base, adjacency)
        tp_aug = hopcroft_karp(self.base + self.additions, adjacency)
        return tp_base, tp_aug

    def gain(self, removed=frozenset()):
        tp_base, tp_aug = self.matchings(removed)
        return tp_aug - tp_base

    def adversary(self, confirmed=frozenset(), budget=None):
        """Solver-claimed minimum of gain after deleting unconfirmed objects, with exact verification."""
        cand = [o for o in self.objects_with_edge if o not in confirmed]
        if not cand:
            g = self.gain()
            return {'deleted': [], 'gain_after': g, 'solver_gain_after': g, 'status': 'no_candidate',
                    'verified': True}
        xi = {o: i for i, o in enumerate(cand)}
        dets = self.base + self.additions
        n_x = len(cand)
        cover_vertices = dets + self.objects_with_edge
        ci = {v: n_x + i for i, v in enumerate(cover_vertices)}
        n_c = len(cover_vertices)
        mi = {e: n_x + n_c + i for i, e in enumerate(self.base_edges)}
        n_m = len(self.base_edges)
        n = n_x + n_c + n_m
        cost = np.zeros(n)
        cost[n_x:n_x + n_c] = 1.0
        cost[n_x + n_c:] = -1.0
        rows = []
        lo, hi = [], []
        A = lil_matrix((len(self.edges) + n_m + len(dets) + len(self.objects_with_edge) + 1, n))
        r = 0
        for d, o in self.edges:  # cover: c_d + c_o + x_o >= 1
            A[r, ci[d]] = 1; A[r, ci[o]] = 1
            if o in xi:
                A[r, xi[o]] = 1
            lo.append(1); hi.append(np.inf); r += 1
        for e in self.base_edges:  # m_e + x_o <= 1
            A[r, mi[e]] = 1
            if e[1] in xi:
                A[r, xi[e[1]]] = 1
            lo.append(-np.inf); hi.append(1); r += 1
        for d in dets:  # matching degree at detections
            for e in self.base_edges:
                if e[0] == d:
                    A[r, mi[e]] = 1
            lo.append(-np.inf); hi.append(1); r += 1
        for o in self.objects_with_edge:  # matching degree at objects
            for e in self.base_edges:
                if e[1] == o:
                    A[r, mi[e]] = 1
            lo.append(-np.inf); hi.append(1); r += 1
        for o in cand:  # budget row
            A[r, xi[o]] = 1
        lo.append(-np.inf); hi.append(np.inf if budget is None else float(budget)); r += 1
        A = A.tocsr()[:r]
        integrality = np.zeros(n)
        integrality[:n_x + n_c] = 1
        res = milp(c=cost, constraints=LinearConstraint(A, np.array(lo), np.array(hi)),
                   integrality=integrality, bounds=Bounds(0, 1))
        if res.status != 0:
            return {'deleted': None, 'gain_after': None, 'solver_gain_after': None,
                    'status': 'solver_' + str(res.status), 'verified': False}
        deleted = sorted(o for o in cand if res.x[xi[o]] > 0.5)
        solver_gain = int(round(res.fun))
        exact_gain = self.gain(frozenset(deleted))
        return {'deleted': deleted, 'gain_after': exact_gain, 'solver_gain_after': solver_gain,
                'status': 'optimal', 'verified': exact_gain == solver_gain}


class Case:
    def __init__(self, raw):
        self.raw = raw
        self.fn = rational(raw['loss']['false_negative'])
        self.fp = rational(raw['loss']['false_positive'])
        self.tolerance = rational(raw['loss']['tolerance'])
        if raw['model']['variables'] or raw['model']['clauses']:
            raise ValueError('only variable-free finite models are supported here')
        self.anchors = [Anchor(a) for a in raw['anchors']]
        self.by_id = {a.id: a for a in self.anchors}
        self.labels = [(a.id, o) for a in self.anchors for o in a.objects]

    def with_loss(self, fn, fp, tolerance=None):
        raw = json.loads(json.dumps(self.raw))
        raw['loss']['false_negative'] = {'numerator': str(fn.numerator), 'denominator': str(fn.denominator)}
        raw['loss']['false_positive'] = {'numerator': str(fp.numerator), 'denominator': str(fp.denominator)}
        if tolerance is not None:
            raw['loss']['tolerance'] = {'numerator': str(tolerance.numerator),
                                        'denominator': str(tolerance.denominator)}
        return Case(raw)

    def without(self, removed):
        """A new case with the given (anchor, object) labels deleted from the world."""
        raw = json.loads(json.dumps(self.raw))
        for a in raw['anchors']:
            gone = {o for aid, o in removed if aid == a['id']}
            a['reference']['objects'] = [o for o in a['reference']['objects'] if o['id'] not in gone]
            a['reference']['edges'] = [e for e in a['reference']['edges'] if e['object'] not in gone]
        return Case(raw)

    def anchor_delta(self, anchor, removed=frozenset()):
        tp_base, tp_aug = anchor.matchings(removed)
        r = len(anchor.additions)
        return (self.fn + self.fp) * (tp_aug - tp_base) - self.fp * r

    def delta(self, removed=frozenset()):
        total = Fraction(0)
        for a in self.anchors:
            rem = frozenset(o for aid, o in removed if aid == a.id)
            total += a.weight * self.anchor_delta(a, rem)
        return total

    def criterion(self, value):
        return 'supported' if value > self.tolerance else 'excluded'

    def certificate(self, confirmed=frozenset(), budget=None):
        """Three-tier sufficiency certificate for the strict-improvement criterion."""
        started = time.perf_counter()
        conf_by = {}
        for aid, o in confirmed:
            conf_by.setdefault(aid, set()).add(o)
        delta = self.delta()
        if delta <= self.tolerance:
            return {'criterion': 'excluded', 'delta': str(delta), 'note': 'criterion already excluded',
                    'sound': 'not_applicable', 'solver': 'not_applicable', 'achieved': 'not_applicable'}
        margin = delta - self.tolerance
        unit = self.fn + self.fp
        sound_drop = Fraction(0)
        solver_drop = Fraction(0)
        counter = []
        per_anchor = []
        unverified = 0
        for a in self.anchors:
            c = frozenset(conf_by.get(a.id, ()))
            g = a.gain()
            free = sum(1 for o in a.objects_with_edge if o not in c)
            s_units = min(g, free) if budget is None else min(g, free, budget)
            sound_drop += a.weight * unit * s_units
            adv = a.adversary(c, budget)
            if adv['status'] == 'optimal' or adv['status'] == 'no_candidate':
                units = g - adv['gain_after']
                if not adv['verified']:
                    unverified += 1
                solver_drop += a.weight * unit * units
                counter.extend((a.id, o) for o in adv['deleted'])
                per_anchor.append({'anchor': a.id, 'gain': g, 'free_objects': free,
                                   'sound_units': s_units, 'solver_units': units,
                                   'deleted': len(adv['deleted'])})
            else:
                per_anchor.append({'anchor': a.id, 'gain': g, 'free_objects': free,
                                   'sound_units': s_units, 'solver_units': None, 'status': adv['status']})
                solver_drop = None
        if budget is not None:
            cap = budget * max(a.weight for a in self.anchors) * unit
            sound_drop = min(sound_drop, cap)
        achieved = self.delta(frozenset(counter)) if solver_drop is not None else None
        achieved_drop = (delta - achieved) if achieved is not None else None
        if budget is not None and solver_drop is not None:
            # per-anchor budgets are independent above; the global budget is enforced by taking
            # the best allocation over anchors of at most `budget` deletions in total
            solver_drop, counter, achieved, achieved_drop = self._budgeted(confirmed, budget, delta, unit)
        result = {
            'criterion': 'supported', 'delta': str(delta), 'tolerance': str(self.tolerance),
            'margin': str(margin), 'confirmed': len(confirmed), 'budget': budget,
            'sound_max_drop': str(sound_drop),
            'sound': 'sufficient' if sound_drop < margin else 'unresolved',
            'solver_max_drop': None if solver_drop is None else str(solver_drop),
            'solver': (None if solver_drop is None else
                       'sufficient' if solver_drop < margin else 'insufficient'),
            'solver_unverified_anchors': unverified,
            'achieved_drop': None if achieved_drop is None else str(achieved_drop),
            'achieved': (None if achieved_drop is None else
                         'crosses' if achieved_drop >= margin else 'does_not_cross'),
            'counterexample_size': len(counter),
            'counterexample_frames': len({aid for aid, _ in counter}),
            'seconds': round(time.perf_counter() - started, 3),
        }
        result['_counterexample'] = counter
        result['_per_anchor'] = per_anchor
        return result

    def _budgeted(self, confirmed, budget, delta, unit):
        conf_by = {}
        for aid, o in confirmed:
            conf_by.setdefault(aid, set()).add(o)
        curves = []
        for a in self.anchors:
            c = frozenset(conf_by.get(a.id, ()))
            g = a.gain()
            curve = [(0, [])]
            free = sum(1 for o in a.objects_with_edge if o not in c)
            for k in range(1, min(free, budget) + 1):
                adv = a.adversary(c, k)
                if adv['status'] not in ('optimal', 'no_candidate'):
                    break
                curve.append((g - adv['gain_after'], adv['deleted']))
                if adv['gain_after'] == 0:
                    break
            curves.append((a, curve))
        best = {0: (Fraction(0), [])}
        for a, curve in curves:
            nxt = {}
            for used, (drop, sets) in best.items():
                for k, (units, deleted) in enumerate(curve):
                    if used + k > budget:
                        break
                    cand = drop + a.weight * unit * units
                    key = used + k
                    if key not in nxt or cand > nxt[key][0]:
                        nxt[key] = (cand, sets + [(a.id, o) for o in deleted])
            best = nxt
        drop, counter = max(best.values(), key=lambda t: t[0])
        achieved = self.delta(frozenset(counter))
        return drop, counter, achieved, delta - achieved


# ---------------------------------------------------------------- selection policies

def policy_random(case, confirmed, batch, rng, state):
    pool = [l for l in case.labels if l not in confirmed]
    rng.shuffle(pool)
    return pool[:batch]


def policy_degree(case, confirmed, batch, rng, state):
    scored = []
    for a in case.anchors:
        for o in a.objects:
            if (a.id, o) not in confirmed:
                scored.append((-len(a.object_edges.get(o, ())), a.id, o))
    scored.sort()
    return [(aid, o) for _, aid, o in scored[:batch]]


def policy_addition_adjacent(case, confirmed, batch, rng, state):
    scored = []
    for a in case.anchors:
        adds = set(a.additions)
        for o in a.objects:
            if (a.id, o) in confirmed:
                continue
            k = sum(1 for d in a.object_edges.get(o, ()) if d in adds)
            scored.append((-k, -len(a.object_edges.get(o, ())), a.id, o))
    scored.sort()
    return [(aid, o) for _, _, aid, o in scored[:batch]]


def policy_influence(case, confirmed, batch, rng, state):
    """Single-deletion drop on the current world, largest first (AMIP-style first-order score)."""
    if 'influence' not in state:
        scores = []
        for a in case.anchors:
            g = a.gain()
            for o in a.objects:
                drop = g - a.gain(frozenset([o])) if o in a.object_edges else 0
                scores.append((-drop, a.id, o))
        scores.sort()
        state['influence'] = [(aid, o) for _, aid, o in scores]
    return [l for l in state['influence'] if l not in confirmed][:batch]


def policy_counterexample(case, confirmed, batch, rng, state):
    """Confirm the labels of the current solver counterexample (counterexample-guided)."""
    cert = case.certificate(confirmed)
    state['last_certificate'] = cert
    return [l for l in cert['_counterexample'] if l not in confirmed][:batch]


POLICIES = {
    'random': policy_random,
    'degree': policy_degree,
    'addition_adjacent': policy_addition_adjacent,
    'influence': policy_influence,
    'counterexample_guided': policy_counterexample,
}


def run_policy(case, name, batch=10, seed=0, confirmed=frozenset(), oracle=None, max_queries=None):
    """Query labels until the solver tier certifies sufficiency.

    oracle(label) -> True if present (confirmed), False if absent (the world loses the object).
    Default oracle answers True for every label (benchmark labels taken as declared truth).
    Returns a record with query counts, certificate tiers and the final world's decision.
    """
    rng = random.Random(seed)
    state = {}
    confirmed = set(confirmed)
    queries = 0
    absent = []
    world = case
    started = time.perf_counter()
    cert = world.certificate(confirmed)
    rounds = 0
    queried = set(confirmed)
    while cert.get('solver') == 'insufficient':
        picks = POLICIES[name](world, queried, batch, rng, state)
        if not picks:
            break
        for l in picks:
            queries += 1
            queried.add(l)
            present = True if oracle is None else oracle(l)
            if present:
                confirmed.add(l)
            else:
                absent.append(l)
        if absent:
            world = case.without(frozenset(absent))
        rounds += 1
        cert = world.certificate(confirmed)
        if max_queries is not None and queries >= max_queries:
            break
    return {'policy': name, 'seed': seed, 'batch': batch, 'queries': queries, 'rounds': rounds,
            'confirmed': len(confirmed), 'absent_found': len(absent),
            'final_delta': cert.get('delta'), 'final_criterion': cert.get('criterion'),
            'sound': cert.get('sound'), 'solver': cert.get('solver'),
            'seconds': round(time.perf_counter() - started, 2),
            '_confirmed': sorted(confirmed), '_absent': absent}
