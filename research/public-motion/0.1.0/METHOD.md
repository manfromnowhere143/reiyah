# What a recorded trajectory can establish

Document ID: reiyah.public-motion.method. Version 0.1.0.
Lifecycle status: exploratory.

For each preselected ego identifier, keep its initial source preceding
identifier over a two-second window. The source coordinate is the vehicle's
front centre along the road. Its reported space headway is front-to-front;
it is not rear-to-front clearance. Vehicle length belongs to the lead vehicle.

Define the **recorded longitudinal proxy**, at an available common timestamp,

`q(t) = (lead.local_y(t) - lead.v_length(t) - ego.local_y(t)) * 381/1250`.

The multiplier explicitly adopts the international-foot convention to express
this authored proxy in metres. Local fields are documented as feet, while
separate aerial/global metadata contains survey-foot and coordinate-zone
details. This calculation does not settle those physical coordinate issues.
Subtracting a vehicle length along an axis also does not establish its projected
rear-bumper location when heading and footprint evidence are absent.

The discrete question is whether q(t) is at least five at **all 21 allocated
recorded instants**, including both endpoints, spaced 100 ms apart.
A below-threshold recorded proxy contradicts that annotation-level statement.
It does not establish a physical violation. Safe recorded points do not
establish continuous clearance.

The producer uses an identity/time index and subtracts the converted front
coordinate from a converted rear proxy. The conventional checker independently
selects the first identities, scans the two rows for each timestamp, computes
the raw difference before conversion, and derives its own result. Both use
exact rational numbers parsed from finite decimal strings. No floating-point
threshold rounding or dictionary-order actor choice is used. Equal minima use
the earliest relative time.

## Qualification and non-promotion

Both implementations require: exactly 200 ordered seed rows, eight distinct
selected ego identifiers, an uncapped trace response, only requested identities
and times, no duplicate identity/time pair, one common frame sequence, the same
explicit preceding identity and lane throughout, and constant positive reported
vehicle dimensions. Missing interior or boundary frames, off-grid frames,
changed actors/lanes/dimensions and incompatible frame clocks retain an
unresolved source binding. Their discrete calculation is not evaluated.
Malformed or out-of-query input is invalid and is rejected; it is not empty data.

Each admitted record also reports the largest discrepancy between the separate
front-to-front headway field and the difference of front coordinates. This is
a descriptive consistency diagnostic; zero does not establish physical accuracy,
and a discrepancy is never corrected or silently used as an error tolerance.

The physical continuous-clearance field remains unresolved: measurement bounds,
projected bumper geometry and inter-sample behavior are not qualified. The
source's approximate accuracy is not a uniform error bound or a confidence
interval with a specified probability. A favorable arithmetic margin cannot
supply a missing premise.

The margin q_min minus five is retained privately to identify the precision a
later measurement contract would need. It is not a measured sensor-error budget.
No chosen interpolation, confidence score, source quality flag or process exit
code changes the physical admission decision.

This is established arithmetic and a source-qualification interface, not new
temporal-logic mathematics or a new full driving monitor. Eight dependent cases
cannot establish fleet prevalence, false-assurance rates, customer value or
comparative speed. The existing authored continuous-clearance checker remains
unchanged; actual traces are not relabelled as its authored exhaustive worlds.
