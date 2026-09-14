# The fixed detector change, conditional on benchmark labels

Document ID: `reiyah.engine.annotation-case`. Version: `0.1.1`.
Status: `exploratory`. Dated 14 September 2026.

The added detector improves the declared weighted loss by **1** under the retained benchmark
labels, exceeding tolerance **1/10**. The first anchor improves and the second worsens:

| Anchor | Reference labels | Base / additions | TP base / augmented | Loss base / augmented | Difference |
|---|---:|---:|---:|---:|---:|
| window-0001 | 61 | 48 / 9 | 40 / 46 | 29 / 26 | +3 |
| window-0002 | 45 | 37 / 7 | 32 / 35 | 18 / 19 | -1 |
| Equal-weight result | 106 total | 85 / 16 total | Not aggregated here | 23.5 / 22.5 | **+1** |

These are the same two previously exposed frames and the same received detector outputs.
The source scan covers 1,166,187 annotation rows and selects all 119 annotations at those
anchors. The fixed category/range policy includes 106 and records all 13 exclusions.
Fourteen other context frames remain outside the loss population.

## Why this route now

Daniel explicitly requested continued autonomous Engine development without supplying human
reviewers. The completed assisted selection verified point custody but supplied no object
judgment. Waiting for independent discovery would prevent an executable check against available
benchmark labels. The chosen alternative is a separate, retrospective annotation-conditional
replay. The target, exclusions, comparator, cost categories and falsifier were recorded before
the first verdict in the private `PLAN.json`.

The original staged-review experiment and its reference assumptions are preserved. Its exact
comparison still yields **[-8,8]**, with **zero admitted human readings**. No form, reference
admission, source annotation or original common input was modified. This checkpoint does not
claim physical improvement, generalization, independently demonstrated decision value or state
of the art. No prospective cohort or seed is selected; Gate A remains unaccepted.

## Implemented connection and checks

The [annotation adapter](../research/perception-annotations/0.1.0/README.md) binds the retained
metadata archive, scans complete tables, and joins selected annotation -> instance -> category
and annotation -> sample -> nominal anchor clock. Every selected row has its original table
index, byte offset, byte length and digest. Exact decimal coordinates become rational values;
the existing reference compiler and common projection produce the graph. Existing matching
and vertex-cover certificates verify maximum cardinalities and paired additive loss.

No core, compiler, human-admission or common-interface schema was extended. A small offline
adapter supplies the already supported point-reference input. Mapped labels within nominal
XY range <=50 m count, including zero-point labels. No visibility/bicycle-rack filter is applied.
Matching remains same-class strict distance <2 m. This is Reiyah's fixed loss on nuScenes labels,
not an official nuScenes benchmark score. The [source basis](../research/perception-annotations/0.1.0/README.md#target-and-policy)
records the inspected official mapping and SDK differences.

Two producer runs return byte-identical payload files. The second packet additionally records
implementation identity. A separate consumer audit reopens all source tables, checks the 119
literal row identities and joins, and reconstructs all graph edges. It calls neither annotation
producer nor reference compiler. Eight altered-source/graph/result/scope controls are refused.
It shares source parsers, archive handling and the core certificate checker; it is not an
independent annotation assessment. The existing prediction audit also rechecks 648 original
source rows, 158 qualified records and complete 85-base/16-addition retention.

Validation passes 12 focused adapter tests, the **430-test repository suite**, the measurement
suite and `gate_b_check`. The latter checks retained research consistency, not a Gate A release
or a replay of historical physical experiments. Fable's selected existing cohort producer and
checker accept the exact export and agree on **[1,1]**. That replay was performed in the Engine
lane and does not stand in for Fable's forthcoming independent source audit or an effort study.

Those earlier validation commands preceded this document's final table edit. The later
dependency-trace checkpoint found that the table's em dash violated the live documentation
check and caused two measurement regressions to fail. Version 0.1.1 replaces that placeholder
with explicit text; the prior failed check and the unchanged numerical results are retained.

## Exact bindings and cost

The closed private task is
`~/.codex/reports/reiyah/engine-annotation-case-2026-09-14-a63851u3/`.
It begins at Engine main `5a9e702705a94eb333e507d9e1f2b016b17b5263`, tree
`7516fc37ed1b7ddd963fd74355bd21deba1439e6`. Its new source commit is selected by the sealed outbox;
this document's base hash is not authority to reset a newer checkout.

| Artifact | SHA-256 |
|---|---|
| Original open common comparison | `fbb2610aef00687e429bb71d805c4c1f321ec14978005e9fbdf44048bb5547b4` |
| Retained metadata archive | `db48746b10e3544d5ef619eaa3d687e3960626fe1b4422ed856711da5aa7325b` |
| New request file | `3ddf154aeec71fd8ae6925f6e8b60b666caaf760b01e46d7210d8c165e8f3d36` |
| New conditional reference | `1e0ea38b55bfb20d7c0b1a127dd12c593b51f095d371bf1f68c9ecaeee4c9024` |
| New common comparison | `45308db6cec4b5034100f780a2ecd8beb1779b8101cac7c77b343b511ed1afa1` |
| Final computation packet | `11f25fca339977097ef4046820f9ddf1015beb0e1984a305fafab225a14f90e3` |

First producer: 26.431 command seconds, 239,140,864 bytes peak child RSS. Second producer:
27.289 seconds, 215,924,736 bytes; it overlapped repository tests. Consumer source/geometry
audit: 24.657 seconds, 223,363,072 bytes; its start overlapped measurement/consistency checks.
The prediction refresh took 0.394 seconds; the Fable compatibility/export check took 0.038
seconds on already prepared graphs. These commands do different work and are **not a speed
comparison**. Preparation, interpretation, integration and repair time outside the captured
commands remain unmeasured; no human active-time saving is claimed.

Initial research URL attempts for `v1.2.0` and `LICENSE` returned 404. The source selection was
corrected to the exact official commit and `LICENSE.txt`; failed paths are retained in the
private source ledger. The first adapter replay and its focused tests passed. The final packet
adds source identity checking; no favorable-result patch or reference narrowing was needed.

## Next falsifier and ownership

Fable receives the exact benchmark case and source mappings through
`OUTBOX/annotation-conditional-case-0.1.0`. It should independently reconstruct membership,
geometry and the conventional verdict before accepting the headline. The next bounded
diagnostic asks whether deleting any single included annotation, as an explicitly hypothetical
label-error test, changes the improvement criterion. Those counterfactuals are not admitted
human readings or estimated error probabilities. They may expose a fragile positive result.

Engine owns the adapter, source custody, common operands and main integration. Fable owns
the conventional comparator and this challenge. Preserve parity if the ordinary method obtains
the same answer. After checking this case, use a second already available case with a declared
selection rule before expanding the architecture. Independent physical validation remains a
separate future claim; it does not block this automated research route.
