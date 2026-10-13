"""Authored inputs only; no source TIFF read or model execution."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

OWNER = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('reconstruct', OWNER/'probe/reconstruct.py')
recon = importlib.util.module_from_spec(spec); spec.loader.exec_module(recon)
SOURCE = (OWNER/'candidate/research/multiorg-reference-admission/0.2.0/run_pair.py').read_bytes()

class Controls(unittest.TestCase):
    def test_altered_source_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'source digest'): recon.primitives(SOURCE+b'\n')

    def test_rectangular_lattice_and_orientation(self):
        self.assertEqual(recon.placement([600,700],4,256,256),((256,256),9))
        self.assertEqual(recon.placement([2860,3192],9,0,2304),((0,2304),156))
        self.assertEqual(recon.placement([2860,3192],155,2816,3072),((2816,3072),156))
        with self.assertRaisesRegex(ValueError, 'placement'): recon.placement([600,700],4,0,256)
        with self.assertRaisesRegex(ValueError, 'ordinal'): recon.placement([600,700],9,0,0)

    def test_constant_tile_known_normalization(self):
        original = recon.primitives(SOURCE)
        tensor,side=original['model_input'](np.full((512,512),128,dtype=np.uint8),'faster')
        expected=(np.float32(128)-np.array([123.675,116.28,103.53],dtype=np.float32))/np.array([58.395,57.12,57.375],dtype=np.float32)
        self.assertEqual(side,800);self.assertEqual(tensor.shape,(1,3,800,800));self.assertEqual(tensor.dtype,np.float32)
        for channel in range(3): self.assertTrue((tensor[0,channel]==expected[channel]).all())
        self.assertNotIn('execute', original);self.assertNotIn('decode_output',original)

    def test_incomplete_and_wrong_dtype_tile_refused(self):
        original=recon.primitives(SOURCE)
        for bad in [np.zeros((511,512),dtype=np.uint8),np.zeros((512,512),dtype=np.float32)]:
            with self.assertRaisesRegex(ValueError,'incomplete tile or dtype'):original['model_input'](bad,'faster')

    def test_constant_image_does_not_become_valid_tensor(self):
        original=recon.primitives(SOURCE)
        with self.assertRaisesRegex(ValueError,'constant or nonfinite'):
            original['prepare_image'](np.full((16,16),100,dtype=np.uint16))

if __name__=='__main__':unittest.main(verbosity=2)
