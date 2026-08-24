#!/bin/sh
# Copyright 2026 Daniel Wahnich
# SPDX-License-Identifier: Apache-2.0
set -eu

REIYAH_GATE_ROOT=$(pwd -P)
if [ "$REIYAH_GATE_ROOT" != "/Users/danielwahnich/workspace/reiyah" ]; then
    echo "gate_a_1_2_0 launcher error: working directory must be /Users/danielwahnich/workspace/reiyah" >&2
    exit 2
fi

unset DYLD_INSERT_LIBRARIES DYLD_LIBRARY_PATH DYLD_FRAMEWORK_PATH
unset DYLD_FALLBACK_LIBRARY_PATH DYLD_FALLBACK_FRAMEWORK_PATH LD_PRELOAD

REIYAH_GATE_SEATBELT='(version 1)
(allow default)
(deny network*)
(deny file-write*)
(allow file-write-data (literal "/dev/null"))'

exec /usr/bin/sandbox-exec -p "$REIYAH_GATE_SEATBELT" \
    /usr/bin/env -i LANG=C LC_ALL=C PATH=/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin \
    /opt/homebrew/bin/python3.14 -I -S -B \
    /Users/danielwahnich/workspace/reiyah/tools/gate_a_1_2_0.py "$@"
