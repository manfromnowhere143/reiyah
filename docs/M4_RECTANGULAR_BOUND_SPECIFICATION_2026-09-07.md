# Rectangular bounds for the coincidence ratio

Document ID: `reiyah.m4-rectangular-bound-specification.2026-09-07`

Version: `0.1.0`

Lifecycle status: `proposed`

This investigation concerns exact mathematics on a declared rectangular cell domain. It is
not a model of the physical reference process, a sampling-confidence interval, a replacement
for independent adjudication or a safety certificate. The reference-transition problem in
[the preceding correction](REFERENCE_NOISE_INTERPRETATION_2026-09-07.md) remains open.

## Domain and the two questions that must remain separate

Let x = (a,b,c,d) contain nonnegative cell masses: both errors, A only, B only and neither.
Each coordinate lies in a supplied closed rational interval [x_L,x_U]. Define n = a+b+c+d
and, only where both marginals are positive,

```text
C(x) = a n / [(a+b)(a+c)]
D+   = {x in the box : a+b > 0 and a+c > 0}.
```

The task is to bound inf C and sup C on D+, and separately report whether the box permits
positive-universe points with an undefined coefficient or permits an empty universe. An
undefined point does not imply that C is arbitrarily large at nearby defined points.
If D+ is empty, no numerical lower or upper coefficient is supplied.

A defined point exists precisely when a_U > 0 or both b_U > 0 and c_U > 0. An empty
universe is feasible precisely when all four lower endpoints are zero. A positive-universe
undefined point is feasible precisely when a_L = 0 and either:

```text
b_L = 0 and c_U + d_U > 0, or
c_L = 0 and b_U + d_U > 0.
```

These are mathematical feasibility states, not claims about missing observations or the
physical world. Unknown empirical constraints cannot be supplied as zero endpoints.

## Reduction by monotonicity

Within D+, fixing the other cells gives:

```text
partial C / partial b = -a(c+d) / [(a+b)^2 (a+c)] <= 0
partial C / partial c = -a(b+d) / [(a+c)^2 (a+b)] <= 0
partial C / partial d =  a / [(a+b)(a+c)]          >= 0.
```

Thus the infimum uses b_U,c_U,d_L, and the supremum uses b_L,c_L,d_U, subject to handling
undefined boundary faces by limits. If a_U = 0 but D+ is nonempty, C is exactly zero
throughout D+; singular faces do not change that fact.

For fixed b,c,d, let s = b+c and t = bc. The derivative with respect to a has the sign of:

```text
g(a) = -d a^2 + 2t a + t(s+d).
```

If b,c are positive and d is positive, g has exactly one nonnegative sign change, at
the positive root [t + sqrt(t^2 + d t(s+d))]/d. C increases before that root and decreases
after it. The infimum is therefore at a valid interval endpoint. For the supremum, endpoint
derivative signs either select an endpoint or bracket the unique interior maximum. If d=0,
the derivative is nonnegative and the upper a endpoint maximizes C.

## Singular faces and attainable bounds

For a > 0 and b=0,c>0, cancellation gives C=1+d/(a+c). Its limit as a tends to zero is
1+d/c, which is finite. The analogous statement holds after exchanging b and c. When d>0
and a_L=0, that supremum can be approached without being attained on D+.

For a > 0 and b=c=0, C=1+d/a. Its supremum is unbounded exactly when the box allows
a approaching zero from above and positive d at that face: a_L=b_L=c_L=0, a_U>0 and d_U>0.
If d_U=0 the defined coefficient on that face is instead exactly one.

Together with the a_U=0 case, these cases exhaust the nonnegative rectangular domain.
Every finite infimum is attained at a defined point. A finite supremum may be attained or
may be a limit at an undefined face. The output must distinguish the two.

## Rational enclosure of an interior maximum

If the stationary root is rational, represent it and its value exactly. Otherwise use exact
rational bisection with g(low)>0 and g(high)<0 to retain a bracket for that root. Over this
bracket both a(a+s+d) and (a+b)(a+c) are positive increasing functions. Therefore:

```text
C(root) <= high(high+s+d) / [(low+b)(low+c)].
```

Any evaluated defined point supplies a lower bound on the supremum. These quantities give a
rigorous rational enclosure whose width decreases with refinement. Report the actual width
and whether the requested tolerance was met. Reaching a refinement budget must never be
reported as achieving an accuracy that was not obtained.

The reduction identifies the sharp extrema of the rectangle; a finite-width rational
enclosure is not an exact decimal value of an irrational extremum. This rectangle may itself
be a conservative outer domain for a different, coupled reference-error model. Its sharp
bounds are not thereby sharp bounds for that more restrictive model.

## Falsification criteria and minimum controls

The retained M4 grid will be exercised without changing its globals on two authored cases.
For a in [0,11], b=c=d=1, the exact maximum is 9/8 at a=3. For a in [0,1], b=0,c=10,d=90,
the coefficient is undefined at a=0 but its supremum is finite at 10.

A replacement fails if it excludes any feasible coefficient, confuses either undefined
case with infinity, loses a defined zero-ratio domain, mislabels an unattained limit as an
observed coefficient, or reports an unmet tolerance as met. Controls must include these
cases, a genuinely unbounded domain, an entirely undefined domain, an empty universe,
exchange of channels, proportional scaling, irrational stationary points and exact checks
on a finite lattice. Arithmetic and proof errors invalidate this mathematical component;
passing controls grants no empirical identification claim.
