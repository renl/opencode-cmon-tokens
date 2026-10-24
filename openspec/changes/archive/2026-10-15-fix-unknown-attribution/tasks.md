# Tasks

Recover missing attribution from the exact source message while preserving known fields and accounting.

## 1. Exact-message live recovery

- [x] 1.1 Add name-matched recorder/backfill tests for missing-start recovery, observed-start authority, identity/type rejection, partial fields and source failure scenarios.
- [x] 1.2 Implement the source reader and recorder injection in existing modules; verify the group 1 scenarios pass through `bun run test`.
- [x] 1.3 Update the existing `Missing step start falls back` regression and retain the completed-step scenarios; verify no other step's attribution is borrowed and failed-step/compaction contracts still pass.
- [x] 1.4 Document live best-effort recovery and unavailable-source limits in README; verify the text matches the delta scenarios.

## 2. Persistent repair and redelivery

- [x] 2.1 Add name-matched store/backfill tests for startup repair, idempotency, retries, concurrent guards, batch failure and redelivery scenarios.
- [x] 2.2 Implement field-wise guarded step merges and bounded startup repair; verify group 2 tests preserve every non-attribution column and known field.
- [x] 2.3 Wire repair before RPC registration and revision changes only on actual repairs; verify initial summary attribution with existing store/summary interfaces and inspect startup ordering.
- [x] 2.4 Document startup retries and unchanged accounting in README; verify documentation against preservation and retry tests.

## 3. Bounded failure diagnostics

- [x] 3.1 Add name-matched integration tests for diagnostic content exclusion, deduplication and non-throwing behavior.
- [x] 3.2 Wire categorical diagnostics through the existing stderr channel; verify group 3 tests and document their safe content and limits in README.

## 4. Integrated verification

- [x] 4.1 Run `bun run test`, `bun run lint` and `bun run build`; verify all exit successfully and scenario names map to the delta or existing main spec.
- [x] 4.2 Verify field preservation, conflict handling, failure categorization and non-throwing diagnostics across the integrated recovery path.

## Test map and commands

| Test area | Assertions |
| --- | --- |
| `src/recorder.test.ts` | Missing-start and completed/failed recovery; observed-start authority; no attribution inference from another step; a throwing log sink cannot stop the event loop. |
| `src/backfill.test.ts` | Exact-ID/type matching, partial fields, unavailable source, locked synthetic source, retry/resource handling and failure in a second repair batch. |
| `src/store.test.ts` | Startup repair, idempotency, two-connection stale-candidate merge, field-wise redelivery guards and preservation of every accounting column. |
| Integration scenarios | Repair precedes RPC availability; revisions change only on actual repairs; diagnostics exclude sensitive content, deduplicate and retain existing per-event ledger errors; empty startup summaries do not add noise. |

```sh
bun run test ./src/recorder.test.ts ./src/backfill.test.ts ./src/store.test.ts
bun run test
bun run lint
bun run build
```

Use the test script's timezone/browser conditions rather than bare `bun test`. Scenario titles in the delta map to tests; unchanged retention scenarios retain their existing coverage. Documentation is not executable proof.

## Technical constraints and validation limits

- Shared field-wise merge SQL preserves known attribution and avoids duplicated update rules. Exact source access stays in the existing backfill module; no schema, dependency or recovery timer is added. Existing startup fills keep their behavior.
- Existing steps preserve accounting on redelivery, including backfills; compactions retain replacement behavior. The matching retention delta retains existing scenario titles. The backfilled-token-null window preserves accounting until existing fills run.
- Source reads explicitly apply the 50 ms lock wait; this bounds lock waiting, not total I/O latency. Missing-message handling is covered by the exact-ID mismatch integration case.
- Ledger-side failures retain categorical diagnostics, insert conflict handling stays narrowly scoped, and a throwing diagnostic sink cannot interrupt recording.
- SQLite `run` replaces the deprecated `exec` alias where touched. Asynchronous rejection assertions retain their required sequencing.
- Dedicated concurrency, batch-failure, retry and source-lock/resource tests cover their safeguards, but were not demonstrated failing before implementation. Passing coverage does not establish test-first history or real-host behavior.
