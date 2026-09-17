"""Robustness of a paired detector comparison to reference localization error.

Family. Every reference object may be displaced by at most epsilon metres in the plane. Under
the strict 2 m same-class matching rule, only edges whose centre distance lies in
(2 - epsilon, 2 + epsilon) can change: a present edge can be lost, an absent one gained. Objects
whose positions have been confirmed (measured to within epsilon) keep their edges fixed.

Certificate. The adversary chooses flips on boundary edges to minimise gain = TP_aug - TP_base,
per anchor, as a single MILP (Konig duality as in sufficiency.py) with one binary flip variable
per boundary edge. Treating flips as independent is a relaxation: a real displacement moves all
of an object's edges together. Hence

  robust                the relaxed adversary cannot cross: no physical displacement can either
  insufficient_realized the relaxed counterexample's edge pattern is realized, object by object,
                        by an explicit displacement within epsilon (checked on a disc grid plus
                        the exact distance rule): a physical counterexample
  insufficient_relaxed  the relaxed adversary crosses but the check found no realizing
                        displacement: unresolved between geometry and relaxation

A sound tier without a solver: the adversary removes at most one gain unit per boundary flip
and never more than the anchor's gain.

Usage: python -B localization.py CASE_WITH_XY_JSON EPSILON [EPSILON ...] --out OUT_JSON
"""
import json
import math
import sys
import time
from fractions import Fraction

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import lil_matrix

from sufficiency import Case, hopcroft_karp, rational

NEAR = 2.0
SOLVER_TIME_LIMIT = 30.0   # seconds per anchor MILP; a limit hit is reported as solver_failed, never as robust


