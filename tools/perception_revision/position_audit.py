"""Propose a current comparison proof after bounded position observations."""
from . import localization
from .position_contract import VERSION, condition
from .position_checker import conclude


def produce(case, request, observations, linear_certificate=None):
    report, derived = condition(case, request, observations)
    proof = {'kind': 'position_audit', 'version': VERSION, 'conditioning': report,
             'geometry': localization.produce(*derived, linear_certificate=linear_certificate)['proof'] if derived is not None else None}
    return {'result': conclude(case, request, observations, proof), 'proof': proof}
