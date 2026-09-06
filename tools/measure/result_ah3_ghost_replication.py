"""Result AH3: the ghost coefficient (Result AH) on a second camera, a second lidar, and a second
operating point. The Result AH tool is imported unchanged; only its channel table and score
threshold are assigned before main() runs, as Result AB did for Z and AA. The imported tool's
header line names its default channels; the banner above each block is the configuration run.
"""
import importlib.util
import pathlib
import sys

here = pathlib.Path(__file__).parent
CONFIGS = [
    ("P2 FCOS3D x Megvii @0.30", {"camera": "predictions/fcos3d_val.json", "lidar": "predictions/megvii_val.json"}, 0.30),
    ("P3 Mapillary x PointPillars @0.30", {"camera": "predictions/mapillary_val.json", "lidar": "predictions/pointpillars-val.json"}, 0.30),
    ("P4 Mapillary x Megvii @0.50", {"camera": "predictions/mapillary_val.json", "lidar": "predictions/megvii_val.json"}, 0.50),
]


def main():
    for label, ch, score in CONFIGS:
        print("\n" + "#" * 92); print(f"# RESULT AH3  {label}  ::  result_ah_ghost_coincidence")
        print("# the imported tool's own header line names its default channels; this banner is the configuration run")
        print("#" * 92, flush=True)
        spec = importlib.util.spec_from_file_location("ah", here / "result_ah_ghost_coincidence.py")
        m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
        m.CH = ch; m.SCORE = score
        m.main()
    print("\n" + "-" * 92)
    print("NON-CLAIMS: replication of Result AH on released nuScenes validation predictions, retained as")
    print("proposed; every caveat of Result AH applies to each configuration. No detector is executed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
