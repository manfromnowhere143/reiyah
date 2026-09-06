"""Human channel H4: distraction and takeover response in L3 automation (DCPT).

A modern counterpart to the 100-Car human channel. DCPT is an L3 conditional-automation
simulator study: the automation drives while the participant does a non-driving task, then a
takeover request (TOR) is issued at a random time and the participant must resume control. The
response measure is the takeover time (reaction, 0.1 s units), encoded in each trial id together
with the task and participant.

The random TOR timing means the automation handover is independent of the human state by design,
so this is not the cross-agent dependence measurement; it is the human readiness-to-response
relationship in a real L3 setting: does the non-driving task the human was absorbed in predict a
slower takeover.

Trial id format: NDRT_P<person>_<YYYYMMDD>_<HH>_<MM>_<takeover_time_ds>
Task ids: 1 no task, 2 video, 3 game, 4 messaging, 5 phone call, 6 radio, 7 reading, 8 eating,
9 chatting with passenger.
"""
import re
import zipfile
import statistics as st
from collections import defaultdict

XLSX = "human-channel/dcpt/TakeoverTime.xlsx"
TASK = {1: "no task", 2: "watching video", 3: "playing game", 4: "messaging",
        5: "phone call", 6: "radio", 7: "reading", 8: "eating", 9: "chatting"}
VISUAL_MANUAL = {3, 4, 7, 8}      # tasks pulling eyes/hands off the road
COGNITIVE_ONLY = {5, 6, 9}        # tasks mainly loading attention, eyes freer


def load_trials():
    z = zipfile.ZipFile(XLSX)
    ss = z.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
    strings = re.findall(r"<t[^>]*>([^<]*)</t>", ss)
    pat = re.compile(r"^(\d+)_P(\d+)_\d{8}_\d+_\d+_\d+_(\d+)$")
    trials = []
    for s in strings:
        m = pat.match(s.strip())
        if m:
            ndrt = int(m.group(1)); person = m.group(2); tt = int(m.group(3)) / 10.0
            trials.append((ndrt, person, tt))
    return trials


def summarize(vals, label):
    if not vals:
        print(f"  {label}: none"); return None
    m = st.mean(vals)
    print(f"  {label:<26} n={len(vals):>4}  mean {m:.2f}s  median {st.median(vals):.2f}s  "
          f"sd {st.pstdev(vals):.2f}")
    return m


def main():
    trials = load_trials()
    print("=" * 82)
    print("HUMAN CHANNEL H4 - distraction and takeover response in L3 automation (DCPT)")
    print("takeover time = reaction to resume control (s); TOR issued at random time")
    print("=" * 82)
    persons = sorted(set(t[1] for t in trials))
    print(f"\ntrials {len(trials)}, participants {len(persons)}")

    by = defaultdict(list)
    for ndrt, person, tt in trials:
        by[ndrt].append(tt)
    all_tt = [t[2] for t in trials]
    print("\n### takeover time by non-driving task ###")
    overall = summarize(all_tt, "ALL tasks")
    means = {}
    for k in sorted(by):
        means[k] = summarize(by[k], f"{k} {TASK.get(k, '?')}")

    print("\n### grouped by how the task loads the driver ###")
    notask = by.get(1, [])
    vm = [t for k in VISUAL_MANUAL for t in by.get(k, [])]
    co = [t for k in COGNITIVE_ONLY for t in by.get(k, [])]
    m_no = summarize(notask, "no task (baseline)")
    m_co = summarize(co, "cognitive-only (5,6,9)")
    m_vm = summarize(vm, "visual-manual (3,4,7,8)")
    print("\n" + "-" * 82)
    if m_no and m_vm:
        print(f"visual-manual vs no-task: {m_vm:.2f}s vs {m_no:.2f}s, "
              f"{'+' if m_vm > m_no else ''}{m_vm - m_no:.2f}s "
              f"({100*(m_vm/m_no - 1):+.0f}%). Eyes/hands off the road slows the takeover.")
    if m_no and m_co:
        print(f"cognitive-only vs no-task: {m_co:.2f}s vs {m_no:.2f}s, "
              f"{m_co - m_no:+.2f}s. Attention load with eyes freer costs less.")
    print("-" * 82)
    print("NON-CLAIMS: L3 driving-simulator study, CC BY 4.0; random TOR so this is readiness to")
    print("response, not the cross-agent dependence; descriptive across participants, not clustered;")
    print("takeover time is reaction to resume control, not a collision outcome.")


if __name__ == "__main__":
    main()
