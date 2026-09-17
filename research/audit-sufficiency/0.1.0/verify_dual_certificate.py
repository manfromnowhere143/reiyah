"""Independent checker for a solver-free localization robustness certificate.

A certificate file holds, per anchor, the rational multipliers (y_lo, y_hi) for the boundary-flip
program of that anchor at the declared epsilon and confirmed positions. This checker rebuilds the
program's exact data (cost, A, lo, hi) from the unit geometry with the declared rules, evaluates
the Neumaier-Shcherbina bound with exact rational arithmetic, rounds it up (the objective is an
integer gain), sums the certified maximum drops with the anchor weights, and compares with the
margin. It never runs a solver. What it shares with the producer is the program construction
from the declared matching rules; everything else is arithmetic.

Usage: python -B verify_dual_certificate.py UNIT_JSON CERT_JSON
Exit 0 and print 'robust certified' when the certificate proves robustness; exit 1 otherwise.
Produce a certificate with:  python -B verify_dual_certificate.py UNIT_JSON --emit EPS OUT_JSON
"""
import json
import sys
from fractions import Fraction

from localization import GeoCase
from dual_certificate import rigorous_bound


def program(anchor, confirmed):
    """Rebuild the exact program data for one anchor (same construction as GeoAnchor.adversary)."""
    import numpy as np
    from scipy.sparse import lil_matrix
    flips = anchor.flippable(confirmed)
    if not flips:
        return None
    fi = {(d, o): i for i, (d, o, _) in enumerate(flips)}
    nf = len(flips)
    all_pairs = sorted(anchor.present | {(d, o) for d, o, _ in flips})
    objs_in = sorted({o for _, o in all_pairs})
    dets = anchor.base + anchor.additions
    cover_vertices = dets + objs_in
    ci = {v: nf + i for i, v in enumerate(cover_vertices)}
    nc = len(cover_vertices)
    base_pairs = [(d, o) for d, o in all_pairs if d in anchor.base_set]
    mi = {e: nf + nc + i for i, e in enumerate(base_pairs)}
    nm = len(base_pairs)
    n = nf + nc + nm
    cost = [0] * n
    for j in range(nf, nf + nc):
        cost[j] = 1
    for j in range(nf + nc, n):
        cost[j] = -1
    rows = len(all_pairs) + nm + len(dets) + len(objs_in) + 1
    A = lil_matrix((rows, n))
    lo, hi = [], []
    r = 0
    for d, o in all_pairs:
        p = 1 if (d, o) in anchor.present else 0
        A[r, ci[d]] = 1
        A[r, ci[o]] = 1
        if (d, o) in fi:
            A[r, fi[(d, o)]] = -(1 - 2 * p)
        lo.append(p); hi.append(np.inf); r += 1
    for e in base_pairs:
        p = 1 if e in anchor.present else 0
        A[r, mi[e]] = 1
        if e in fi:
            A[r, fi[e]] = -(1 - 2 * p)
        lo.append(-np.inf); hi.append(p); r += 1
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
    lo.append(-np.inf); hi.append(np.inf); r += 1
    return cost, A.tocsr()[:r], lo, hi


def emit(unit_path, eps, out_path):
    geo = GeoCase(json.load(open(unit_path)), eps)
    cert = {'artifact_id': 'reiyah.research.audit-sufficiency.dual-certificate', 'version': '0.1.0',
            'comparison_id': geo.case.raw['comparison_id'], 'epsilon': str(geo.eps), 'confirmed': {}, 'anchors': {}}
    for a in geo.anchors:
        adv = a.adversary({})
        dc = adv.get('dual_certificate')
        if dc is None:
            continue
        cert['anchors'][a.id] = {'y_lo': [str(v) for v in dc['y_lo']], 'y_hi': [str(v) for v in dc['y_hi']]}
    json.dump(cert, open(out_path, 'w'), indent=1)
    print('emitted', len(cert['anchors']), 'anchor certificates')


def verify(unit_path, cert_path):
    cert = json.load(open(cert_path))
    geo = GeoCase(json.load(open(unit_path)), cert['epsilon'])
    case = geo.case
    delta = case.delta()
    margin = delta - case.tolerance
    unit = case.fn + case.fp
    total = Fraction(0)
    for a in geo.anchors:
        g = a.gain(a.present)
        prog = program(a, {})
        if prog is None:
            continue
        if a.id not in cert['anchors']:
            total += a.weight * unit * g          # no certificate: assume the whole gain is at risk
            continue
        cost, A, lo, hi = prog
        y_lo = [Fraction(v) for v in cert['anchors'][a.id]['y_lo']]
        y_hi = [Fraction(v) for v in cert['anchors'][a.id]['y_hi']]
        assert len(y_lo) == A.shape[0] == len(y_hi), 'certificate shape mismatch at %s' % a.id
        assert all(v >= 0 for v in y_lo + y_hi), 'negative multiplier at %s' % a.id
        b = rigorous_bound(cost, A, lo, hi, y_lo, y_hi)
        min_gain = -(-b.numerator // b.denominator)
        total += a.weight * unit * max(0, g - min_gain)
    print('delta', delta, 'margin', margin, 'certified max drop', total)
    if total < margin:
        print('robust certified')
        return 0
    print('not certified by this certificate')
    return 1


if __name__ == '__main__':
    if '--emit' in sys.argv:
        i = sys.argv.index('--emit')
        emit(sys.argv[1], sys.argv[i + 1], sys.argv[i + 2])
    else:
        sys.exit(verify(sys.argv[1], sys.argv[2]))
