# Monthly token display — architecture contract

Add a read-only token projection to the existing summary and a session-only unit choice, without changing dollar accounting.

- **Workflow / status:** Authorized `software-change`; compact-format/container-layout correction aligned on 2026-10-24, ready for SDET test updates. Source semantics checked on 2026-10-23. User reports the live panel works after the local plugin-load correction; this document claims no independent runtime verification.
- **Owner:** Architect. PM remains primary author of the `cost-display` delta; this design owns the cross-component contract, not a second capability spec.
- **Parents:** [Proposal](proposal.md), [product delta](specs/cost-display/spec.md), [current capability](../../specs/cost-display/spec.md).
- **UI authority:** [UX reference](ux.md). Layout, wrapping, control hit targets and accessibility limitations remain defined there.
- **Read next:** SDET tasks and verification evidence, once authored through CoS.

## Boundaries and compatibility

| Boundary | Contract |
|---|---|
| Ledger → summary | Read the five nullable token columns for every row in the requested range, preserving each component's availability. Aggregate in the same database read snapshot as dollar summary inputs. |
| Summary builder → RPC | Compute token totals independently of prices and cache-write dollar adjustments; attach the additive `tokens` object below. |
| RPC → TUI | One summary response supplies both units. Switching units changes local presentation only; no request, write, catalog load or change event is required. |
| TUI slots → shared state | Sidebar and footer share one session unit; persisted open state and sidebar breakdown choice remain independent. |

The system shall retain RPC id `cmon`, method `summary`, input `{from: number, to: number}` (UTC epoch milliseconds, half-open `[from,to)`), and event `changed({revision: number})`. It shall retain all existing response fields, dollar values, dollar ordering, pricing completeness and refresh/retry/debounce semantics. There is no new route, RPC method, event or tool.

Neither `cost_report` nor `cost_hotspots`, their schemas, outputs or token interpretations shall change. No database/schema-version change, new recording behavior, historical reinterpretation, retention change or repair-policy change is authorized. Private implementation structure remains SE-owned.

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

CoS supplied source-first research for the lock-resolved OpenCode packages at **2.0.24**. The following exact sources were also fetched and checked for this contract:

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

**Host evidence limit:** current `src/tui.tsx` uses terminal dimensions for all three fit decisions and therefore does not establish container-aware behavior. No new container measurement callback, dimension property or intrinsic wrapping API is verified by this correction: **[UNVERIFIED — requires source check]**. Before SDET/SE relies on any such external interface, CoS shall supply a bounded check of locked dependency source/declarations or official documentation and relevant real examples. The smallest proof is a rendered panel inside a narrower parent at fixed terminal width, resized with intact controls and coordinate-click targets. Use that as the correction's layout proof, not a new general-purpose host harness or approval gate. No new RPC/storage integration research is needed. Exceptional amounts too wide even for a dedicated line retain their full text per UX; whether the host clips that overflow is unverified and must be recorded, not claimed solved by guessed APIs. Widths below 22 cells are not a new guarantee.

**Accessibility limit:** existing mouse-driven text controls provide no evidenced native focus/screen-reader contract. This change shall preserve host keyboard handling and shall not add guessed focus APIs, claim WCAG conformance, or invent shortcuts. Brackets/bold and explicit status text provide non-colour cues; terminal keyboard/screen-reader access remains unproven.

## Verification gates, risks and handoff

No broad new external integration is needed. Before broader UI work, SDET shall define the minimal host-boundary proof and distinguish executable contract tests from final supported-host evidence: two independently mounted slots share memory state across unmount/remount, exit restores dollars, and the RPC round-trip preserves the optional token object/legacy reply. **Define does not mean complete a new real-host harness before implementation.** Source-checked storage signatures, the existing RPC pattern, and reviewed test doubles permit the vertical implementation to proceed after test-plan corrections. Real-host lifecycle/transport and first normal model activity remain independent integrated-candidate verification gates before sync/archive/merge; they cannot be claimed from the doubles. Existing renderer mouse tests are the reference for click dispatch, not proof by helper output alone. If the documented memory/RPC interfaces fail against locked dependencies, stop and return evidence through CoS for source research rather than inventing substitutes.

