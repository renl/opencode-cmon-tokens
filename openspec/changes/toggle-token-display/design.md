# Monthly token display — architecture contract

Add a read-only token projection to the existing summary and a session-only unit choice, without changing dollar accounting.

- **Parents:** [Proposal](proposal.md), [product delta](specs/cost-display/spec.md), [current capability](../../specs/cost-display/spec.md).
- **UI authority:** [UX reference](ux.md). Layout, wrapping, control hit targets and accessibility limitations remain defined there.
- **Related:** [Tasks and verification evidence](tasks.md).

## Boundaries and compatibility

| Boundary | Contract |
|---|---|
| Ledger → summary | Read the five nullable token columns for every row in the requested range, preserving each component's availability. Aggregate in the same database read snapshot as dollar summary inputs. |
| Summary builder → RPC | Compute token totals independently of prices and cache-write dollar adjustments; attach the additive `tokens` object below. |
| RPC → TUI | One summary response supplies both units. Switching units changes local presentation only; no request, write, catalog load or change event is required. |
| TUI slots → shared state | Sidebar and footer share one session unit; persisted open state and sidebar breakdown choice remain independent. |

The system shall retain RPC id `cmon`, method `summary`, input `{from: number, to: number}` (UTC epoch milliseconds, half-open `[from,to)`), and event `changed({revision: number})`. It shall retain all existing response fields, dollar values, dollar ordering, pricing completeness and refresh/retry/debounce semantics. There is no new route, RPC method, event or tool.

Neither `cost_report` nor `cost_hotspots`, their schemas, outputs or token interpretations shall change. Database/schema version, recording behavior, historical interpretation, retention and repair policy shall remain unchanged.

## Verified token meaning

The five **stored** fields are disjoint categories, not the provider's inclusive raw input/output totals:

| Ledger column | OpenCode normalized field | Meaning |
|---|---|---|
| `tokens_input` | `tokens.input` | Non-cached prompt tokens |
| `tokens_cache_read` | `tokens.cache.read` | Cached prompt tokens read |
| `tokens_cache_write` | `tokens.cache.write` | Prompt tokens written to cache |
| `tokens_output` | `tokens.output` | Visible, non-reasoning generated tokens |
| `tokens_reasoning` | `tokens.reasoning` | Reasoning generated tokens |

For a complete row, token usage shall equal the sum of these five columns once each. Do not subtract cache tokens from stored input or reasoning from stored output, or add an upstream `totalTokens` to that sum. Example: input 100, cache-read 200, cache-write 300, output 40, reasoning 60 yields **700 tokens**. Cache-write dollar surcharges add no tokens.

### Source evidence

Token semantics are grounded in the following sources for the lock-resolved OpenCode packages at **2.0.24**:

