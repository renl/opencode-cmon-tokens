# Operations

Prepare isolated verification environments without touching user installations or production.

## Approved environment and actions

- Target: disposable Docker Linux/amd64 on the reachable local engine.
- Current authorized candidate: `6ff10b39178bd1ce9ca5acb5080c049de1e08406` (prior evidence checkpoint: `3d634094`). Pass it explicitly with `-Revision`; the runner resolves and records one immutable commit SHA. Accepting a revision does not authorize verification of other artifacts.
- Authorized: operations documentation/scripts, pinned image discovery/pull/build and bounded image-readiness probes. SDET separately owns execution of candidate verification.
- No production, shared data deletion, host home/config/auth mounts, global settings, dependency/test changes, provider calls or persistent services.
- Docker manages image storage. Do not inspect its host storage directories. Scratch stays in ignored `node_modules/.cache/cmon-linux/`.

## Procedures

| Document | Purpose |
| --- | --- |
| [Linux verification](linux-verification.md) | Pinned images, finite clean-room commands, cleanup and evidence |
| [Host preparation](host-preparation.md) | Credential-free host lifecycle/RPC proposal; remaining proof blockers |

Owner: DevOps. Parent: [project guidance](../../AGENTS.md). Independent acceptance/e2e authority: [candidate tasks](../../openspec/changes/toggle-token-display/tasks.md).
