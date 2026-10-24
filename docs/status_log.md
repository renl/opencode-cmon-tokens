# Code changes

## Dollar and token display

- Clickable `$` and `Tokens` controls switch the monthly total and agent, model and provider breakdowns.
- Dollars are the default; the selected unit is shared by the sidebar and footer for the current session.
- Token totals include input, output, reasoning, cached reads and cached writes without double counting.
- Compact decimal suffixes `k`, `M` and `B` use up to two fractional digits; exact counts and sorting remain unchanged internally.
- Partial token coverage is marked explicitly; unavailable counts are not presented as zero.

## Responsive panel

- Breakdown and unit controls use separate rows and wrap only between complete choices.
- Layout follows the panel's available width rather than the terminal's full width.
- Long breakdown names truncate before numeric amounts.

## Installation

- Local directory configuration points to the built `dist` directory, which contains server, TUI and RPC entrypoints.
- [Installation and update instructions](../README.md) cover Windows, macOS and Linux.

Dollar calculations, reporting tools, recording, retention and historical repair behavior are unaffected by display-unit selection.
