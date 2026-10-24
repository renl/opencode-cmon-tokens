# Operations

Prepare isolated verification environments without touching user installations or production.

## Environment and isolation

- Target: disposable Docker Linux/amd64 on the reachable local engine.
- Pass a local commit ID explicitly with `-Revision`; the runner resolves and records one immutable commit SHA.
- The default mode prepares the pinned image and runs bounded readiness probes. Add `-Verify` to install dependencies and run candidate checks.
- No production, shared data deletion, host home/config/auth mounts, global settings, dependency/test changes, provider calls or persistent services.
- Docker manages image storage. Do not inspect its host storage directories. Scratch stays in ignored `node_modules/.cache/cmon-linux/`.

## Procedures

| Document | Purpose |
| --- | --- |
| [Linux verification](linux-verification.md) | Pinned images, finite clean-room commands, cleanup and evidence |
| [Host preparation](host-preparation.md) | Credential-free host lifecycle/RPC requirements and verification limitations |
