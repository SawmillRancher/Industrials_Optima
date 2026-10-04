"""Row definitions for the Hermès Model tab.

Layout follows the MLM model (itself on the TDY template): revenue build → group total → IFRS income statement →
IFRS→adjusted bridges → growth & margins → cash flow → buyback → balance sheet → working capital → BS schedules →
ratios → valuation.

Hermès discloses no volumes or prices, so the build is a métier (sector) revenue build: prior-period revenue ×
(1 + constant-currency growth + currency effect). Profit is modelled at group level (gross margin and recurring
operating margin levers) because Hermès reports profitability by geographical area only (IFRS 8 segments), shown as a
memo. Hermès' alternative performance measures — recurring operating income, adjusted free cash flow and restated net
cash — are reconciled to the IFRS statements and checked against every published figure; EBITDA and recurring net
income / EPS are model measures (Hermès publishes net income excluding the French exceptional contribution for 2025
and H1/25–H1/26, which the recurring-NI bridge is checked against).
"""
from __future__ import annotations

from .data import AREAS, SECTORS
from .framework import FMT_DAYS, FMT_EPS, FMT_NUM, FMT_PCT, FMT_SHR, FMT_X, Row, ratio, yoy
from .scenario import (S_BUYB, S_CAPEX26, S_CC, S_EXC26, S_FX26, S_GM, S_PAYOUT, S_ROI, S_TAX26, S_XDIV,
                       SECTOR_NAMES, srow)

SECTOR_DESC = {
    "leather": "Leather Goods & Saddlery (bags, travel, small leather goods, saddles & equestrian)",
    "rtw": "Ready-to-wear and Accessories (men's & women's RTW, belts, fashion jewellery, gloves, hats, shoes)",
    "silk": "Silk and Textiles",
    "other_hermes": "Other Hermès sectors (Jewellery, Home / Art of Living & Tableware — Tableware folded in from 2014)",
    "perfume": "Perfume and Beauty (Perfumes to 2019; Beauty from 2020)",
    "watches": "Watches (La Montre Hermès)",
    "other_products": "Other products (John Lobb, Saint-Louis, Puiforcat, textile production for third parties)",
}
SRC_SECTOR = {s: f"sector.{s}" for s in SECTORS}
SRC_SECTOR["other_hermes"] = "sector.other_hermes_c"
SRC_CC = {s: f"sector.cc_{s}" for s in SECTORS}
SRC_CC["other_hermes"] = "sector.cc_other_hermes_c"
AREA_NAMES = {"france": "France", "europe": "Europe (excl. France)", "japan": "Japan",
              "apac": "Asia-Pacific (excl. Japan)", "americas": "Americas", "other": "Other (Middle East)"}

DEF_B1 = {
    "2009": "IAS 17 (pre-IFRS 16)||Leases off balance sheet to 2018: rents in operating expenses; EBITDA pre- and "
            "post-IFRS 16 are identical. FY2009 = comparative column of the 2010 registration document.",
    "H1/19": "IFRS 16 from 1-Jan-2019||Right-of-use assets and lease liabilities on the balance sheet; depreciation of "
             "right-of-use assets in operating expenses, lease interest in net financial income, principal repayments "
             "in financing cash flows. 2018 is shown as originally reported (not restated).",
    "2019": "IFRS 16 from 1-Jan-2019||See H1/19.",
}
DEF_B2 = {
    "2017": "2017: French surtaxes||Two exceptional 15% French corporate-tax surtaxes net of the refund of the 3% "
            "dividend tax: net expense €20m (2017 registration document, tax note).",
    "2018": "2018: HK property gain||Non-recurring income €52.7m: gain on sale of the former Galleria store premises "
            "in Hong Kong (not taxed). Recognised in H1/18.",
    "2020": "2020: Shang Xia||Non-recurring income €91.1m: deconsolidation of Shang Xia after Exor's reserved capital "
            "increase (23-Dec-2020; not taxed).",
    "H1/25": "French exceptional contribution||Exceptional contribution on the profits of large companies in France "
             "(2025, renewed 2026). H1 amounts estimated from the disclosed ETR with / without it; FY2025 €331m "
             "disclosed. Hermès publishes net income excluding it (rounded to €0.1bn / €0.01bn).",
    "2025": "Contribution €331m||2025 URD: ETR 33.4% (28.5% excluding the contribution); net income excluding it "
            "€4.86bn.",
}
DEF_B3 = {
    "2018": "Free cash flow (pre-IFRS 16)||2018 and before: free cash flow = operating cash flows after working "
            "capital less operating investments (no lease repayments).",
    "H1/19": "Adjusted FCF (from 2019)||Hermès APM: cash flows from operating activities − operating investments − "
             "repayment of lease liabilities.",
}
DEF_B4 = {
    "2017": "Restated net cash (from 2017)||Net cash + cash investments with original maturity > 3 months (not cash "
            "equivalents under IFRS).",
    "2020": "Less financial liabilities (from 2020)||Restated net cash also deducts financial liabilities.",
}


