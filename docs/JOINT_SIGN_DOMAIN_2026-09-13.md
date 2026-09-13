# The complete sign classification, and a withdrawn identification condition

Document ID: `reiyah.joint-sign-domain.2026-09-13`

Version: `0.1.0`

Lifecycle status: `proposed`

Lane: independent research and conventional comparator. Changes no Engine file, no common operand,
no admission, viewer, shared handoff or main. Gate A remains unaccepted.

## The identity

For observed counts `w` both channels report, `x` and `y` reported by one each, `u` reported by some
other channel and by neither of the pair, and an additional unseen count `m`:

```
c(m) - 1  =  [ w * (u + m) - x * y ]  /  [ (u + x + m) * (u + y + m) ]
```

derived rather than assumed, checked on 20,000 random configurations with no mismatch. The
denominator vanishes only at `m = 0` with `u + x = 0` or `u + y = 0`, and those tables are refused as
an invalid domain rather than reported as a sign.

## Withdrawn: a third channel makes the sign identifiable

This lane's sealed checkpoint asked a consumer for a third prediction submission, on the ground that
it would populate the empty cell and **make the sign identifiable**. That is false.

At `(w, x, y, u) = (1, 2, 2, 1)` a third channel reports, `u` is positive, and

| `m` | `c(m)` |
|---|---|
| 0 | `2/3` |
| 4 | `50/49` |

Opposite signs remain possible. The sufficient condition is `w * u > x * y`, which an additional
channel need not produce, and a channel's report is not thereby a true physical object. **The request
is withdrawn**, and what replaces it is narrower: a third channel is useful because it can make
`w * u > x * y` attainable, not because its presence settles anything.

## Withdrawn: one undefined state

The earlier routine returned a single `undefined` whenever the threshold had no value, and stopped.
At `w = 0, x = y = 1, u = 0` the threshold is indeed undefined, and yet

```
c(m) = 1 - 1/(m + 1)^2  <  1   for every admissible m
```

so the sign is fully determined. **Invalid, undefined and unresolved are three different outcomes.**

The threshold formula is also corrected: it is `(x*y - w*u)/w`, not `x*y/w`. They agree only when
`u = 0`, which is why the old form was right on two channel tables and would have been wrong the
moment a third channel appeared.

## The complete classification

Over non negative integers `m`:

| condition | state |
|---|---|
| `w > 0` and `w*u > x*y` | `c > 1` for every `m` |
| `w > 0` and `w*u = x*y` | `c = 1` at `m = 0`, above 1 for every `m >= 1` |
| `w > 0` and `w*u < x*y` | **unresolved**: at most 1 below the threshold, above it afterwards |
| `w = 0` and `x*y > 0` | `c < 1` for every `m` |
| `w = 0` and `x*y = 0` | `c = 1` for every `m` |
| denominator zero at `m = 0` | **invalid domain**, refused rather than reported |

Verified exhaustively against direct evaluation on all `6^4 = 1,296` tables with counts up to five,
and on `2,401` in the wider sweep, with no contradiction.

## Reproduce

```sh
python3 -B tools/measure/joint_sign_domain.py
python3 -B tools/measure/joint_sign_domain.py 1 2 2 1
python3 -B -m unittest discover -s tools/measure -p 'test_joint_sign_domain.py'
```

Thirteen tests, exact rational arithmetic, standard library only, no data read.

## Non-claims

An internal research artifact, retained as `proposed`. Not independent external scientific review,
not an operator acceptance, not a safety, compliance or vendor claim. Nothing here establishes that
any real pair of channels is or is not positively coupled.
