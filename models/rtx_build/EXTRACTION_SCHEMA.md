# RTX data extraction: schema and rules

<!-- Give this file, unchanged, to every extraction agent. Adapted from the DHR / TDY / WAB / WWD schemas for RTX Corporation
(United Technologies Corporation to 3-Apr-2020, Raytheon Technologies Corporation to 29-Jun-2023). -->

## Sources
- **SEC EDGAR only** (CIK 0000101829). The IR site is blocked; its releases are the 8-K Ex. 99 exhibits.
- **Text versions** of every document are in `$RTX_SRC/txt`: one table row per line, cells joined by ` | `. File names embed
  `<filing date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/101829/<accession-no-dashes>/<doc>.htm`.
  Record those URLs in `sources` (they are given in the period index).
- **Period index:** `$RTX_SRC/period_index.json` maps each period key to `release` (8-K Ex. 99 news release of that quarter; the Q4
  release for annual records), `filing` (10-Q; for Q4 / annual the 10-K — for FY2006–FY2018 the financial statements are in the
  10-K's Exhibit 13 annual report, `ex13_txt`), `next_release` / `next_filing` (the same documents one year later: prior-year
  comparatives), `filing_2y` (annual records: the 10-K two years later) and `q3_filing` (Q4 records). Each entry gives `url` and `txt`.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative. Newer files print "( 1,901 )" with spaces.
  - "—" or "-" alone means zero.
  - Large files (10-K / Exhibit 13, 1–3 MB): grep for the table titles (e.g. `grep -n "Total Assets\|Net cash flows provided by operating"`)
    and read only the lines you need. Release files (20–55 KB) can be read in full.
- **Optional cross-check:** `$RTX_SRC/cf_101829.json` (XBRL company facts; us-gaap concepts such as Revenues, OperatingIncomeLoss,
  NetIncomeLoss, Assets, NetCashProvidedByUsedInOperatingActivities).
- Work only from the local files; do not fetch from EDGAR.

## Basis rules
- **Quarters:** income statement, segment table, non-GAAP bridges and KPIs come from that quarter's release (**three-month** columns),
  **as originally reported**. Q4 = the Q4 release's three-month ("Quarter Ended December 31") column.
- **Annual records:** the Q4 release twelve-month column plus that year's 10-K (Exhibit 13 for FY2006–FY2018). **The 10-K wins** when
  they differ (say so in `notes`). Annual records also carry the 10-K extras (`extra`).
- **Balance sheet:** the period-end statement (release; 10-Q / 10-K if the release lacks a line).
- **Cash flow:** the **year-to-date** statement as presented (`cf.ytd_months` = 3, 6, 9 or 12). UTC releases before 2020 print both a
  quarter and a year-to-date cash-flow column: use the year-to-date column (for Q1 the three-month column is the year to date).
- **Prior-year comparatives (`py`):** the prior-year column as presented in the **next year's** release / filing (the same period one
  year later). Set `py.restated` true with the reason whenever any value differs from what this period's own documents show
  (discontinued operations such as Sikorsky in 2015 and Otis / Carrier in 2020; segment recasts such as RIS + RMD → Raytheon in 2023
  and the 2024 Collins / Raytheon realignment; ASU 2017-07 pension reclassification in 2018; the 2026 presentation that moved
  "Other income, net" into operating costs). This is what makes the model's hybrid recast possible, so fill `py` for every period.
- **Two-step recasts (annual records only, `py2`):** the same income-statement totals, segments and adjusted EPS as presented for this
  year in the 10-K **two years later** (`filing_2y`; e.g. FY2018 as recast for continuing operations in the FY2020 10-K; FY2013 as
  recast ex-Sikorsky in the FY2015 10-K; FY2010 in the FY2012 10-K). Omit if that 10-K does not present the year.
- **Units:** USD millions as published (the statements are already in millions; use the published decimals); shares in millions
  (RTX prints 1,368.1 = 1,368.1 million; UTC prints 998 = 998 million); per-share as published; percentages as numbers in percent
  (3.5 = 3.5%); backlog in USD billions as stated in the text (`_bn` keys).
- **Stock splits:** none in the window; record shares / EPS / DPS exactly as published.
- **Signs:**
  - costs positive (cost of sales, R&D, SG&A, interest expense, tax expense, restructuring in `seg` restr fields);
  - two-sided items **signed by their effect on earnings** (income / gain +, expense / charge −): `other_income`,
    `nonservice_pension`, `other_nonop`, `elim_op`, `corp_op`, `fas_cas`, `acq_acct_adj`, every non-GAAP `item` (pretax and
    after-tax) and every `eps_bridge` entry, `disc_ops`;
  - cash flow as presented (outflows negative);
  - `nci` (noncontrolling / minority interest deducted from net income) positive.
