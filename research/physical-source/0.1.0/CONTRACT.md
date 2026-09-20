# From navigation records to a clearance statement

Document ID: `reiyah.physical-source.contract`. Version: `0.1.0`.
Status: proposed mathematical bridge; no physical parameters are qualified here.

The existing [conditional calculation](../../continuous-envelope/0.1.0/METHOD.md)
accepts intervals on a scalar clearance, a global rate bound and one shared
clock offset. A 3D vehicle pose, a covariance matrix and an interpolated display
are not yet that contract. This note specifies the intervening obligations.

## Fix the quantity before computing it

For a fixed unit road direction `u`, let a vehicle's occupied set at time `t` be
`P_j(t) = p_j(t) + R_j(t) B_j`. `B_j` is its measured body geometry relative to
the INS output reference, including mounting changes where relevant. Define the
projected longitudinal gap

`c(t) = min(x in P_lead(t)) u·x - max(y in P_ego(t)) u·y`.

This is a directional separation. Positive separation implies separation along
that axis. It does not describe lane membership, curved-road following, collision
probability or recoverability. A changing road frame needs additional frame and
rate terms. Both actor identities, reference-point definitions, handedness,
orientation conventions, units, origin and common time must be bound to records.

## Propagate an actual error contract

Suppose, as separately justified assumptions, translation error is bounded by
`e_p`, geometry Hausdorff error by `e_B`, orientation discrepancy by angle
`e_R in [0, pi]`, and body radius about the chosen reference by `rho`.
For compact nonempty body sets, the support-function error along a unit direction
is at most the Hausdorff displacement. Rotation contributes at most
`2 rho sin(e_R/2)`, by the norm of the difference of two rotation matrices.
One actor therefore contributes no more than

`e_p + e_B + 2 rho sin(e_R/2)`.

The pair's deterministic clearance error is bounded by the sum of both actor
contributions. This triangle-inequality bound needs no independence assumption.
It only applies if each premise holds jointly for the stated actor/time scope.
A missing ego footprint, unbound INS lever arm or unknown reference convention
cannot be replaced by a generic vehicle dimension or zero error.

For an absolutely continuous rigid trajectory in a fixed frame, if each actor
has justified translational-speed bound `V_j` and angular-speed bound `Omega_j`,
its support function is Lipschitz with constant at most `V_j + rho_j Omega_j`.
Their sum supplies one sufficient global clearance-rate bound. Flexible parts,
geometry changes and moving axes need additional terms. Maximum sampled speed
is not a proof of a maximum between samples. Linear interpolation at 100 Hz
is a reconstruction choice, not an observed physical rate bound.

The previous solver models one constant common offset. Per-device bias, drift,
jitter, network delay and asynchronous samples require an explicitly justified
reduction to that model or a different frozen calculation. A manufacturer timing
statement for postprocessed navigation packets does not automatically describe
ROS reception timestamps, WiFi-delivered objects or all attached sensors.

## Keep a statistical route distinct

A probabilistic experiment can instead freeze a whole-trajectory event:
both bodies, poses and clocks satisfy the stated envelopes for every relevant
time with probability at least `1 - alpha`, for a named population and horizon.
On that event, a valid deterministic certificate transfers. Unconditional
coverage must include uncertainty from estimating the envelope and any data
selection. Pointwise CEP, RMS or one-sigma specifications do not establish this
event. Cross-vehicle shared corrections and temporal dependence must be handled.
Finite-sample coverage requires a defensible calibration design and its actual
records; a covariance field alone cannot supply them. Such a study needs a
separate protocol and adequate nonreserved calibration/evaluation units.

These are standard geometric and probabilistic implications. Their integration
defines what evidence Reiyah needs; it makes no mathematical novelty claim.
