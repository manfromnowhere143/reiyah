"""Clock census controls: input-only selection and honest missing-time states."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_opportunity_clock import summarize


def fixture():
    scenes = {"s": {"name": "scene-a", "nbr_samples": 3, "first_sample_token": "f0", "last_sample_token": "f2"}}
    samples = {f"f{i}": {"scene_token": "s", "timestamp": 1000000 + 2000000 * i,
                         "prev": f"f{i - 1}" if i else "", "next": f"f{i + 1}" if i < 2 else ""} for i in range(3)}
    records = [(f"l{i}", f"f{i}", "cal-lidar", row["timestamp"]) for i, row in enumerate(samples.values())]
    records += [(f"c{i}", f"f{i}", "cal-camera", row["timestamp"] + 30000) for i, row in enumerate(samples.values())]
    return [scenes, samples, records, {"cal-lidar": "sensor-l", "cal-camera": "sensor-c"},
            {"sensor-l": "LIDAR_TOP", "sensor-c": "CAM_FRONT"}, ["scene-a"], ["CAM_FRONT", "LIDAR_TOP"], 2000000]


class OpportunityClockTests(unittest.TestCase):
    def test_capture_offsets_do_not_become_online_availability(self):
        result, rows, _ = summarize(*fixture())
        self.assertEqual(result["sample_anchor_count"], 3)
        self.assertEqual(result["context_anchor_count"], 1)
        self.assertEqual(result["per_channel"]["CAM_FRONT"]["later_than_anchor_capture_count"], 3)
        self.assertEqual(result["per_channel"]["CAM_FRONT"]["absolute_p95_nearest_rank_us"], 30000)
        self.assertEqual(result["online_availability_times"], "unmeasured")
        self.assertIsNone(result["physical_joint_error_coefficient"])
        self.assertTrue(rows[1]["has_declared_scene_context"])

    def test_missing_camera_does_not_remove_an_anchor_or_supply_zero_offset(self):
        data = fixture()
        data[2] = [r for r in data[2] if r[2] != "cal-camera"]
        result, rows, _ = summarize(*data)
        self.assertEqual(result["sample_anchor_count"], 3)
        self.assertEqual(result["context_anchor_count"], 1)
        self.assertEqual(result["per_channel"]["CAM_FRONT"]["metadata_missing"], 3)
        self.assertIsNone(result["per_channel"]["CAM_FRONT"]["signed_min_us"])
        self.assertIsNone(rows[1]["channels"]["CAM_FRONT"]["capture_delta_us"])

    def test_duplicate_channel_record_is_rejected(self):
        data = fixture();data[2].append(data[2][0])
        with self.assertRaisesRegex(ValueError, "multiple keyframes"):
            summarize(*data)

    def test_broken_time_chain_is_rejected(self):
        data = fixture();data[1]["f1"]["next"] = ""
        with self.assertRaisesRegex(ValueError, "sample chain"):
            summarize(*data)

    def test_missing_boolean_or_inexact_timestamp_is_rejected(self):
        for bad in (None, True, 3000000.0):
            data = fixture();data[1]["f1"]["timestamp"] = bad
            with self.assertRaisesRegex(ValueError, "timestamp"):
                summarize(*data)

    def test_unknown_calibration_or_missing_requested_scene_is_rejected(self):
        data = fixture();data[3] = {}
        with self.assertRaisesRegex(ValueError, "calibration"):
            summarize(*data)
        data = fixture();data[5] = ["scene-absent"]
        with self.assertRaisesRegex(ValueError, "membership"):
            summarize(*data)


if __name__ == "__main__":
    unittest.main()
