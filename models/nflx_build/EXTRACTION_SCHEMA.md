# NFLX data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources; `normalize.py` maps the raw rows to flat model keys. The extraction is scripted, not agent-transcribed. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Netflix, Inc., CIK 1065280; "Netflix.com Inc" to Mar-2002). The investor-relations site is not used; its shareholder letters are the 8-K Item 2.02 Ex. 99.1 exhibits.
- **Raw files** live in `$NFLX_SRC/docs`, with text versions in `$NFLX_SRC/txt` (one table row per line, cells joined by ` | `). Document URLs are recorded in each record's `sources`.
- **Text quirks:**
  - A dropped ")" means "(25,433" is negative.
  - "—" is zero.
  - Values like ".82" (2006–07 releases) are parsed as 0.82.
- **XBRL company facts:** `$NFLX_SRC/cf_1065280.json`, with the subset used committed as `data/_xbrl.json`. It provides cross-checks (revenue, operating income, net income, diluted EPS, CFO, total assets) and shares outstanding (`CommonStockSharesOutstanding`, as first filed).

## Periods and columns
- **Annual FY2006–FY2025:** the 10-K face statements, first column. The FY2006 10-K lists its columns oldest first, so the last column is used there. The 10-K wins over the Q4 letter.
- **Quarters Q1-13 – Q2-26:**
  - Q1–Q3 come from the 10-Q three-month column. The 10-Q income statement runs [3M current, 3M prior, YTD current, YTD prior].
  - Q4 = FY (10-K) − nine months (Q3 10-Q YTD column).
  - Q4 EPS and weighted shares come from the Q4 letter's three-month column, matched on revenue.
- **2018 quarters:** recast basis from the 2019 10-Q prior-year columns. Personnel costs were reclassified effective Q4-2018 (8-K 3-Jan-2019), and the FY2018 10-K and the Q4-18 letter are on the new basis. The originally reported cost lines are kept as `orig_*` keys.
- **Cash flow:** year to date. Recent 10-Qs show [3M, 3M prior, YTD, YTD prior] and older ones [YTD, YTD prior]; the YTD column is chosen by the row width. `normalize.py` derives discrete quarters.
- **Balance sheet:** period end (first column).
- **Statement detection:** each table is found by its first row label ("Revenues", "Cash and cash equivalents", "Net income" after an "operating activities" header). It must contain its subtotal rows, which skips selected-data and MD&A tables.

## Regions and legacy segments
- **Regions (UCAN / EMEA / LATAM / APAC):** revenue, paid net additions, paid memberships at period end, average paying memberships, ARM.
  - FY2017–19 come from the FY2019 10-K, which presents them first.
  - The 2019 quarters come from the 2020 10-Q prior-year columns.
  - Q4 revenue / net additions = FY − 9M.
  - Q4 ARM comes from the Q4 letter regional table.
  - From 2025 Netflix reports revenue by region only.
- **Legacy segments (2011–2019):** Domestic streaming / International streaming / Domestic DVD revenue, cost of revenues, marketing, contribution profit and memberships (10-K tables 2015–17 only).
  - Tables are keyed by their caption (`3-2013`, `9-2013`, `Y-2014`).
  - FY2011 is blank because the FY2011 10-K has the fourth quarter only.
  - Q4 = FY − 9M.

## Published non-GAAP (letters)
- **Free cash flow:** every reconciliation table. The column is matched on the period's net cash from operating activities (±$1.5k; ±$100k with a log entry for restated comparatives, e.g. Q2-13). Items other than CFO and capex go to `fcf_oth` (DVD / content library, intangibles, other assets to 2016; change in other assets 2017–20).
- **Adjusted EBITDA:** letters Q2-15 – Q1-23, plus TTM columns. Each quarter takes its first published value, with the column matched on GAAP net income. The definition is net income + interest and other (income) expense + taxes + non-content D&A + stock-based compensation.
- **Non-GAAP net income / EPS:** 2006 – Q2-10 (excluding stock-based compensation net of tax), Q1-13 (debt extinguishment), Q4-14 and Q4-15 (tax-accrual releases), Q1-15 (foreign-exchange impact). Matched on GAAP net income.

## Units, signs, splits
- USD millions (filings are in thousands ÷ 1,000); per share as published, then split-adjusted; shares in millions.
- Costs are positive. Tax = income before taxes − net income. Interest expense is an absolute value. "Interest and other income (expense)" is signed as income.
- **Splits:** 7-for-1 on 14-Jul-2015 and 10-for-1 on 14-Nov-2025, applied by the source document's filing date: ×70 shares and ÷70 per share before 15-Jul-2015; ×10 / ÷10 before 14-Nov-2025.
- **Null vs zero:** a line not presented is omitted. Nothing is estimated, and computed values (FY − 9M, derived "other" lines) are stated in the code and the workbook notes.

## Record keys (data/<period>.json)
```
period, period_end, form, filed, sources{filing, release[]}, notes[]
is_rows / bs_rows / cf_rows:  [[label, first value, [all values]], ...]  (raw face statements)
release_is:                   Q4 letter income statement (annual records)
seg_tables:                   {'<3|6|9|Y>-<year>': {row: {segment: value}}}
reg, reg_py, reg_9m, reg_9m_py, reg_2017, reg_2018: {region: {rev, netadds, paid, avgpaid, arm}}
letter_reg:                   Q4 letter regional table (ARM, paid memberships; latest quarter)
fcf_tables, ebitda_tables, ngni_tables: [{label: [values by column]}]
```
Normalised keys (`normalize.py`): `rev cor mkt td ga oth_op oi int_exp oth_inc ext ebt tax ni eps_b eps_d sh_b sh_d`; `cf_*` (discrete); `bs_*`; `rg_<region>_{rev,paid,netadds,arm}`; `sg_<dom|int|dvd>_{rev,cor,mkt,cp,mem}`; `camort`; `fcf_pub fcf_oth adj_ebitda_pub ng_ni_pub ng_eps_pub ng_sbc na_fx na_fee oa_restr oa_brazil`.

## Self-checks (`check_data.py`, 1,254 checks, 0 exceptions)
- **Income statement:** revenue − costs = operating income; operating income − interest + other + extinguishment = income before taxes; net income / diluted shares = EPS (split-adjusted, ±0.005).
- **Cash flow:** beginning cash + net change = ending cash; cash-flow net income = net income; balance-sheet cash = cash-flow cash before 2018, when restricted cash entered the cash-flow total.
- **Balance sheet:** TA = TL&E; TL + equity = TL&E.
- **Bridges vs published:** CFO + capex + other items = published FCF; operating income + D&A + SBC = published adjusted EBITDA; net income + items + tax = published non-GAAP net income.
- **Regions and segments:** regions = revenue (2024+; DVD revenue sits outside the regions to 2023); Σ legacy segments = revenue; Σ contribution profit = revenue − cost of revenues − marketing.
- **Quarters vs years:** Σ quarters = FY for the main lines.
- **XBRL (as first filed):** revenue, operating income, net income, total assets, diluted EPS, CFO. FY2007 is skipped because its XBRL facts are the restated FY2008 10-K comparatives.
- **Logged, not failed:** FY2007 published FCF not matched (10-K CFO $291.8m vs release $290.1m); Q2-13 FCF matched within $85k (restated Q1-13 comparative); Q2-13 release capex $8.1m vs filing $8.0m; Q4-14 tax-accrual release sign corrected.
