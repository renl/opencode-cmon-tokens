# Monthly usage unit selection

Define panel behavior for retaining dollars alongside a token view.

- **Status:** Accepted product scope, including user-authorized compact-formatting and narrow-sidebar readability correction; PM is primary author.
- **Parent:** [Proposal and direction check](../../proposal.md).
- **Covered outcomes:** Unit selection, comparable breakdowns, honest token coverage, compact amounts and readable narrow controls.
- **Decision needed:** None; no additional user sign-off. Existing source-grounded counting obligations remain unchanged.
- **Read next:** Architect's subsequent contract; no wire format is prescribed here.

## MODIFIED Requirements

### Requirement: Cost block is collapsed by default

The TUI SHALL render in `sidebar.content` and `home.footer.status` a block that is wrapped by default, with glyph `▶` when wrapped and `▼` when opened. The collapsed block SHALL show the monthly total in the selected unit; dollars SHALL be the default unit.

#### Scenario: Default wrapped sidebar

- **WHEN** a new TUI session renders with a monthly dollar total of 12.34
- **THEN** the sidebar shows `▶ This month: $12.34` and no breakdown lines

#### Scenario: Footer uses the same glyphs

- **WHEN** the footer renders wrapped and then opened in either unit
- **THEN** it starts with `▶` when wrapped and `▼` when opened

### Requirement: Opened block shows cost per agent

When opened, the sidebar SHALL list each agent with its monthly amount in the selected unit while the agent breakdown is selected. Entries SHALL be ordered by that unit's amount descending, then name for ties. The home footer SHALL stay on one line showing the selected-unit total, the top two agents by that unit and `+N` for the rest.

#### Scenario: Opened sidebar

- **WHEN** the block is opened with the agent breakdown selected
- **THEN** agents are listed by the selected unit's amount descending, then name

#### Scenario: Opened footer stays one line

- **GIVEN** three agents with available usage in the selected unit
- **WHEN** the footer is opened
- **THEN** it shows the total, the top two agents and `+1` on one line

### Requirement: Loading and error states never break the host

The TUI SHALL show `…` while loading and `Error` in the theme's error colour when the summary request fails, without throwing. With no rows, it SHALL show `$0.00` in dollars or `0 tokens` in tokens, with an empty breakdown. Missing token information SHALL be an unavailable-data state, not a request error.

#### Scenario: Request failure

- **WHEN** the summary request fails in either unit
- **THEN** the block shows `Error` in the error colour without crashing the host

### Requirement: Incomplete pricing is flagged

The summary SHALL report `complete: false` when a row that could carry a cache-write cost has unknown token counts or no priced catalog entry, SHALL reload the catalog (at most once per minute) when such a model is missing, and the TUI SHALL prefix the dollar-mode total with `~` when pricing is incomplete. Token-mode completeness SHALL instead follow token availability.

#### Scenario: NULL tokens mark the summary incomplete

- **GIVEN** a Copilot Claude row with NULL token counts
- **WHEN** the summary is built
- **THEN** `complete` is false and the row adds no cache-write cost

#### Scenario: An unpriced model marks the summary incomplete

- **GIVEN** a Copilot Claude row with cache-write tokens whose model has no priced catalog entry
- **WHEN** the summary is built
- **THEN** `complete` is false and a catalog reload is requested

#### Scenario: Reloads are rate-limited

- **WHEN** summaries keep finding an unpriced model
- **THEN** the catalog is reloaded at most once per minute

#### Scenario: A hanging catalog never stalls the summary

- **WHEN** the catalog load does not finish
- **THEN** the summary is served from the cached catalog without waiting

#### Scenario: Incomplete dollar total is marked

- **WHEN** the TUI renders an incomplete pricing summary in dollar mode
- **THEN** the total is shown as `~$12.34` and agent and model lines carry no marker

#### Scenario: Complete dollar total is unmarked

- **WHEN** the TUI renders a complete pricing summary in dollar mode
- **THEN** the total has no `~`

#### Scenario: Change notifications are debounced

- **WHEN** several changes occur within 500 ms
- **THEN** one `changed` event is emitted

## ADDED Requirements

### Requirement: Clickable unit selection retains both views

