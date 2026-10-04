"""Row definitions for the Teledyne Model tab.

Layout follows the RBA model (itself on the HII template): revenue / segment build → group total →
GAAP income statement → GAAP→adjusted bridges → growth & margins → cash flow → buyback → balance
sheet → working capital → BS schedules → ratios → valuation.

Teledyne reports four segments (Digital Imaging, Instrumentation, Aerospace & Defense Electronics,
Engineered Systems), so the build is a segment P&L (HII-style): segment net sales → segment GAAP
operating income → + acquired-intangible amortization and other items → non-GAAP segment operating
income, less corporate expense. A future-M&A block (scenario lever) adds unallocated acquired sales
and profit. The group KPIs are Teledyne's non-GAAP operating income and non-GAAP EPS.
"""
from __future__ import annotations

from .data import SEGS
from .framework import (FMT_DAYS, FMT_EPS, FMT_NUM, FMT_NUM1, FMT_PCT, FMT_SHR, FMT_X, Row, ratio, yoy)

# ---------------------------------------------------------------------------------------
# Scenario-table rows (absolute row numbers in the scenario columns, right of the notes)
# ---------------------------------------------------------------------------------------
S_EPS_FY, S_EPS_Q3, S_GAAP_FY = 12, 13, 14   # FY26 outlook: high / mid / low
S_TAX, S_CAPEX = 16, 17                      # FY26 point estimates
S_GR = {"di": 20, "inst": 26, "ade": 32, "es": 38}      # organic sales growth levers
S_MG = {"di": 44, "inst": 50, "ade": 56, "es": 62}      # non-GAAP operating margin levers
S_MA, S_BUYB = 68, 74                                   # M&A spend (2027–30), buybacks (2H/26, 2027–30)

SEG_NAMES = {
    "di": "Digital Imaging",
    "inst": "Instrumentation",
    "ade": "Aerospace and Defense Electronics",
    "es": "Engineered Systems",
}
SEG_DESC = {
    "di": "Digital Imaging (infrared / visible / X-ray sensors, cameras & systems; FLIR from 14-May-2021)",
    "inst": "Instrumentation (marine, environmental, electronic test & measurement)",
    "ade": "Aerospace and Defense Electronics (aerospace & defense electronics; Excelitas A&D from Dec-2024)",
    "es": "Engineered Systems (engineered products & services, energy systems)",
}
PRODUCT_LINES = {
    "inst": [("inst_marine", "Marine instrumentation"), ("inst_env", "Environmental instrumentation"),
             ("inst_etm", "Electronic test & measurement")],
    "ade": [("ade_aero", "Aerospace electronics"), ("ade_def", "Defense electronics")],
    "es": [("es_eng", "Engineered products & services"), ("es_energy", "Energy systems")],
}


def srow(base, year):
    """Scenario value row for a 2027E–2030E driver (base row holds the Δ)."""
    return base + (year - 2026)


def _share(x, s):
    """Segment share of acquired-intangible amortization (1H/26)."""
    tot = "+".join(x.abs_at(f"am_{k}", "1H/26") for k in SEGS)
    return f"{x.abs_at('am_' + s, '1H/26')}/({tot})"


