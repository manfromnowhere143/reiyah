# Bounds with optional unknown references

Version `0.1.0`. Informative derivation for the [frozen plan](PLAN.md).

Let A and B be the two fixed prediction sets, including duplicate occurrences
as distinct identities. Let K be the known eligible modeled reference boxes
and let U contain at most k additional eligible boxes, one per unavailable car
instance. An unavailable instance may also be ineligible. K cannot be deleted
or displaced in this contract; its geometry is a conditional model premise.

For one-to-one matching cardinality m(X,T), unit false-positive/miss loss is

`L(X,T) = |X| + |T| - 2 m(X,T)`.

The common reference count cancels in the replacement difference:

`D(T) = L(A,T) - L(B,T) = |A| - |B| + 2[m(B,T) - m(A,T)]`.

Writing nA,nB for prediction counts and rA,rB for matching ranks against K,
adding at most k right vertices cannot decrease a rank or increase it by more
than k. Hence

`rX <= m(X,K union U) <= min(nX,rX+k)`.

With D0 = nA-nB+2(rB-rA), this gives the universal enclosure

`D0 - 2 min(k,nA-rA) <= D(K union U) <= D0 + 2 min(k,nB-rB)`.

The two rank extrema need not be jointly realizable by the same geometric
boxes. This is a sound enclosure, not a general exactness claim.

There is also a shared-prediction bound. Inserting one prediction changes its
unit matching loss by either +1 or -1, because the maximum matching rank grows
by zero or one. Starting from the common prediction identities and inserting
the unique identities on each side yields `|D(T)| <= |A symmetric_difference B|`
for every common reference T. Shared identities require exact matching operands;
they do not mean approximate visual similarity. Intersect the two bounds. If
A and B are identical, the difference remains exactly zero even with unknown
references.

For any case, sum image bounds and divide by its full allocated image count.
Reference worlds may vary together across images; no independent-error premise
or frequency interpretation is used. If an input census is unavailable, retain
an input-blocked case. A smaller complete subset is a different estimand.

Every constructed world is separately checked against its unknown-instance
budget, candidate geometry and native matching proof. Finding one world with
nonpositive mean difference and another with positive difference proves
unresolved strict improvement under this contract. A straddling enclosure
without that pair remains a bound gap. A finite candidate pool, a greedy
search stop or equal scores on tested worlds does not prove universal equality.

All three matching implementations receive the same fixed decimal geometry.
The conventional workflow has these bounds too. No query or cost advantage
follows merely from using a native certificate to check a world.
