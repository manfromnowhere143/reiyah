"""Soundness and information-boundary controls for the development driver."""
from copy import deepcopy
from fractions import Fraction
from itertools import combinations, product
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare import (ROOT, ObservationService, additions, can_stop, conventional_bounds,
                     decision, direct_order, encoded, labels, observation, request_for,
                     sha, subject)
sys.path.insert(0, str(ROOT/'tests'))
from test_perception_revision import finite, direct_delta, ratio
from tools.perception_revision import contract, audit_checker
from replay import verify_event


class ExperimentControls(unittest.TestCase):
    def setUp(self):
        self.case = finite(['a'], ['a', 'b'], ['x', 'y'], {('a','x'),('b','y')})

    def test_endpoint_bounds_against_independent_all_worlds(self):
        checks = 0
        objects = ['x', 'y']
        possibilities = list(product(['a','b'], objects))
        for mask in range(16):
            edges = {e for i,e in enumerate(possibilities) if mask & (1 << i)}
            case = finite(['a'], ['a','b'], objects, edges)
            aid = case['anchors'][0]['id']
            for answers in product(['unknown','present','absent'], repeat=2):
                obs = [{'anchor':aid,'object':o,'outcome':v,'evidence_sha256':'0'*64}
                       for o,v in zip(objects,answers) if v != 'unknown']
                req = request_for(case,obs)
                values = []
                for n in range(3):
                    for removed_ids in combinations(objects,n):
                        if all(v=='unknown' or ((o not in removed_ids)==(v=='present')) for o,v in zip(objects,answers)):
                            values.append(direct_delta(case,{(aid,o) for o in removed_ids}))
                self.assertEqual(conventional_bounds(case,req),(min(values),max(values)))
                native = can_stop(case,req,'B')
                self.assertEqual(native['bounds'],[str(min(values)),str(max(values))])
                checks += 1
        self.assertEqual(checks,144)

    def test_strict_threshold_and_insufficiency_are_not_false_exclusion(self):
        self.assertEqual(decision((Fraction(1),Fraction(2)),Fraction(1)),'unresolved')
        self.assertEqual(decision((Fraction(-1),Fraction(1)),Fraction(1)),'excluded')
        self.assertEqual(can_stop(self.case,request_for(self.case),'B')['decision'],'unresolved')

    def test_replacement_rejects_monotonicity(self):
        case = finite(['a'],['b'],['x','y'],{('a','x'),('b','y')})
        self.assertFalse(additions(case))
        with self.assertRaises(ValueError):
            conventional_bounds(case,request_for(case))
        self.assertEqual({p['method'] for p in can_stop(case,request_for(case),'B')['proofs']},{'legacy','components'})

    def test_query_rejects_wrong_context_duplicate_and_unknown(self):
        case = self.case; key = labels(case)[0]
        service = ObservationService(case,sha(encoded(case)),{k:'present' for k in labels(case)})
        with self.assertRaises(ValueError):
            service.query(key,'0'*64,'test')
        changed = deepcopy(case); changed['reference_context_sha256']='f'*64
        with self.assertRaises(ValueError):
            service.query(key,subject(changed,key),'test')
        event = service.query(key,subject(case,key),'test')
        self.assertEqual(observation(event)['outcome'],'present')
        with self.assertRaises(ValueError):
            service.query(key,subject(case,key),'test')
        with self.assertRaises(ValueError):
            service.query(('missing','missing'),'0'*64,'test')

    def test_unresolved_answer_is_not_absent_or_present(self):
        case=self.case; key=labels(case)[0]
        service=ObservationService(case,sha(encoded(case)),{k:'unresolved' for k in labels(case)})
        event=service.query(key,subject(case,key),'test')
        self.assertIsNone(observation(event))
        self.assertEqual(event['residual_uncertainty'],'presence_unknown')
        self.assertEqual(event['cost']['observation_units'],1)

    def test_selector_cannot_read_hidden_answer_table(self):
        # Same original operands, opposite oracle contents: pre-query order identical.
        case=self.case
        first=ObservationService(case,sha(encoded(case)),{k:'present' for k in labels(case)})
        second=ObservationService(case,sha(encoded(case)),{k:'absent' for k in labels(case)})
        with patch.object(ObservationService,'query',side_effect=AssertionError('unqueried answer access')):
            self.assertEqual(direct_order(case),direct_order(deepcopy(case)))
        key=direct_order(case)[0][0]
        self.assertNotEqual(first.query(key,subject(case,key),'test')['answer'],
                            second.query(key,subject(case,key),'test')['answer'])

    def test_forged_native_result_rejected(self):
        case=self.case; req=request_for(case)
        payload=can_stop(case,req,'B')['proofs'][0]['payload']
        forged=deepcopy(payload); forged['result']['sufficiency']='sufficient'
        with self.assertRaises(Exception):
            audit_checker.check(case,req,forged)

    def test_changed_context_request_rejected(self):
        req=request_for(self.case); req['reference_context_sha256']='f'*64
        with self.assertRaises(Exception):
            contract.validate_request(self.case,req)

    def test_query_replay_rejects_rehashed_false_context_precision_and_cost(self):
        case=self.case; key=labels(case)[0]; digest=sha(encoded(case))
        service=ObservationService(case,digest,{k:'present' for k in labels(case)})
        event=service.query(key,subject(case,key),'test')
        spec={'input_sha256':digest}
        verify_event(case,spec,event,1,set())
        for field,value in [('source_input_sha256','f'*64),('reference_context_sha256','f'*64),
                            ('requested_precision','approximate'),('answer','absent')]:
            forged=deepcopy(event);forged[field]=value
            forged['evidence_sha256']=sha(encoded({k:v for k,v in forged.items() if k!='evidence_sha256'}))
            with self.assertRaises(ValueError):verify_event(case,spec,forged,1,set())
        forged=deepcopy(event);forged['cost']['human_seconds']=0
        forged['evidence_sha256']=sha(encoded({k:v for k,v in forged.items() if k!='evidence_sha256'}))
        with self.assertRaises(ValueError):verify_event(case,spec,forged,1,set())

    def test_query_replay_rejects_tamper_and_reordering(self):
        case=self.case;key=labels(case)[0];digest=sha(encoded(case))
        event=ObservationService(case,digest,{k:'present' for k in labels(case)}).query(key,subject(case,key),'test')
        with self.assertRaises(ValueError):verify_event(case,{'input_sha256':digest},event,2,set())
        forged=deepcopy(event);forged['answer']='absent'
        with self.assertRaises(ValueError):verify_event(case,{'input_sha256':digest},forged,1,set())


if __name__=='__main__':
    unittest.main()