- **Null vs zero:** a line shown as "—" = 0.0. A line not presented = null (or omit the key). **Never estimate.** Any computed value
  (sum, difference, FY − 9M) is stated in `notes`.
- **Presentation changes to respect (record as presented in each period's own documents):**
  - FY2006–FY2008 (pre-SFAS 160): "Minority interests" is deducted above net income; `net_income` is then net of minority interests
    (put minority interests in `nci`, and set `ni_parent` = `net_income`). From 2009 net income includes NCI and
    `ni_parent` = "Net income attributable to common shareowners".
  - Products / services sales and costs are shown separately 2006–2025 (fill `sales_products`, `sales_services`, `cogs_products`,
    `cogs_services`; `cogs` = their sum). 2026 shows one "Cost of sales" line.
  - "Other income, net" is a separate line (income +). "Non-service pension income" is shown below operating profit from 2018
    (income +). Interest: "Interest expense" and "Interest income" separately where shown (both positive), otherwise
    `interest_exp_net` (positive = net expense).
  - Discontinued operations: Sikorsky (classified Q2-15; sold 6-Nov-2015), Otis and Carrier (classified Q1-20; separated 3-Apr-2020),
    earlier UTC disposals (Rocketdyne, Clipper, Hamilton Sundstrand industrial, UTC Power; 2012–13). Record `cont_ops`, `disc_ops`,
    `net_income` and the continuing / discontinued EPS lines as presented.
  - Segments as presented: 2006–2008 Otis, Carrier, UTC Fire & Security, Pratt & Whitney, Hamilton Sundstrand, Sikorsky;
    2012+ UTC Climate, Controls & Security (CCS) replaces Carrier + F&S; UTC Aerospace Systems (UTAS, Goodrich, from Jul-2012)
    replaces Hamilton Sundstrand; Collins Aerospace Systems from Q4-18 (Rockwell Collins, 26-Nov-2018); Sikorsky to Q1-15;
    Otis and Carrier to Q4-19; Raytheon Intelligence & Space (RIS) and Raytheon Missiles & Defense (RMD) Q2-20 to Q4-22;
    Raytheon from Q1-23. Use the exact names as printed.

## Output
One JSON file per period: `models/rtx_build/data/<period_key>.json`. Keys: `2006` … `2025` (annual) and `Q1-13` … `Q3-26`.
Write valid JSON (no comments, no trailing commas). Write it with Python `json.dump(rec, open(path, 'w'), indent=1)` or the
Write tool, then run `python3 models/rtx_build/check_record.py models/rtx_build/data/<period_key>.json` and fix or explain every
failure in `notes`.

```json
{
  "period": "Q2-25", "period_end": "2025-06-30",
  "sources": {"release": "https://...", "filing": "https://...", "next_release": "https://...", "next_filing": "https://...", "filing_2y": "https://..."},
  "is": {
    "sales": null, "sales_products": null, "sales_services": null,
    "cogs": "positive (products + services)", "cogs_products": null, "cogs_services": null,
    "rnd": "positive", "sga": "positive", "other_op_lines": [["exact label", "signed by effect on earnings"]],
    "other_income": "signed: income +", "op_profit": null,
    "nonservice_pension": "signed: income +", "interest_exp": "positive", "interest_inc": "positive", "interest_exp_net": "positive = expense",
    "other_nonop": "signed", "ebt": null, "tax": "positive = expense",
    "cont_ops": "net income from continuing operations incl. NCI", "disc_ops": "signed, incl. NCI", "net_income": "total incl. NCI",
    "nci": "positive = deducted", "nci_cont": null, "ni_parent": null, "ni_parent_cont": null,
    "shares_basic": null, "shares_diluted": null,
    "eps_basic": null, "eps_dil": null, "eps_dil_cont": null, "eps_dil_disc": null,
    "dps": "dividends declared per share in the period (quarter, or year total); from the release, 10-Q or 10-K"
  },
  "seg": {
    "segments": [{"name": "exact", "sales": null, "op_profit": null, "adj_sales": null, "adj_op": null, "restr": "positive = restructuring cost in the segment",
                  "other_items": "signed: other significant items in the segment (income +)", "margin_pct": null, "adj_margin_pct": null}],
    "total_seg_sales": null, "elim_sales": "signed", "elim_op": "signed", "elim_adj_op": null,
    "corp_op": "general corporate expenses / corporate expenses and other unallocated items, signed (negative = cost)", "corp_adj_op": null,
    "fas_cas": "FAS/CAS operating adjustment, signed (2020+)", "acq_acct_adj": "acquisition accounting adjustments, signed (negative; 2020+)",
    "total_seg_op": null, "consol_sales": null, "consol_op": null, "consol_adj_op": null,
    "seg_note": "structure in force / recast wording"
  },
  "cust": {
    "note": "10-Q / 10-K revenue disaggregation (ASC 606, 2018+): exact row labels × segment; include the 'Products' / 'Services' rows and inter-segment sales",
    "<Segment name>": {"<exact row label>": null, "Inter-segment sales": null}
  },
  "kpi": {
    "organic_growth_pct": "consolidated organic sales growth % (release table 'Components of Changes in Net Sales' / 'Organic Sales Reconciliation')",
    "fx_pct": null, "acq_div_pct": null,
    "seg_organic_pct": {"<segment>": null},
    "backlog_total_bn": null, "backlog_commercial_bn": null, "backlog_defense_bn": null, "seg_backlog_bn": {"<segment>": null},
    "defense_bookings_bn": "quarter (release / 10-Q text)",
    "narrative_growth_pct": {"collins_commercial_oe": null, "collins_commercial_aftermarket": null, "collins_defense": null,
                             "pw_commercial_oe": null, "pw_commercial_aftermarket": null, "pw_military": null,
                             "<legacy segment KPI as printed>": null},
    "other": {"<label>": "value as printed, with units in the key"}
  },
  "ngaap": {
    "adj_sales_pub": null, "adj_op_pub": null, "adj_ni_pub": null, "adj_eps_pub": null, "adj_etr_pct_pub": null, "fcf_pub": null,
    "eps_bridge_start": null, "eps_bridge_start_label": "exact",
    "eps_bridge": [["exact label", "per-share value signed by effect on earnings"]],
    "items": [{"label": "exact", "segment": "Collins Aerospace | Pratt & Whitney | Raytheon | Eliminations and Other | Corporate | Consolidated | …",
               "where": "op | nonservice_pension | interest | tax | disc_ops | nci | other_nonop",
               "pretax": "signed $m (income +)", "aftertax": "signed $m if given", "cat": "CAT code"}],
    "restr_total": "total restructuring (pre-tax, positive = cost) as published",
    "acq_acct_adj_total": "signed (negative)", "sig_items_op_total": "signed: total net significant items in operating profit",
    "tax_effect": "signed: tax effect of the items (negative = tax expense added back reverses…) exactly as printed",
    "guidance": "forward outlook text verbatim (sales, organic growth, adjusted EPS, FCF, segment outlooks, tax, interest, pension, capex, shares, buybacks)",
    "definitions": "definition wording of each adjusted measure in this release (what is excluded)"
  },
  "cf": {
    "ytd_months": 6, "ni": null, "dda": null, "deferred_tax": null, "sbc": null, "pension_noncash": "signed as presented",
    "k401_match": null, "pension_contrib": "signed (negative = contribution)", "wc_lines": [["exact label", "value"]], "wc_total": "signed sum of the change-in lines",
    "other_op": null, "cfo": null,
    "capex": "negative", "acq": "negative", "divest": "positive", "other_intang": "negative", "customer_financing": null, "other_inv": null, "cfi": null,
    "debt_issue": null, "debt_repay": "negative", "cp_change": "signed", "st_debt_change": "signed", "dividends": "negative", "nci_dividends": "negative",
    "buyback": "negative", "other_fin": null, "cff": null, "fx": null, "net_change": null,
    "cash_begin": null, "cash_end": null, "restricted_cash": null, "cash_basis": "cash | cash+restricted",
    "disc_ops_cf": {"cfo": null, "cfi": null, "cff": null},
    "lines_raw": [["exact label", "value as shown"]]
  },
  "bs": {
    "cash": null, "ar": null, "contract_assets": null, "inventory": null, "other_ca": null, "tca": null,
    "customer_financing": null, "ppe": null, "rou": null, "goodwill": null, "intangibles": null, "other_nca": null, "ta": null,
    "st_debt": null, "ap": null, "accrued_comp": null, "other_accrued": null, "contract_liabilities": null, "ltd_current": null, "tcl": null,
    "ltd": null, "lease_ltl": null, "pension_obl": null, "other_ncl": null, "tl": null, "redeemable_nci": null,
    "common_stock": null, "treasury": "negative", "retained": null, "aoci": "signed", "equity_parent": null, "nci": null, "te": null, "tle": null,
    "shares_out": "shares outstanding at period end (10-Q / 10-K cover page), millions",
    "lines_raw": [["exact label", "value"]]
  },
  "py": {"restated": false, "reason": null, "source": "next_release / next_filing URL",
         "is": {"same keys as is"}, "seg": {"same keys as seg"}, "cust": {}, "ngaap": {"adj_sales_pub": null, "adj_op_pub": null, "adj_ni_pub": null, "adj_eps_pub": null, "items": []}},
  "py2": {"restated": false, "reason": null, "source": "filing_2y URL", "is": {}, "seg": {}, "ngaap": {}},
  "extra": {
    "employees": null,
    "seg_dda": {"<segment>": null}, "seg_capex": {"<segment>": null}, "seg_assets": {"<segment>": null},
    "backlog_bn": {"<segment or total>": null},
    "debt_maturities": [["year", "$m"]], "amort_schedule": [["year", "$m"]],
    "pension": {"fas_service_cost": null, "cas_expense": null, "fas_cas_adj": null, "nonservice_pension_income": null,
                "contributions": null, "funded_status": null, "expected_return_pct": null, "discount_rate_pct": null},
    "acquisitions": [["name", "close date", "consideration $m", "segment"]], "divestitures": [["name", "date", "notes"]],
    "share_repurchases": {"shares_m": null, "amount_m": null, "authorization_remaining_m": null},
    "notes": null
  },
  "notes": "computed values; any self-check that does not pass and why; anything unusual in the presentation"
}
```

Omit keys that do not exist in the period (do not invent). Keep `lines_raw` for cf and bs (they let the model derive "other" lines).

## Adjusting-item categories (CAT)
| Code | Meaning |
|---|---|
| AMORT | Acquisition accounting adjustments (acquired-intangible amortization, PP&E fair-value amortization, contractual-obligation amortization) |
| ACQ | Acquisition, merger, transaction, separation and integration costs (incl. Otis / Carrier separation, Rockwell Collins, Raytheon merger costs) |
| STEPUP | Inventory step-up and other purchase accounting |
| RESTR | Restructuring (incl. non-service pension restructuring) |
| PENSION | Pension items other than restructuring (curtailments, settlements, mark-to-market) |
| DEBT | Debt extinguishment / early repayment costs |
| GAIN | (Gain) / loss on sale of businesses, investments, product lines; fair-value gains on investments |
| IMPAIR | Impairments and charges (goodwill, intangibles, powder metal / customer bankruptcy / Russia charges, program charges) |
| LEGAL | Litigation, legal matters, DOJ / SEC settlements |
| TAX | Tax effect of the items |
| TAXD | Discrete tax items (tax reform, audit settlements, valuation allowances, tax law changes) |
| NCI | Share attributable to NCI |
| OTHER | Any other item; keep the company's label |

## Self-checks before writing each period (`check_record.py` runs them)
Re-read the source if any of these fail, and report any failure that remains, with the reason, in `notes`.
- **IS:** sales − cogs − rnd − sga + other_income (+ Σ other_op_lines) = op_profit (±1); op_profit + nonservice_pension − interest
  (+ other_nonop) = ebt (±1); ebt − tax = cont_ops (or net_income when no disc ops) (±1); cont_ops + disc_ops = net_income; net_income − nci
  = ni_parent (±1); ni_parent ÷ shares_diluted ≈ eps_dil (±0.015).
- **Segments:** Σ segment sales + elim_sales = consol_sales = is.sales (±1); Σ segment op_profit + elim_op + corp_op + fas_cas +
  acq_acct_adj = consol_op = is.op_profit (±1).
- **Non-GAAP:** eps_bridge_start + Σ eps_bridge = adj_eps_pub (±0.01); adj_ni_pub ÷ shares_diluted ≈ adj_eps_pub (±0.015);
  consol_adj_op = consol_op + restructuring + acquisition accounting adjustments − Σ significant items in operating profit (±1).
- **Cash flow:** cfo + cfi + cff + fx = net_change (±1); cash_begin + net_change = cash_end (±1); cfo = ni + Σ adjustment lines (±1).
- **Balance sheet:** ta = tle (±1); components sum to subtotals (±1); bs.cash = cf.cash_end less restricted cash where the cash-flow
  statement includes restricted cash (note it otherwise).
- **Cust:** Σ customer-type rows = consolidated (external) net sales of the segment; external + inter-segment = segment sales (±1).
