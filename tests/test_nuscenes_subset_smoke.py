"""Small counterexamples for real temporal histories and coordinate conventions."""
import copy
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "measure"))
import smoke_nuscenes_training_subset as smoke


class FakeSDK:
    def __init__(self):
        self.sample = {"token": "sample", "scene_token": "scene", "data": {c: c for c in smoke.CHANNELS}}
        self.rows = {c: {"token": c, "sample_token": "sample", "is_key_frame": True,
                         "channel": c, "timestamp": 100, "prev": "", "next": ""} for c in smoke.CHANNELS}
        self.rows["LIDAR_TOP"]["prev"] = "previous"
        self.rows["previous"] = {"token": "previous", "sample_token": "sample", "is_key_frame": False,
                                 "channel": "LIDAR_TOP", "timestamp": 90, "prev": "", "next": "LIDAR_TOP"}

    def get(self, table, token):
        return self.rows[token] if table == "sample_data" else self.sample


class SubsetSDKSmokeTests(unittest.TestCase):
    def test_scalar_first_rotation_and_sign_invariance(self):
        half = np.sqrt(0.5)
        expected = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        np.testing.assert_allclose(smoke.rotation([half, 0, 0, half]), expected, atol=1e-15)
        np.testing.assert_allclose(smoke.rotation([-half, 0, 0, -half]), expected, atol=1e-15)
        for bad in ([0, 0, 0, 0], [np.nan, 0, 0, 1], [1, 0, 0], [2, 0, 0, 0]):
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "invalid rotation"):
                smoke.rotation(bad)

    def test_short_histories_stay_short(self):
        sdk = FakeSDK()
        keys, previous = smoke.temporal_sources(sdk, sdk.sample)
        self.assertEqual(len(keys), 7)
        self.assertEqual([r["token"] for r in previous], ["previous"])
        sdk.rows["LIDAR_TOP"]["prev"] = ""
        self.assertEqual(smoke.temporal_sources(sdk, sdk.sample)[1], [])

    def test_tenth_cached_candidate_is_retained_for_nine_of_ten_training_draws(self):
        sdk = FakeSDK()
        sdk.rows["LIDAR_TOP"]["prev"] = "p1"
        for i in range(1, 12):
            sdk.rows["p" + str(i)] = {"token": "p" + str(i), "sample_token": "sample", "is_key_frame": False,
                                     "channel": "LIDAR_TOP", "timestamp": 100-i,
                                     "next": "LIDAR_TOP" if i == 1 else "p" + str(i-1),
                                     "prev": "p" + str(i+1) if i < 11 else ""}
        previous = smoke.temporal_sources(sdk, sdk.sample)[1]
        self.assertEqual([r["token"] for r in previous], ["p" + str(i) for i in range(1, 11)])

    def test_nonreciprocal_future_and_foreign_channel_sources_rejected(self):
        for field, value in (("next", "absent"), ("timestamp", 101), ("channel", "CAM_FRONT")):
            sdk = FakeSDK()
            sdk.rows["previous"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "temporal source boundary"):
                smoke.temporal_sources(sdk, sdk.sample)

    def test_missing_channel_is_not_an_empty_negative(self):
        sdk = FakeSDK()
        del sdk.sample["data"]["CAM_FRONT"]
        with self.assertRaisesRegex(ValueError, "missing requested channel"):
            smoke.temporal_sources(sdk, sdk.sample)


if __name__ == "__main__":
    unittest.main()
