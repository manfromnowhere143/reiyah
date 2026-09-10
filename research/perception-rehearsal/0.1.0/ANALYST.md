# Compare a retained configuration with its proposed addition

Guide ID: `reiyah.perception-rehearsal.analyst-guide`; version `0.1.0`.

The engineering question is whether the added detector warrants further integration work under
the declared loss and uncertain reference evidence. Give the supported conclusion and the
observation or assumption that still prevents a choice. This rehearsal measures workflow
problems; it cannot establish reliability, safety or comparative product value on its own.

The coordinator gives the Engine and conventional analysts identical evidence at each declared
stage, including exact output populations, normalization, clocks, loss, weights and all shared
reference alternatives. Ask for the full evidence if an exported graph or summary is
insufficient. Clarifications and additional permitted material go to both analysts with recorded
identities. Neither analyst receives the other's conclusion until both conclusions are locked.

The conventional analyst may use any competent conventional method, including scripts,
matching libraries, exact arithmetic and the same partial-identification mathematics as the
Engine. Record the method and versions, implementation time and any repair. Matching the Engine
is a valid result. This is not a contest against a deliberately limited calculator.

For each common reference interpretation, preserve every base detection and use maximum
same-class one-to-one matching with the declared gate. For nonnegative FN/FP penalties a and b
and r retained additions, the additive loss contrast is

    loss_base - loss_augmented = (a+b) * (TP_augmented - TP_base) - b*r

The elementary interval is `[-b*r, a*r]`. FP counts are unmatched predictions; an invented
true-negative population is unnecessary. Use the same objects in the base and augmented
matchings. An unknown object near a base detection can change which match is available to an
addition. Preserve joint alternatives across windows; separate per-window extrema can lose
information. Document a conservative relaxation as such.

Work from the supplied exact comparison's weights, penalties and tolerance, rather than copying
numbers from an example. The lower and upper limits describe the declared reference model; they
are not statistical confidence limits or proof of physical coverage. If required inputs are
missing or invalid, report `not_evaluated` and the reason. If valid bounds straddle a decision
threshold, preserve `unresolved`. A wide bound alone is not proof of non-identifiability.

Use a copy of your conclusion draft to record the evidence identities, derivation, bounds,
decision, assumptions, missing evidence and next informative observation. Own formats are
welcome if they preserve these fields. Record an initial conclusion before cross-method
discussion. Later corrections get a new identity and keep the original accessible.

Report person time separately for preparation, review, integration, calculation, adjudication
and repair; report compute elapsed time and memory separately. Include failed attempts and
tool setup. Do not assign zero to missing time. Independent adjudication must distinguish a
calculation error, an omitted alternative, a physical-reference disagreement and a difference
in declared decision preference. A more favorable interval is not automatically a better result.
