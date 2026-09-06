"""Human channel H7: intervals for the human-channel coefficients, clustered where the data allow.

H1 to H4 report point estimates. This puts intervals on them: an event-resampled bootstrap for
the 100-Car quantities (H2 gaze-forward-at-the-instant rate, H3 observation x response
coefficient and the looked-forward-yet-no-reaction cell) and a participant-clustered bootstrap
for the DCPT takeover contrast (H4 visual-manual minus no-task), since the DCPT trial ids carry
the participant and trials cluster within 40 people. The 100-Car public files carry no driver id,
so those intervals are event-resampled and are stated as not driver-clustered. Parsing and
definitions are imported from the H3 and H4 tools unchanged. B = 2000, seeded.
"""
import importlib.util
import pathlib

import numpy as np

here = pathlib.Path(__file__).parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, here / f"{name}.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


h3 = load("h3_observation_response_joint")
h4 = load("h4_dcpt_takeover")
B, SEED = 2000, 20260906


def coeff(obs, resp):
    p_obs, p_resp, p_both = obs.mean(), resp.mean(), (obs & resp).mean()
    return p_both / (p_obs * p_resp) if p_obs * p_resp > 0 else np.nan


def band(vals):
    v = np.array(vals, dtype=float); v = v[~np.isnan(v)]
    return np.percentile(v, [2.5, 97.5]) if len(v) else (np.nan, np.nan)


def main():
    rng = np.random.RandomState(SEED)
    glances, ev = h3.load()
    recs = []
    for wid, gl in glances.items():
        if wid not in ev:
            continue
        es, ee, sev, reaction = ev[wid]
        g = h3.climax_gaze(gl)
        if g in h3.UNKNOWN_GAZE or g is None:
            continue
        obs_fail = g not in h3.ON
        known_resp = reaction not in h3.UNKNOWN_RESP
        resp_fail = reaction in h3.NO_RESPONSE if known_resp else None
        recs.append((sev, obs_fail, known_resp, resp_fail))
    print("=" * 88)
    print("HUMAN CHANNEL H7 - intervals for the human-channel coefficients")
    print(f"100-Car: event-resampled bootstrap, not driver-clustered (no driver id in the public files);")
    print(f"DCPT: participant-clustered bootstrap; B = {B}, seed {SEED}")
    print("=" * 88)

    for label, sel in (("all events", lambda s: True), ("crashes", lambda s: s == "Crash"), ("near-crashes", lambda s: s == "Near-Crash")):
        rows = [r for r in recs if sel(r[0])]
        obs_all = np.array([r[1] for r in rows])
        fwd = 1 - obs_all
        known = [r for r in rows if r[2]]
        obs = np.array([r[1] for r in known]); resp = np.array([r[3] for r in known])
        looked_no_act = (~obs & resp)
        pt = {"gaze forward at the instant (H2)": fwd.mean(), "coefficient c (H3)": coeff(obs, resp),
              "looked forward yet no reaction (H3)": looked_no_act.mean()}
        bs = {k: [] for k in pt}
        n1, n2 = len(rows), len(known)
        for _ in range(B):
            i1 = rng.randint(0, n1, n1); bs["gaze forward at the instant (H2)"].append(fwd[i1].mean())
            i2 = rng.randint(0, n2, n2)
            bs["coefficient c (H3)"].append(coeff(obs[i2], resp[i2]))
            bs["looked forward yet no reaction (H3)"].append(looked_no_act[i2].mean())
        print(f"\n  {label}: {n1} events with known gaze, {n2} with known gaze and reaction")
        print(f"    {'quantity':<40}{'point':>9}{'2.5%':>9}{'97.5%':>9}")
        for k, v in pt.items():
            lo, hi = band(bs[k])
            print(f"    {k:<40}{v:>9.3f}{lo:>9.3f}{hi:>9.3f}")

    trials = h4.load_trials()
    persons = sorted(set(t[1] for t in trials))
    by_p = {p: [t for t in trials if t[1] == p] for p in persons}
    def contrast(tr):
        vm = [t[2] for t in tr if t[0] in h4.VISUAL_MANUAL]; nt = [t[2] for t in tr if t[0] == 1]
        co = [t[2] for t in tr if t[0] in h4.COGNITIVE_ONLY]
        return (np.mean(vm) - np.mean(nt), np.mean(co) - np.mean(nt), np.mean(vm) / np.mean(nt) - 1)
    pt = contrast(trials)
    bs = [[], [], []]
    for _ in range(B):
        sample = [t for p in rng.choice(persons, len(persons), replace=True) for t in by_p[p]]
        c = contrast(sample)
        for k in range(3):
            bs[k].append(c[k])
    print(f"\n  DCPT takeover (H4): {len(trials)} trials, {len(persons)} participants, participant-clustered")
    print(f"    {'quantity':<40}{'point':>9}{'2.5%':>9}{'97.5%':>9}")
    for k, name in enumerate(("visual-manual minus no task, s", "cognitive-only minus no task, s", "visual-manual relative to no task")):
        lo, hi = band(bs[k])
        print(f"    {name:<40}{pt[k]:>9.3f}{lo:>9.3f}{hi:>9.3f}")

    print("\n" + "-" * 88)
    print("NON-CLAIMS: descriptive intervals on public CC0 (100-Car) and CC BY 4.0 (DCPT) data,")
    print("retained as proposed. The 100-Car intervals are event-resampled and understate")
    print("uncertainty if events cluster within drivers; the DCPT interval is participant-clustered.")
    print("H3's coefficient includes a causal component and is not pure latent dependence. Not a")
    print("causal claim, not a safety determination, not a claim about any product. No released 1.2")
    print("byte is involved.")


if __name__ == "__main__":
    main()
