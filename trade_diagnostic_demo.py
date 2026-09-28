"""Offline closed-trade diagnostic. --demo uses SYNTHETIC data only.

Optional input: --input normalized.json --output-prefix path/to/report
JSON shape: {"initial_balance":"1000", "trades":[{"id":"T1",
"closed_at":"2026-01-01T12:00:00+00:00", "gross_pnl":"100",
"commission":"-2", "swap":"0"}]}. All amounts use one currency.
Fees are negative; rebates are positive. Use one row per closed position.
Deposits/withdrawals are unsupported. Non-demo output files must be new.
"""

import argparse
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


def money(value, field):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError(f"{field}: amount must be a decimal string or number")
    try:
        amount = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(f"{field}: invalid amount") from exc
    if not amount.is_finite():
        raise ValueError(f"{field}: amount must be finite")
    return amount


def percent(numerator, denominator):
    return str((numerator / denominator * 100).quantize(Decimal("0.0001"))) + "%"


def analyze(data, synthetic=False):
    if not isinstance(data, dict) or not isinstance(data.get("trades"), list):
        raise ValueError("Expected an object with a trades array")
    initial = money(data.get("initial_balance"), "initial_balance")
    if initial <= 0:
        raise ValueError("initial_balance must be positive")

    balance = peak = initial
    max_drawdown = Decimal(0)
    max_drawdown_pct = Decimal(0)
    gross_total = commission_total = swap_total = gains = losses = Decimal(0)
    wins = 0
    seen = set()
    previous = None
    rows = []
    for i, trade in enumerate(data["trades"], 1):
        if not isinstance(trade, dict):
            raise ValueError(f"trade {i}: expected an object")
        ident = trade.get("id")
        if not isinstance(ident, str) or not ident.strip() or ident in seen:
            raise ValueError(f"trade {i}: id missing or duplicate")
        seen.add(ident)
        raw_date = trade.get("closed_at")
        if not isinstance(raw_date, str):
            raise ValueError(f"trade {i}: closed_at must be an ISO timestamp with timezone")
        try:
            closed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"trade {i}: invalid closed_at") from exc
        if closed.utcoffset() is None:
            raise ValueError(f"trade {i}: closed_at must include a timezone")
        if previous is not None and closed < previous:
            raise ValueError(f"trade {i}: trades must be sorted by closed_at")
        previous = closed
        gross = money(trade.get("gross_pnl"), f"trade {i} gross_pnl")
        commission = money(trade.get("commission"), f"trade {i} commission")
        swap = money(trade.get("swap"), f"trade {i} swap")
        net = gross + commission + swap
        gross_total += gross
        commission_total += commission
        swap_total += swap
        if net > 0:
            gains += net
            wins += 1
        elif net < 0:
            losses += -net
        balance += net
        peak = max(peak, balance)
        drawdown = peak - balance
        if drawdown > max_drawdown:
            max_drawdown = drawdown
        max_drawdown_pct = max(max_drawdown_pct, drawdown / peak)
        rows.append({"id": ident, "closed_at": closed.isoformat(),
                     "net_pnl": str(net), "closed_balance": str(balance),
                     "drawdown": str(drawdown)})

    count = len(rows)
    return {
        "label": "SYNTHETIC / 合成数据" if synthetic else "USER-SUPPLIED / 用户提供数据",
        "trade_count": count,
        "initial_balance": str(initial),
        "gross_pnl_total": str(gross_total),
        "commission_total": str(commission_total),
        "swap_total": str(swap_total),
        "net_pnl_total": str(gross_total + commission_total + swap_total),
        "winning_net_total": str(gains),
        "losing_net_total": str(-losses),
        "profit_factor": str((gains / losses).quantize(Decimal("0.0001"))) if losses else None,
        "profit_factor_note": "Undefined: no losing trades" if not losses else None,
        "win_rate": percent(Decimal(wins), Decimal(count)) if count else None,
        "max_closed_balance_drawdown": str(max_drawdown),
        "max_closed_balance_drawdown_pct": str((max_drawdown_pct * 100).quantize(Decimal("0.0001"))) + "%",
        "first_close": rows[0]["closed_at"] if rows else None,
        "last_close": rows[-1]["closed_at"] if rows else None,
        "trades": rows,
        "limitations": [
            "Drawdown uses balances after each close, not floating equity.",
            "The date span is not a count of trading days.",
            "Cost fields are included as supplied; their completeness is not independently verified.",
            "No backtest, profitability claim, or future-return estimate is made."
        ],
    }


