import { Plugin } from "@opencode/plugin/tui";
import type { JSX } from "@opentui/solid";
import { useTerminalDimensions } from "@opentui/solid";
import {
  createEffect,
  createMemo,
  createSignal,
  For,
  onCleanup,
  Show,
  type Accessor,
} from "solid-js";
import { formatUsd } from "./money.js";
import { CostRpc } from "./rpc.js";
import { localMonthRange } from "./time.js";
import type { Summary, SummaryReply, TokenSummary } from "./types.js";

export type FeedState =
  | { readonly kind: "loading" }
  | { readonly kind: "error" }
  | { readonly kind: "ready"; readonly summary: SummaryReply };

/** The slice of `context.client.rpc(CostRpc)` this module depends on; tests supply a fake. */
export interface CostRpcClient {
  summary(input: { from: number; to: number }): Promise<unknown>;
  events: {
    on(
      name: "changed",
      handler: (event: { data: unknown }) => void,
    ): () => void;
  };
}

/** Which unit both slots present. Session-only: a new TUI starts in dollars. */
export type Unit = "dollars" | "tokens";

/** Bounded reconciliation: catches cost written by other server processes and the month rollover. */
const SAFETY_NET_INTERVAL_MS = 60_000;
/** While in the error state, e.g. the server restarted and the RPC is not registered yet. */
const ERROR_RETRY_INTERVAL_MS = 5_000;
const FOOTER_AGENT_LIMIT = 2;
const LOADING = "…";
const FAILED = "Error";
const TOKENS_UNAVAILABLE = "Tokens unavailable";
const TOKEN_PARTIAL = "Partial: some token counts unavailable";
/** Header label text, kept as one piece so it stays a single non-selectable run. */
const MONTH_LABEL = "This month: ";
const CONTROL_INDENT = 2;
/** Two spaces between choices, four between the View and Unit groups. */
const CHOICE_GAP = 2;
const GROUP_GAP = 4;

export interface CostFeed {
  readonly state: Accessor<FeedState>;
}

/**
 * Fetches the current local month's summary, refreshing on `changed` and on a safety-net interval,
 * and retrying every few seconds while in the `error` state.
 * Never throws an RPC failure into the host; it becomes the `error` state.
 */
export function createCostFeed(
  client: CostRpcClient,
  now: () => Date = () => new Date(),
): CostFeed {
  const [state, setState] = createSignal<FeedState>({ kind: "loading" });

  let retryTimer: ReturnType<typeof setTimeout> | undefined;
  let disposed = false;
  const cancelRetry = (): void => {
    clearTimeout(retryTimer);
    retryTimer = undefined;
  };

  const refresh = async (): Promise<void> => {
    const [from, to] = localMonthRange(now());
    try {
      const summary = (await client.summary({ from, to })) as SummaryReply;
      cancelRetry();
      setState({ kind: "ready", summary });
    } catch {
      setState({ kind: "error" });
      if (!disposed)
        retryTimer ??= setTimeout(() => {
          retryTimer = undefined;
          void refresh();
        }, ERROR_RETRY_INTERVAL_MS);
    }
  };

  createEffect(() => {
    void refresh();
    onCleanup(client.events.on("changed", () => void refresh()));
    const timer = setInterval(() => void refresh(), SAFETY_NET_INTERVAL_MS);
    onCleanup(() => clearInterval(timer));
    onCleanup(() => {
      disposed = true;
      cancelRetry();
    });
  });

  return { state };
}

export function glyph(open: boolean): string {
  return open ? "▼" : "▶";
}

