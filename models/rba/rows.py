"""Row definitions for the RB Global Model tab.

Layout mirrors the HII model: divisional build → group total → GAAP income statement →
GAAP→adjusted bridges → growth & margins → cash flow → buyback → balance sheet →
working capital → BS schedules → ratios → valuation.

RB Global reports ONE operating segment, so the HII "segment P&L by division" block is
replaced by a revenue-stream build: GTV by sector (Automotive / Heavy Equipment &
Transportation / Other) × service take rate + inventory sales, with adjusted EBITDA as the
group profit KPI (RB Global's primary non-GAAP measure).
"""
from __future__ import annotations

from .framework import (FMT_DAYS, FMT_EPS, FMT_NUM, FMT_NUM1, FMT_PCT, FMT_SHR, FMT_X, Row, ratio, yoy)

# ---------------------------------------------------------------------------------------
# Scenario-table rows (absolute row numbers in the scenario columns, right of the notes)
# ---------------------------------------------------------------------------------------
S_GTV_G, S_EBITDA = 12, 13             # FY26 outlook: high / mid / low
S_TAX, S_CAPEX = 16, 17                # FY26 point estimates
S_AUTO, S_HET, S_OTH, S_MARGIN, S_BUYB = 20, 26, 32, 38, 44


def srow(base, year):
    """Scenario value row for a 2027E–2030E driver (base row holds the Δ)."""
    return base + (year - 2026)


FC_INPUT_CATS = {"SBC", "ACQ", "RESTR", "LEGAL"}   # forecast as explicit inputs; other items nil


def _w(x, c):
    """Sector weight for Q3/Q4-26E allocation: prior-year quarter GTV × 1H/26 vs 1H/25 sector growth."""
    return f"{x.py('gtv_' + c)}*{x.h('gtv_' + c, 2026)}/{x.h('gtv_' + c, 2025)}"


