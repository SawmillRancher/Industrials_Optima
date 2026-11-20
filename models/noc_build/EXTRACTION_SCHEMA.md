# NOC data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed:
`parse_release.py` reads the release tables from the text versions of the filings. The rules follow
`templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Northrop Grumman Corporation, CIK 0001133421). The IR site is blocked; its releases are the 8-K Item 2.02
  Ex. 99 / 99.1 exhibits.
- **Raw files** live in `$NOC_SRC/docs`, with text versions in `$NOC_SRC/txt` (one table row per line, cells joined by ` | `; an
  empty cell is dropped, so a row can print fewer cells than the table has columns). Document URLs are recorded in each record's
  `sources`.
- **Release used:** the first 8-K Item 2.02 exhibit for each quarter that carries the consolidated segment table (sales and
  operating income by segment with intersegment eliminations). That makes each period as originally reported.
- **Forms 10-K:** FY2006–FY2008 statements and segment note (no usable release tables for those years); the segment notes of every
  10-K (FY2006–FY2025) for the three-year recast history (`data/_seg_10k.json`).
- **XBRL company facts:** `$NOC_SRC/cf_1133421.json`, subset committed as `data/_xbrl.json`: cross-check values (sales, operating
  income, net earnings, diluted EPS, operating cash flow, total assets, as first filed) and items the releases omit (2009–15
  depreciation & amortization, stock-based compensation, deferred taxes, retiree-benefit cash-flow line; shares outstanding;
  dividends declared per share; current portion of long-term debt from 2013; remaining performance obligations).

## Periods and columns
- **Annual FY2006–FY2008:** own Form 10-K, as originally reported (FY2007–08 XBRL comparatives are the TASC-recast values and are
  not used).
- **Annual FY2009–FY2025:** the fourth-quarter release's twelve-month columns; balance sheet at 31 December; cash flow for twelve
  months.
- **Quarters Q1/13 – Q3/26:** the release's three-month columns. The fourth-quarter releases print only full-year statements, so
  Q4 income-statement lines come from the release's consolidated table (three-month column) and the product / service / G&A
  split is the year less the three reported quarters (`q4_derived`).
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Columns:** resolved from the header with year tokens: layout `['v','v','c','v','v','c']` (value / Change columns); the
  first value block is the quarter and the second the year to date. Rows shorter than the layout are placed greedily (a Change
  column takes a token only when it is marked %, bps or NM, or when more tokens remain than value columns; a marked token never
  fills a value column). Rows whose values are rates are skipped.

## Units and signs
- USD millions as published; per share in $; shares in millions.
- Costs positive in `is`; items in the segment reconciliation and below operating income signed as printed (income +).
- `(524` / `(524)` → −524; `—` → 0. A line not presented is omitted. Nothing is estimated; computed values (Q4 split = FY − ΣQ1–Q3,
  the derived "other" lines) are stated in `notes` or in the normalised keys' names.

## Record keys
```
period, fy, q, period_end, sources{release, release_date, filing}, notes[]
is:    prod_sales, svc_sales, sales, cost_prod, cost_svc, ga, total_costs, other_op[[label, v]], oi, int_exp, int_inc, nonop_fas, mtm,
       other_net, other_nonop[[label, v]], ebt, tax, cont_ops, disc_ops, ni, eps_b, eps_d, eps_b_cont, eps_d_cont, sh_b, sh_d
seg:   sales{segment: v}, elim_sales, total_sales, oi{segment: v}, elim_oi, seg_oi, recon[[label, v]] (FAS/CAS or net pension
       adjustment, unallocated corporate expense and its components, royalty reversal, divestiture items), oi_total,
       below[[label, v]] (interest, pension items, other, EBT, tax, net earnings), layout; FY2006–08: source '10-K segment note'
ng:    [[label, quarter value, year-to-date value, number of value columns]] for every pension-adjusted / MTM-adjusted /
       free-cash-flow / backlog / per-share row (single-value rows are guidance-table rows)
backlog: total_row [funded, unfunded, total, prior total] (schedule) or total_bn_text ($bn, narrative); segments; awards_bn_text
cf:    ytd_months, company lines mapped to ni, dda, sbc, deftax, mtm, gain_sale, b21, pension_inc, pension_contrib, retiree,
       other_noncash, wc_*, cfo (cfo_cont / cfo_disc through 2013), capex, acq, divest, equip, sale_inv, cfi, debt_iss, debt_rep,
       credit, bb, div, tax_withheld, stock_iss, cff, net, beg, end, lines_raw
bs:    cash, ar, unbilled, inv, prepaid, dta_cur, tca, ppe, rou, gw, intang, dta, pension_asset, other_nca, ta, notes_pay, cur_debt,
       ap, accrued_comp, advances, other_cl, tcl, ltd, pension_liab, lease_liab, other_ncl, tl, common, pic, re, aoci, equity, tle, lines_raw
py:    release, seg (segment table comparative as printed one year later), is, ng — realignment and restatement detection
x:     XBRL cross-checks and extras (rev, oi, ni, eps_d, cfo_ytd, ta, sbc_ytd, deftax_ytd, dda_ytd, retiree_ytd, sh_out, dps, rpo,
       amort_intang, ltd_cur, intang_bs, pension_* ...)
guidance: text of the release's guidance section (manual_items.json holds the structured guidance)
```
Auxiliary files: `data/_releases.json` (release index), `data/_seg_10k.json` (10-K segment notes, three years each),
`data/_recast_2018.json` (Q4 2018 release Schedule 6: 2016–17 and Q1–Q3 2018 recast for the MTM accounting change),
`data/_xbrl.json`.

## FY2006–08 10-K cash-flow rows
The direct-method statements and the reconciliation of net income to operating cash flow print three years; a row that is
blank in a year loses that cell in the text conversion, so a short row cannot be placed by position. `extract.resolve_tenk_cf`
uses a row only when it prints all three years, and otherwise places it by consistency with the following filings; rows that
remain ambiguous (acquisitions 2006–08, the 2008 goodwill impairment line) are left blank and absorbed in the derived
"other" lines (noted per record).

## Self-checks (`check_data.py`)
- **Statement arithmetic:** sales − cost of sales − G&A − other operating items = operating income; operating income − interest
  + pension items + other = earnings before taxes; EBT − tax = continuing operations; + discontinued = net earnings; EPS
  (2006–07 diluted EPS adds back dividends on the convertible preferred, derived).
- **XBRL cross-checks** (2009+, as first filed): sales, operating income, net earnings, diluted EPS, total assets, operating cash flow.
- **Segments:** Σ segments + eliminations = sales and = segment operating income (current and legacy structures); segment
  operating income + FAS/CAS + unallocated + divestiture items + royalty reversal + residual = operating income.
- **Non-GAAP:** MTM-adjusted EPS = (net earnings + MTM net of tax) ÷ diluted shares; pension-adjusted EPS = diluted EPS
  (continuing operations in the 2009–12 releases) + after-tax net pension adjustment per share.
- **Cash flow:** components sum to operating cash flow; beginning + change = ending; ending cash = balance-sheet cash (2018–19 cash
  flow includes restricted cash); CFO − capex = published free cash flow (2016+).
- **Balance sheet:** total assets = total liabilities and equity.
- **Quarters vs years** (2013–25) for the main lines. Documented exceptions: the 2019 quarters recast on the 2020 structure sum to
  $3,967m of segment operating income vs $3,978m for the year as recast (company figures; counterpart in unallocated).
