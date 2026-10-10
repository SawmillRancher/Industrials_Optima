"""Fiscal-period helpers for Copart (fiscal year ends July 31)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


def _d(s: str) -> date:
    y, m, dd = (int(x) for x in s.split("-"))
    return date(y, m, dd)


def duration_days(start: str, end: str) -> int:
    return (_d(end) - _d(start)).days


def classify_duration(start: str | None, end: str) -> str:
    """Classify a duration fact as Q (3mo), H (6mo), N (9mo) or FY (12mo)."""
    if start is None:
        return "INSTANT"
    days = duration_days(start, end)
    if 80 <= days <= 100:
        return "Q"
    if 170 <= days <= 200:
        return "H"
    if 260 <= days <= 285:
        return "N"
    if 350 <= days <= 380:
        return "FY"
    return "OTHER"


def fiscal_year(end: str) -> int:
    """Copart fiscal year for a period ending ``end`` (FYE July 31).

    Aug-Dec belong to the *next* calendar year's fiscal year.
    """
    y, m, _ = (int(x) for x in end.split("-"))
    return y + 1 if m >= 8 else y


def fiscal_quarter(end: str) -> int | None:
    """Fiscal quarter number (1-4) from the period-end month."""
    m = int(end.split("-")[1])
    return {10: 1, 11: 1, 1: 2, 2: 2, 4: 3, 5: 3, 7: 4, 8: 4}.get(m)


@dataclass(frozen=True, order=True)
class Period:
    """A reporting period keyed for sorting and display."""

    end: str
    kind: str  # "FY" or "Q"

    @property
    def fy(self) -> int:
        return fiscal_year(self.end)

    @property
    def q(self) -> int | None:
        return fiscal_quarter(self.end)

    @property
    def label(self) -> str:
        if self.kind == "FY":
            return f"FY{self.fy}"
        return f"Q{self.q} FY{self.fy}"

    @property
    def sort_key(self) -> str:
        return self.end
