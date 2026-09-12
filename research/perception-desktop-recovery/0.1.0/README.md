# Native desktop connection diagnosis, 0.1.0

The connection is not recovered. Its retained failure now has a demonstrated cause:
the supplied native service aborts in the dynamic loader on macOS 14.4 because a required
Swift concurrency symbol is missing. The next prerequisite is a compatible official
service/runtime combination. Another identical launch, screen-permission change or cloud
login does not repair this loader failure.

This is a bounded environment diagnosis in the Engine observation lane. It adds no viewer,
planner, matching method, system patch or reference judgment. The prepared native Blender
opening/selection/Save As procedure remains the conventional workflow and manual alternative.

## Evidence chain

The retained official Blender-inspection request began at `08:47:46.247 UTC` on
2026-09-12. The service launched at `08:47:46.643100 UTC`; its OS crash report was captured
at `08:47:46.794300 UTC`. Both fall inside that request, which returned its native-pipe
startup failure at `08:47:51.847 UTC`. This correlates an existing failure with an existing
crash report; no new GUI launch or observation was performed here.

The report identifies `DYLD`, `Symbol missing`, and
`_swift_task_addPriorityEscalationHandler`, required from
`/usr/lib/swift/libswift_Concurrency.dylib`. A second retained service crash reports the
same failure. Read-only checks independently establish:

- The installed and plugin-cache service executables have identical SHA-256 digests.
- Their Mach-O UUID matches the crashing executable in both reports.
- The installed binary has the same strong undefined import in its symbol table.
- The live OS is macOS 14.4, build 23E214, matching both reports.
- Strict on-disk code-signature verification succeeds. Integrity does not establish runtime
  compatibility or desktop permission state.

The service is version `26.708.1000366`, build `1000366`. Its Mach-O metadata declares
minimum OS 14.4 and SDK 26.4. The declared minimum alone therefore cannot establish that
this binary actually loads on this host. No working replacement build or minimum working
OS version has been verified. Do not invent an upgrade target from those metadata fields.

The native client source attempts to connect, requests service startup, and then waits
for the connection. A service that aborts at launch cannot supply that connection. Public
runtime metadata does not expose the host's effective overrides; this review does not
rule out further configuration or permission issues after the loader failure is repaired.
The six-hour process-filtered log query returned no service events; the useful evidence
was in the retained OS crash reports. See [verification](verification.json).

## Changed engineering decision

Retire repeated unchanged bootstrap attempts as the next task. The smallest concrete
prerequisite is an official native build compatible with the host and supplied client API,
or a separately selected supported host/runtime. The supplied cache contains the same
failing executable, so recopying it is not a demonstrated remedy. No system library,
security setting, operating system, installed app or other owner's process was changed.

Once that prerequisite changes, the first falsifiable check is a successful official
`get_app_state` response for Blender, with actual current app state and screenshot.
Retain the new service/host identities and any failure. Only then exercise the prepared
source-bound scene, select visible points, Save As, and verify the returned original record
indices and attributes. App state is engineering observation, not independent human review.

An actual participant can test the existing
[opening procedure](../../perception-viewer/0.1.0/OPENING.md) directly in Blender without
depending on this agent connection. The prepared scene remains unchanged. No participant
has supplied an exercise result or human reference judgment in this checkpoint.

## Cost and limits

The OS-version query took 0.008 seconds, Mach-O load-command inspection 0.062 seconds,
and undefined-symbol inspection 18.926 seconds, including process startup. These are
individual local command times, not a human-review or comparative effort budget.
The initial timestamp-correlation attempt rejected Apple's timestamp spelling; the
corrected parser uses its explicit numeric timezone format. That failed attempt is retained.

Raw crash reports and installed client excerpts remain private. Only the relevant facts
and integrity bindings are published. Existing Engine, point-selection and image-fidelity
checks remain retained evidence; unchanged test suites were not rerun for this diagnosis.
No Fable source, branch, status, outbox, comparator or planner was modified or reimplemented.
Its newer exchanges have not been accepted by this environment diagnosis.

The real comparison remains [-8,8]. Independent staged discovery, practical human effort
and external scientific review remain missing. Preserve joint alternatives, matching
competition, weights, loss, tolerance and unknown states. Gate A is unaccepted; the physical
study has no selected cohort or seed and is unrun. P005 is operator-reported published;
no further publication or outreach is authorized by this checkpoint.
