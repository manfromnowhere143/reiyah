# Sources and the implemented comparison

Document ID: `reiyah.sequential-audit.sources-note`.
Version: `0.1.0`.
Lifecycle status: `exploratory`.
Review date: 19 September 2026.

The exact source versions, authors, dates, retained response-body and extracted-text
digests and access/redistribution records are in sources.json. The source bytes
remain in the closed roadmap-audit packet and were rechecked before use. No
third-party source body or code is copied into this public packet.

- [Shekhar et al., UAI 2023](https://proceedings.mlr.press/v216/shekhar23a.html),
  retained arXiv 2305.06884v1: read the weighted importance-corrected betting
  construction, sampling strategies, logical bounds and control-variate sections.
  This is the principal method family. The present code uses a separately
  specified fixed stake, one-sided tests and residual endpoint bounds; it does
  not reproduce the paper's optimized ApproxKelly implementation or claim a
  comparison against that full implementation.
- [Waudby-Smith and Ramdas, NeurIPS 2020](https://arxiv.org/abs/2006.04347v4),
  retained v4 dated 8 January 2021: revisit the sampling-without-replacement
  setup and time-uniform guarantee. Random sampling from fixed populations
  does not require the member values themselves to be independent. Their
  named prior-posterior and concentration constructions are not implemented here.
- [Prediction-Powered Active Testing, 2026](https://arxiv.org/abs/2607.08347v1),
  retained 9 July 2026 v1: revisit Section 4 and the appendix conditions for
  asymptotic intervals. Its residualized estimation motivates a serious later
  comparator, but no PPAT run or finite-sample optional-stopping guarantee is
  inferred from those intervals. Its stronger implementation is not claimed
  defeated by this methods exercise.

This turn used three discovery queries, then primary pages and targeted theorem
reads. The prior 20-source frontier review remains the broader dated context.
The initial discovery response is retained in the conversation, with query text
recorded privately; subsequent primary-page tool responses are also retained in
the owned packet. Secondary search hits are not used as method evidence.
No claim of exhaustive coverage or a globally optimal algorithm follows.
