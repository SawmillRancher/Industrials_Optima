"""Assemble Copart's financial history from SEC filings.

Two data sources, both SEC EDGAR:

* **Consolidated** income statement / balance sheet / cash-flow lines come from
  the aggregated ``companyfacts`` API (reliable, all periods).
* **Segment** figures (United States vs International) are parsed out of each
  10-K / 10-Q XBRL *instance*, because ``companyfacts`` discards the
  dimensional (segment) breakdown.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .edgar import EdgarClient
from .periods import Period, classify_duration, fiscal_quarter, fiscal_year
from .xbrl import Fact, parse_instance

COPART_CIK = "900075"

# ---------------------------------------------------------------------------
# Consolidated line items.  Each entry lists candidate us-gaap concepts in
# priority order (first one that has a value for the period wins), so the model
# survives Copart's tag changes over 15 years (e.g. SalesRevenueNet ->
# RevenueFromContractWithCustomerIncludingAssessedTax).
# ---------------------------------------------------------------------------
FLOW = "flow"  # duration fact (income statement / cash flow)
STOCK = "stock"  # instant fact (balance sheet)
PS = "ps"  # per-share (duration, not additive)

@dataclass
class Line:
    key: str
    label: str
    concepts: list[str]
    kind: str = FLOW
    bold: bool = False
    indent: int = 0
    blank_before: bool = False


INCOME_STATEMENT: list[Line] = [
    Line("rev_service", "Service revenues", ["SalesRevenueServicesNet"], indent=1),
    Line("rev_vehicle", "Vehicle sales", ["SalesRevenueGoodsNet"], indent=1),
    Line(
        "revenue",
        "Total revenues",
        [
            "RevenueFromContractWithCustomerIncludingAssessedTax",
            "SalesRevenueNet",
            "Revenues",
        ],
        bold=True,
    ),
    Line("cost_yard", "Yard operations", ["DirectOperatingCosts"], indent=1, blank_before=True),
    Line("cost_vehicle", "Cost of vehicle sales", ["CostDirectMaterial", "CostOfGoodsSold"], indent=1),
    Line("gross_profit", "Gross profit", ["GrossProfit"], bold=True),
    Line("gna", "General & administrative", ["GeneralAndAdministrativeExpense"], indent=1),
    Line("operating_income", "Operating income", ["OperatingIncomeLoss"], bold=True),
    Line(
        "other_income",
        "Other income / (expense), net",
        ["NonoperatingIncomeExpense", "InterestIncomeExpenseNonoperatingNet"],
        indent=1,
        blank_before=True,
    ),
    Line(
        "pretax_income",
        "Income before income taxes",
        [
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
            "IncomeLossFromContinuingOperationsBeforeIncomeTaxesMinorityInterestAndIncomeLossFromEquityMethodInvestments",
        ],
        bold=True,
    ),
    Line("income_tax", "Income tax expense", ["IncomeTaxExpenseBenefit"], indent=1),
    Line("net_income", "Net income", ["NetIncomeLoss"], bold=True),
    Line("eps_basic", "EPS — basic", ["EarningsPerShareBasic"], kind=PS, blank_before=True),
    Line("eps_diluted", "EPS — diluted", ["EarningsPerShareDiluted"], kind=PS),
    Line(
        "sh_basic",
        "Wtd. avg. shares — basic",
        ["WeightedAverageNumberOfSharesOutstandingBasic"],
    ),
    Line(
        "sh_diluted",
        "Wtd. avg. shares — diluted",
        ["WeightedAverageNumberOfDilutedSharesOutstanding"],
    ),
]

BALANCE_SHEET: list[Line] = [
    Line(
        "cash",
        "Cash & cash equivalents",
        [
            "CashAndCashEquivalentsAtCarryingValue",
            "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents",
        ],
        kind=STOCK,
    ),
    Line("current_assets", "Total current assets", ["AssetsCurrent"], kind=STOCK),
    Line("ppe_net", "Property & equipment, net", ["PropertyPlantAndEquipmentNet"], kind=STOCK),
    Line("goodwill", "Goodwill", ["Goodwill"], kind=STOCK),
    Line("total_assets", "Total assets", ["Assets"], kind=STOCK, bold=True),
    Line("current_liab", "Total current liabilities", ["LiabilitiesCurrent"], kind=STOCK, blank_before=True),
    Line(
        "long_term_debt",
        "Long-term debt",
        ["LongTermDebtNoncurrent", "LongTermDebtAndCapitalLeaseObligations", "LongTermDebt"],
        kind=STOCK,
    ),
    Line("total_liab", "Total liabilities", ["Liabilities"], kind=STOCK, bold=True),
    Line(
        "equity",
        "Total stockholders' equity",
        [
            "StockholdersEquity",
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",
        ],
        kind=STOCK,
        bold=True,
    ),
]

CASH_FLOW: list[Line] = [
    Line("cfo", "Cash from operations", ["NetCashProvidedByUsedInOperatingActivities"], bold=True),
    Line("dna", "Depreciation & amortization", ["DepreciationDepletionAndAmortization"], indent=1),
    Line("sbc", "Stock-based compensation", ["ShareBasedCompensation"], indent=1),
    Line(
        "capex",
        "Capital expenditures",
        ["PaymentsToAcquireProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"],
        indent=1,
    ),
    Line("cfi", "Cash from investing", ["NetCashProvidedByUsedInInvestingActivities"], bold=True, blank_before=True),
    Line("cff", "Cash from financing", ["NetCashProvidedByUsedInFinancingActivities"], bold=True),
]

# ---------------------------------------------------------------------------
# Segment (US vs International) metrics parsed from filing instances.
# ---------------------------------------------------------------------------
SEG_METRICS = [
    ("revenue", "Revenue", FLOW,
     ["SalesRevenueNet", "Revenues",
      "RevenueFromContractWithCustomerIncludingAssessedTax",
      "RevenueFromContractWithCustomerExcludingAssessedTax"]),
    ("operating_income", "Operating income", FLOW, ["OperatingIncomeLoss"]),
    ("dna", "Depreciation & amortization", FLOW,
     ["DepreciationDepletionAndAmortization", "Depreciation"]),
    ("capex", "Capital expenditures", FLOW,
     ["PaymentsToAcquireProductiveAssets", "PaymentsToAcquirePropertyPlantAndEquipment"]),
    ("assets", "Total assets", STOCK, ["Assets"]),
    ("goodwill", "Goodwill", STOCK, ["Goodwill"]),
]

# Geographic / business-segment members, bucketed into the two reported
# segments.  Priority order — earlier entries preferred when several map to the
# same bucket.  Sub-country members (GB, DE, Canada, OtherSegment) are
# intentionally excluded to avoid double counting the segment totals.
US_MEMBERS = ["USMember", "US", "UnitedStatesMember", "UnitedStatesSegmentMember",
              "USSegmentMember", "NorthAmericaMember", "CountryUS", "DomesticMember"]
INTL_MEMBERS = ["InternationalMember", "InternationalSegmentMember",
                "NonUsMember", "ForeignMember"]
_SEG_AXES = {"StatementGeographicalAxis", "StatementBusinessSegmentsAxis"}
_ALLOWED_SEG_DIM_KEYS = _SEG_AXES | {"ConsolidationItemsAxis"}


def _bucket(dims: dict) -> Optional[str]:
    """Return 'US', 'International' or None for a fact's dimensions."""
    if not dims:
        return None
    if "ProductOrServiceAxis" in dims:  # service/vehicle split — not a segment total
        return None
    if set(dims) - _ALLOWED_SEG_DIM_KEYS:  # some other subdividing axis
        return None
    members = {dims[a] for a in _SEG_AXES if a in dims}
    if not members:
        return None
    if members & set(US_MEMBERS):
        return "US"
    if members & set(INTL_MEMBERS):
        return "International"
    return None


