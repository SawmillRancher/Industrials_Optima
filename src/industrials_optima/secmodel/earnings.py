"""Parse Copart's non-GAAP reconciliation tables from 8-K earnings releases.

Copart reported non-GAAP net income and non-GAAP diluted EPS in its quarterly
earnings press releases (Exhibit 99.1 of the Item 2.02 Form 8-K) from fiscal
2016 through fiscal 2023, reverting to pure-GAAP reporting thereafter.  This
module extracts those reconciliation tables — the only "adjusted" figures the
company publishes — so the model can present them exactly as reported.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from bs4 import BeautifulSoup

from .edgar import EdgarClient
from .periods import fiscal_quarter, fiscal_year

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

# canonical row keys, in display order
RECON_ROWS = [
    ("gaap_ni", "GAAP net income attributable to Copart, Inc."),
    ("adj_repat", "  Deemed repatriation of foreign earnings, net of tax"),
    ("adj_tcja", "  Tax Cuts & Jobs Act / discrete tax items, net of tax"),
    ("adj_disposal", "  Disposal of non-operating assets, net of tax"),
    ("adj_impair", "  Impairment of long-lived assets, net of tax"),
    ("adj_acq", "  Acquisition-related fees & integration charges, net of tax"),
    ("adj_salestax", "  Reserve for legacy sales-tax liabilities, net of tax"),
    ("adj_fx", "  Foreign currency-related (gains) losses, net of tax"),
    ("adj_asu", "  Stock-option tax effects (ASU 2016-09), net of tax"),
    ("adj_payroll", "  Payroll taxes on executive stock compensation, net of tax"),
    ("adj_other", "  Other adjustments, net of tax"),
    ("ng_ni", "Non-GAAP net income attributable to Copart, Inc."),
    ("gaap_eps", "GAAP diluted EPS ($)"),
    ("ng_eps", "Non-GAAP diluted EPS ($)"),
    ("gaap_sh", "GAAP diluted shares (m)"),
    ("ng_sh", "Non-GAAP diluted shares (m)"),
]
DOLLAR_KEYS = {k for k, _ in RECON_ROWS if k not in ("gaap_eps", "ng_eps", "gaap_sh", "ng_sh")}
SHARE_KEYS = {"gaap_sh", "ng_sh"}
EPS_KEYS = {"gaap_eps", "ng_eps"}


def _canon(label: str) -> Optional[str]:
    l = re.sub(r"\s+", " ", label).strip().lower()
    if not l:
        return None
    per_share = "per share" in l or "per common share" in l or "per diluted" in l
    # --- per-share and share-count rows first (they also contain "net income") ---
    if per_share:
        return "ng_eps" if "non-gaap" in l else "gaap_eps"
    if "shares" in l or "common equivalent" in l:
        if "common equivalent" in l or "effect on" in l:
            return "adj_sh_asu"  # a shares adjustment; not part of the NI bridge
        return "ng_sh" if "non-gaap" in l else "gaap_sh"
    # --- net income totals ---
    if "non-gaap net income" in l:
        return "ng_ni"
    if "gaap net income" in l:
        return "gaap_ni"
    # --- individual adjustments (net of tax) ---
    if "repatriation" in l or "deemed" in l:
        return "adj_repat"
    if "tax cuts" in l or "jobs act" in l or "transition tax" in l:
        return "adj_tcja"
    if "disposal" in l:
        return "adj_disposal"
    if "impairment" in l:
        return "adj_impair"
    if "acquisition" in l or "integration" in l:
        return "adj_acq"
    if "sales tax" in l:
        return "adj_salestax"
    if "foreign currency" in l or "currency-related" in l or "currency related" in l:
        return "adj_fx"
    if "2016-09" in l or "stock option" in l or "stock-based compensation" in l or "excess tax" in l:
        return "adj_asu"
    if "payroll tax" in l:
        return "adj_payroll"
    if l.startswith("effect of"):
        return "adj_other"  # an adjustment without a dedicated row
    return None


def _numbers(cells: list[str]) -> list[Optional[float]]:
    """Extract signed numbers from a row's post-label cells (handles split
    ``(1,234`` / ``)`` cells and ``—`` dashes)."""
    s = " ".join(cells)
    out: list[Optional[float]] = []
    for tok in re.findall(r"\(\s*[\d,]+(?:\.\d+)?\s*\)|[\d,]+(?:\.\d+)?|—|–|-", s):
        t = tok.strip()
        if t in ("—", "–", "-"):
            out.append(None)
            continue
        neg = t.startswith("(")
        val = float(re.sub(r"[(),\s]", "", t))
        out.append(-val if neg else val)
    return out


@dataclass
class NonGaap:
    # (period_end, kind) -> {row_key: value}; dollar rows in raw $ thousands
    data: dict = field(default_factory=dict)
    sources: dict = field(default_factory=dict)  # (end,kind) -> accession

    def add(self, end: str, kind: str, key: str, value: float, acc: str):
        self.data.setdefault((end, kind), {})[key] = value
        self.sources[(end, kind)] = acc


def _parse_period_header(rows: list[list[str]]):
    """Find (label -> [(period_end, kind)]) column mapping from header rows.

    Returns a list aligned to the numeric-column order, each entry being
    (period_end_str, 'Q'|'FY') or None to skip that column.
    """
    # locate a row mentioning "Months Ended" and the following year row
    span_row = year_row = None
    for i, r in enumerate(rows):
        joined = " ".join(r).lower()
        if "months ended" in joined:
            span_row = r
            if i + 1 < len(rows):
                year_row = rows[i + 1]
            break
    if not span_row or not year_row:
        return None
    # spans: e.g. ["Three Months Ended July 31,", "Twelve Months Ended July 31,"]
    spans = []
    for cell in span_row:
        m = re.search(r"(three|six|nine|twelve)\s+months\s+ended\s+([a-z]+)\s+(\d{1,2})", cell.lower())
        if m:
            spans.append((m.group(1), _MONTHS[m.group(2)], int(m.group(3))))
    years = [int(t) for t in year_row if re.fullmatch(r"\d{4}", t.strip())]
    if not spans or not years:
        return None
    # years are laid out as [cur, prior] under each span in order
    per_span = len(years) // len(spans) if len(spans) else 0
    if per_span == 0:
        return None
    cols = []
    yi = 0
    for span, mon, day in spans:
        for j in range(per_span):
            if yi >= len(years):
                break
            yr = years[yi]; yi += 1
            end = f"{yr:04d}-{mon:02d}-{day:02d}"
            if j == 0:  # current-year column only
                kind = "FY" if span == "twelve" else ("Q" if span == "three" else "SKIP")
                cols.append((end, kind))
            else:
                cols.append(None)  # prior-year comparative — skip
    return cols


def load_nongaap(client: EdgarClient, min_fy: int = 2011) -> NonGaap:
    subs = client.submissions()["filings"]["recent"]
    rows = list(zip(subs["form"], subs["filingDate"], subs["accessionNumber"],
                    subs.get("items", [""] * len(subs["form"]))))
    result = NonGaap()
    for form, fdate, acc, items in rows:
        if form != "8-K" or "2.02" not in (items or ""):
            continue
        if fdate < "2011-08-01":
            continue
        html = client.earnings_exhibit(acc)
        if not html or "non-gaap" not in html.lower():
            continue
        _parse_release(html, acc, result)
    return result


def _parse_release(html: str, acc: str, result: NonGaap) -> None:
    soup = BeautifulSoup(html, "html.parser")
    seen_other: set = set()  # (end, kind, raw label) — avoid double counting
    for tbl in soup.find_all("table"):
        txt = tbl.get_text(" ").lower()
        if "non-gaap net income" not in txt:
            continue
        rows = []
        for tr in tbl.find_all("tr"):
            cells = [re.sub(r"\s+", " ", c.get_text(" ")).strip()
                     for c in tr.find_all(["td", "th"])]
            cells = [c for c in cells if c not in ("", "$", "%")]
            if cells:
                rows.append(cells)
        cols = _parse_period_header(rows)
        if not cols:
            continue
        for r in rows:
            key = _canon(r[0])
            if key is None or key == "adj_sh_asu":
                continue
            nums = _numbers(r[1:])
            # align numbers to columns; the first len(cols) numbers correspond
            for ci, colspec in enumerate(cols):
                if colspec is None or ci >= len(nums):
                    continue
                end, kind = colspec
                if kind == "SKIP":
                    continue
                val = nums[ci]
                if val is None:
                    continue
                # accumulate 'other' adjustments (multiple distinct lines)
                if key == "adj_other":
                    sig = (end, kind, re.sub(r"\s+", " ", r[0]).strip().lower())
                    if sig in seen_other:
                        continue
                    seen_other.add(sig)
                    cur = result.data.get((end, kind), {}).get("adj_other", 0.0)
                    result.add(end, kind, "adj_other", cur + val, acc)
                else:
                    result.add(end, kind, key, val, acc)