The opened, ready sidebar SHALL offer separate clickable `$` and `Tokens` choices. The selected choice SHALL be bracketed and bold, so it is distinguishable without colour. These controls SHALL be non-text-selectable; amounts and breakdown content SHALL remain selectable. The unit selector SHALL be absent when collapsed, loading or in error.

#### Scenario: Switch both directions without other state changes

- **GIVEN** an opened sidebar with Models selected and dollars active
- **WHEN** Tokens is clicked and then $ is clicked
- **THEN** the total and model amounts switch to tokens and back to the original dollar values, while Models stays selected and the block remains open

#### Scenario: Active selection and non-control clicks

- **WHEN** the active unit choice, selector label or spacing is clicked
- **THEN** neither the unit nor the open/closed state changes

### Requirement: Narrow-sidebar controls remain readable

At an available sidebar content width of 45 character cells, the opened, ready panel SHALL keep every unit and breakdown choice readable, identifiable and clickable in both dollar and token modes. Control labels and individual choices SHALL NOT break midword, overlap or interleave with other controls. Selected-state brackets SHALL stay with their choice. Breakdown names and amounts SHALL remain visually distinct without overlap; each amount SHALL remain intact. UX SHALL determine the exact layout and treatment of long names, rather than preserving a layout that fragments labels.

#### Scenario: Readable controls and amounts in a narrow sidebar

- **GIVEN** a ready sidebar with 45 character cells of content width and token amounts in the millions and billions
- **WHEN** the user opens the panel and switches between dollar/token units and agent/model/provider breakdowns
- **THEN** all choices remain readable and operable, no control word splits across lines, selected choices remain identifiable, and each displayed amount stays intact and separate from its name

### Requirement: Unit choice is shared for the current TUI session

The unit SHALL default to dollars on every TUI restart, without altering persisted open/closed state. A unit change SHALL apply to both sidebar and footer, survive refresh, navigation and collapse/reopen within the session, and leave breakdown selection independent.

#### Scenario: Retain the choice until restart

- **GIVEN** Tokens is selected
- **WHEN** the panel refreshes, collapses, reopens or the user navigates to the home view
- **THEN** its available total and breakdown values remain in tokens

#### Scenario: Restart restores dollar mode

- **GIVEN** Tokens was selected before restarting the TUI
- **WHEN** the TUI restarts
- **THEN** dollars are selected and the existing persisted open/closed preference is retained

### Requirement: Token mode measures usage without double counting

Tokens SHALL represent recorded prompt usage, including cached prompt usage, plus generated usage, including reasoning, with overlapping categories counted only once. Counts SHALL NOT be inferred from prices or dollar amounts. The Architect SHALL establish the field-level formula from supported source evidence before implementation; this requirement does not assume cache categories or reasoning are additive to input or output.

The token view SHALL cover the same monthly rows and attribution as the dollar view, including recorded sub-agent, failed-step and compaction usage. Each agent/model/provider grouping SHALL sum the same known usage, with each grouping's amounts summing to the known monthly total. Models SHALL retain existing merging across providers. Each breakdown SHALL sort by token amount descending, then name, independently of dollar order. Existing cost-labelled breakdown behavior SHALL apply to dollars; in token mode the same breakdown controls SHALL show token amounts and ordering instead.

#### Scenario: Token ranking differs from dollar ranking

- **GIVEN** agent A has more dollars but fewer tokens than agent B
- **WHEN** Tokens is selected
- **THEN** B precedes A in the sidebar and footer ranking; selecting $ restores dollar ranking

#### Scenario: All breakdowns reconcile

- **GIVEN** complete token counts for the month's rows
- **WHEN** Agents, Models and Providers are selected in turn
- **THEN** each list sums to the same token total with no repeated cache or reasoning usage

### Requirement: Token formatting and incomplete history are explicit

All token amounts in the sidebar and home footer, including collapsed totals and every breakdown, SHALL use the same compact decimal formatting with no dollar sign. Counts below 1,000 SHALL remain exact whole numbers. Larger counts SHALL use `k` for thousands (1,000), `M` for millions (1,000,000) and `B` for billions (1,000,000,000); `B` means billion, not million. Choose the largest applicable suffix, round its scaled value to at most two fractional digits (nearest, halfway rounded up), and remove trailing fractional zeroes and any trailing decimal point. If rounding produces `1000k` or `1000M`, promote to the next suffix and round there instead. `B` is the highest suffix; larger amounts remain expressed in billions. Use a decimal point, no digit-grouping separators, and a space before the unit label: `1 token` for exactly one, otherwise `tokens` (including abbreviated amounts). This supersedes the earlier exact-whole-count display requirement.