1. [Core `SessionUsage.tokens`, `record`, `add`](https://cdn.jsdelivr.net/npm/@opencode/core@2.0.24/dist/chunks/repository-tdstcens.js): input maps from `nonCachedInputTokens`, output from `visibleOutputTokens`, reasoning and both cache fields map separately through `safe`; `safe` normalizes missing/nonfinite/negative values to zero. `add` accumulates each normalized category separately.
2. [Schema `TokenUsage.total`](https://cdn.jsdelivr.net/npm/@opencode/schema@2.0.24/dist/token-usage.js): explicitly sums input, output, reasoning, cache-read and cache-write.
3. [AI `Usage.visibleOutputTokens`](https://cdn.jsdelivr.net/npm/@opencode/ai@2.0.24/dist/schema/events.js): computes `max(0, outputTokens - reasoningTokens)` upstream, before core stores normalized output. This subtraction must not be repeated over the ledger.
4. [V2 CLI plugin API](https://opencode.ai/v2/docs/build/plugins/cli): documents shared memory storage that survives plugin reload and is discarded on TUI exit, versus durable storage that survives restart. [V2 RPC API](https://opencode.ai/v2/docs/build/plugins/rpc) documents additive JSON Schema definitions and existing registration/client/event mechanisms. [Plugin overview](https://opencode.ai/v2/docs/build/plugins) confirms server/CLI separation and lifecycle.

Local reference paths inspected: `src/recorder.ts` copies normalized event tokens; `src/backfill.ts` reads the same normalized `session_message.data.tokens` fields; `src/store.ts` persists their columns. Existing `src/index.ts` + `src/rpc.ts` + `src/tui.tsx` demonstrate the server/client pattern; `src/tui.click.test.tsx` demonstrates real renderer mouse and selection tests. These are existing integration patterns, not new host interfaces.

**Evidence limit:** completeness means availability in the retained ledger, not independent proof of provider billing accuracy. Core normalization and existing ingestion/repair can already have zero-filled missing data. In particular, `runTokenFill` can write input/cache zeros after successful source reads find no message or token object; imports also default missing input/cache fields to zero. Such zeros cannot now be distinguished from measured zero. The new read shall treat stored zero as known, shall not claim to recover that lost provenance, and shall not change those writers. Source evidence establishes the supported normalized shape; it does not prove every historical row originated under 2.0.24.

## Availability and aggregation invariants

For each row and independently for every total/group:

- A non-NULL component, including zero, is known. A NULL component is unknown, not zero for availability purposes.
- The known subtotal sums only non-NULL components. A row with some known components contributes those components even if another component is NULL.
- `complete` is true exactly when every component of every included row is known. For an empty row set it is true.
- A nonempty row set with no known components has `totalTokens: null` and `complete: false`. Any known component, including a known zero, yields a numeric subtotal. Thus a partially known zero is `0` with `complete: false`, not unavailable.
- An empty month has numeric `0`, `complete: true`, and empty breakdown arrays. It is distinct from existing rows with no counts.

The token projection shall read raw nullable columns or an equivalent lossless aggregate. It shall **not** reuse the pricing candidate subset (Copilot/cache-write only), or a row mapper that turns NULL input/cache into zero or discards known components when cache-write is NULL. Existing `summaryInputs` and `toCostRow` contain such pricing-oriented transformations; leave their dollar/tool behavior intact while supplying lossless token inputs.

Include exactly the same retained range rows as dollar aggregation, regardless of cost, provider, kind, failed status, parent session or pricing availability. Include recorded sub-agents, failed steps, compactions, zero-cost rows and `unknown` attribution; do not manufacture unrecorded activity. Group once by `agent`, once by `model_id` (merged across providers), and once by `provider_id`, using the ledger's existing names without re-attribution.

Each grouping shall contain one entry for every distinct group represented by rows, including zero and unavailable groups. Each list's numeric known subtotals, treating unavailable entries as adding no known amount, shall sum to the monthly numeric known subtotal. If the monthly total is unavailable, every group is unavailable. Compute group completeness from that group's rows, not the monthly flag. Pricing completeness shall never determine token completeness.

## Additive summary / RPC schema

The existing response fields `revision`, `totalMicros`, `agents`, `models`, `providers` and `complete` keep their meanings and existing required/optional status. New servers shall always include `tokens`; its top-level RPC schema property and consumer type shall be **optional** so older servers remain accepted. Within a present `tokens` object all fields below are required:

| Field | Shape / meaning |
|---|---|
| `tokens.totalTokens` | Nonnegative whole-number count or `null`; known subtotal or entirely unavailable, per rules above |
| `tokens.complete` | Boolean; token availability only |
| `tokens.agents` | Array of `{agent: string, totalTokens: number or null, complete: boolean}` |
| `tokens.models` | Array of `{model: string, totalTokens: number or null, complete: boolean}` |
| `tokens.providers` | Array of `{provider: string, totalTokens: number or null, complete: boolean}` |

All entry fields are required. Counts shall remain exact whole counts in storage, summary and serialization; presentation alone shall use the compact formatting below. No rounded/scaled values shall enter accounting, aggregation, RPC or ranking. This extends the existing numeric transport; no token-category drilldown is exposed. `tokens.complete: true` forbids a NULL total or incomplete entries. A group's NULL subtotal requires its `complete: false`.

The summary shall return token arrays separately from dollar arrays; it shall not reorder/mutate dollar arrays or add markers into monetary fields. Sort token lists by numeric known subtotal descending, unavailable after all numeric values (including zero), then **binary ascending name order** for equal values or two unavailable values, matching existing dollar name comparison. Completeness is not an additional tie-breaker. Footer ranking shall use `tokens.agents`, never dollar order, for its top two and `+N`.

### Legacy response handling

If `tokens` is absent, token mode remains ready: total is `Tokens unavailable`, the sidebar shows the coverage explanation, and existing dollar values stay usable. For the selected breakdown, existing dollar-list names may be displayed with unavailable token amounts in their supplied order; no token counts or extra names shall be invented. A missing legacy models/providers list yields no rows. The footer similarly uses existing agent names/order with unavailable amounts and its usual top-two limit. No token ranking can be inferred in this case. An empty dollar list or zero dollars does **not** establish an empty month without the new token projection; legacy absence remains unavailable.

No stricter top-level required fields or rejection of legacy dollar-only replies shall be introduced. Missing token support is not an RPC failure. New servers keep accepting unchanged old inputs; old clients can continue ignoring the additive object.

## TUI state and presentation

The system shall use plugin-scoped session memory under key `unit` with state `{unit: "dollars" | "tokens"}`, initially `"dollars"`, shared by both slots. This shall use the documented memory-storage lifetime, not durable storage or slot-local state. Slot remount, navigation, refresh, collapse and plugin reload shall not reset the unit within a running TUI; a new TUI starts in dollars. Existing durable key `view` and its `{open}` state shall remain untouched. Breakdown selection shall remain independent; a unit change must not reset it.

Both slots shall project their current ready summary using that shared unit. The unit selector remains available in every ready state, including empty/partial/unavailable data; loading/error hides controls without resetting the unit. A click shall select the requested inactive unit once, not toggle blindly. Active-choice/label/gap clicks shall do nothing; control-group events must not bubble into collapse. Dollar formatting and total-only pricing marker stay unchanged.

| Token value state | Display |
|---|---|
| Numeric, complete | Compact decimal count plus ` token` for exactly one, otherwise ` tokens`, including `0 tokens` and `1 token` |
| Numeric, incomplete | Same, prefixed `~`, including `~0 tokens` |
| NULL or absent token support | `Tokens unavailable` (no `~` prefix) |

Apply this per total and per breakdown entry, in both slots and open/collapsed states. Counts below 1,000 shall remain exact integers. Otherwise choose the largest applicable decimal suffix: `k` = 1,000, `M` = 1,000,000, `B` = 1,000,000,000. Round the scaled value to at most two decimal places, nearest with halfway rounded up; trim trailing fractional zeroes and the trailing decimal point. If rounding reaches `1000k` or `1000M`, promote and round the original count in the next unit. `B` is the highest suffix, including for larger counts. Use a decimal point, no grouping separators, and one space before the unit label, independently of host locale. The [product examples](specs/cost-display/spec.md#requirement-token-formatting-and-incomplete-history-are-explicit) govern boundaries, including `999,994` → `999.99k tokens`, `999,995` → `1M tokens` and `999,995,000` → `1B tokens`.

Formatting shall not alter numeric ranking or group reconciliation; independently rounded displayed subtotals need not sum to the displayed total. Rounding alone shall never add `~`. In token mode, any incomplete/unavailable monthly total shall show `Partial: some token counts unavailable` in the opened sidebar; never show it in dollar mode or the one-line footer. Empty complete summaries have no warning. Unavailable values and legacy fallback remain unchanged.

### Container layout contract

Follow [UX](ux.md#width-adaptation-actual-container-character-cells) for exact packing, spacing, selectable values and footer trailing truncation. View and Unit shall occupy separate rows at every width, View first. Each label and complete choice, including brackets, shall remain an atomic, nonshrinking, non-word-wrapping segment. Reflow shall occur only between segments, with stable reserved selected-choice widths and hit targets limited to rendered choice text. Header/footer collapse behavior remains independent of unit controls.

Header fit, control reflow and breakdown fit shall respond to the **actual sidebar content width**, after host padding/borders and before the panel's two-cell indent, not the full terminal column count. Actual container measurement or intrinsic container-constrained layout is acceptable; this contract prescribes neither a production helper nor a host API. At 45/40/22 available cells, including inside a wider terminal and after independent sidebar resize, controls and the specified compact amounts shall remain intact and nonoverlapping. Header amounts move intact to a continuation line when necessary. Breakdown amounts retain their marker/unit and separation from names; only names may truncate or move to a separate line under UX rules. Footer remains one line with its existing trailing truncation at its own available width; that truncation shall not apply to sidebar amounts.

The locked renderer exposes `RenderableOptions.onSizeChange?: (this: T) => void` and measured `width`; its Solid box supports `ref`. Core layout assigns measured width before invoking the visible resize callback (`Renderable.d.ts:31,65,86`; `chunk-node-wp7ct2m6.js:1113–1131,1163–1165`; Solid `elements.d.ts:7–9,24–26,38–40`). These interfaces support an optional measurement strategy, not a required private implementation structure. Container behavior requires rendered frames and coordinate clicks inside a narrower parent at fixed terminal width, including independent parent resize; terminal dimensions or helper-only width assertions do not establish it.

### Footer available-space invariant

The footer contribution shall fit the space actually available to it in the host row, respecting host padding, gaps and sibling contributions. It shall remain one line and preserve the existing total-first, trailing-truncation behavior. When that space permits the complete total, its marker, number and unit label shall remain visible, including `0 tokens`; an earlier narrow allocation shall not leave the footer stuck at `▼0` after space becomes available. Repeated layout passes with unchanged data and host space shall produce stable text, not progressively shorter text. Unit changes, remounts and host/sibling resizing shall recover the full fitting text without requiring new summary data.

The contribution's own intrinsic or resolved width shall not be treated as an independent measure of available parent space when that width depends on the text already clipped to it. Such self-clipping feedback can turn an initial allocation into a permanent truncation limit. Layout shall neither wrap the footer nor claim the whole parent width at the expense of host siblings. Measurement or intrinsic constrained layout remains a private implementation choice; no new host sizing API is required by this contract.

**Source evidence:** OpenCode **2.0.24** [home footer `View`](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.24/packages/tui/src/feature-plugins/home/footer.tsx) defines a full-width padded row with gaps, nonshrinking MCP/plugin/version siblings, the `home.footer.status` slot and a following growing spacer. [Slot rendering](https://raw.githubusercontent.com/anomalyco/opencode/v2.0.24/packages/tui/src/plugin/render.tsx) emits contributions through fragments/providers, not a dedicated available-width layout box. Thus the contribution participates directly in the row's flex allocation; its measured width alone does not establish the remaining host capacity. The locked [OpenTUI core 0.5.14 declarations](https://cdn.jsdelivr.net/npm/@opentui/core@0.5.14/Renderable.d.ts) expose numeric/auto/percentage width, flex growth/shrinkage, minimum/maximum sizing, `onSizeChange(this: T)` and the numeric `width` getter; these are sizing primitives, not a guaranteed available-space query.

**Accessibility limit:** existing mouse-driven text controls provide no evidenced native focus/screen-reader contract. This change shall preserve host keyboard handling and shall not add guessed focus APIs, claim WCAG conformance, or invent shortcuts. Brackets/bold and explicit status text provide non-colour cues; terminal keyboard/screen-reader access remains unproven.

## Technical verification coverage

1. **Ledger → summary:** full five-component vector above; all 32 nullable vectors (especially cache-write NULL with known input/cache-read); all-NULL, known-zero partial, empty, multiple providers, failed/sub-agent/compaction and zero-cost rows; `[from,to)` edges; group reconciliation, group-specific completeness, deterministic ties and unavailable-last ordering. Summary reads must not write rows or change revision.
2. **Summary → RPC → UI:** optional top-level `tokens`, required nested fields and exact agent/model/provider keys; nullable numeric totals and boolean completeness; old replies and distinct NULL/zero serialization. Dollar outputs/order/pricing markers and both cost-tool outputs remain unchanged for identical rows/catalog. Unknown prices with known tokens must not mark token mode partial.
3. **Interaction:** rendered clicks both directions, no-op active/label/gap clicks, selection drag, independent breakdown/open state, shared footer unit/ranking after navigation/remount, restart default with persisted open preference retained, loading/error recovery and all coverage states. Layout coverage includes 45-/40-/22-cell containers inside a wider terminal, independent sidebar resize, all six unit/breakdown selections, intact amounts, long-name truncation/stacking and footer clipping. Formatting coverage includes compact boundaries, half-up rounding, promotion, trimmed zeroes, singular/plural, large B values and equal formatted strings with different numeric ranks.
4. **Recording integration:** clean isolated installation → open zero token view → normal supported model activity → existing recorder/store/notification/RPC refresh populates both views → return to identical dollars. Injected summary fixtures alone do not prove this path. The database remains intact and unit switching causes no accounting mutations.

Footer regression coverage shall use rendered frames in a host-shaped padded flex row, including nonshrinking siblings and the following growing spacer, not only an explicitly sized standalone contribution or clipping helper. Assert: (a) `0 tokens` and a representative nonzero compact total retain their complete unit text whenever space permits, across repeated settled frames and both unit-switch directions; (b) reducing then restoring row space, changing sibling occupancy at fixed terminal width, and remounting restore the full fitting text without a summary refresh; (c) genuine space shortage truncates only the trailing text, stays one line and does not overlap or displace host siblings. Repeat the empty-token check on the supported real host and continue the existing normal-activity recording verification on the corrected candidate; renderer fixtures do not replace that verification. Reconciliation and archive remain gated on a clean, verified candidate.

## Technical limitations

- **Historical provenance:** stored zeros may include ingestion defaults; provider billing accuracy and the original availability of those values cannot be recovered from this projection. Historical rows are not necessarily from OpenCode 2.0.24.
- **Host state and transport:** `src/test-support/token-host{,.test}.ts` models session memory and JSON replies, not actual host reload/restart, disk persistence, runtime schema validation or RPC transport. The locked memory/durable setter distinction is documented in `@opencode/plugin@2.0.24/dist/tui/context.d.ts:6–21`; simulated shared state does not establish real-host behavior. Production must not depend on the test-only adapter.
- **Recording fixtures:** synthetic start/end events can exercise recorder/store/notification/summary/feed/renderer with subscribers active, but fixtures with startup backfill already complete do not establish clean-install backfill or normal provider activity.
- **Container boundaries:** hidden/zero-width callback behavior and real host padding remain unverified. Exceptional amounts too wide even for a dedicated line retain their full text per UX; host overflow clipping remains unverified. Widths below 22 cells are not guaranteed.
- **Accessibility:** native focus and terminal keyboard/screen-reader access remain unproven, as described above.

These limitations distinguish source and fixture evidence from supported-host behavior; this document makes no runtime-verification or release claim.
