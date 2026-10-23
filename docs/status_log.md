# Status log

## 2026-10-23 — Dollar/token panel toggle

- User approved a clickable `$` / `Tokens` switch for the onscreen total and breakdowns, retaining dollar mode and leaving reporting tools unchanged.
- SDET verified clean target `main` at `ae05f0b69bacb0547a49873e8efd27f286b40a96` and created branch/worktree `toggle-token-display` under `.worktree/`; SDET retains lifecycle ownership.
- PM authored change proposal/product delta; UX authored change-local interaction specification. Product direction validated against user confirmation.
- Defaults: dollars on session start; selection shared by sidebar/footer during session. Existing history remains intact; missing token counts are identified rather than guessed.
- Next: establish source-backed token formula, author architecture, then SDET tests and SE implementation. No feature verification claimed.

## 2026-10-24 — Implemented; live-host verification pending

- Architecture confirmed all five recorded token components are disjoint in the supported OpenCode mapping. Boundary/decomposition reviewed and accepted after SDET corrections.
- SE implemented additive token summaries/RPC and clickable shared-session panel selector; dollars, agent tools, recording and history policies remain unchanged. Implementation/test candidate: `73f1f09bac9b306e2fce8c73f2bb1f38dfe95b19`.
- SDET corrected the loading-state test literal and test-owned SQLite handle leaks. Independent Windows and disposable Linux runs pass all 342 tests plus typecheck/lint/build/format gates; fixture/container cleanup passed. Durable verification evidence committed at `9d87c3e` in change tasks.
- DevOps prepared digest-pinned isolated Linux procedure. No real user settings, database or provider credentials used.
- Blocked: actual supported OpenCode host lifecycle/RPC and normal model-activity proof. No feature/release sign-off, sync/archive, PR or merge yet. Branch/worktree retained by SDET; model access or alternative scoped verification decision requires user authorization.

## 2026-10-24 — Global configuration switched to local fork

- User explicitly authorized scoped global server/CLI configuration edits and backups. General replaced the original plugin with `file:///C:/Users/User/work/projects/opencode-cmon-tokens/.worktree/toggle-token-display` in global `opencode.json`; removed the redundant original entry from `cli.json` so the package's `./tui` export loads automatically.
- Adjacent originals preserved as `opencode.json.bak-20261024-002701` and `cli.json.bak-20261024-002701`. JSON syntax/package exports verified; unrelated settings preserved. No credentials inspected, model calls made or services restarted.
- User should `/reload` and confirm the expanded panel offers `$` / `Tokens`. Actual runtime success remains unconfirmed. This worktree is now a global runtime dependency and must remain until configuration is repointed.
