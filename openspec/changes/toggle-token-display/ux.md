# Monthly usage selector — UX reference

- **Owner:** `@ux-ui-designer`; workflow: `software-change`, UX specification stage.
- **Parent / behavior authority:** [Proposal](proposal.md), [product delta](specs/cost-display/spec.md).
- **Scope:** Existing terminal sidebar and home footer only; retain host theme, dollar formatting, recording, tools, refresh/retry and persisted open/closed behavior. This is the change-local, separately owned UX reference; architecture should link here rather than copy it.
- **Read next:** Architect's source-grounded token formula and summary contract (pending). No formula is defined here.
- **Inputs:** `src/tui.tsx`, `src/tui.test.ts`, `src/tui.click.test.tsx`. No `docs/ux-ui-spec/README.md` exists in this worktree; this dispatch authorizes only this file, not a new documentation directory.

## Layout and hierarchy

Keep the block first in the sidebar. Header remains `▶ This month: $12.34` when collapsed, `▼` when opened. Only the amount changes units. Keep the current two-column indent beneath the header.

In the opened, ready sidebar, place a compact **Unit** group immediately after the existing **View** group, in reading order. Example when sufficient inner width is available:

```text
▼ This month: 1,234,567 tokens
  View  [Agents]  Models  Providers    Unit  $  [Tokens]
  build                             1,000,000 tokens
  explore                             234,567 tokens
```

- Use two spaces between segments, four between groups; no surrounding panel, icons or new decorative treatment. Preserve existing `View` labels verbatim.
- Active choice is bracketed **and bold**: `[$]` or `[Tokens]`. Inactive choice is bare `$` or `Tokens`. Reuse existing action text styling for controls, base text for header amounts and muted text for breakdowns. Selection must remain clear in monochrome.
- Both groups precede any coverage explanation, then breakdown rows. No selector in the footer or collapsed block.
- Keep amounts right-aligned when each label and complete amount fit on one row; truncate long breakdown names before sacrificing amount space.

## Width adaptation (terminal columns, not pixel breakpoints)

- **Both groups fit:** use the shared control row above. Measure the full groups including brackets and indent; reserve enough room for either active choice so selecting a unit does not make the layout jump.
- **Groups do not fit together:** move the entire Unit group to its own indented row immediately below View. At a 40-column sidebar this is the expected layout. Do not squeeze labels or reduce the existing inter-choice gaps.
- **A group itself does not fit:** wrap at segment boundaries, preserving order, indent and complete clickable choice labels. At 22 columns, all controls must remain reachable on continuation rows; no horizontally clipped choice.
- **Header amount does not fit:** retain glyph and `This month:` on the first line; move the complete amount to an indented continuation line. This also applies when collapsed. Preserve the existing single-line dollar header at 22 columns when it fits.
- **Breakdown amount does not fit beside a useful name:** use a name line followed by an indented amount line. Wrap `tokens` onto a continuation line if needed. If even the numeric string exceeds available width, hard-wrap it without removing/reordering digits, commas or `~`. Never substitute K/M notation, round, or ellipsize sidebar amounts. Coverage text wraps normally.
- Footer retains its existing **single line with trailing truncation** at the available host width; do not enlarge it. Construct exact counts before clipping, with total first. Narrow-footer clipping is not numeric abbreviation; the expanded sidebar is where full values remain readable and selectable.

## Interaction and session state

1. Start each TUI session in dollars; existing stored open/closed state remains unchanged. On an opened ready sidebar, show `Unit  [$]  Tokens`.
2. Clicking an inactive unit updates the header, current breakdown and footer immediately from available summary data. Keep the block open and the current Agents/Models/Providers choice unchanged. Selecting Tokens also applies token ordering; selecting dollars restores dollar ordering and values.
3. Keep one shared unit choice for both slots throughout refresh, navigation and collapse/reopen, including if a slot remounts. Do not store this preference across restart. Breakdown choice remains independent and does not change footer grouping.
4. Clicking the active unit, `Unit`, `View`, or control-row whitespace does nothing. Consume control-group mouse events so they cannot trigger collapse or any ancestor action. Only each choice's rendered text, including active brackets, is its click target; gaps are not targets. One click produces at most one change.
5. Header and footer retain their current collapse interaction. Unit changes do not create a notification, confirmation, spinner or extra request requirement.
6. Selector chrome is not text-selectable, like existing View controls. Amounts, breakdown names and coverage explanation remain selectable; dragging over them must not select selector text or change the unit.

