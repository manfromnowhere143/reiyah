"""Adapter controls; actual data is never used by these tests."""
from copy import deepcopy
from fractions import Fraction
import unittest

from timing_witness import context, digest, refine, search_identity, w
from timing_witness_verify import check_pair, check_rows, reconstruct
from operating_certificate import check_case, verify_proof
from operating_math import FAMILIES, aggregate, analyze_state, world_banks
from operating_sources import ANCHORS, filtered_image
from test_operating_math import synthetic_sources
from test_timing_bounds import image, rectangle
from timing_bounds import candidates


def cache():
    return {'native': set(), 'native_check_seconds': 0., 'pools': set(), 'searches': {}}


def synthetic():
    item = image([rectangle('a', [30,30,60,60])], [rectangle('b', [31,30,61,60])])
    known = []; edit = {'search_state': 'complete', 'search': {'witnesses': {d: {
        'edit': {'operation': 'none', 'removed_reference': None, 'inserted_reference': None},
        'altered_references': []} for d in ('lower','upper')}}}
    temporal = {'known_references': known, 'current_unknown_instances': ['u'], 'union_unknown_instances': ['u'],
                'proofs': {'known': {'references': []}}, 'candidate_pool': candidates(item)}
    bank = world_banks([], edit, temporal); inherited = {}
    before = {'image': item, 'custody': {}, 'analysis': analyze_state(item, bank, inherited)}
    new = {}; pools = {}; searches = {}; key = digest({'image': item, 'custody': {}})
    after, detail = refine(before, bank, temporal, 'current_partial', inherited, new, pools, searches, [key,'current_partial'])
    union, second = refine(after, bank, temporal, 'union_partial', inherited, new, pools, searches, [key,'union_partial'])
    return before, after, union, detail, second, bank, temporal, inherited, new, pools, key


class AdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = synthetic()

    def check(self, before=None, after=None, detail=None, bank=None, temporal=None, new=None):
        b,a,u,d,s,bk,t,p,n,pools,key = self.data
        new = n if new is None else new; checked = cache()
        for proof_key, value in new.items(): verify_proof(proof_key, value, checked)
        return check_pair(b if before is None else before, a if after is None else after,
                          bk if bank is None else bank, t if temporal is None else temporal,
                          'current_partial', d if detail is None else detail, p, new, pools, checked, [key,'current_partial'])

    def test_complete_worlds_and_exact_context_reuse(self):
        b,a,u,d,s,bk,t,p,n,pools,key = self.data; checked = cache()
        for k,v in n.items(): verify_proof(k,v,checked)
        first = check_pair(b,a,bk,t,'current_partial',d,p,n,pools,checked,[key,'current_partial'])
        second = check_pair(a,u,bk,t,'union_partial',s,p,n,pools,checked,[key,'union_partial'])
        self.assertGreater(first[1],0); self.assertEqual(second[1],0)
        self.assertEqual(s['reused_from'],[key,'current_partial'])
        self.assertEqual(a['analysis']['families']['current_partial']['attained'], [w(-2),w(2)])

    def test_same_id_different_geometry_cannot_reuse(self):
        b,a,u,d,s,bk,t,p,n,pools,key = self.data
        known,unknown,bases = context(b,bk,t,'current_partial'); pool = pools[d['pool_key']]
        original = search_identity(b['image'],known,unknown,pool,d['seeds'],d['search']['bounds'])
        for field in ('image','unknown','known','bounds','seeds'):
            args = {'image':deepcopy(b['image']), 'known':deepcopy(known), 'unknown':list(unknown),
                    'pool':pool,'seeds':deepcopy(d['seeds']),'bounds':deepcopy(d['search']['bounds'])}
            if field == 'image': args[field]['width'] += 1
            elif field == 'unknown': args[field] = ['another']
            elif field == 'known': args[field] = [rectangle('new',[0,0,25,25])]
            elif field == 'bounds': args[field][0] = w(-99)
            else: args[field][0]['measurement']['ranks'][0] += 1
            self.assertNotEqual(search_identity(**args),original)
        bad = deepcopy(d); bad['reused_from'] = ['same-image','current_partial']; bad['new_search']=False
        with self.assertRaisesRegex(ValueError,'reuse'): self.check(detail=bad)

    def test_forged_optional_operation_and_absence_rejected(self):
        d = self.data[3]
        for field in ('instance','candidate_index','operation'):
            bad = deepcopy(d); bad['endpoints'][0]['operations'][0][field] = 'forged'
            with self.assertRaisesRegex(ValueError,'forged'): self.check(detail=bad)
        bad = deepcopy(d); bad['endpoints'][0]['absent_or_ineligible'] = ['invented']
        with self.assertRaisesRegex(ValueError,'forged'): self.check(detail=bad)

    def test_wrong_census_budget_and_absent_inputs_rejected(self):
        b,a,u,d,s,bk,t,p,n,pools,key = self.data
        for value in (None, [], ['u','u'], ['wrong']):
            bad = deepcopy(t); bad['current_unknown_instances'] = value
            with self.assertRaises(ValueError): self.check(temporal=bad)
        bad = deepcopy(bk); bad['temporal']['current']['unknown_count'] += 1
        with self.assertRaisesRegex(ValueError,'budget'): self.check(bank=bad)
        bad = deepcopy(b); bad['analysis']['families']['current_partial']['state']='input_blocked'
        with self.assertRaisesRegex(ValueError,'Absent'): self.check(before=bad)

    def test_wrong_bounds_threshold_context_and_other_family_rejected(self):
        a = self.data[1]
        for family in ('current_partial','union_partial'):
            bad=deepcopy(a); bad['analysis']['families'][family]['bounds'][0]=w(99)
            with self.assertRaisesRegex(ValueError,'changed'): self.check(after=bad)
        bad=deepcopy(a); bad['custody']={'wrong_threshold':True}
        with self.assertRaisesRegex(ValueError,'threshold'): self.check(after=bad)

    def test_wrong_proof_and_forged_native_payload_rejected(self):
        d=self.data[3]; n=self.data[8]
        bad=deepcopy(d); bad['endpoints'][0]['proof_key']='wrong'
        with self.assertRaisesRegex(ValueError,'proof'): self.check(detail=bad)
        with self.assertRaisesRegex(ValueError,'proof'): self.check(new={})
        bad=deepcopy(n); next(iter(bad.values()))['proof']['payload']['result']['bounds']['lower']=w(99)
        with self.assertRaises(Exception): self.check(new=bad)

    def test_nonexact_skip_and_failed_changed_state_rejected(self):
        b=self.data[0]
        with self.assertRaisesRegex(ValueError,'inheritance'):
            self.check(after=b,detail={'state':'inherited_exact','new_search':False})
        failure={'state':'search_incomplete','new_search':True,'error':'synthetic timeout','retained_attempt_proof_keys':[]}
        self.check(after=b,detail=failure)
        with self.assertRaisesRegex(ValueError,'Failed'): self.check(detail=failure)

    def test_repeated_geometry_keeps_distinct_unknown_identities(self):
        b,a,u,d,s,bk,t,p,n,pools,key=self.data; pool=pools[d['pool_key']]
        unknown=['u0','u1']; indices=[0,0]
        endpoint={'operations':[{'operation':'optional_eligible','instance':u,'candidate_index':0} for u in unknown],
                  'absent_or_ineligible':[]}
        refs=reconstruct([],unknown,pool,endpoint,indices,b['image'])
        self.assertEqual(refs[0]['xyxy'],refs[1]['xyxy']); self.assertNotEqual(refs[0]['id'],refs[1]['id'])
        with self.assertRaises(ValueError): reconstruct([],['u0'],pool,endpoint,indices,b['image'])

    def test_every_anchor_and_family_complete_case_composition(self):
        item,packets,original,edit,temporal=synthetic_sources()
        temporal['candidate_pool']=candidates(item); bank=world_banks(original,edit,temporal)
        count=0
        for threshold in ANCHORS:
            img,custody=filtered_image(item,packets,threshold,'3'*64); old={}
            before={'image':img,'custody':custody,'analysis':analyze_state(img,bank,old)}
            # Keep a legitimate known-only incumbent to exercise optional search.
            v=before['analysis']['families']['current_partial']; known=before['analysis']['known_proof_key']
            v['attained']=[old[known]['measurement']['delta']]*2; v['proof_keys']=[known]*2
            new={}; pools={}; checked=cache(); key=digest({'image':img,'custody':custody})
            after,detail=refine(before,bank,temporal,'current_partial',old,new,pools,{},[key,'current_partial'])
            for k,v in new.items(): verify_proof(k,v,checked)
            check_pair(before,after,bank,temporal,'current_partial',detail,old,new,pools,checked,[key,'current_partial'])
            case={'id':'case','group':'primary','images':[img['id']]}
            for family in FAMILIES:
                row=aggregate(case,family,[key],{key:after})
                check_case(row,case,family,[key],{key:after},{**old,**new}); count+=1
        self.assertEqual(count,56)

    def test_wrong_case_threshold_and_bound_rejected(self):
        b,a,u,d,s,bk,t,p,n,pools,key=self.data; case={'id':'case','group':'primary','images':[b['image']['id']]}
        old=aggregate(case,'current_partial',[key],{key:b}); old['cell_id']='cell-0000'
        row=aggregate(case,'current_partial',[key],{key:a}); row['cell_id']='cell-0000'
        parent={'primary_rows':[old],'anchor_rows':[]}
        result={'primary_rows':[row],'anchor_rows':[], 'evidence_counts':{'primary_rows':{'opposite_worlds':1},'anchor_rows':{}},
                'target_classifications':[{'section':'primary_rows','index':0,'classification':'opposing_worlds_established','failed_components':[]}]}
        allocation={'target_rows':[['primary_rows',0]]}
        check_rows(parent,result,allocation,{key:a},{**p,**n},{})
        for field,value in [('cell_id','cell-0001'),('bounds',[w(-99),w(99)]),('membership',[])]:
            bad=deepcopy(result); bad['primary_rows'][0][field]=value
            with self.assertRaises(ValueError): check_rows(parent,bad,allocation,{key:a},{**p,**n},{})


if __name__ == '__main__': unittest.main()
