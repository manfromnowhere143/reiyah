"""Human channel H2: the driver's gaze in the reaction window and at the conflict instant.

H1 measured the whole observed window. This anchors to the actual conflict. The eyeglance
sequence ends exactly at the reduced file's event_end for every event (verified, offset 0), so
event_end is the conflict climax and [event_start, event_end] is the few-second reaction window.

Measured per event:
  - off-road proportion during the reaction window [event_start, event_end] (glances clipped
    to the window), the tight analogue of H1's whole-window proportion;
  - the glance location at the climax (the glance covering event_end), the driver's gaze at the
    conflict instant, and whether it was on the forward roadway.

Reiyah discipline: No Video kept as unknown. Syncs are 1/10 s. Reduced columns: 1 webid,
3 event_start, 4 event_end, 5 severity, 6 subject_webid.
"""
from collections import defaultdict

EYE = "human-channel/data/eventEyeglance.txt"
RED = "human-channel/data/eventVideoReduced.txt"
ON = {"forward"}
UNKNOWN = {"no video"}


def load():
    glances = defaultdict(list)
    for line in open(EYE, encoding="latin-1"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 5:
            continue
        try:
            b, e = float(p[1]), float(p[2])
        except ValueError:
            continue
        glances[p[0].strip()].append((b, e, p[4].strip().lower()))
    ev = {}
    for line in open(RED, encoding="latin-1"):
        p = line.rstrip("\n").split("\t")
        if len(p) < 6:
            continue
        try:
            ev[p[0].strip()] = (float(p[2]), float(p[3]), p[4].strip(), p[5].strip())
        except ValueError:
            pass
    return glances, ev


def pct(x):
    return f"{100*x:.1f}%"


def main():
    glances, ev = load()
    # per event: reaction-window off-road proportion + climax glance
    recs = []
    for wid, gl in glances.items():
        if wid not in ev:
            continue
        es, ee, sev, subj = ev[wid]
        on_t = off_t = unk_t = 0.0
        climax_loc = None
        climax_end = -1
        for (b, e, loc) in gl:
            lo, hi = max(b, es), min(e, ee)   # clip to reaction window
            if hi > lo:
                d = hi - lo
                if loc in UNKNOWN:
                    unk_t += d
                elif loc in ON:
                    on_t += d
                else:
                    off_t += d
            if e >= climax_end:               # glance covering the climax (ends latest)
                climax_end = e
                climax_loc = loc
        obs = on_t + off_t
        if obs <= 0:
            continue
        recs.append((wid, sev, subj, off_t / obs, climax_loc))

    def block(sevfilter, label):
        rows = [r for r in recs if (sevfilter is None or r[1] == sevfilter)]
        n = len(rows)
        if not n:
            print(f"  {label}: none"); return
        props = sorted(r[3] for r in rows)
        mean = sum(props) / n
        climax_fwd = sum(1 for r in rows if r[4] in ON) / n
        climax_off = sum(1 for r in rows if r[4] is not None and r[4] not in ON and r[4] not in UNKNOWN) / n
        climax_unk = sum(1 for r in rows if r[4] in UNKNOWN) / n
        print(f"  {label}: n={n}")
        print(f"    reaction-window off-road proportion : mean {pct(mean)}, median {pct(props[n//2])}")
        print(f"    gaze AT the conflict instant  forward : {pct(climax_fwd)}   <- eyes on the road, still in it")
        print(f"                                  off-road : {pct(climax_off)}")
        print(f"                                  unknown  : {pct(climax_unk)}")

    print("=" * 88)
    print("HUMAN CHANNEL H2 - gaze in the reaction window and at the conflict instant")
    print("100-Car NDS; reaction window [event_start, event_end]; climax = event_end")
    print("=" * 88)
    print(f"\nevents: {len(recs)}")
    block(None, "all events")
    block("Crash", "crashes")
    block("Near-Crash", "near-crashes")
    print("\nNON-CLAIMS: 2003-2004 CC0 naturalistic data; descriptive, not causal, not a safety")
    print("determination; No Video kept as unknown; not driver-clustered here.")


if __name__ == "__main__":
    main()