Required proof chain:

1. **Ledger → summary:** full five-component vector above; mixed NULL permutations (especially cache-write NULL with known input/cache-read); all-NULL, known-zero partial, empty, multiple providers, failed/sub-agent/compaction and zero-cost rows; `[from,to)` edges; group reconciliation, group-specific completeness, deterministic ties and unavailable-last ordering. Summary reads must not write rows or change revision.
2. **Summary → RPC → UI:** schema accepts old replies and serializes NULL/zero distinctly; dollar outputs/order/pricing markers and both cost-tool outputs remain unchanged for identical rows/catalog. Unknown prices with known tokens must not mark token mode partial.
3. **Interaction:** actual rendered clicks both directions, no-op active/label/gap clicks, selection drag, independent breakdown/open state, shared footer unit/ranking after navigation/remount, restart default with persisted open preference retained, loading/error recovery, all coverage states, and 45-/40-/22-cell actual-container layouts per UX. Verify rendered frames and coordinate clicks inside a wider terminal, including sidebar resize without terminal resize and all six unit/breakdown selections; helper-only width assertions are insufficient. Cover compact boundaries, half-up rounding, promotion, trimmed zeroes, singular/plural, large B values, partial/unavailable/empty states, equal formatted strings with different numeric ranks, long-name truncation/stacking and footer clipping.
4. **First useful workflow:** clean isolated installation → open zero token view → normal supported model activity → existing recorder/store/notification/RPC refresh populates both views → return to identical dollars. Injected summary fixtures alone do not prove recording integration. Preserve the database and verify no unit-switch accounting mutations.

Risks are bounded: unknown historical provenance remains unrecoverable; raw-NULL loss in existing convenience mappings must be avoided; session sharing and narrow-terminal hit targets need runtime proof. Containerized checks are the default; any required native terminal exception and real external-boundary evidence belong in SDET's test plan, not an implied waiver. No tests, runtime spike or e2e pass is claimed by this document.

**Handoff:** CoS should route to `@sdet-engineer` for task/test planning and boundary-proof definition in the existing change worktree; implementation dispatch remains with CoS after SDET readiness. PM may reconcile stale source-blocker status and link this contract in their owned artifacts; no product scope change or separate Architect-authored capability delta is needed.

### Correction handoff — 2026-10-24

This correction changes presentation only. The user confirms live panel operation after correcting the local plugin reference to the built **`dist` directory**, not an individual entry file. README/install guidance correction is pending with its owner; no installation, README or configuration edits are authorized here. No unrelated RPC/accounting changes are required.

CoS shall route SDET to update existing tasks/tests for compact formatting and the actual-container frame/click proof above, preserving dollar/tool regression coverage and established token semantics. Reuse the current worktree and existing verification approach; no new worktree, product approval, general harness, live model call or repeated accounting spike is required for this presentation correction. Resolve any newly needed external layout interface through the scoped source check above before relying on it. Prior review findings below are historical; they do not independently establish current candidate evidence or reopen resolved blockers. Independent verification remains against the corrected candidate under the existing change lifecycle, without expanding this correction's scope.

## Architecture review — 2026-10-23

Review scope: [tasks](tasks.md) Boundary Verification and checkpoints; `src/token-summary.test.ts`, `src/token-display.test.tsx`, `src/test-support/token-host{,.test}.ts`, existing click tests, production registration/recorder/RPC/TUI, and locked plugin storage declarations. Static review only; no test execution or host proof claimed. Findings live here because OpenSpec Architect write scope permits this design, not a separate review file.

### Boundary fidelity: ACCEPT