def _member_score(dims: dict) -> int:
    members = {dims[a] for a in _SEG_AXES if a in dims}
    best = 0
    for i, m in enumerate(US_MEMBERS + INTL_MEMBERS):
        if m in members:
            best = max(best, 100 - i)
    if dims.get("ConsolidationItemsAxis") == "OperatingSegmentsMember":
        best += 200
    return best


# ---------------------------------------------------------------------------
@dataclass
class CopartModel:
    client: EdgarClient
    # consolidated: concept -> end -> {kind: value}; instants: concept -> end -> value
    flows: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(dict)))
    instants: dict = field(default_factory=lambda: defaultdict(dict))
    # segments: metric -> (end, kind) -> bucket -> value
    seg: dict = field(default_factory=lambda: defaultdict(lambda: defaultdict(dict)))
    seg_source: dict = field(default_factory=dict)  # (end,kind)->accession
    nongaap: object = None  # earnings.NonGaap — 8-K non-GAAP reconciliations
    annual_ends: list = field(default_factory=list)
    quarter_ends: list = field(default_factory=list)

    # -- consolidated from companyfacts -------------------------------------
    def load_consolidated(self) -> None:
        facts = self.client.company_facts()["facts"]
        gaap = facts.get("us-gaap", {})
        for concept, node in gaap.items():
            for unit, items in node.get("units", {}).items():
                for it in items:
                    end = it["end"]
                    start = it.get("start")
                    val = it.get("val")
                    if val is None:
                        continue
                    if start is None:
                        # instant (balance sheet) — keep the latest-filed value
                        self.instants[concept][end] = val
                    else:
                        kind = classify_duration(start, end)
                        if kind in ("Q", "H", "N", "FY"):
                            self.flows[concept][end][kind] = val

    # -- segments from filing instances -------------------------------------
    def load_segments(self, min_report: str = "2011-08-01") -> None:
        subs = self.client.submissions()["filings"]["recent"]
        rows = list(
            zip(subs["form"], subs["reportDate"], subs["accessionNumber"])
        )
        filings = [
            (form, rpt, acc)
            for form, rpt, acc in rows
            if form in ("10-K", "10-Q") and rpt >= min_report
        ]
        for form, rpt, acc in sorted(filings, key=lambda z: z[1]):
            xml = self.client.instance_document(acc)
            if not xml:
                continue
            try:
                facts = parse_instance(xml)
            except Exception:
                continue
            want_kind = "FY" if form == "10-K" else "Q"
            self._ingest_segment_facts(facts, rpt, want_kind, acc)

    def _ingest_segment_facts(
        self, facts: Iterable[Fact], report_end: str, want_kind: str, acc: str
    ) -> None:
        # index metric concept -> metric key
        concept_to_metric = {}
        metric_kind = {}
        for key, _label, kind, concepts in SEG_METRICS:
            metric_kind[key] = kind
            for c in concepts:
                concept_to_metric.setdefault(c, key)
        # best[(metric,bucket)] = (score, value)
        best: dict = {}
        for f in facts:
            metric = concept_to_metric.get(f.concept)
            if metric is None or f.value is None:
                continue
            bucket = _bucket(f.dims)
            if bucket is None:
                continue
            kind = metric_kind[metric]
            if kind == STOCK:
                if not f.is_instant or f.end != report_end:
                    continue
            else:
                if f.is_instant:
                    continue
                if classify_duration(f.start, f.end) != want_kind:
                    continue
                if f.end != report_end:
                    continue
            score = _member_score(f.dims)
            k = (metric, bucket)
            if k not in best or score > best[k][0]:
                best[k] = (score, f.value)
        pk = (report_end, "FY" if want_kind == "FY" else "Q")
        wrote = False
        for (metric, bucket), (_score, val) in best.items():
            self.seg[metric][pk][bucket] = val
            wrote = True
        if wrote:
            self.seg_source[pk] = acc

    def load_nongaap(self) -> None:
        from .earnings import load_nongaap
        self.nongaap = load_nongaap(self.client)

    def nongaap_value(self, key: str, end: str, kind: str):
        if self.nongaap is None:
            return None
        return self.nongaap.data.get((end, kind), {}).get(key)

    # -- period universe ----------------------------------------------------
    def build_periods(self, first_fy: int) -> None:
        rev = self.flows.get("SalesRevenueNet", {})
        rev2 = self.flows.get("RevenueFromContractWithCustomerIncludingAssessedTax", {})
        rev3 = self.flows.get("Revenues", {})
        ends = set(rev) | set(rev2) | set(rev3)
        annual, quarter = set(), set()
        for end in ends:
            fy = fiscal_year(end)
            if fy < first_fy:
                continue
            kinds = {}
            for src in (rev, rev2, rev3):
                kinds.update(src.get(end, {}))
            if "FY" in kinds:
                annual.add(end)
            if "Q" in kinds:
                quarter.add(end)
            # Q4 quarter-end (Jul 31) also becomes a quarter column (derived)
            if fiscal_quarter(end) == 4 and "FY" in kinds:
                quarter.add(end)
        self.annual_ends = sorted(annual)
        self.quarter_ends = sorted(quarter)

    # -- value accessors ----------------------------------------------------
    def flow_value(self, concepts: list[str], end: str, kind: str) -> Optional[float]:
        for c in concepts:
            v = self.flows.get(c, {}).get(end, {}).get(kind)
            if v is not None:
                return v
        return None

    def instant_value(self, concepts: list[str], end: str) -> Optional[float]:
        for c in concepts:
            v = self.instants.get(c, {}).get(end)
            if v is not None:
                return v
        return None

    def seg_annual(self, metric: str, end: str, bucket: str) -> Optional[float]:
        return self.seg.get(metric, {}).get((end, "FY"), {}).get(bucket)

    def seg_quarter(self, metric: str, end: str, bucket: str, is_stock: bool) -> Optional[float]:
        """Segment value for a quarter, deriving Q4 = FY − (Q1+Q2+Q3)."""
        direct = self.seg.get(metric, {}).get((end, "Q"), {}).get(bucket)
        if direct is not None:
            return direct
        if fiscal_quarter(end) != 4:
            return None
        fy_val = self.seg.get(metric, {}).get((end, "FY"), {}).get(bucket)
        if is_stock:
            return fy_val
        if fy_val is None:
            return None
        fy = fiscal_year(end)
        parts, found = 0.0, 0
        for qend in self.quarter_ends:
            if fiscal_year(qend) == fy and fiscal_quarter(qend) in (1, 2, 3):
                qv = self.seg.get(metric, {}).get((qend, "Q"), {}).get(bucket)
                if qv is None:
                    return None
                parts += qv
                found += 1
        return fy_val - parts if found == 3 else None

    def quarter_flow(self, concepts: list[str], end: str) -> Optional[float]:
        """3-month value for a quarter end, deriving Q4 = FY − (Q1+Q2+Q3)."""
        direct = self.flow_value(concepts, end, "Q")
        if direct is not None:
            return direct
        if fiscal_quarter(end) != 4:
            return None
        fy_val = self.flow_value(concepts, end, "FY")
        if fy_val is None:
            return None
        fy = fiscal_year(end)
        parts = 0.0
        found = 0
        for qend in self.quarter_ends:
            if fiscal_year(qend) == fy and fiscal_quarter(qend) in (1, 2, 3):
                qv = self.flow_value(concepts, qend, "Q")
                if qv is None:
                    return None
                parts += qv
                found += 1
        if found != 3:
            return None
        return fy_val - parts