def markdown(report):
    r = report
    lines = [f"# Trade diagnostic — {r['label']}", "",
             "Offline closed-trade illustration. Amounts use one currency.", "",
             f"Trades: **{r['trade_count']}**. Gross P&L: **{r['gross_pnl_total']}**; "
             f"commission: **{r['commission_total']}**; swap: **{r['swap_total']}**; "
             f"net P&L: **{r['net_pnl_total']}**.",
             f"Winning net total: **{r['winning_net_total']}**; losing net total: "
             f"**{r['losing_net_total']}**. Profit factor: **{r['profit_factor'] or 'N/A'}**"
             f"{(' (' + r['profit_factor_note'] + ')') if r['profit_factor_note'] else ''}; "
             f"win rate: **{r['win_rate'] or 'N/A'}**.",
             f"Maximum closed-balance drawdown: **{r['max_closed_balance_drawdown']}** "
             f"(**{r['max_closed_balance_drawdown_pct']}**).",
             f"First / last close: {r['first_close'] or 'N/A'} / {r['last_close'] or 'N/A'}.", "",
             "| ID | Closed at | Net P&L | Closed balance | Drawdown |",
             "| --- | --- | ---: | ---: | ---: |"]
    for t in r["trades"]:
        lines.append(f"| {t['id']} | {t['closed_at']} | {t['net_pnl']} | "
                     f"{t['closed_balance']} | {t['drawdown']} |")
    lines += ["", "Limits:"] + [f"- {item}" for item in r["limitations"]]
    return "\n".join(lines) + "\n"


def demo_data():
    return {"initial_balance": "1000", "trades": [
        {"id": "S1", "closed_at": "2026-01-01T12:00:00+00:00", "gross_pnl": "100", "commission": "-2", "swap": "0"},
        {"id": "S2", "closed_at": "2026-01-02T12:00:00+00:00", "gross_pnl": "-60", "commission": "-2", "swap": "-1"},
        {"id": "S3", "closed_at": "2026-01-04T12:00:00+00:00", "gross_pnl": "-40", "commission": "-1", "swap": "0"},
        {"id": "S4", "closed_at": "2026-01-05T12:00:00+00:00", "gross_pnl": "80", "commission": "-2", "swap": "1"},
    ]}


def self_check():
    data = demo_data()
    r = analyze(data, synthetic=True)
    assert [t["net_pnl"] for t in r["trades"]] == ["98", "-63", "-41", "79"]
    assert [t["closed_balance"] for t in r["trades"]] == ["1098", "1035", "994", "1073"]
    assert (r["gross_pnl_total"], r["commission_total"], r["swap_total"], r["net_pnl_total"]) == ("80", "-7", "0", "73")
    assert (r["profit_factor"], r["win_rate"], r["max_closed_balance_drawdown"], r["max_closed_balance_drawdown_pct"]) == ("1.7019", "50.0000%", "104", "9.4718%")
    cases = [
        {**data, "trades": list(reversed(data["trades"]))},
        {**data, "trades": [dict(data["trades"][0], gross_pnl="NaN")]},
        {**data, "trades": [dict(data["trades"][0], closed_at="2026-01-01T12:00:00")]},
        {**data, "trades": [data["trades"][0], data["trades"][0]]},
        {**data, "initial_balance": "0"},
    ]
    for bad in cases:
        try:
            analyze(bad)
        except ValueError:
            continue
        raise AssertionError("Invalid input was accepted")
    no_loss = {**data, "trades": [data["trades"][0]]}
    assert analyze(no_loss)["profit_factor"] is None
    print("SELF-CHECK PASS: fees, drawdown, sorting, invalid input, zero-loss PF")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--demo", action="store_true")
    mode.add_argument("--self-check", action="store_true")
    mode.add_argument("--input", type=Path, help="normalized JSON input")
    parser.add_argument("--output-prefix", type=Path, help="required with --input")
    args = parser.parse_args()
    if args.self_check:
        self_check()
        return
    if args.demo:
        if args.output_prefix:
            parser.error("--output-prefix is for --input")
        data = demo_data()
        prefix = Path(__file__).with_suffix("")
    else:
        if not args.output_prefix:
            parser.error("--input requires --output-prefix")
        data = json.loads(args.input.read_text(encoding="utf-8"), parse_float=Decimal)
        prefix = args.output_prefix
    report = analyze(data, synthetic=args.demo)
    paths = [prefix.with_suffix(".json"), prefix.with_suffix(".md")]
    if not args.demo and any(path.exists() for path in paths):
        parser.error("Refusing to overwrite existing files; choose a new output prefix")
    for path, content in zip(paths, [json.dumps(report, ensure_ascii=False, indent=2) + "\n", markdown(report)]):
        with path.open("w" if args.demo else "x", encoding="utf-8") as handle:
            handle.write(content)
    print(f"Wrote {prefix.with_suffix('.md')} and {prefix.with_suffix('.json')}")


if __name__ == "__main__":
    main()