def build_rows(info):
    """info: dict with 'def_notes_ebitda', 'def_notes_ni' (colkey -> text), 'used_cats_e', 'used_cats_n',
    plus forecast-input dicts keyed by year."""
    A = info["assump"]
    R = []
    add = R.append

    def blank():
        add(Row(None, style="blank"))

    # =====================================================================================
    add(Row("sec_rev", "REVENUE BUILD — GTV BY SECTOR × TAKE RATE + INVENTORY SALES (single reportable segment)",
            style="section", note="REVENUE BUILD — modelling logic (RB Global reports one operating segment; the build "
                                  "replaces HII's segment P&L)"))
    blank()

    # ---------------- Automotive ----------------
    def sector_block(code, name, src_gtv, src_lots, scn_base, note_hdr, legacy=None):
        add(Row(f"blk_{code}", name, style="block", note=note_hdr))
        add(Row(f"gtv_{code}", "  GTV (USDm)", style="sub", src=f"ops.{src_gtv}", cagr="cagr",
                qe=lambda x, c=code: f"={x.a('gtv')}*{_w(x, c)}/({_w(x, 'auto')}+{_w(x, 'het')}+{_w(x, 'oth')})",
                e=lambda x, c=code: f"={x.pp('gtv_'+c)}*(1+{x.a('gtvg_'+c)})",
                note="Q3/26E–Q4/26E: total GTV (FY26 outlook) allocated across sectors by prior-year same-quarter "
                     "sector GTV × 1H/26 sector y/y momentum. 2027E+: prior year × (1 + scenario sector GTV growth).",
                comment="Source: RB Global earnings releases (Form 8-K Ex. 99.1) — 'GTV by Sector' tables. "
                        + ("Current basis (Automotive / Heavy Equipment & Transportation / Other) recast from Q1/25 in the "
                           "Q2-26 release." if code != "auto" else
                           "Automotive composition unchanged across the Q2-26 sector re-presentation; disclosed from Q1/23 "
                           "(IAA acquired 20-Mar-2023).")))
        add(Row(f"lots_{code}", "  Lots sold (000s)", src=f"ops.{src_lots}", fmt=FMT_NUM1,
                fc=lambda x, c=code: f'=IFERROR({x.a("gtv_"+c)}/{x.a("gpl_"+c)}*1000,"")',
                e26=lambda x, c=code: (f"=SUM({x.q('lots_'+c,1)},{x.q('lots_'+c,2)},{x.q('lots_'+c,3)},"
                                       f"{x.q('lots_'+c,4)})"),
                comment="Source: earnings releases — 'Lots Sold by Sector' tables (thousands)."))
        add(Row(f"gpl_{code}", "  GTV per lot sold ($)", style="pct", fmt=FMT_NUM,
                hist=lambda x, c=code: f'=IFERROR({x.a("gtv_"+c)}/{x.a("lots_"+c)}*1000,"")',
                qe=lambda x, c=code: f"={x.py('gpl_'+c)}*(1+{x.abs_at('gplg_'+c,'2026E')})",
                e26=lambda x, c=code: f'=IFERROR({x.a("gtv_"+c)}/{x.a("lots_"+c)}*1000,"")',
                e=lambda x, c=code: f"={x.pp('gpl_'+c)}*(1+{x.a('gplg_'+c)})"))
        add(Row(f"gplg_{code}", "  GTV per lot y/y % (forecast input)", style="growth", fmt=FMT_PCT,
                hist=lambda x, c=code: f'=IFERROR({x.a("gpl_"+c)}/{x.py("gpl_"+c)}-1,"")' if x.py("gpl_" + c) else None,
                e26=A[f"gplg_{code}"][2026], e=lambda x, c=code: A[f"gplg_{c}"][x.c.year], input_fc=True,
                note="Price/mix per lot (input). 2026E cell drives Q3/Q4-26E lots (vs prior-year quarter GTV per lot)."))
        add(Row(f"gtvg_{code}", "  GTV y/y %", style="growth", fmt=FMT_PCT,
                hist=yoy(f"gtv_{code}"), qe=yoy(f"gtv_{code}"), e26=yoy(f"gtv_{code}"),
                e=lambda x, b=scn_base: "=" + x.scn(srow(b, x.c.year)),
                note=f"2027E–2030E: scenario lever ({code.upper()}_gtvGrowth, Bull/Base/Bear table →)."))
        add(Row(f"lotsg_{code}", "  Lots sold y/y %", style="growth", fmt=FMT_PCT, hist=yoy(f"lots_{code}"),
                fc=yoy(f"lots_{code}")))
        if legacy:
            for k, lab, s in legacy:
                add(Row(k, lab, style="memo", src=f"ops.{s}", fmt=FMT_NUM,
                        comment="Legacy sector basis as originally reported (Automotive / CC&T / Other) — 2023 to Q1/26. "
                                "Not comparable with the current basis rows above."))
        blank()

    sector_block("auto", "Automotive (salvage & remarketed passenger vehicles; IAA from 20-Mar-2023)",
                 "gtv_auto", "lots_auto", S_AUTO, "AUTOMOTIVE — modelling logic")
    sector_block("het", "Heavy Equipment & Transportation (HE&T — current basis from Q1/25)",
                 "gtv_het", "lots_het", S_HET, "HEAVY EQUIPMENT & TRANSPORTATION — modelling logic",
                 legacy=[("gtv_cct", "  Memo: CC&T GTV — legacy basis (2023–Q1/26)", "gtv_cct"),
                         ("lots_cct", "  Memo: CC&T lots sold (000s) — legacy basis", "lots_cct")])
    sector_block("oth", "Other (consumer goods, real estate, parts — current basis from Q1/25)",
                 "gtv_other", "lots_other", S_OTH, "OTHER — modelling logic",
                 legacy=[("gtv_othl", "  Memo: Other GTV — legacy basis (2023–Q1/26)", "gtv_other_legacy"),
                         ("lots_othl", "  Memo: Other lots sold (000s) — legacy basis", "lots_other_legacy")])

    # ---------------- Total GTV ----------------
    add(Row("blk_gtv", "Total GTV & lots", style="block", note="TOTAL GTV — modelling logic"))
    add(Row("gtv", "  Gross transaction value (GTV; 'gross auction proceeds' to Q2/17)", style="total", src="ops.gtv",
            cagr="cagr",
            qe=lambda x: (f"=({x.fy('gtv',2025)}*(1+{x.scn(S_GTV_G)})-{x.h('gtv')})*"
                          f"{x.q('gtv',x.c.q,2025)}/({x.q('gtv',3,2025)}+{x.q('gtv',4,2025)})"),
            e=lambda x: f"={x.a('gtv_auto')}+{x.a('gtv_het')}+{x.a('gtv_oth')}",
            note="Q3/26E–Q4/26E: FY26 outlook GTV growth (scenario: 11% / 10% / 9%) on FY25 GTV, less 1H/26 actual, "
                 "split by Q3/Q4-25 seasonality. 2027E+: sum of sectors.",
            comment="GTV = total proceeds from all items sold at auctions and online marketplaces (non-GAAP operating "
                    "metric). Ritchie Bros. reported 'gross auction proceeds' (GAP; 'gross auction sales' in 2006) through "
                    "Q2/17 and 'gross transaction value' (GTV, incl. IronPlanet online marketplaces) from the Q3-17 "
                    "release (GTV excludes EquipmentOne buyer premiums from Aug-2017; Q2/17 revised 1,257.4 → 1,254.3). "
                    "2013 GAP excludes EquipmentOne buyer premiums ($8.2m). Source: 40-F MD&A (2006–14), earnings releases "
                    "/ 10-K / 10-Q MD&A (2015+)."))
    add(Row("gtv_g", "  GTV y/y %", style="growth", fmt=FMT_PCT, hist=yoy("gtv"), fc=yoy("gtv")))
    add(Row("gtv_nonauto", "  Non-automotive GTV (HE&T + Other; total − Automotive)", fmt=FMT_NUM,
            hist=lambda x: f'=IF(ISNUMBER({x.a("gtv_auto")}),{x.a("gtv")}-{x.a("gtv_auto")},"")',
            fc=lambda x: f"={x.a('gtv')}-{x.a('gtv_auto')}",
            note="Comparable across the 2026 sector re-presentation (Automotive composition unchanged)."))
    add(Row("gtv_nonauto_g", "  Non-automotive GTV y/y %", style="growth", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("gtv_nonauto")}/{x.py("gtv_nonauto")}-1,"")' if x.py("gtv_nonauto") else None,
            fc=yoy("gtv_nonauto")))
    add(Row("auto_mix", "  Automotive % of GTV", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IF(ISNUMBER({x.a("gtv_auto")}),{x.a("gtv_auto")}/{x.a("gtv")},"")',
            fc=ratio("gtv_auto", "gtv")))
    add(Row("lots", "  Total lots sold (000s)", src="ops.lots_total", fmt=FMT_NUM1,
            fc=lambda x: f"={x.a('lots_auto')}+{x.a('lots_het')}+{x.a('lots_oth')}",
            comment="Lots sold (000s) per earnings releases; disclosed consistently from 2023 (RB Global)."))
    add(Row("gtv_chk", "  Check: sector GTV vs total (should be 0)", style="check",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("gtv_het")}),ROUND({x.a("gtv")}-{x.a("gtv_auto")}-{x.a("gtv_het")}'
                            f'-{x.a("gtv_oth")},1),"")'),
            fc=lambda x: f"=ROUND({x.a('gtv')}-{x.a('gtv_auto')}-{x.a('gtv_het')}-{x.a('gtv_oth')},1)"))
    blank()

    # ---------------- Revenue streams ----------------
    add(Row("blk_rs", "Revenue streams", style="block", note="REVENUE STREAMS — modelling logic"))
    add(Row("rs_seller", "  Transactional seller revenue (2023+)", src="is.seller_rev",
            qe=lambda x: f"={x.a('svc_b')}*{x.h('rs_seller')}/{x.h('svc_b')}",
            e=lambda x: f"={x.a('svc_b')}*{x.pp('rs_seller')}/{x.pp('svc_b')}",
            note="Service revenue split held at the prior-period mix (1H/26 mix for Q3/Q4-26E).",
            comment="Source: 10-K/10-Q 'Disaggregated Revenue' note and earnings releases. Revenue categories introduced "
                    "with the IAA acquisition (2023): transactional seller / transactional buyer / marketplace services."))
    add(Row("rs_buyer", "  Transactional buyer revenue (2023+)", src="is.buyer_rev",
            qe=lambda x: f"={x.a('svc_b')}*{x.h('rs_buyer')}/{x.h('svc_b')}",
            e=lambda x: f"={x.a('svc_b')}*{x.pp('rs_buyer')}/{x.pp('svc_b')}"))
    add(Row("rs_mkt", "  Marketplace services revenue (2023+)", src="is.mkt_services_rev",
            qe=lambda x: f"={x.a('svc_b')}-{x.a('rs_seller')}-{x.a('rs_buyer')}",
            e=lambda x: f"={x.a('svc_b')}-{x.a('rs_seller')}-{x.a('rs_buyer')}"))
    add(Row("rs_comm", "  Commissions (legacy presentation, ≤2022)", src="is.comm_rev",
            comment="Ritchie Bros. legacy revenue presentation: commission revenues (incl. net inventory gains pre-2018) "
                    "and fee revenues (buyer fees, documentation and other fees). Source: 40-F / 10-K revenue note."))
    add(Row("rs_fee", "  Fees (legacy presentation, ≤2022)", src="is.fee_rev"))
    add(Row("svc_b", "  Service revenue (build)", style="sub", cagr="cagr",
            hist=lambda x: (f'=IF(COUNT({x.a("rs_seller")},{x.a("rs_buyer")},{x.a("rs_mkt")},{x.a("rs_comm")},'
                            f'{x.a("rs_fee")})=0,"n/d",SUM({x.a("rs_seller")},{x.a("rs_buyer")},{x.a("rs_mkt")},'
                            f'{x.a("rs_comm")},{x.a("rs_fee")}))'),
            fc=lambda x: f"={x.a('gtv')}*{x.a('take')}",
            note="Forecast service revenue = GTV × service revenue take rate."))
    add(Row("take", "  Service revenue take rate (service revenue / GTV)", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("service_rev")}/{x.a("gtv")},"")',
            qe=lambda x: f"={x.abs_at('take','1H/26')}+{x.abs_at('take_d','2026E')}",
            e26=lambda x: f'=IFERROR({x.a("service_rev")}/{x.a("gtv")},"")',
            e=lambda x: A["take"][x.c.year], input_fc=True,
            note="Q3/Q4-26E: 1H/26 take rate + Δ input (row below). 2027E+: input — acquired businesses (J.J. Kane, "
                 "BigIron) and automotive volume incentives carry lower take rates.",
            comment="Pre-2018 (before ASC 606) Ritchie Bros. revenue included net gains on inventory contracts, so the "
                    "historical take rate equals total revenue / GAP ('revenue rate'). 2018+: service revenue / GTV."))
    add(Row("take_d", "  Q3/Q4-26E take-rate change vs 1H/26 (bps, input)", style="pct", fmt=FMT_PCT,
            e26=A["take_d26"], input_fc=True))
    add(Row("inv_b", "  Inventory sales revenue (gross basis from 2018, ASC 606)", src="is.inv_sales_rev", cagr="cagr",
            fc=lambda x: f"={x.a('gtv')}*{x.a('inv_pct')}",
            note="Forecast inventory sales = GTV × inventory sales % of GTV."))
    add(Row("inv_pct", "  Inventory sales % of GTV", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("inv_b")}/{x.a("gtv")},"")',
            qe=lambda x: f"={x.py('inv_pct')}*{x.abs_at('inv_pct','1H/26')}/{x.abs_at('inv_pct','1H/25')}",
            e26=lambda x: f'=IFERROR({x.a("inv_b")}/{x.a("gtv")},"")',
            e=lambda x: A["inv_pct"][x.c.year], input_fc=True,
            note="Q3/Q4-26E: prior-year quarter ratio scaled by the 1H/26 vs 1H/25 change (HE&T shift to inventory "
                 "contracts). 2027E+: input."))
    add(Row("inv_ret", "  Inventory return (inventory sales − cost of inventory sold)", fmt=FMT_NUM,
            hist=lambda x: f'=IF(ISNUMBER({x.a("inv_b")}),{x.a("inv_b")}-{x.a("cost_inv")},"")',
            fc=lambda x: f"={x.a('inv_b')}-{x.a('cost_inv')}"))
    add(Row("inv_rate", "  Inventory rate (inventory return / inventory sales)", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("inv_ret")}/{x.a("inv_b")},"")',
            qe=lambda x: f"={x.abs_at('inv_rate','1H/26')}",
            e26=lambda x: f'=IFERROR({x.a("inv_ret")}/{x.a("inv_b")},"")',
            e=lambda x: A["inv_rate"][x.c.year], input_fc=True,
            note="Q3/Q4-26E at the 1H/26 inventory rate; 2027E+ input (5-yr range ~5–9%)."))
    add(Row("rev_b", "  Total revenue (build)", style="total", cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("svc_b")}),{x.a("svc_b")}+N({x.a("inv_b")}),'
                            f'{x.a("service_rev")}+N({x.a("inv_b")}))'),
            fc=lambda x: f"={x.a('svc_b')}+{x.a('inv_b')}",
            note="Group revenue = service revenue + inventory sales revenue (ties to the GAAP income statement)."))
    add(Row("rev_pct_gtv", "  Total revenue % of GTV", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("rev_b")}/{x.a("gtv")},"")', fc=ratio("rev_b", "gtv")))
    add(Row("rev_chk", "  Check: service revenue build vs income statement (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("svc_b")}),ROUND({x.a("svc_b")}-{x.a("service_rev")},1),"n/d")',
            fc=lambda x: f"=ROUND({x.a('rev_b')}-{x.a('total_rev')},1)"))
    blank()

    # ---------------- Cost drivers ----------------
    add(Row("blk_cd", "Cost drivers (% of revenue)", style="block",
            note="% OF REVENUE drivers — hardcoded inputs that drive forecast cost lines"))
    add(Row("cs_pct", "  Costs of services % of service revenue", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("cost_services")}/{x.a("service_rev")},"")',
            qe=lambda x: f"={x.py('cs_pct')}*{x.abs_at('cs_pct','1H/26')}/{x.abs_at('cs_pct','1H/25')}",
            e26=lambda x: f'=IFERROR({x.a("cost_services")}/{x.a("service_rev")},"")',
            e=lambda x: A["cs_pct"][x.c.year], input_fc=True,
            note="Costs of services (ex D&A): towing, yard & auction-site labour, inspection, buyer-fee related costs. "
                 "Q3/Q4-26E: prior-year quarter ratio × 1H/26 vs 1H/25 drift; 2027E+ input."))
    add(Row("adj_da_pct", "  Adjusted D&A % of revenue (ex acquired-intangible amortization)", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("adj_da")}/{x.a("total_rev")},"")',
            qe=lambda x: f"={x.abs_at('adj_da_pct','1H/26')}",
            e26=lambda x: f'=IFERROR({x.a("adj_da")}/{x.a("total_rev")},"")',
            e=lambda x: A["adj_da_pct"][x.c.year], input_fc=True,
            note="Depreciation of yards / IT and amortization of software (ex acquired intangibles). 1H/26 ratio for "
                 "Q3/Q4-26E; 2027E+ input."))
    add(Row("sbc_pct", "  Stock-based compensation % of revenue", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("a_SBC")}/{x.a("total_rev")},"")', fc=ratio("a_SBC", "total_rev")))
    blank()

    # ---------------- Geography ----------------
    add(Row("blk_geo", "Revenue by geography (location of auction / service)", style="block",
            note="GEOGRAPHY — historical disclosure only (not forecast)"))
    for k, lab, s in [("geo_us", "  United States", "rev_us"), ("geo_ca", "  Canada", "rev_canada"),
                      ("geo_eu", "  Europe", "rev_europe"), ("geo_au", "  Australia", "rev_australia"),
                      ("geo_ot", "  Other", "rev_other_geo"), ("geo_intl", "  International (legacy: non-US/Canada)", "rev_international")]:
        add(Row(k, lab, src=f"ops.{s}",
                comment="Source: 40-F / 10-K segment & geographic information note (annual); 10-Q disaggregated "
                        "revenue note (quarterly, 2023+)." if k == "geo_us" else ""))
    add(Row("geo_us_pct", "  United States % of revenue", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IF(ISNUMBER({x.a("geo_us")}),{x.a("geo_us")}/{x.a("total_rev")},"")'))
    blank()

    # ---------------- Group total: adjusted EBITDA ----------------
    add(Row("blk_grp", "Group Total — adjusted EBITDA & adjusted EBIT (RB Global's primary profit KPIs)", style="block",
            note="GROUP TOTAL (CONSOLIDATED) — modelling logic"))
    add(Row("total_rev_g", "  Total revenue", style="sub", cagr="cagr",
            hist=lambda x: f"={x.a('total_rev')}", fc=lambda x: f"={x.a('total_rev')}"))
    add(Row("adj_ebitda", "  Adjusted EBITDA (company definition of the period)", style="total", cagr="cagr",
            hist=lambda x: f'=IF(ISNUMBER({x.a("a_pub")}),{x.a("a_pub")},{x.a("a_adj")})',
            qe=lambda x: (f"=({x.scn(S_EBITDA)}-{x.h('adj_ebitda')})*{x.a('total_rev')}/"
                          f"({x.q('total_rev',3)}+{x.q('total_rev',4)})"),
            e26=lambda x: f"=SUM({x.q('adj_ebitda',1)},{x.q('adj_ebitda',2)},{x.q('adj_ebitda',3)},{x.q('adj_ebitda',4)})",
            e=lambda x: f"={x.a('total_rev')}*{x.a('adj_ebitda_m')}",
            note="Historical = company-published adjusted EBITDA (model bridge where not published). Q3/26E–Q4/26E: FY26 "
                 "outlook ($1,545m / $1,520m / $1,495m by scenario) less 1H/26, split by quarterly revenue. 2027E+: "
                 "revenue × scenario adjusted EBITDA margin."))
    add(Row("adj_ebitda_m", "  Adjusted EBITDA margin % (of total revenue)", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebitda", "total_rev"), qe=ratio("adj_ebitda", "total_rev"),
            e26=ratio("adj_ebitda", "total_rev"),
            e=lambda x: "=" + x.scn(srow(S_MARGIN, x.c.year)),
            note="2027E–2030E: scenario lever (ADJ_EBITDA_margin). Inventory-sales mix dilutes the revenue margin; see "
                 "% of GTV and % of service revenue + inventory return below."))
    add(Row("adj_ebitda_gtv", "  Adjusted EBITDA % of GTV", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebitda", "gtv"), fc=ratio("adj_ebitda", "gtv")))
    add(Row("adj_ebitda_nr", "  Adjusted EBITDA % of (service revenue + inventory return)", style="pct", fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR({x.a("adj_ebitda")}/({x.a("service_rev")}+N({x.a("inv_ret")})),"")',
            fc=lambda x: f'=IFERROR({x.a("adj_ebitda")}/({x.a("service_rev")}+{x.a("inv_ret")}),"")'))
    add(Row("adj_ebitda_g", "  Adjusted EBITDA y/y %", style="growth", fmt=FMT_PCT, hist=yoy("adj_ebitda"),
            fc=yoy("adj_ebitda")))
    add(Row("adj_ebitda_inc", "  Incremental adjusted EBITDA margin (ΔAdj. EBITDA / ΔRevenue)", style="pct", fmt=FMT_PCT,
            hist=lambda x: (f'=IFERROR(({x.a("adj_ebitda")}-{x.py("adj_ebitda")})/({x.a("total_rev")}-'
                            f'{x.py("total_rev")}),"")') if x.py("adj_ebitda") else None,
            fc=lambda x: (f'=IFERROR(({x.a("adj_ebitda")}-{x.py("adj_ebitda")})/({x.a("total_rev")}-'
                          f'{x.py("total_rev")}),"")')))
    add(Row("adj_da", "  Adjusted D&A (total D&A − amortization of acquired intangibles)", fmt=FMT_NUM,
            hist=lambda x: f"={x.a('da')}-N({x.a('n_AMORT')})",
            fc=lambda x: f"={x.a('total_rev')}*{x.a('adj_da_pct')}",
            note="Amortization of acquired intangibles is disclosed as an adjusting item from 2023 (IAA); before 2023 "
                 "adjusted D&A = total D&A."))
    add(Row("adj_ebit", "  Adjusted EBIT (adjusted EBITDA − adjusted D&A)", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('adj_ebitda')}-{x.a('adj_da')}", fc=lambda x: f"={x.a('adj_ebitda')}-{x.a('adj_da')}",
            note="Model measure (RB Global does not publish adjusted EBIT): adjusted operating profit after the "
                 "depreciation of yards / IT but before acquired-intangible amortization — the 'segment OI' analogue."))
    add(Row("adj_ebit_m", "  Adjusted EBIT margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebit", "total_rev"), fc=ratio("adj_ebit", "total_rev")))
    add(Row("ebitda_gaap", "  EBITDA (GAAP-derived: net income + D&A + interest − interest income + tax)", fmt=FMT_NUM,
            hist=lambda x: f"={x.a('a_ebitda')}", fc=lambda x: f"={x.a('a_ebitda')}"))
    add(Row("grp_chk", "  Check: adjusted EBITDA model bridge vs KPI (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("a_pub")}),ROUND({x.a("a_adj")}-{x.a("adj_ebitda")},1),"n/p")',
            fc=lambda x: f"=ROUND({x.a('a_adj')}-{x.a('adj_ebitda')},1)"))
    blank()

    # =====================================================================================
    add(Row("sec_is", "CONSOLIDATED INCOME STATEMENT (US GAAP)", style="section", note="CONSOLIDATED IS — forecast logic"))
    add(Row("service_rev", "Service revenue (pre-2018: total revenues, commissions + fees)", src="is.service_rev",
            cagr="cagr", fc=lambda x: f"={x.a('svc_b')}",
            note="Forecast linked to the revenue build.",
            comment="Source: 40-F (2006–14) and 10-K/10-Q (2015+) consolidated income statements, latest filing "
                    "presenting each period; quarters from earnings releases (Form 6-K pre-2016, 8-K Ex. 99.1)."))
    add(Row("inv_sales_rev", "Inventory sales revenue", src="is.inv_sales_rev", cagr="cagr",
            fc=lambda x: f"={x.a('inv_b')}",
            comment="ASC 606 (adopted 1-Jan-2018, modified retrospective): inventory contracts presented gross as "
                    "inventory sales revenue / cost of inventory sold. Pre-2018 inventory gains were netted in revenues."))
    add(Row("total_rev", "Total revenue", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('service_rev')}+{x.a('inv_sales_rev')}",
            fc=lambda x: f"={x.a('service_rev')}+{x.a('inv_sales_rev')}"))
    add(Row("rev606_memo", "  Memo: total revenue on ASC 606 basis — company recast of 2016 (FY2018 10-K)", style="memo",
            src="ops.rev_asc606_memo",
            comment="ASC 606 adopted 1-Jan-2018 (full retrospective): the 2018 10-Qs / FY2018 10-K recast 2017 in full "
                    "(used in this model) and re-presented 2016 total revenue only (gross inventory sales). 2016 and "
                    "earlier are therefore shown on the legacy net basis; this memo bridges the two."))
    add(Row("cost_services", "Costs of services (ex D&A; legacy 'direct expenses')", src="is.cost_services",
            fc=lambda x: f"={x.a('service_rev')}*{x.a('cs_pct')}",
            note="Costs of services = service revenue × cost-of-services % (driver block)."))
    add(Row("cost_inv", "Cost of inventory sold", src="is.cost_inventory",
            fc=lambda x: f"={x.a('inv_sales_rev')}*(1-{x.a('inv_rate')})",
            note="Cost of inventory sold = inventory sales × (1 − inventory rate)."))
    add(Row("sga", "Selling, general and administrative expenses", src="is.sga",
            fc=lambda x: (f"={x.a('total_rev')}-{x.a('cost_services')}-{x.a('cost_inv')}-{x.a('acq_costs')}"
                          f"-{x.a('impairment')}+{x.a('gain_disp')}+{x.a('other_op')}-{x.a('adj_ebitda')}"
                          f"+{x.a('a_items')}+{x.a('other_income')}+{x.a('fx')}+{x.a('other_nonop')}"),
            note="Forecast SG&A is the balancing line so that adjusted EBITDA equals the KPI driver (outlook / margin "
                 "lever): SG&A = revenue − costs of services − cost of inventory − adj. EBITDA + SBC, restructuring "
                 "& other adjusting items recorded in SG&A."))
    add(Row("acq_costs", "Acquisition-related and integration costs", src="is.acq_costs",
            fc=lambda x: f"={x.a('a_ACQ')}"))
    add(Row("da", "Depreciation and amortization", src="is.da", cagr="cagr",
            fc=lambda x: f"={x.a('adj_da')}+{x.a('n_AMORT')}",
            note="D&A = adjusted D&A (% of revenue) + amortization of acquired intangibles (10-K schedule)."))
    add(Row("impairment", "Impairment losses", src="is.impairment", fc=0))
    add(Row("total_opex", "Total operating expenses", style="sub",
            hist=lambda x: (f"={x.a('cost_services')}+N({x.a('cost_inv')})+{x.a('sga')}+N({x.a('acq_costs')})"
                            f"+{x.a('da')}+N({x.a('impairment')})"),
            fc=lambda x: (f"={x.a('cost_services')}+{x.a('cost_inv')}+{x.a('sga')}+{x.a('acq_costs')}+{x.a('da')}"
                          f"+{x.a('impairment')}")))
    add(Row("gain_disp", "Gain (loss) on disposition of property, plant and equipment", src="is.gain_disp_ppe", fc=0,
            note="Forecast nil (large historical gains were surplus-land sales)."))
    add(Row("other_op", "Other operating items (e.g. loss on deconsolidation / divestiture)", src="is.other_op", fc=0))
    add(Row("op_income", "Operating income", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('total_rev')}-{x.a('total_opex')}+N({x.a('gain_disp')})+N({x.a('other_op')})",
            fc=lambda x: f"={x.a('total_rev')}-{x.a('total_opex')}+{x.a('gain_disp')}+{x.a('other_op')}"))
    add(Row("interest_exp", "Interest expense", src="is.interest_exp",
            qe=lambda x: f"={x.h('interest_exp')}/2",
            e=lambda x: f"={x.a('int_rate')}*AVERAGE({x.a('debt')},{x.pp('debt')})",
            note="Q3/Q4-26E at 1H/26 run-rate (no interest guidance). 2027E+ = rate on average total debt."))
    add(Row("interest_inc", "Interest income", src="is.interest_income",
            qe=lambda x: f"={x.h('interest_inc')}/2",
            e=lambda x: f"={x.a('cash_rate')}*{x.pp('cash')}",
            note="Q3/Q4-26E at 1H/26 run-rate. 2027E+ = yield × prior year-end cash (avoids a circular reference)."))
    add(Row("other_income", "Other income (loss), net (incl. equity income)", src="is.other_income", fc=0))
    add(Row("fx", "Foreign exchange gain (loss)", src="is.fx", fc=0))
    add(Row("other_nonop", "Other non-operating items (e.g. change in fair value of derivatives)", src="is.other_nonop",
            fc=0))
    add(Row("pretax", "Income before income taxes", style="total", cagr="cagr",
            hist=lambda x: (f"={x.a('op_income')}-{x.a('interest_exp')}+N({x.a('interest_inc')})+N({x.a('other_income')})"
                            f"+N({x.a('fx')})+N({x.a('other_nonop')})"),
            fc=lambda x: (f"={x.a('op_income')}-{x.a('interest_exp')}+{x.a('interest_inc')}+{x.a('other_income')}"
                          f"+{x.a('fx')}+{x.a('other_nonop')}")))
    add(Row("tax", "Income tax expense", src="is.tax",
            qe=lambda x: (f"=({x.base(S_TAX)}*({x.h('pretax')}+{x.q('pretax',3)}+{x.q('pretax',4)})"
                          f"-{x.h('tax')})/2"),
            e=lambda x: f"={x.a('pretax')}*{x.a('etr')}",
            note="FY26 tax-rate outlook 23–25% (24% mid) applied to FY26E pre-tax income less 1H tax, split across "
                 "Q3/Q4. 2027E+ input ETR."))
    add(Row("etr", "  Effective tax rate", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("tax", "pretax"), qe=ratio("tax", "pretax"), e26=ratio("tax", "pretax"),
            e=lambda x: A["etr"][x.c.year], input_fc=True))
    add(Row("net_income", "Net income", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('pretax')}-{x.a('tax')}", fc=lambda x: f"={x.a('pretax')}-{x.a('tax')}"))
    add(Row("nci", "  Net income (loss) attributable to non-controlling interests", src="is.nci", fc=0))
    add(Row("ni_ctrl", "Net income attributable to controlling interests", style="sub",
            hist=lambda x: f"={x.a('net_income')}-N({x.a('nci')})",
            fc=lambda x: f"={x.a('net_income')}-{x.a('nci')}"))
    add(Row("pref_div", "  Cumulative dividends on Series A Senior Preferred Shares (2023+)", src="is.pref_div",
            qe=A["pref_div_q"], e=A["pref_div_y"], input_fc=True,
            note="Series A Senior Preferred ($485m, 5.5% cumulative; issued 2023 to Starboard / Ancora) — ~$6.7m per "
                 "quarter."))
    add(Row("pref_alloc", "  Allocated earnings to Series A Senior Preferred (two-class)", src="is.pref_alloc",
            fc=lambda x: f"=({x.a('ni_ctrl')}-{x.a('pref_div')})*{x.a('pref_alloc_pct')}",
            note="Two-class participation: (NI to controlling − preferred dividends) × allocation % (schedule)."))
    add(Row("rnci_adj", "  Adjustment of redeemable non-controlling interest", src="is.rnci_adj", fc=0))
    add(Row("ni_common", "Net income available to common stockholders", style="total", cagr="cagr",
            hist=lambda x: (f"={x.a('ni_ctrl')}-N({x.a('pref_div')})-N({x.a('pref_alloc')})+N({x.a('rnci_adj')})"),
            fc=lambda x: f"={x.a('ni_ctrl')}-{x.a('pref_div')}-{x.a('pref_alloc')}+{x.a('rnci_adj')}",
            note="Pre-2023 (no preferred shares) = net income attributable to stockholders."))
    add(Row("ni_chk", "  Check: net income vs as reported (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("ni_rep")}),ROUND({x.a("net_income")}-{x.a("ni_rep")},1),"")'))
    add(Row("ni_rep", "  Memo: net income as reported", style="memo", src="is.net_income"))
    add(Row("memo_debt_ext", "  Memo: loss on debt extinguishment / refinancing (within interest or other)", style="memo",
            src="is.memo_debt_extinguishment", fc=0))
    add(Row("eps_hdr", "(Earnings per share)", style="line"))
    add(Row("sh_basic", "  Weighted-average basic shares (m)", src="is.shares_basic", agg="avg", fmt=FMT_SHR,
            qe=lambda x: f"={x.at('sh_basic','Q2/26')}-{x.at('bb_shares','2026E')}*(" + ("0.25" if False else "") +
            f"{x.c.q}-2)/2",
            e26=lambda x: f"=AVERAGE({x.q('sh_basic',1)},{x.q('sh_basic',2)},{x.q('sh_basic',3)},{x.q('sh_basic',4)})",
            e=lambda x: f"=AVERAGE({x.a('bb_beg')},{x.a('bb_end')})",
            note="Q3/Q4-26E: Q2/26 less the 2H/26 buyback phased in. 2027E+ = average of beginning and ending shares "
                 "(buyback schedule)."))
    add(Row("sh_dil", "  Weighted-average diluted shares (m)", src="is.shares_diluted", agg="avg", fmt=FMT_SHR,
            qe=lambda x: f"={x.a('sh_basic')}+({x.at('sh_dil','Q2/26')}-{x.at('sh_basic','Q2/26')})",
            e26=lambda x: f"=AVERAGE({x.q('sh_dil',1)},{x.q('sh_dil',2)},{x.q('sh_dil',3)},{x.q('sh_dil',4)})",
            e=lambda x: f"={x.a('sh_basic')}+{x.a('dil_sec')}",
            note="Diluted = basic + dilutive stock options / PSUs / RSUs (input). Series A preferred conversion is "
                 "anti-dilutive under the two-class method in most periods."))
    add(Row("eps_basic", "EPS – basic, available to common ($)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("ni_common")}/{x.a("sh_basic")},"")',
            fc=lambda x: f'=IFERROR({x.a("ni_common")}/{x.a("sh_basic")},"")'))
    add(Row("eps_dil", "EPS – diluted, available to common ($)", style="total", fmt=FMT_EPS, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("ni_common")}/{x.a("sh_dil")},"")',
            fc=lambda x: f'=IFERROR({x.a("ni_common")}/{x.a("sh_dil")},"")',
            note="EPS computed as NI available to common / weighted diluted shares (may differ by ±$0.01 vs reported)."))
    add(Row("eps_dil_rep", "  Memo: EPS – diluted as reported ($)", style="memo", fmt=FMT_EPS, src="is.eps_diluted",
            agg="none"))
    add(Row("dps", "Dividends declared per share ($)", src="is.dps_declared", fmt=FMT_EPS, cagr="cagr",
            qe=A["dps_q"], e=lambda x: f"={x.pp('dps')}*(1+{x.a('dps_g')})", input_fc=False,
            note="Q3/Q4-26E at the $0.33 quarterly dividend declared 21-Jul-2026. 2027E+ grows with the DPS-growth "
                 "input."))
    blank()

    # =====================================================================================
    # Bridge A: NI → EBITDA → adjusted EBITDA → adjusted EBIT
    add(Row("sec_ra", "RECONCILIATION: GAAP NET INCOME → EBITDA → ADJUSTED EBITDA → ADJUSTED EBIT",
            style="section", note="ADJUSTED EBITDA RECONCILIATION — per RB Global earnings-release 'Adjusted EBITDA' "
                                  "table; adjusting items follow the company definition in force in each period"))
    add(Row("a_ni", "Net income (GAAP)", style="sub", hist=lambda x: f"={x.a('net_income')}",
            fc=lambda x: f"={x.a('net_income')}"))
    add(Row("a_da", "  (+) Depreciation and amortization", hist=lambda x: f"={x.a('da')}", fc=lambda x: f"={x.a('da')}"))
    add(Row("a_int", "  (+) Interest expense", hist=lambda x: f"={x.a('interest_exp')}",
            fc=lambda x: f"={x.a('interest_exp')}"))
    add(Row("a_intinc", "  (−) Interest income", hist=lambda x: f"=-N({x.a('interest_inc')})",
            fc=lambda x: f"=-{x.a('interest_inc')}"))
    add(Row("a_tax", "  (+) Income tax expense", hist=lambda x: f"={x.a('tax')}", fc=lambda x: f"={x.a('tax')}"))
    add(Row("a_ebitda", "  = EBITDA", style="total", cagr="cagr",
            hist=lambda x: f"=SUM({x.a('a_ni')}:{x.a('a_tax')})", fc=lambda x: f"=SUM({x.a('a_ni')}:{x.a('a_tax')})"))
    add(Row("a_ebitda_chk", "  Check: EBITDA vs company-published EBITDA (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("a_ebitda_pub")}),ROUND({x.a("a_ebitda")}-{x.a("a_ebitda_pub")},1),"n/p")'))
    add(Row("a_ebitda_pub", "  Memo: EBITDA as published", style="memo", src="adjE.ebitda_published"))
    add(Row("a_hdr", "Adjusting items (pre-tax; company definition of the period — see definition row):", style="memo"))
    first_item = None
    for cat, lab in info["cats_e"]:
        k = f"a_{cat}"
        first_item = first_item or k
        if cat in FC_INPUT_CATS:
            fc_kw = dict(qe=(lambda x, c=cat: A[f"adj_{c}_q"]), e=(lambda x, c=cat: A[f"adj_{c}"][x.c.year]),
                         input_fc=True)
        else:
            fc_kw = dict(fc=0)
        add(Row(k, "  (+) " + lab, src=f"adjE.{cat}", **fc_kw,
                note={"SBC": "SBC added back from Q1/23 (RB Global definition adopted with IAA). Forecast input (~3% of "
                             "revenue less in out-years).",
                      "ACQ": "Acquisition & integration costs (IAA, J.J. Kane, BigIron). Forecast input.",
                      "RESTR": "Restructuring (IAA integration, 2025–26 programmes). Forecast input.",
                      "LEGAL": "Other legal, advisory & non-income tax. Forecast input."}.get(cat, "")))
    last_item = f"a_{info['cats_e'][-1][0]}"
    add(Row("a_items", "  Total adjusting items", style="sub",
            hist=lambda x: f"=SUM({x.a(first_item)}:{x.a(last_item)})",
            fc=lambda x: f"=SUM({x.a(first_item)}:{x.a(last_item)})"))
    add(Row("a_adj", "  = Adjusted EBITDA (model bridge)", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('a_ebitda')}+{x.a('a_items')}", fc=lambda x: f"={x.a('a_ebitda')}+{x.a('a_items')}"))
    add(Row("a_adj_m", "  Adjusted EBITDA margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("a_adj", "total_rev"), fc=ratio("a_adj", "total_rev")))
    add(Row("a_pub", "  Company-published adjusted EBITDA", style="memo", src="adjE.adj_ebitda_published"))
    add(Row("a_chk", "  Check: model bridge vs company-published (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("a_pub")}),ROUND({x.a("a_adj")}-{x.a("a_pub")},1),"n/p")'))
    add(Row("a_def", "  Definition basis (company adjusted-EBITDA definition in force)", style="deftext",
            texts=info["def_ebitda"]))
    add(Row("a_ebit_hdr", "To adjusted EBIT:", style="memo"))
    add(Row("a_less_da", "  (−) Depreciation and amortization", hist=lambda x: f"=-{x.a('da')}",
            fc=lambda x: f"=-{x.a('da')}"))
    add(Row("a_add_amort", "  (+) Amortization of acquired intangibles (excluded from adjusted measures from 2023)",
            hist=lambda x: f"=N({x.a('n_AMORT')})", fc=lambda x: f"={x.a('n_AMORT')}"))
    add(Row("a_ebit", "  = Adjusted EBIT (model)", style="total", cagr="cagr",
            hist=lambda x: f"={x.a('a_adj')}+{x.a('a_less_da')}+{x.a('a_add_amort')}",
            fc=lambda x: f"={x.a('a_adj')}+{x.a('a_less_da')}+{x.a('a_add_amort')}"))
    add(Row("a_oi_chk", "  Check: GAAP operating income + D&A + other income / FX = EBITDA (should be 0)", style="check",
            hist=lambda x: (f"=ROUND({x.a('op_income')}+{x.a('da')}+N({x.a('other_income')})+N({x.a('fx')})"
                            f"+N({x.a('other_nonop')})-{x.a('a_ebitda')},1)"),
            fc=lambda x: (f"=ROUND({x.a('op_income')}+{x.a('da')}+{x.a('other_income')}+{x.a('fx')}"
                          f"+{x.a('other_nonop')}-{x.a('a_ebitda')},1)")))
    blank()

    # =====================================================================================
    # Bridge B: NI available to common → adjusted NI → adjusted EPS
    add(Row("sec_rb", "RECONCILIATION: GAAP NET INCOME AVAILABLE TO COMMON → ADJUSTED NET INCOME / ADJUSTED EPS",
            style="section", note="ADJUSTED NET INCOME & EPS RECONCILIATION — company definition in force in each "
                                  "period (definition changes flagged in the definition row and cell comments)"))
    add(Row("b_base", "Net income available to common stockholders (GAAP; pre-2023: attributable to stockholders)",
            style="sub", hist=lambda x: f"={x.a('ni_common')}", fc=lambda x: f"={x.a('ni_common')}"))
    first_n = None
    for cat, lab in info["cats_n"]:
        k = f"n_{cat}"
        first_n = first_n or k
        if cat == "AMORT":
            fc_kw = dict(qe=lambda x: f"=({x.abs_at('amort_sched','2026E')}-{x.h('n_AMORT')})/2",
                         e26=lambda x: f"=SUM({x.q('n_AMORT',1)},{x.q('n_AMORT',2)},{x.q('n_AMORT',3)},{x.q('n_AMORT',4)})",
                         e=lambda x: f"={x.a('amort_sched')}")
        elif cat in FC_INPUT_CATS:
            fc_kw = dict(fc=lambda x, c=cat: f"={x.a('a_'+c)}")
        else:
            fc_kw = dict(fc=0)
        add(Row(k, "  (+) " + lab, src=f"adjN.{cat}", **fc_kw,
                note="Acquired-intangible amortization added back from Q1/23 (RB Global definition)."
                if cat == "AMORT" else ""))
    last_n = f"n_{info['cats_n'][-1][0]}"
    add(Row("n_TAX", "  (−) Related tax effects of the above", src="adjN.TAX",
            fc=lambda x: f"=-SUM({x.a(first_n)}:{x.a(last_n)})*{x.a('b_taxrate')}"))
    add(Row("n_TAXD", "  (+/−) Discrete / non-recurring tax items (tax reform, reorganisation, valuation allowance)",
            src="adjN.TAXD", fc=0))
    add(Row("n_PREF", "  (−) Related allocation of the above to Series A Senior Preferred Shares", src="adjN.PREF",
            fc=lambda x: f"=-SUM({x.a(first_n)}:{x.a('n_TAXD')})*{x.a('pref_alloc_pct')}"))
    add(Row("n_RNCI", "  (+/−) Adjustment of redeemable non-controlling interest", src="adjN.RNCI", fc=0))
    add(Row("b_adj", "  = Adjusted net income available to common stockholders (model bridge)", style="total",
            cagr="cagr", hist=lambda x: f"=SUM({x.a('b_base')}:{x.a('n_RNCI')})",
            fc=lambda x: f"=SUM({x.a('b_base')}:{x.a('n_RNCI')})"))
    add(Row("b_taxrate", "  Tax rate applied to adjustments (forecast input; historical = implied)", style="pct",
            fmt=FMT_PCT,
            hist=lambda x: f'=IFERROR(-{x.a("n_TAX")}/SUM({x.a(first_n)}:{x.a(last_n)}),"")',
            fc=A["adj_taxrate"], input_fc=True))
    add(Row("b_sh", "  Weighted-average diluted shares (m)", fmt=FMT_SHR, agg="avg", hist=lambda x: f"={x.a('sh_dil')}",
            fc=lambda x: f"={x.a('sh_dil')}"))
    add(Row("b_eps", "Adjusted EPS – diluted, available to common ($) (model bridge)", style="total", fmt=FMT_EPS,
            cagr="cagr", hist=lambda x: f'=IFERROR({x.a("b_adj")}/{x.a("b_sh")},"")',
            fc=lambda x: f'=IFERROR({x.a("b_adj")}/{x.a("b_sh")},"")'))
    add(Row("b_pub_ni", "  Company-published adjusted net income (available to common)", style="memo",
            src="adjN.adj_ni_published"))
    add(Row("b_pub_eps", "  Company-published diluted adjusted EPS ($)", style="memo", fmt=FMT_EPS,
            src="adjN.adj_eps_published", agg="none"))
    add(Row("b_chk", "  Check: model bridge vs company-published adjusted net income (should be 0)", style="check",
            hist=lambda x: f'=IF(ISNUMBER({x.a("b_pub_ni")}),ROUND({x.a("b_adj")}-{x.a("b_pub_ni")},1),"n/p")'))
    add(Row("b_def", "  Definition basis (company adjusted-EPS definition in force)", style="deftext",
            texts=info["def_ni"]))
    blank()

    # =====================================================================================
    add(Row("sec_gm", "GROWTH & MARGINS", style="section", note="GROWTH & MARGINS (consolidated) — forecast outputs"))
    add(Row("g_rev", "  Revenue y/y %", style="growth", fmt=FMT_PCT, hist=yoy("total_rev"), fc=yoy("total_rev")))
    add(Row("g_org", "  Revenue — organic y/y %", style="growth", fmt=FMT_PCT, quarters_ok=False,
            hist=lambda x: f'=IFERROR({x.a("g_rev")}-{x.a("g_acq")},"")' if x.c.kind in ("A", "Y") else None,
            fc=lambda x: f'=IFERROR({x.a("g_rev")}-{x.a("g_acq")},"")',
            note="Organic = total growth less disclosed acquisition revenue contribution (first 12 months)."))
    add(Row("g_acq", "  Revenue — acquisition y/y %", style="growth", fmt=FMT_PCT, quarters_ok=False,
            hist=lambda x: (f'=IFERROR({x.a("acq_rev")}/{x.py("total_rev")},0)' if x.c.kind in ("A", "Y") and x.py("total_rev")
                            else None),
            e26=lambda x: f'=IFERROR({x.a("acq_rev")}/{x.py("total_rev")},0)', e=0))
    add(Row("acq_rev", "  Memo: revenue contributed by acquisitions (USDm, disclosed)", style="memo",
            src="ops.acq_revenue_contribution", quarters_ok=False, e26=A["acq_rev_2026"], input_fc=True,
            note="2026E: BigIron (closed 15-May-2026) and J.J. Kane annualisation — estimate (input)."))
    add(Row("g_svc", "  Service revenue y/y %", style="growth", fmt=FMT_PCT, hist=yoy("service_rev"), fc=yoy("service_rev")))
    add(Row("g_ebitda", "  Adjusted EBITDA y/y %", style="growth", fmt=FMT_PCT, hist=yoy("adj_ebitda"), fc=yoy("adj_ebitda")))
    add(Row("g_oi", "  Operating income y/y %", style="growth", fmt=FMT_PCT, hist=yoy("op_income"), fc=yoy("op_income")))
    add(Row("g_ni", "  Net income y/y %", style="growth", fmt=FMT_PCT, hist=yoy("net_income"), fc=yoy("net_income")))
    add(Row("g_eps", "  Adjusted EPS y/y %", style="growth", fmt=FMT_PCT, hist=yoy("b_eps"), fc=yoy("b_eps")))
    add(Row("m_take", "  Service revenue take rate %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f"={x.a('take')}", fc=lambda x: f"={x.a('take')}"))
    add(Row("m_net", "  (Service revenue + inventory return) % of revenue", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f'=IFERROR(({x.a("service_rev")}+N({x.a("inv_ret")}))/{x.a("total_rev")},"")',
            fc=lambda x: f'=IFERROR(({x.a("service_rev")}+{x.a("inv_ret")})/{x.a("total_rev")},"")'))
    add(Row("m_ebitda", "  Adjusted EBITDA margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("adj_ebitda", "total_rev"), fc=ratio("adj_ebitda", "total_rev")))
    add(Row("m_oi", "  Operating margin (GAAP) %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("op_income", "total_rev"), fc=ratio("op_income", "total_rev")))
    add(Row("m_ni", "  Net margin %", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("net_income", "total_rev"), fc=ratio("net_income", "total_rev")))
    add(Row("m_inc", "  Incremental adjusted EBITDA margin (ΔAdj. EBITDA / ΔRev)", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f"={x.a('adj_ebitda_inc')}", fc=lambda x: f"={x.a('adj_ebitda_inc')}"))
    add(Row("m_cs", "  Costs of services % of service revenue", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=lambda x: f"={x.a('cs_pct')}", fc=lambda x: f"={x.a('cs_pct')}"))
    add(Row("m_sga", "  SG&A % of revenue", style="pct", fmt=FMT_PCT, cagr="avg",
            hist=ratio("sga", "total_rev"), fc=ratio("sga", "total_rev")))
    blank()

    # =====================================================================================
    cf_rows(R, A)
    bs_rows(R, A)
    return R


def cf_rows(R, A):
    add = R.append

    def cf(key, label, src, fc=None, e26=None, e=None, style="line", note="", **kw):
        add(Row(key, label, src=src, style=style, annual_only=True, agg="none", e26=e26 if e26 is not None else fc,
                e=e if e is not None else fc, note=note, **kw))

    add(Row("sec_cf", "CONSOLIDATED CASH FLOW STATEMENT", style="section",
            note="CONSOLIDATED CASH FLOW STATEMENT — forecast logic (annual; 1H/26 = reported six months)"))
    add(Row(None, style="blank"))
    cf("cf_ni", "Net income", "cf.net_income", fc=lambda x: f"={x.a('net_income')}")
    add(Row("cf_adj_hdr", "Adjustments:", style="line"))
    cf("cf_da", "  Depreciation and amortization", "cf.da", fc=lambda x: f"={x.a('da')}")
    cf("cf_sbc", "  Stock-based compensation expense", "cf.sbc", fc=lambda x: f"={x.a('a_SBC')}")
    cf("cf_dtax", "  Deferred income taxes", "cf.deferred_tax", fc=lambda x: A["dtax"][x.c.year],
       note="Deferred tax benefit from acquired-intangible amortization (book > tax) — input.", input_fc=True)
    cf("cf_debtc", "  Amortization of debt issuance costs", "cf.amort_debt_costs", fc=0,
       note="Forecast nil: debt is carried at principal in the forecast (issue-cost amortization folded into the "
            "interest rate).")
    cf("cf_disp", "  (Gain) loss on disposition of PP&E", "cf.gain_disp", fc=lambda x: f"=-{x.a('gain_disp')}")
    cf("cf_imp", "  Impairment / loss on deconsolidation & divestiture", "cf.impairment_plus",
       fc=lambda x: f"={x.a('impairment')}-{x.a('other_op')}")
    cf("cf_oth", "  Other non-cash items, net", "cf.other_noncash", fc=0)
    cf("cf_wc", "  Net changes in operating assets and liabilities", "cf.chg_wc",
       fc=lambda x: (f"=-({x.a('ar')}-{x.pp('ar')})-({x.a('inv')}-{x.pp('inv')})-({x.a('ppcv')}-{x.pp('ppcv')})"
                     f"-({x.a('adv')}-{x.pp('adv')})-({x.a('oca')}-{x.pp('oca')})-({x.a('taxrec')}-{x.pp('taxrec')})"
                     f"+({x.a('app')}-{x.pp('app')})+({x.a('tol')}-{x.pp('tol')})+({x.a('taxpay')}-{x.pp('taxpay')})"
                     f"+({x.a('ocl')}-{x.pp('ocl')})+({x.a('oncl')}-{x.pp('oncl')})"),
       note="Linked to BS: −Δ(receivables, inventory, prepaid consigned vehicle charges, advances, other current assets, "
            "tax receivable) + Δ(auction proceeds payable, trade & other liabilities, taxes payable, other liabilities). "
            "Auction proceeds payable swings with quarter-end auction timing.")
    cf("cfo", "Net cash provided by operating activities", "cf.cfo", style="sub", cagr="cagr",
       fc=lambda x: f"=SUM({x.a('cf_ni')}:{x.a('cf_wc')})")
    cf("cf_capex", "Property, plant and equipment additions", "cf.capex_ppe",
       e26=lambda x: f"=-({x.base(S_CAPEX)}-{x.a('cf_capi')}*-1)+0",
       e=lambda x: f"=-{x.a('total_rev')}*{x.a('capex_pct')}-{x.a('cf_capi')}",
       note="2026E: outlook capex $350–400m (mid $375m; company definition = PP&E net of disposal proceeds + intangible "
            "additions) less intangible additions. 2027E+: revenue × capex % less intangible additions.")
    cf("cf_capi", "Intangible asset additions (capitalised software)", "cf.capex_intangibles",
       fc=lambda x: f"=-{x.a('total_rev')}*{A['capi_pct']}",
       note=f"Capitalised software ~{A['capi_pct']:.1%} of revenue (input).")
    cf("cf_procd", "Proceeds on disposition of PP&E", "cf.proceeds_disp",
       e26=lambda x: f"={x.at('cf_procd','1H/26')}", e=0)
    cf("cf_acq", "Acquisitions, net of cash acquired", "cf.acquisitions",
       e26=lambda x: f"={x.at('cf_acq','1H/26')}", e=0,
       note="2026E = 1H/26 actual (BigIron, $316.6m consideration). No further M&A assumed.")
    cf("cf_oinv", "Other investing activities, net", "cf.other_investing", fc=0)
    cf("cfi", "Net cash used in investing activities", "cf.cfi", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_capex')}:{x.a('cf_oinv')})")
    add(Row(None, style="blank"))
    cf("cf_dissue", "Proceeds from debt (long-term + short-term, net)", "cf.debt_issued_net_plus",
       fc=lambda x: f"=MAX(0,{x.a('debt')}-{x.pp('debt')})")
    cf("cf_drepay", "Repayment of debt", "cf.debt_repaid",
       fc=lambda x: f"=MIN(0,{x.a('debt')}-{x.pp('debt')})",
       note="Net debt issuance / (repayment) = change in total debt per the debt schedule.")
    cf("cf_divc", "Dividends paid to common stockholders", "cf.dividends_common",
       fc=lambda x: f"=-{x.a('dps')}*{x.a('sh_basic')}",
       note="Dividends paid = DPS × weighted-average basic shares.")
    cf("cf_divp", "Dividends paid to Series A preferred / NCI", "cf.dividends_pref",
       fc=lambda x: f"=-{x.a('pref_div')}")
    cf("cf_bb", "Repurchases of common stock", "cf.buybacks",
       e26=lambda x: f"={x.at('cf_bb','1H/26')}-{x.scn(S_BUYB + 1)}",
       e=lambda x: "=-" + x.scn(S_BUYB + 1 + (x.c.year - 2026)),
       note="Share repurchases: 2026E = 1H/26 actual + 2H scenario amount; 2027E+ scenario lever (Buybacks table →).")
    cf("cf_issue", "Issuance of common stock (option exercises, ESPP)", "cf.shares_issued",
       fc=lambda x: A["shares_issued_cash"], input_fc=True)
    cf("cf_wht", "Withholding taxes paid on share settlements", "cf.withholding_tax",
       fc=lambda x: A["wht"], input_fc=True)
    cf("cf_ofin", "Other financing activities, net (incl. debt issue costs)", "cf.other_fin_plus",
       fc=lambda x: f"={x.a('trnci')}-{x.pp('trnci')}",
       note="Forecast = change in redeemable NCI (2026E: VeriTread NCI bought out in 1H/26; finance-lease repayments "
            "assumed offset by new leases).")
    cf("cff", "Net cash provided by (used in) financing activities", "cf.cff", style="sub",
       fc=lambda x: f"=SUM({x.a('cf_dissue')}:{x.a('cf_ofin')})")
    cf("cf_fx", "Effect of exchange-rate changes on cash", "cf.fx_effect", fc=0)
    cf("cf_chg", "Change in cash, cash equivalents and restricted cash", "cf.chg_cash", style="sub",
       fc=lambda x: f"={x.a('cfo')}+{x.a('cfi')}+{x.a('cff')}+{x.a('cf_fx')}")
    cf("cf_beg", "Cash, cash equivalents and restricted cash — beginning", "cf.cash_begin",
       fc=lambda x: f"={x.pp('cf_end')}")
    cf("cf_end", "Cash, cash equivalents and restricted cash — end", "cf.cash_end", style="sub",
       fc=lambda x: f"={x.a('cf_beg')}+{x.a('cf_chg')}",
       note="Pre-2018 the cash-flow statement reconciled unrestricted cash only (ASU 2016-18 adopted 2018).")
    add(Row("cf_chk", "  Check: CFO + CFI + CFF + FX = change in cash (should be 0)", style="check", annual_only=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("cfo")}),ROUND({x.a("cfo")}+{x.a("cfi")}+{x.a("cff")}'
                            f'+N({x.a("cf_fx")})-{x.a("cf_chg")},1),"")') if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None))
    add(Row("cf_memo", "(Memo)", style="line"))
    add(Row("fcf", "Free cash flow (CFO − PP&E additions − intangible additions + disposal proceeds)", style="total",
            annual_only=True, cagr="cagr",
            hist=lambda x: (f'=IF(ISNUMBER({x.a("cfo")}),{x.a("cfo")}+N({x.a("cf_capex")})+N({x.a("cf_capi")})'
                            f'+N({x.a("cf_procd")}),"")') if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None,
            fc=lambda x: f"={x.a('cfo')}+{x.a('cf_capex')}+{x.a('cf_capi')}+{x.a('cf_procd')}",
            note="Consistent with RB Global's capex definition (PP&E + intangible additions, net of disposal proceeds). "
                 "Ritchie Bros. published 'operating free cash flow' on a similar basis."))
    add(Row("fcf_g", "  FCF y/y %", style="growth", fmt=FMT_PCT, annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("fcf")}/{x.py("fcf")}-1,"")' if x.c.kind in ("A", "Y") and x.py("fcf") else None),
            fc=yoy("fcf")))
    for k, lab, f in [("fcf_m", "  FCF % of revenue", lambda x: f'=IFERROR({x.a("fcf")}/{x.a("total_rev")},"")'),
                      ("fcf_conv", "  FCF / adjusted net income conversion %",
                       lambda x: f'=IFERROR({x.a("fcf")}/{x.a("b_adj")},"")')]:
        add(Row(k, lab, style="pct", fmt=FMT_PCT, annual_only=True, cagr="avg",
                hist=lambda x, f=f: f(x) if x.c.kind in ("A", "Y") else None, fc=f))
    add(Row("fcf_ps", "  FCF per diluted share ($)", style="pct", fmt=FMT_EPS, annual_only=True, cagr="cagr",
            hist=lambda x: f'=IFERROR({x.a("fcf")}/{x.a("sh_dil")},"")' if x.c.kind in ("A", "Y") else None,
            fc=lambda x: f'=IFERROR({x.a("fcf")}/{x.a("sh_dil")},"")'))
    add(Row("cx_hdr", "Capex / revenue ratios", style="line"))
    add(Row("capex_pct", "  Capex % of revenue (company definition: PP&E + intangibles − disposal proceeds)",
            style="pct", fmt=FMT_PCT, annual_only=True, cagr="avg", input_fc=True,
            hist=lambda x: (f'=IFERROR(-(N({x.a("cf_capex")})+N({x.a("cf_capi")})+N({x.a("cf_procd")}))/{x.a("total_rev")},"")'
                            if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
            e26=lambda x: f'=IFERROR(-({x.a("cf_capex")}+{x.a("cf_capi")}+{x.a("cf_procd")})/{x.a("total_rev")},"")',
            e=lambda x: A["capex_pct"][x.c.year],
            note="FY26 outlook capex $350–400m. 2027E+ input (yard build-out for IAA/RB co-location, technology)."))
    add(Row("capex_da", "  Capex / D&A (x)", style="pct", fmt=FMT_X, annual_only=True,
            hist=lambda x: (f'=IFERROR(-(N({x.a("cf_capex")})+N({x.a("cf_capi")}))/{x.a("da")},"")'
                            if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
            fc=lambda x: f'=IFERROR(-({x.a("cf_capex")}+{x.a("cf_capi")})/{x.a("da")},"")'))
    add(Row(None, style="blank"))

    # buyback schedule
    add(Row("sec_bb", "SHARE BUYBACK SCHEDULE", style="section"))
    add(Row("bb_px", "  Avg buyback price ($)", fmt=FMT_EPS, annual_only=True,
            e26=lambda x: f"={x.a('px')}", e=lambda x: f"={x.pp('bb_px')}*(1+{x.a('px_g')})",
            note="2026E = current share price ($80, valuation input); appreciates with the share-price input."))
    add(Row("bb_cash", "  Buyback cash deployed (USDm)", annual_only=True,
            e26=lambda x: f"=-({x.a('cf_bb')}-{x.at('cf_bb','1H/26')})", e=lambda x: f"=-{x.a('cf_bb')}",
            note="2026E row = 2H/26 buyback only (1H/26 repurchases already reflected in Q1/Q2 share counts)."))
    add(Row("bb_shares", "  Implied shares repurchased (m)", fmt=FMT_SHR, annual_only=True,
            fc=lambda x: f'=IFERROR({x.a("bb_cash")}/{x.a("bb_px")},0)'))
    add(Row("bb_issued", "  Shares issued under equity plans (m)", fmt=FMT_SHR, annual_only=True,
            fc=A["bb_issued"], input_fc=True))
    add(Row("bb_beg", "  Beginning shares outstanding (m)", fmt=FMT_SHR, annual_only=True,
            e26=lambda x: f"={x.at('sh_out','1H/26')}", e=lambda x: f"={x.pp('bb_end')}"))
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

    flat = lambda k: (lambda x: f"={x.pp(k)}")
    add(Row("sec_bs", "CONSOLIDATED BALANCE SHEET", style="section",
            note="BS FORECAST — first-principles roll-forward (2026E from FY2025 year-end; 1H/26 shown as reported)"))
    add(Row(None, style="blank"))
    add(Row("bs_a", "ASSETS", style="line"))
    add(Row("bs_ca", "Current assets:", style="line"))
    bs("cash", "  Cash and cash equivalents", "bs.cash", fc=lambda x: f"={x.a('cf_end')}-{x.a('rcash')}",
       note="Cash = CF ending cash (incl. restricted) − restricted cash.")
    bs("rcash", "  Restricted cash", "bs.restricted_cash", fc=flat("rcash"))
    bs("ar", "  Trade and other receivables, net", "bs.receivables",
       fc=lambda x: f"={x.a('gtv')}*{x.a('d_ar')}/365", note="Receivables = GTV × days / 365 (buyer balances).")
    bs("ppcv", "  Prepaid consigned vehicle charges (IAA, 2023+)", "bs.prepaid_consigned",
       fc=lambda x: f"={x.a('gtv_auto')}*{x.pp('ppcv')}/{x.pp('gtv_auto')}",
       note="Held at the prior-year ratio to Automotive GTV.")
    bs("inv", "  Inventory", "bs.inventory", fc=lambda x: f"={x.a('cost_inv')}*{x.a('d_inv')}/365")
    bs("adv", "  Advances against auction contracts (legacy)", "bs.advances_auction", fc=flat("adv"))
    bs("taxrec", "  Income taxes receivable", "bs.tax_receivable", fc=flat("taxrec"))
    bs("oca", "  Other current assets (incl. assets held for sale)", "bs.other_current_plus", fc=flat("oca"))
    bs("tca", "Total current assets", "bs.total_ca", style="sub",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("cash")}),SUM({x.a("cash")}:{x.a("oca")}),"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"=SUM({x.a('cash')}:{x.a('oca')})")
    bs("ppe", "  Property, plant and equipment, net", "bs.ppe",
       fc=lambda x: (f"={x.pp('ppe')}-{x.a('cf_capex')}-({x.a('cf_procd')}-{x.a('gain_disp')})"
                     f"-({x.a('adj_da')}-{x.a('capi_amort')})"),
       note="PP&E roll-forward: prior + PP&E additions − net book value of disposals (proceeds − gain) − depreciation "
            "(adjusted D&A less software amortization).")
    bs("rou", "  Operating lease right-of-use assets (2019+)", "bs.rou", fc=flat("rou"))
    bs("onca", "  Other non-current assets (incl. equity-accounted investments)", "bs.other_noncurrent_plus",
       fc=flat("onca"))
    bs("intang", "  Intangible assets, net", "bs.intangibles",
       e26=lambda x: f"={x.pp('intang')}-{x.a('cf_capi')}-{x.a('cf_acq')}*{x.a('acq_intang_pct')}-{x.a('n_AMORT')}-{x.a('capi_amort')}",
       e=lambda x: f"={x.pp('intang')}-{x.a('cf_capi')}-{x.a('cf_acq')}*{x.a('acq_intang_pct')}-{x.a('n_AMORT')}-{x.a('capi_amort')}",
       note="Intangibles roll-forward: prior + software additions + acquired intangibles − acquired-intangible "
            "amortization − software amortization.")
    bs("gw", "  Goodwill", "bs.goodwill", fc=lambda x: f"={x.pp('gw')}-{x.a('cf_acq')}*(1-{x.a('acq_intang_pct')})",
       note="Goodwill + acquisition consideration not allocated to intangibles (BigIron 2026).")
    bs("dta", "  Deferred tax assets", "bs.dta", fc=flat("dta"))
    bs("ta", "TOTAL ASSETS", "bs.total_assets", style="total",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("cash")}),{x.a("tca")}+SUM({x.a("ppe")}:{x.a("dta")}),"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"={x.a('tca')}+SUM({x.a('ppe')}:{x.a('dta')})")
    add(Row(None, style="blank"))
    add(Row("bs_l", "LIABILITIES, TEMPORARY EQUITY & STOCKHOLDERS' EQUITY", style="line"))
    add(Row("bs_cl", "Current liabilities:", style="line"))
    bs("app", "  Auction proceeds payable", "bs.auction_proceeds_payable",
       fc=lambda x: f"={x.a('gtv')}*{x.a('d_app')}/365", note="Auction proceeds payable = GTV × days / 365.")
    bs("tol", "  Trade and other liabilities", "bs.trade_other_liab",
       fc=lambda x: f"={x.a('total_rev')}*{x.a('tol_pct')}")
    bs("cll", "  Current operating lease liabilities", "bs.current_lease_liab", fc=flat("cll"))
    bs("taxpay", "  Income taxes payable", "bs.tax_payable", fc=flat("taxpay"))
    bs("std", "  Short-term debt", "bs.st_debt", fc=flat("std"))
    bs("cltd", "  Current portion of long-term debt", "bs.current_ltd", fc=flat("cltd"))
    bs("ocl", "  Other current liabilities (incl. held for sale)", "bs.other_cl_plus", fc=flat("ocl"))
    bs("tcl", "Total current liabilities", "bs.total_cl", style="sub",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("app")}),SUM({x.a("app")}:{x.a("ocl")}),"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"=SUM({x.a('app')}:{x.a('ocl')})")
    bs("ltd", "  Long-term debt", "bs.ltd", fc=lambda x: f"={x.a('debt')}-{x.a('std')}-{x.a('cltd')}")
    bs("ltll", "  Long-term operating lease liabilities", "bs.lt_lease_liab", fc=flat("ltll"))
    bs("oncl", "  Other non-current liabilities", "bs.other_ncl", fc=flat("oncl"))
    bs("dtl", "  Deferred tax liabilities", "bs.dtl", fc=lambda x: f"={x.pp('dtl')}+{x.a('cf_dtax')}")
    bs("tl", "Total liabilities", "bs.total_liab", style="total",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("app")}),{x.a("tcl")}+SUM({x.a("ltd")}:{x.a("dtl")}),"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"={x.a('tcl')}+SUM({x.a('ltd')}:{x.a('dtl')})")
    bs("tpref", "  Temporary equity — Series A Senior Preferred Shares (2023+)", "bs.temp_pref", fc=flat("tpref"))
    bs("trnci", "  Temporary equity — redeemable non-controlling interest", "bs.temp_rnci",
       e26=lambda x: f"={x.at('trnci','1H/26')}", e=flat("trnci"))
    add(Row("bs_eq", "Stockholders' equity:", style="line"))
    bs("sc", "  Share capital & additional paid-in capital", "bs.share_cap_apic",
       fc=lambda x: f"={x.pp('sc')}+{x.a('cf_sbc')}+{x.a('cf_issue')}+{x.a('cf_wht')}",
       note="Share capital + APIC + SBC + option / ESPP proceeds − withholding taxes.")
    bs("re", "  Retained earnings", "bs.retained_earnings",
       fc=lambda x: (f"={x.pp('re')}+{x.a('ni_ctrl')}-{x.a('pref_div')}+{x.a('cf_divc')}+{x.a('cf_bb')}"),
       note="Retained earnings + NI to controlling − preferred dividends − common dividends − repurchases (RB Global "
            "cancels repurchased shares; excess over stated capital charged to retained earnings).")
    bs("aoci", "  Accumulated other comprehensive income (loss)", "bs.aoci", fc=flat("aoci"))
    bs("eqp", "Stockholders' equity attributable to RB Global", "bs.equity_parent", style="sub",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("sc")}),SUM({x.a("sc")}:{x.a("aoci")}),"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"=SUM({x.a('sc')}:{x.a('aoci')})")
    bs("nci_bs", "  Non-controlling interests", "bs.nci",
       fc=lambda x: f"={x.pp('nci_bs')}+{x.a('nci')}+{x.a('cf_divp')}+{x.a('pref_div')}")
    bs("teq", "Total stockholders' equity", "bs.total_equity", style="total",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("eqp")}),{x.a("eqp")}+N({x.a("nci_bs")}),"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"={x.a('eqp')}+{x.a('nci_bs')}")
    bs("tle", "TOTAL LIABILITIES, TEMPORARY EQUITY AND EQUITY", "bs.total_le", style="total",
       hist=lambda x: (f'=IF(ISNUMBER({x.a("tl")}),{x.a("tl")}+N({x.a("tpref")})+N({x.a("trnci")})+{x.a("teq")},"")'
                       if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
       fc=lambda x: f"={x.a('tl')}+{x.a('tpref')}+{x.a('trnci')}+{x.a('teq')}")
    add(Row(None, style="blank"))
    add(Row("bs_chk", "BS tie-out check (TA − TL, temp. equity & equity)", style="check", annual_only=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("ta")}),ROUND({x.a("ta")}-{x.a("tle")},1),"")'
                            if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
            fc=lambda x: f"=ROUND({x.a('ta')}-{x.a('tle')},1)"))
    add(Row("bs_rep_chk", "  Check: model total assets vs reported (should be 0)", style="check", annual_only=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("ta_rep")}),ROUND({x.a("ta")}-{x.a("ta_rep")},1),"")'
                            if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None)))
    add(Row("ta_rep", "  Memo: total assets as reported", style="memo", src="bs.total_assets_rep", annual_only=True,
            agg="none"))
    add(Row("sh_out", "  Memo: common shares outstanding at period end (m)", style="memo", fmt=FMT_SHR,
            src="bs.shares_outstanding_end", annual_only=True, agg="none", fc=lambda x: f"={x.a('bb_end')}"))

    # ---------------- Working capital ----------------
    add(Row("sec_wc", "WORKING CAPITAL & CASH CONVERSION", style="section",
            note="WORKING CAPITAL — forecast drivers (blue = input)"))
    def wc(key, label, hist, val, note="", fmt=FMT_DAYS):
        add(Row(key, label, style="pct", fmt=fmt, annual_only=True, input_fc=True,
                hist=lambda x: hist(x) if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None,
                fc=(lambda x, v=val: v[x.c.year]) if isinstance(val, dict) else val, note=note))
    days_gtv = lambda k: (lambda x: f'=IFERROR({x.a(k)}/{x.a("gtv")}*365*IF(LEFT("{x.c.key}",2)="1H",0.5,1),"n/a")')
    wc("d_ar", "  Receivable days — receivables / GTV × 365", days_gtv("ar"), A["d_ar"])
    wc("d_app", "  Auction-proceeds-payable days — payable / GTV × 365", days_gtv("app"), A["d_app"],
       note="Year-end auction timing drives large swings in receivables and auction proceeds payable.")
    wc("d_inv", "  Inventory days — inventory / cost of inventory sold × 365",
       lambda x: f'=IFERROR({x.a("inv")}/{x.a("cost_inv")}*365*IF(LEFT("{x.c.key}",2)="1H",0.5,1),"n/a")', A["d_inv"])
    wc("tol_pct", "  Trade & other liabilities % of revenue",
       lambda x: f'=IFERROR({x.a("tol")}/{x.a("total_rev")}/IF(LEFT("{x.c.key}",2)="1H",2,1),"n/a")', A["tol_pct"],
       fmt=FMT_PCT)
    add(Row("nwc", "  Operating NWC (receivables + inventory + prepaid consigned − auction proceeds payable − trade & "
                   "other liabilities)", annual_only=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("ar")}),{x.a("ar")}+N({x.a("inv")})+N({x.a("ppcv")})+N({x.a("adv")})'
                            f'-{x.a("app")}-{x.a("tol")},"n/a")' if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
            fc=lambda x: f"={x.a('ar')}+{x.a('inv')}+{x.a('ppcv')}+{x.a('adv')}-{x.a('app')}-{x.a('tol')}"))
    add(Row("nwc_pct", "  NWC % of revenue", style="pct", fmt=FMT_PCT, annual_only=True, cagr="avg",
            hist=lambda x: f'=IFERROR({x.a("nwc")}/{x.a("total_rev")},"n/a")' if x.c.kind in ("A", "Y") else None,
            fc=lambda x: f'=IFERROR({x.a("nwc")}/{x.a("total_rev")},"n/a")'))
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
    sched("amort_sched", "  Amortization of acquired intangibles (USDm)", A["amort_sched"],
          note=A["amort_note"],
          hist=lambda x: f"=N({x.a('n_AMORT')})" if (x.c.kind in ("A", "Y") and x.c.year >= 2023) or x.c.key == "1H/26" else None)
    sched("capi_amort", "  Amortization of capitalised software (within adjusted D&A, USDm)", A["capi_amort"],
          note="Software amortization (estimate) — splits adjusted D&A between PP&E depreciation and software.")
    sched("acq_intang_pct", "  Acquired intangibles % of acquisition consideration", A["acq_intang_pct"], fmt=FMT_PCT,
          note="BigIron preliminary PPA: intangibles $79.1m of $316.6m consideration (25%).")
    sched("dil_sec", "  Dilutive securities (m shares)", A["dil_sec"], fmt=FMT_SHR)
    sched("dps_g", "  Dividend per share growth %", A["dps_g"], fmt=FMT_PCT,
          note="DPS growth ~6% p.a. (2026 increase $0.31 → $0.33).")
    sched("px_g", "  Share-price appreciation % (buyback pricing)", A["px_g"], fmt=FMT_PCT)
    sched("pref_alloc_pct", "  Earnings allocated to Series A preferred % (two-class)", A["pref_alloc_pct"], fmt=FMT_PCT,
          note="1H/26: allocated earnings $9.4m / (NI to controlling $279.0m − pref. dividends $13.4m) ≈ 3.5%.")
    add(Row("blk_sch2", "Debt schedule", style="block"))
    add(Row("debt", "  Total debt (short-term + current + long-term)", style="sched", annual_only=True, input_fc=True,
            hist=lambda x: (f'=IF(ISNUMBER({x.a("ltd")}),N({x.a("std")})+N({x.a("cltd")})+{x.a("ltd")},"")'
                            if x.c.kind in ("A", "Y") or x.c.key == "1H/26" else None),
            e26=A["debt"][2026], e=lambda x: A["debt"][x.c.year], note=A["debt_note"]))
    add(Row("debt_iss", "  Net issuance / (repayment)", annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("debt")}-{x.py("debt")},"")' if x.c.kind in ("A", "Y") and x.py("debt") else None),
            fc=lambda x: f"={x.a('debt')}-{x.pp('debt')}"))
    add(Row("int_rate", "  Interest rate on average total debt %", style="sched", fmt=FMT_PCT, annual_only=True,
            input_fc=True,
            hist=lambda x: (f'=IFERROR({x.a("interest_exp")}/AVERAGE({x.a("debt")},{x.py("debt")}),"")'
                            if x.c.kind in ("A", "Y") and x.py("debt") else None),
            e26=lambda x: f'=IFERROR({x.a("interest_exp")}/AVERAGE({x.a("debt")},{x.pp("debt")}),"")',
            e=lambda x: A["int_rate"][x.c.year], note=A["int_note"]))
    add(Row("cash_rate", "  Interest income yield on prior year-end cash %", style="sched", fmt=FMT_PCT, annual_only=True,
            input_fc=True,
            hist=lambda x: (f'=IFERROR({x.a("interest_inc")}/{x.py("cash")},"")'
                            if x.c.kind in ("A", "Y") and x.py("cash") else None),
            e26=lambda x: f'=IFERROR({x.a("interest_inc")}/{x.pp("cash")},"")',
            e=lambda x: A["cash_rate"][x.c.year]))
    add(Row("blk_sch3", "Historical reference (driver context)", style="block"))
    add(Row("h_da", "  Total D&A % of revenue", style="pct", fmt=FMT_PCT, cagr="avg", annual_only=True,
            hist=lambda x: f'=IFERROR({x.a("da")}/{x.a("total_rev")},"")' if x.c.kind in ("A", "Y") else None,
            fc=ratio("da", "total_rev")))
    add(Row("h_ppe_g", "  PP&E y/y growth", style="growth", fmt=FMT_PCT, annual_only=True,
            hist=lambda x: (f'=IFERROR({x.a("ppe")}/{x.py("ppe")}-1,"")' if x.c.kind in ("A", "Y") and x.py("ppe") else None),
            fc=lambda x: f'=IFERROR({x.a("ppe")}/{x.pp("ppe")}-1,"")'))
    add(Row(None, style="blank"))

    ratios_rows(R, A)


