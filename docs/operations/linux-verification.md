# Disposable Linux verification

Run the immutable candidate without reusing Windows dependencies, user settings or ledgers.

Parent: [operations index](README.md). Acceptance sequence: [SDET tasks](../../openspec/changes/toggle-token-display/tasks.md#run-sequence-canonical-shell-powershell-7--windows-x64).

## Invocation (PowerShell 7, from this worktree)

```powershell
# DevOps: image preparation/readiness only; no candidate installation or tests.
pwsh -NoProfile -File docs/operations/verify-linux.ps1

# SDET only, under independent verification authorization:
pwsh -NoProfile -File docs/operations/verify-linux.ps1 -Verify
```

Prerequisites: Docker Linux/amd64 engine, Git, PowerShell 7, registry connectivity and at least 6 GiB available container memory. No host Bun, Node or package cache is used. Keep this terminal open until the runner exits; interruption still requires checking the recorded resource name and cleanup logs. Do not use a shell timeout shorter than the runner's finite lifecycle (allow 35 minutes for full verification including image preparation).

## Image pins

| Component | Source tag (informational) | Immutable Linux/amd64 manifest |
| --- | --- | --- |
| Bun | `oven/bun:1.4.3-debian` | `sha256:cafb038ad9ebf08d42914f8af35a7b0b825655ad4046ea3470f5ef4f714f3325` |
| Node / Debian | `node:22.23.1-bookworm-slim` | `sha256:8607a9064d4a571140998ae9e52a3b3fcf9cff361d04642d5971e6cd76d39e27` |

Dockerfile copies only Bun into the pinned Node image; it installs no OS packages. The derived image is local, not published; its exact content ID and base metadata are captured in `image-identity.log`. Never substitute a mutable tag for these digests. Bun release differs from the previous Windows canary; record its revision and let SDET assess any runtime-sensitive difference, not assume equivalence.

## Isolation and lifecycle

- `git archive` exports exactly `73f1f09bac9b306e2fce8c73f2bb1f38dfe95b19`, excluding ignored/untracked dependencies and local state. No checkout or branch mutation.
- Input and evidence bind mounts contain only this invocation's project-local ignored scratch. No repository Git metadata, host homes/configuration/auth, Docker socket or credential injection.
- Source is copied into fresh container `/work` tmpfs. Dependencies, build, test scratch, home and caches live there and disappear on container removal. Root filesystem is read-only; privileges/capabilities are restricted.
- Full verification uses Docker's default network for locked registry installation; it receives no provider credentials and issues no real model calls. It is not a security sandbox against malicious candidate code. Readiness uses `--network=none`.
- Install: frozen lock, ignored lifecycle scripts, 180 seconds. Existing adapter → summary → display → full suites, typecheck, lint, build and scoped format run separately with 120-second bounds (build 180). Local locked binaries replace `bunx` to forbid accidental remote tool resolution.
- Overall container deadline: 1450 seconds, TERM then KILL after 10 seconds; host wait 1500 seconds. Image build/pull: 300 seconds. Every host subprocess has its own timeout and output capture.
- Shell EXIT trap records the original status; Docker `--rm` plus PowerShell `finally` removes the unique named container and verifies absence. The unique derived image tag is removed; shared pinned base layers may remain in Docker-managed cache. No persistent services or volumes are created; no prune.
- Logs remain in `node_modules/.cache/cmon-linux/cmon-linux-<UUID>/`. `host-exits.log`, `exits.log`, stage logs, candidate identity, lock/build hashes and `cleanup-check.log` are the evidence bundle. An empty successful cleanup query proves no matching container remains; an `rm` error alone can mean `--rm` already removed it.
- Any failed gate stops the sequence and retains logs. Cleanup uncertainty is a blocker, not success. Do not rerun silently or label tests passed from runtime readiness.

## Status

Preparation only. Independent candidate checks and actual host/provider proof remain separate SDET gates. No rollout/rollback of a deployed service is involved.

### Readiness evidence — 2026-10-24 (DevOps)

- Engine reports `linux/amd64`; bounded manifest discovery resolved the pins above. The initial combined Node manifest query exceeded 30 seconds; a separate 60-second query succeeded. No mutable-tag deployment.
- Final invocation: `pwsh -NoProfile -File docs/operations/verify-linux.ps1`, exit 0. Evidence directory: `node_modules/.cache/cmon-linux/cmon-linux-89622290ed4644e9ba7cb0a9f666bef3/`.
- Derived image ID: `sha256:9d3bb1b7b2a6bf716e68bd88c47afad1b09493ee2f0cc621763381ecb7ee140c` (local content ID, not a published registry digest).
- Network-disabled probe: `x86_64`, Bun `1.4.3+c6da4a4d3`, Node `v22.23.1`, GNU timeout `9.1`; `bash -n` accepts the verification shell script. Build, identity, readiness, container removal, empty cleanup query and derived tag removal all exit 0 in `host-exits.log`.
- Earlier preparation attempts exposed null handling of an empty cleanup log. Fixed the runner to check file length. All four earlier named containers were confirmed absent and their temporary image tags removed; only shared base/build cache and ignored logs remain. No shared-resource prune.
- Working HEAD before operations changes: `3caf32887c831717a45d06ae91b0ee8315a179d7`; diff from pinned candidate contains only `openspec/changes/toggle-token-display/tasks.md`. Operations files do not change candidate code/tests/dependencies/configuration.
- **Not executed:** `-Verify`, locked install, candidate suites/build/format, actual OpenCode host, RPC transport, terminal lifecycle, provider activity. Image readiness is not independent verification or feature/release readiness. Next: CoS routes SDET to run the immutable clean-room procedure and supplies host-artifact discovery/harness work separately.
