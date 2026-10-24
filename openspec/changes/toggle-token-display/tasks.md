# Toggle token display — implementation and tests

Display compact token amounts and keep every control usable in a narrow sidebar without changing counts, ranking or dollar accounting.

References: [proposal](proposal.md), [behavior delta](specs/cost-display/spec.md), [design](design.md), [UX](ux.md), [Linux verification procedure](../../../docs/operations/linux-verification.md).

## Implementation checklist

- [x] Read the five disjoint token columns losslessly in the existing summary snapshot; preserve NULL versus zero, per-group completeness, range boundaries and raw-value ordering.
- [x] Add an optional `tokens` RPC response block without changing existing inputs, dollar fields, database version or tool outputs. When present, the block contains all five fields required by the design.
- [x] Share the selected unit between sidebar and footer through session memory. Keep durable breakdown/open state independent; a fresh session defaults to dollars.
- [x] Render token loading, unavailable and partial states without confusing missing prices with missing token history. Preserve dollar totals and ranking when switching back.
- [x] Format integers below 1,000 exactly; otherwise use decimal `k`/`M`/`B`, at most two decimals, nearest-half-up rounding, trimmed zeroes and suffix promotion. Keep the `B` cap and singular `1 token`.
- [x] Measure the actual panel, not the terminal. Keep separate View/Unit rows, reserved nonshrinking choice widths and atomic clickable text at 45/40/22 cells inside a wider terminal.
- [x] Preserve intact amounts with continuation lines, name truncation or stacking as specified in UX. Clip the footer once at its own width. Control/gap clicks must not activate an ancestor; content remains selectable and chrome does not.
- [x] Close test-owned SQLite readers before fixture removal. Loading uses U+2026 (`…`).
- [x] Complete controlled clean-room regression, type, lint, build and formatting checks.
- [ ] Verify actual OpenCode slot geometry, shared-memory reload/restart lifecycle and RPC compatibility in a supported host.
- [ ] Verify clean first use with normal provider activity from an isolated empty installation, including both unit views and unchanged accounting after switching.

Production areas: `src/{types,store,summary,rpc,index}.ts` and `src/tui.tsx`. Recording, repair, retention, monetary semantics, ranking, tool output, dependencies and configuration remain unchanged by the token presentation feature.

## Executable test map

Test paths below are relative to `src/`. Assertions run through production entry points where applicable; adapter checks do not establish real-host compatibility.

| Tests | Required assertions |
| --- | --- |
| `test-support/token-host.test.ts` TOK-00 | Adapter recording path, dollar baseline and fixture cleanup. |
| `token-summary.test.ts` TOK-01/02 | All 32 NULL masks; complete vector totals 700; failed child, compaction, zero-cost, unknown attribution, merged models, binary ties, unavailable-last ordering, group completeness, half-open range, empty zero and read-only repeat. |
| `token-summary.test.ts` TOK-03 | Unchanged RPC input/top-level required status; nullable numeric total and boolean completeness; arrays with exact required agent/model/provider string keys and nullable totals/boolean completeness. Equivalent numeric union spellings are accepted. |
| `token-display.test.tsx` TOK-04 | Rendered clicks switch both ways, preserve Models/open state, update token footer ranking/top-two/+1 and restore dollars without RPC or durable accounting writes. |
| `token-display.test.tsx` TOK-05; `tui.click.test.tsx` | Active choice, label and gap clicks are no-ops; real selection drag selects content but not chrome at 80/45/40/22 cells; collapse and control behavior remain intact. |
| `token-display.test.tsx` TOK-06 | Shared slots, independent remount, refresh/error recovery, collapse, new mount with the same memory, fresh-memory dollars default and retained open state. |
| `token-display.test.tsx` TOK-07/10 | Legacy reply without tokens, loading ellipsis, unavailable feedback and suppression of invented rows/partial markers. |
| `token-display.test.tsx` TOK-08/11 | Intact amounts at narrow widths, reachable Providers control, group-specific coverage markers, singular label and larger-than-billion amounts; sidebar assertions are not masked by footer output. |
| `token-display.test.tsx` TOK-09 | Empty Tokens view, active subscription before normalized start/end events, production recorder/store/notification/RPC-adapter refresh to 700 tokens and $0.25, unchanged ledger after switching, subscription/database/directory disposal. Synthetic events are not provider activity. |
| `token-summary.test.ts` TOK-12/13 | Immutable dollar regression; missing Copilot price still yields 700 complete tokens. Rendered TOK-04 independently restores the dollar `~` marker without adding a token partial marker. |
| `token-format.test.ts` TOK-14/15 | Every integer below 1,000; zero/one/NULL/absent, complete/partial; half-up suffix boundaries, promotion at 999995 and 999995000, trimmed zeroes, B cap/large B; equal formatted strings preserve raw values/order and dollar projection. |
| `token-display.test.tsx` TOK-16 | Nested 45/40/22 panels in a 120-cell terminal; separate rows, whole choices/brackets at reserved coordinates, all six selections, active/label/gap/reserved-cell no-ops, no ancestor action or RPC/durable write, panel-only resize. |
| `token-display.test.tsx` TOK-17/18 | Approximately 1.58B header, collapsed/continuation states, long-name alignment/truncation for every breakdown and unavailable name/amount stacking at 22 cells. |
| `token-summary.test.ts` TOK-19 | Exact RPC total 2467; raw 1234 ranks before 1233 despite names/equal compact strings; unchanged dollar order/total and ledger. |
| `test-support/layout-boundary.test.tsx` TOK-20 | Test-only renderer ref/resize probe observes parent widths 45→22→40→45 while terminal width stays 120. Production must not depend on this probe. |
| `token-display.test.tsx` TOK-21 | Equal compact strings retain raw order; footer trailing clipping uses its own 120/45/22 widths. |
| Existing `store`, `backfill`, `summary`, `pricing`, `money`, `tui`, `analysis`, `tools`, `index` suites | Preserve accounting, tools, recording, repair, retention and existing dollar behavior. |

