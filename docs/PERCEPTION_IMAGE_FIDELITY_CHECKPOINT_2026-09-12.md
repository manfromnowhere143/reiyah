# Camera pixel correspondence checkpoint, 2026-09-12

One declared development camera capture now has a full decoded-pixel correspondence check
against its unchanged original JPEG. All 4,320,000 RGB samples agree between native Blender
5.1.2 and Pillow 12.3.0 after exact inversion of the byte-to-binary32 mapping and reversal
of native row order. [The probe and coordinate rule](../research/perception-image-fidelity/0.1.0/README.md)
make the checked behavior reviewable. [Verification](../research/perception-image-fidelity/0.1.0/verification.json)
binds the implementation and retained measurements. Twelve focused adversarial tests and
93 measurement tests pass. A wrong encoded-size request rejects before native import. The
initial native dependency failure is retained; the header check is now standalone while
full profile validation remains in the conventional comparison environment.

The changed engineering decision is to require an explicit top-left image coordinate
convention and bind the original compressed capture separately from its decoded raster.
Dimensions alone did not establish that relationship. No admission/common comparison
interface or Engine mathematics changes were necessary. This is bounded offline verification,
not another viewer. The check covers one first-in-order capture, not all delivered images;
the two application paths share libjpeg lineage.

No interactive observation or human judgment was obtained. The separate point exercise
remains prepared at the closed `engine-viewer-2026-09-12` checkpoint. Its return directory
contained only an unfilled observation form when this continuation began. The desktop's
default native socket was still absent. No identical failed bootstrap was repeated.
The Computer Use service bundle exists locally; why it has not provided a socket remains
unestablished. Neither missing screen permissions nor cloud authentication was diagnosed.

Next, an actual participant can perform the already prepared opening/point-selection/Save As
exercise and record actual time and difficulties, or an operational desktop connection can
permit an agent engineering exercise. Agent interaction would still not establish human
usability or independence. Keep discovery and assisted review staged; do not turn a selected
point or an exact decoded pixel into an admitted physical object judgment.

Fable retains its comparator/planner lane and the continuation brief following immutable
5cf4c91. Its source, branch and outputs were not modified or newly accepted here. This task
supplies no reference input to that planner. The open real comparison remains [-8,8]; no
independent human reference judgment or external scientific review was created. Gate A is
unaccepted. No physical-study cohort or seed is selected and the study remains unrun.

P005 remains operator-reported published on 12 September. Earlier unpublished/deferred
records are historical. No new publication or outreach was performed or authorized. The
comparison commitment remains equal staged evidence with all effort counted, including
preparation, checking, interaction, analysis and repair. Frozen protocols, previous failures
and owner checkouts remain preserved.
