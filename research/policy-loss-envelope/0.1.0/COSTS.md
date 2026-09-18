# Joint envelope costs and retained storage failure

Version `0.1.0`. Machine measurements do not establish human or full economic
cost. Exact phase boundaries and the pre-publication cutoff are in
[summary.json](summary.json).

| Phase | Outer process seconds |
| --- | ---: |
| Initial mathematical controls | 0.323092750 |
| All 13 controls and complete synthetic pipeline | 0.497786250 |
| Source/implementation/runtime freeze | 0.132081500 |
| Actual envelope analysis | 0.293926958 |
| Successful separate verification | 0.567518750 |

The actual analysis intersects 48,655 and 26,496 line constraints, retaining
all 519 source cells. Its internal timer is 0.155595416 seconds. Independent
verification takes 0.447963709 internal seconds and checks 52,938 endpoint
dominance obligations, in addition to its lower hull, source and partition
checks. These internal timers nest inside the outer processes.

The first verification invocation failed with `ENOSPC` before its phase
launcher could create the STARTED receipt. The verification child did not
run. The tool reported 0.414131541 seconds for that failed invocation; a
following result-view command also failed to create a shell temporary file
and reported 0.246422958 seconds. These tool durations have no retained
precise start/end intervals and are not added to a process wall-time union.
The absent child receipt is not represented as a successful verification.

Recovery losslessly archived 31,945,868 bytes of completed synthetic cached-
audit analysis/verification outputs into 1,158,469 bytes. Every archive member
was read back and its digest checked before the unpacked copy was removed.
Synthetic source inputs, actual scientific packets, frozen input paths and
other user files were untouched. The private archive/manifest restores exact
original relative paths without regeneration or network access. Recovery
takes 0.943629458 outer process seconds and 0.849778250 internal seconds.
Storage remained low afterward; no claim is made that the machine-wide
storage problem is solved. A fresh verification invocation then passed.

Publication, plotting, review, repository consistency checks and push are
retained afterward in the mission ledger. No images, model calls, downloads,
dependency installation or training are added. Earlier 230,321,747 response-
body bytes and 11.847570214 charged inference seconds remain mission costs.
The 51 penalty cells are not 51 independent decisions; no query, review or
economic saving is inferred from this mathematical calculation.
