# opencode-cmon

opencode V2-only plugin that records opencode cost per calendar month (per agent, sub-agents included) in a local SQLite database and shows it in a collapsible TUI block.

- Runtime: V2 (`@opencode/plugin`) only. Server plugin `.` (`src/index.ts`, consumes events via `ctx.event.subscribe`) and TUI plugin `./tui` (`src/tui.tsx`, Solid/opentui); RPC in `src/rpc.ts`. The server plugin registers two read-only pinned Code Mode agent tools, `cost_report` and `cost_hotspots` (namespace `cmon`), via `ctx.tool.transform`; implemented in `src/tools.ts` over the pure logic in `src/analysis.ts`.
- Layout: `src/` with colocated `*.test.ts` (`store`, `recorder`, `backfill`, `pricing`, `summary`, `money`, `time`, `analysis`, `tools`), `script/build-tui.mjs`, `openspec/` specs.
- Commands (bun): `bun run test`, `bun run lint`, `bun run build` (`tsc` + TUI build to `dist/`). CI: `.github/workflows/ci.yml`.
- Gotcha: the `test` script sets `TZ=Europe/Berlin` and `--conditions=browser`; run tests through the script, not bare `bun test`.
- Usage and install: see `README.md`.

## Current Work

- Change: `toggle-token-display` — clickable dollar/token panel selector; dollar reporting and agent tools preserved.
- State: implemented; all 342 tests and static/build checks pass independently on Windows and in a clean Linux container. Live OpenCode lifecycle/RPC/model-activity verification remains blocked; no feature/release sign-off or PR yet.
- Target: `main`; branch: `toggle-token-display`; worktree: `.worktree/toggle-token-display` (SDET lifecycle owner).
- Artifacts: [proposal](openspec/changes/toggle-token-display/proposal.md), [product delta](openspec/changes/toggle-token-display/specs/cost-display/spec.md), [UX](openspec/changes/toggle-token-display/ux.md).
- Ownership: PM authors `cost-display` product spec; Architect owns change design/contracts; SDET owns tasks/tests. One change, one PR; user merges.
- Evidence: code/test candidate `73f1f09bac9b306e2fce8c73f2bb1f38dfe95b19`; subsequent changes are documentation/verification procedure only. [Tasks and evidence](openspec/changes/toggle-token-display/tasks.md); [Linux procedure](docs/operations/linux-verification.md). Live model access requires separate authorization.
- History: [status log](docs/status_log.md).
- Local runtime dependency: user authorized global configuration to load this package directory. Original entries backed up and replaced in global server config; redundant TUI entry removed. Retain this worktree until global configuration is repointed; do not treat it as disposable after landing. Runtime reload still needs user confirmation.

## Scoped installation reference

- User authorized permanent installation, global repointing, README updates, commit and push of `toggle-token-display` (not merge).
- External install scope: `C:\Users\User\.local\share\opencode\plugins\opencode-cmon-tokens` only; inspect/create standalone clone, install locked dependencies, build/validate this fork. Do not inspect siblings or overwrite unrelated contents.
- External config scope: read/edit `C:\Users\User\.config\opencode\opencode.json`, `opencode.jsonc`, `cli.json`, creating adjacent timestamped backups before changes. Preserve unrelated settings; no credential access, global scanning or live model calls.