def build_rows(info):
    A = info["assump"]
    P = info["P"]
    R = []
    add = R.append

    def have(x, *keys):
        c = x.c
        if c.kind == "H2":
            pers = [str(c.year), f"H1/{c.year % 100:02d}"]
        else:
            pers = [c.key]
        return all(P.get(p, {}).get(k) is not None for p in pers for k in keys)

    def blank():
        add(Row(None, style="blank"))

    def scn(base):
        return lambda x: "=" + x.scn(srow(base, x.c))

    # =====================================================================================
    add(Row("sec_rev", "MÉTIER REVENUE BUILD — SEVEN SECTORS (prior period × (1 + constant-currency growth + currency "
                       "effect))", style="section",
            note="MÉTIER BUILD — modelling logic (constant-currency growth by métier + group currency effect)"))
    blank()
    for s in SECTORS:
        add(Row(f"blk_{s}", SECTOR_DESC[s], style="block", note=f"{SECTOR_NAMES[s].upper()} — modelling logic"))
        add(Row(f"rev_{s}", "  Revenue", style="sub", src=SRC_SECTOR[s], cagr="cagr",
                he=lambda x, s=s: f"={x.py('rev_' + s)}*(1+{x.a('cc_' + s)}+{x.a('fx_grp')})",
                e=lambda x, s=s: f"={x.pp('rev_' + s)}*(1+{x.a('cc_' + s)}+{x.a('fx_grp')})",
                note="H2/26E: H2/25 × (1 + scenario constant-currency growth + H2/26E currency effect). 2027E+: prior "
                     "year × (1 + scenario cc growth + currency effect).",
                comment=("Source: revenue by métier — registration documents / URDs (FY, management report) and "
                         "half-year financial reports (H1). FY2009–11 printed in whole €m. H2 = FY − H1."
                         if s == "leather" else "")))
        add(Row(f"g_{s}", "  Revenue y/y % (reported)", style="growth", fmt=FMT_PCT,
                hist=yoy(f"rev_{s}"), fc=yoy(f"rev_{s}")))
        add(Row(f"cc_{s}", "  Revenue y/y % at constant exchange rates (company)", style="pct", fmt=FMT_PCT,
                src=SRC_CC[s], agg="none", cagr="avg",
                he=scn(S_CC[s]), e=scn(S_CC[s]),
                e26=lambda x, s=s: (f"=({x.at('rev_' + s, 'H1/25')}*(1+{x.at('cc_' + s, 'H1/26')})"
                                    f"+{x.at('rev_' + s, 'H2/25')}*(1+{x.at('cc_' + s, 'H2/26E')}))"
                                    f"/{x.at('rev_' + s, '2025')}-1"),
                note=f"Scenario lever ({s.upper()}_ccGrowth, Bull/Base/Bear table →). 2026E = H1/26 actual and "
                     f"H2/26E growth weighted by 2025 halves. Company figures to one decimal (press releases)."))
        add(Row(f"fx_{s}", "  Currency (and scope) effect on growth, pts (reported − constant FX)", style="pct",
                fmt=FMT_PCT,
                hist=lambda x, s=s: (f'=IF(AND(ISNUMBER({x.a("g_" + s)}),ISNUMBER({x.a("cc_" + s)})),'
                                     f'{x.a("g_" + s)}-{x.a("cc_" + s)},"")'),
                he=lambda x: f"={x.a('fx_grp')}", e=lambda x: f"={x.a('fx_grp')}",
                e26=lambda x, s=s: f"={x.a('g_' + s)}-{x.a('cc_' + s)}",
                note="Forecast: group currency effect applied to every métier." if s == "leather" else
                     ("2014: Other Hermès sectors scope restated by the company (Tableware folded in, comparatives "
                      "restated), so reported y/y vs 2013 as originally published is not like-for-like."
                      if s == "other_hermes" else "")))
        add(Row(f"sh_{s}", "  % of group revenue", style="pct", fmt=FMT_PCT, cagr="avg",
                hist=ratio(f"rev_{s}", "rev_grp"), fc=ratio(f"rev_{s}", "rev_grp")))
        if s == "other_hermes":
            add(Row("tableware", "  Memo: Tableware (separate métier to 2013, as originally reported)", style="memo",
                    src="sector.tableware"))
        blank()

    add(Row("blk_grp", "Group revenue (métier build) — constant-currency growth and currency effect", style="block",
            note="GROUP REVENUE — modelling logic"))
    sec_sum = lambda x: "+".join(f"N({x.a('rev_' + s)})" for s in SECTORS)  # noqa: E731
    add(Row("rev_grp", "Revenue (métier build)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("rev_leather")}),{sec_sum(x)},"")',
            fc=lambda x: "=" + "+".join(x.a("rev_" + s) for s in SECTORS),
            note="Σ métier revenues."))
    add(Row("g_grp", "  Revenue y/y % (reported)", style="growth", fmt=FMT_PCT, hist=yoy("rev_grp"), fc=yoy("rev_grp")))
    add(Row("cc_grp", "  Revenue y/y % at constant exchange rates (company; forecast = Σ métiers)", style="pct",
            fmt=FMT_PCT, src="sector.cc_total", agg="none", cagr="avg",
            fc=lambda x: ("=(" + "+".join(f"{x.py('rev_' + s)}*{x.a('cc_' + s)}" for s in SECTORS) + ")/("
                          + "+".join(x.py("rev_" + s) for s in SECTORS) + ")"),
            note="Hermès' headline growth measure. Forecast = prior-period-weighted average of métier cc growth."))
    add(Row("fx_grp", "  Currency (and scope) effect, pts (reported − constant FX)", style="pct", fmt=FMT_PCT,
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("g_grp")}),ISNUMBER({x.a("cc_grp")})),'
                            f'{x.a("g_grp")}-{x.a("cc_grp")},"")'),
            he=lambda x: "=" + x.scn(S_FX26), e26=lambda x: f"={x.a('g_grp')}-{x.a('cc_grp')}",
            e=lambda x: A["fx"][x.c.year], input_fc=True,
            note="H2/26E: scenario point estimate (Bull / Base / Bear table →). " + A["fx_note"]))
    add(Row("rev_chk", "  Check: métier build vs consolidated revenue (should be 0; ±1 whole-€m rounding)",
            style="check",
            hist=lambda x: f'=IF(AND(ISNUMBER({x.a("rev_grp")}),ISNUMBER({x.a("revenue")})),ROUND({x.a("rev_grp")}'
                           f'-{x.a("revenue")},0),"")',
            fc=lambda x: f"=ROUND({x.a('rev_grp')}-{x.a('revenue')},0)"))
    add(Row("q_hdr", "Quarterly revenue (memo; Hermès publishes revenue only for Q1 and Q3)", style="memo"))
    add(Row("qa_rev", "  Revenue — 1st quarter of the half (Q1 in H1 columns, Q3 in H2 columns)", src="qa.revenue",
            agg="none", comment="Source: quarterly revenue releases and the quarter columns of the half-year and "
                                "full-year results releases (Q1/14–Q2/26)."))
    add(Row("qa_cc", "    y/y % at constant exchange rates", style="pct", fmt=FMT_PCT, src="qa.cc_growth", agg="none"))
    add(Row("qb_rev", "  Revenue — 2nd quarter of the half (Q2 in H1 columns, Q4 in H2 columns)", src="qb.revenue",
            agg="none"))
    add(Row("qb_cc", "    y/y % at constant exchange rates", style="pct", fmt=FMT_PCT, src="qb.cc_growth", agg="none"))
    add(Row("q_chk", "  Check: quarters vs half-year revenue (should be 0; ±1 from whole-€m quarters)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("qa_rev")}),ISNUMBER({x.a("qb_rev")})),ROUND({x.a("qa_rev")}'
                            f'+{x.a("qb_rev")}-{x.a("revenue")},0),"")') if x.c.is_half else None))
    blank()

    # ---------------- Geography ----------------
    add(Row("blk_geo", "Revenue & recurring operating income by geographical area (IFRS 8 operating segments; memo)",
            style="block", note="GEOGRAPHY — historical disclosure (memo cross-check; not forecast)"))
    for a in AREAS:
        add(Row(f"geo_{a}", f"  Revenue — {AREA_NAMES[a]}", src=f"geo.rev_{a}", cagr="cagr",
                comment="Source: segment note (revenue by destination) in the URDs / half-year reports." if a == "france"
                else ""))
    geo_sum = lambda x: "+".join(f"N({x.a('geo_' + a)})" for a in AREAS)  # noqa: E731
    add(Row("geo_tot", "  Revenue — total of areas", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("geo_france")}),{geo_sum(x)},"")'))
    add(Row("geo_chk", "  Check: Σ areas vs consolidated revenue (should be 0; ±1 whole-€m rounding)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("geo_tot")}),ISNUMBER({x.a("revenue")})),'
                            f'ROUND({x.a("geo_tot")}-{x.a("revenue")},0),"")')))
    for a in AREAS:
        add(Row(f"geo_sh_{a}", f"  % of revenue — {AREA_NAMES[a]}", style="pct", fmt=FMT_PCT, cagr="avg",
                hist=ratio(f"geo_{a}", "geo_tot")))
    for a in AREAS:
        add(Row(f"geo_cc_{a}", f"  y/y % at constant exchange rates — {AREA_NAMES[a]}", style="pct", fmt=FMT_PCT,
                src=f"geo.cc_{a}", agg="none"))
    for a in AREAS:
        add(Row(f"roi_{a}", f"  Recurring operating income — {AREA_NAMES[a]}", src=f"geo.roi_{a}"))
    add(Row("roi_unalloc", "  Recurring operating income — Unallocated / Holding (free-share plans, central costs, "
                           "internal billings)", src="geo.roi_unalloc"))
    roi_sum = lambda x: "+".join(f"N({x.a('roi_' + a)})" for a in AREAS + ["unalloc"])  # noqa: E731
    add(Row("roi_geo_tot", "  Recurring operating income — total of areas", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("roi_france")}),{roi_sum(x)},"")'))
    add(Row("roi_geo_chk", "  Check: Σ areas vs consolidated recurring operating income (should be 0; ±1–3 rounding)",
            style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("roi_geo_tot")}),ISNUMBER({x.a("roi")})),'
                            f'ROUND({x.a("roi_geo_tot")}-{x.a("roi")},0),"")')))
    for a in AREAS:
        add(Row(f"roim_{a}", f"  Recurring operating margin — {AREA_NAMES[a]}", style="pct", fmt=FMT_PCT, cagr="avg",
                hist=ratio(f"roi_{a}", f"geo_{a}")))
    blank()

    # ---------------- Profitability drivers ----------------
    add(Row("blk_prof", "Profitability drivers (group; % of revenue)", style="block",
            note="PROFITABILITY — scenario levers (gross margin, recurring operating margin) and cost inputs"))
    add(Row("gm_pct", "  Gross margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("gross", "revenue"),
            he=scn(S_GM), e=scn(S_GM), e26=ratio("gross", "revenue"),
            note="Scenario lever (GM). Cost of sales = revenue × (1 − gross margin)."))
    add(Row("roi_m", "  Recurring operating margin % (Hermès KPI)", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("roi", "revenue"), he=scn(S_ROI), e=scn(S_ROI), e26=ratio("roi", "revenue"),
            note="Scenario lever (ROI_margin). Recurring operating income = revenue × margin; sales & administrative "
                 "expenses are the balancing line."))
    add(Row("oie_pct", "  Other income and expenses (net expense) % of revenue", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f'=IF(AND(ISNUMBER({x.a("oie")}),ISNUMBER({x.a("revenue")})),-{x.a("oie")}/{x.a("revenue")},"")',
            he=lambda x: A["oie_pct"][2026], e26=lambda x: f"=-{x.a('oie')}/{x.a('revenue')}",
            e=lambda x: A["oie_pct"][x.c.year], input_fc=True, note=A["oie_note"]))
    add(Row("sa_pct", "  Sales and administrative expenses % of revenue (balancing line)", style="pct", fmt=FMT_PCT,
            cagr="avg",
            hist=lambda x: f'=IF(AND(ISNUMBER({x.a("sga")}),ISNUMBER({x.a("revenue")})),-{x.a("sga")}/{x.a("revenue")},"")',
            fc=lambda x: f"=-{x.a('sga')}/{x.a('revenue')}"))
    add(Row("da_pct", "  D&A of PP&E and intangibles incl. impairment (excl. right-of-use) % of revenue", style="pct",
            fmt=FMT_PCT, cagr="avg", hist=ratio("da_fixed", "revenue"), he=ratio("da_fixed", "revenue"),
            e26=lambda x: A["da_pct"][2026], e=lambda x: A["da_pct"][x.c.year], input_fc=True, note=A["da_note"]))
    add(Row("sbc_pct", "  Share-based payments (free-share plans, CF statement) % of revenue", style="pct",
            fmt=FMT_PCT, hist=ratio("sbc", "revenue"), he=ratio("sbc", "revenue"),
            e26=lambda x: A["sbc_pct"][2026], e=lambda x: A["sbc_pct"][x.c.year], input_fc=True))
    blank()

    # =====================================================================================
    add(Row("sec_is", "CONSOLIDATED INCOME STATEMENT (IFRS as reported; expenses negative)", style="section",
            note="CONSOLIDATED IS — forecast logic"))

    def sub_or_data(keys, f):
        return lambda x: f(x) if have(x, *keys) else None

    add(Row("revenue", "Revenue", style="total", src="is.revenue", cagr="cagr", fc=lambda x: f"={x.a('rev_grp')}",
            note="Forecast linked to the métier build.",
            comment="Source: consolidated income statement — registration documents / URDs (FY), half-year financial "
                    "reports (H1); FY2006–08 key consolidated data (2010 registration document). H2 = FY − H1."))
    add(Row("cogs", "Cost of sales", src="is.cogs",
            he=lambda x: f"=-{x.a('revenue')}*(1-{x.a('gm_pct')})", e=lambda x: f"=-{x.a('revenue')}*(1-{x.a('gm_pct')})"))
    add(Row("gross", "Gross margin", style="sub", src="is.gross_margin",
            hist=sub_or_data(("is.revenue", "is.cogs"), lambda x: f"={x.a('revenue')}+{x.a('cogs')}"),
            he=lambda x: f"={x.a('revenue')}+{x.a('cogs')}", e=lambda x: f"={x.a('revenue')}+{x.a('cogs')}"))
    add(Row("sga", "Sales and administrative expenses", src="is.sga",
            he=lambda x: f"={x.a('roi')}-{x.a('gross')}-{x.a('oie')}",
            e=lambda x: f"={x.a('roi')}-{x.a('gross')}-{x.a('oie')}",
            note="Forecast: balancing line so that recurring operating income = revenue × recurring operating margin.",
            comment="2015 reclassification: free-share plan expense moved from S&A to other income and expenses (2014 "
                    "as originally reported)."))
    add(Row("oie", "Other income and expenses (incl. D&A outside cost of sales, free-share plans)", src="is.other_inc_exp",
            he=lambda x: f"=-{x.a('revenue')}*{x.a('oie_pct')}", e=lambda x: f"=-{x.a('revenue')}*{x.a('oie_pct')}"))
    add(Row("roi", "Recurring operating income", style="total", src="is.roi", cagr="cagr",
            hist=sub_or_data(("is.revenue", "is.cogs", "is.sga", "is.other_inc_exp"),
                             lambda x: f"={x.a('gross')}+{x.a('sga')}+{x.a('oie')}"),
            he=lambda x: f"={x.a('revenue')}*{x.a('roi_m')}", e=lambda x: f"={x.a('revenue')}*{x.a('roi_m')}",
            note="Hermès' main performance indicator (APM): operating income excluding non-recurring items."))
    add(Row("roi_chk", "  Check: recurring operating income vs reported (should be 0; ±1–3 whole-€m rounding of printed lines)",
            style="check",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("b1_roi_pub")}),ROUND({x.a("roi")}-{x.a("b1_roi_pub")},0),"")')))
    add(Row("nonrec", "Other non-recurring income and expenses", src="is.nonrec", he=0, e=0,
            note="2006–07: operating income − recurring operating income (items not described); 2018 HK property gain "
                 "€52.7m; 2020 Shang Xia deconsolidation €91.1m."))
    add(Row("op_inc", "Operating income", style="total", src="is.op_inc", cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("roi")}),{x.a("roi")}+N({x.a("nonrec")}),"")'
                            if have(x, "is.roi") else None),
            he=lambda x: f"={x.a('roi')}+{x.a('nonrec')}", e=lambda x: f"={x.a('roi')}+{x.a('nonrec')}"))
    add(Row("fin_inc", "Net financial income (incl. interest on lease liabilities)", src="is.fin_inc",
            he=lambda x: f"=0.5*{x.at('cash_yield', '2026E')}*{x.at('rnc', 'H1/26')}-{x.a('lease_int')}",
            e=lambda x: f"={x.a('cash_yield')}*{x.pp('rnc')}-{x.a('lease_int')}",
            note="Forecast: yield × opening restated net cash − interest on lease liabilities (H2/26E: half-year yield on "
                 "the 30-Jun-26 balance)."))
    add(Row("lease_int", "  Memo: interest on lease liabilities (IFRS 16; within net financial income)", style="memo",
            src="memo.lease_interest",
            he=lambda x: f"=0.5*{x.at('lease_rate', '2026E')}*{x.at('lease_tot', 'H1/26')}",
            e=lambda x: f"={x.a('lease_rate')}*{x.pp('lease_tot')}"))
    add(Row("pbt", "Net income before tax", style="sub", src="is.pbt", cagr="cagr",
            hist=sub_or_data(("is.roi", "is.fin_inc"), lambda x: f"={x.a('op_inc')}+{x.a('fin_inc')}"),
            he=lambda x: f"={x.a('op_inc')}+{x.a('fin_inc')}", e=lambda x: f"={x.a('op_inc')}+{x.a('fin_inc')}"))
    add(Row("tax", "Income tax", src="is.tax",
            he=lambda x: (f"=-{x.base(S_TAX26)}*({x.at('pbt', 'H1/26')}+{x.a('pbt')})-{x.at('tax', 'H1/26')}"),
            e=lambda x: f"=-{x.a('pbt')}*{x.a('etr_in')}",
            note="H2/26E: 2026E ETR (33% incl. the exceptional contribution, H1/26 report) × 2026E pre-tax income − "
                 "H1/26 tax. 2027E+: ETR input."))
    add(Row("etr", "  Effective tax rate", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f'=IF(AND(ISNUMBER({x.a("tax")}),ISNUMBER({x.a("pbt")})),-{x.a("tax")}/{x.a("pbt")},"")',
            fc=lambda x: f"=-{x.a('tax')}/{x.a('pbt')}"))
    add(Row("excep", "  of which: French exceptional contribution / surtaxes (expense +)", style="memo",
            src="n.excep_tax",
            he=lambda x: (f"={x.base(S_EXC26)}*({x.at('pbt', 'H1/26')}+{x.a('pbt')})-{x.at('excep', 'H1/26')}"),
            e=0,
            note="2017: surtaxes net of 3% dividend-tax refund (€20m). 2025: €331m. H1/25, H1/26: estimated from the "
                 "disclosed ETR with / without the contribution. 2027E+: assumed not renewed."))
    add(Row("etr_ex", "  Effective tax rate excl. exceptional contribution / surtaxes", style="pct", fmt=FMT_PCT,
            cagr="avg",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("tax")}),ISNUMBER({x.a("pbt")})),'
                            f'(-{x.a("tax")}-N({x.a("excep")}))/{x.a("pbt")},"")'),
            fc=lambda x: f"=(-{x.a('tax')}-{x.a('excep')})/{x.a('pbt')}"))
    add(Row("etr_in", "  ETR input (2027E+)", style="sched", fmt=FMT_PCT, halves=False, input_fc=True,
            e=lambda x: A["etr"][x.c.year], note=A["etr_note"]))
    add(Row("assoc", "Net income from associates", src="is.assoc",
            he=lambda x: f"={x.at('assoc', 'H1/26')}", e=lambda x: A["assoc"][x.c.year], input_fc=True))
    add(Row("cons_ni", "Consolidated net income", style="sub", src="is.cons_ni", cagr="cagr",
            hist=sub_or_data(("is.pbt", "is.tax", "is.assoc"),
                             lambda x: f"={x.a('pbt')}+{x.a('tax')}+{x.a('assoc')}"),
            he=lambda x: f"={x.a('pbt')}+{x.a('tax')}+{x.a('assoc')}",
            e=lambda x: f"={x.a('pbt')}+{x.a('tax')}+{x.a('assoc')}"))
    add(Row("nci", "Non-controlling interests", src="is.nci",
            he=lambda x: f"=-{x.a('cons_ni')}*{x.at('nci_pct', '2026E')}",
            e=lambda x: f"=-{x.a('cons_ni')}*{x.a('nci_pct')}"))
    add(Row("ni", "Net income attributable to owners of the parent", style="total", src="is.ni", cagr="cagr",
            hist=sub_or_data(("is.pbt", "is.tax", "is.assoc", "is.nci"),
                             lambda x: f"={x.a('cons_ni')}+{x.a('nci')}"),
            he=lambda x: f"={x.a('cons_ni')}+{x.a('nci')}", e=lambda x: f"={x.a('cons_ni')}+{x.a('nci')}"))
    add(Row("ni_chk", "  Check: net income attributable vs reported (should be 0; ±1–2 whole-€m rounding)",
            style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni_rep")}),ROUND({x.a("ni")}-{x.a("ni_rep")},0),"")'))
    add(Row("ni_rep", "  Memo: net income attributable as reported", style="memo", src="is.ni"))
    add(Row("da_tot", "  Memo: depreciation, amortisation & impairment — total incl. right-of-use (CF statement)",
            style="memo", src="n.da_total", annual_fc=True,
            fc=lambda x: f"={x.a('da_fixed')}+{x.a('da_rou')}",
            comment="Cash-flow statement: depreciation & amortisation of fixed assets + right-of-use assets (from 2019) "
                    "+ impairment losses (shown as separate lines in some years; summed here)."))
    add(Row("da_rou", "    of which: depreciation of right-of-use assets (IFRS 16, from 2019)", style="memo",
            src="n.da_rou", annual_fc=True, fc=lambda x: f"={x.a('rou_dep')}"))
    add(Row("da_fixed", "    of which: PP&E and intangibles incl. impairment", style="memo",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("da_tot")}),{x.a("da_tot")}-N({x.a("da_rou")}),"")'),
            annual_fc=True, fc=lambda x: f"={x.a('revenue')}*{x.a('da_pct')}"))
    add(Row("sbc", "  Memo: share-based payments (free-share plans; CF statement)", style="memo", src="memo.sbc_cf",
            annual_fc=True, fc=lambda x: f"={x.a('revenue')}*{x.a('sbc_pct')}"))
    add(Row("eps_hdr", "(Earnings per share)", style="line"))
    add(Row("sh_basic", "  Weighted-average basic shares (m)", src="memo.shares_wavg_basic", agg="last", fmt=FMT_SHR,
            he=lambda x: f"={x.at('sh_basic', 'H1/26')}",
            e=lambda x: f"=AVERAGE({x.a('bb_beg')},{x.a('bb_end')})",
            note="H2 columns: full-year average (FY). 2027E+: average of beginning and ending shares outstanding."))
    add(Row("sh_dil", "  Weighted-average diluted shares (m)", src="memo.shares_wavg_diluted", agg="last", fmt=FMT_SHR,
            he=lambda x: f"={x.at('sh_dil', 'H1/26')}", e=lambda x: f"={x.a('sh_basic')}+{x.a('dil_sec')}"))
    add(Row("eps_basic", "EPS – basic (€)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("ni")}/{x.a("sh_basic")},"")',
            fc=lambda x: f'=IFERROR({x.a("ni")}/{x.a("sh_basic")},"")'))
    add(Row("eps_dil", "EPS – diluted (€)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("ni")}/{x.a("sh_dil")},"")',
            fc=lambda x: f'=IFERROR({x.a("ni")}/{x.a("sh_dil")},"")',
            note="NI attributable / weighted diluted shares (H2: FY shares)."))
    add(Row("eps_rep", "  Memo: EPS – diluted as reported (€)", style="memo", fmt=FMT_EPS, src="is.eps_diluted",
            agg="none"))
    add(Row("dps", "  Ordinary dividend per share in respect of the year (€)", fmt=FMT_EPS, src="memo.dps", agg="none",
            halves=False, fc=lambda x: f"={x.a('payout')}*{x.a('b2_eps')}",
            note="Forecast: payout lever × recurring diluted EPS. Paid the following year (balance after the AGM; "
                 "interim dividends paid in some years)."))
    add(Row("dps_exc", "  Exceptional dividend per share (€; year declared / paid as noted)", fmt=FMT_EPS,
            src="memo.dps_exceptional", agg="none",
            comment="€5.00 (FY2011, FY2014 paid 2015, FY2017 paid 2018); €10.00 paid 2024 and 2025."))
    add(Row("payout", "  Payout — ordinary DPS / recurring diluted EPS", style="pct", fmt=FMT_PCT, halves=False,
            hist=lambda x: f'=IFERROR({x.a("dps")}/{x.a("b2_eps")},"")', fc=scn(S_PAYOUT)))
    blank()

    # =====================================================================================
    # Bridge 1: NI → OI → ROI → EBITDA
    add(Row("sec_b1", "RECONCILIATION: NET INCOME → OPERATING INCOME → RECURRING OPERATING INCOME → EBITDA",
            style="section",
            note="ROI is Hermès' APM (operating income excl. non-recurring items); EBITDA is a model measure (Hermès "
                 "does not publish EBITDA)"))
    add(Row("b1_ni", "Net income attributable to owners of the parent (IFRS)", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni")}),{x.a("ni")},"")', fc=lambda x: f"={x.a('ni')}"))
    for k, lab, src in [("b1_nci", "  (+) Non-controlling interests", "nci"),
                        ("b1_assoc", "  (−) Net income from associates", "assoc"),
                        ("b1_tax", "  (+) Income tax", "tax"),
                        ("b1_fin", "  (−) Net financial income", "fin_inc")]:
        add(Row(k, lab, hist=lambda x, s=src: f'=IF(ISNUMBER({x.a(s)}),-{x.a(s)},"")', fc=lambda x, s=src: f"=-{x.a(s)}"))
    add(Row("b1_oi", "  = Operating income", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b1_tax")}),SUM({x.a("b1_ni")}:{x.a("b1_fin")}),"")',
            fc=lambda x: f"=SUM({x.a('b1_ni')}:{x.a('b1_fin')})"))
    add(Row("b1_oichk", "  Check: vs income-statement operating income (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b1_oi")}),ROUND({x.a("b1_oi")}-{x.a("op_inc")},1),"")',
            fc=lambda x: f"=ROUND({x.a('b1_oi')}-{x.a('op_inc')},1)"))
    add(Row("b1_nonrec", "  (−) Other non-recurring income and expenses",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b1_oi")}),-N({x.a("nonrec")}),"")', fc=lambda x: f"=-{x.a('nonrec')}"))
    add(Row("b1_roi", "  = Recurring operating income (model bridge)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b1_oi")}),{x.a("b1_oi")}+{x.a("b1_nonrec")},"")',
            fc=lambda x: f"={x.a('b1_oi')}+{x.a('b1_nonrec')}"))
    add(Row("b1_roi_m", "  Recurring operating margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("b1_roi", "revenue"), fc=ratio("b1_roi", "revenue")))
    add(Row("b1_roi_pub", "  Company-published recurring operating income", style="memo", src="is.roi"))
    add(Row("b1_chk", "  Check: model bridge vs company-published (should be 0; ±1–3 whole-€m rounding of printed lines)",
            style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("b1_roi")}),ISNUMBER({x.a("b1_roi_pub")})),'
                            f'ROUND({x.a("b1_roi")}-{x.a("b1_roi_pub")},0),"n/p")')))
    add(Row("b1_dafix", "  (+) Depreciation, amortisation & impairment of PP&E and intangibles",
            hist=lambda x: f'=IF(ISNUMBER({x.a("da_fixed")}),{x.a("da_fixed")},"")', fc=lambda x: f"={x.a('da_fixed')}"))
    add(Row("b1_darou", "  (+) Depreciation of right-of-use assets (IFRS 16, from 2019)",
            hist=lambda x: f'=IF(ISNUMBER({x.a("da_fixed")}),N({x.a("da_rou")}),"")', fc=lambda x: f"={x.a('da_rou')}"))
    add(Row("ebitda", "  = EBITDA (recurring; IFRS 16 basis from 2019)", style="total", cagr="cagr",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("b1_roi")}),ISNUMBER({x.a("b1_dafix")})),'
                            f'{x.a("b1_roi")}+{x.a("b1_dafix")}+{x.a("b1_darou")},"")'),
            fc=lambda x: f"={x.a('b1_roi')}+{x.a('b1_dafix')}+{x.a('b1_darou')}",
            note="Model measure: recurring operating income + all depreciation, amortisation & impairment (cash-flow "
                 "statement)."))
    add(Row("ebitda_m", "  EBITDA margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("ebitda", "revenue"),
            fc=ratio("ebitda", "revenue")))
    add(Row("b1_lease", "  (−) Repayment of lease liabilities (principal; CF statement)",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ebitda")}),N({x.a("cf_lease")}),"")', fc=lambda x: f"={x.a('cf_lease')}"))
    add(Row("b1_lint", "  (−) Interest on lease liabilities",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ebitda")}),-N({x.a("lease_int")}),"")',
            fc=lambda x: f"=-{x.a('lease_int')}"))
    add(Row("ebitda_pre", "  = EBITDA after lease payments (pre-IFRS 16 comparable)", style="total", cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("ebitda")}),{x.a("ebitda")}+{x.a("b1_lease")}+{x.a("b1_lint")},"")'),
            fc=lambda x: f"={x.a('ebitda')}+{x.a('b1_lease')}+{x.a('b1_lint')}",
            note="Fixed lease payments (principal + interest) deducted — comparable with 2018 and earlier."))
    add(Row("ebitda_pre_m", "  EBITDA after lease payments margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("ebitda_pre", "revenue"), fc=ratio("ebitda_pre", "revenue")))
    add(Row("b1_def", "  Definition basis (lease accounting / APM in force)", style="deftext", texts=DEF_B1))
    add(Row("b1_ebit_hdr", "To adjusted EBIT:", style="memo"))
    add(Row("ebit", "  = Adjusted EBIT = recurring operating income (EBITDA − all D&A)", style="sub", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ebitda")}),{x.a("ebitda")}-{x.a("b1_dafix")}-{x.a("b1_darou")},"")',
            fc=lambda x: f"={x.a('ebitda')}-{x.a('b1_dafix')}-{x.a('b1_darou')}"))
    add(Row("ebit_m", "  Adjusted EBIT margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("ebit", "revenue"),
            fc=ratio("ebit", "revenue")))
    blank()

    # =====================================================================================
    # Bridge 2: NI → recurring NI → recurring EPS
    add(Row("sec_b2", "RECONCILIATION: NET INCOME ATTRIBUTABLE → RECURRING NET INCOME / RECURRING EPS",
            style="section",
            note="RECURRING NET INCOME — excludes non-recurring items (after tax) and French exceptional tax "
                 "contributions; checked against Hermès' 'net income excluding the exceptional contribution'"))
    add(Row("b2_ni", "Net income attributable to owners of the parent (IFRS)", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni")}),{x.a("ni")},"")', fc=lambda x: f"={x.a('ni')}"))
    add(Row("b2_nonrec", "  (−) Other non-recurring income and expenses (pre-tax)",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni")}),-N({x.a("nonrec")}),"")', fc=lambda x: f"=-{x.a('nonrec')}"))

    def nonrec_tax(x):
        if have(x, "n.nonrec_tax"):
            return None
        return f'=IF(AND(ISNUMBER({x.a("ni")}),ISNUMBER({x.a("etr")})),N({x.a("nonrec")})*{x.a("etr")},"")'
    add(Row("b2_nrtax", "  (+) Income tax on non-recurring items", src="n.nonrec_tax", hist=nonrec_tax, he=0, e=0,
            note="2018 and 2020 gains not taxed (URD tax commentary); 2006–07: period ETR applied (items not "
                 "described)."))
    add(Row("b2_excep", "  (+) French exceptional contribution / surtaxes (income tax)",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni")}),N({x.a("excep")}),"")', fc=lambda x: f"={x.a('excep')}"))
    add(Row("b2_rni", "  = Recurring net income attributable (model bridge)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b2_ni")}),SUM({x.a("b2_ni")}:{x.a("b2_excep")}),"")',
            fc=lambda x: f"=SUM({x.a('b2_ni')}:{x.a('b2_excep')})"))
    add(Row("b2_pub", "  Company-published net income excl. the exceptional contribution (€0.1bn / €0.01bn precision)",
            style="memo", src="memo.ni_excl_excep", agg="none"))
    add(Row("b2_chk", "  Check: model bridge vs company-published (should be 0; 0 = within the published rounding)",
            style="check",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("b2_pub")}),IF(ABS({x.a("b2_rni")}-{x.a("b2_pub")})<=50,0,'
                            f'ROUND({x.a("b2_rni")}-{x.a("b2_pub")},0)),"n/p")')))
    add(Row("b2_sh", "  Weighted-average diluted shares (m)", fmt=FMT_SHR,
            hist=lambda x: f'=IF(ISNUMBER({x.a("sh_dil")}),{x.a("sh_dil")},"")', fc=lambda x: f"={x.a('sh_dil')}"))
    add(Row("b2_eps", "Recurring EPS – diluted (€) (model)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("b2_rni")}/{x.a("b2_sh")},"")',
            fc=lambda x: f'=IFERROR({x.a("b2_rni")}/{x.a("b2_sh")},"")'))
    add(Row("b2_g", "  Recurring EPS y/y %", style="growth", fmt=FMT_PCT, hist=yoy("b2_eps"), fc=yoy("b2_eps")))
    add(Row("b2_def", "  Definition basis (items excluded)", style="deftext", texts=DEF_B2))
    blank()

    # =====================================================================================
    add(Row("sec_gm", "GROWTH & MARGINS", style="section", note="GROWTH & MARGINS (consolidated) — forecast outputs"))
    add(Row("gr_rev", "  Revenue y/y % (reported)", style="growth", fmt=FMT_PCT, hist=yoy("revenue"),
            fc=yoy("revenue")))
    add(Row("gr_cc", "  Revenue y/y % at constant exchange rates", style="growth", fmt=FMT_PCT,
            hist=lambda x: f'=IF(ISNUMBER({x.a("cc_grp")}),{x.a("cc_grp")},"")', fc=lambda x: f"={x.a('cc_grp')}"))
    add(Row("gr_roi", "  Recurring operating income y/y %", style="growth", fmt=FMT_PCT, hist=yoy("roi"), fc=yoy("roi")))
    add(Row("gr_ebitda", "  EBITDA y/y %", style="growth", fmt=FMT_PCT, hist=yoy("ebitda"), fc=yoy("ebitda")))
    add(Row("gr_ni", "  Net income attributable y/y %", style="growth", fmt=FMT_PCT, hist=yoy("ni"), fc=yoy("ni")))
    add(Row("gr_eps", "  Recurring EPS y/y %", style="growth", fmt=FMT_PCT, hist=yoy("b2_eps"), fc=yoy("b2_eps")))
    add(Row("mg_gross", "  Gross margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("gross", "revenue"),
            fc=ratio("gross", "revenue")))
    add(Row("mg_roi", "  Recurring operating margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("roi", "revenue"),
            fc=ratio("roi", "revenue")))
    add(Row("mg_ebitda", "  EBITDA margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("ebitda", "revenue"),
            fc=ratio("ebitda", "revenue")))
    add(Row("mg_oi", "  Operating margin (IFRS) %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("op_inc", "revenue"), fc=ratio("op_inc", "revenue")))
    add(Row("mg_ni", "  Net margin %", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("ni", "revenue"),
            fc=ratio("ni", "revenue")))
    add(Row("mg_inc", "  Incremental recurring operating margin (ΔROI / ΔRevenue)", style="pct", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR(({x.a("roi")}-{x.py("roi")})/({x.a("revenue")}-{x.py("revenue")}),"")'
                            if x.py("roi") else None),
            fc=lambda x: f'=IFERROR(({x.a("roi")}-{x.py("roi")})/({x.a("revenue")}-{x.py("revenue")}),"")'))
    blank()

    cf_rows(R, A, have)
    bs_rows(R, A, have)
    return R


def cf_rows(R, A, have):
    add = R.append

    def cf(key, label, src, fc=None, e26=None, e=None, style="line", note="", **kw):
        add(Row(key, label, src=src, style=style, annual_fc=True, fc=fc, e26=e26, e=e, note=note, **kw))

    add(Row("sec_cf", "CONSOLIDATED STATEMENT OF CASH FLOWS", style="section",
            note="CASH FLOW — forecast built annually from the 31-Dec-25 balance sheet; H2/26E = 2026E − H1/26"))
    cf("cf_ni", "Net income attributable to owners of the parent", "cf.ni_start", fc=lambda x: f"={x.a('ni')}",
       comment="Source: consolidated statement of cash flows (URDs; half-year reports). Hermès' cash = net cash "
               "position (cash and cash equivalents less bank overdrafts).")
    cf("cf_da", "  Depreciation, amortisation & impairment (incl. right-of-use)", "n.da_total",
       fc=lambda x: f"={x.a('da_tot')}")
    cf("cf_sbc", "  Share-based payments (free-share plans)", "memo.sbc_cf", fc=lambda x: f"={x.a('sbc')}")
    cf("cf_oth", "  Other non-cash items (NCI, associates, provisions, deferred tax, FX; derived)", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("cf_opcf")}),{x.a("cf_opcf")}-{x.a("cf_ni")}-N({x.a("cf_da")})'
                       f'-N({x.a("cf_sbc")}),"")'),
       fc=lambda x: f"=-{x.a('assoc')}-{x.a('nci')}",
       note="Forecast: removes associates' income and adds back non-controlling interests.")
    cf("cf_opcf", "Operating cash flows (before working capital)", "cf.op_cash_flows", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_ni')}:{x.a('cf_oth')})")
    cf("cf_wc", "  Change in working capital requirements", "cf.d_wc",
       fc=lambda x: (f"=-({x.a('bs_inv')}-{x.pp('bs_inv')})-({x.a('bs_ar')}-{x.pp('bs_ar')})"
                     f"+({x.a('bs_ap')}-{x.pp('bs_ap')})+({x.a('bs_taxl')}-{x.pp('bs_taxl')})"),
       note="Linked to the balance sheet: −Δ inventories − Δ receivables + Δ payables + Δ current tax liabilities.")
    cf("cf_lay", "  Interest & tax paid / layout differences (2014–18 statements; derived)", None,
       hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("cf_cfo")}),ISNUMBER({x.a("cf_opcf")})),'
                       f'{x.a("cf_cfo")}-{x.a("cf_opcf")}-N({x.a("cf_wc")}),"")'), fc=0)
    cf("cf_cfo", "Cash flows related to operating activities", "cf.cfo", style="sub", cagr="cagr",
       fc=lambda x: f"={x.a('cf_opcf')}+{x.a('cf_wc')}+{x.a('cf_lay')}")
    cf("cf_capex", "Operating investments (PP&E and intangibles)", "n.capex",
       e26=lambda x: f"=-{x.base(S_CAPEX26)}", e=lambda x: f"=-{x.a('revenue')}*{x.a('capex_pct')}",
       note="2026E: point estimate (scenario table). 2027E+: revenue × capex % input. Before 2018: purchases of "
            "intangibles + PP&E (= operating investments, key figures).")
    cf("cf_acq", "Acquisitions of consolidated shares (net)", "cf.acq",
       e26=lambda x: f"={x.at('cf_acq', 'H1/26')}", e=0)
    cf("cf_oinv", "Financial investments, dividends received & other investing (derived)", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("cf_cfi")}),{x.a("cf_cfi")}-N({x.a("cf_capex")})-N({x.a("cf_acq")}),"")'),
       e26=lambda x: f"={x.at('cf_oinv', 'H1/26')}", e=lambda x: A["oinv"][x.c.year], input_fc=True,
       note=A["oinv_note"])
    cf("cf_cfi", "Cash flows related to investing activities", "cf.cfi", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_capex')}:{x.a('cf_oinv')})")
    cf("cf_div", "Dividends paid (incl. to non-controlling interests)", "cf.div_paid",
       e26=lambda x: f"={x.at('cf_div', 'H1/26')}+{A['div_h2_26']}-{x.scn(S_XDIV + 1)}",
       e=lambda x: (f"=-{x.pp('dps')}*{x.pp('sh_out')}-{x.scn(srow(S_XDIV, x.c))}+{x.a('nci_div')}"),
       note="2026E = H1/26 actual + H2 dividends to NCI + exceptional lever. 2027E+: prior-year ordinary DPS × shares "
            "outstanding + exceptional dividend lever + dividends to NCI.")
    cf("cf_lease", "Repayment of lease liabilities (IFRS 16, from 2019)", "cf.lease_repay",
       fc=lambda x: f"=-{x.a('rou_dep')}", note="Forecast: principal repayments ≈ right-of-use depreciation.")
    cf("cf_bb", "Treasury share buybacks net of disposals", "cf.buyback",
       e26=lambda x: f"={x.at('cf_bb', 'H1/26')}-{x.scn(S_BUYB + 1)}", e=lambda x: "=-" + x.scn(srow(S_BUYB, x.c)),
       note="2026E = H1/26 actual + H2/26E lever; 2027E+ scenario lever (Buybacks table →).")
    cf("cf_ofin", "Borrowings, other financing (derived)", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("cf_cff")}),{x.a("cf_cff")}-N({x.a("cf_div")})-N({x.a("cf_lease")})'
                       f'-N({x.a("cf_bb")}),"")'), fc=0)
    cf("cf_cff", "Cash flows related to financing activities", "cf.cff", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_div')}:{x.a('cf_ofin')})")
    cf("cf_fx", "Foreign currency translation & scope effects (derived)", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("cf_chg")}),{x.a("cf_chg")}-{x.a("cf_cfo")}-{x.a("cf_cfi")}'
                       f'-{x.a("cf_cff")},"")'), fc=0)
    cf("cf_chg", "Change in net cash position", "cf.d_cash", style="sub",
       fc=lambda x: f"={x.a('cf_cfo')}+{x.a('cf_cfi')}+{x.a('cf_cff')}+{x.a('cf_fx')}")
    add(Row("cf_beg", "Net cash position — beginning of period", src="cf.cash_begin", agg="none", annual_fc=True,
            hist=lambda x: f"={x.h1('cf_end')}" if x.c.kind == "H2" and have(x, "cf.cash_end") else None,
            he=lambda x: f"={x.h1('cf_end')}", fc=lambda x: f"={x.pp('cf_end')}"))
    add(Row("cf_end", "Net cash position — end of period", src="cf.cash_end", style="sub", agg="last", annual_fc=True,
            fc=lambda x: f"={x.a('cf_beg')}+{x.a('cf_chg')}"))
    add(Row("cf_chk", "  Check: beginning + change = ending net cash (should be 0; ±1 from whole-€m statements)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("cf_beg")}),ISNUMBER({x.a("cf_end")})),ROUND({x.a("cf_beg")}'
                            f'+{x.a("cf_chg")}-{x.a("cf_end")},1),"")'),
            fc=lambda x: f"=ROUND({x.a('cf_beg')}+{x.a('cf_chg')}-{x.a('cf_end')},1)"))
    add(Row("cf_cashchk", "  Check: BS cash − bank overdrafts vs cash-flow net cash (should be 0)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("bs_cash")}),ISNUMBER({x.a("cf_end")})),ROUND({x.a("bs_cash")}'
                            f'-N({x.a("b4_od")})-{x.a("cf_end")},0),"")'),
            fc=lambda x: f"=ROUND({x.a('bs_cash')}-{x.a('b4_od')}-{x.a('cf_end')},0)"))
    add(Row(None, style="blank"))

    # Bridge 3: CFO → adjusted FCF
    add(Row("sec_b3", "RECONCILIATION: OPERATING CASH FLOWS → ADJUSTED FREE CASH FLOW (Hermès APM)", style="section",
            note="ADJUSTED FCF = cash flows from operating activities − operating investments − lease repayments"))
    add(Row("b3_opcf", "Operating cash flows (before working capital)", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("cf_opcf")}),{x.a("cf_opcf")},"")', fc=lambda x: f"={x.a('cf_opcf')}"))
    add(Row("b3_wc", "  (+) Change in working capital requirements (incl. layout differences)",
            hist=lambda x: f'=IF(ISNUMBER({x.a("cf_cfo")}),N({x.a("cf_wc")})+N({x.a("cf_lay")}),"")',
            fc=lambda x: f"={x.a('cf_wc')}+{x.a('cf_lay')}"))
    add(Row("b3_capex", "  (−) Operating investments",
            hist=lambda x: f'=IF(ISNUMBER({x.a("cf_cfo")}),N({x.a("cf_capex")}),"")', fc=lambda x: f"={x.a('cf_capex')}"))
    add(Row("b3_lease", "  (−) Repayment of lease liabilities (from 2019)",
            hist=lambda x: f'=IF(ISNUMBER({x.a("cf_cfo")}),N({x.a("cf_lease")}),"")', fc=lambda x: f"={x.a('cf_lease')}"))
    add(Row("afcf", "  = Adjusted free cash flow (model bridge)", style="total", cagr="cagr",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("cf_cfo")}),ISNUMBER({x.a("cf_capex")})),'
                            f'SUM({x.a("b3_opcf")}:{x.a("b3_lease")}),"")'),
            fc=lambda x: f"=SUM({x.a('b3_opcf')}:{x.a('b3_lease')})"))
    add(Row("afcf_pub", "  Company-published adjusted free cash flow (free cash flow in 2018)", style="memo",
            src="apm.adj_fcf"))
    add(Row("afcf_chk", "  Check: model bridge vs company-published (should be 0; ±1 rounding)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("afcf")}),ISNUMBER({x.a("afcf_pub")})),'
                            f'ROUND({x.a("afcf")}-{x.a("afcf_pub")},0),"n/p")')))
    add(Row("b3_def", "  Definition basis (company APM in force)", style="deftext", texts=DEF_B3))
    add(Row("afcf_g", "  Adjusted FCF y/y %", style="growth", fmt=FMT_PCT, hist=yoy("afcf"), fc=yoy("afcf")))
    add(Row("afcf_m", "  Adjusted FCF % of revenue", style="pct", fmt=FMT_PCT, cagr="avg", hist=ratio("afcf", "revenue"),
            fc=ratio("afcf", "revenue")))
    add(Row("afcf_conv", "  Adjusted FCF / recurring net income conversion %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("afcf", "b2_rni"), fc=ratio("afcf", "b2_rni")))
    add(Row("afcf_ps", "  Adjusted FCF per diluted share (€)", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("afcf")}/{x.a("sh_dil")},"")',
            fc=lambda x: f'=IFERROR({x.a("afcf")}/{x.a("sh_dil")},"")'))
    add(Row("cx_hdr", "Capex ratios", style="line"))
    add(Row("capex_pct", "  Operating investments % of revenue", style="pct", fmt=FMT_PCT, cagr="avg", input_fc=True,
            hist=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("revenue")},"")',
            he=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("revenue")},"")',
            e26=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("revenue")},"")',
            e=lambda x: A["capex_pct"][x.c.year], note=A["capex_note"]))
    add(Row("capex_da", "  Operating investments / D&A of PP&E and intangibles (x)", style="pct", fmt=FMT_X,
            hist=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("da_fixed")},"")',
            fc=lambda x: f'=IFERROR(-{x.a("cf_capex")}/{x.a("da_fixed")},"")'))
    add(Row(None, style="blank"))

    add(Row("sec_bb", "SHARE BUYBACK SCHEDULE", style="section",
            note="Hermès buys back shares mainly to serve employee free-share plans (shares delivered from treasury)"))
    ann = dict(halves=False)
    add(Row("bb_px", "  Avg buyback price (€)", fmt=FMT_EPS, e26=lambda x: f"={x.a('px')}",
            e=lambda x: f"={x.pp('bb_px')}*(1+{x.a('px_g')})", **ann))
    add(Row("bb_cash", "  Buyback cash deployed (€m)", e26=lambda x: f"=-({x.a('cf_bb')}-{x.at('cf_bb', 'H1/26')})",
            e=lambda x: f"=-{x.a('cf_bb')}", note="2026E row = H2/26E buyback only (H1/26 in the 30-Jun share count).",
            **ann))
    add(Row("bb_shares", "  Implied shares repurchased (m)", fmt=FMT_SHR,
            fc=lambda x: f'=IFERROR({x.a("bb_cash")}/{x.a("bb_px")},0)', **ann))
    add(Row("bb_issued", "  Shares delivered under free-share plans (m)", fmt=FMT_SHR,
            fc=lambda x: A["bb_issued"][x.c.year], input_fc=True, **ann))
    add(Row("bb_beg", "  Beginning shares outstanding (m)", fmt=FMT_SHR,
            e26=lambda x: f"={x.at('sh_out', 'H1/26')}", e=lambda x: f"={x.pp('bb_end')}", **ann))
    add(Row("bb_end", "  Ending shares outstanding (m)", fmt=FMT_SHR,
            fc=lambda x: f"={x.a('bb_beg')}-{x.a('bb_shares')}+{x.a('bb_issued')}", **ann))
    add(Row("bb_pct", "  % of shares repurchased", style="pct", fmt=FMT_PCT,
            fc=lambda x: f'=IFERROR({x.a("bb_shares")}/{x.a("bb_beg")},"")', **ann))
    add(Row("bb_cum", "  Memo: cumulative shares repurchased since H2/26 (m)", style="memo", fmt=FMT_SHR,
            e26=lambda x: f"={x.a('bb_shares')}", e=lambda x: f"={x.pp('bb_cum')}+{x.a('bb_shares')}", **ann))
    add(Row(None, style="blank"))


