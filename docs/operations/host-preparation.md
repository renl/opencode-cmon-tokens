# Credential-free host preparation proposal

Separate real OpenCode lifecycle/RPC evidence from provider-backed first-use proof.

Parent: [operations](README.md). Required assertions and ordering remain owned by [SDET](../../openspec/changes/toggle-token-display/tasks.md#boundary-verification--architect-accept-corrected-decomposition-accept).

## Proposed environment, not yet executable proof

- Use a disposable Linux/amd64 container with OpenCode **2.0.24**, matching the locked `@opencode/plugin` SDK. An exact host binary/image digest must be source-verified and pinned before launch; the SDK package alone is not a host installation. No unpinned `latest`, V1 host, global install or invented launch/RPC endpoint.
- Reuse the pinned Bun/Node base and immutable candidate export described in [Linux verification](linux-verification.md). Put host config/data/cache, plugin dependencies, project state and compatibility fixtures in container-only paths. Load server and TUI entry points from this candidate, not an installed global plugin.
- Prepare a credential-free config with no inherited provider/auth files. No host homes, config, auth mounts, real model calls or user ledger reuse. Separate lifecycle/legacy fixtures from the still-empty first-use installation.
- SDET must supply the smallest terminal driver and real host RPC fixture mechanism, using supported host interfaces; no production test APIs or replacement adapter. DevOps implements no new harness in this task.
- Before execution, document exact host launch/terminal commands, supported readiness signal, per-step assertions, at most 120-second readiness and 10-minute total lifecycle, and process-tree/container teardown with absence checks. Until the host artifact and runner are pinned these are proposed limits, not runnable commands.

## Evidence still needed

1. Actual host two-slot interaction, remount/reload retaining tokens, exit/restart restoring dollars while retaining durable open state.
2. Actual host schema/transport: unchanged old input, legacy dollar-only response, nested NULL and zero accepted without value loss. No invented HTTP/WebSocket substitute.
3. Separately authorized model access and clean installation: empty Tokens before normal provider activity, receiver ready first, recorder → change notification → real RPC → both views, unchanged accounting when switching.

Credential-free lifecycle/RPC preparation can progress without model access, but no source-verified pinned host distribution or terminal/RPC runner was supplied. These are **BLOCKED**, not waived or verified. Provider first-use remains **BLOCKED** on separate model-access authorization as well. Ask CoS to route host artifact discovery and SDET harness ownership; do not inspect user settings to work around the gap.
