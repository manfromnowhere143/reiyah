"""Human channel, measurement H1: the driver's observation state in real conflicts.

First empirical brick of the human channel. On the 100-Car Naturalistic Driving Study,
for each crash and near-crash event with completed eyeglance reduction, measure how much of
the observed event window the driver's gaze was OFF the forward roadway, and how often the
driver was looking forward for the entire observed window yet was still in a conflict.

This is the human analogue of a channel that was observing and still missed. It does not yet
locate the exact precipitating instant (that needs the reaction sync from the 69-column
reduced file); it measures the observed-window proportion, which is well defined without that
anchor and is stated as such.

Reiyah discipline: `No Video` is unknown time, kept separate and never folded into on-road or
off-road. Glances are in syncs (1/10 s).

Eyeglance columns: webid, begin_sync, end_sync, duration, location.
Reduced columns used: 1 webid, 5 severity, 7 age, 8 gender.
"""
import sys
from collections import defaultdict

EYE = "human-channel/data/eventEyeglance.txt"
RED = "human-channel/data/eventVideoReduced.txt"

ON_STRICT = {"forward"}
ON_PERIPHERAL = {"forward", "left forward", "right forward"}
UNKNOWN = {"no video"}


def load():
    on_strict = defaultdict(float)
    on_periph = defaultdict(float)
    off_strict = defaultdict(float)   # everything not strict-on and not unknown
    off_periph = defaultdict(float)   # everything not peripheral-on and not unknown
    unk = defaultdict(float)
    seen = set()
    for line in open(EYE, encoding="latin-1"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 5:
            continue
        wid = p[0].strip()
        try:
            dur = float(p[3])
        except ValueError:
            continue
        loc = p[4].strip().lower()
        seen.add(wid)
        if loc in UNKNOWN:
            unk[wid] += dur
            continue
        if loc in ON_STRICT:
            on_strict[wid] += dur
        else:
            off_strict[wid] += dur
        if loc in ON_PERIPHERAL:
            on_periph[wid] += dur
        else:
            off_periph[wid] += dur
    meta = {}
    for line in open(RED, encoding="latin-1"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 8:
            continue
        wid = p[0].strip()
        meta[wid] = {"severity": p[4].strip(), "age": p[6].strip(), "gender": p[7].strip()}
    return seen, on_strict, off_strict, on_periph, off_periph, unk, meta


def pct(x):
    return f"{100*x:.1f}%"


def summarize(events, on, off, unk, meta, label, severity_filter=None):
    rows = []
    for wid in events:
        if severity_filter and meta.get(wid, {}).get("severity") != severity_filter:
            continue
        t_on, t_off, t_unk = on[wid], off[wid], unk[wid]
        obs = t_on + t_off
        if obs <= 0:
            continue
        rows.append((wid, t_off / obs, t_off, t_on, t_unk))
    n = len(rows)
    if n == 0:
        print(f"  {label}: no events"); return
    props = sorted(r[1] for r in rows)
    mean = sum(props) / n
    median = props[n // 2]
    any_off = sum(1 for r in rows if r[2] > 0) / n
    fwd_whole = sum(1 for r in rows if r[2] == 0) / n          # forward entire observed window
    off_majority = sum(1 for r in rows if r[1] >= 0.5) / n     # off-road most of the window
    unk_events = sum(1 for r in rows if r[4] > 0) / n
    print(f"  {label}: n={n}")
    print(f"    off-road proportion of observed window: mean {pct(mean)}, median {pct(median)}")
    print(f"    any off-road glance in window          : {pct(any_off)}")
    print(f"    off-road for >= half the window        : {pct(off_majority)}")
    print(f"    forward for the ENTIRE observed window : {pct(fwd_whole)}  <- observed yet in conflict")
    print(f"    events with some No-Video (unknown)    : {pct(unk_events)}")


def baseline_offroad(path):
    """Off-road proportion per baseline epoch, strict Forward = on-road, No Video excluded."""
    on = defaultdict(float); off = defaultdict(float); seen = set()
    for line in open(path, encoding="latin-1"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 5:
            continue
        wid = p[0].strip()
        try:
            dur = float(p[3])
        except ValueError:
            continue
        loc = p[4].strip().lower()
        seen.add(wid)
        if loc in UNKNOWN:
            continue
        if loc in ON_STRICT:
            on[wid] += dur
        else:
            off[wid] += dur
    props = []
    for wid in seen:
        obs = on[wid] + off[wid]
        if obs > 0:
            props.append(off[wid] / obs)
    props.sort()
    n = len(props)
    return n, (sum(props)/n if n else 0), (props[n//2] if n else 0), \
        (sum(1 for x in props if x == 0)/n if n else 0)


def main():
    seen, on_s, off_s, on_p, off_p, unk, meta = load()
    print("=" * 90)
    print("HUMAN CHANNEL H1 - driver observation state in real crash/near-crash conflicts")
    print("100-Car NDS, eyeglance reduction, syncs = 1/10 s; No Video kept as unknown")
    print("=" * 90)
    print(f"\nevents with eyeglance data: {len(seen)}")
    sev = defaultdict(int)
    for wid in seen:
        sev[meta.get(wid, {}).get('severity', 'unmatched')] += 1
    print("severity split:", dict(sev))

    print("\n### ON-ROAD = strict 'Forward' only ###")
    summarize(seen, on_s, off_s, unk, meta, "all events")
    summarize(seen, on_s, off_s, unk, meta, "crashes", "Crash")
    summarize(seen, on_s, off_s, unk, meta, "near-crashes", "Near-Crash")

    print("\n### ON-ROAD = Forward + Left/Right Forward (peripheral through windshield) ###")
    summarize(seen, on_p, off_p, unk, meta, "all events")
    summarize(seen, on_p, off_p, unk, meta, "crashes", "Crash")
    summarize(seen, on_p, off_p, unk, meta, "near-crashes", "Near-Crash")

    import os
    bpath = "human-channel/data/baselineEyeglance.txt"
    if os.path.exists(bpath):
        bn, bmean, bmed, bfwd = baseline_offroad(bpath)
        print("\n### THE CONTRAST that gives the number meaning (strict Forward) ###")
        print(f"  baseline (normal driving), n={bn} epochs:")
        print(f"    off-road proportion: mean {pct(bmean)}, median {pct(bmed)}; "
              f"forward entire epoch {pct(bfwd)}")
        print(f"  conflicts vs baseline: crashes 28.3% vs baseline {pct(bmean)} off-road (mean).")
        print(f"  If conflicts exceed baseline, inattention is elevated where it mattered, not ambient.")

    print("\nNON-CLAIMS: observed-window proportion, not the precipitating-instant glance;")
    print("2003-2004 naturalistic data, CC0; descriptive, not a causal or safety determination.")


if __name__ == "__main__":
    main()