## Boundary contracts and limits

- OpenCode subscription remains `ctx.event.subscribe({signal})` with `session.step.started`/`session.step.ended`. Normalized input/output/reasoning/cache.read/cache.write are disjoint. Receivers must be active before activity.
- RPC remains `CostRpc.id = "cmon"`, `summary({from:number,to:number})` over a UTC half-open interval and `changed({revision:number})`, using `ctx.rpc.register` and `ctx.client.rpc(CostRpc)`. No new network endpoint, authentication flow or name mapping is introduced.
- Locked `@opencode/plugin@2.0.24` defines `memory<Value extends object>(key,{initial})` with a live store and synchronous void setter, retained across reload but lost on exit. Durable `store` has a Promise-returning setter and persists across restart.
- Locked `@opentui/{core,solid}@0.5.14` provides `testRender`, mouse/selection support, typed refs, measured renderable width, `flexShrink` and `onSizeChange`. The resize callback has no width argument; measured width is available on the renderable. The probe permits but does not mandate a private layout strategy.
- Schema-shape assertions, JSON round-trips and storage doubles do not prove actual host validation, transport or lifecycle. Hidden/zero-width host padding, exceptional amounts wider than a dedicated line, keyboard focus and screen-reader behavior are not established by the renderer probe.

## Portable command sequence

Run from the repository root with locked dependencies. Use `bun run test`, not bare `bun test`: the script supplies the required timezone and browser conditions. Bound individual test/static/format commands to 120 seconds and install/build to 180 seconds; preserve exit status and report cleanup separately.

```sh
bun install --frozen-lockfile --ignore-scripts
bun run test ./src/test-support/token-host.test.ts
bun run test ./src/token-summary.test.ts
bun run test ./src/token-format.test.ts
bun run test ./src/test-support/layout-boundary.test.tsx
bun run test ./src/token-display.test.tsx ./src/tui.click.test.tsx
bun run test
bunx --no-install tsc --noEmit
bun run lint
bun run build
bunx --no-install prettier --check src/token-format.test.ts src/token-summary.test.ts src/token-display.test.tsx src/tui.click.test.tsx src/test-support/token-host.ts src/test-support/token-host.test.ts src/test-support/layout-boundary.test.tsx openspec/changes/toggle-token-display/tasks.md
git diff --check
```

Use run-isolated fixture directories and dispose renderer/subscriptions/database readers before removing them. The [Linux procedure](../../../docs/operations/linux-verification.md) describes the bounded disposable-container checks; supply an explicit candidate revision with its documented `-Revision` parameter.

## Validation limits and remaining host checks

Controlled clean-room checks cover the production renderer, coordinate clicks, selection and the synthetic recorder→store→notification→RPC-adapter→rendered chain. They do **not** prove a running OpenCode installation, real provider activity or a clean first-use workflow. A timing-sensitive backfill test can time out during fixture/storage work; a passing retry alone does not establish timing repeatability or root cause.

Real-host proof remains incomplete. A bounded, isolated supported-host procedure must establish:

1. Two independently mounted slots share selection; navigation/remount/reload retains it; exit/restart restores dollars while durable open state remains.
2. Actual RPC/schema handling accepts unchanged inputs, old dollar-only replies and new nested NULL/zero values without loss.
3. A separate empty installation/ledger starts at zero, activates receivers before normal supported model activity, refreshes both unit views and returns to identical dollars with no switch-induced accounting writes.

Keep first-use data separate from compatibility fixtures. Record finite command exits, readiness/time limits, assertion values, process teardown and cleanup independently. A clean-room build is not live-host, deployment or release proof. Changes to code, tests, dependencies or configuration require affected validation; documentation-only edits do not establish new software results.