def build_rows(info):
    A = info["assump"]
    cur_from = info["cur_from"]       # set of column keys from which the company definition = current definition
    R = []
    add = R.append

    def blank():
        add(Row(None, style="blank"))

    # =====================================================================================
    add(Row("sec_seg", "SEGMENT P&L — BY SEGMENT (four reportable segments; current basis from FY2008)",
            style="section", note="SEGMENT BUILD — modelling logic (segment sales → GAAP OI → non-GAAP OI)"))
    blank()

    for s in SEGS:
        nm = SEG_NAMES[s]
        add(Row(f"blk_{s}", SEG_DESC[s], style="block", note=f"{nm.upper()} — modelling logic"))
        add(Row(f"sales_{s}", "  Net sales", style="sub", src=f"seg.sales_{s}", cagr="cagr",
                qe=lambda x, s=s: f"={x.py('sales_' + s)}*{x.at('sales_' + s, 'Q2/26')}/{x.at('sales_' + s, 'Q2/25')}",
                e=lambda x, s=s: f"={x.pp('sales_' + s)}*(1+{x.a('gr_' + s)})",
                note="Q3/26E–Q4/26E: prior-year quarter × Q2/26 y/y growth of the segment (after the Excelitas A&D anniversary). 2027E+: prior year × (1 + "
                     "scenario organic growth).",
                comment="Source: earnings releases (Form 8-K Ex. 99.1) segment tables; 10-K segment note for FY. "
                        "FY2008–09 as recast into the current four segments in the FY2010 10-K."
                        if s == "di" else ""))
        add(Row(f"gr_{s}", "  Net sales y/y %", style="growth", fmt=FMT_PCT,
                hist=yoy(f"sales_{s}"), qe=yoy(f"sales_{s}"), e26=yoy(f"sales_{s}"),
                e=lambda x, s=s: "=" + x.scn(srow(S_GR[s], x.c.year)),
                note=f"2027E–2030E: scenario lever ({s.upper()}_organicGrowth, Bull/Base/Bear table →)."))
        add(Row(f"oi_{s}", "  Segment operating income (GAAP)", src=f"seg.oi_{s}", cagr="cagr",
                fc=lambda x, s=s: f"={x.a('adj_' + s)}-{x.a('am_' + s)}-{x.a('it_' + s)}",
                note="Forecast GAAP OI = non-GAAP OI − acquired-intangible amortization − other items."))
        add(Row(f"am_{s}", "  (+) Acquired intangible asset amortization", src=f"seg.amort_{s}",
                qe=lambda x, s=s: f"={x.a('am_tot')}*{_share(x, s)}",
                e=lambda x, s=s: f"={x.a('amort_sched')}*{_share(x, s)}",
                note="Disclosed by segment from Q1/21. Forecast = amortization of existing intangibles (10-K schedule) "
                     "× 1H/26 segment share."))
        add(Row(f"it_{s}", "  (+) Other segment non-GAAP items (inventory step-up, transaction costs)",
                src=f"seg.items_{s}", fc=0))
        add(Row(f"adj_{s}", "  Non-GAAP segment operating income", style="total", cagr="cagr",
                hist=lambda x, s=s: (f'=IF(OR(ISNUMBER({x.a("adjp_" + s)}),ISNUMBER({x.a("am_" + s)})),'
                                     f'{x.a("oi_" + s)}+N({x.a("am_" + s)})+N({x.a("it_" + s)}),"")'),
                fc=lambda x, s=s: f"={x.a('sales_' + s)}*{x.a('mg_' + s)}",
                note="Company non-GAAP measure from Q1/21 (segment OI excluding acquired-intangible amortization and "
                     "acquisition items). Forecast = net sales × non-GAAP margin."))
        add(Row(f"adjp_{s}", "  Memo: non-GAAP segment operating income as published", style="memo",
                src=f"seg.adj_oi_{s}"))
        add(Row(f"chk_{s}", "  Check: build vs published (should be 0)", style="check",
                hist=lambda x, s=s: (f'=IF(ISNUMBER({x.a("adjp_" + s)}),ROUND({x.a("adj_" + s)}-{x.a("adjp_" + s)},1),'
                                     f'"n/p")')))
        add(Row(f"m_{s}", "  Segment operating margin (GAAP) %", style="pct", fmt=FMT_PCT, cagr="avg",
                hist=ratio(f"oi_{s}", f"sales_{s}"), fc=ratio(f"oi_{s}", f"sales_{s}")))
        add(Row(f"mg_{s}", "  Non-GAAP segment operating margin %", style="pct", fmt=FMT_PCT, cagr="avg",
                hist=lambda x, s=s: f'=IFERROR({x.a("adj_" + s)}/{x.a("sales_" + s)},"")',
                qe=lambda x, s=s: (f"={x.py('mg_' + s)}+{x.abs_at('mg_' + s, '1H/26')}"
                                   f"-{x.abs_at('mg_' + s, '1H/25')}+{x.a('mg_cal')}"),
                e26=ratio(f"adj_{s}", f"sales_{s}"),
                e=lambda x, s=s: "=" + x.scn(srow(S_MG[s], x.c.year)),
                note="Q3/Q4-26E: prior-year quarter margin + 1H/26 vs 1H/25 change + outlook calibration Δ. 2027E+: scenario lever "
                     f"({s.upper()}_margin)."))
        add(Row(f"goi_{s}", "  Segment operating income (GAAP) y/y %", style="growth", fmt=FMT_PCT,
                hist=yoy(f"oi_{s}"), fc=yoy(f"oi_{s}")))
        add(Row(f"inc_{s}", "  Incremental non-GAAP margin (ΔOI / ΔSales)", style="pct", fmt=FMT_PCT,
                hist=lambda x, s=s: (f'=IFERROR(({x.a("adj_" + s)}-{x.py("adj_" + s)})/({x.a("sales_" + s)}'
                                     f'-{x.py("sales_" + s)}),"")') if x.py(f"adj_{s}") else None,
                fc=lambda x, s=s: (f'=IFERROR(({x.a("adj_" + s)}-{x.py("adj_" + s)})/({x.a("sales_" + s)}'
                                   f'-{x.py("sales_" + s)}),"")')))
        for k, lab in PRODUCT_LINES.get(s, []):
            add(Row(f"pl_{k}", f"  Memo: {lab} sales", style="memo", src=f"seg.{k}",
                    comment="Product-line sales as stated in the earnings release / 10-K MD&A." if k.endswith(
                        ("marine", "aero", "eng")) else ""))
        add(Row(f"da_{s}", "  Segment D&A (annual, 10-K segment note)", src=f"seg.da_{s}", annual_only=True, agg="none"))
        add(Row(f"cx_{s}", "  Segment capital expenditures (annual)", src=f"seg.capex_{s}", annual_only=True,
                agg="none"))
        add(Row(f"cxp_{s}", "  Segment capex % of sales", style="pct", fmt=FMT_PCT, annual_only=True,
                hist=lambda x, s=s: (f'=IFERROR({x.a("cx_" + s)}/{x.a("sales_" + s)},"")'
                                     if x.c.kind in ("A", "Y") else None)))
        blank()

    # ---------------- Legacy segments ----------------
    add(Row("blk_leg", "Legacy segments (as originally reported, FY2006–07; superseded by the FY2010 10-K recast)",
            style="block", note="LEGACY SEGMENTS — memo only (not comparable with the current basis)"))
    for k, lab in [("ec", "Electronics and Communications"),
                   ("ses", "Systems Engineering Solutions / Engineered Systems"),
                   ("aec", "Aerospace Engines and Components (piston engines sold Apr-2011)"),
                   ("eps", "Energy (and Power) Systems")]:
        add(Row(f"lgs_{k}", f"  {lab} — net sales", style="memo", src=f"seg.leg_sales_{k}", agg="none"))
        add(Row(f"lgo_{k}", f"  {lab} — operating profit", style="memo", src=f"seg.leg_oi_{k}", agg="none"))
    add(Row("lg_corp", "  Corporate expense (legacy basis)", style="memo", src="seg.leg_corp_exp", agg="none"))
    blank()

    # ---------------- Corporate ----------------
    add(Row("blk_corp", "Corporate & reconciling items", style="block", note="CORPORATE — modelling logic"))
    add(Row("corp", "  Corporate expense (GAAP)", src="seg.corp_exp",
            fc=lambda x: f"={x.a('adj_corp')}+{x.a('corp_it')}",
            note="Forecast = non-GAAP corporate expense + corporate adjusting items."))
    add(Row("corp_it", "  Corporate non-GAAP items (transaction & integration costs)", src="seg.items_corp",
            qe=A["corp_items_q"], e=lambda x: A["corp_items"][x.c.year], input_fc=True,
            note="Acquisition transaction / integration costs recorded at corporate (input)."))
    add(Row("adj_corp", "  Non-GAAP corporate expense", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("corp")}),{x.a("corp")}-N({x.a("corp_it")}),"")',
            qe=lambda x: f"={x.h('adj_corp')}/2",
            e=lambda x: f"={x.a('net_sales')}*{x.a('corp_pct')}",
            note="Q3/Q4-26E at the 1H/26 run-rate; 2027E+: % of sales input."))
    add(Row("corp_pct", "  Non-GAAP corporate expense % of sales", style="pct", fmt=FMT_PCT,
            hist=ratio("adj_corp", "net_sales"), qe=ratio("adj_corp", "net_sales"), e26=ratio("adj_corp", "net_sales"),
            e=lambda x: A["corp_pct"][x.c.year], input_fc=True))
    add(Row("other_seg", "  Other reconciling items to operating income (signed)", src="seg.other_seg", fc=0,
            comment="Any line between total segment operating income and consolidated operating income other than "
                    "corporate expense (e.g. unallocated pension in some years) — see data notes."))
    seg_sales = lambda x: "+".join(x.a("sales_" + k) for k in SEGS)  # noqa: E731
    base_oi = lambda x: "+".join(  # noqa: E731
        f"{x.a('sales_' + k)}*({x.py('mg_' + k)}+{x.abs_at('mg_' + k, '1H/26')}-{x.abs_at('mg_' + k, '1H/25')})"
        for k in SEGS)
    add(Row("mg_cal", "  Outlook calibration: Δ non-GAAP margin applied to all segments (Q3/Q4-26E)", style="pct",
            fmt=FMT_PCT,
            qe=lambda x: (f"=(({x.a('ng_target')}+{x.a('nci')})/(1-{x.base(S_TAX)})+{x.a('interest_exp_net')}"
                          f"-{x.a('non_service_pension')}-{x.a('other_income')}+{x.a('adj_corp')}-{x.a('other_seg')}"
                          f"-({base_oi(x)}))/({seg_sales(x)})"),
            note="Solves the margin shift (vs prior-year quarter + 1H/26 drift) so that non-GAAP net income equals the "
                 "FY26 / Q3 non-GAAP EPS outlook (scenario: high / mid / low) × diluted shares."))
    add(Row("ng_target", "  Memo: non-GAAP net income target (FY26 outlook × diluted shares)", style="memo",
            qe=lambda x: (f"={x.scn(S_EPS_Q3)}*{x.a('sh_dil')}" if x.c.q == 3 else
                          f"={x.scn(S_EPS_FY)}*{x.at('sh_dil', '2026E')}-{x.at('b_adj', '1H/26')}"
                          f"-{x.at('ng_target', 'Q3/26E')}"),
            e26=lambda x: f"={x.h('b_adj')}+{x.q('ng_target', 3)}+{x.q('ng_target', 4)}",
            note="Q3/26E = Q3 non-GAAP EPS outlook × Q3 diluted shares; Q4/26E = FY26 outlook × FY diluted shares − 1H "
                 "actual − Q3E."))
    blank()

    # ---------------- Future M&A ----------------
    add(Row("blk_ma", "Future acquisitions (M&A lever — unallocated; deals closed from 2027E)", style="block",
            note="M&A LEVER — acquired sales = spend ÷ EV/sales; mid-year convention"))
    ann = dict(annual_only=True, agg="none")
    add(Row("ma_spend", "  Acquisition spend (USDm, scenario)", e26=0,
            e=lambda x: "=" + x.scn(srow(S_MA, x.c.year)), **ann,
            note="Scenario lever (M&A_spend, Bull/Base/Bear table →). Teledyne deployed ~$0.3–1.0bn p.a. on bolt-on "
                 "deals ex FLIR (2017 e2v $0.8bn; 2021 FLIR $8.2bn; 2024–25 Excelitas A&D $0.7bn)."))
    add(Row("ma_mult", "  Purchase multiple — EV / sales (x)", style="sched", fmt=FMT_X, e26=None,
            e=lambda x: A["ma_mult"][x.c.year], input_fc=True, **ann))
    add(Row("ma_new", "  Annualised sales acquired in the year", e26=0,
            e=lambda x: f'=IFERROR({x.a("ma_spend")}/{x.a("ma_mult")},0)', **ann))
    add(Row("ma_g", "  Growth of acquired businesses after acquisition %", style="sched", fmt=FMT_PCT,
            e=lambda x: A["ma_g"][x.c.year], input_fc=True, **ann))
    add(Row("ma_rr", "  Run-rate sales of businesses acquired (year end)", e26=0,
            e=lambda x: f"={x.pp('ma_rr')}*(1+{x.a('ma_g')})+{x.a('ma_new')}", **ann))
    add(Row("ma_rev", "  Net sales from future acquisitions", style="sub", e26=0,
            e=lambda x: f"={x.pp('ma_rr')}*(1+{x.a('ma_g')})+0.5*{x.a('ma_new')}", **ann,
            note="Mid-year convention: deals close evenly through the year (half a year of sales in year 1)."))
    add(Row("ma_mg", "  Non-GAAP operating margin of acquired businesses %", style="sched", fmt=FMT_PCT,
            e=lambda x: A["ma_mg"][x.c.year], input_fc=True, **ann))
    add(Row("ma_adjoi", "  Non-GAAP operating income from future acquisitions", e26=0,
            e=lambda x: f"={x.a('ma_rev')}*{x.a('ma_mg')}", **ann))
    add(Row("ma_ip", "  Acquired intangibles % of spend", style="sched", fmt=FMT_PCT,
            e=lambda x: A["ma_ip"][x.c.year], input_fc=True, **ann))
    add(Row("ma_life", "  Amortization life (years)", style="sched", fmt=FMT_NUM1,
            e=lambda x: A["ma_life"][x.c.year], input_fc=True, **ann))
    add(Row("ma_intang", "  Cumulative acquired intangibles (gross)", e26=0,
            e=lambda x: f"={x.pp('ma_intang')}+{x.a('ma_spend')}*{x.a('ma_ip')}", **ann))
    add(Row("ma_amort", "  Amortization of future-acquisition intangibles", e26=0,
            e=lambda x: f"=({x.pp('ma_intang')}+0.5*{x.a('ma_spend')}*{x.a('ma_ip')})/{x.a('ma_life')}", **ann))
    add(Row("ma_oi", "  Operating income (GAAP) from future acquisitions", e26=0,
            e=lambda x: f"={x.a('ma_adjoi')}-{x.a('ma_amort')}", **ann))
    add(Row("ma_contrib", "  Incremental acquisition sales (first 12 months of ownership)", e26=0,
            e=lambda x: f"=0.5*{x.a('ma_new')}+0.5*{x.pp('ma_new')}", **ann))
    blank()

    # ---------------- Group total ----------------
    add(Row("blk_grp", "Group Total — non-GAAP operating income (Teledyne's primary profit KPI)", style="block",
            note="GROUP TOTAL (CONSOLIDATED) — modelling logic"))
    seg_sum = lambda x, p: "+".join(f"N({x.a(p + s)})" for s in SEGS)  # noqa: E731
    add(Row("grp_sales", "  Net sales (segment build)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("sales_di")}),{seg_sum(x, "sales_")},"")',
            fc=lambda x: f"={seg_sum(x, 'sales_')}+N({x.a('ma_rev')})",
            note="Σ segment net sales (+ future acquisitions from 2027E)."))
    add(Row("grp_adjoi", "  Non-GAAP operating income (Σ segments − non-GAAP corporate)", style="total", cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("adj_di")}),{seg_sum(x, "adj_")}-{x.a("adj_corp")}'
                            f'+N({x.a("other_seg")}),"")'),
            fc=lambda x: f"={seg_sum(x, 'adj_')}+N({x.a('ma_adjoi')})-{x.a('adj_corp')}+{x.a('other_seg')}"))
    add(Row("grp_adjm", "  Non-GAAP operating margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("grp_adjoi", "grp_sales"), fc=ratio("grp_adjoi", "grp_sales")))
    add(Row("am_tot", "  Acquired intangible asset amortization (total)", src="is.amort_intangibles",
            qe=lambda x: f"=({x.abs_at('amort_sched', '2026E')}-{x.h('am_tot')})/2",
            e26=lambda x: f"=SUM({x.q('am_tot', 1)},{x.q('am_tot', 2)},{x.q('am_tot', 3)},{x.q('am_tot', 4)})",
            e=lambda x: f"={x.a('amort_sched')}+{x.a('ma_amort')}",
            note="Historical: earnings releases (quarterly from 2021) / 10-K intangibles note (annual). Forecast = 10-K "
                 "expected amortization of existing intangibles + future-M&A amortization.",
            comment="Total amortization of acquired intangible assets (all acquisitions)."))
    add(Row("grp_oi", "  Operating income (GAAP; Σ segment OI − corporate)", style="total", cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("oi_di")}),{seg_sum(x, "oi_")}-{x.a("corp")}'
                            f'+N({x.a("other_seg")}),"")'),
            fc=lambda x: f"={seg_sum(x, 'oi_')}+N({x.a('ma_oi')})-{x.a('corp')}+{x.a('other_seg')}"))
    add(Row("grp_om", "  Operating margin (GAAP) %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("grp_oi", "grp_sales"), fc=ratio("grp_oi", "grp_sales")))
    add(Row("grp_g", "  Net sales y/y %", style="growth", fmt=FMT_PCT, hist=yoy("grp_sales"), fc=yoy("grp_sales")))
    add(Row("grp_adjg", "  Non-GAAP operating income y/y %", style="growth", fmt=FMT_PCT, hist=yoy("grp_adjoi"),
            fc=yoy("grp_adjoi")))
    add(Row("acq_sales", "  Incremental sales from acquisitions (disclosed)", src="ops.acq_sales",
            qe=A["acq_sales_q"], e=lambda x: f"={x.a('ma_contrib')}", input_fc=True,
            note="Releases: 'net sales included $x million of incremental sales from recent acquisitions'. Q3/Q4-26E "
                 "input; 2027E+ = future-M&A contribution."))
    add(Row("backlog", "  Funded backlog (period end, as disclosed)", style="memo", src="ops.funded_backlog",
            agg="last"))
    add(Row("orders", "  Orders (as disclosed)", style="memo", src="ops.orders"))
    add(Row("grp_chk", "  Check: segment build vs consolidated net sales (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("grp_sales")}),ROUND({x.a("grp_sales")}-{x.a("net_sales")},1),"")',
            fc=lambda x: f"=ROUND({x.a('grp_sales')}-{x.a('net_sales')},1)"))
    add(Row("grp_oichk", "  Check: segment build vs consolidated operating income (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("grp_oi")}),ROUND({x.a("grp_oi")}-{x.a("op_income")},1),"")',
            fc=lambda x: f"=ROUND({x.a('grp_oi')}-{x.a('op_income')},1)"))
    add(Row("grp_adjchk", "  Check: segment build vs company non-GAAP operating income (should be 0)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("grp_adjoi")}),ISNUMBER({x.a("o_pub")})),'
                            f'ROUND({x.a("grp_adjoi")}-{x.a("o_pub")},1),"n/p")'),
            fc=lambda x: f"=ROUND({x.a('grp_adjoi')}-{x.a('o_adj')},1)"))
    blank()

    # ---------------- Cost drivers ----------------
    add(Row("blk_cd", "Cost drivers (% of sales)", style="block",
            note="% OF SALES drivers — inputs that drive forecast cost lines"))
    add(Row("cogs_pct", "  Cost of sales % of net sales", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("cost_sales", "net_sales"),
            qe=lambda x: f"={x.py('cogs_pct')}+{x.abs_at('cogs_pct', '1H/26')}-{x.abs_at('cogs_pct', '1H/25')}",
            e26=ratio("cost_sales", "net_sales"), e=lambda x: A["cogs_pct"][x.c.year], input_fc=True,
            note="Cost of sales incl. acquired-intangible amortization charged to cost of sales. SG&A is the balancing "
                 "line to the segment-build operating income."))
    add(Row("adj_da_pct", "  Depreciation (D&A ex acquired-intangible amortization) % of sales", style="pct",
            fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f'=IFERROR({x.a("adj_da")}/{x.a("net_sales")},"")',
            qe=lambda x: f"={x.abs_at('adj_da_pct', '1H/26')}",
            e26=lambda x: f'=IFERROR({x.a("adj_da")}/{x.a("net_sales")},"")',
            e=lambda x: A["adj_da_pct"][x.c.year], input_fc=True))
    add(Row("adj_da", "  Depreciation & other amortization (total D&A − acquired-intangible amortization)",
            hist=lambda x: f'=IF(AND(ISNUMBER({x.a("da")}),ISNUMBER({x.a("am_tot")})),{x.a("da")}-{x.a("am_tot")},"")',
            fc=lambda x: f"={x.a('net_sales')}*{x.a('adj_da_pct')}"))
    add(Row("sbc_pct", "  Stock-based compensation % of sales", style="pct", fmt=FMT_PCT,
            hist=ratio("sbc", "net_sales"), qe=lambda x: f"={x.abs_at('sbc_pct', '1H/26')}",
            e26=ratio("sbc", "net_sales"), e=lambda x: A["sbc_pct"][x.c.year], input_fc=True))
    add(Row("rd_pct", "  Company-funded R&D % of sales (memo)", style="pct", fmt=FMT_PCT,
            hist=ratio("rd", "net_sales")))
    blank()

    # ---------------- Customers & geography ----------------
    add(Row("blk_geo", "Sales by customer & geography (annual disclosure)", style="block",
            note="CUSTOMER / GEOGRAPHY — historical disclosure only (not forecast)"))
    add(Row("geo_usg", "  Sales to the US Government", src="ops.sales_us_gov", annual_only=True, agg="none",
            comment="Source: 10-K business section / segment note."))
    add(Row("geo_usg_pct", "  US Government % of sales", style="pct", fmt=FMT_PCT, annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("geo_usg")}/{x.a("net_sales")},"")' if x.c.kind in ("A", "Y") else None)))
    add(Row("geo_us", "  Sales — United States", src="ops.rev_us", annual_only=True, agg="none"))
    add(Row("geo_intl", "  Sales — outside the United States", annual_only=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("geo_us")}),{x.a("net_sales")}-{x.a("geo_us")},"")'
                            if x.c.kind in ("A", "Y") else None)))
    add(Row("geo_intl_pct", "  International % of sales", style="pct", fmt=FMT_PCT, annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("geo_intl")}/{x.a("net_sales")},"")' if x.c.kind in ("A", "Y") else None)))
    blank()

    # =====================================================================================
    add(Row("sec_is", "CONSOLIDATED INCOME STATEMENT (US GAAP)", style="section", note="CONSOLIDATED IS — forecast logic"))
    add(Row("net_sales", "Net sales", style="total", src="is.net_sales", cagr="cagr",
            fc=lambda x: f"={x.a('grp_sales')}", note="Forecast linked to the segment build.",
            comment="Source: 10-K (annual) and earnings releases / 10-Q (quarters), latest filing presenting each period."))
    add(Row("prod_sales", "  of which: product sales", style="memo", src="is.product_sales"))
    add(Row("svc_sales", "  of which: service sales", style="memo", src="is.service_sales"))
    add(Row("cost_sales", "Cost of sales", src="is.cost_sales", fc=lambda x: f"={x.a('net_sales')}*{x.a('cogs_pct')}"))
    add(Row("gross", "Gross profit", style="sub",
            hist=lambda x: f"={x.a('net_sales')}-{x.a('cost_sales')}", fc=lambda x: f"={x.a('net_sales')}-{x.a('cost_sales')}"))
    add(Row("sga", "Selling, general and administrative expenses (incl. R&D)", src="is.sga",
            fc=lambda x: f"={x.a('gross')}-{x.a('amort_line')}+{x.a('other_op')}-{x.a('grp_oi')}",
            note="Forecast SG&A is the balancing line so that operating income equals the segment build."))
    add(Row("amort_line", "Acquired intangible asset amortization (separate IS line from 2021)", src="is.amort_line",
            fc=lambda x: f"={x.a('am_tot')}",
            comment="From the Q2-21 release / FY2021 10-K Teledyne presents acquired-intangible amortization as a "
                    "separate line (Q1/21 and FY2019–20 reclassified out of SG&A in later filings); earlier periods "
                    "include it in cost of sales and SG&A (not re-presented). Q4/24: incl. in other operating items the "
                    "$52.5m trademark impairment."))
    add(Row("other_op", "Other operating items (gains, impairments; signed)", src="is.other_op", fc=0))
    add(Row("op_income", "Operating income", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('gross')}-{x.a('sga')}-N({x.a('amort_line')})+N({x.a('other_op')})",
            fc=lambda x: f"={x.a('gross')}-{x.a('sga')}-{x.a('amort_line')}+{x.a('other_op')}"))
    add(Row("interest_exp_net", "Interest and debt expense, net", src="is.interest_exp_net",
            qe=lambda x: f"={x.at('interest_exp_net', 'Q2/26')}",
            e=lambda x: f"={x.a('int_rate')}*{x.pp('debt')}-{x.a('cash_rate')}*{x.pp('cash')}",
            note="Q3/Q4-26E at the Q2/26 run-rate (after the $450m April-2026 maturity). 2027E+ = rate × opening debt − "
                 "yield × opening cash (no circularity)."))
    add(Row("non_service_pension", "Non-service retirement benefit income (expense)", src="is.non_service_pension",
            qe=lambda x: f"={x.at('non_service_pension', 'Q2/26')}",
            e=lambda x: A["pension"][x.c.year], input_fc=True,
            note="ASU 2017-07 (2018; 2017 recast): non-service pension cost presented below operating income."))
    add(Row("other_income", "Other income (expense), net (incl. gain / loss on debt extinguishment)", src="is.other_income",
            fc=0))
    add(Row("pretax", "Income before income taxes", style="total", cagr="cagr",
            hist=lambda x: (f"={x.a('op_income')}-{x.a('interest_exp_net')}+N({x.a('non_service_pension')})"
                            f"+N({x.a('other_income')})"),
            fc=lambda x: (f"={x.a('op_income')}-{x.a('interest_exp_net')}+{x.a('non_service_pension')}"
                          f"+{x.a('other_income')}")))
    add(Row("tax", "Provision for income taxes", src="is.tax",
            qe=lambda x: f"={x.a('pretax')}*{x.base(S_TAX)}",
            e=lambda x: f"={x.a('pretax')}*{x.a('etr')}",
            note="Q3/Q4-26E at the FY26 outlook tax rate; 2027E+ input ETR."))
    add(Row("etr", "  Effective tax rate", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("tax", "pretax"), qe=ratio("tax", "pretax"), e26=ratio("tax", "pretax"),
            e=lambda x: A["etr"][x.c.year], input_fc=True))
    add(Row("inc_cont", "Income from continuing operations", style="sub",
            hist=lambda x: f"={x.a('pretax')}-{x.a('tax')}", fc=lambda x: f"={x.a('pretax')}-{x.a('tax')}"))
    add(Row("disc_ops", "Income (loss) from discontinued operations, net of tax", src="is.disc_ops", fc=0))
    add(Row("net_income", "Net income (incl. non-controlling interests)", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('inc_cont')}+N({x.a('disc_ops')})",
            fc=lambda x: f"={x.a('inc_cont')}+{x.a('disc_ops')}"))
    add(Row("nci", "  Net income attributable to non-controlling interests", src="is.nci", fc=0))
    add(Row("ni_tdy", "Net income attributable to Teledyne", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('net_income')}-N({x.a('nci')})", fc=lambda x: f"={x.a('net_income')}-{x.a('nci')}"))
    add(Row("ni_chk", "  Check: net income attributable to Teledyne vs reported (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni_rep")}),ROUND({x.a("ni_tdy")}-{x.a("ni_rep")},1),"")'))
    add(Row("ni_rep", "  Memo: net income attributable to Teledyne as reported", style="memo", src="is.ni_teledyne"))
    add(Row("da", "  Memo: depreciation and amortization (total)", style="memo", src="is.da",
            fc=lambda x: f"={x.a('adj_da')}+{x.a('am_tot')}"))
    add(Row("sbc", "  Memo: stock-based compensation", style="memo", src="is.sbc",
            fc=lambda x: f"={x.a('net_sales')}*{x.a('sbc_pct')}"))
    add(Row("rd", "  Memo: company-funded research and development", style="memo", src="is.rd_company"))
    add(Row("eps_hdr", "(Earnings per share)", style="line"))
    add(Row("sh_basic", "  Weighted-average basic shares (m)", src="is.shares_basic", agg="avg", fmt=FMT_SHR,
            qe=lambda x: f"={x.at('sh_basic', 'Q2/26')}-{x.at('bb_shares', '2026E')}*({x.c.q}-2)/2",
            e26=lambda x: f"=AVERAGE({x.q('sh_basic', 1)},{x.q('sh_basic', 2)},{x.q('sh_basic', 3)},{x.q('sh_basic', 4)})",
            e=lambda x: f"=AVERAGE({x.a('bb_beg')},{x.a('bb_end')})",
            note="Q3/Q4-26E: Q2/26 less the 2H/26 buyback phased in. 2027E+ = average of beginning and ending shares."))
    add(Row("sh_dil", "  Weighted-average diluted shares (m)", src="is.shares_diluted", agg="avg", fmt=FMT_SHR,
            qe=lambda x: f"={x.a('sh_basic')}+({x.at('sh_dil', 'Q2/26')}-{x.at('sh_basic', 'Q2/26')})",
            e26=lambda x: f"=AVERAGE({x.q('sh_dil', 1)},{x.q('sh_dil', 2)},{x.q('sh_dil', 3)},{x.q('sh_dil', 4)})",
            e=lambda x: f"={x.a('sh_basic')}+{x.a('dil_sec')}",
            note="Diluted = basic + dilutive stock options / RSUs (schedule input)."))
    add(Row("eps_basic", "EPS – basic, attributable to Teledyne ($)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("ni_tdy")}/{x.a("sh_basic")},"")',
            fc=lambda x: f'=IFERROR({x.a("ni_tdy")}/{x.a("sh_basic")},"")'))
    add(Row("eps_dil", "EPS – diluted, attributable to Teledyne ($)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("ni_tdy")}/{x.a("sh_dil")},"")',
            fc=lambda x: f'=IFERROR({x.a("ni_tdy")}/{x.a("sh_dil")},"")',
            note="EPS computed as NI attributable to Teledyne / weighted diluted shares (may differ by ±$0.01 vs "
                 "reported)."))
    add(Row("eps_dil_rep", "  Memo: EPS – diluted as reported ($)", style="memo", fmt=FMT_EPS, src="is.eps_diluted",
            agg="none"))
    add(Row("eps_gaap_ol", "  Memo: FY26 GAAP diluted EPS outlook (scenario end-point, $)", style="memo", fmt=FMT_EPS,
            e26=lambda x: "=" + x.scn(S_GAAP_FY), note="Compare with the model 2026E GAAP EPS above (the outlook "
                                                        "embeds the company's own amortization / tax assumptions)."))
    blank()

    # =====================================================================================
    # Bridge A: GAAP OI → non-GAAP OI
    add(Row("sec_ro", "RECONCILIATION: GAAP OPERATING INCOME → NON-GAAP OPERATING INCOME (company definition)",
            style="section", note="NON-GAAP OPERATING INCOME — per Teledyne earnings-release reconciliation; company "
                                  "definition in force in each period"))
    add(Row("o_oi", "Operating income (GAAP)", style="sub", hist=lambda x: f"={x.a('op_income')}",
            fc=lambda x: f"={x.a('op_income')}"))
    first_o = None
    for cat, lab in info["cats_o"]:
        k = f"o_{cat}"
        first_o = first_o or k
        if cat == "AMORT":
            fc_kw = dict(fc=lambda x: f"={x.a('am_tot')}")
        elif cat == "ACQ":
            fc_kw = dict(fc=lambda x: f"={x.a('corp_it')}")
        elif cat == "STEPUP":
            fc_kw = dict(fc=lambda x: "=" + "+".join(x.a("it_" + s) for s in SEGS))
        else:
            fc_kw = dict(fc=0)
        add(Row(k, "  (+) " + lab, src=f"adjO.{cat}", **fc_kw))
    last_o = f"o_{info['cats_o'][-1][0]}"
    add(Row("o_items", "  Total adjusting items", style="sub",
            hist=lambda x: f"=SUM({x.a(first_o)}:{x.a(last_o)})", fc=lambda x: f"=SUM({x.a(first_o)}:{x.a(last_o)})"))
    add(Row("o_adj", "  = Non-GAAP operating income (model bridge)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("o_pub")}),{x.a("o_oi")}+{x.a("o_items")},"")',
            fc=lambda x: f"={x.a('o_oi')}+{x.a('o_items')}",
            note="Historical shown only where Teledyne published a non-GAAP operating income (see the current-"
                 "definition memo below for all periods)."))
    add(Row("o_m", "  Non-GAAP operating margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("o_adj", "net_sales"), fc=ratio("o_adj", "net_sales")))
    add(Row("o_pub", "  Company-published non-GAAP operating income", style="memo", src="adjO.adj_oi_published"))
    add(Row("o_chk", "  Check: model bridge vs company-published (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("o_pub")}),ROUND({x.a("o_adj")}-{x.a("o_pub")},1),"n/p")'))
    add(Row("o_def", "  Definition basis (company non-GAAP operating income definition in force)", style="deftext",
            texts=info["def_oi"]))
    non_am = lambda x: (f"N({x.a('o_items')})-N({x.a('o_AMORT')})"  # noqa: E731
                        + "".join(f"-N({x.a('o_' + c)})" for c in ("PENSION", "SBC", "BASIS") if f"o_{c}" in info["o_keys"]))
    add(Row("o_cur_hdr", "Memo — current definition applied to all periods (model):", style="memo"))
    add(Row("o_cur_items", "  Non-amortization items (company-published: transaction, step-up, restructuring etc.)",
            hist=lambda x: "=" + non_am(x), fc=lambda x: "=" + non_am(x),
            note="Company-published adjusting items other than amortization; pension and stock-option exclusions "
                 "(2005–06 'pro forma' EPS) are not part of the current definition and are left out."))
    add(Row("o_cur", "  Non-GAAP operating income — current definition (GAAP OI + acquired-intangible amortization + "
                     "items)", style="sub", cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("am_tot")}),{x.a("op_income")}+{x.a("am_tot")}+{x.a("o_cur_items")},'
                            f'"")'),
            fc=lambda x: f"={x.a('op_income')}+{x.a('am_tot')}+{x.a('o_cur_items')}",
            note="Consistent series: Teledyne's current definition (from 2021) applied back to every period using total "
                 "acquired-intangible amortization (releases quarterly from 2021; 10-K annually before)."))
    add(Row("o_cur_m", "  Non-GAAP operating margin — current definition %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("o_cur", "net_sales"), fc=ratio("o_cur", "net_sales")))
    blank()

    # =====================================================================================
    # Bridge B: NI → EBITDA → adjusted EBITDA → adjusted EBIT
    add(Row("sec_re", "RECONCILIATION: GAAP NET INCOME → EBITDA → ADJUSTED EBITDA → ADJUSTED EBIT (model)",
            style="section", note="EBITDA BRIDGE — model measure (Teledyne does not publish EBITDA / adjusted EBITDA; it "
                                  "uses EBITDA only within its credit-agreement leverage ratio)"))
    add(Row("e_ni", "Net income (GAAP, incl. NCI)", style="sub", hist=lambda x: f"={x.a('net_income')}",
            fc=lambda x: f"={x.a('net_income')}"))
    add(Row("e_disc", "  (−) Income from discontinued operations", hist=lambda x: f"=-N({x.a('disc_ops')})",
            fc=lambda x: f"=-{x.a('disc_ops')}"))
    add(Row("e_tax", "  (+) Provision for income taxes", hist=lambda x: f"={x.a('tax')}", fc=lambda x: f"={x.a('tax')}"))
    add(Row("e_int", "  (+) Interest and debt expense, net", hist=lambda x: f"={x.a('interest_exp_net')}",
            fc=lambda x: f"={x.a('interest_exp_net')}"))
    add(Row("e_da", "  (+) Depreciation and amortization", hist=lambda x: f"={x.a('da')}", fc=lambda x: f"={x.a('da')}"))
    add(Row("e_ebitda", "  = EBITDA", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("da")}),SUM({x.a("e_ni")}:{x.a("e_da")}),"")',
            fc=lambda x: f"=SUM({x.a('e_ni')}:{x.a('e_da')})"))
    add(Row("e_items", "  (+) Non-amortization adjusting items (company-published, pre-tax)",
            hist=lambda x: f"={x.a('o_cur_items')}", fc=lambda x: f"={x.a('o_cur_items')}"))
    add(Row("adj_ebitda", "  = Adjusted EBITDA (model)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("e_ebitda")}),{x.a("e_ebitda")}+{x.a("e_items")},"")',
            fc=lambda x: f"={x.a('e_ebitda')}+{x.a('e_items')}"))
    add(Row("adj_ebitda_m", "  Adjusted EBITDA margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebitda", "net_sales"), fc=ratio("adj_ebitda", "net_sales")))
    add(Row("e_ebit_hdr", "To adjusted EBIT:", style="memo"))
    add(Row("e_less_da", "  (−) Depreciation and amortization", hist=lambda x: f"=-N({x.a('da')})",
            fc=lambda x: f"=-{x.a('da')}"))
    add(Row("e_add_am", "  (+) Acquired intangible asset amortization", hist=lambda x: f"=N({x.a('am_tot')})",
            fc=lambda x: f"={x.a('am_tot')}"))
    add(Row("adj_ebit", "  = Adjusted EBIT (model; current-definition non-GAAP OI + non-operating income)",
            style="total", cagr="cagr",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("adj_ebitda")}),ISNUMBER({x.a("am_tot")})),'
                            f'{x.a("adj_ebitda")}+{x.a("e_less_da")}+{x.a("e_add_am")},"")'),
            fc=lambda x: f"={x.a('adj_ebitda')}+{x.a('e_less_da')}+{x.a('e_add_am')}"))
    add(Row("adj_ebit_m", "  Adjusted EBIT margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebit", "net_sales"), fc=ratio("adj_ebit", "net_sales")))
    add(Row("e_chk", "  Check: adj. EBIT − (current-def. non-GAAP OI + pension + other income) (should be 0)",
            style="check",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("adj_ebit")}),ROUND({x.a("adj_ebit")}-{x.a("o_cur")}'
                            f'-N({x.a("non_service_pension")})-N({x.a("other_income")}),1),"")'),
            fc=lambda x: (f"=ROUND({x.a('adj_ebit')}-{x.a('o_cur')}-{x.a('non_service_pension')}"
                          f"-{x.a('other_income')},1)")))
    blank()

    # =====================================================================================
    # Bridge C: NI attributable → non-GAAP NI → non-GAAP EPS
    add(Row("sec_rb", "RECONCILIATION: GAAP NET INCOME ATTRIBUTABLE TO TELEDYNE → NON-GAAP NET INCOME / NON-GAAP EPS",
            style="section", note="NON-GAAP NET INCOME & EPS — company definition in force in each period (definition "
                                  "changes flagged in the definition row and cell comments)"))
    add(Row("b_base", "Net income attributable to Teledyne (GAAP)", style="sub", hist=lambda x: f"={x.a('ni_tdy')}",
            fc=lambda x: f"={x.a('ni_tdy')}"))
    first_n = None
    for cat, lab in info["cats_n"]:
        k = f"n_{cat}"
        first_n = first_n or k
        if cat == "AMORT":
            fc_kw = dict(fc=lambda x: f"={x.a('am_tot')}")
        elif cat == "ACQ":
            fc_kw = dict(fc=lambda x: f"={x.a('corp_it')}")
        elif cat == "STEPUP":
            fc_kw = dict(fc=lambda x: "=" + "+".join(x.a("it_" + s) for s in SEGS))
        else:
            fc_kw = dict(fc=0)
        add(Row(k, "  (+) " + lab, src=f"adjN.{cat}", **fc_kw))
    last_n = f"n_{info['cats_n'][-1][0]}"
    add(Row("n_TAX", "  (−) Income tax effect of the above", src="adjN.TAX",
            fc=lambda x: f"=-SUM({x.a(first_n)}:{x.a(last_n)})*{x.a('b_taxrate')}"))
    add(Row("n_TAXD", "  (+/−) Discrete tax items (FLIR acquisition-related tax matters, tax-law changes)",
            src="adjN.TAXD", fc=0))
    add(Row("n_NCI", "  (−) Portion attributable to non-controlling interests", src="adjN.NCI", fc=0))
    add(Row("b_adj", "  = Non-GAAP net income attributable to Teledyne (model bridge)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b_pub_ni")}),SUM({x.a("b_base")}:{x.a("n_NCI")}),"")',
            fc=lambda x: f"=SUM({x.a('b_base')}:{x.a('n_NCI')})",
            note="Historical shown only where Teledyne published non-GAAP net income (see current-definition memo)."))
    add(Row("b_taxrate", "  Tax rate applied to adjustments (forecast input; historical = implied)", style="pct",
            fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR(-{x.a("n_TAX")}/SUM({x.a(first_n)}:{x.a(last_n)}),"")',
            qe=lambda x: "=" + x.base(S_TAX), e26=lambda x: "=" + x.base(S_TAX),
            e=lambda x: A["adj_taxrate"][x.c.year], input_fc=True,
            note="Q3/Q4-26E = FY26 outlook tax rate (same rate as GAAP, so the outlook EPS is hit exactly)."))
    add(Row("b_sh", "  Weighted-average diluted shares (m)", fmt=FMT_SHR, agg="avg", hist=lambda x: f"={x.a('sh_dil')}",
            fc=lambda x: f"={x.a('sh_dil')}"))
    add(Row("b_eps", "Non-GAAP EPS – diluted ($) (model bridge)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("b_adj")}/{x.a("b_sh")},"")',
            fc=lambda x: f'=IFERROR({x.a("b_adj")}/{x.a("b_sh")},"")'))
    add(Row("b_pub_ni", "  Company-published non-GAAP net income", style="memo", src="adjN.adj_ni_published"))
    add(Row("b_pub_eps", "  Company-published non-GAAP diluted EPS ($)", style="memo", fmt=FMT_EPS,
            src="adjN.adj_eps_published", agg="none"))
    add(Row("b_chk", "  Check: model bridge vs company-published non-GAAP net income (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b_pub_ni")}),ROUND({x.a("b_adj")}-{x.a("b_pub_ni")},1),"n/p")'))
    add(Row("b_def", "  Definition basis (company non-GAAP EPS definition in force)", style="deftext",
            texts=info["def_ni"]))
    add(Row("c_hdr", "Memo — current definition applied to all periods (model):", style="memo"))

    def c_ni(x):
        if x.c.key in cur_from:
            return f'=IF(ISNUMBER({x.a("b_adj")}),{x.a("b_adj")},"")' if not x.c.is_forecast else f"={x.a('b_adj')}"
        t = f"MAX(0.15,MIN(0.4,N({x.a('etr')})))"
        return (f'=IF(ISNUMBER({x.a("am_tot")}),{x.a("ni_tdy")}-N({x.a("disc_ops")})+({x.a("am_tot")}'
                f'+{x.a("o_cur_items")})*(1-{t}),"")')
    add(Row("c_ni", "  Non-GAAP net income — current definition", style="sub", cagr="cagr", hist=c_ni, fc=c_ni,
            note="Periods before the current definition: NI from continuing operations + (acquired-intangible "
                 "amortization + company-published non-amortization items) × (1 − period ETR, bounded 15–40%). From "
                 "the current definition onward = company bridge."))
    add(Row("c_eps", "  Non-GAAP EPS — current definition, diluted ($)", style="sub", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("c_ni")}/{x.a("sh_dil")},"")',
            fc=lambda x: f'=IFERROR({x.a("c_ni")}/{x.a("sh_dil")},"")'))
    blank()

    # =====================================================================================
    add(Row("sec_gm", "GROWTH & MARGINS", style="section", note="GROWTH & MARGINS (consolidated) — forecast outputs"))
    add(Row("g_rev", "  Net sales y/y %", style="growth", fmt=FMT_PCT, hist=yoy("net_sales"), fc=yoy("net_sales")))
    add(Row("g_org", "  Net sales — organic y/y %", style="growth", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("g_rev")}-{x.a("g_acq")},"")' if x.py("net_sales") else None,
            fc=lambda x: f'=IFERROR({x.a("g_rev")}-{x.a("g_acq")},"")',
            note="Organic = total growth less disclosed incremental acquisition sales (first 12 months), incl. FX."))
    add(Row("g_acq", "  Net sales — acquisition y/y %", style="growth", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR(N({x.a("acq_sales")})/{x.py("net_sales")},"")' if x.py("net_sales") else None),
            fc=lambda x: f'=IFERROR({x.a("acq_sales")}/{x.py("net_sales")},0)'))
    add(Row("g_adjoi", "  Non-GAAP operating income (current definition) y/y %", style="growth", fmt=FMT_PCT,
            hist=yoy("o_cur"), fc=yoy("o_cur")))
    add(Row("g_oi", "  Operating income (GAAP) y/y %", style="growth", fmt=FMT_PCT, hist=yoy("op_income"),
            fc=yoy("op_income")))
    add(Row("g_ni", "  Net income attributable to Teledyne y/y %", style="growth", fmt=FMT_PCT, hist=yoy("ni_tdy"),
            fc=yoy("ni_tdy")))
    add(Row("g_eps", "  Non-GAAP EPS (current definition) y/y %", style="growth", fmt=FMT_PCT, hist=yoy("c_eps"),
            fc=yoy("c_eps")))
    add(Row("m_gross", "  Gross margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("gross", "net_sales"),
            fc=ratio("gross", "net_sales")))
    add(Row("m_adjoi", "  Non-GAAP operating margin (current definition) %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("o_cur", "net_sales"), fc=ratio("o_cur", "net_sales")))
    add(Row("m_oi", "  Operating margin (GAAP) %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("op_income", "net_sales"), fc=ratio("op_income", "net_sales")))
    add(Row("m_ebitda", "  Adjusted EBITDA margin (model) %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebitda", "net_sales"), fc=ratio("adj_ebitda", "net_sales")))
    add(Row("m_ni", "  Net margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("ni_tdy", "net_sales"), fc=ratio("ni_tdy", "net_sales")))
    add(Row("m_inc", "  Incremental non-GAAP operating margin (ΔOI / ΔSales)", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: (f'=IFERROR(({x.a("o_cur")}-{x.py("o_cur")})/({x.a("net_sales")}-{x.py("net_sales")}),"")'
                            if x.py("o_cur") else None),
            fc=lambda x: f'=IFERROR(({x.a("o_cur")}-{x.py("o_cur")})/({x.a("net_sales")}-{x.py("net_sales")}),"")'))
    add(Row("m_sga", "  SG&A % of sales", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("sga", "net_sales"), fc=ratio("sga", "net_sales")))
    blank()

    cf_rows(R, A)
    bs_rows(R, A)
    return R


def _hist_ann(f):
    return lambda x: f(x) if (x.c.kind in ("A", "Y") or x.c.key == "1H/26") else None


def cf_rows(R, A):
    add = R.append

    def cf(key, label, src, fc=None, e26=None, e=None, style="line", note="", **kw):
        add(Row(key, label, src=src, style=style, annual_only=True, agg="none", e26=e26 if e26 is not None else fc,
                e=e if e is not None else fc, note=note, **kw))

    add(Row("sec_cf", "CONSOLIDATED CASH FLOW STATEMENT", style="section",
            note="CONSOLIDATED CASH FLOW STATEMENT — forecast logic (annual; 1H/26 = reported six months)"))
    add(Row(None, style="blank"))
    cf("cf_ni", "Net income (incl. NCI)", "cf.net_income", fc=lambda x: f"={x.a('net_income')}")
    add(Row("cf_adj_hdr", "Adjustments:", style="line"))
    cf("cf_da", "  Depreciation and amortization", "cf.da", fc=lambda x: f"={x.a('da')}")
    cf("cf_sbc", "  Stock-based compensation", "cf.sbc", fc=lambda x: f"={x.a('sbc')}")
    cf("cf_dtax", "  Deferred income taxes", "cf.deferred_tax", fc=lambda x: A["dtax"][x.c.year], input_fc=True,
       note="Deferred tax benefit from book amortization of acquired intangibles in excess of tax — input.")
    cf("cf_pens", "  Pension / retirement-benefit (income) expense and contributions", "cf.pension_plus",
       fc=lambda x: f"=-{x.a('non_service_pension')}",
       note="Forecast reverses the non-cash non-service pension income (no contributions assumed; plans over-funded).")
    cf("cf_oth", "  Other non-cash items, net (incl. gains, discontinued ops)", "cf.other_nc_plus", fc=0)
    cf("cf_wc", "  Changes in operating assets and liabilities", "cf.chg_wc",
       fc=lambda x: (f"=-({x.a('ar')}-{x.pp('ar')})-({x.a('unb')}-{x.pp('unb')})-({x.a('inv')}-{x.pp('inv')})"
                     f"-({x.a('oca')}-{x.pp('oca')})+({x.a('ap')}-{x.pp('ap')})+({x.a('acc')}-{x.pp('acc')})"
                     f"+({x.a('cl')}-{x.pp('cl')})+({x.a('ocl')}-{x.pp('ocl')})+({x.a('pens_l')}-{x.pp('pens_l')})"
                     f"+({x.a('oncl')}-{x.pp('oncl')})"),
       note="Linked to BS: −Δ(receivables, unbilled, inventories, other current assets) + Δ(payables, accrued, "
            "contract liabilities, other current, pension and other non-current liabilities).")
    cf("cfo", "Net cash provided by operating activities", "cf.cfo", style="sub", cagr="cagr",
       fc=lambda x: f"=SUM({x.a('cf_ni')}:{x.a('cf_wc')})")
    cf("cf_capex", "Purchases of property, plant and equipment", "cf.capex",
       e26=lambda x: f"=-{x.base(S_CAPEX)}", e=lambda x: f"=-{x.a('net_sales')}*{x.a('capex_pct')}",
       note="2026E: capex estimate (scenario table point estimate). 2027E+: sales × capex % input.")
    cf("cf_acq", "Purchase of businesses, net of cash acquired", "cf.acquisitions",
       e26=lambda x: f"={x.at('cf_acq', '1H/26')}", e=lambda x: f"=-{x.a('ma_spend')}",
       note="2026E = 1H/26 actual (no further 2026 M&A assumed). 2027E+ = M&A lever.")
    cf("cf_procd", "Proceeds from sale of businesses / assets", "cf.proceeds_disp",
       e26=lambda x: f"={x.at('cf_procd', '1H/26')}", e=0)
    cf("cf_oinv", "Other investing activities, net", "cf.other_inv_plus",
       e26=lambda x: f"={x.at('cf_oinv', '1H/26')}", e=0)
    cf("cfi", "Net cash used in investing activities", "cf.cfi", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_capex')}:{x.a('cf_oinv')})")
    add(Row(None, style="blank"))
    cf("cf_dissue", "Proceeds from debt / credit-facility borrowings (incl. net short-term)", "cf.debt_net",
       fc=lambda x: f"=MAX(0,{x.a('debt')}-{x.pp('debt')})")
    cf("cf_drepay", "Repayment of debt", "cf.debt_repaid", fc=lambda x: f"=MIN(0,{x.a('debt')}-{x.pp('debt')})",
       note="Net issuance / (repayment) = change in total debt per the debt schedule (maturities + revolver).")
    cf("cf_bb", "Purchases of treasury stock (share repurchases)", "cf.buybacks",
       e26=lambda x: f"={x.at('cf_bb', '1H/26')}-{x.scn(S_BUYB + 1)}",
       e=lambda x: "=-" + x.scn(S_BUYB + 1 + (x.c.year - 2026)),
       note="2026E = 1H/26 actual + 2H scenario amount; 2027E+ scenario lever (Buybacks table →).")
    cf("cf_opt", "Proceeds from exercise of stock options", "cf.options_proceeds",
       fc=lambda x: A["options_proceeds"][x.c.year], input_fc=True)
    cf("cf_ofin", "Other financing activities, net (debt costs, excess tax benefit, other)", "cf.other_fin_plus", fc=0)
    cf("cff", "Net cash provided by (used in) financing activities", "cf.cff", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_dissue')}:{x.a('cf_ofin')})")
    cf("cf_fx", "Effect of exchange-rate changes on cash", "cf.fx_effect", fc=0)
    cf("cf_chg", "Change in cash and cash equivalents", "cf.chg_cash", style="sub",
       fc=lambda x: f"={x.a('cfo')}+{x.a('cfi')}+{x.a('cff')}+{x.a('cf_fx')}")
    cf("cf_beg", "Cash and cash equivalents — beginning", "cf.cash_begin", fc=lambda x: f"={x.pp('cf_end')}")
    cf("cf_end", "Cash and cash equivalents — end", "cf.cash_end", style="sub",
       fc=lambda x: f"={x.a('cf_beg')}+{x.a('cf_chg')}")
    add(Row("cf_chk", "  Check: CFO + CFI + CFF + FX = change in cash (should be 0)", style="check", annual_only=True,
            hist=_hist_ann(lambda x: (f'=IF(ISNUMBER({x.a("cfo")}),ROUND({x.a("cfo")}+{x.a("cfi")}+{x.a("cff")}'
                                      f'+N({x.a("cf_fx")})+N({x.a("cf_disc")})-{x.a("cf_chg")},1),"")'))))
    cf("cf_disc", "  Memo: net cash from discontinued operations (where presented separately)", "cf.disc_ops_cash",
       style="memo")
    add(Row("cf_memo", "(Memo)", style="line"))
    add(Row("fcf", "Free cash flow (CFO − capital expenditures; company definition)", style="total",
            annual_only=True, cagr="cagr",
            hist=_hist_ann(lambda x: f'=IF(ISNUMBER({x.a("cfo")}),{x.a("cfo")}+N({x.a("cf_capex")}),"")'),
            fc=lambda x: f"={x.a('cfo')}+{x.a('cf_capex')}",
            note="Teledyne defines free cash flow as cash from operating activities less capital expenditures for PP&E."))
    add(Row("fcf_pub", "  Memo: free cash flow as published", style="memo", src="ops.fcf_published", annual_only=True,
            agg="none"))
    add(Row("fcf_g", "  FCF y/y %", style="growth", fmt=FMT_PCT, annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("fcf")}/{x.py("fcf")}-1,"")' if x.c.kind in ("A", "Y") and x.py("fcf") else None),
            fc=yoy("fcf")))
    for k, lab, f in [("fcf_m", "  FCF % of sales", lambda x: f'=IFERROR({x.a("fcf")}/{x.a("net_sales")},"")'),
                      ("fcf_conv", "  FCF / non-GAAP net income (current definition) conversion %",
                       lambda x: f'=IFERROR({x.a("fcf")}/{x.a("c_ni")},"")')]:
        add(Row(k, lab, style="pct", fmt=FMT_PCT, annual_only=True, cagr="avg",
                hist=lambda x, f=f: f(x) if x.c.kind in ("A", "Y") else None, fc=f))
    add(Row("fcf_ps", "  FCF per diluted share ($)", style="pct", fmt=FMT_EPS, annual_only=True, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("fcf")}/{x.a("sh_dil")},"")' if x.c.kind in ("A", "Y") else None,
            fc=lambda x: f'=IFERROR({x.a("fcf")}/{x.a("sh_dil")},"")'))
    add(Row("cx_hdr", "Capex ratios", style="line"))
    add(Row("capex_pct", "  Capex % of sales", style="pct", fmt=FMT_PCT, annual_only=True, cagr="avg", input_fc=True,
            hist=_hist_ann(lambda x: f'=IFERROR(-N({x.a("cf_capex")})/{x.a("net_sales")},"")'),
            e26=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("net_sales")},"")',
            e=lambda x: A["capex_pct"][x.c.year]))
    add(Row("capex_da", "  Capex / depreciation (ex acquired-intangible amortization) (x)", style="pct", fmt=FMT_X,
            annual_only=True,
            hist=_hist_ann(lambda x: f'=IFERROR(-N({x.a("cf_capex")})/{x.a("adj_da")},"")'),
            fc=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("adj_da")},"")'))
    add(Row(None, style="blank"))

    add(Row("sec_bb", "SHARE BUYBACK SCHEDULE", style="section"))
    add(Row("bb_px", "  Avg buyback price ($)", fmt=FMT_EPS, annual_only=True,
            e26=lambda x: f"={x.a('px')}", e=lambda x: f"={x.pp('bb_px')}*(1+{x.a('px_g')})",
            note="2026E = current share price ($615, valuation input); appreciates with the share-price input."))
    add(Row("bb_cash", "  Buyback cash deployed (USDm)", annual_only=True,
            e26=lambda x: f"=-({x.a('cf_bb')}-{x.at('cf_bb', '1H/26')})", e=lambda x: f"=-{x.a('cf_bb')}",
            note="2026E row = 2H/26 buyback only (1H/26 repurchases already in Q1/Q2 share counts)."))
    add(Row("bb_shares", "  Implied shares repurchased (m)", fmt=FMT_SHR, annual_only=True,
            fc=lambda x: f'=IFERROR({x.a("bb_cash")}/{x.a("bb_px")},0)'))
    add(Row("bb_issued", "  Shares issued under equity plans (m)", fmt=FMT_SHR, annual_only=True,
            fc=lambda x: A["bb_issued"][x.c.year], input_fc=True))
    add(Row("bb_beg", "  Beginning shares outstanding (m)", fmt=FMT_SHR, annual_only=True,
            e26=lambda x: f"={x.at('sh_out', '1H/26')}", e=lambda x: f"={x.pp('bb_end')}"))
    add(Row("bb_end", "  Ending shares outstanding (m)", fmt=FMT_SHR, annual_only=True,
            fc=lambda x: f"={x.a('bb_beg')}-{x.a('bb_shares')}+{x.a('bb_issued')}"))
    add(Row("bb_pct", "  % of shares repurchased", style="pct", fmt=FMT_PCT, annual_only=True,
            fc=lambda x: f'=IFERROR({x.a("bb_shares")}/{x.a("bb_beg")},"")'))
    add(Row("bb_cum", "  Memo: cumulative shares repurchased since 2H/26 (m)", style="memo", fmt=FMT_SHR,
            annual_only=True, e26=lambda x: f"={x.a('bb_shares')}", e=lambda x: f"={x.pp('bb_cum')}+{x.a('bb_shares')}"))
    add(Row(None, style="blank"))


def bs_rows(R, A):
    add = R.append

    def bs(key, label, src, fc=None, e26=None, e=None, style="line", note="", **kw):
        add(Row(key, label, src=src, style=style, annual_only=True, agg="none",
                e26=e26 if e26 is not None else fc, e=e if e is not None else fc, note=note, **kw))

    flat = lambda k: (lambda x: f"={x.pp(k)}")  # noqa: E731
    ha = _hist_ann
    add(Row("sec_bs", "CONSOLIDATED BALANCE SHEET", style="section",
            note="BS FORECAST — first-principles roll-forward (2026E from FY2025 year-end; 1H/26 shown as reported)"))
    add(Row(None, style="blank"))
    add(Row("bs_a", "ASSETS", style="line"))
    add(Row("bs_ca", "Current assets:", style="line"))
    bs("cash", "  Cash and cash equivalents", "bs.cash", fc=lambda x: f"={x.a('cf_end')}")
    bs("ar", "  Accounts receivable, net", "bs.receivables", fc=lambda x: f"={x.a('net_sales')}*{x.a('d_ar')}/365",
       note="Receivables = net sales × DSO / 365.")
    bs("unb", "  Unbilled receivables / contract assets", "bs.unbilled",
       fc=lambda x: f"={x.a('net_sales')}*{x.a('unb_pct')}")
    bs("inv", "  Inventories, net", "bs.inventories", fc=lambda x: f"={x.a('cost_sales')}*{x.a('d_inv')}/365")
    bs("oca", "  Prepaid expenses and other current assets (incl. held for sale)", "bs.oca_plus", fc=flat("oca"))
    bs("tca", "Total current assets", "bs.total_ca", style="sub",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("cash")}),SUM({x.a("cash")}:{x.a("oca")}),"")'),
       fc=lambda x: f"=SUM({x.a('cash')}:{x.a('oca')})")
    bs("ppe", "  Property, plant and equipment, net", "bs.ppe",
       fc=lambda x: f"={x.pp('ppe')}-{x.a('cf_capex')}-{x.a('adj_da')}-{x.a('cf_procd')}-{x.a('cf_oinv')}",
       note="PP&E roll-forward: prior + capex − depreciation (D&A ex acquired-intangible amortization) − disposals.")
    bs("rou", "  Operating lease right-of-use assets (2019+)", "bs.rou", fc=flat("rou"))
    bs("gw", "  Goodwill", "bs.goodwill",
       e26=lambda x: f"={x.pp('gw')}-{x.a('cf_acq')}*(1-{x.a('acq_ip26')})",
       e=lambda x: f"={x.pp('gw')}+{x.a('ma_spend')}*(1-{x.a('ma_ip')})",
       note="Goodwill + acquisition consideration not allocated to intangibles.")
    bs("intang", "  Acquired intangible assets, net", "bs.intangibles",
       e26=lambda x: f"={x.pp('intang')}-{x.a('cf_acq')}*{x.a('acq_ip26')}-{x.a('am_tot')}",
       e=lambda x: f"={x.pp('intang')}+{x.a('ma_spend')}*{x.a('ma_ip')}-{x.a('am_tot')}",
       note="Intangibles roll-forward: prior + acquired intangibles − amortization.")
    bs("onca", "  Other assets (incl. prepaid pension, deferred taxes)", "bs.onca_plus",
       fc=lambda x: f"={x.pp('onca')}-{x.a('cf_pens')}",
       note="Prepaid pension grows with the non-cash pension income reversed in the CF statement.")
    bs("ta", "TOTAL ASSETS", "bs.total_assets", style="total",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("cash")}),{x.a("tca")}+SUM({x.a("ppe")}:{x.a("onca")}),"")'),
       fc=lambda x: f"={x.a('tca')}+SUM({x.a('ppe')}:{x.a('onca')})")
    add(Row(None, style="blank"))
    add(Row("bs_l", "LIABILITIES AND STOCKHOLDERS' EQUITY", style="line"))
    add(Row("bs_cl", "Current liabilities:", style="line"))
    bs("ap", "  Accounts payable", "bs.ap", fc=lambda x: f"={x.a('cost_sales')}*{x.a('d_ap')}/365")
    bs("acc", "  Accrued liabilities", "bs.accrued_liab", fc=lambda x: f"={x.a('net_sales')}*{x.a('acc_pct')}")
    bs("cl", "  Contract liabilities / customer deposits (where separate)", "bs.contract_liab",
       fc=lambda x: f"={x.a('net_sales')}*{x.a('cl_pct')}")
    bs("cltd", "  Current portion of long-term debt and other debt", "bs.current_ltd",
       fc=lambda x: f"=MIN({x.pp('cltd')},{x.a('debt')})")
    bs("ocl", "  Other current liabilities (incl. held for sale)", "bs.ocl_plus", fc=flat("ocl"))
    bs("tcl", "Total current liabilities", "bs.total_cl", style="sub",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("ap")}),SUM({x.a("ap")}:{x.a("ocl")}),"")'),
       fc=lambda x: f"=SUM({x.a('ap')}:{x.a('ocl')})")
    bs("ltd", "  Long-term debt, net of current portion", "bs.ltd", fc=lambda x: f"={x.a('debt')}-{x.a('cltd')}")
    bs("ltll", "  Long-term operating lease liabilities", "bs.lt_lease_liab", fc=flat("ltll"))
    bs("pens_l", "  Accrued pension and postretirement benefits", "bs.pension_liab", fc=flat("pens_l"))
    bs("dtl", "  Deferred income taxes", "bs.dtl", fc=lambda x: f"={x.pp('dtl')}+{x.a('cf_dtax')}")
    bs("oncl", "  Other long-term liabilities", "bs.oncl_plus", fc=flat("oncl"))
    bs("tl", "Total liabilities", "bs.total_liab", style="total",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("ap")}),{x.a("tcl")}+SUM({x.a("ltd")}:{x.a("oncl")}),"")'),
       fc=lambda x: f"={x.a('tcl')}+SUM({x.a('ltd')}:{x.a('oncl')})")
    bs("rnci", "  Redeemable non-controlling interest (temporary equity)", "bs.redeemable_nci", fc=flat("rnci"))
    add(Row("bs_eq", "Stockholders' equity:", style="line"))
    bs("sc", "  Common stock & additional paid-in capital", "bs.sc_apic",
       fc=lambda x: f"={x.pp('sc')}+{x.a('cf_sbc')}+{x.a('cf_opt')}",
       note="Common stock + APIC + SBC + option proceeds.")
    bs("re", "  Retained earnings", "bs.retained_earnings", fc=lambda x: f"={x.pp('re')}+{x.a('ni_tdy')}",
       note="Retained earnings + NI attributable to Teledyne (Teledyne pays no dividend).")
    bs("ts", "  Treasury stock", "bs.treasury_stock", fc=lambda x: f"={x.pp('ts')}+{x.a('cf_bb')}",
       note="Repurchased shares held in treasury (at cost).")
    bs("aoci", "  Accumulated other comprehensive income (loss)", "bs.aoci", fc=flat("aoci"))
    bs("eqp", "Total Teledyne stockholders' equity", "bs.equity_teledyne", style="sub",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("sc")}),SUM({x.a("sc")}:{x.a("aoci")}),"")'),
       fc=lambda x: f"=SUM({x.a('sc')}:{x.a('aoci')})")
    bs("nci_bs", "  Non-controlling interests", "bs.nci", fc=lambda x: f"={x.pp('nci_bs')}+{x.a('nci')}")
    bs("teq", "Total stockholders' equity", "bs.total_equity", style="total",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("eqp")}),{x.a("eqp")}+N({x.a("nci_bs")}),"")'),
       fc=lambda x: f"={x.a('eqp')}+{x.a('nci_bs')}")
    bs("tle", "TOTAL LIABILITIES AND STOCKHOLDERS' EQUITY", "bs.total_le", style="total",
       hist=ha(lambda x: f'=IF(ISNUMBER({x.a("tl")}),{x.a("tl")}+N({x.a("rnci")})+{x.a("teq")},"")'),
       fc=lambda x: f"={x.a('tl')}+{x.a('rnci')}+{x.a('teq')}")
    add(Row(None, style="blank"))
    add(Row("bs_chk", "BS tie-out check (TA − TL&E)", style="check", annual_only=True,
            hist=ha(lambda x: f'=IF(ISNUMBER({x.a("ta")}),ROUND({x.a("ta")}-{x.a("tle")},1),"")'),
            fc=lambda x: f"=ROUND({x.a('ta')}-{x.a('tle')},1)"))
    add(Row("bs_rep_chk", "  Check: model total assets vs reported (should be 0)", style="check", annual_only=True,
            hist=ha(lambda x: f'=IF(ISNUMBER({x.a("ta_rep")}),ROUND({x.a("ta")}-{x.a("ta_rep")},1),"")')))
    add(Row("ta_rep", "  Memo: total assets as reported", style="memo", src="bs.total_assets_rep", annual_only=True,
            agg="none"))
    add(Row("cash_chk", "  Check: BS cash vs cash-flow ending cash (should be 0)", style="check", annual_only=True,
            hist=ha(lambda x: f'=IF(AND(ISNUMBER({x.a("cash")}),ISNUMBER({x.a("cf_end")})),ROUND({x.a("cash")}'
                              f'-{x.a("cf_end")},1),"")')))
    add(Row("sh_out", "  Memo: common shares outstanding at period end (m)", style="memo", fmt=FMT_SHR,
            src="bs.shares_outstanding_end", annual_only=True, agg="none", fc=lambda x: f"={x.a('bb_end')}"))

    # ---------------- Working capital ----------------
    add(Row("sec_wc", "WORKING CAPITAL & CASH CONVERSION", style="section",
            note="WORKING CAPITAL — forecast drivers (blue = input)"))

    def wc(key, label, hist, val, note="", fmt=FMT_DAYS):
        add(Row(key, label, style="pct", fmt=fmt, annual_only=True, input_fc=True,
                hist=lambda x: hist(x) if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None,
                fc=(lambda x, v=val: v[x.c.year]) if isinstance(val, dict) else val, note=note))
    half = lambda x: f'IF(LEFT("{x.c.key}",2)="1H",0.5,1)'  # noqa: E731
    wc("d_ar", "  DSO — receivables / sales × 365",
       lambda x: f'=IFERROR({x.a("ar")}/{x.a("net_sales")}*365*{half(x)},"n/a")', A["d_ar"])
    wc("unb_pct", "  Unbilled receivables % of sales",
       lambda x: f'=IFERROR({x.a("unb")}/{x.a("net_sales")}*{half(x)},"n/a")', A["unb_pct"], fmt=FMT_PCT)
    wc("d_inv", "  Inventory days — inventories / cost of sales × 365",
       lambda x: f'=IFERROR({x.a("inv")}/{x.a("cost_sales")}*365*{half(x)},"n/a")', A["d_inv"])
    wc("d_ap", "  Payable days — payables / cost of sales × 365",
       lambda x: f'=IFERROR({x.a("ap")}/{x.a("cost_sales")}*365*{half(x)},"n/a")', A["d_ap"])
    wc("acc_pct", "  Accrued liabilities % of sales",
       lambda x: f'=IFERROR({x.a("acc")}/{x.a("net_sales")}*{half(x)},"n/a")', A["acc_pct"], fmt=FMT_PCT)
    wc("cl_pct", "  Contract liabilities % of sales",
       lambda x: f'=IFERROR(N({x.a("cl")})/{x.a("net_sales")}*{half(x)},"n/a")', A["cl_pct"], fmt=FMT_PCT)
    nwc = lambda x: (f"{x.a('ar')}+N({x.a('unb')})+{x.a('inv')}-{x.a('ap')}-{x.a('acc')}-N({x.a('cl')})")  # noqa: E731
    add(Row("nwc", "  Operating NWC (receivables + unbilled + inventories − payables − accrued − contract liabilities)",
            annual_only=True,
            hist=ha(lambda x: f'=IF(ISNUMBER({x.a("ar")}),{nwc(x)},"n/a")'), fc=lambda x: "=" + nwc(x)))
    add(Row("nwc_pct", "  NWC % of sales", style="pct", fmt=FMT_PCT, annual_only=True, cagr="avg",
            hist=lambda x: f'=IFERROR({x.a("nwc")}/{x.a("net_sales")},"n/a")' if x.c.kind in ("A", "Y") else None,
            fc=lambda x: f'=IFERROR({x.a("nwc")}/{x.a("net_sales")},"n/a")'))
    add(Row("nwc_d", "  ΔNWC (y/y)", annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("nwc")}-{x.py("nwc")},"n/a")' if x.c.kind in ("A", "Y") and x.py("nwc") else None),
            fc=lambda x: f'=IFERROR({x.a("nwc")}-{x.pp("nwc")},"n/a")'))
    add(Row(None, style="blank"))

    # ---------------- Schedules ----------------
    add(Row("sec_sch", "BALANCE SHEET FORECAST SCHEDULES", style="section",
            note="BS FORECAST SCHEDULES — explicit driver assumptions"))
    add(Row("blk_sch1", "Asset roll-forwards & non-cash items", style="block"))

    def sched(key, label, val, fmt=FMT_NUM, note="", e26=None, hist=None):
        add(Row(key, label, style="sched", fmt=fmt, annual_only=True, input_fc=True,
                e26=e26 if e26 is not None else ((lambda x, v=val: v[x.c.year]) if isinstance(val, dict) else val),
                e=(lambda x, v=val: v[x.c.year]) if isinstance(val, dict) else val, note=note, hist=hist))
    sched("amort_sched", "  Amortization of existing acquired intangibles (USDm)", A["amort_sched"],
          note=A["amort_note"],
          hist=lambda x: f"=N({x.a('am_tot')})" if (x.c.kind in ("A", "Y") or x.c.key == "1H/26") else None)
    sched("acq_ip26", "  Acquired intangibles % of 2026 acquisition consideration", A["acq_ip26"], fmt=FMT_PCT,
          note=A["acq_ip26_note"])
    sched("dil_sec", "  Dilutive securities (m shares)", A["dil_sec"], fmt=FMT_SHR)
    sched("px_g", "  Share-price appreciation % (buyback pricing)", A["px_g"], fmt=FMT_PCT)
    add(Row("blk_sch2", "Debt schedule (scheduled maturities + revolver to a minimum cash balance)", style="block"))
    add(Row("debt", "  Total debt (current + long-term)", style="sched", annual_only=True,
            hist=ha(lambda x: f'=IF(ISNUMBER({x.a("ltd")}),N({x.a("cltd")})+{x.a("ltd")},"")'),
            e26=lambda x: f"={x.pp('debt')}+{x.a('d_mand')}+{x.a('d_rev')}",
            e=lambda x: f"={x.pp('debt')}+{x.a('d_mand')}+{x.a('d_rev')}-{x.pp('d_rev')}",
            note=A["debt_note"]))
    add(Row("d_mand", "  Scheduled maturities / repayments (input, negative)", style="sched", annual_only=True,
            input_fc=True, e26=A["debt_mand"][2026], e=lambda x: A["debt_mand"][x.c.year],
            note="2026E includes the $450m April-2026 maturity repaid in Q2."))
    add(Row("d_cashpre", "  Cash before revolver (opening cash + CFO + CFI + non-debt CFF + FX + maturities)",
            annual_only=True,
            fc=lambda x: (f"={x.pp('cash')}+{x.a('cfo')}+{x.a('cfi')}+{x.a('cf_bb')}+{x.a('cf_opt')}+{x.a('cf_ofin')}"
                          f"+{x.a('cf_fx')}+{x.a('d_mand')}")))
    add(Row("d_mincash", "  Minimum cash balance", style="sched", annual_only=True, input_fc=True,
            fc=lambda x: A["min_cash"][x.c.year]))
    add(Row("d_rev", "  Revolver / new borrowings outstanding (year end)", annual_only=True,
            e26=lambda x: f"=MAX(0,{x.a('d_mincash')}-{x.a('d_cashpre')})",
            e=lambda x: f"=MAX(0,{x.pp('d_rev')}+{x.a('d_mincash')}-{x.a('d_cashpre')})",
            note="Draws when cash would fall below the minimum (e.g. Bull M&A); repaid from surplus cash first."))
    add(Row("debt_iss", "  Net issuance / (repayment)", annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("debt")}-{x.py("debt")},"")' if x.c.kind in ("A", "Y") and x.py("debt") else None),
            fc=lambda x: f"={x.a('debt')}-{x.pp('debt')}"))
    add(Row("int_rate", "  Interest rate on opening total debt %", style="sched", fmt=FMT_PCT, annual_only=True,
            input_fc=True,
            hist=lambda x: (f'=IFERROR({x.a("interest_exp_net")}/{x.py("debt")},"")'
                            if x.c.kind in ("A", "Y") and x.py("debt") else None),
            e26=lambda x: f'=IFERROR({x.a("interest_exp_net")}/{x.pp("debt")},"")',
            e=lambda x: A["int_rate"][x.c.year], note=A["int_note"]))
    add(Row("cash_rate", "  Interest income yield on opening cash %", style="sched", fmt=FMT_PCT, annual_only=True,
            input_fc=True, e=lambda x: A["cash_rate"][x.c.year],
            note="Teledyne reports interest net; historical rate above is net interest / opening debt."))
    add(Row("blk_sch3", "Historical reference (driver context)", style="block"))
    add(Row("h_da", "  Total D&A % of sales", style="pct", fmt=FMT_PCT, cagr="avg", annual_only=True,
            hist=lambda x: f'=IFERROR({x.a("da")}/{x.a("net_sales")},"")' if x.c.kind in ("A", "Y") else None,
            fc=ratio("da", "net_sales")))
    add(Row("h_am", "  Acquired-intangible amortization % of sales", style="pct", fmt=FMT_PCT, cagr="avg",
            annual_only=True,
            hist=lambda x: f'=IFERROR({x.a("am_tot")}/{x.a("net_sales")},"")' if x.c.kind in ("A", "Y") else None,
            fc=ratio("am_tot", "net_sales")))
    add(Row(None, style="blank"))

    ratios_rows(R, A)


