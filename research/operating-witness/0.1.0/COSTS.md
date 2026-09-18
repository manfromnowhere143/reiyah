# Retained follow-up costs

Version `0.1.0`. Process durations measure local machine work, not reviewer
time, total session effort or full economic cost.

| Phase | Outer process seconds |
| --- | ---: |
| Eight controls / 56 synthetic case compositions | 0.359801083 |
| Source and implementation freeze | 2.476642250 |
| 98 new searches / 87 inherited exact states | 23.721293708 |
| Separate proof and complete case verification | 5.598980667 |

Internal analysis and verification timers are 23.094481667 and 5.298593750
seconds, respectively. Native checking consumes 0.012444962 seconds inside
the latter. Each state retains its search and endpoint proof timers privately;
these are nested, not additional outer wall time. All phase boundaries are
in [summary.json](summary.json). The original 7,407 proof checks are inherited
through exact bindings, not falsely charged as newly executed checks.

The publication helper takes 0.719929084 process seconds after this snapshot.
Subsequent consistency checks, review, Git integration and publisher readback
are retained in the mission ledger with their later cutoff. Writing/reviewing
code and historical inputs remain incompletely timed. No inference, image
reads, downloads, paid compute or training occur in this follow-up. Human
adjudication, full economics and savings remain unknown.