class GeoAnchor:
    def __init__(self, raw, eps):
        self.id = raw['id']
        self.weight = rational(raw['weight'])
        dets = [(d['id'], d['class'], d['xy']) for d in raw['base']['value']] + \
               [(d['id'], d['class'], d['xy']) for d in raw['additions']['value']]
        self.base = [d['id'] for d in raw['base']['value']]
        self.additions = [d['id'] for d in raw['additions']['value']]
        self.det_xy = {i: xy for i, _, xy in dets}
        self.det_cls = {i: c for i, c, _ in dets}
        self.objects = [(o['id'], o['class'], o['xy']) for o in raw['reference']['objects']]
        self.obj_xy = {i: xy for i, _, xy in self.objects}
        self.obj_cls = {i: c for i, c, _ in self.objects}
        self.eps = eps
        # candidate pairs within 2 + eps, same class; present iff distance < 2
        self.present = set()
        self.boundary = []  # (det, obj, present)
        for did, dc, dxy in dets:
            for oid, oc, oxy in self.objects:
                if dc != oc:
                    continue
                dist = math.hypot(dxy[0] - oxy[0], dxy[1] - oxy[1])
                if dist >= NEAR + eps:
                    continue
                pres = dist < NEAR
                if pres:
                    self.present.add((did, oid))
                if dist > NEAR - eps:
                    self.boundary.append((did, oid, pres))
        declared = {(e['detection'], e['object']) for e in raw['reference']['edges']}
        assert declared == self.present, 'coordinates and declared edges disagree at %s' % self.id
        self.base_set = set(self.base)

    def gain(self, edge_set):
        adjacency = {}
        for d, o in edge_set:
            adjacency.setdefault(d, []).append(o)
        return hopcroft_karp(self.base + self.additions, adjacency) - hopcroft_karp(self.base, adjacency)

    def adversary(self, confirmed=frozenset(), budget=None):
        flips = [(d, o, p) for d, o, p in self.boundary if o not in confirmed]
        g0 = self.gain(self.present)
        if not flips:
            return {'flips': [], 'gain_after': g0, 'solver_gain_after': g0, 'status': 'no_candidate', 'verified': True}
        fi = {(d, o): i for i, (d, o, _) in enumerate(flips)}
        nf = len(flips)
        all_pairs = sorted(self.present | {(d, o) for d, o, _ in flips})
        objs_in = sorted({o for _, o in all_pairs})
        dets = self.base + self.additions
        cover_vertices = dets + objs_in
        ci = {v: nf + i for i, v in enumerate(cover_vertices)}
        nc = len(cover_vertices)
        base_pairs = [(d, o) for d, o in all_pairs if d in self.base_set]
        mi = {e: nf + nc + i for i, e in enumerate(base_pairs)}
        nm = len(base_pairs)
        n = nf + nc + nm
        cost = np.zeros(n)
        cost[nf:nf + nc] = 1.0
        cost[nf + nc:] = -1.0
        rows = len(all_pairs) + nm + len(dets) + len(objs_in) + 1
        A = lil_matrix((rows, n))
        lo, hi = [], []
        r = 0
        for d, o in all_pairs:
            # present_after = p + (1-2p) y ; cover: c_d + c_o >= present_after
            p = 1 if (d, o) in self.present else 0
            A[r, ci[d]] = 1
            A[r, ci[o]] = 1
            if (d, o) in fi:
                A[r, fi[(d, o)]] = -(1 - 2 * p)
            lo.append(p)
            hi.append(np.inf)
            r += 1
        for e in base_pairs:  # m_e <= present_after
            p = 1 if e in self.present else 0
            A[r, mi[e]] = 1
            if e in fi:
                A[r, fi[e]] = -(1 - 2 * p)
            lo.append(-np.inf)
            hi.append(p)
            r += 1
        for d in dets:
            for e in base_pairs:
                if e[0] == d:
                    A[r, mi[e]] = 1
            lo.append(-np.inf); hi.append(1); r += 1
        for o in objs_in:
            for e in base_pairs:
                if e[1] == o:
                    A[r, mi[e]] = 1
            lo.append(-np.inf); hi.append(1); r += 1
        for e in fi:
            A[r, fi[e]] = 1
        lo.append(-np.inf); hi.append(np.inf if budget is None else float(budget)); r += 1
        A = A.tocsr()[:r]
        integrality = np.zeros(n)
        integrality[:nf + nc] = 1
        res = milp(c=cost, constraints=LinearConstraint(A, np.array(lo), np.array(hi)),
                   integrality=integrality, bounds=Bounds(0, 1), options={'time_limit': SOLVER_TIME_LIMIT})
        if res.status != 0:
            return {'flips': None, 'gain_after': None, 'solver_gain_after': None, 'status': 'solver_%d' % res.status, 'verified': False}
        chosen = [(d, o, p) for (d, o, p) in flips if res.x[fi[(d, o)]] > 0.5]
        edges = set(self.present)
        for d, o, p in chosen:
            if p:
                edges.discard((d, o))
            else:
                edges.add((d, o))
        exact = self.gain(edges)
        return {'flips': chosen, 'gain_after': exact, 'solver_gain_after': int(round(res.fun)),
                'status': 'optimal', 'verified': exact == int(round(res.fun)), 'edges_after': edges}

    def realize(self, chosen):
        """For each moved object, find a displacement within eps realizing the flipped pattern."""
        by_obj = {}
        for d, o, p in chosen:
            by_obj.setdefault(o, []).append((d, p))
        realized = {}
        for o, want in by_obj.items():
            ox, oy = self.obj_xy[o]
            # desired adjacency after flips for every same-class detection within reach
            desired = {}
            for did, dc, dxy in [(i, self.det_cls[i], self.det_xy[i]) for i in self.det_xy]:
                if dc != self.obj_cls[o]:
                    continue
                if math.hypot(dxy[0] - ox, dxy[1] - oy) >= NEAR + self.eps:
                    continue
                desired[did] = (did, o) in self.present
            for d, p in want:
                desired[d] = not p
            found = None
            steps = 25
            for i in range(-steps, steps + 1):
                for j in range(-steps, steps + 1):
                    dx, dy = self.eps * i / steps, self.eps * j / steps
                    if dx * dx + dy * dy > self.eps * self.eps:
                        continue
                    px, py = ox + dx, oy + dy
                    ok = True
                    for did, adj in desired.items():
                        dxy = self.det_xy[did]
                        if (math.hypot(dxy[0] - px, dxy[1] - py) < NEAR) != adj:
                            ok = False
                            break
                    if ok:
                        found = [dx, dy]
                        break
                if found:
                    break
            realized[o] = found
        return realized


