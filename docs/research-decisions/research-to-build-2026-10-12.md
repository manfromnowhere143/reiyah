# Research that changes an engineering decision

Document ID: `reiyah.research-to-build`. Version: `0.1.0`.
12 October 2026. Exploratory source review and bounded implementation decision.

**Use existing retrieval and agent capabilities, with a small deterministic
intake that binds evidence to a specific Reiyah decision.** The useful output is
a justified choice and a test that can change it. More papers, longer reports
and more agents are diagnostic activity, not demonstrated progress.

The [source ledger](../../evidence/research-loop-2026-10-12.json) records exact
versions, private custody and limitations. The
[intake helper](../../tools/research_intake/README.md) checks local records and
source bindings; the [first pilot](../../research/decision-research/0.1.0/README.md)
applies that boundary. Neither constitutes an autonomous research engine or a
scientific acceptance mechanism. This recommendation is our engineering
inference from the reviewed methods, not an experimentally established optimum.

## What to reuse

| System and exact inspected release | Useful capability | Boundary and decision |
| --- | --- | --- |
| [PaperQA2 `v2026.08.12`](https://github.com/Future-House/paper-qa/releases/tag/v2026.08.12), commit `57e89f7`; PyPI `2026.8.12`, released 12 August 2026 | Local full-text indexing; configurable sparse/dense retrieval; contextual summaries and relevance scores; Python `Docs`, `ask`/`agent_query` and CLI interfaces. | A plausible optional adapter for a frozen local corpus. The [original methods, 2409.13740v2, 26 September 2024](https://arxiv.org/html/2409.13740v2), distinguish the public package from the study's hosted search and citation-traversal infrastructure. Package release freshness does not renew those evaluations. |
| [OpenScholar, Nature, 4 February 2026](https://www.nature.com/articles/s41586-025-10072-4); [code `0e9b8fb`](https://github.com/AkariAsai/OpenScholar/tree/0e9b8fb912273d3dae39e593da86e4f6d3bf8de1), 13 August 2025 | Dense retrieval plus keyword/web candidates, scientific reranking, bounded feedback and further retrieval. | Reuse the separation of retrieval, gap identification and revision. Its evaluation datastore and tasks predate publication; generator-driven citation insertion is not independent verification. Rebuilding the 236-million-passage datastore is unjustified here. |
| [ScholarQA `a962328`](https://github.com/allenai/ai2-scholarqa-lib/tree/a96232870bdb0bd763f0131320e8377c6deb575e), 19 March 2026 | Snippet/keyword retrieval, reranking, quote extraction, outline, section synthesis and cost/event traces; replaceable library components. | Reuse the workflow before adopting the web stack. [Quote mapping](https://github.com/allenai/ai2-scholarqa-lib/blob/a96232870bdb0bd763f0131320e8377c6deb575e/api/scholarqa/scholar_qa.py#L230) includes alphabet-only and approximate matching; source linkage alone does not prove exact wording or numeric entailment. Pin actual code/configuration rather than infer defaults from older README examples. |
| [Asta PaperFinder `0623cce`](https://github.com/allenai/asta-paper-finder/tree/0623cce6ff61b0a1a637c78d352c4f4d431d0364), 17 March 2026 | Structured paper-seeking queries, relevance judgments and metadata constraints; documented `/api/2/rounds`. | Its README explicitly describes an unmaintained single-turn snapshot that differs from live Asta's indices and configuration. Learn from its decomposition; do not assume production equivalence or maintenance. |
| [AstaBrief, 2 October 2026](https://allenai.org/blog/astabrief); [8B model `6a34f54`](https://huggingface.co/allenai/AstaBrief_8B/tree/6a34f54dcd7887b790a570249b4a2a2fe81c6694) | Generates a cited report in one pass from already retrieved excerpts, reducing synthesis stages. | A future high-volume writing option, not a replacement for discovery. Authors say most evaluation occurred in 2025 and was not repeated against today's frontier. Their human study has 14 questions and three researchers; DR-Tulu wins overall preference. Citation support can still overstate a study's scope. |
| [Odeya `5311ff5`](https://github.com/manfromnowhere143/odeya/blob/5311ff5dfa9d87725cce36ffad1d3ad61eb5eae2/README.md), published state 1 September 2026 | Architecture for question, contract, evidence, verification and bounded claim. | Its published README explicitly disclaims executable research runtime. Reuse inspected design ideas where appropriate; no callable literature engine was identified. Odeya's architecture and authority do not become Reiyah runtime or acceptance. |

The inspected PaperQA, OpenScholar, ScholarQA and PaperFinder code declares
Apache-2.0; model, service and source-document rights remain separate. No package
was installed or inference performed in this comparison.

## Evaluate the whole path

[SAGE, 2602.05975v2, 6 February 2026](https://arxiv.org/html/2602.05975v2),
shows that retrieval quality depends on the agent's query behavior: BM25 beats
two tested dense retrievers on its short-form tasks, with closer open-ended
results. This supports retaining a cheap lexical baseline, not rejecting modern
embeddings generally. [AutoResearchBench, 2604.25256v1, 28 April](https://arxiv.org/html/2604.25256v1),
separates constrained discovery, set completeness and over-inclusion. Its fixed
corpus cannot establish absence from the whole literature.

Retrieval success can disappear during synthesis. In
[MetaSyn, 2606.17041v6, 26 July](https://arxiv.org/html/2606.17041v6),
one-pass GPT-5.4 RAG retrieves 91.7% of reference articles but retains 48.4%
in the final inclusion set on 86 held-out reviews. These are author-reported
results against PubMed-linked review lists, not a measure of scientific truth
or human-work savings. Track exposed, read, eligible, used and omitted sources
separately, preserving reasons and denominators.

[INSPIRE, 2609.33233v1, 27 September](https://arxiv.org/html/2609.33233v1),
is especially relevant to research before a solution: redacted research briefs,
a prior-literature cutoff, common search budgets and separate exposure,
selection and ranking traces. Its automatically graded citation lineage can
miss useful uncited or older alternatives. Borrow its experimental controls,
not its target as Reiyah's utility.

[Scaling Agent Systems, 2512.08296v3, 8 April](https://arxiv.org/html/2512.08296v3),
and [The Illusion of Multi-Agent Advantage, 2606.13003v2, 13 June](https://arxiv.org/html/2606.13003v2),
both make task structure and comparison budgets consequential. Neither supports
universal swarm superiority. Begin with a strong single-agent workflow and one
accountable synthesis owner. Add parallel branches for separable evidence
questions only when their measured benefit exceeds coordination and review cost.

## The bounded function

`Engineering question → bounded search → retained sources → claim/applicability review → decision → smallest resolving test`

The agent handles query reformulation, method reading and interpretation. The
offline helper handles explicit records, byte identities and evidence-span
bindings. It diagnoses the structure of supplied assessments; it does not infer
method compatibility or verify their scientific truth. A matching span proves
which text was cited, not that it supports a conclusion. Human or separately
qualified review must still check assumptions, numbers, comparators and transfer.

For Reiyah, keep two decisions distinct. **Metric qualification** asks what a
score and its support fields actually measure. **Observation qualification**
asks which actual review responses justify shrinking the admissible reference
states. The WOD score interpretation does not supply reliable reviewer histories;
fixed-rank AUGRC does not automatically transfer to a nonlinear trajectory score.
Search should name the missing observation or method that would change these
decisions. Closed, unchanged leads remain closed.

A useful intake records project/commit, alternatives, consequence, source dates,
budget, stopping rule and falsifier. Discovery combines literal terminology and
semantic candidates, with citation expansion when a named gap warrants it.
Retain full methods and exact source versions before consequential use. Preserve
abstract-only access, failed retrieval, contradictory evidence and uncertainty.
Conclude adopt, test, defer or reject, with the smallest reversible next action.
Source corrections should identify dependent claims for renewed review.

Acquisition adapters must respect provider terms and separate metadata rights
from full-text rights. The inspected [arXiv API rules](https://info.arxiv.org/help/api/tou.html)
allow one legacy API connection at a time, with at least three seconds between
requests across machines. Current [OpenAlex access](https://help.openalex.org/access/querying)
and [full-text documentation](https://help.openalex.org/access/fulltext)
describe key-based, metered access; metadata availability does not grant rights
to redistribute papers. No paid service or new acquisition adapter was activated.

Portability means a common record interface with project-specific adapters for
identity, permissions, evidence rules and tests. It does not mean pooling
scientific authority or silently activating a cross-project service. Add an
adapter only when an actual second use justifies it.

## Conditions for a useful pilot

The present pilot binds existing authored Reiyah records to four development
controls: compatible binary AUGRC is `ready_for_review`; direct transfer to the
geometric WOD score is `incompatible`; missing actual observation qualification
is `needs_evidence`; unchanged reinspection of the closed WOD lead is
`closed_no_new_basis`. These exercise declared assessment and intake rules.
They are neither fresh scientific findings nor evidence of utility, and
`ready_for_review` is not acceptance.

A utility comparison needs fresh held-out engineering decisions after freezing the workflow, source policy,
acceptance rubric, failure rules and minimum useful effect. Compare with a
competent analyst using the same initial evidence, access and corrected tools.
Historical exposed studies cannot become fresh efficacy cases.

Measure justified, incorrect and unresolved decisions separately. Count active
review and correction time, elapsed time, setup/indexing, coordination, retrieval,
tokens and provider charges; leave unobservable resources unknown. Preserve
failures and use decisions, not citations or agent messages, as statistical units.
First meet the declared correctness requirement, then assess complete-work
reduction with paired uncertainty. Insufficient precision means inconclusive.

No current-model superiority, complete-work advantage, physical validity or
Gate A acceptance follows from this source review or deterministic intake.
The opportunity is concrete: make new research change the next engineering
choice through an inspectable chain, then measure whether that chain helps.