def ratios_rows(R, A):
    add = R.append
    ann = lambda f: (lambda x: f(x) if x.c.kind in ("A", "Y") else None)  # noqa: E731

    def rr(key, label, f, style="line", fmt=FMT_NUM, cagr=None):
        add(Row(key, label, style=style, fmt=fmt, annual_only=True, hist=ann(f), fc=f, cagr=cagr))

    add(Row("sec_ratio", "RATIO ANALYSIS", style="section"))
    add(Row("blk_roic", "DuPont decomposition of ROIC", style="block"))
    rr("r_ebit", "Non-GAAP operating income (current definition)", lambda x: f"={x.a('o_cur')}")
    rr("r_tax", "Effective tax rate (actual)", lambda x: f"={x.a('etr')}", fmt=FMT_PCT)
    rr("r_nopat", "NOPAT  =  Non-GAAP OI × (1 − tax rate)",
       lambda x: f'=IFERROR({x.a("r_ebit")}*(1-{x.a("r_tax")}),"n/a")')
    rr("r_ic", "Invested capital (IC)  =  Equity + Net debt", lambda x: f'=IFERROR({x.a("r_eq")}+{x.a("r_nd")},"n/a")')
    rr("r_eq", "  Total equity incl. redeemable NCI", lambda x: f"={x.a('teq')}+N({x.a('rnci')})")
    rr("r_nd", "  Net debt  =  Total debt − Cash", lambda x: f"={x.a('debt')}-{x.a('cash')}")
    rr("roic", "ROIC  =  NOPAT / IC", lambda x: f'=IFERROR({x.a("r_nopat")}/{x.a("r_ic")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    rr("r_m", "  Margin  =  Non-GAAP OI / Sales", lambda x: f'=IFERROR({x.a("r_ebit")}/{x.a("net_sales")},"n/a")',
       fmt=FMT_PCT)
    rr("r_t", "  Capital turnover  =  Sales / IC", lambda x: f'=IFERROR({x.a("net_sales")}/{x.a("r_ic")},"n/a")',
       fmt=FMT_X)
    rr("r_tb", "  Tax burden  =  (1 − effective tax rate)", lambda x: f'=IFERROR(1-{x.a("r_tax")},"n/a")', fmt=FMT_PCT)
    rr("r_chk", "  Check: Margin × Turnover × Tax burden  =  ROIC",
       lambda x: f'=IFERROR({x.a("r_m")}*{x.a("r_t")}*{x.a("r_tb")},"n/a")', fmt=FMT_PCT)
    add(Row(None, style="blank"))
    add(Row("blk_ronta", "RONTA decomposition", style="block"))
    rr("t_nopat", "NOPAT  =  Non-GAAP OI × (1 − tax rate)", lambda x: f"={x.a('r_nopat')}")
    rr("t_ta", "  Total assets", lambda x: f"={x.a('ta')}")
    rr("t_gw", "  − Goodwill & acquired intangible assets", lambda x: f"=-({x.a('gw')}+{x.a('intang')})")
    rr("t_nibcl", "  − Non-interest-bearing current liabilities (total CL excl. debt)",
       lambda x: f"=-({x.a('tcl')}-N({x.a('cltd')}))")
    rr("t_nta", "  = Net tangible assets", lambda x: f"=SUM({x.a('t_ta')}:{x.a('t_nibcl')})")
    rr("ronta", "RONTA  =  NOPAT / NTA", lambda x: f'=IFERROR({x.a("t_nopat")}/{x.a("t_nta")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    add(Row(None, style="blank"))
    add(Row("blk_roe", "Return on Equity (ROE)", style="block"))
    rr("e_ni2", "Net income attributable to Teledyne", lambda x: f"={x.a('ni_tdy')}")
    rr("e_eq", "Teledyne stockholders' equity", lambda x: f"={x.a('eqp')}")
    rr("roe", "ROE  =  NI / Equity", lambda x: f'=IFERROR({x.a("e_ni2")}/{x.a("e_eq")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    add(Row(None, style="blank"))
    add(Row("blk_lev", "Leverage", style="block"))
    rr("l_nd", "Net debt  =  Total debt − cash (company definition)", lambda x: f"={x.a('r_nd')}")
    rr("l_ebitda", "Adjusted EBITDA (model)", lambda x: f"={x.a('adj_ebitda')}")
    rr("lev", "Net debt / adjusted EBITDA (x)", lambda x: f'=IFERROR({x.a("l_nd")}/{x.a("l_ebitda")},"n/a")',
       style="total", fmt=FMT_X)
    add(Row("lev_pub", "  Memo: company leverage ratio as published (x)", style="memo", fmt=FMT_X,
            src="ops.leverage_published", annual_only=True, agg="none"))
    add(Row(None, style="blank"))

    add(Row("sec_val", "VALUATION", style="section",
            note="VALUATION — current share price input $615 (per user); applied to 2026E–2030E"))
    add(Row("px", "Share price ($) — current", style="sched", fmt=FMT_EPS, annual_only=True, input_fc=True,
            e26=A["px"], e=lambda x: f"={x.pp('px')}"))
    rr2 = lambda key, label, f, fmt=FMT_NUM, style="line": add(  # noqa: E731
        Row(key, label, style=style, fmt=fmt, annual_only=True, quarters_ok=False, e26=f, e=f))
    rr2("v_sh", "Diluted shares (m)", lambda x: f"={x.a('sh_dil')}", fmt=FMT_SHR)
    rr2("v_mcap", "Market capitalisation (USDm)", lambda x: f'=IFERROR({x.a("px")}*{x.a("v_sh")},"n/a")')
    rr2("v_nd", "Net debt (USDm)", lambda x: f"={x.a('l_nd')}")
    rr2("v_nci", "Non-controlling interests (incl. redeemable, USDm)", lambda x: f"={x.a('rnci')}+{x.a('nci_bs')}")
    rr2("v_ev", "Enterprise value (USDm)", lambda x: f'=IFERROR({x.a("v_mcap")}+{x.a("v_nd")}+{x.a("v_nci")},"n/a")',
        style="sub")
    add(Row("blk_mult", "Multiples", style="block"))
    for key, lab, f, fmt in [
        ("m_evs", "  EV / Sales", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("net_sales")},"n/a")', FMT_X),
        ("m_evebitda", "  EV / Adjusted EBITDA", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("adj_ebitda")},"n/a")', FMT_X),
        ("m_evebit", "  EV / Non-GAAP operating income", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("o_cur")},"n/a")',
         FMT_X),
        ("m_evic", "  EV / IC", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("r_ic")},"n/a")', FMT_X),
        ("m_pe", "  P / E (GAAP diluted)", lambda x: f'=IFERROR({x.a("px")}/{x.a("eps_dil")},"n/a")', FMT_X),
        ("m_pea", "  P / E (non-GAAP, company definition)", lambda x: f'=IFERROR({x.a("px")}/{x.a("c_eps")},"n/a")',
         FMT_X),
        ("m_fcfy", "  FCF yield", lambda x: f'=IFERROR({x.a("fcf")}/{x.a("v_mcap")},"n/a")', FMT_PCT)]:
        rr2(key, lab, f, fmt=fmt)
