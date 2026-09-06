"""Result AM (exploratory): where does the same-kind ordering fail at 0.50?

Result AJ falsified, at the 0.50 operating point, the prediction that same-kind pairs are the
least independent: the two-camera pair and the two-lidar pair both read as more independent than
a cross-kind pair. This is a diagnostic, marked exploratory and not preregistered: the pairwise
inflation over independence (P(both miss) / product) for every pair at 0.30 and 0.50, stratified
by ego range band and by object class, on all annotated objects, with the per-stratum miss rates
beside each value so the marginal artifact of Result P can be seen where it acts. Definitions are
Result AF's, imported unchanged. No bands: this is a map of where to look, not a result.
"""
import importlib.util
import json
import pathlib
import sys
from itertools import combinations

import numpy as np

here = pathlib.Path(__file__).parent
spec = importlib.util.spec_from_file_location("af", here / "result_af_sensor_jury.py")
af = importlib.util.module_from_spec(spec); spec.loader.exec_module(af)


def main():
    gt = json.load(open(af.GT)); names = list(af.DET); matched = [af.load_matched(af.DET[n]) for n in names]
    dist = np.array([o["dist"] for o in gt]); cls = np.array([o["cls"] for o in gt])
    bands = [("0-20 m", dist < 20), ("20-30 m", (dist >= 20) & (dist < 30)), ("30-40 m", (dist >= 30) & (dist < 40)), ("40 m+", dist >= 40)]
    pairs = [(0, 1, "two cameras"), (2, 3, "two lidars"), (0, 2, "Mapillary x Megvii"), (0, 3, "Mapillary x PointPillars"), (1, 2, "FCOS3D x Megvii"), (1, 3, "FCOS3D x PointPillars")]
    print("=" * 96); print("RESULT AM (exploratory) - pairwise inflation by range band and class at 0.30 and 0.50"); print("=" * 96)
    for score in (0.30, 0.50):
        M = np.array([[matched[k].get(i, 0.0) < score for k in range(4)] for i in range(len(gt))])
        print(f"\n  score >= {score:.2f}, all annotated objects; cells: inflation (miss_i, miss_j)")
        print(f"    {'pair':<26}" + "".join(f"{b:>22}" for b, _ in bands) + f"{'all':>22}")
        for i, j, label in pairs:
            row = f"    {label:<26}"
            for _, m in bands + [("all", np.ones(len(gt), bool))]:
                wi, wj = M[m, i], M[m, j]; pi, pj = wi.mean(), wj.mean()
                infl = (wi & wj).mean() / (pi * pj) if pi * pj > 0 else np.nan
                row += f"{infl:>7.2f} ({100*pi:>3.0f},{100*pj:>3.0f})"
            print(row)
        print(f"\n    by class, inflation at {score:.2f}:")
        classes = ["car", "pedestrian", "barrier", "traffic_cone", "truck", "bus", "bicycle", "motorcycle", "trailer", "construction_vehicle"]
        print(f"    {'pair':<26}" + "".join(f"{c[:9]:>10}" for c in classes))
        for i, j, label in pairs:
            row = f"    {label:<26}"
            for c in classes:
                m = cls == c; wi, wj = M[m, i], M[m, j]; pi, pj = wi.mean(), wj.mean()
                row += f"{((wi & wj).mean() / (pi * pj) if pi * pj > 0 else float('nan')):>10.2f}"
            print(row)
    print("\n" + "-" * 96)
    print("NON-CLAIMS: exploratory diagnostic, not preregistered, no bands; marginal quantities including")
    print("shared difficulty; released detector outputs on the public nuScenes validation split. Not a")
    print("result and not a safety determination. No detector is executed. No released 1.2 byte.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
