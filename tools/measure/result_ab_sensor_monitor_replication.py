"""Result AB: the two sensor monitors (Z, AA) on a second detector pair and a second operating point.

Results Z and AA left the two-sensor conjecture unsupported on one pair (Mapillary x Megvii) at one
operating point (0.30). Their registered reconsideration requirements ask for a second pair and a
second operating point before the conjecture may be called refuted rather than unsupported. This
reruns both tools, imported unchanged, on:

  P2  FCOS3D (camera) x Megvii (lidar) at 0.30          second camera
  P3  Mapillary (camera) x PointPillars (lidar) at 0.30  second lidar
  P4  Mapillary (camera) x Megvii (lidar) at 0.50        second operating point

Each configuration is set by assigning the imported modules' channel table and score threshold;
nothing in the Result Z or AA tools is edited. The verdict rule is the same: the coupling-aware
increment over the density (Z) or own-feature (AA) baseline must exceed its five-fold spread to
count as support.
"""
import importlib.util
import pathlib
import sys

here = pathlib.Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, here / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


CONFIGS = [
    ("P2 FCOS3D x Megvii @0.30", {"camera": ("matched_fcos3d.json", "predictions/fcos3d_val.json"),
                                  "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.30),
    ("P3 Mapillary x PointPillars @0.30", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                          "lidar": ("matched_pointpillars.json", "predictions/pointpillars-val.json")}, 0.30),
    ("P4 Mapillary x Megvii @0.50", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                    "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.50),
]


def main():
    for label, ch, score in CONFIGS:
        for tool in ("result_z_scene_blindness_monitor", "result_aa_disagreement_monitor"):
            print("\n" + "#" * 92)
            print(f"# RESULT AB  {label}  ::  {tool}")
            print("# the imported tool's own header line below names its default channels; this banner is the")
            print("# configuration actually run (channel table and score threshold assigned before main())")
            print("#" * 92, flush=True)
            m = load(tool)
            m.CH = ch
            m.SCORE = score
            rc = m.main()
            if rc:
                print(f"# {tool} refused this configuration (rc={rc})")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: replication of Results Z and AA on released nuScenes validation predictions,")
    print("retained as proposed. Each pair's match set was gated at its published mAP before use.")
    print("Descriptive, not a safety determination. No detector is executed. No released 1.2 byte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