def bs_rows(R, A, have):
    add = R.append

    def bs(key, label, src, fc=None, e26=None, e=None, style="line", note="", **kw):
        add(Row(key, label, src=src, style=style, agg="last", annual_fc=True, fc=fc, e26=e26, e=e, note=note, **kw))

    flat = lambda k: (lambda x: f"={x.pp(k)}")  # noqa: E731
    add(Row("sec_bs", "CONSOLIDATED BALANCE SHEET", style="section",
            note="BS FORECAST — first-principles roll-forward (2026E from the 31-Dec-25 balance sheet; H1/26 as reported)"))
    add(Row("bs_a", "ASSETS", style="line"))
    bs("bs_gw", "  Goodwill", "bs.goodwill", fc=flat("bs_gw"),
       comment="Source: consolidated balance sheet — URDs (31-Dec) and half-year reports (30-Jun).")
    bs("bs_int", "  Intangible assets", "bs.intangibles", fc=flat("bs_int"))
    bs("bs_rou", "  Right-of-use assets (IFRS 16, from 2019)", "bs.rou",
       fc=lambda x: f"={x.pp('bs_rou')}+{x.a('ls_new')}-{x.a('rou_dep')}",
       note="Prior + new leases − right-of-use depreciation.")
    bs("bs_ppe", "  Property, plant and equipment", "bs.ppe",
       fc=lambda x: f"={x.pp('bs_ppe')}-{x.a('cf_capex')}-{x.a('da_fixed')}",
       note="Prior + operating investments − D&A of PP&E and intangibles (intangible additions included here).")
    bs("bs_fin", "  Financial assets, loans & deposits, investment property & other non-current assets", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("bs_tnca")}),{x.a("bs_tnca")}-{x.a("bs_gw")}-{x.a("bs_int")}'
                       f'-N({x.a("bs_rou")})-{x.a("bs_ppe")}-{x.a("bs_assoc")}-{x.a("bs_dta")},"")'),
       fc=lambda x: f"={x.pp('bs_fin')}-{x.a('cf_oinv')}-{x.a('cf_acq')}",
       note="Derived (total non-current assets − lines shown). Forecast: + financial investments / acquisitions.")
    bs("bs_assoc", "  Investments in associates", "bs.assoc", fc=lambda x: f"={x.pp('bs_assoc')}+{x.a('assoc')}")
    bs("bs_dta", "  Deferred tax assets", "bs.dta", fc=flat("bs_dta"))
    bs("bs_tnca", "Non-current assets", "bs.total_nca", style="sub",
       fc=lambda x: f"=SUM({x.a('bs_gw')}:{x.a('bs_dta')})")
    bs("bs_inv", "  Inventories and work-in-progress", "bs.inventories",
       fc=lambda x: f"=-{x.a('cogs')}*{x.a('d_inv')}/365", note="−Cost of sales × inventory days / 365.")
    bs("bs_ar", "  Trade and other receivables", "bs.receivables",
       fc=lambda x: f"={x.a('revenue')}*{x.a('d_ar')}/365")
    bs("bs_oca", "  Other current assets (current tax, derivatives, other; derived)", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("bs_tca")}),{x.a("bs_tca")}-{x.a("bs_inv")}-{x.a("bs_ar")}'
                       f'-{x.a("bs_cash")},"")'), fc=flat("bs_oca"))
    bs("bs_cash", "  Cash and cash equivalents", "bs.cash", fc=lambda x: f"={x.a('cf_end')}+{x.a('b4_od')}")
    bs("bs_tca", "Current assets", "bs.total_ca", style="sub", fc=lambda x: f"=SUM({x.a('bs_inv')}:{x.a('bs_cash')})")
    bs("bs_ta", "TOTAL ASSETS", None, style="total",
       hist=lambda x: f'=IF(ISNUMBER({x.a("bs_tnca")}),{x.a("bs_tnca")}+{x.a("bs_tca")},"")',
       fc=lambda x: f"={x.a('bs_tnca')}+{x.a('bs_tca')}")
    add(Row("bs_l", "EQUITY AND LIABILITIES", style="line"))
    bs("bs_sc", "  Share capital & share premium", "n.sc_sp", fc=flat("bs_sc"))
    bs("bs_ts", "  Treasury shares", "bs.treasury_eq", fc=lambda x: f"={x.pp('bs_ts')}+{x.a('cf_bb')}")
    bs("bs_res", "  Reserves, translation & revaluation adjustments and net income (derived)", "n.reserves",
       fc=lambda x: f"={x.pp('bs_res')}+{x.a('ni')}+{x.a('sbc')}+({x.a('cf_div')}-{x.a('nci_div')})",
       note="Prior + NI attributable + share-based payments − dividends to owners of the parent.")
    bs("bs_eqp", "Equity attributable to owners of the parent", "bs.equity_parent", style="sub",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("bs_sc")}),{x.a("bs_sc")}+{x.a("bs_ts")}+{x.a("bs_res")},"")'
                       if have(x, "n.sc_sp") else None),
       fc=lambda x: f"={x.a('bs_sc')}+{x.a('bs_ts')}+{x.a('bs_res')}")
    bs("bs_nci", "  Non-controlling interests", "bs.nci_eq",
       fc=lambda x: f"={x.pp('bs_nci')}-{x.a('nci')}+{x.a('nci_div')}")
    bs("bs_teq", "Equity", "bs.total_equity", style="sub",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("bs_nci")}),{x.a("bs_eqp")}+{x.a("bs_nci")},"")'
                       if have(x, "bs.nci_eq") else None),
       fc=lambda x: f"={x.a('bs_eqp')}+{x.a('bs_nci')}")
    bs("bs_debt", "  Borrowings and financial liabilities (incl. NCI put options; current + non-current)",
       "n.borrowings", fc=flat("bs_debt"))
    bs("bs_llt", "  Lease liabilities due in more than one year", "n.lease_lt",
       fc=lambda x: f"={x.a('lease_tot')}-{x.a('bs_lst')}")
    bs("bs_lst", "  Lease liabilities due in less than one year", "n.lease_st", fc=flat("bs_lst"))
    bs("bs_prov", "  Provisions & employee benefit obligations (current + non-current)", "n.prov", fc=flat("bs_prov"))
    bs("bs_dtl", "  Deferred tax liabilities", "bs.dtl", fc=flat("bs_dtl"))
    bs("bs_ap", "  Trade and other payables", "bs.payables", fc=lambda x: f"=-{x.a('cogs')}*{x.a('d_ap')}/365")
    bs("bs_taxl", "  Current tax liabilities", "bs.cur_tax_liab", fc=lambda x: f"=-{x.a('tax')}*{x.a('taxl_pct')}")
    bs("bs_ol", "  Other liabilities (other current & non-current, derivatives; derived from total assets)", None,
       hist=lambda x: (f'=IF(ISNUMBER({x.a("bs_ta")}),{x.a("bs_ta")}-{x.a("bs_teq")}-{x.a("bs_debt")}'
                       f'-{x.a("bs_llt")}-{x.a("bs_lst")}-{x.a("bs_prov")}-{x.a("bs_dtl")}-{x.a("bs_ap")}'
                       f'-{x.a("bs_taxl")},"")'), fc=flat("bs_ol"))
    bs("bs_tl", "Total liabilities", None, style="sub",
       hist=lambda x: f'=IF(ISNUMBER({x.a("bs_debt")}),SUM({x.a("bs_debt")}:{x.a("bs_ol")}),"")',
       fc=lambda x: f"=SUM({x.a('bs_debt')}:{x.a('bs_ol')})")
    bs("bs_tle", "TOTAL EQUITY AND LIABILITIES", "bs.total_le", style="total",
       fc=lambda x: f"={x.a('bs_teq')}+{x.a('bs_tl')}")
    add(Row("bs_chk", "BS tie-out check (TA − TE&L as reported; ±1 whole-€m rounding)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("bs_ta")}),ROUND({x.a("bs_ta")}-{x.a("bs_tle")},0),"")',
            fc=lambda x: f"=ROUND({x.a('bs_ta')}-{x.a('bs_tle')},1)"))
    add(Row("bs_rep_chk", "  Check: model total assets vs reported (should be 0; ±1 whole-€m rounding)",
            style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ta_rep")}),ROUND({x.a("bs_ta")}-{x.a("ta_rep")},0),"")'))
    add(Row("ta_rep", "  Memo: total assets as reported", style="memo", src="bs.total_assets", agg="last"))
    add(Row("eqp_chk", "  Check: equity attributable vs reported (should be 0)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("bs_eqp")}),ISNUMBER({x.a("eqp_rep")})),'
                            f'ROUND({x.a("bs_eqp")}-{x.a("eqp_rep")},0),"")')))
    add(Row("eqp_rep", "  Memo: equity attributable to owners of the parent as reported", style="memo",
            src="bs.equity_parent", agg="last"))
    add(Row("sh_out", "  Memo: shares outstanding at period end (issued − treasury, m)", style="memo", fmt=FMT_SHR,
            src="n.shares_out", agg="last", annual_fc=True, fc=lambda x: f"={x.a('bb_end')}"))
    add(Row(None, style="blank"))

    # Bridge 4: cash → net cash → restated net cash
    add(Row("sec_b4", "RECONCILIATION: CASH → NET CASH POSITION → RESTATED NET CASH POSITION (Hermès APM)",
            style="section", note="NET CASH — Hermès excludes lease liabilities (IFRS 16) from net cash"))
    add(Row("b4_cash", "Cash and cash equivalents (balance sheet)", style="sub",
            hist=lambda x: f'=IF(ISNUMBER({x.a("bs_cash")}),{x.a("bs_cash")},"")', annual_fc=True, agg="last",
            fc=lambda x: f"={x.a('bs_cash')}"))
    add(Row("b4_od", "  (−) Bank overdrafts (derived = BS cash − CF net cash where not printed separately)",
            src="apm.bank_overdrafts", agg="last", annual_fc=True, fc=0,
            hist=lambda x: (None if have(x, "apm.bank_overdrafts") else
                            f'=IF(AND(ISNUMBER({x.a("bs_cash")}),ISNUMBER({x.a("cf_end")})),{x.a("bs_cash")}'
                            f'-{x.a("cf_end")},"")'),
            note="Bank overdrafts sit in short-term borrowings (net-cash reconciliation note); derived as balance-sheet "
                 "cash − cash-flow net cash position only where not printed."))
    add(Row("b4_nc", "  = Net cash position (model)", style="sub", agg="last", annual_fc=True,
            hist=lambda x: f'=IF(ISNUMBER({x.a("b4_cash")}),{x.a("b4_cash")}-N({x.a("b4_od")}),"")',
            fc=lambda x: f"={x.a('b4_cash')}-{x.a('b4_od')}"))
    add(Row("b4_nc_pub", "  Company-published net cash position", style="memo", src="apm.net_cash", agg="last"))
    add(Row("b4_nc_chk", "  Check: model vs company-published (should be 0)", style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("b4_nc")}),ISNUMBER({x.a("b4_nc_pub")})),'
                            f'ROUND({x.a("b4_nc")}-{x.a("b4_nc_pub")},0),"n/p")')))
    add(Row("b4_inv", "  (+) Cash investments with maturity > 3 months (from 2017)", src="apm.cash_inv_gt3m",
            agg="last", annual_fc=True, fc=lambda x: f"={x.pp('b4_inv')}"))
    add(Row("b4_fl", "  (−) Financial liabilities (from 2020)", src="apm.fin_liab_restated", agg="last",
            annual_fc=True, fc=lambda x: f"={x.pp('b4_fl')}"))
    add(Row("b4_rnc", "  = Restated net cash position (model)", style="total", agg="last", annual_fc=True,
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("b4_nc")}),ISNUMBER({x.a("b4_inv")})),'
                            f'{x.a("b4_nc")}+{x.a("b4_inv")}+N({x.a("b4_fl")}),"")'),
            fc=lambda x: f"={x.a('b4_nc')}+{x.a('b4_inv')}+{x.a('b4_fl')}"))
    add(Row("b4_pub", "  Company-published restated net cash position", style="memo", src="apm.restated_net_cash",
            agg="last"))
    add(Row("b4_chk", "  Check: model bridge vs company-published (should be 0; n/p = reconciliation not published)",
            style="check",
            hist=lambda x: (f'=IF(AND(ISNUMBER({x.a("b4_rnc")}),ISNUMBER({x.a("b4_pub")})),'
                            f'ROUND({x.a("b4_rnc")}-{x.a("b4_pub")},0),"n/p")')))
    add(Row("b4_def", "  Definition basis (company APM in force)", style="deftext", texts=DEF_B4))
    add(Row("rnc", "Restated net cash (model bridge where reconcilable, else as published)", style="sub", agg="last",
            annual_fc=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("b4_rnc")}),{x.a("b4_rnc")},IF(ISNUMBER({x.a("b4_pub")}),'
                            f'{x.a("b4_pub")},""))'),
            fc=lambda x: f"={x.a('b4_rnc')}"))
    add(Row("lease_tot", "  Lease liabilities (current + non-current)", agg="last", annual_fc=True,
            hist=lambda x: f'=IF(ISNUMBER({x.a("bs_llt")}),{x.a("bs_llt")}+{x.a("bs_lst")},"")',
            fc=lambda x: f"={x.pp('lease_tot')}+{x.a('ls_new')}+{x.a('cf_lease')}",
            note="Prior + new leases − principal repayments."))
    add(Row("rnc_l", "  Restated net cash after lease liabilities", style="sub", agg="last", annual_fc=True,
            hist=lambda x: f'=IF(ISNUMBER({x.a("rnc")}),{x.a("rnc")}-N({x.a("lease_tot")}),"")',
            fc=lambda x: f"={x.a('rnc')}-{x.a('lease_tot')}"))
    add(Row(None, style="blank"))

    # ---------------- Working capital ----------------
    add(Row("sec_wc", "WORKING CAPITAL & CASH CONVERSION", style="section",
            note="WORKING CAPITAL — forecast drivers (blue = input); half-year flows annualised"))

    def wc(key, label, hist, val, fmt=FMT_DAYS, note=""):
        add(Row(key, label, style="pct", fmt=fmt, input_fc=True, hist=hist, he=hist,
                e26=lambda x, v=val: v[2026], e=lambda x, v=val: v[x.c.year], note=note))
    wc("d_inv", "  Inventory days — inventories / cost of sales × 365",
       lambda x: f'=IFERROR({x.a("bs_inv")}/(-{x.a("cogs")}*{x.half_mult})*365,"")', A["d_inv"],
       note="2025: 203 days; H1/26 annualised 209 days.")
    wc("d_ar", "  DSO — receivables / revenue × 365",
       lambda x: f'=IFERROR({x.a("bs_ar")}/({x.a("revenue")}*{x.half_mult})*365,"")', A["d_ar"])
    wc("d_ap", "  Payable days — payables / cost of sales × 365",
       lambda x: f'=IFERROR({x.a("bs_ap")}/(-{x.a("cogs")}*{x.half_mult})*365,"")', A["d_ap"])
    wc("taxl_pct", "  Current tax liabilities % of income tax expense",
       lambda x: f'=IFERROR({x.a("bs_taxl")}/(-{x.a("tax")}*{x.half_mult}),"")', A["taxl_pct"], fmt=FMT_PCT)
    nwc = lambda x: f"{x.a('bs_inv')}+{x.a('bs_ar')}-{x.a('bs_ap')}"  # noqa: E731
    add(Row("nwc", "  Operating NWC (inventories + receivables − payables)", agg="last",
            hist=lambda x: f'=IF(ISNUMBER({x.a("bs_inv")}),{nwc(x)},"")', fc=lambda x: "=" + nwc(x)))
    add(Row("nwc_pct", "  NWC % of revenue (annualised)", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f'=IFERROR({x.a("nwc")}/({x.a("revenue")}*{x.half_mult}),"")',
            fc=lambda x: f'=IFERROR({x.a("nwc")}/({x.a("revenue")}*{x.half_mult}),"")'))
    add(Row("nwc_d", "  ΔNWC (y/y)", hist=lambda x: (f'=IFERROR({x.a("nwc")}-{x.py("nwc")},"")' if x.py("nwc") else None),
            fc=lambda x: f'=IFERROR({x.a("nwc")}-{x.py("nwc")},"")'))
    add(Row(None, style="blank"))

    # ---------------- Schedules ----------------
    add(Row("sec_sch", "BALANCE SHEET FORECAST SCHEDULES", style="section",
            note="BS FORECAST SCHEDULES — explicit driver assumptions"))
    add(Row("blk_ls", "Leases (IFRS 16)", style="block"))
    sch = dict(style="sched", halves=False, input_fc=True)
    add(Row("ls_pct", "  New leases (right-of-use additions) % of revenue", fmt=FMT_PCT,
            fc=lambda x: A["new_leases"][x.c.year], note=A["lease_note"], **sch))
    add(Row("ls_new", "  New leases (€m)", style="line", halves=False, fc=lambda x: f"={x.a('revenue')}*{x.a('ls_pct')}"))
    add(Row("rou_pct", "  Right-of-use depreciation % of opening right-of-use assets", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR({x.a("da_rou")}/{x.pp("bs_rou")},"")' if x.c.is_annual else None),
            fc=lambda x: A["rou_dep"][x.c.year], **sch))
    add(Row("rou_dep", "  Right-of-use depreciation (€m)", style="line", halves=False,
            fc=lambda x: f"={x.pp('bs_rou')}*{x.a('rou_pct')}"))
    add(Row("lease_rate", "  Interest rate on opening lease liabilities %", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR({x.a("lease_int")}/{x.pp("lease_tot")},"")' if x.c.is_annual else None),
            fc=lambda x: A["lease_rate"][x.c.year], **sch))
    add(Row("blk_cash", "Net cash, financial income & distributions", style="block"))
    add(Row("cash_yield", "  Yield on opening restated net cash % (net financial income + lease interest)", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR(({x.a("fin_inc")}+N({x.a("lease_int")}))/{x.pp("rnc")},"")'
                            if x.c.is_annual else None),
            fc=lambda x: A["cash_yield"][x.c.year], note=A["cash_note"], **sch))
    add(Row("nci_pct", "  Non-controlling interests % of consolidated net income", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR(-{x.a("nci")}/{x.a("cons_ni")},"")' if x.c.is_annual else None),
            fc=lambda x: A["nci_pct"][x.c.year], **sch))
    add(Row("nci_div", "  Dividends paid to non-controlling interests (€m) = NCI share of net income", style="line",
            halves=False, fc=lambda x: f"={x.a('nci')}",
            note="2025: €43m paid vs €36m NCI income; forecast pays out NCI income (NCI equity flat)."))
    add(Row("blk_shr", "Shares & valuation inputs", style="block"))
    add(Row("dil_sec", "  Dilutive free-share awards (m shares)", fmt=FMT_SHR,
            hist=lambda x: f'=IFERROR({x.a("sh_dil")}-{x.a("sh_basic")},"")',
            fc=lambda x: A["dil_sec"][x.c.year], **sch))
    add(Row("px_g", "  Share-price appreciation % (buyback pricing)", fmt=FMT_PCT,
            e=lambda x: A["px_g"][x.c.year], **sch))
    add(Row("blk_href", "Historical reference (driver context)", style="block"))
    add(Row("h_da", "  Total D&A (incl. right-of-use) % of revenue", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("da_tot", "revenue"), fc=ratio("da_tot", "revenue")))
    add(Row("h_lease", "  Lease payments (principal + interest) % of revenue", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f'=IFERROR(-(N({x.a("cf_lease")})-N({x.a("lease_int")}))/{x.a("revenue")},"")',
            fc=lambda x: f'=IFERROR(-({x.a("cf_lease")}-{x.a("lease_int")})/{x.a("revenue")},"")'))
    add(Row(None, style="blank"))

    ratios_rows(R, A)


