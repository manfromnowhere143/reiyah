# Desktop prerequisite, 2026-09-12

The retained native-pipe failure is now tied to an OS loader crash: the supplied native
service requires a Swift concurrency symbol absent on this macOS 14.4 host. The crash
occurs within the exact earlier Blender-inspection request, and its executable UUID and
missing symbol match independent inspection of the installed binary. The code signature
checks successfully, and the plugin-cache executable has identical bytes.

Read the [diagnosis, limits and next check](../research/perception-desktop-recovery/0.1.0/README.md)
and [verification](../research/perception-desktop-recovery/0.1.0/verification.json).
This changes the next engineering action: obtain a compatible official native service/runtime
combination before another automated desktop request. Neither a working replacement build
nor a minimum working OS version has been established. No installed application, OS,
security setting or other owner's process was changed.

The existing prepared Blender procedure is the immediate manual alternative. Actual
display/selection, participant effort and independent human reference judgments remain
unobserved. No repeated GUI bootstrap, generated screenshot or background import was
substituted for them. New Fable exchanges remain outside this diagnosis; Fable's work and
the Engine comparison/admission interfaces are unchanged.

The real result remains [-8,8], Gate A remains unaccepted, and the physical study is unrun
with no cohort or seed selected. P005 is operator-reported published; no further publication
or outreach is authorized. Continue from the exact private `engine-desktop-recovery-2026-09-12`
packet, preserving all older owner checkouts and closed evidence.
