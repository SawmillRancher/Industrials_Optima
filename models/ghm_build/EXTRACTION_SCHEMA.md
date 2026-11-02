# GHM data extraction: schema and rules

Derived from `templates/EXTRACTION_SCHEMA_TEMPLATE.md`. Extraction is scripted (`extract.py` over `parse_release.py`); this file documents what each `data/<period>.json` holds and the rules the scripts apply, so a manual or agent re-extraction produces the same records.

## Sources
- **SEC EDGAR only.** Graham Corporation, CIK 0000716314 (one registrant since listing; no predecessor CIK in the window). The investor-relations site (ir.grahamcorp.com) is not used; its releases are the 8-K Ex. 99.1 exhibits.
- **Documents** are downloaded to `$GHM_SRC/docs` by `fetch.py`, with text versions in `$GHM_SRC/txt`:
  - one table row per line, cells joined by ` | `;
  - file names embed `<date>_<form>_<accession>_<doc>`;
  - a document's URL is `https://www.sec.gov/Archives/edgar/data/716314/<accession-no-dashes>/<doc>`.
- **Releases** are 8-K Item 2.02, Ex. 99.1. From Q2 FY2023 the market, region, orders and backlog tables move to Ex. 99.2 ("Supplemental Information") in USD thousands; the Q4 FY2023 8-K carries them as Ex. 99.3.
- **Filings:** 10-K / 10-Q revenue note ("net sales disaggregated by market and geographic area"), acquisition notes, the intangible amortization schedule and the debt note.
- **XBRL company facts** (`$GHM_SRC/cf_716314.json`; subset committed as `data/_xbrl.json`): cover-page and balance-sheet shares, and cross-checks of revenue, net income, diluted EPS, total assets and CFO.
- **EDGAR requests:** User-Agent on every request, throttled below 5 per second.

## Basis rules
- **Quarters:** statement of operations and non-GAAP tables come from that quarter's release (three-month column), as originally reported.
  - Q4 is the fourth-quarter release three-month column.
  - The 10-Q market table Q4 = FY (10-K) − nine months, only when both use the same market basis.
- **Annual records:** the fourth-quarter release twelve-month columns. FY2006–FY2012 are annual only.
- **Balance sheet:** the period-end statement in the release.
- **Cash flow:** the year-to-date statement (`cf.ytd_months` = 3 / 6 / 9 / 12); discrete quarters are derived in `normalize.py`.
- **Prior-year comparatives (`py`):** the prior-year column of the following year's release (statement, non-GAAP tables, market grids). `normalize.py` uses them for the FY2020 Defense split.
- **Units:**
  - statements in USD thousands → USD millions (÷ 1,000);
  - release grids (orders, backlog, sales by industry / region) are USD millions to one decimal through FY2022 and USD thousands in the supplemental exhibits;
  - FY2011–FY2012 EBITDA tables are in USD millions;
  - shares in millions; per-share as published.
- **Stock splits:** shares and per-share data are recorded exactly as published. `normalize.py` restates releases dated before 3-Jan-2008 ×2.5 and before 6-Oct-2008 ×2.
- **Signs:** costs positive; "other operating expense (income)", "other expense (income)" and net interest expense (income) positive = expense; cash flow as presented.
- **Null vs zero:** a dash = 0.0; a line not presented is absent. Nothing is estimated.

