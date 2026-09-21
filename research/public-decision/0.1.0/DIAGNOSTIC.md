# Missing-result diagnostic

Document ID: reiyah.public-decision.missing-result-diagnostic. Version:0.1.0.
Post-structure development follow-up. The original QUESTION remains BLOCKED:
Base218unique records, Tiny215, union218, shared215, no conflicting shared
scenario/town/weather labels. No driving-score values have been deliberately
inspected or computed here; publisher aggregate figures were already exposed.

Keep the original complete-group decision blocked. Do not replace it with a
claim that all44groups are non-regressing. Perform one separate nominal question:
conditional on both artifacts belonging to the SAME intended220-route population,
on their recorded scores being the intended protocol outcomes, and on every
unrecorded outcome being in[0,100], is Base's complete-population mean score
strictly greater for EVERY possible completion?

This conditional premise is not proved by the available route manifest or execution
provenance. The full original XML/model/runtime binding remains unresolved.
No distribution, independence, confidence or real-world safety claim is added.
The publisher explicitly uses220as divisor, assigning missing contributions zero.
That declared scoring convention is different from an observed zero score.
Keep its deterministic score reproduction distinct from the unknown-outcome question.

Let B,T be exact sums of the delivered Base/Tiny scores, counts b,t,N=220.
The conventional complete-population mean-difference interval is
[(B-T-100*(N-t))/N, (B-T+100*(N-b))/N].
Strictly positive lower endpoint supports this conditional aggregate comparison;
nonpositive upper endpoint excludes it; otherwise unresolved. Construct two
hypothetical completions attaining endpoints. They are not imputed measurements.

Reuse Reiyah's existing validated finite-population primitive with at most4units:
observed Base mean transformed as2s/100-1, weight b/(2N);
observed Tiny mean transformed as1-2s/100, weight t/(2N);
unrecorded Base block with[-1,1], status missing, weight(N-b)/(2N);
unrecorded Tiny block with[-1,1], status missing, weight(N-t)/(2N).
Omit zero-weight blocks. The weighted interval is the score difference divided
by100. The additive constants cancel because each full arm has Nmembers.
Call existing validate() and logical() only. This preserves the six-unit cap;
no statistical sampler, new theorem or runtime adapter is introduced.

Conventional arm independently parses decimal JSON, scales to integers and
computes sums/bounds. Native arm parses Fractions and uses the existing methods.
Both validate unique ids,count<=220,finite scores[0,100],completed/failed recorded
statuses,infraction lists and shared metadata. If union>N or shared metadata
conflicts, diagnostic blocks. Retain all observed failures; no filtering.

Freeze implementation and source SHA256before numerical execution. Fixed order:
conventional then native, one run each. Checker reconstructs exact sums from
source decimal strings, endpoint completions, the4unit binding, and actual
saved-result mutations. Authored controls cover missing-vs-zero,duplicates,
out-of-range/nonfinite scores,metadata conflicts,unknown/started status,
strictzero boundary,ties and reversed winners. Separate code is same-author work.

No additional source acquisition or arbitrary scenario subset. No source/result
body or route-level derivative published. Same source/time/storage limits and
all1433reserved-image closure remain. Original blocked result and this
conditional narrower diagnostic must both appear in the report. Parity or
higher cost provides no competitive-value evidence and justifies no expansion.
