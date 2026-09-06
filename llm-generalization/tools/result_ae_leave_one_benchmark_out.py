"""Result AE: leave-one-benchmark-out calibration of the monitor.

Result X showed the monitor transfers across juries on one task and fails across tasks; X2 showed
no label-free rescaling repairs that. The remaining question for deployment is whether calibrating
on DIVERSE tasks buys transfer to an unseen task. This fits the monitor on two benchmarks' items
(jury A) and reads the third, for each of the three held-out choices, and compares with the
single-benchmark transfer (fit on MMLU alone, Result X) and the in-domain ceiling on the held-out
benchmark. It also reads jury B on the held-out benchmark, so both jury and task are unseen.

Two things are stated in advance. First, the monitor's features include the agreement fraction and
vote entropy, which depend on the number of answer choices; MMLU and ARC have four choices,
HellaSwag four. Second, benchmarks are joined per model as in Result X; ARC drops Falcon and two
jury B models by the non-joining rule, so the jury size differs by benchmark, and the features are
size-normalized where they can be (agreement fraction, entropy) and not where they cannot (number
of distinct answers, capped by jury size). Everything else is imported from the Result X tool.
"""
import importlib.util
import pathlib

import numpy as np

spec = importlib.util.spec_from_file_location("rx", pathlib.Path(__file__).with_name("result_x_monitor_transfer.py"))
rx = importlib.util.module_from_spec(spec); spec.loader.exec_module(rx)
rx.TASKS["hellaswag"] = "|hellaswag|"
TASKS = ["mmlu", "arc", "hellaswag"]


def main():
    print("loading juries on three benchmarks...", flush=True)
    A = {t: rx.jury_frame(rx.JURY_A, t) for t in TASKS}
    Bj = {t: rx.jury_frame(rx.JURY_B, t) for t in TASKS}
    XA = {t: rx.features(*A[t][:3]) for t in TASKS}
    XB = {t: rx.features(*Bj[t][:3]) for t in TASKS}
    print("=" * 92)
    print("RESULT AE - leave-one-benchmark-out: fit the monitor on two benchmarks, read the third")
    for t in TASKS:
        print(f"  jury A on {t}: {len(A[t][3])} models, {len(XA[t][1])} items, wrong {100*XA[t][1].mean():.1f}%;"
              f"  jury B on {t}: {len(Bj[t][3])} models, {len(XB[t][1])} items")
    print("=" * 92)
    mono = rx.fit(*XA["mmlu"])
    for held in TASKS:
        train = [t for t in TASKS if t != held]
        Xtr = np.vstack([XA[t][0] for t in train]); ytr = np.concatenate([XA[t][1] for t in train])
        multi = rx.fit(Xtr, ytr)
        for jury, frames, feats in (("jury A", A, XA), ("jury B", Bj, XB)):
            X, y = feats[held]
            if len(frames[held][3]) < rx.MIN_JURY:
                print(f"\n  held-out {held}, {jury}: NOT RUN, jury below minimum"); continue
            label = f"held-out {held}, {jury} ({len(frames[held][3])} models), fitted on {' + '.join(train)}"
            p_multi = multi.predict_proba(X)[:, 1]
            rx.report(f"AE {label}", y, p_multi, 1.0 - X[:, 0], X[:, 0])
            if jury == "jury A" or held != "mmlu":
                p_mono = mono.predict_proba(X)[:, 1]
                from sklearn.metrics import roc_auc_score, brier_score_loss
                print(f"    single-benchmark reference (fitted on mmlu only): AUC {roc_auc_score(y, p_mono):.3f}  "
                      f"Brier {brier_score_loss(y, p_mono):.3f}  ECE {rx.ece(y, p_mono):.3f}")
            rx.ceiling(X, y, f"{held}/{jury}")
    print("\n" + "-" * 92)
    print("NON-CLAIMS: public leaderboard outputs, retained as proposed. Three benchmarks, two juries;")
    print("the held-out MMLU / jury A row is not an out-of-sample test for the single-benchmark")
    print("reference and is marked so by omission. Not a deployed product, not a safety determination,")
    print("not a driving result. No released 1.2 byte is involved.")


if __name__ == "__main__":
    main()
