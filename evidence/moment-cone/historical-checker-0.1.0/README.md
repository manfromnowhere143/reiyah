# Check outputs from checker version 0.1.0, retained as history

Dated 10 September 2026. These files were produced by
`tools/measure/check_moment_cone_certificate.py` at version `0.1.0`, the version whose
corner-coverage test was defeated by the forgery retained in `../retained-failures/`.

They are kept because they are what that version actually emitted, not because they are current.
Do not read them as current confirmations, and do not expect them to be byte-identical to a
present-day rerun: the repaired checker reports `corners_declared` alongside `corners_checked`
and attaches a receipt binding the exact bytes it read, neither of which exists here.

Every verdict recorded in these files was re-established by the repaired checker. The current
outputs are the `*-check.json` files in the parent directory.
