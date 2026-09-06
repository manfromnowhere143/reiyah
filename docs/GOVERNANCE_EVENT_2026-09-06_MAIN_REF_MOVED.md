# Governance event, 2026-09-06: the public `main` ref was moved to the Gate B tip

Document ID: `reiyah.gate-b.governance-event-2026-09-06-main-ref-moved`

Version: `0.1.0`

Lifecycle status: `proposed`

## What was observed, from exact records

On 2026-09-06 the local remote-tracking reflog for `origin/main` in the canonical clone at
`/Users/danielwahnich/workspace/reiyah` shows eight successive `update by push` entries moving the
public `main` ref along the `gate-b-measurement` history, ending at `3450415` (Result W). A
`git ls-remote` readback the same day returned `refs/heads/main` at
`34504151bee0225ac88e5b94c107e061791917e1` and `refs/heads/gate-b-measurement` at
`21c533b36e6a8506ad228657a28d1cbe51f11e5c`. The local `main` branch remains at the released Gate A
`1.2.0` receipt commit `d42d4d298d515b59e9df15f2ba45572a91b9fab8`.

## Why it is an event

1. The engine's Gate A documents state that Gate B is not defined or authorized and that public
   distribution is authorized only for the exact receipt-bound static packet.
2. The Gate B baton states that the measurement lane is published at the `gate-b-measurement`
   branch. It does not state that `main` carries it.
3. No public-distribution receipt, rights observation, or transport observation binds any Gate B
   commit. A push is a publisher act with no scientific, acceptance, or publication authority.

## Disposition

Recorded, not reversed. Which commit the public `main` ref should name is an operator decision.
Until it is taken, readers of the public repository must resolve state from the exact commit they
read and from its receipts, never from the branch name. Every Gate B artifact remains `proposed`.
This record creates no acceptance, no authority, and no transport verification, and it modifies no
released `1.2` byte.