class GeoCase:
    def __init__(self, raw, eps):
        self.case = Case(raw)
        self.eps = eps
        self.anchors = [GeoAnchor(a, eps) for a in raw['anchors']]

    def certificate(self, confirmed=frozenset(), budget=None, realize=True):
        started = time.perf_counter()
        case = self.case
        delta = case.delta()
        excluded = delta <= case.tolerance
        margin = delta - case.tolerance
        unit = case.fn + case.fp
        conf = {}
        for aid, o in confirmed:
            conf.setdefault(aid, set()).add(o)
        sound = Fraction(0)
        solver = Fraction(0)
        edges_after = {}
        chosen_all = []
        boundary_total = 0
        for a in self.anchors:
            c = frozenset(conf.get(a.id, ()))
            g = a.gain(a.present)
            nb = sum(1 for d, o, p in a.boundary if o not in c)
            boundary_total += nb
            sound += a.weight * unit * min(g, nb) if g > 0 else 0
            adv = a.adversary(c, budget)
            if adv['status'] in ('optimal', 'no_candidate'):
                solver += a.weight * unit * (g - adv['gain_after'])
                if adv['flips']:
                    edges_after[a.id] = adv['edges_after']
                    chosen_all.append((a, adv['flips']))
            else:
                solver = None
                break
        if budget is not None and solver is not None:
            sound = min(sound, budget * max(a.weight for a in self.anchors) * unit)
        result = {'criterion': 'excluded' if excluded else 'supported', 'delta': str(delta), 'margin': str(margin), 'epsilon': self.eps,
                  'confirmed': len(confirmed), 'boundary_edges_unconfirmed': boundary_total,
                  'sound_max_drop': str(sound), 'sound': 'robust' if sound < margin else 'unresolved',
                  'solver_max_drop': None if solver is None else str(solver)}
        if solver is None:
            result['status'] = 'solver_failed'
            return result
        if excluded:
            result['status'] = 'excluded_max_drop_only'
            result['seconds'] = round(time.perf_counter() - started, 2)
            return result
        if solver < margin:
            result['status'] = 'robust'
        else:
            # recompute the whole case on the flipped graphs (exact) and try to realize it
            total = Fraction(0)
            for a in self.anchors:
                e = edges_after.get(a.id, a.present)
                total += a.weight * ((case.fn + case.fp) * a.gain(e) - case.fp * len(a.additions))
            result['achieved_delta'] = str(total)
            result['achieved'] = 'crosses' if total <= case.tolerance else 'does_not_cross'
            moved = 0
            unrealized = 0
            for a, flips in chosen_all:
                if realize:
                    real = a.realize(flips)
                    moved += len(real)
                    unrealized += sum(1 for v in real.values() if v is None)
                else:
                    moved += len({o for _, o, _ in flips})
                    unrealized = None
            result['objects_moved'] = moved
            result['objects_unrealized'] = unrealized
            result['flips'] = sum(len(f) for _, f in chosen_all)
            result['status'] = ('insufficient_realized' if (unrealized == 0 and total <= case.tolerance)
                                else 'insufficient_relaxed' if realize else 'insufficient_unchecked')
        result['seconds'] = round(time.perf_counter() - started, 2)
        result['_confirmed'] = sorted(confirmed)
        result['_moved'] = [(a.id, o) for a, flips in chosen_all for o in {o for _, o, _ in flips}]
        return result


def audit_boundary_first(geo, batch=10, max_rounds=500):
    """Confirm the positions of objects with the most unconfirmed boundary edges until robust."""
    confirmed = set()
    cert = geo.certificate(frozenset(confirmed), realize=False)
    rounds = 0
    while cert.get('status', '').startswith('insufficient') and rounds < max_rounds:
        counts = {}
        for a in geo.anchors:
            for d, o, p in a.boundary:
                if (a.id, o) not in confirmed:
                    counts[(a.id, o)] = counts.get((a.id, o), 0) + 1
        picks = sorted(counts, key=lambda k: (-counts[k], k))[:batch]
        if not picks:
            break
        confirmed.update(picks)
        rounds += 1
        cert = geo.certificate(frozenset(confirmed), realize=False)
    return {'confirmed_positions': len(confirmed), 'rounds': rounds, 'final_status': cert.get('status')}


def audit_counterexample_guided(geo, batch=10, max_rounds=500):
    confirmed = set()
    cert = geo.certificate(frozenset(confirmed), realize=False)
    rounds = 0
    while cert.get('status', '').startswith('insufficient') and rounds < max_rounds:
        picks = [m for m in cert['_moved'] if m not in confirmed][:batch]
        if not picks:
            break
        confirmed.update(picks)
        rounds += 1
        cert = geo.certificate(frozenset(confirmed), realize=False)
    return {'confirmed_positions': len(confirmed), 'rounds': rounds, 'final_status': cert.get('status')}


if __name__ == '__main__':
    raw = json.load(open(sys.argv[1]))
    out = sys.argv[sys.argv.index('--out') + 1]
    epsilons = [float(v) for v in sys.argv[2:sys.argv.index('--out')]]
    report = {'unit': raw.get('comparison_id'), 'labels': sum(len(a['reference']['objects']) for a in raw['anchors']), 'by_epsilon': {}}
    for eps in epsilons:
        geo = GeoCase(raw, eps)
        cert = geo.certificate()
        row = {k: v for k, v in cert.items() if not k.startswith('_')}
        if cert.get('status', '').startswith('insufficient'):
            row['audit_boundary_first'] = audit_boundary_first(geo)
            row['audit_counterexample_guided'] = audit_counterexample_guided(geo)
        row['boundary_objects_total'] = len({(a.id, o) for a in geo.anchors for _, o, _ in a.boundary})
        report['by_epsilon'][str(eps)] = row
        print(json.dumps({'epsilon': eps, **{k: row[k] for k in row if k in ('status', 'solver_max_drop', 'margin', 'boundary_edges_unconfirmed', 'boundary_objects_total', 'objects_moved', 'objects_unrealized', 'flips', 'audit_boundary_first', 'audit_counterexample_guided', 'seconds')}}), flush=True)
    json.dump(report, open(out, 'w'), indent=1)