- The boundary table retains `cmon`, `summary({from,to})`, `changed({revision})`, existing registration/client calls and event names. No endpoint, authentication or mapping is invented. Top-level `tokens` remains optional; its five fields and group entry names match this contract. Existing optional monetary lists remain optional.
- `token-host.ts` is explicitly test-only and is consumed by tests, not production. Its `TokenReply`/projection matches the additive contract. JSON cloning preserves NULL and zero but performs no host schema validation or transport; ignored registration definitions/event names are limitations of the double, not platform guarantees.
- The memory map is scoped to the simulated TUI session, not a slot. It shares a live Solid store across mounts and reload simulation; a fresh map models exit. Its synchronous memory setter versus asynchronous durable setter agrees with locked `@opencode/plugin@2.0.24/dist/tui/context.d.ts:6–21`. TOK-06 proves component behavior under that model, not actual host reload/restart or disk persistence.
- TOK-01 tests all 32 nullable vectors, including known components with NULL cache-write; TOK-02 distinguishes partial zero, unavailable and empty, verifies independent group completeness/ranking/reconciliation and unchanged rows/revision through repeated replies. TOK-13 keeps price completeness separate. These assertions preserve the approved formula without prescribing a private implementation API.
- TOK-09 activates subscribers before synthetic start/end events and traverses production recorder/store/notification/summary/feed/renderer. Startup backfill is marked complete and source data is absent in this fixture. It is an isolated plugin integration test, not a clean host installation, normal provider activity or host RPC proof. The tasks correctly disclose this distinction.

### Decomposition fidelity: ACCEPT — corrections confirmed 2026-10-23

The isolated per-test ledgers, active-receiver ordering, cleanup, and single vertical checkpoint are coherent. Static confirmation of the submitted correction (`1a73b09`), limited to `tasks.md` and `src/token-summary.test.ts`, resolves the prior gate-placement and nested-schema findings. No tests or host verification were run for this confirmation. Boundary fidelity remains ACCEPT.

Prior findings, all resolved by this confirmation:

| Owner / location | Required correction (now satisfied) |
|---|---|
| SDET — tasks setup status, checkpoint 1 lines 28–29, checkpoint 2 dependency, boundary smoke line 79 | Remove completion of a **new real-host harness** as an unconditional implementation prerequisite. Checkpoint 1 requires this review's corrections and a defined evidence/environment plan. Checkpoint 2 depends on that readiness, not on a full feature smoke that itself needs checkpoint 2 implementation. |
| SDET — checkpoint 3 and boundary smoke | Retain actual supported-host lifecycle, legacy/new RPC and first normal model activity before finalization. Separate environment preparation from proof against the pinned implemented candidate. A general-purpose new automation framework is not a product/architecture requirement; use the smallest reproducible bounded verification procedure. If no suitable environment exists, final e2e stays BLOCKED, never passed by adapter substitution. |
| SDET — TOK-03 and traceability | Current assertions check optional top-level status and the five object keys, but not the nested property/item schemas. Add assertions for nullable numeric totals, boolean completeness, required entry fields and exact agent/model/provider names. Keep schema-shape/JSON tests labelled as such; acceptance of legacy and new NULL/zero replies through the supported runtime remains a separate candidate proof. No new dependency or production test API is required by this finding. |

Checkpoint 1 now requires confirmed corrections and a defined candidate evidence/environment plan; checkpoint 2 no longer depends on host proof that requires its own implementation. Checkpoint 3 retains pinned-candidate lifecycle, real RPC legacy/NULL/zero acceptance and first normal model activity, with a separate clean first-use ledger and environment preparation independent of implementation. TOK-03 now asserts nullable numeric totals, boolean completeness, array/object item schemas, required entry fields and exact agent/model/provider string keys; equivalent numeric union spellings are accepted. These remain schema-shape assertions, not runtime transport proof.

The corrected decomposition is ready for vertical implementation through CoS. The existing 22 backfill/store EBUSY failures remain reported failed checks with an unconfirmed environmental cause; controlled candidate regression evidence is required before finalization. No waiver, baseline pass, candidate verification, or sync/archive/merge authorization is granted. Final real-host e2e remains BLOCKED pending a suitable approved environment/procedure; adapter success cannot clear it.

### Minimal next step and environment contingency

Return to CoS: SDET may record this confirmation as checkpoint 1 readiness, after which CoS may dispatch the existing vertical implementation. No additional SDET setup or pre-implementation DevOps environment is required by these resolved findings. Environment preparation may proceed independently; independent SDET verification of the pinned implemented candidate remains required before finalization.