## Values and feedback states

| State | Sidebar and footer amount | Opened sidebar detail |
|---|---|---|
| Loading | `…`, same glyph/open state | Hide both control groups and breakdowns. Retain the session unit internally. |
| Request error | `Error`, existing error text colour | Hide both control groups and breakdowns. Existing automatic retries remain; no new retry control. Recovery restores selected unit and breakdown. |
| Ready, complete tokens | `1,234 tokens` | Unit selector available; every breakdown amount includes `tokens`, including `1 tokens` to keep the specified fixed label. |
| Ready, partially known tokens | `~1,234 tokens` | Show `Partial: some token counts unavailable` immediately below controls. Prefix only affected breakdown subtotals with `~`; unaffected entries stay unmarked. |
| Existing usage, no available counts | `Tokens unavailable` | Keep selector available so dollars remain reachable. Affected breakdown values use `Tokens unavailable`, never `0 tokens`. Show the same partial-coverage explanation; no request-error styling. |
| Older server without token summary | `Tokens unavailable` | Same unavailable treatment. Do not invent missing breakdown entries or throw; returning to dollars restores existing usable content. |
| Empty month, first run or after retention/month rollover | `$0.00` or `0 tokens` | Empty breakdown, selectors available, no partial warning. Normal model activity populates first-run usage through the existing recording and refresh path; no setup form or disabled primary action. |
| Dollar mode | Existing dollar values and total-only pricing `~` | No token-coverage warning or token markers. Unknown pricing alone must not mark complete token counts partial. |

Unavailable/partial token history is a ready state, not a failed request. Token counts are exact grouped whole numbers; examples are illustrative, not formula definitions. No success toast: updated amounts, order and selected brackets provide feedback.

## Footer

- Closed example: `▶ 1,234 tokens this month`.
- Open example: `▼ 1,234 tokens · build 1,000 tokens · explore 200 tokens · +1`.
- Always use the selected unit for total and agent amounts, and that unit's top two agents, regardless of sidebar breakdown choice. Retain existing separators, `+N`, glyph and open-state sharing. Apply partial/unavailable formatting per value; keep the explanatory sentence in the sidebar only.

## Terminal accessibility and control states

- Preserve readable plain-text labels and exact selectable amounts. Brackets/bold convey selection without colour; `Error`, `~` and the coverage sentence carry status without colour. Use host theme roles, not hard-coded colours; verify text contrast against the host background (AA target 4.5:1). No animation or hover-only information.
- **Hover / pressed:** retain the existing View controls' stable text styling; no layout shift or transient unit change. **Selected:** bracketed/bold. **Unavailable controls:** omitted during loading/error rather than misleadingly disabled; available in empty/partial/unavailable ready states.
- Current supplied controls are mouse-driven terminal text, not native focusable widgets: no plugin tab stops, keyboard shortcut, browser ARIA or live-region mechanism is evidenced in the inspected UI. Preserve host keyboard handling; do not hijack Tab or typing or claim screen-reader/keyboard compliance. Reading order is header → View choices → Unit choices → coverage → breakdowns.
- If a supported native host focus path is available, reuse it: follow that reading order, show a visible focus indicator distinct from selection, activate choices with Enter/Space, and retain focus on the activated choice. Do not silently introduce a new navigation system. Architect must record any remaining keyboard/screen-reader limitation; full WCAG compliance is not established by this mouse-only change. Terminal cell targets cannot promise a 44px touch target; touch-browser affordances are outside this scope.

## Review / handoff

Verify both switch directions, active/label/gap clicks, text dragging, shared footer mode across navigation, restart defaults, 40- and 22-column controls, multi-line exact counts, differing dollar/token ranking, every feedback row above, and recovery without losing the unit choice. Existing dollar and tool behavior must remain unchanged.

**Implementation blocker carried forward:** Architect must establish non-double-counting token semantics and missing-field rules from supported source evidence. **Accessibility limitation:** the inspected plugin provides no keyboard/focus or screen-reader contract; do not represent this reference as proof of AA conformance. No additional product decision is introduced here.
