# Initial compact motion diagnostic, retained failure

Packet version: `0.1.0`. Status: failed actual audit, 20 September 2026.

The first complete audit rejected one legitimate integer-valued MATLAB heading
cell because its initial decoder allowed only floats. No result JSON was emitted
and no actual decision comparison ran. Twenty diagnostic pre-controls and seven
decision pre-controls passed before that failure; they did not cover the mixed
numeric cell type encountered in the source.

All frozen files and both freezes here remain unchanged. The explicit
[correction](../0.1.1/CORRECTION.md) and [current results](../0.1.1/README.md)
are in packet 0.1.1. The original source selections are preserved. This failed
run is included in cumulative costs, never counted as a passing actual execution.
