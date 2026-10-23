# Toggle token display

Keep monthly dollar reporting and let users inspect token usage in the same panel.

- **Status:** Accepted product scope; ready for downstream elaboration. Source-grounded token formula remains an implementation blocker.
- **Workflow / authority:** `software-change`, product specification stage; user explicitly confirmed direction and implementation scope, as supplied by Chief of Staff. Safe minimal defaults below require no additional user sign-off.
- **Parent:** [Current cost-display capability](../../specs/cost-display/spec.md).
- **Covered outcomes:** Switch units without losing dollar reporting; honest historical token coverage.
- **Decision needed:** No unresolved product decision. Architect must establish token field semantics from source evidence before implementation.
- **Read next:** [Product behavior delta](specs/cost-display/spec.md).

## Why

Dollars describe spend, but users also need to compare monthly token usage across agents, models and providers without leaving the usage panel or losing the existing cost view.

## Direction Check

- **Subject:** The onscreen usage panel; **desired outcome:** clickable `$` / `Tokens` selection changes the total and breakdowns.
- **Problem:** Retain both views, rather than replace dollar reporting or change reporting tools. This change serves that panel and preserves dollar accounting.

## What Changes

- Add a clickable unit selector to the opened, ready sidebar. Its selection applies to the sidebar and home footer totals and breakdown amounts, including when collapsed.
- Start each TUI session in dollars. Keep the selection during refresh, collapse/reopen and navigation within that session; do not persist it across restart. This matches the existing session-only breakdown choice and avoids introducing a saved preference.
- Show exact, clearly labelled token counts, sorted by tokens in token mode; mark incomplete historical coverage separately from incomplete pricing.
- Preserve historical rows and all existing dollar results. A new installation can start at zero and acquire usage through normal recorded model activity, without manual data setup.

## User Stories

- As a plugin user, I want to switch between dollars and tokens, so that I can compare spend and usage without losing either view.
- As a user with older history, I want unavailable token counts distinguished from zero, so that I do not mistake missing data for low usage.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `cost-display`: unit selection, token totals and existing agent/model/provider breakdowns, formatting and coverage feedback.

## Impact and Non-goals

- One coherent change, delivered as **one PR**, including implementation, verification and authorized finalization.
- No changes to `cost_report`, `cost_hotspots`, dollar calculation/pricing, recording policy, retention, historical repair policy or unrelated refactors. No token-type drilldown, new reporting filters or user-managed data setup.
- Existing monthly range, attribution, refresh, retry, collapse behavior and footer's one-line/top-two-agent layout remain in force.

## Ownership and Handoff

- PM is primary author of this `proposal.md` and `specs/cost-display/spec.md` product delta. Architect owns any subsequent `design.md` and public/cross-component contracts; SDET owns subsequent tasks/tests. No baseline spec edits are part of this dispatch. CoS should reflect this file ownership in the project index.
- Before implementation, Architect must establish from the supported OpenCode source whether cached input overlaps input and reasoning overlaps output, for live and historical records. Existing ledger field names alone do not establish those semantics. Record the non-double-counting formula and missing-field rules in the contract; return to PM if this changes the product definition or requires recording changes.
- Product scope is accepted for downstream UX/Architect elaboration through CoS; no second user sign-off gate is required. Implementation remains blocked on the source-grounded formula above. No agents are dispatched here.

## Related Artifacts

- [Product acceptance criteria](specs/cost-display/spec.md)
- [Existing token recording behavior](../../specs/cost-recording/spec.md)
- [Existing history/retention behavior](../../specs/cost-retention/spec.md)
- Source evidence inspected: `src/tui.tsx`, `src/types.ts`, `src/summary.ts`, `src/rpc.ts`, `src/store.ts`; counts exist in the ledger, but the current panel summary contains dollar amounts only.
