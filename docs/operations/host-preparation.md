# Credential-free host preparation proposal

Separate real OpenCode lifecycle/RPC evidence from provider-backed first-use proof.

Parent: [operations](README.md).

## Proposed environment, not yet executable proof

- Use a disposable Linux/amd64 container with OpenCode **2.0.24**, matching the locked `@opencode/plugin` SDK. An exact host binary/image digest must be source-verified and pinned before launch; the SDK package alone is not a host installation. No unpinned `latest`, V1 host, global install or invented launch/RPC endpoint.
- Reuse the pinned Bun/Node base and immutable candidate export described in [Linux verification](linux-verification.md). Put host config/data/cache, plugin dependencies, project state and compatibility fixtures in container-only paths. Load server and TUI entry points from this candidate, not an installed global plugin.
- Prepare a credential-free config with no inherited provider/auth files. No host homes, config, auth mounts, real model calls or user ledger reuse. Separate lifecycle/legacy fixtures from the still-empty first-use installation.
- Host verification requires a terminal driver and real host RPC fixture mechanism using supported host interfaces; no production test APIs or replacement adapter. The Linux verification scripts do not provide this harness.
- Before execution, document exact host launch/terminal commands, supported readiness signal, per-step assertions, at most 120-second readiness and 10-minute total lifecycle, and process-tree/container teardown with absence checks. Until the host artifact and runner are pinned these are proposed limits, not runnable commands.

## Evidence still needed

1. Actual host two-slot interaction, remount/reload retaining tokens, exit/restart restoring dollars while retaining durable open state.
2. Actual host schema/transport: unchanged old input, legacy dollar-only response, nested NULL and zero accepted without value loss. No invented HTTP/WebSocket substitute.
3. Provider-backed activity in a separate clean installation: empty Tokens before normal provider activity, receiver ready first, recorder → change notification → real RPC → both views, unchanged accounting when switching.

The documented Linux runner does not include a source-verified pinned host distribution or terminal/RPC harness. It cannot verify host lifecycle, real RPC transport or provider first-use behavior. Credential-free preparation does not prove provider-backed behavior; that requires a separate environment with explicitly configured model access. Do not reuse user settings or credentials to fill this gap.
