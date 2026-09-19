"""Offline finite-population audit methods, version 0.1.0.

This research module implements a specified linear-betting construction, not
product behavior, physical truth, or a complete reproduction of any paper.
"""
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json

VERSION = '0.1.0'
ARMS = ('uniform', 'weight', 'proxy', 'proxy_cv')
STATES = {'observed', 'missing', 'unmeasured', 'out_of_distribution', 'sensor_invalid', 'abstained'}

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode()

def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()

def rational(value):
    if not isinstance(value, str):
        raise ValueError('rational_string_required')
    try:
        r = F(value)
    except (ValueError, ZeroDivisionError):
        raise ValueError('invalid_rational') from None
    if str(r) != value:
        raise ValueError('canonical_rational_required')
    return r

def validate(pop):
    if set(pop) != {'id', 'version', 'threshold', 'units', 'purpose'} or pop['version'] != VERSION:
        raise ValueError('population_properties')
    units = pop['units']
    if not 1 <= len(units) <= 6 or len({u['id'] for u in units}) != len(units):
        raise ValueError('population_membership')
    if not -1 <= rational(pop['threshold']) <= 1:
        raise ValueError('threshold_range')
    weights = []
    for u in units:
        if set(u) != {'id', 'weight', 'lower', 'upper', 'proxy', 'status', 'cluster'}:
            raise ValueError('unit_properties')
        w, lo, hi, proxy = (rational(u[k]) for k in ('weight', 'lower', 'upper', 'proxy'))
        if w < 0 or not -1 <= lo <= hi <= 1 or not -1 <= proxy <= 1:
            raise ValueError('unit_range')
        if u['status'] not in STATES:
            raise ValueError('unknown_observation_status')
        if u['status'] != 'observed' and (lo, hi) != (F(-1), F(1)):
            raise ValueError('unavailable_must_retain_full_interval')
        weights.append(w)
    if sum(weights) != 1:
        raise ValueError('weight_sum')
    return pop

def probabilities(weights, proxies, remaining, arm):
    if arm not in ARMS:
        raise ValueError('unknown_arm')
    scores = {}
    for i in remaining:
        if weights[i] <= 0:
            raise ValueError('inactive_member_sampled')
        scores[i] = F(1) if arm == 'uniform' else weights[i]
        if arm in ('proxy', 'proxy_cv'):
            scores[i] *= F(1, 8) + (proxies[i] + 1) / 2
    total = sum(scores.values())
    return {i: score / total for i, score in scores.items()}

def validate_probabilities(q, remaining):
    if set(q) != set(remaining) or any(p <= 0 for p in q.values()) or sum(q.values()) != 1:
        raise ValueError('sampling_support_or_mass')

def logical(pop, seen):
    low = sum(F(u['weight']) * (F(u['lower']) if i in seen else -1) for i, u in enumerate(pop['units']))
    high = sum(F(u['weight']) * (F(u['upper']) if i in seen else 1) for i, u in enumerate(pop['units']))
    tau = F(pop['threshold'])
    return ('supported' if low > tau else 'excluded' if high <= tau else 'unresolved'), low, high

def factor(weights, proxies, observations, remaining, q, selected, value, threshold, cv):
    """One-sided nonnegative supermartingale factor; threshold is endpoint total."""
    validate_probabilities(q, remaining)
    used = sum(weights[i] * x for i, x in observations.items())
    mu = threshold - used
    center = sum(weights[i] * proxies[i] for i in remaining) if cv else F(0)
    minimum = center + min(-weights[i] * proxies[i] / q[i] for i in remaining) if cv else F(0)
    z = weights[selected] * (value - (proxies[selected] if cv else 0)) / q[selected] + center
    stake = F(1, 2) / (mu-minimum) if mu > minimum else F(0)
    f = 1 + stake * (z-mu)
    if f < 0:
        raise ValueError('negative_factor')
    return f

def walk(pop, arm):
    """Enumerate all orders with positive sampling probability; no outcome pruning."""
    validate(pop)
    units = pop['units']
    weights = [F(u['weight']) for u in units]
    proxies = [F(u['proxy']) for u in units]
    active = tuple(i for i, w in enumerate(weights) if w > 0)
    tau = F(pop['threshold'])
    low_x = [(F(u['lower'])+1)/2 for u in units]
    high_x = [(1-F(u['upper']))/2 for u in units]
    proxy_low = [(x+1)/2 for x in proxies]
    proxy_high = [(1-x)/2 for x in proxies]
    thresholds = ((tau+1)/2, (1-tau)/2)
    alpha_side = F(1, 40)
    initial = logical(pop, set())[0]
    initial_stop = (0, initial, 'logical', F(1), F(1)) if initial != 'unresolved' else None

    @lru_cache(None)
    def next_steps(seen_key):
        remaining = tuple(i for i in active if i not in seen_key)
        q = probabilities(weights, proxies, remaining, arm)
        prior_low = {i: low_x[i] for i in seen_key}
        prior_high = {i: high_x[i] for i in seen_key}
        return tuple((i, q[i],
                      factor(weights, proxy_low, prior_low, remaining, q, i, low_x[i], thresholds[0], arm == 'proxy_cv'),
                      factor(weights, proxy_high, prior_high, remaining, q, i, high_x[i], thresholds[1], arm == 'proxy_cv'))
                     for i in remaining)

    @lru_cache(None)
    def exact_decision(seen_key):
        return logical(pop, set(seen_key))[0]

    def visit(order, probability, e_low, e_high, exact_stop, stat_stop, cross_low, cross_high):
        seen = set(order)
        remaining = tuple(i for i in active if i not in seen)
        seen_key = tuple(sorted(seen))
        decision = exact_decision(seen_key)
        if decision != 'unresolved' and exact_stop is None:
            exact_stop = (len(order), decision)
        if stat_stop is None:
            if decision != 'unresolved':
                stat_stop = (len(order), decision, 'logical', e_low, e_high)
            elif not remaining:
                stat_stop = (len(order), 'unresolved', 'residual_reference', e_low, e_high)
            elif e_low >= 1/alpha_side and e_high >= 1/alpha_side:
                stat_stop = (len(order), 'unresolved', 'statistical_conflict', e_low, e_high)
            elif e_low >= 1/alpha_side:
                stat_stop = (len(order), 'supported', 'statistical', e_low, e_high)
            elif e_high >= 1/alpha_side:
                stat_stop = (len(order), 'excluded', 'statistical', e_low, e_high)
        cross_low = cross_low or e_low >= 1/alpha_side
        cross_high = cross_high or e_high >= 1/alpha_side
        if not remaining:
            exact_stop = exact_stop or (len(order), 'unresolved')
            yield {'population': pop['id'], 'arm': arm, 'order': ''.join(map(str, order)),
                   'probability': str(probability), 'exact_stop': str(exact_stop[0]),
                   'exact_decision': exact_stop[1], 'stat_stop': str(stat_stop[0]),
                   'stat_decision': stat_stop[1], 'stat_reason': stat_stop[2],
                   'e_lower_at_stop': str(stat_stop[3]), 'e_upper_at_stop': str(stat_stop[4]),
                   'lower_ever_crossed': str(int(cross_low)), 'upper_ever_crossed': str(int(cross_high))}
            return
        for i, q_i, a, b in next_steps(seen_key):
            yield from visit(order+(i,), probability*q_i, e_low*a, e_high*b,
                             exact_stop, stat_stop, cross_low, cross_high)
    yield from visit((), F(1), F(1), F(1), (0, initial) if initial != 'unresolved' else None,
                     initial_stop, False, False)
