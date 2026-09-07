from pathlib import Path
import math
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/measure'))
from spatial_continuity_monitor import geometry_rows,velocity_sites,support,log_resampled_scene_mean


def box(x): return ('car',.8,float(x),0.)


class SpatialControls(unittest.TestCase):
    def test_moving_site_changes_projection(self):
        projected=velocity_sites([box(3)],[box(0)],.5,.5)
        self.assertEqual(projected,[box(6)])
        self.assertEqual(support([box(3)],[box(6)],[box(6)])['r2.both_absent'],1.)
        self.assertEqual(support(projected,[box(6)],[box(6)])['r2.both_present'],1.)

    def test_ties_and_nonmutual_associations_rejected(self):
        self.assertEqual(velocity_sites([box(0)],[box(-1),box(1)],1.,1.),[])
        self.assertEqual(len(velocity_sites([box(0),box(.1)],[box(0)],1.,1.)),1)
        self.assertEqual(velocity_sites([box(10)],[box(0)],1.,1.),[])

    def test_invalid_projection_clock_rejected(self):
        with self.assertRaises(ValueError): velocity_sites([box(0)],[box(0)],0.,1.)

    def test_future_outputs_cannot_change_past_geometry(self):
        frames=np.array(['a','b','c','d']);scenes=np.array(['s']*4);times=np.arange(4)*500000
        camera={t:[box(i)] for i,t in enumerate(frames)};lidar={t:[box(i)] for i,t in enumerate(frames)}
        a,names=geometry_rows(camera,lidar,frames,scenes,times)
        camera['d']=[box(1000)]
        b,other=geometry_rows(camera,lidar,frames,scenes,times)
        self.assertEqual(names,other);np.testing.assert_equal(a[:3],b[:3])
        self.assertTrue(math.isnan(a[0,names.index('stationary.sites')]))
        self.assertEqual(a[0,names.index('previous_available')],0.)

    def test_empty_history_is_an_observed_empty(self):
        x,names=geometry_rows({'a':[],'b':[]},{'a':[],'b':[]},np.array(['a','b']),np.array(['s','s']),np.array([1,2]))
        self.assertEqual(x[1,names.index('stationary.sites')],0.)
        self.assertTrue(math.isnan(x[1,names.index('stationary.site_score_mean')]))
        self.assertEqual(x[1,names.index('previous_available')],1.)

    def test_log_resampling_preserves_equal_scene_point(self):
        rows=[{'log':log,'scene':scene,'y':0,'prediction':{'base':p,'candidate':1.}}
              for log,scene,p in [('a','a1',2.),('a','a2',2.),('b','b1',4.)]]
        r=log_resampled_scene_mean(rows,'base','candidate',repetitions=100)
        self.assertAlmostEqual(r['improvement'],10/3)
        self.assertEqual(r['scenes'],3);self.assertEqual(r['logs'],2)


if __name__=='__main__': unittest.main()
