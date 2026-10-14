import unittest
import numpy as np
import reconstruct_inputs as r

class Tests(unittest.TestCase):
    def test_uniform_tile_channel_normalization(self):
        tile=np.full((512,512),255,np.uint8)
        for model,side in [('faster',800),('yolo',416)]:
            values=[(np.float32(255)-np.float32(m))/np.float32(s) for m,s in zip((123.675,116.28,103.53),(58.395,57.12,57.375))] if model=='faster' else [np.float32(1)]*3
            expected=np.empty((1,3,side,side),np.float32)
            for i,value in enumerate(values):expected[:,i,:,:]=value
            self.assertEqual(r.tensor(tile,model),{'dtype':'<f4','shape':[1,3,side,side],'c_order_data_sha256':r.sha(expected.tobytes())})
    def test_invalid_pixel_domains(self):
        for image in (np.ones((10,10)),np.full((10,10),np.nan),np.ones((10,10,3))):
            with self.subTest(shape=image.shape),self.assertRaises(ValueError):r.pixels(image)
    def test_tile_shape_dtype_and_model(self):
        for tile,model in [(np.zeros((511,512),np.uint8),'faster'),(np.zeros((512,512),np.float32),'faster'),(np.zeros((512,512),np.uint8),'unrecognized')]:
            with self.assertRaises(ValueError):r.tensor(tile,model)

if __name__=='__main__':unittest.main()
