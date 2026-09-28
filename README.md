# Offline trade diagnostic — synthetic example

**Self-initiated portfolio sample, not client work or a profitable strategy.** `trade_diagnostic_demo.py` uses only the Python standard library. Its built-in four-trade example is synthetic and is reproduced in `trade_diagnostic_demo.md` and `.json`.

Run `python trade_diagnostic_demo.py --self-check` to verify fee arithmetic, closed-balance drawdown, input ordering and invalid-input rejection. Run `python trade_diagnostic_demo.py --demo` to regenerate the synthetic reports; that command replaces only the bundled demo outputs.

For a separate normalized input, run `python trade_diagnostic_demo.py --input normalized.json --output-prefix NEW_REPORT_PREFIX`. The output prefix must not exist. Input shape:

```json
{
  "initial_balance": "1000",
  "trades": [
    {"id": "T1", "closed_at": "2026-01-01T12:00:00+00:00", "gross_pnl": "100", "commission": "-2", "swap": "0"}
  ]
}
```

All amounts use one currency. Fees are negative and rebates positive. Use one row per closed position, sorted by timezone-aware close time. The script rejects missing or duplicate IDs, invalid amounts and unordered timestamps. It reports gross and net P&L, win rate, profit factor and maximum drawdown of **balances after each close**. It does not read floating equity, deposits, withdrawals, partial-position history or broker reports directly. Supplied costs are included but their completeness is not independently verified. No backtest, future-return estimate or profitability certification is made.

## Request a scoped review

Reference price: **USD 50** for one agreed normalized closed-trade export with up to 2,000 rows, a calculation report and one correction round. Raw MT5 statement parsing, strategy changes, parameter optimization and additional evidence checks need separate scope and price. The source schema, currency, cost fields, schedule, payment and data-transfer method must be agreed before work starts.

Open a GitHub issue with only the approximate trade count, export format, cost-field names and review question. **Issues are public: do not upload account numbers, statements, credentials, private datasets or confidential links.** An inquiry is not an accepted order.

AI-assisted code and executable checks are used. The buyer retains the original data; no broker connection or trading access is required.
