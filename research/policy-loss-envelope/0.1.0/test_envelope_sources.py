from copy import deepcopy
import csv
from fractions import Fraction as Q
from pathlib import Path
import tempfile
import unittest

from envelope_sources import FIELDS,MODELS,parse,read,sha


def row(model,i,left,right,fp,fn,references=3,last=False):
    rank=references-fn
    return dict(zip(('model','cell_id','threshold_left','threshold_right','left_closed','right_closed',
        'false_positives','misses','predictions','matching_rank','references','unit_loss'),
        (model,'cell-'+str(i).zfill(4),str(left),str(right),'True','True' if last else 'False',
         str(fp),str(fn),str(fp+rank),str(rank),str(references),str(fp+fn))))


def fixture():
    return [row('a',0,Q(1,4),Q(1,2),2,0),row('a',1,Q(1,2),Q(1),0,3),row('a',2,1,1,0,3,last=True),
            row('b',0,Q(1,4),1,0,2),row('b',1,1,1,0,3,last=True)]


class SourceControls(unittest.TestCase):
    def test_complete_cells_and_empty_endpoint(self):
        actual=parse(fixture(),models=('a','b'),counts=(3,2),references=3)
        self.assertEqual([len(c['lines']) for c in actual],[3,2])
        self.assertEqual(actual[0]['lines'][0],{'id':'cell-0000','fp':2,'fn':0})

    def test_missing_extra_fields_models_and_cells_fail(self):
        changes=[lambda r:r.pop(),lambda r:r[0].update(extra='0'),lambda r:r[0].update(model='c'),
                 lambda r:r[1].update(cell_id='cell-0000')]
        for change in changes:
            rows=fixture();change(rows)
            with self.assertRaises(ValueError):parse(rows,models=('a','b'),counts=(3,2),references=3)

    def test_threshold_gaps_closures_and_endpoint_fail(self):
        for change in ({'threshold_left':'3/5'},{'right_closed':'True'},{'left_closed':'False'}):
            rows=fixture();rows[1].update(change)
            with self.assertRaises(ValueError):parse(rows,models=('a','b'),counts=(3,2),references=3)
        rows=fixture();rows[2].update(threshold_right='2')
        with self.assertRaises(ValueError):parse(rows,models=('a','b'),counts=(3,2),references=3)

    def test_noncanonical_counts_matching_identities_and_monotonicity_fail(self):
        for change in ({'false_positives':'02'},{'misses':'-1'},{'matching_rank':'2'},{'references':'4'},
                       {'unit_loss':'3'}):
            rows=fixture();rows[0].update(change)
            with self.assertRaises(ValueError):parse(rows,models=('a','b'),counts=(3,2),references=3)
        rows=fixture();rows[1]=row('a',1,Q(1,2),1,3,1)
        with self.assertRaisesRegex(ValueError,'monotonicity'):parse(rows,models=('a','b'),counts=(3,2),references=3)

    def test_complete_synthetic_519_cell_run_and_separate_verification(self):
        from envelope_run import check,run
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/'synthetic.csv';rows=[]
            for model,count,misses in zip(MODELS,(299,220),(207,210)):
                for i in range(count):
                    lo=Q(1,4)+Q(3,4)*Q(i,count-1)
                    hi=Q(1,4)+Q(3,4)*Q(min(i+1,count-1),count-1)
                    rows.append(row(model,i,lo,hi,0,misses if i+1<count else 305,305,last=i+1==count))
            with path.open('w',newline='') as stream:
                writer=csv.DictWriter(stream,fieldnames=sorted(FIELDS));writer.writeheader();writer.writerows(rows)
            frozen={'models':list(MODELS),'population':64,'curve_path':str(path),
                    'bindings':[{'path':str(path),'bytes':path.stat().st_size,'sha256':sha(path)}]}
            run(frozen,root/'run');check(frozen,root/'run',root/'verification')
            result=read(root/'run/RESULTS.json')
            self.assertEqual([c['envelope_comparison'] for c in result['partition']],['tie','old_lower','old_lower'])
            self.assertEqual(result['partition'][1]['delta_mean_coefficients'],['0','-3/64'])
            self.assertEqual(read(root/'verification/VERIFICATION.json')['all_lines_verified'],519)


if __name__=='__main__':unittest.main()
