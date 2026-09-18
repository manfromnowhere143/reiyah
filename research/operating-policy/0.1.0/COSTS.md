# Known operating-policy costs

Version `0.1.0`. These are retained local command measurements, not full
engineering, human review or economic costs.

| Process | Seconds |
| --- | ---: |
| First controls, retained failure | 0.260306875 |
| Corrected controls, 31 tests | 0.254730875 |
| Complete synthetic pipeline | 5.687896375 |
| Real score-packet qualification | 0.208333208 |
| Source/implementation freeze | 0.257534584 |
| Actual threshold analysis and native proof production | 56.621070416 |
| Complete independent verification | 55.775448542 |

The seven-phase public snapshot sums to 119.065320875 process seconds; the
union of retained command intervals is 119.069386959 wall seconds. Their
small difference reflects command-boundary bookkeeping. The first failed
controls used a macOS temporary-path alias to look up a canonical resolved
source binding. Resolving the root corrected the lookup without weakening
any byte or membership check. All first-failure diagnostics remain retained.

Analysis's internal timer is 55.982514417 seconds; verification's is
55.473676625. Across 7,407 distinct native worlds, compilation totals
25.140784217 seconds, proposal 0.446433765 and immediate checking 0.433703667.
The separate verifier's native checking is 0.466203775 seconds. These are
nested inside the outer processes and are not additional wall time.
Both checking paths use the same world operands; their timings do not claim
an equivalent-work speedup or an observation saving.

The [summary](summary.json) records exact phase boundaries and the snapshot
cutoff before publication. Publishing, both figure renders, default repository
checks, review and push are retained later in private phase/publication
records. The first figure and its helper remain retained before layout repair.
Interactive work, human seconds and complete economic cost remain unknown.

New image reads, model calls and downloaded asset bytes are zero. The session's
earlier 227,930,532 downloaded asset bytes and 11.847570214 charged inference
seconds remain inherited costs. The nominal pair grid, thresholds and cases
overlap and are not a count of independent customer decisions. Retrospective
threshold minima do not measure review savings or establish a deployment policy.
