from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/measure'))
from audit_collection_log_dependence import coefficient,bootstrap


class CollectionControls(unittest.TestCase):
    def test_known_independence_and_dependence(self):
        self.assertEqual(float(coefficient(np.array([[81.,9.,9.,1.]]))),1.)
        self.assertEqual(float(coefficient(np.array([[50.,0.,0.,50.]]))),2.)

    def test_undefined_is_not_zero(self):
        self.assertTrue(np.isnan(coefficient(np.array([[100.,0.,0.,0.]]))))
        r=bootstrap(np.array([[[100.,0.,0.,0.]]]),1,10)
        self.assertEqual(r['undefined_resamples'],10)
        self.assertIsNone(r['percentile_95'])

    def test_repeated_identical_groups_have_degenerate_band(self):
        cube=np.repeat(np.array([[[81.,9.,9.,1.]]]),3,axis=0)
        self.assertEqual(bootstrap(cube,1,101)['percentile_95'],[1.,1.])


if __name__=='__main__': unittest.main()