## Record layout (`data/<period>.json`)
```json
{
  "period": "Q1-27", "fy": 2027, "q": 1,
  "sources": {"release": "https://...", "release_date": "YYYY-MM-DD", "exhibits": ["...dex991.htm", "...dex992.htm"], "filing": "https://..."},
  "is": {"rev": 0, "cogs": 0, "cogs_amort": 0, "gp": 0, "sga": 0, "sga_amort": 0, "restr": 0, "impair": 0, "oth_op": 0, "op_profit": 0,
         "int_inc": 0, "int_exp": 0, "int_net": 0, "oth_nonop": 0, "ebt": 0, "tax": 0, "cont_ops": 0, "disc_ops": 0, "ni": 0,
         "eps_b": 0, "eps_d": 0, "sh_b": 0, "sh_d": 0, "dps": 0, "other_op_lines": [["label", 0]], "nonop_lines": [["label", 0]]},
  "ngaap": {"ebitda": {"start": 0, "int": 0, "tax": 0, "dda": 0, "ebitda": 0, "adj_ebitda": 0, "items": [["exact label", 0, "CAT"]], "unit": "k|m"},
            "adjni": {"start": 0, "items": [["exact label", 0, "CAT", "net_of_tax?"]], "adj_ni": 0, "gaap_eps": 0, "adj_eps": 0, "sh_d": 0},
            "adjop": {"start": 0, "items": [], "adj_op": 0}},
  "kpi": {"orders": 0, "backlog": 0, "sales_mkt": {"defense": 0, "space": 0, "ep": 0, "refining": 0, "chem": 0, "power": 0, "other": 0},
          "orders_mkt": {}, "backlog_mkt": {}, "sales_reg": {"us": 0, "mideast": 0, "asia": 0, "other": 0}},
  "mkt_note": {"defense": 0, "space": 0, "ep": 0, "total": 0},
  "cf": {"ytd_months": 3, "ni": 0, "dep": 0, "amort": 0, "pens_amort": 0, "sbc": 0, "deftax": 0, "gain_ppe": 0, "cont_cons": 0, "cfo": 0,
         "capex": 0, "capex_proc": 0, "acq": 0, "inv_purch": 0, "inv_red": 0, "cfi": 0, "debt_borrow": 0, "debt_repay": 0, "fin_lease": 0,
         "div": 0, "stock_iss": 0, "stock_cost": 0, "withhold": 0, "bb": 0, "cff": 0, "fx": 0, "net": 0, "beg": 0, "end": 0, "lines_raw": []},
  "bs": {"cash": 0, "invest": 0, "ar": 0, "unbilled": 0, "inv": 0, "tca": 0, "ppe": 0, "pension_asset": 0, "rou": 0, "gw": 0, "intang": 0, "ta": 0,
         "std": 0, "ap": 0, "accr_comp": 0, "accr_oth": 0, "deposits": 0, "oplease_cl": 0, "tax_pay": 0, "tcl": 0, "ltd": 0, "oplease_ncl": 0,
         "tl": 0, "eq": 0, "tle": 0, "lines_raw": []},
  "py": {"release": "https://...", "is": {}, "ngaap": {}, "kpi": {}},
  "x": {"sh_cover": {"shares": 0, "date": ""}, "sh_issued": 0, "sh_treasury": 0, "sh_out": 0, "rev": 0, "ni": 0, "eps_d": 0, "ta": 0, "cfo_ytd": 0},
  "notes": []
}
```

## Market and KPI keys
- **Current basis** (FY2025 10-K onward): `defense`, `space`, `ep` (Energy & Process).
- **Legacy industry split:** `refining`, `chem` (chemical / petrochemical), `power` (incl. nuclear), `defense` (separate from FY2017), `space` (from FY2022), `other`. The `other` label changed: "Other Commercial and Industrial (incl. NNPP)"; "Other Commercial, Industrial and Defense" FY2015–19.
- **Orders and backlog** come from the release trend tables; Defense / Space / Energy & Process splits are available from FY2022 (orders) and FY2023 (backlog).

## Adjusting-item categories (CAT)
| Code | Meaning | Model bucket |
|---|---|---|
| ACQ | Acquisition & integration (incl. contingent earn-out fair value changes) | acq |
| STEPUP | Acquisition-related inventory step-up | acq |
| AMORT | Amortization of intangible assets (adjusted net income only, FY2022+) | amort |
| RESTR / TRANS | Restructuring, CEO / CFO severance and transition | restr |
| IMPAIR / BADDEBT / GAIN | Goodwill & intangible impairments; nuclear bad debt; loss on sale and operating loss of the commercial nuclear utility business | impair |
| ERP | ERP implementation costs | erp |
| SBC | Equity-based compensation (Adjusted EBITDA only, from Q4 FY2024) | sbc |
| BNBONUS / DEBT / ERC / OTHER | Barber-Nichols performance bonus, debt amendment costs, ERC tax credit, other | oth |
| TAX | Tax effect / normalized tax rate | tax |
| TAXD | US tax-law impact (FY2018) | taxd |

## Self-checks (`check_data.py`, 1,679 checks, all pass)
- **Statement arithmetic:** GP − SG&A − amortization − restructuring − impairment − other = operating profit; − net interest − other = EBT; − tax (+ disc ops) = net income (±0.0011).
- **EPS:** NI ÷ diluted shares = diluted EPS (±0.01; split-adjusted FY2006–08 ±0.006 after restatement).
- **Non-GAAP:**
  - NI + net interest + tax + D&A = published EBITDA;
  - EBITDA + items = published Adjusted EBITDA (±0.0011; ±0.16 for USD m tables);
  - NI + items = published adjusted net income;
  - adjusted NI ÷ shares = adjusted EPS;
  - operating profit + items = adjusted operating profit.
- **Markets and regions:** Σ = net sales (exact for USD thousand sources; ±0.36 for USD m grids).
- **Cash and balance sheet:** beginning cash + net change = ending cash; CF ending cash = BS cash; TA = TL&E; component sums.
- **XBRL:** revenue, net income, diluted EPS, total assets and annual CFO match the earliest-filed facts.
- **Quarters vs year:** Σ Q1–Q4 = FY for P&L, cash-flow, orders and market lines (FY2013–FY2026).
