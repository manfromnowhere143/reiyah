# Locate and close the four test database handles

Document ID: `reiyah.perception-catalog-lifetime.checkpoint`

Version: `0.1.0`

Lifecycle status: `exploratory`

The four SQLite warnings retained by the preceding 399-test suite originate in two partition
test fixtures. All five production connections exercised by the diagnostic already close on
their normal or rejected paths. The proposed production repair was withdrawn. Two fixture
scopes now explicitly close their connections; the mutation fixture still commits its
adversarial change before testing rejection. Production, mathematical and admission code is
unchanged, as are the tests' existing assertions.

The warning's reporting stack was not its allocation site. A natural replay of the two tests
reproduced four unclosed-database warnings after collection. A separate diagnostic deliberately
held the nine returned connection objects: all five created by the builder were closed, while
four opened directly by the fixtures remained usable after the tests returned. After the
repair, the same probes recorded zero warnings and nine explicitly closed connections. Holding
objects changes garbage-collection timing; this is a lifetime diagnostic, not a production
handle-count or performance benchmark.

Python documents that its SQLite connection context manages transactions without closing the
connection, and recommends a separate closing context when needed. The repair uses that
conventional method. [Connection context](https://docs.python.org/3.14/library/sqlite3.html#how-to-use-the-connection-context-manager),
[contextlib.closing](https://docs.python.org/3.14/library/contextlib.html#contextlib.closing).
The exact official pages were retained privately on 2026-09-13. They identify Python 3.14.7;
the diagnostic directly checks the selected local Python 3.14.2 runtime. No third-party page
payload is distributed with this change.

The whole affected module passed **12 tests**, with resource warnings enabled and none emitted,
in 0.535 seconds; macOS child maximum RSS was 36,306,944 bytes. Both before/after lifetime probes
are retained. No new test was added and no broad suite was rerun. The previous **399-test** full
run remains historical evidence at `8e3e55d5cd4a28ea5f838a85722bf615ade88339`; its one changed test
file is explicitly distinguished from the unchanged sources. The earlier 93 measurement tests
remain retained evidence. This cleanup supplies no new scientific, human-effort or viewing result.

Replay the affected tests from the repository root:

```sh
python -B -W always::ResourceWarning -m unittest tests.test_nuscenes_training_partitions -v
```

Exact initial/corrected source identities, four lifetime reports, allocation-site records,
command captures and the selected documentation are retained under
`~/.codex/reports/reiyah/engine-catalog-lifetime-2026-09-13/`. Its sealed outbox requests only that
the earlier four warnings be attributed to these fixtures; it requests no Fable source change.
The next falsifier is a warning or usable connection left by the corrected scopes, or loss of
the committed mutation needed by the cross-partition rejection control.

The real comparison remains `[-8,8]`, with no admitted human references. Participant usability
and external scientific review remain missing; Gate A remains unaccepted. A supported actual
opening and source selection remains the principal external prerequisite.
