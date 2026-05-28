"""CLI for building a parameterized industrial 3-statement model template."""

from __future__ import annotations

import argparse
from pathlib import Path

from .builder import build_template
from .config import CompanyConfig, SegmentLine


def _parse_segments(values: list[str] | None) -> list[SegmentLine]:
    if not values:
        return []
    return [SegmentLine(name=v) for v in values]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate an industrial 3-statement model template "
            "(Model / Bull-Base-Bear / DCF / Charts), modeled on the Moog Inc. workbook."
        )
    )
    parser.add_argument("--company", required=True, help="Company name (e.g., 'Acme Industries')")
    parser.add_argument("--ticker", required=True, help="Ticker symbol (e.g., 'ACME')")
    parser.add_argument(
        "-o",
        "--output",
        default="Industrial_Model_Template.xlsx",
        help="Output .xlsx path (default: ./Industrial_Model_Template.xlsx)",
    )
    parser.add_argument(
        "--segment",
        action="append",
        dest="segments_current",
        help="Current reportable segment name; pass once per segment (in order)",
    )
    parser.add_argument(
        "--legacy-segment",
        action="append",
        dest="segments_legacy",
        help="Legacy reportable segment name; pass once per segment (in order)",
    )
    parser.add_argument(
        "--share-price",
        type=float,
        default=100.0,
        help="Current share price for valuation anchors (default 100)",
    )
    parser.add_argument("--currency-symbol", default="$")
    parser.add_argument("--currency-units", default="millions")
    parser.add_argument(
        "--basis",
        default="US GAAP as reported",
        help="Accounting basis line for the header (e.g., 'US GAAP', 'IFRS')",
    )
    parser.add_argument(
        "--risk-free-rate", type=float, default=0.043, help="DCF: risk-free rate"
    )
    parser.add_argument(
        "--equity-risk-premium", type=float, default=0.055, help="DCF: ERP"
    )
    parser.add_argument("--beta", type=float, default=1.0, help="DCF: levered beta")
    parser.add_argument(
        "--pretax-cost-of-debt", type=float, default=0.05, help="DCF: pre-tax cost of debt"
    )
    parser.add_argument("--tax-rate", type=float, default=0.24, help="DCF: long-run tax rate")
    parser.add_argument(
        "--target-dv", type=float, default=0.20, help="DCF: target debt / total capital"
    )
    parser.add_argument(
        "--terminal-growth", type=float, default=0.025, help="DCF: terminal growth rate"
    )

    args = parser.parse_args(argv)

    cfg = CompanyConfig(
        company_name=args.company,
        ticker=args.ticker,
        currency_symbol=args.currency_symbol,
        currency_units=args.currency_units,
        accounting_basis=args.basis,
        current_share_price=args.share_price,
        segments_current=_parse_segments(args.segments_current),
        segments_legacy=_parse_segments(args.segments_legacy),
        risk_free_rate=args.risk_free_rate,
        equity_risk_premium=args.equity_risk_premium,
        levered_beta=args.beta,
        pretax_cost_of_debt=args.pretax_cost_of_debt,
        tax_rate=args.tax_rate,
        target_debt_to_value=args.target_dv,
        terminal_growth=args.terminal_growth,
    )

    output_path = build_template(cfg, Path(args.output))
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