def ratios_rows(R, A):
    add = R.append
    ann = lambda f: (lambda x: f(x) if x.c.kind in ("A", "Y") else None)  # noqa: E731

    def rr(key, label, f, style="line", fmt=FMT_NUM, cagr=None):
        add(Row(key, label, style=style, fmt=fmt, halves=False, hist=ann(f), fc=f, cagr=cagr))

    add(Row("sec_ratio", "RATIO ANALYSIS", style="section"))
    add(Row("blk_roic", "DuPont decomposition of ROIC", style="block"))
    rr("r_ebit", "Recurring operating income (adjusted EBIT)", lambda x: f"={x.a('roi')}")
    rr("r_tax", "Effective tax rate excl. exceptional contribution (actual)", lambda x: f"={x.a('etr_ex')}", fmt=FMT_PCT)
    rr("r_nopat", "NOPAT  =  Recurring operating income × (1 − tax rate)",
       lambda x: f'=IFERROR({x.a("r_ebit")}*(1-{x.a("r_tax")}),"n/a")')
    rr("r_ic", "Invested capital (IC)  =  Equity + lease liabilities − restated net cash",
       lambda x: f'=IFERROR({x.a("r_eq")}+N({x.a("lease_tot")})-{x.a("rnc")},"n/a")')
    rr("r_eq", "  Total equity incl. NCI", lambda x: f"={x.a('bs_teq')}")
    rr("roic", "ROIC  =  NOPAT / IC", lambda x: f'=IFERROR({x.a("r_nopat")}/{x.a("r_ic")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    rr("r_m", "  Margin  =  ROI / Revenue", lambda x: f'=IFERROR({x.a("r_ebit")}/{x.a("revenue")},"n/a")', fmt=FMT_PCT)
    rr("r_t", "  Capital turnover  =  Revenue / IC", lambda x: f'=IFERROR({x.a("revenue")}/{x.a("r_ic")},"n/a")',
       fmt=FMT_X)
    rr("r_tb", "  Tax burden  =  (1 − tax rate)", lambda x: f'=IFERROR(1-{x.a("r_tax")},"n/a")', fmt=FMT_PCT)
    rr("r_chk", "  Check: Margin × Turnover × Tax burden  =  ROIC",
       lambda x: f'=IFERROR({x.a("r_m")}*{x.a("r_t")}*{x.a("r_tb")},"n/a")', fmt=FMT_PCT)
    add(Row(None, style="blank"))
    add(Row("blk_ronta", "RONTA decomposition", style="block"))
    rr("t_nopat", "NOPAT  =  ROI × (1 − tax rate)", lambda x: f"={x.a('r_nopat')}")
    rr("t_ta", "  Total assets", lambda x: f"={x.a('bs_ta')}")
    rr("t_gw", "  − Goodwill & intangible assets", lambda x: f"=-({x.a('bs_gw')}+{x.a('bs_int')})")
    rr("t_cash", "  − Cash and cash equivalents", lambda x: f"=-{x.a('bs_cash')}")
    rr("t_nibl", "  − Non-interest-bearing liabilities (payables, current tax, other liabilities)",
       lambda x: f"=-(N({x.a('bs_ap')})+N({x.a('bs_taxl')})+N({x.a('bs_ol')}))")
    rr("t_nta", "  = Net tangible operating assets", lambda x: f"=SUM({x.a('t_ta')}:{x.a('t_nibl')})")
    rr("ronta", "RONTA  =  NOPAT / NTA", lambda x: f'=IFERROR({x.a("t_nopat")}/{x.a("t_nta")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    add(Row(None, style="blank"))
    add(Row("blk_roe", "Return on Equity (ROE)", style="block"))
    rr("e_ni2", "Net income attributable to owners of the parent", lambda x: f"={x.a('ni')}")
    rr("e_eq", "Equity attributable to owners of the parent", lambda x: f"={x.a('bs_eqp')}")
    rr("roe", "ROE  =  NI / Equity", lambda x: f'=IFERROR({x.a("e_ni2")}/{x.a("e_eq")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    add(Row(None, style="blank"))
    add(Row("blk_lev", "Leverage (Hermès is net cash: negative = net cash)", style="block"))
    rr("l_nd", "Net debt  =  − restated net cash (excl. lease liabilities)", lambda x: f"=-{x.a('rnc')}")
    rr("l_ndl", "Net debt incl. lease liabilities", lambda x: f"=-{x.a('rnc_l')}")
    rr("l_ebitda", "EBITDA (IFRS 16)", lambda x: f"={x.a('ebitda')}")
    rr("lev", "Net debt / EBITDA (x)", lambda x: f'=IFERROR({x.a("l_nd")}/{x.a("l_ebitda")},"n/a")', style="total",
       fmt=FMT_X)
    rr("lev_l", "Net debt incl. leases / EBITDA (x)", lambda x: f'=IFERROR({x.a("l_ndl")}/{x.a("l_ebitda")},"n/a")',
       fmt=FMT_X)
    add(Row(None, style="blank"))

    from .assumptions import PX, PX_NOTE
    add(Row("sec_val", "VALUATION", style="section",
            note="VALUATION — share price €1,299.50 (Euronext close 2-Oct-2026); applied to 2026E–2030E"))
    add(Row("px", "Share price (€) — current", style="sched", fmt=FMT_EPS, halves=False, input_fc=True,
            e26=PX, e=lambda x: f"={x.pp('px')}", note=PX_NOTE))

    def vr(key, label, f, fmt=FMT_NUM, style="line"):
        add(Row(key, label, style=style, fmt=fmt, halves=False, e26=f, e=f))
    vr("v_sh", "Diluted shares (m)", lambda x: f"={x.a('sh_dil')}", fmt=FMT_SHR)
    vr("v_mcap", "Market capitalisation (€m)", lambda x: f'=IFERROR({x.a("px")}*{x.a("v_sh")},"n/a")')
    vr("v_nd", "Net debt (€m; negative = net cash)", lambda x: f"={x.a('l_nd')}")
    vr("v_nci", "Non-controlling interests (€m)", lambda x: f"={x.a('bs_nci')}")
    vr("v_ev", "Enterprise value (€m)", lambda x: f'=IFERROR({x.a("v_mcap")}+{x.a("v_nd")}+{x.a("v_nci")},"n/a")',
       style="sub")
    add(Row("blk_mult", "Multiples", style="block"))
    for key, lab, f, fmt in [
        ("m_evs", "  EV / Revenue", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("revenue")},"n/a")', FMT_X),
        ("m_evebitda", "  EV / EBITDA", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("ebitda")},"n/a")', FMT_X),
        ("m_evebit", "  EV / Recurring operating income", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("roi")},"n/a")', FMT_X),
        ("m_evic", "  EV / IC", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("r_ic")},"n/a")', FMT_X),
        ("m_pe", "  P / E (IFRS diluted)", lambda x: f'=IFERROR({x.a("px")}/{x.a("eps_dil")},"n/a")', FMT_X),
        ("m_pea", "  P / E (recurring EPS)", lambda x: f'=IFERROR({x.a("px")}/{x.a("b2_eps")},"n/a")', FMT_X),
        ("m_fcfy", "  Adjusted FCF yield", lambda x: f'=IFERROR({x.a("afcf")}/{x.a("v_mcap")},"n/a")', FMT_PCT),
        ("m_dy", "  Dividend yield (ordinary DPS)", lambda x: f'=IFERROR({x.a("dps")}/{x.a("px")},"n/a")', FMT_PCT)]:
        vr(key, lab, f, fmt=fmt)
