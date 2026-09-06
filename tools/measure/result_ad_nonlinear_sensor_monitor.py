"""Result AD: the two sensor monitors (Z, AA) with a non-linear model, stated in advance.

The registered reconsideration requirements for the two-sensor conjecture ask for a non-linear
monitor named before it is run. This names it: a histogram gradient-boosted model with default
depth, 200 iterations, learning rate 0.05, seeded, replacing the Poisson regression in Result Z
(with a Poisson loss) and the logistic regression in Result AA (calibrated by the same isotonic
cross-validation wrapper). Features, labels, splits, baselines and the verdict rule are imported
from the Result Z and AA tools unchanged; only the model class is swapped by assignment. All four
configurations of Results Z, AA and AB are run: the primary pair at 0.30, the second camera, the
second lidar, and the second operating point. The verdict rule is the same as before: the
increment over the density (Z) or own-feature (AA) baseline must exceed its five-fold spread to
count as support. If a boosted model cannot find it, the conjecture stays unsupported for this
program's data; if it can, the linear negative results were a model limitation and the register
records that.
"""
import importlib.util
import pathlib
import sys

import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor

here = pathlib.Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, here / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


class BoostedPoisson:
    """Drop-in for PoissonRegressor(alpha, max_iter): same fit/predict; coef_ is reported as the
    permutation-free feature count of the boosted model, zeros, so the imported coefficient
    print-out reads as 'not a linear model' rather than crashing."""
    def __init__(self, alpha=None, max_iter=None):
        self.m = HistGradientBoostingRegressor(loss="poisson", max_iter=200, learning_rate=0.05, random_state=20260906)
    def fit(self, X, y):
        self.m.fit(X, y); self.coef_ = np.zeros(X.shape[1]); return self
    def predict(self, X):
        return self.m.predict(X)


class BoostedLogistic:
    """Drop-in for LogisticRegression(max_iter): same fit/predict_proba, sklearn-compatible so the
    calibration wrapper can clone it."""
    def __init__(self, max_iter=None):
        self.max_iter = max_iter
    def get_params(self, deep=True):
        return {"max_iter": self.max_iter}
    def set_params(self, **p):
        self.max_iter = p.get("max_iter", self.max_iter); return self
    def fit(self, X, y):
        self.m = HistGradientBoostingClassifier(max_iter=200, learning_rate=0.05, random_state=20260906).fit(X, y)
        self.classes_ = self.m.classes_; return self
    def predict_proba(self, X):
        return self.m.predict_proba(X)
    def predict(self, X):
        return self.m.predict(X)
    def __sklearn_tags__(self):
        from sklearn.utils import Tags, ClassifierTags, TargetTags
        t = Tags(estimator_type="classifier", target_tags=TargetTags(required=True), classifier_tags=ClassifierTags())
        return t


CONFIGS = [
    ("P1 Mapillary x Megvii @0.30", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                    "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.30),
    ("P2 FCOS3D x Megvii @0.30", {"camera": ("matched_fcos3d.json", "predictions/fcos3d_val.json"),
                                  "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.30),
    ("P3 Mapillary x PointPillars @0.30", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                          "lidar": ("matched_pointpillars.json", "predictions/pointpillars-val.json")}, 0.30),
    ("P4 Mapillary x Megvii @0.50", {"camera": ("matched_mapillary.json", "predictions/mapillary_val.json"),
                                    "lidar": ("matched_megvii.json", "predictions/megvii_val.json")}, 0.50),
]


def main():
    rc_all = 0
    for label, ch, score in CONFIGS:
        for tool, patch in (("result_z_scene_blindness_monitor", ("PoissonRegressor", BoostedPoisson)),
                            ("result_aa_disagreement_monitor", ("LogisticRegression", BoostedLogistic))):
            print("\n" + "#" * 92)
            print(f"# RESULT AD  boosted  {label}  ::  {tool}")
            print("# the imported tool's own header line below names its default channels; this banner is the")
            print("# configuration actually run; the Z-form coefficient print-out is all zeros by construction")
            print("#" * 92, flush=True)
            m = load(tool)
            m.CH = ch; m.SCORE = score
            setattr(m, patch[0], patch[1])
            rc = m.main()
            if rc:
                print(f"# {tool} refused this configuration (rc={rc})"); rc_all = rc
    print("\n" + "-" * 92)
    print("NON-CLAIMS: replication of Results Z and AA with a boosted model named in advance, on four")
    print("configurations, retained as proposed. Descriptive, not a safety determination. No detector")
    print("is executed. No released 1.2 byte is involved.")
    return rc_all


if __name__ == "__main__":
    sys.exit(main())
