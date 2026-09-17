"""Independent exhaustive check of the arbitrary-neighborhood relaxation."""
from itertools import product
import unittest
from common import w
from refine import graph_edit_bounds, rectangles
from test_observation import brute_rank, image, rectangle


class RefinedBoundControls(unittest.TestCase):
    def test_tight_over_disjoint_graph_neighborhoods(self):
        im=image(a=[rectangle('a0'),rectangle('a1')], b=[rectangle('b0'),rectangle('b1')])
        pairs=[(d,r) for d in range(4) for r in (0,1)]
        for bits in product((False,True),repeat=8):
            edges={p for p,yes in zip(pairs,bits) if yes}; bases=[]; all_deltas=[]
            for removed in [None,0,1]:
                refs={0,1}-{removed}; base={(d,r) for d,r in edges if r!=removed}
                ranks=[brute_rank((0,1),refs,base),brute_rank((2,3),refs,base)]
                bases.append({'ranks':ranks,'delta':w(2*(ranks[1]-ranks[0]))})
                all_deltas.append(2*(ranks[1]-ranks[0]))
                for neighbor_bits in product((False,True),repeat=4):
                    changed=base|{(d,2) for d,yes in zip(range(4),neighbor_bits) if yes}
                    all_deltas.append(2*(brute_rank((2,3),refs|{2},changed)-brute_rank((0,1),refs|{2},changed)))
            self.assertEqual(graph_edit_bounds(im,bases),(min(all_deltas),max(all_deltas)))

    def test_boundary_candidates_obey_declared_height(self):
        from common import q, iou
        im=image(b=[rectangle('b')])
        found=rectangles(im)
        self.assertTrue(all(q(row[3])-q(row[1])>=25 for row in found))
        self.assertTrue(any(iou(im['output_b']['value'][0],{'xyxy':row})==1/2 for row in found))


if __name__=='__main__':
    unittest.main()
