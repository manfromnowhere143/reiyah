# Discovery package custody, 2026-09-13

Document ID: `reiyah.perception-discovery-custody.checkpoint`

Version: `0.1.0`

Lifecycle status: `exploratory`

Discovery draft/seal operations now reject destinations inside their observation package.
Previously each could report success after adding a private review file that invalidated the
package's next verification. Eight fresh synthetic controls reproduced this behavior at the
root, inside `assets`, through a symlink and through a case-insensitive alias, for both writers.
The corrected operations reject all eight and preserve every package file and its expected seal.

The [change and reproduction](../research/perception-discovery-custody/0.1.0/README.md) use
directory identity rather than path spelling. A separately checked valid private output remains
usable, and retargeting its original parent symlink during verification does not redirect the
write. The stable-directory assumption remains explicit; this is not a filesystem sandbox.
No record schema, exposure rule, reference interpretation or common comparison interface changes.

The [verification record](../research/perception-discovery-custody/0.1.0/verification.json)
retains 29 passing discovery tests, 359 repository tests, 93 measurement tests and the before/after
reproduction. The research consistency check passes with 52 retained transcript identities,
zero historical experiment replays and no attack-suite replay. Runtime recovery cost and failed
dependency attempts are retained. Existing SQLite ResourceWarnings were not repaired here.
These checks are internal engineering evidence, not human or external scientific review.

The supported Browser runtime reported no available browser connection. The existing native
loader diagnosis and ready manual Blender exercise remain retained, and the participant return
is still absent. No unchanged native bootstrap was retried, no unofficial browser backend was
used, and no permissions or cloud-login diagnosis was inferred. Actual display/selection and
human effort remain unobserved. A valid browser connection or actual participant return is
still needed for those steps.

The next independent Engine check is the same case-alias failure against its remaining private
output guards. Fable's source, branch, planners, status and outboxes remain untouched. No human
judgments were created or admitted. Real bounds remain [-8,8]; preserve joint worlds, matching,
weights, loss, tolerance and explicit unknown states. Gate A is unaccepted. The physical study
is unrun with no selected cohort or seed. P005 is operator-reported published; no further
publication or outreach is authorized.

Exact private continuation: `engine-discovery-custody-2026-09-13`. Older owner checkouts and
closed evidence packets are preserved. This checkpoint is part of the continuing autonomous
Engine work window, not completion of the broader mission.
