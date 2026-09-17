"""Robustness of a paired detector comparison to reference localization error.  Version 0.2.1 (0.2.1: the ball radius is converted from its decimal text like every coordinate; 0.2.0 used the binary float, 5.5e-18 too large at 0.1, and one boundary shift was rejected by the Engine).

Family. Every reference object may lie anywhere in a closed ball of radius e around its retained
centre (e = epsilon for unmeasured objects; e = the residual radius of a measurement for confirmed
objects, around the returned centre). Under the strict same-class rule "match iff centre distance
< R", with exact squared distance s to a detection:

    guaranteed present  iff  e < R  and  s < (R - e)^2
    possible            iff  s < (R + e)^2

Inner equality is uncertain; outer equality cannot match. Every possible-but-not-guaranteed edge
is a flip variable. Coordinates are converted from the source floats to exact rationals
(Fraction(float) is exact), so every comparison is exact; no floating epsilon enters.

0.2.0 repairs, both reproduced on the Engine's retained controls before the change: (1) the
0.1.0 code treated a present edge at distance exactly R - e as fixed (strict inequality on the
wrong side), so a reference at 1.9 m with e = 0.1 was reported robust although the shift
(0.1, 0) loses the match; (2) a confirmed position froze all edges regardless of measurement
error, so a reference measured at 1.95 m to within 0.1 m was reported robust although the shift
(0.05, 0) loses the match. Confirmation now carries a returned centre and a residual radius; a
zero residual radius is the exact-adjacency oracle and is declared as such wherever used.

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

NEAR = 2


def coord(v):
    """Exact rational from a source value.

    Floats are converted through their shortest round-trip decimal text (repr), the same
    decimal-to-rational convention the Engine applies to source coordinates, so both
    implementations reason about identical rationals. Strings such as '19/10' are exact rationals.
    """
    if isinstance(v, str):
        return Fraction(v)
    if isinstance(v, int):
        return Fraction(v)
    return Fraction(repr(float(v)))
SOLVER_TIME_LIMIT = 30.0   # seconds per anchor MILP; a limit hit is reported as solver_failed, never as robust


class GeoAnchor:
    def __init__(self, raw, eps):
        self.id = raw['id']
        self.weight = rational(raw['weight'])
        dets = [(d['id'], d['class'], d['xy']) for d in raw['base']['value']] + \
               [(d['id'], d['class'], d['xy']) for d in raw['additions']['value']]
        self.base = [d['id'] for d in raw['base']['value']]
        self.additions = [d['id'] for d in raw['additions']['value']]
        self.det_xy = {i: (coord(xy[0]), coord(xy[1])) for i, _, xy in dets}
        self.det_cls = {i: c for i, c, _ in dets}
        self.objects = [(o['id'], o['class'], o['xy']) for o in raw['reference']['objects']]
        self.obj_xy = {i: (coord(xy[0]), coord(xy[1])) for i, _, xy in self.objects}
        self.obj_cls = {i: c for i, c, _ in self.objects}
        self.eps = coord(eps)   # decimal convention: 0.1 is 1/10, never the binary float
        self.R = Fraction(NEAR)
        # nominal adjacency (exact) and the candidate pairs within reach of any admitted ball
        self.present = set()
        self.candidates = {}   # object -> list of same-class detections with s < (R + eps)^2
        for oid, oc, _ in self.objects:
            ox, oy = self.obj_xy[oid]
            for did, dc, _ in dets:
                if dc != oc:
                    continue
                dx, dy = self.det_xy[did]
                s2 = (dx - ox) ** 2 + (dy - oy) ** 2
                if s2 < self.R ** 2:
                    self.present.add((did, oid))
                if s2 < (self.R + self.eps) ** 2:
                    self.candidates.setdefault(oid, []).append(did)
        declared = {(e['detection'], e['object']) for e in raw['reference']['edges']}
        assert declared == self.present, 'coordinates and declared edges disagree at %s' % self.id
        self.base_set = set(self.base)
        self.boundary = self.flippable({})

    def flippable(self, confirmed):
        """(det, obj, present) for every possible-but-not-guaranteed edge.

        confirmed: object -> (cx, cy, r) returned centre and residual radius; other objects use
        their retained centre and radius eps.
        """
        out = []
        for oid, dets in self.candidates.items():
            if oid in confirmed:
                cx, cy, r = confirmed[oid]
            else:
                (cx, cy), r = self.obj_xy[oid], self.eps
            for did in dets:
                dx, dy = self.det_xy[did]
                s2 = (dx - cx) ** 2 + (dy - cy) ** 2
                possible = s2 < (self.R + r) ** 2
                guaranteed = r < self.R and s2 < (self.R - r) ** 2
                if possible and not guaranteed:
                    out.append((did, oid, (did, oid) in self.present))
        return out

    def gain(self, edge_set):
        adjacency = {}
        for d, o in edge_set:
            adjacency.setdefault(d, []).append(o)
        return hopcroft_karp(self.base + self.additions, adjacency) - hopcroft_karp(self.base, adjacency)

    def adversary(self, confirmed=None, budget=None):
        confirmed = confirmed or {}
        flips = self.flippable(confirmed)
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

    def realize(self, chosen, confirmed=None, steps=25):
        """For each moved object, search a rational grid inside its admitted ball for a shift that
        realizes the whole flipped pattern of that object at once (all its candidate edges).
        A grid that finds nothing is reported as None: not found, never proved infeasible."""
        confirmed = confirmed or {}
        by_obj = {}
        for d, o, p in chosen:
            by_obj.setdefault(o, []).append((d, p))
        realized = {}
        for o, want in by_obj.items():
            if o in confirmed:
                (cx, cy, r) = confirmed[o]
            else:
                (cx, cy), r = self.obj_xy[o], self.eps
            desired = {did: (did, o) in self.present for did in self.candidates.get(o, [])}
            for d, p in want:
                desired[d] = not p
            found = None
            for i in range(-steps, steps + 1):
                for j in range(-steps, steps + 1):
                    dx, dy = r * i / steps, r * j / steps
                    if dx * dx + dy * dy > r * r:
                        continue
                    px, py = cx + dx, cy + dy
                    ok = True
                    for did, adj in desired.items():
                        ex, ey = self.det_xy[did]
                        if (((ex - px) ** 2 + (ey - py) ** 2) < self.R ** 2) != adj:
                            ok = False
                            break
                    if ok:
                        found = (dx, dy)
                        break
                if found:
                    break
            realized[o] = found
        return realized


class GeoCase:
    def __init__(self, raw, eps):
        self.case = Case(raw)
        self.eps = coord(eps)
        self.anchors = [GeoAnchor(a, eps) for a in raw['anchors']]
        self.by_id = {a.id: a for a in self.anchors}

    def certificate(self, confirmed=None, budget=None, realize=True):
        """confirmed: {(anchor, object): (cx, cy, r)} returned centres and residual radii, or a
        set/list of (anchor, object) meaning the exact-adjacency oracle (returned centre = retained,
        residual radius 0); that premise is recorded in the result."""
        started = time.perf_counter()
        case = self.case
        delta = case.delta()
        excluded = delta <= case.tolerance
        margin = delta - case.tolerance
        unit = case.fn + case.fp
        conf = {}
        oracle = False
        if confirmed:
            if isinstance(confirmed, dict):
                for (aid, o), (cx, cy, r) in confirmed.items():
                    conf.setdefault(aid, {})[o] = (Fraction(cx), Fraction(cy), Fraction(r))
                    oracle = oracle or Fraction(r) == 0
            else:
                oracle = True
                for aid, o in confirmed:
                    ox, oy = self.by_id[aid].obj_xy[o]
                    conf.setdefault(aid, {})[o] = (ox, oy, Fraction(0))
        sound = Fraction(0)
        solver = Fraction(0)
        edges_after = {}
        chosen_all = []
        boundary_total = 0
        for a in self.anchors:
            c = conf.get(a.id, {})
            g = a.gain(a.present)
            flips = a.flippable(c)
            nb = len(flips)
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
        result = {'criterion': 'excluded' if excluded else 'supported', 'delta': str(delta), 'margin': str(margin),
                  'epsilon': str(self.eps), 'confirmed': sum(len(v) for v in conf.values()),
                  'confirmation_model': ('none' if not conf else
                                         'exact_adjacency_oracle_residual_zero' if oracle else 'returned_centre_with_residual_radius'),
                  'boundary_edges_unconfirmed': boundary_total,
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
            total = Fraction(0)
            for a in self.anchors:
                e = edges_after.get(a.id, a.present)
                total += a.weight * ((case.fn + case.fp) * a.gain(e) - case.fp * len(a.additions))
            result['achieved_delta'] = str(total)
            result['achieved'] = 'crosses' if total <= case.tolerance else 'does_not_cross'
            moved = 0
            unrealized = 0
            displacements = []
            for a, flips in chosen_all:
                if realize:
                    real = a.realize(flips, conf.get(a.id, {}))
                    moved += len(real)
                    for o, v in real.items():
                        if v is None:
                            unrealized += 1
                        else:
                            displacements.append({'anchor': a.id, 'object': o,
                                                  'shift': [str(v[0]), str(v[1])]})
                else:
                    moved += len({o for _, o, _ in flips})
                    unrealized = None
            result['objects_moved'] = moved
            result['objects_unrealized'] = unrealized
            result['flips'] = sum(len(f) for _, f in chosen_all)
            result['status'] = ('insufficient_realized' if (unrealized == 0 and total <= case.tolerance)
                                else 'insufficient_relaxed' if realize else 'insufficient_unchecked')
            result['_displacements'] = displacements
        result['seconds'] = round(time.perf_counter() - started, 2)
        result['_confirmed'] = sorted(conf_key for aid in conf for conf_key in [(aid, o) for o in conf[aid]])
        result['_moved'] = [(a.id, o) for a, flips in chosen_all for o in {o for _, o, _ in flips}]
        return result


def _answer(geo, key, residual):
    """Declared computational oracle: the returned centre is the retained centre; residual radius as declared."""
    aid, o = key
    ox, oy = geo.by_id[aid].obj_xy[o]
    return (ox, oy, Fraction(residual))


def audit_boundary_first(geo, batch=10, max_rounds=500, residual=0):
    """Confirm the positions of objects with the most unconfirmed boundary edges until robust."""
    confirmed = {}
    cert = geo.certificate(confirmed, realize=False)
    rounds = 0
    history = []
    while cert.get('status', '').startswith('insufficient') and rounds < max_rounds:
        counts = {}
        for a in geo.anchors:
            for d, o, p in a.flippable({k[1]: v for k, v in confirmed.items() if k[0] == a.id}):
                if (a.id, o) not in confirmed:
                    counts[(a.id, o)] = counts.get((a.id, o), 0) + 1
        picks = sorted(counts, key=lambda k: (-counts[k], k))[:batch]
        if not picks:
            break
        for k in picks:
            confirmed[k] = _answer(geo, k, residual)
        history.append([list(k) for k in picks])
        rounds += 1
        cert = geo.certificate(confirmed, realize=False)
    return {'confirmed_positions': len(confirmed), 'rounds': rounds, 'final_status': cert.get('status'),
            'residual_radius': str(Fraction(residual)), '_history': history}


def audit_counterexample_guided(geo, batch=10, max_rounds=500, residual=0):
    confirmed = {}
    cert = geo.certificate(confirmed, realize=False)
    rounds = 0
    history = []
    while cert.get('status', '').startswith('insufficient') and rounds < max_rounds:
        picks = [m for m in cert['_moved'] if m not in confirmed][:batch]
        if not picks:
            break
        for k in picks:
            confirmed[k] = _answer(geo, k, residual)
        history.append([list(k) for k in picks])
        rounds += 1
        cert = geo.certificate(confirmed, realize=False)
    return {'confirmed_positions': len(confirmed), 'rounds': rounds, 'final_status': cert.get('status'),
            'residual_radius': str(Fraction(residual)), '_history': history}


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
