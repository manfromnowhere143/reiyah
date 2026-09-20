# Primary research and decision, 20 September 2026

The exact source bytes, version observations, digests, access and distribution
terms are recorded in [sources.json](sources.json). Bodies remain in the owner's
private source store. No source code, figure or dataset payload is distributed.

- [Besset, Tillet, Fan and Alexandre dit Sandretto, arXiv:2609.09439v1](https://arxiv.org/html/2609.09439v1),
  submitted 8 September 2026, studies sufficient constraints for correcting
  uncertain temporal verdicts over reachable tubes. Its discussion retains
  reachability computation as a substantial cost. This supports investigating
  actionable uncertainty, while ruling out a novelty claim for that broad idea.
  Reiyah does not reproduce its nonlinear control experiment or reported speed.
- [Baird et al., author manuscript](https://coogan.ece.gatech.edu/papers/pdf/baird2025risk.pdf),
  listed as IEEE Control Systems Letters 2026, DOI 10.1109/LCSYS.2025.3645827,
  identifies times needing tighter signal intervals. It also distinguishes
  whole-trajectory confidence from individual point bounds. Its delay discussion
  leaves temporal robustness outside the letter's scope. Our shared-clock
  calculation is a narrowly specified additional model, not evidence of an
  advantage over their optimization method.
- [Finkbeiner et al., Algorithms 15(4),126](https://www.mdpi.com/1999-4893/15/4/126),
  published 11 April 2022, shows why shared sensor offsets must remain jointly
  constrained during temporal evaluation. An author-hosted PDF supplies retained
  evidence when the web renderer fails. Our temporal offset differs from their
  sensor-offset model; the common lesson is to preserve dependencies.
- [Das et al., retained arXiv HTML](https://arxiv.org/html/2604.14714v1)
  studies disturbance tolerance for specified dynamical systems. The requested
  v1 URL has a 16 April header and an internal 24 August 2026 date; that version
  ambiguity remains. We use the distinction between a signal margin and a
  dynamical disturbance bound as context. No matrix theorem, scenario guarantee
  or reported result is imported or validated here.

These papers justify a research direction; none supplies the missing calibrated
NGSIM geometry, clock or relative-motion envelope. No probabilistic coverage is
inferred by multiplying marginal coverages without justified dependence. The
new computation instead proves an exact result inside its authored deterministic
scalar model. A full STL monitor, controller or uncertainty-learning system
would require a separate task and stronger evidence. This is the reason to
build the small conditional calculation now and defer a physical comparison.
