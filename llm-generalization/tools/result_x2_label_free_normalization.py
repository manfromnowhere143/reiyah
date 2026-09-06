"""Result X2: can a label-free margin normalization repair the monitor's task transfer?

Result X found the monitor transfers across juries and fails across benchmarks, and named the
suspect: per-model confidence margins on a 25-shot reasoning task are on a different scale from
5-shot knowledge questions. If that is the whole story, a normalization that uses only the target's
own unlabeled outputs should repair it. If it is not, the failure is a signal problem and no
label-free fix will do.

Normalization: each model's margins are mapped to their within-model empirical quantile on the set
being read (training jury on its benchmark; target jury on its benchmark). No label is used. The
monitor is fitted once on jury A / MMLU with normalized margins and never refitted. The four
Result X transfers are rerun with normalized margins and compared to Result X's unnormalized rows.
Everything else (juries, join rule, gold recovery, features, model, seed) is imported from the
Result X tool, which is not edited.
"""
import importlib.util
import pathlib

import numpy as np
import pandas as pd

spec = importlib.util.spec_from_file_location("rx", pathlib.Path(__file__).with_name("result_x_monitor_transfer.py"))
rx = importlib.util.module_from_spec(spec); spec.loader.exec_module(rx)


def quantile_normalize(mg):
    """Within-model empirical quantile of each margin, on this set only. Label-free."""
    return mg.rank(pct=True)


def main():
    print("loading juries...", flush=True)
    A_m = rx.jury_frame(rx.JURY_A, "mmlu")
    B_m = rx.jury_frame(rx.JURY_B, "mmlu")
    A_a = rx.jury_frame(rx.JURY_A, "arc")
    B_a = rx.jury_frame(rx.JURY_B, "arc")
    XA, yA = rx.features(A_m[0], quantile_normalize(A_m[1]), A_m[2])
    monitor = rx.fit(XA, yA)
    print("=" * 92)
    print("RESULT X2 - label-free margin normalization: does it repair task transfer?")
    print(f"jury A: {len(A_m[3])} models, {len(yA)} MMLU items; margins replaced by within-model quantiles on each set read")
    print("=" * 92)

    def run(label, frame, subset=None):
        ch, mg, gold, keep = frame
        if subset:
            cols = [m for m in keep if m in subset]
            ch, mg, keep = ch[cols], mg[cols], cols
        names = [m.split("__")[-1] for m in keep]
        if len(keep) < rx.MIN_JURY:
            print(f"\n  {label}\n    NOT RUN: jury has {len(keep)} models, below the minimum of {rx.MIN_JURY}")
            return
        X, y = rx.features(ch, quantile_normalize(mg), gold)
        p_mon = monitor.predict_proba(X)[:, 1]
        rx.report(f"{label}  [{len(keep)} models: {', '.join(names)}]", y, p_mon, 1.0 - X[:, 0], X[:, 0])
        rx.ceiling(X, y, label.split(":")[0])

    run("X2-1: jury B / MMLU, normalized  (Result X: monitor AUC 0.853, ECE 0.032)", B_m)
    run("X2-2: jury B / ARC-Challenge, normalized  (Result X: monitor AUC 0.610, ECE 0.213)", B_a)
    run("X2-3: jury A / ARC-Challenge, normalized  (Result X: monitor AUC 0.575, ECE 0.184)", A_a)
    run("X2-4: five of jury B / MMLU, normalized  (Result X: monitor AUC 0.852, ECE 0.023)", B_m, B_m[3][:5])

    print("\n" + "-" * 92)
    print("NON-CLAIMS: public leaderboard outputs, retained as proposed. The normalization uses only the")
    print("outputs of the set being read, never a label. Same juries, benchmarks, features, model and")
    print("seed as Result X, imported from its tool unchanged. Not a deployed product, not a safety")
    print("determination, not a driving result. No released 1.2 byte is involved.")


if __name__ == "__main__":
    main()