/** Exact whole counts with ASCII comma grouping, never abbreviated or scaled. */
export function formatTokens(count: number): string {
  return count.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * One token amount. An unknown subtotal is unavailable, not zero; an incomplete one is marked `~`.
 * `1 tokens` keeps the fixed unit label.
 */
export function tokenAmount(
  totalTokens: number | null | undefined,
  complete: boolean | undefined,
): string {
  if (totalTokens === null || totalTokens === undefined)
    return TOKENS_UNAVAILABLE;
  return `${complete === false ? "~" : ""}${formatTokens(totalTokens)} tokens`;
}

function dollarsAmount(summary: Summary): string {
  // `~` marks a total that may be understated because some pricing is unknown.
  return `${summary.complete === false ? "~" : ""}${formatUsd(summary.totalMicros)}`;
}

export function amount(state: FeedState, unit: Unit = "dollars"): string {
  switch (state.kind) {
    case "loading":
      return LOADING;
    case "error":
      return FAILED;
    case "ready":
      return unit === "tokens"
        ? tokenAmount(
            state.summary.tokens?.totalTokens,
            state.summary.tokens?.complete,
          )
        : dollarsAmount(state.summary);
  }
}

/**
 * Why token mode cannot show a full month, if it cannot. Pricing completeness never contributes:
 * unknown prices leave token amounts complete. Empty and complete months have no warning.
 */
export function tokenWarning(state: FeedState, unit: Unit): string | undefined {
  if (unit !== "tokens" || state.kind !== "ready") return undefined;
  const tokens = state.summary.tokens;
  if (tokens === undefined || tokens.complete === false) return TOKEN_PARTIAL;
  return undefined;
}

function agentParts(
  summary: SummaryReply,
  unit: Unit,
): ReadonlyArray<{ label: string; amount: string }> {
  if (unit === "tokens") {
    const tokens = summary.tokens;
    // An older server supplies no token ranking; keep its dollar names in their order.
    if (tokens === undefined)
      return summary.agents.map((entry) => ({
        label: entry.agent,
        amount: TOKENS_UNAVAILABLE,
      }));
    return tokens.agents.map((entry) => ({
      label: entry.agent,
      amount: tokenAmount(entry.totalTokens, entry.complete),
    }));
  }
  return summary.agents.map((entry) => ({
    label: entry.agent,
    amount: formatUsd(entry.micros),
  }));
}

/** Single-line footer: never grows the footer, even when opened. */
export function footerLine(
  state: FeedState,
  open: boolean,
  unit: Unit = "dollars",
): string {
  if (!open) return `${glyph(open)} ${amount(state, unit)} this month`;
  const parts = [`${glyph(open)} ${amount(state, unit)}`];
  if (state.kind === "ready") {
    const entries = agentParts(state.summary, unit);
    for (const entry of entries.slice(0, FOOTER_AGENT_LIMIT))
      parts.push(`${entry.label} ${entry.amount}`);
    if (entries.length > FOOTER_AGENT_LIMIT)
      parts.push(`+${entries.length - FOOTER_AGENT_LIMIT}`);
  }
  return parts.join(" · ");
}

export interface OpenStateStorage {
  store(
    key: string,
    options: { readonly initial: { open: boolean } },
  ): readonly [
    { open: boolean },
    (mutation: (draft: { open: boolean }) => void) => Promise<void>,
  ];
}

/** Same storage key in every slot: one persisted open/closed state shared everywhere. */
export function createOpenState(storage: OpenStateStorage) {
  const [view, updateView] = storage.store("view", {
    initial: { open: false },
  });
  const toggle = (): void => {
    void updateView((draft) => {
      draft.open = !draft.open;
    }).catch((error: unknown) =>
      console.error("Failed to persist cost block state", error),
    );
  };
  return { view, toggle };
}

export interface UnitState {
  unit: Unit;
}

export interface UnitStateStorage {
  memory(
    key: "unit",
    options: { readonly initial: UnitState },
  ): readonly [UnitState, (mutation: (draft: UnitState) => void) => void];
}

/**
 * One live session memory shared by both slots. It survives remounts and plugin reloads within a
 * running TUI and is discarded when the TUI exits, so a restart starts in dollars while the durable
 * open/closed preference is untouched.
 */
export function createUnitState(storage: UnitStateStorage) {
  const [state, update] = storage.memory("unit", {
    initial: { unit: "dollars" },
  });
  const select = (unit: Unit): void => {
    if (state.unit === unit) return;
    update((draft) => {
      draft.unit = unit;
    });
  };
  return { unitState: state, select };
}

export type Breakdown = "agent" | "model" | "provider";

export function breakdownLines(
  state: FeedState,
  breakdown: Breakdown,
  unit: Unit = "dollars",
): ReadonlyArray<{ label: string; amount: string }> {
  if (state.kind !== "ready") return [];
  const { summary } = state;
  const tokens: TokenSummary | undefined = summary.tokens;
  if (unit === "tokens") {
    if (tokens === undefined) {
      // A server without token support: keep its names in their supplied order, unavailable amounts.
      const names =
        breakdown === "agent"
          ? summary.agents.map((e) => e.agent)
          : breakdown === "model"
            ? (summary.models ?? []).map((e) => e.model)
            : (summary.providers ?? []).map((e) => e.provider);
      return names.map((label) => ({ label, amount: TOKENS_UNAVAILABLE }));
    }
    const entries =
      breakdown === "agent"
        ? tokens.agents.map((e) => ({
            label: e.agent,
            amount: tokenAmount(e.totalTokens, e.complete),
          }))
        : breakdown === "model"
          ? tokens.models.map((e) => ({
              label: e.model,
              amount: tokenAmount(e.totalTokens, e.complete),
            }))
          : tokens.providers.map((e) => ({
              label: e.provider,
              amount: tokenAmount(e.totalTokens, e.complete),
            }));
    return entries;
  }
  // A server process still running an older plugin replies without `models`/`providers`.
  switch (breakdown) {
    case "agent":
      return summary.agents.map((e) => ({
        label: e.agent,
        amount: formatUsd(e.micros),
      }));
    case "model":
      return (summary.models ?? []).map((e) => ({
        label: e.model,
        amount: formatUsd(e.micros),
      }));
    case "provider":
      return (summary.providers ?? []).map((e) => ({
        label: e.provider,
        amount: formatUsd(e.micros),
      }));
  }
}

/** One clickable control: the active choice is bracketed and bold so it reads without colour. */
export interface Choice<Mode> {
  readonly text: string;
  readonly bold: boolean;
  readonly mode?: Mode;
}

const BREAKDOWN_LABELS: ReadonlyArray<readonly [Breakdown, string]> = [
  ["agent", "Agents"],
  ["model", "Models"],
  ["provider", "Providers"],
];

/** Toggle row pieces; the active tab is bracketed and bold so it reads without colour. */
export function toggleSegments(
  active: Breakdown,
): ReadonlyArray<Choice<Breakdown>> {
  return [
    { text: "View", bold: false },
    ...BREAKDOWN_LABELS.map(([mode, label]) =>
      mode === active
        ? { text: `[${label}]`, bold: true, mode }
        : { text: label, bold: false, mode },
    ),
  ];
}

/** Unit choices; only the rendered text of a choice is a click target. */
export function unitSegments(active: Unit): ReadonlyArray<Choice<Unit>> {
  return [
    { text: "Unit", bold: false },
    active === "dollars"
      ? { text: "[$]", bold: true, mode: "dollars" }
      : { text: "$", bold: false, mode: "dollars" },
    active === "tokens"
      ? { text: "[Tokens]", bold: true, mode: "tokens" }
      : { text: "Tokens", bold: false, mode: "tokens" },
  ];
}

/** Width reserved for each group in its widest selection, so selecting never reflows the row. */
const VIEW_WIDTH = "View".length + 8 + 8 + 11 + 3 * CHOICE_GAP;
const UNIT_WIDTH = "Unit".length + 3 + 8 + 2 * CHOICE_GAP;

/** Greedy packing of whole choices, so a choice label is never split across rows. */
function wrapChoices<Mode>(
  segments: ReadonlyArray<Choice<Mode>>,
  available: number,
): ReadonlyArray<ReadonlyArray<Choice<Mode>>> {
  const lines: Choice<Mode>[][] = [];
  let line: Choice<Mode>[] = [];
  let width = 0;
  for (const segment of segments) {
    const needed = (line.length === 0 ? 0 : CHOICE_GAP) + segment.text.length;
    if (line.length > 0 && width + needed > available) {
      lines.push(line);
      line = [segment];
      width = segment.text.length;
      continue;
    }
    line.push(segment);
    width += needed;
  }
  if (line.length > 0) lines.push(line);
  return lines;
}

/** A control row holds the View group, the Unit group, or both when they share a row. */
export interface ControlGroup {
  readonly kind: "breakdown" | "unit";
  readonly segments: ReadonlyArray<Choice<Breakdown | Unit>>;
}

export interface ControlRow {
  readonly groups: ReadonlyArray<ControlGroup>;
}

/**
 * Lays the selector out from the terminal width in columns (the UX measure, not pixels). Both
 * groups share a row when they fit with their widest selection; otherwise the whole Unit group
 * moves below View, and a group too wide for the row wraps at choice boundaries. Like the existing
 * flex layout, this assumes the slot occupies the host column's full width.
 */
export function controlRows(
  width: number,
  breakdown: Breakdown,
  unit: Unit,
): ReadonlyArray<ControlRow> {
  const available = Math.max(0, width - CONTROL_INDENT);
  const view = toggleSegments(breakdown);
  const units = unitSegments(unit);
  if (available >= VIEW_WIDTH + GROUP_GAP + UNIT_WIDTH)
    return [
      {
        groups: [
          { kind: "breakdown", segments: view },
          { kind: "unit", segments: units },
        ],
      },
    ];
  return [
    ...wrapChoices(view, available).map((segments) => ({
      groups: [{ kind: "breakdown" as const, segments }],
    })),
    ...wrapChoices(units, available).map((segments) => ({
      groups: [{ kind: "unit" as const, segments }],
    })),
  ];
}

/** The amount stays on the header line when it fits beside the glyph and label. */
function headerFits(width: number, amountText: string): boolean {
  return 1 + 1 + MONTH_LABEL.length + amountText.length <= width;
}

/** Label and amount share a row when both fit; otherwise the amount moves to its own indented line. */
function breakdownFits(
  width: number,
  line: { label: string; amount: string },
): boolean {
  return CONTROL_INDENT + line.label.length + 1 + line.amount.length <= width;
}

function useCostBlock(context: Plugin.Context) {
  const feed = createCostFeed(context.client.rpc(CostRpc));
  return {
    feed,
    ...createOpenState(context.storage),
    ...createUnitState(context.storage),
  };
}

export function CostSidebar(props: {
  readonly context: Plugin.Context;
}): JSX.Element {
  const { feed, view, toggle, unitState, select } = useCostBlock(props.context);
  const theme = props.context.theme;
  const [breakdown, setBreakdown] = createSignal<Breakdown>("agent");
  const dimensions = useTerminalDimensions();
  const unit = (): Unit => unitState.unit;
  const amountText = (): string => amount(feed.state(), unit());
  const amountColor = (): string =>
    feed.state().kind === "error"
      ? theme.text.feedback.error.base
      : theme.text.base;
  const rows = createMemo(() =>
    controlRows(dimensions().width, breakdown(), unit()),
  );
  const warning = createMemo(() => tokenWarning(feed.state(), unit()));
  /** Only a rendered choice changes state: labels and gaps have no mode. */
  const choose = (
    kind: ControlGroup["kind"],
    mode: Breakdown | Unit | undefined,
  ): void => {
    if (mode === "agent" || mode === "model" || mode === "provider") {
      if (kind === "breakdown") setBreakdown(mode);
      return;
    }
    if (mode === "dollars" || mode === "tokens") select(mode);
  };

  return (
    <box>
      <Show
        when={headerFits(dimensions().width, amountText())}
        fallback={
          <box flexDirection="column" onMouseDown={toggle}>
            <box flexDirection="row" gap={1}>
              <text fg={theme.text.base} selectable={false}>
                {glyph(view.open)}
              </text>
              <text fg={theme.text.base} selectable={false}>
                <b>This month</b>
                {": "}
              </text>
            </box>
            <text
              fg={amountColor()}
              paddingLeft={CONTROL_INDENT}
              wrapMode="char"
            >
              {amountText()}
            </text>
          </box>
        }
      >
        <box flexDirection="row" gap={1} onMouseDown={toggle}>
          <text fg={theme.text.base} selectable={false}>
            {glyph(view.open)}
          </text>
          <box flexDirection="row">
            <text fg={theme.text.base} selectable={false}>
              <b>This month</b>
              {": "}
            </text>
            <text fg={amountColor()}>{amountText()}</text>
          </box>
        </box>
      </Show>
      <Show when={view.open}>
        <Show when={feed.state().kind === "ready"}>
          <For each={rows()}>
            {(row) => (
              <box
                flexDirection="row"
                gap={GROUP_GAP}
                paddingLeft={CONTROL_INDENT}
              >
                <For each={row.groups}>
                  {(group) => (
                    <box flexDirection="row" gap={CHOICE_GAP}>
                      <For each={group.segments}>
                        {(segment) => (
                          <text
                            fg={theme.text.action.primary.base}
                            selectable={false}
                            onMouseDown={() => choose(group.kind, segment.mode)}
                          >
                            {segment.bold ? (
                              <b>{segment.text}</b>
                            ) : (
                              segment.text
                            )}
                          </text>
                        )}
                      </For>
                    </box>
                  )}
                </For>
              </box>
            )}
          </For>
          <Show when={warning()}>
            <text
              fg={theme.text.muted}
              paddingLeft={CONTROL_INDENT}
              wrapMode="word"
            >
              {warning()}
            </text>
          </Show>
        </Show>
        <For each={breakdownLines(feed.state(), breakdown(), unit())}>
          {(line) => (
            <Show
              when={breakdownFits(dimensions().width, line)}
              fallback={
                <box flexDirection="column">
                  <text
                    fg={theme.text.muted}
                    paddingLeft={CONTROL_INDENT}
                    truncate
                  >
                    {line.label}
                  </text>
                  <text
                    fg={theme.text.muted}
                    paddingLeft={CONTROL_INDENT * 2}
                    wrapMode="char"
                  >
                    {line.amount}
                  </text>
                </box>
              }
            >
              <box flexDirection="row" gap={1} paddingLeft={CONTROL_INDENT}>
                <text fg={theme.text.muted} flexGrow={1} truncate>
                  {line.label}
                </text>
                <text fg={theme.text.muted}>{line.amount}</text>
              </box>
            </Show>
          )}
        </For>
      </Show>
    </box>
  );
}

export function CostFooter(props: {
  readonly context: Plugin.Context;
}): JSX.Element {
  const { feed, view, toggle, unitState } = useCostBlock(props.context);
  return (
    <box onMouseDown={toggle}>
      <text
        fg={
          feed.state().kind === "error"
            ? props.context.theme.text.feedback.error.base
            : props.context.theme.text.muted
        }
        truncate
      >
        {footerLine(feed.state(), view.open, unitState.unit)}
      </text>
    </box>
  );
}

export default Plugin.define({
  id: "opencode-cmon-tui",
  setup(context) {
    const sidebar = context.ui.slot({
      prepend: "sidebar.content",
      render: () => <CostSidebar context={context} />,
    });
    const footer = context.ui.slot({
      append: "home.footer.status",
      render: () => <CostFooter context={context} />,
    });
    return async () => {
      await sidebar();
      await footer();
    };
  },
});
