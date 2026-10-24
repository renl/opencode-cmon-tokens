# opencode-cmon

opencode V2-only plugin that records opencode cost per calendar month (per agent, sub-agents included) in a local SQLite database and shows it in a collapsible TUI block.

- Runtime: V2 (`@opencode/plugin`) only. Server plugin `.` (`src/index.ts`, consumes events via `ctx.event.subscribe`) and TUI plugin `./tui` (`src/tui.tsx`, Solid/opentui); RPC in `src/rpc.ts`. The server plugin registers two read-only pinned Code Mode agent tools, `cost_report` and `cost_hotspots` (namespace `cmon`), via `ctx.tool.transform`; implemented in `src/tools.ts` over the pure logic in `src/analysis.ts`.
- Layout: `src/` with colocated `*.test.ts` (`store`, `recorder`, `backfill`, `pricing`, `summary`, `money`, `time`, `analysis`, `tools`), `script/build-tui.mjs`, `openspec/` specs.
- Commands (bun): `bun run test`, `bun run lint`, `bun run build` (`tsc` + TUI build to `dist/`). CI: `.github/workflows/ci.yml`.
- Gotcha: the `test` script sets `TZ=Europe/Berlin` and `--conditions=browser`; run tests through the script, not bare `bun test`.
- Usage and install: see `README.md`.

## Current Work

- Change: `toggle-token-display` — clickable dollar/token panel selector; dollar reporting and agent tools preserved.
- State: compact k/M/B counts and narrow-sidebar control correction implemented; all 381 tests and static/build checks pass independently on Windows and clean Linux. User confirmed earlier panel works after correcting local load path to `dist`; corrected layout awaits visual confirmation. No full feature/release sign-off or PR yet.
- Target: `main`; branch: `toggle-token-display`; worktree: `.worktree/toggle-token-display` (SDET lifecycle owner).
- Artifacts: [proposal](openspec/changes/toggle-token-display/proposal.md), [product delta](openspec/changes/toggle-token-display/specs/cost-display/spec.md), [UX](openspec/changes/toggle-token-display/ux.md).
- Ownership: PM authors `cost-display` product spec; Architect owns change design/contracts; SDET owns tasks/tests. One change, one PR; user merges.
- Evidence: presentation candidate `6ff10b39178bd1ce9ca5acb5080c049de1e08406`, independent verification `e8eb17a`; one original native backfill timeout retained in evidence, targeted/full unchanged retries passed. [Tasks and evidence](openspec/changes/toggle-token-display/tasks.md); [Linux procedure](docs/operations/linux-verification.md). Live model access requires separate authorization.
- History: [status log](docs/status_log.md).
- Global install: standalone clone at `C:\Users\User\.local\share\opencode\plugins\opencode-cmon-tokens`, branch `toggle-token-display` at `73366cf114fab92f6b44311c5e17536517508924`; locked install/build passed. Global config now references that clone, not this worktree. Worktree remains active for unmerged feature; runtime reload still needs user confirmation.
- Publication: [feature branch and installation README](https://github.com/renl/opencode-cmon-tokens/tree/toggle-token-display). No PR/merge; `main` unchanged. Subsequent status-only commits need not update installed code.

## Scoped installation reference

- User authorized permanent installation, global repointing, README updates, commit and push of `toggle-token-display` (not merge).
- External install scope: `C:\Users\User\.local\share\opencode\plugins\opencode-cmon-tokens` only; inspect/create standalone clone, install locked dependencies, build/validate this fork. Do not inspect siblings or overwrite unrelated contents.
- External config scope: read/edit `C:\Users\User\.config\opencode\opencode.json`, `opencode.jsonc`, `cli.json`, creating adjacent timestamped backups before changes. Preserve unrelated settings; no credential access, global scanning or live model calls.
