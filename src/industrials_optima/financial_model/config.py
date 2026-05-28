"""Configuration objects for the financial model template generator."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class SegmentLine:
    """A reportable segment that appears in the segment-P&L block."""

    name: str
    note: str = ""


@dataclass
class CompanyConfig:
    """Inputs that get stamped into the template at build time.

    All values here drive labels and placeholder constants. Historical
    financial data is NOT supplied via config — those cells are left blank
    so the modeler can drop them in from the company's SEC filings.
    """

    company_name: str
    ticker: str
    description_line: str = "3-Statement Financial Model"
    accounting_basis: str = "US GAAP as reported"
    currency_symbol: str = "$"
    currency_units: str = "millions"
    fiscal_year_note: str = ""
    current_share_price: float = 100.0

    # Current segment structure (used in the FY22+ segment P&L block)
    segments_current: list[SegmentLine] = field(default_factory=list)

    # Optional legacy segment structure (FY10–FY21 block)
    segments_legacy: list[SegmentLine] = field(default_factory=list)

    # DCF assumptions (defaults track the Moog DCF build)
    risk_free_rate: float = 0.043
    equity_risk_premium: float = 0.055
    levered_beta: float = 1.0
    pretax_cost_of_debt: float = 0.05
    tax_rate: float = 0.24
    target_debt_to_value: float = 0.20
    terminal_growth: float = 0.025

    def header_subtitle(self) -> str:
        base = f"{self.accounting_basis} · {self.currency_symbol} {self.currency_units}"
        if self.fiscal_year_note:
            base = f"{base} · {self.fiscal_year_note}"
        return base