def ratios_rows(R, A):
    add = R.append
    ann = lambda f: (lambda x: f(x) if x.c.kind in ("A", "Y") else None)

    def rr(key, label, f, style="line", fmt=FMT_NUM, cagr=None):
        add(Row(key, label, style=style, fmt=fmt, annual_only=True, hist=ann(f), fc=f, cagr=cagr))

    add(Row("sec_ratio", "RATIO ANALYSIS", style="section"))
    add(Row("blk_roic", "DuPont decomposition of ROIC", style="block"))
    rr("r_ebit", "Adjusted EBIT (model)", lambda x: f"={x.a('adj_ebit')}")
    rr("r_tax", "Effective tax rate (actual)", lambda x: f"={x.a('etr')}", fmt=FMT_PCT)
    rr("r_nopat", "NOPAT  =  Adj. EBIT × (1 − tax rate)", lambda x: f'=IFERROR({x.a("r_ebit")}*(1-{x.a("r_tax")}),"n/a")')
    rr("r_ic", "Invested capital (IC)  =  Equity + preferred (temp. equity) + Net debt",
       lambda x: f'=IFERROR({x.a("r_eq")}+{x.a("r_nd")},"n/a")')
    rr("r_eq", "  Total equity incl. temporary equity",
       lambda x: f"={x.a('teq')}+N({x.a('tpref')})+N({x.a('trnci')})")
    rr("r_nd", "  Net debt  =  Total debt − Cash (excl. restricted cash & lease liabilities)",
       lambda x: f"={x.a('debt')}-{x.a('cash')}")
    rr("roic", "ROIC  =  NOPAT / IC", lambda x: f'=IFERROR({x.a("r_nopat")}/{x.a("r_ic")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    rr("r_m", "  EBIT margin  =  Adj. EBIT / Revenue", lambda x: f'=IFERROR({x.a("r_ebit")}/{x.a("total_rev")},"n/a")',
       fmt=FMT_PCT)
    rr("r_t", "  Capital turnover  =  Revenue / IC", lambda x: f'=IFERROR({x.a("total_rev")}/{x.a("r_ic")},"n/a")',
       fmt=FMT_X)
    rr("r_tb", "  Tax burden  =  (1 − effective tax rate)", lambda x: f'=IFERROR(1-{x.a("r_tax")},"n/a")', fmt=FMT_PCT)
    rr("r_chk", "  Check: Margin × Turnover × Tax burden  =  ROIC",
       lambda x: f'=IFERROR({x.a("r_m")}*{x.a("r_t")}*{x.a("r_tb")},"n/a")', fmt=FMT_PCT)
    add(Row(None, style="blank"))
    add(Row("blk_ronta", "RONTA decomposition", style="block"))
    rr("t_nopat", "NOPAT  =  Adj. EBIT × (1 − tax rate)", lambda x: f"={x.a('r_nopat')}")
    rr("t_ta", "  Total assets", lambda x: f"={x.a('ta')}")
    rr("t_gw", "  − Goodwill & intangible assets", lambda x: f"=-({x.a('gw')}+{x.a('intang')})")
    rr("t_nibcl", "  − Non-interest-bearing current liabilities (total CL excl. debt)",
       lambda x: f"=-({x.a('tcl')}-N({x.a('std')})-N({x.a('cltd')}))")
    rr("t_nta", "  = Net tangible assets", lambda x: f"=SUM({x.a('t_ta')}:{x.a('t_nibcl')})")
    rr("ronta", "RONTA  =  NOPAT / NTA", lambda x: f'=IFERROR({x.a("t_nopat")}/{x.a("t_nta")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    add(Row(None, style="blank"))
    add(Row("blk_roe", "Return on Equity (ROE)", style="block"))
    rr("e_ni", "Net income available to common", lambda x: f"={x.a('ni_common')}")
    rr("e_eq", "Stockholders' equity attributable to RB Global", lambda x: f"={x.a('eqp')}")
    rr("roe", "ROE  =  NI to common / Equity", lambda x: f'=IFERROR({x.a("e_ni")}/{x.a("e_eq")},"n/a")', style="total",
       fmt=FMT_PCT, cagr="avg")
    add(Row(None, style="blank"))
    add(Row("blk_lev", "Leverage", style="block"))
    rr("l_nd", "Adjusted net debt  =  Short- + long-term debt − cash (company definition)",
       lambda x: f"={x.a('r_nd')}")
    rr("l_ebitda", "Adjusted EBITDA", lambda x: f"={x.a('adj_ebitda')}")
    rr("lev", "Adjusted net debt / adjusted EBITDA (x)", lambda x: f'=IFERROR({x.a("l_nd")}/{x.a("l_ebitda")},"n/a")',
       style="total", fmt=FMT_X)
    add(Row(None, style="blank"))

    add(Row("sec_val", "VALUATION", style="section",
            note="VALUATION — current share price input $80 (per user); applied to 2026E–2030E"))
    add(Row("px", "Share price ($) — current", style="sched", fmt=FMT_EPS, annual_only=True, input_fc=True,
            e26=80, e=lambda x: f"={x.pp('px')}"))
    rr2 = lambda key, label, f, fmt=FMT_NUM, style="line": add(
        Row(key, label, style=style, fmt=fmt, annual_only=True, quarters_ok=False, e26=f, e=f))
    rr2("v_sh", "Diluted shares (m)", lambda x: f"={x.a('sh_dil')}", fmt=FMT_SHR)
    rr2("v_mcap", "Market capitalisation (USDm)", lambda x: f'=IFERROR({x.a("px")}*{x.a("v_sh")},"n/a")')
    rr2("v_nd", "Adjusted net debt (USDm)", lambda x: f"={x.a('l_nd')}")
    rr2("v_pref", "Series A preferred & NCI (temporary equity + NCI, USDm)",
        lambda x: f"={x.a('tpref')}+{x.a('trnci')}+{x.a('nci_bs')}")
    rr2("v_ev", "Enterprise value (USDm)", lambda x: f'=IFERROR({x.a("v_mcap")}+{x.a("v_nd")}+{x.a("v_pref")},"n/a")',
        style="sub")
    add(Row("blk_mult", "Multiples", style="block"))
    for key, lab, f, fmt in [
        ("m_evs", "  EV / Revenue", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("total_rev")},"n/a")', FMT_X),
        ("m_evgtv", "  EV / GTV", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("gtv")},"n/a")', FMT_X),
        ("m_evebitda", "  EV / Adjusted EBITDA", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("adj_ebitda")},"n/a")', FMT_X),
        ("m_evebit", "  EV / Adjusted EBIT", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("adj_ebit")},"n/a")', FMT_X),
        ("m_evic", "  EV / IC", lambda x: f'=IFERROR({x.a("v_ev")}/{x.a("r_ic")},"n/a")', FMT_X),
        ("m_pe", "  P / E (GAAP diluted)", lambda x: f'=IFERROR({x.a("px")}/{x.a("eps_dil")},"n/a")', FMT_X),
        ("m_pea", "  P / E (adjusted, company definition)", lambda x: f'=IFERROR({x.a("px")}/{x.a("b_eps")},"n/a")', FMT_X),
        ("m_fcfy", "  FCF yield", lambda x: f'=IFERROR({x.a("fcf")}/{x.a("v_mcap")},"n/a")', FMT_PCT),
        ("m_dy", "  Dividend yield", lambda x: f'=IFERROR({x.a("dps")}/{x.a("px")},"n/a")', FMT_PCT)]:
        rr2(key, lab, f, fmt=fmt)