If implementation reveals an actual memory/RPC incompatibility, CoS shall first route a bounded source-grounded spike, not the full first-use workflow: one isolated supported TUI with two independently mounted consumers of `unit`, a synchronous update visible to both and retained through remount/reload, reset after exit, and one unchanged `summary` input exercised with legacy and NULL/zero replies over real host RPC. Minimum evidence: pinned runtime/plugin, actual host observations and reply values, command/timeout/exit status, and verified cleanup. No provider activity is needed for this diagnostic spike; it is still required for final first-use verification.

If that spike or final verification needs environment help, request DevOps scope **through CoS** for only an isolated locked-runtime terminal/session and data/config paths, bounded readiness/total timeout/logs and process-tree teardown. Containerized verification remains the default; a native exception needs the documented representability rationale and lifecycle. Credentials/model access require separate scoped authorization; never inspect global configuration or user ledgers. No environment action or agent dispatch is authorized by this review.

## Presentation correction review — 2026-10-24

Scoped static review of SDET setup `89d9943ee69b4bb8dbcbda234a5f223052d7f9b7`: tasks correction block, five affected test files, approved product/UX presentation rules, and installed locked renderer declarations/source. No commands/tests, git operations or independent candidate verification performed; reported RED/pass counts remain SDET evidence.

### Boundary fidelity: ACCEPT

- TOK-20 uses the actual locked `RenderableOptions.onSizeChange?: (this: T) => void`, measured `width`, and Solid box `ref` contracts. Core layout assigns measured width before invoking the visible resize callback (`Renderable.d.ts:31,65,86`; `chunk-node-wp7ct2m6.js:1113–1131,1163–1165`); Solid `elements.d.ts:7–9,24–26,38–40` admits those props. No width callback argument or new host interface is invented. This closes the source-check prerequisite for this optional strategy only; hidden/zero-width behavior and real host padding remain unproved.
- The probe is explicitly test-only, not a production dependency or mandated layout strategy. Existing formatting exports/component boundaries are exercised without requiring new private helpers. Exact frame coordinates implement UX's prescribed stable packing, not private production structure. RPC/accounting/storage interfaces remain unchanged.
- TOK-16 renders actual nested 45/40/22-cell containers inside a fixed 120-cell terminal, verifies all six selections and independent resize, and checks control events do not reach the parent or alter open state. Sidebar-only frames prevent footer text from masking broken sidebar output. TOK-17/18 cover intact amounts and name truncation/stacking; TOK-21 separately covers footer clipping.
- TOK-14/15/19 preserve the approved compact rounding/promotion/labels and exact underlying RPC counts/ranking. No accounting formula or host lifecycle claim is reopened by this correction.

### Decomposition fidelity: ACCEPT — spacing correction confirmed 2026-10-24

C1 → reviewed setup → C2 presentation → C3 independent pinned-candidate verification is correctly ordered. Fixtures are run-isolated; retained TOK-09 subscribes before events; real-host proof is not an implementation prerequisite. Scoped static confirmation of submitted correction `188bd5687d05b7641228a5da617ca1db2d4f4ec1`, limited to `src/tui.click.test.tsx` and the tasks correction record, resolves the sole spacing finding. Boundary fidelity remains ACCEPT; no broader new review is needed.

| Owner / location | Confirmed resolution |
|---|---|
| SDET — `src/tui.click.test.tsx:185–194`, “Controls still work”; tasks “Scoped assertion correction” | Exact expectation is now `View  Agents    Models    [Providers]`, consistent with the Providers assertion at lines 102–104 and the approved reserved-width spacing. The coordinate Providers click and header-click collapse assertion remain intact. Tasks records the gap, correction and expected presentation RED without claiming a candidate pass. |

**Readiness:** READY for C2 presentation implementation through CoS; no further SDET setup or architecture review is required for this resolved gap. No contract change, private implementation prescription, new research/harness or accounting review is required. Only this design disposition changed; no tests or git operations were run. Return to CoS for bounded implementation dispatch. Final independent SDET verification of the implemented immutable candidate and unresolved real-host gates remain required before sync/archive/merge. This review grants no feature acceptance or finalization authorization.
