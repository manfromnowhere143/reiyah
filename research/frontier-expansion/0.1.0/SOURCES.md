# Primary-source review through 20 September 2026

Document ID: reiyah.frontier-expansion.source-review. Version 0.1.0.
This is a bounded review, not an exhaustive survey or proof of optimal strategy.
Exact private-response metadata and digests are in [sources.json](sources.json).
Publication dates below are source dates, distinct from retrieval on 20 September.
Company and paper results remain author-reported. No model benchmark is rerun.

| Source and version | What it changes for Reiyah |
| --- | --- |
| NVIDIA, [Alpamayo 2 Super announcement](https://nvidianews.nvidia.com/news/nvidia-alpamayo-2-super-robotaxis), 31 May 2026, page updated September 2026 | Reasoning, grounded meta-actions, policy training and simulation are becoming a combined development workflow. Reiyah should accept evidence from these systems through explicit contracts. Product announcements are not independent validation. |
| NVIDIA authors, [OmniDreams](https://arxiv.org/abs/2606.03159v2), v2, 23 July 2026 | Review simulation validity, policy ranking and time semantics separately from visual quality. Full HTML methods retained. |
| Mobileye, [Safety Methodology](https://www.mobileye.com/technology/safety-methodology/), undated live page | Separate perception, driving-policy constraints and their assumptions. Its redundancy argument does not authorize assuming independence in Reiyah. |
| Mobileye, [Hands-off driving goes mainstream](https://www.mobileye.com/blog/hands-off-driving-goes-mainstream-enabling-l2-at-scale/), 11 August 2026 | The stated relationship between gaze and external sensing reinforces a contextual human-channel research question. It does not establish that gaze identifies object-level belief or readiness. |
| Tesla, [Master Plan Part IV](https://www.tesla.com/master-plan-part-4), 1 September 2025 | The accessible primary search rendering describes physical AI at scale. This is strategic context, not a reproducible technical specification. Direct article and FSD-safety requests returned 403; those bodies are not qualified evidence. |
| SpaceX, [Starship to Orbit](https://www.spacex.com/updates/), 15 September 2026 | The public article describes staged mission continuation, monitored health and conservative abort criteria. Our inference: recoverability research needs explicit continuation conditions and observable fallback obligations. It supplies no driving-system validation. |
| SpaceX, [Flight 9 and Ship 36 Report](https://www.spacex.com/updates/), 15 August 2025 | The report distinguishes probable causes, reproduced failures, design corrections and additional qualification. Preserve that chain rather than treating test completion as success. |

OmniDreams sections 6, 7 and 9.4 describe action-conditioned video simulation
and policy comparison. The 501-scene simulator comparison uses 20-second rollouts,
replanning throttled to 533 ms, and incident counting conditional on staying
within four metres of the recorded trajectory. Our inference: ranking agreement
inside that envelope cannot establish unrestricted real-world validity. The
paper also notes higher compute requirements than reconstruction. Reiyah should
retain the conditioning, timing and excluded regimes whenever consuming such
results, and test whether a simulator changes the consequential decision.
We do not run or rank these models.

SpaceX's current site initially returned an application shell. Its referenced
public JavaScript identifies the unauthenticated
[article feed](https://content.spacex.com/api/spacex-website/updates).
The retained feed supplies article text and dates, including the September 15
update; no media was fetched. The obsolete hostname's DNS failure remains.
A planned orbital mission in that article is not recorded here as a completed
flight. Corporate claims about safety or qualification are attributed, not adopted.

## The direct research lead and established mathematics

Yu, Feng and Elbaum, [Drive the Thoughts](https://arxiv.org/abs/2608.29583v1),
v1, 30 August 2026, studies 150 Alpamayo 1.5 reasoning/trajectory pairs.
The paper separates reasoning grounding, prescribed-action safety and coherence
from trajectory consistency. Its selected reliable subset contains 100 pairs;
the best reported lane-aware monitor F1 is 0.75. This is a diversity-oriented,
single-policy/simulator sample, with mostly single final annotations and only
nine unsafe trajectories. It is not a naturalistic safety rate. The authors
identify missing agent-relative traces as a limitation for distance claims.
Our inference is to require those traces and preserve unknown answers. We do
not compare the present authored checker with their empirical F1 or use their
annotations as clearance truth.

The [released artifact](https://github.com/776styjsu/drive-the-thoughts/tree/8e01a85b1cdfeb581f0eaafba54ddc1a85c11065)
is pinned at 8e01a85b1cdfeb581f0eaafba54ddc1a85c11065. We inspected its complete
150-entry index and the first alphabetical scene's metadata/additional-info JSON,
not its images, videos or all scene sidecars. The inspected scene exposes 65 ego
poses; these files provide no explicit lead-actor trajectory suitable for this
contract. The [qualification record](qualification.json) retains two discrepancies:
all 150 index taxonomy-source tags say heuristic extraction while the paper
describes GPT-5.5 tagging; the pinned commit predates the paper submission.
Neither discrepancy is silently repaired. Corpus equivalence and underlying
NuRec rights remain unqualified for an empirical clearance comparison.

Deshmukh et al., [Robust Online Monitoring of Signal Temporal Logic](https://arxiv.org/abs/1506.08234v1),
v1, 26 June 2015, sections 2–4, already formalizes robustness intervals for
incomplete traces. The retained paper assumes constant interpolation; our
authored slice explicitly uses piecewise-linear interpolation or leaves it
unspecified. We implement one elementary predicate, not its complete monitoring
algorithm, and claim no novelty in incomplete-trace semantics.

Hegde and Katta, [GUARD](https://arxiv.org/abs/2608.04510v1), v1,
5 August 2026, is an abstract-qualified future comparator: it probes VLA
conditioning through KV-cache ablation. Its HTML endpoint returned 404.
Full methods and implementation are not reviewed here, and model-internal
experiments are outside this study. No reported performance is transferred.

## Qualification and unresolved access

Twenty-seven direct retrievals retained 23 HTTP-200 bodies and four failures:
two Tesla 403 responses, GUARD HTML 404 and the older SpaceX hostname failure.
A successful response can still be only an application shell or metadata.
The later SpaceX feed is a qualified public article source; Tesla search
rendering is explicitly weaker than retained article bytes. No protected
route was bypassed. Repository metadata, paper licenses, response digests and
access scope are recorded before use. [Distribution](DISTRIBUTION.md) keeps all
third-party payloads private. Abstract-only and inaccessible leads never become
methodological authority through repetition.
