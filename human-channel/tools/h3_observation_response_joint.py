"""Human channel H3: the first joint measurement, the human's two channels.

The camera-lidar work measured whether two automation channels fail together beyond
independence. This asks the same question of the human's own two channels on the same
encounter: observation (gaze at the conflict instant) and response (evasive action). It is
the within-agent joint, the honest one this dataset supports; the cross-agent human-automation
joint needs takeover data and is the next acquisition.

Channels, from the data:
  observation failure = gaze NOT forward at the conflict instant (H2's climax glance)
  response failure    = driver_reaction is 'No reaction' (the driver did nothing)

The coefficient is the same estimand as the sensor work:
  c = P(both fail) / [ P(obs fail) * P(resp fail) ]
c = 1 is independence; c > 1 means the two human channels fail together more than independent.

Reduced columns: 1 webid, 3 event_start, 4 event_end, 5 severity, 14 driver_reaction.
No Video and unknown reactions are excluded from the 2x2 and counted separately.
"""
from collections import defaultdict

EYE = "human-channel/data/eventEyeglance.txt"
RED = "human-channel/data/eventVideoReduced.txt"
ON = {"forward"}
UNKNOWN_GAZE = {"no video"}
NO_RESPONSE = {"no reaction"}
UNKNOWN_RESP = {"unknown if action was attempted", "no analyzed data", "other actions"}


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
        if len(p) < 14:
            continue
        try:
            float(p[3])
        except ValueError:
            continue
        ev[p[0].strip()] = (float(p[2]), float(p[3]), p[4].strip(), p[13].strip().lower())
    return glances, ev


def climax_gaze(gl):
    best_end, loc = -1, None
    for (b, e, l) in gl:
        if e >= best_end:
            best_end, loc = e, l
    return loc


def main():
    glances, ev = load()
    recs = []
    for wid, gl in glances.items():
        if wid not in ev:
            continue
        es, ee, sev, reaction = ev[wid]
        g = climax_gaze(gl)
        if g in UNKNOWN_GAZE or g is None:
            continue
        obs_fail = g not in ON                     # gaze not forward
        if reaction in UNKNOWN_RESP:
            continue
        resp_fail = reaction in NO_RESPONSE        # did nothing
        recs.append((wid, sev, obs_fail, resp_fail))

    def coeff(rows, label):
        n = len(rows)
        if not n:
            print(f"  {label}: none"); return
        a = sum(1 for r in rows if r[2] and r[3])       # both fail
        b = sum(1 for r in rows if r[2] and not r[3])   # obs fail only
        c = sum(1 for r in rows if not r[2] and r[3])   # resp fail only
        d = sum(1 for r in rows if not r[2] and not r[3])
        p_obs = (a + b) / n
        p_resp = (a + c) / n
        p_both = a / n
        exp = p_obs * p_resp
        coef = p_both / exp if exp > 0 else float("nan")
        looked_no_act = c / n                            # eyes forward yet no reaction
        print(f"  {label}: n={n}")
        print(f"    P(obs fail = gaze not forward)      : {100*p_obs:.1f}%")
        print(f"    P(resp fail = no reaction)          : {100*p_resp:.1f}%")
        print(f"    P(both fail)                        : {100*p_both:.1f}%")
        print(f"    expected if independent P_obs*P_resp: {100*exp:.1f}%")
        print(f"    coefficient c = observed/expected   : {coef:.2f}")
        print(f"    looked forward yet DID NOT react    : {100*looked_no_act:.1f}%  (n={c})")

    print("=" * 84)
    print("HUMAN CHANNEL H3 - joint failure of the human's observation and response channels")
    print("100-Car NDS; obs fail = gaze not forward at the conflict instant; resp fail = no reaction")
    print("=" * 84)
    print(f"\nevents in the 2x2 (known gaze and known reaction): {len(recs)}")
    coeff(recs, "all events")
    coeff([r for r in recs if r[1] == "Crash"], "crashes")
    coeff([r for r in recs if r[1] == "Near-Crash"], "near-crashes")
    print("\nNON-CLAIMS: within-agent joint (the human's two channels), not the cross-agent")
    print("human-automation joint, which needs takeover data. Descriptive, not driver-clustered,")
    print("2003-2004 CC0 data. c is illustrative on these counts, not an inferential test.")


if __name__ == "__main__":
    main()