Formatting SHALL NOT change recorded counts, computed totals, aggregation, ranking, dollar values or reporting tools. Reconciliation and ranking SHALL use underlying counts, not rounded display strings; independently rounded displayed breakdown amounts need not sum exactly to the displayed total. Rounding alone SHALL NOT add a partial-coverage marker.

Available non-overlapping counts SHALL contribute to a known subtotal even when other counts are missing. If any counts needed for a full total are unknown, the total SHALL have a `~` prefix and the opened sidebar SHALL explain `Partial: some token counts unavailable`. Affected breakdown amounts SHALL also carry `~`.

If no token counts are available for existing rows, the affected total or breakdown amount SHALL instead say `Tokens unavailable`, not zero. An older server with no token summary SHALL receive the same unavailable treatment without throwing. Completeness SHALL follow token availability, not pricing availability: existing pricing-completeness indicators SHALL continue unchanged in dollar mode and SHALL NOT alone mark token mode incomplete. Token mode SHALL NOT write guessed counts into historical rows.

#### Scenario: Partially known history

- **GIVEN** some monthly usage is known and some required counts are unknown
- **WHEN** Tokens is selected
- **THEN** the known subtotal and affected breakdown subtotals have `~`, and the opened sidebar explains the missing counts

#### Scenario: Compact formatting is consistent across panel locations

- **WHEN** available counts are displayed in a sidebar or footer total or breakdown
- **THEN** they follow these examples:

| Recorded count | Display |
| --- | --- |
| 0 | `0 tokens` |
| 1 | `1 token` |
| 999 | `999 tokens` |
| 1,000 | `1k tokens` |
| 1,234 | `1.23k tokens` |
| 1,235 | `1.24k tokens` |
| 1,200 | `1.2k tokens` |
| 999,994 | `999.99k tokens` |
| 999,995 | `1M tokens` |
| 999,995,000 | `1B tokens` |
| 590,977,798 | `590.98M tokens` |
| 1,578,717,226 | `1.58B tokens` |

#### Scenario: Rounding does not change ranking or imply missing history

- **GIVEN** complete counts of 1,234 and 1,233 for two breakdown entries
- **WHEN** Tokens is selected
- **THEN** both display `1.23k tokens` without `~`, but the entry with 1,234 ranks first regardless of name

#### Scenario: Compact partial subtotal retains its marker

- **GIVEN** a known subtotal of 1,578,717,226 with some required counts unknown
- **WHEN** Tokens is selected
- **THEN** the total displays `~1.58B tokens`, affected breakdown amounts retain `~`, and the partial-history explanation remains visible

#### Scenario: All counts unavailable or older server

- **GIVEN** existing monthly rows but no available token counts, or a server without token summary support
- **WHEN** Tokens is selected
- **THEN** the total says `Tokens unavailable`, the host does not crash, and switching to $ still shows the unchanged dollar amounts

#### Scenario: Unknown prices do not imply unknown tokens

- **GIVEN** all token counts are known but the dollar total is marked incomplete for missing pricing
- **WHEN** Tokens is selected
- **THEN** the token total is unmarked; switching to $ restores its existing pricing marker

### Requirement: First useful usage requires no manual setup

On a clean installation with no recorded or imported history, the existing supported recording path SHALL suffice to populate both views. Switching units SHALL neither create nor delete accounting rows. Existing retention and historical repair policies SHALL remain unchanged.

#### Scenario: First usage from an empty installation

- **GIVEN** a clean installation with no history
- **WHEN** the user opens the panel, selects Tokens, then completes normal model activity carrying token counts
- **THEN** the panel initially shows `0 tokens` with no breakdown and no missing-data warning, then shows the recorded usage on the normal refresh path; selecting $ shows that activity's unchanged cost

## Related Artifacts

- [Proposal, authority and source-evidence handoff](../../proposal.md)
- [Current cost-display specification](../../../../specs/cost-display/spec.md)
