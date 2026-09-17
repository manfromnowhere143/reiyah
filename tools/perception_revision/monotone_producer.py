"""Propose two endpoint matching proofs per compatible joint reference world."""
from .monotone_plan import VERSION, admission


def propose(case, domains):
    from .audit import world_proposal
    plan = admission(case, domains)
    if plan['reason'] is not None:
        return {'kind': 'monotone_unavailable', 'version': VERSION, **plan}
    proof = {'kind': 'monotone_deletions', 'version': VERSION, 'worlds': []}
    for bits, env, (required, free, _) in domains:
        lower, _ = world_proposal(case, env, required | set(free))
        upper, _ = world_proposal(case, env, required)
        proof['worlds'].append({'assignment': list(bits), 'lower': lower, 'upper': upper})
    return proof
