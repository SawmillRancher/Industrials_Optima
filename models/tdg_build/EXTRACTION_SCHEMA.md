# TDG data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `tables.py` reads the HTML tables and `parse_filing.py` types them and resolves their columns. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (TransDigm Group Incorporated, CIK 1260221; IPO March 2006). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$TDG_SRC/docs`, with text versions in `$TDG_SRC/txt` (one table row per line, cells joined by ` | `). File names embed `<date>_<form>_<accession>_<doc>`. Document URLs are recorded in each record's `sources`.
- **Release used:** the first 8-K Item 2.02 exhibit for each fiscal quarter that has a statement of income with a thirteen-week column and an EBITDA reconciliation. That makes each period as originally reported.
- **Filing used:** the 10-Q / 10-K for the period (balance sheet, cash flow, segments, end markets, organic sales). The following year's filing supplies the comparatives (`seg_py`, `em_py`); for fiscal years, the filing two years later supplies `seg_py2` / `em_py2`.
- **XBRL company facts:** `$TDG_SRC/cf_1260221.json`, subset committed as `data/_xbrl.json`.
- **EDGAR requests:** a User-Agent on every request, throttled below 5 per second, with retries. A fetched document is rejected if it is an EDGAR "File Unavailable" or rate-limit page.

## Periods and columns
- **Annual FY2006–FY2026:** the Q4 release's fiscal-year column; the balance sheet at 30 September; cash flow for the fiscal year (10-K).
- **Quarters Q1 FY13 – Q4 FY26:** the release's thirteen-week column. Q4 uses the Q4 release's thirteen-week column.
  - Segment, end-market and organic-sales data for Q4 are derived in `normalize.py` as fiscal year − three quarters.
  - Q4 FY2017 / FY2019 organic data are not derived (mixed bases).
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Columns** are resolved from the header rows to (months, current / prior, measure):
  - TransDigm labels periods in weeks: "Thirteen / Twenty-Six / Thirty-Nine / Fifty-Two Week Periods Ended" and "Fiscal Years Ended".
  - Full dates are parsed so that, for example, "December 31, 2011 | January 1, 2011" resolves correctly.
  - Balance sheets are positional (current period end first).
  - ASU 2023-07 segment tables (FY2025+) have segments as columns and the period in the title; they are typed `seg2`.

## Units and signs
- USD millions: documents are in thousands to the FY2019 10-K and in millions from FY2020, with units detected per table. Per share as published; shares in millions.
- Costs positive. `is.other` (other expense (income)) and `is.gain` are signed as expenses (income negative), as presented.
- `is.nci` is negative as presented ("Less: net income attributable to noncontrolling interests"); `normalize.py` flips it.
- `ngaap.adj.div_part` (dividends on participating securities) is negative as presented.
- Adjusting items are signed as added back (charges +, gains −).
- "—" = 0. A line not presented is omitted. Nothing is estimated; computed values (Q4 = FY − 9M) are stated in `notes` / normalisation logs.
- **Short rows:** a row with fewer value cells than columns in the EBITDA reconciliation is right-aligned and logged in `realigned`. The only case is FY2006 "Non-Recurring IPO Costs", proved by Gross Adjustments.

## Record keys
```
period, fy, q, period_end, sources{release, release_date, filing, filing_date}, notes[]
is:          rev, cogs, gp, sga, amort, refin_op (FY2006, inside operating expenses), oi, int_net, refin, other, gain, ebt, tax, ni_cont, disc,
             ni, nci, ni_td, ni_td_cont, ni_common, eps_b, eps_d, eps_cont, eps_disc, dps, sh_b, sh_d, other_op_lines, below_oi_lines, units
is_filing:   the same from the 10-Q / 10-K (cross-check)
ngaap.ebitda: ni, ni_cont, disc, dda, int_net, tax, ebitda_pub, ebitda_label, items[{label, val, cat}], gross_adj, ebitda_ad_pub,
             ebitda_ad_margin_pub, realigned
ngaap.adj:   start, start_label, gross_adj, backlog_amort, tax_adj, items[], adj_ni_pub, adj_eps_pub, eps_div_equiv, div_part,
             sh_common, sh_part, sh_total, sh_adj (adjusted basis), nci
ngaap:       organic_growth_pct, guidance_text, narr_* (release narrative)
seg / seg_py / seg_py2 / seg_9m: pc_, af_, na_, es_ (Esterline, Q2-Q3 FY2019) _sales / _ebitda, seg_sales_tot, seg_ebitda_tot, corp,
             ebitda_ad, dda, int_net, acq, sbc, refin, other, ebt, format (legacy | asu2023-07)
em / em_py / em_py2 / em_9m: pc_coem, pc_caft, pc_def, pc_est (FY2019 as first reported), pc_tot, af_* (same), na, es
organic:     org_sales, acq_sales, rev, rev_py (and *_py)
cf:          ytd_months, ni, dep, amort, amort_debt, refin, gain, sbc, deferred_tax, wc_change, cfo, capex, acq, divest, cfi, stock_proc,
             dividends, buyback, debt_lines, debt_net, cff, fx, net, beg, end, lines_raw
bs:          cash, rcash, ar, inv, tca, ppe, gw, intang, ta, cltd, std, ap, accrued, tcl, ltd, deftax, other_ncl, tl, rnci, eq_td, nci, te, tle,
             shares_issued, shares_treasury (from the equity captions), lines_raw
x:           XBRL as first filed: sbc_ytd, deftax_ytd, dep_ytd, amort_ytd, rev, ni, ta, sh_out, sh_issued, sh_treasury
py:          release, is, ebitda, adj (prior-year comparative in the following year's release)
```

## Adjusting-item categories (EBITDA As Defined)
| Code | Model row | TransDigm labels (examples) |
|---|---|---|
| ACQ / STEPUP | Acquisition & integration | Acquisition-related costs / expenses and adjustments; integration and purchase-accounting adjustments; acquisition transaction and integration-related expenses (incl. inventory step-up) |
| SBC | Stock & deferred compensation | Stock option expense; deferred compensation costs; IPO-related option vesting; non-cash stock (and deferred) compensation expense |
| DEBT | Refinancing | Refinancing costs (and other non-recurring charges, FY2013) |
| RESTR (by label) | Restructuring | COVID-19 & 737 MAX restructuring costs; COVID-19 pandemic restructuring costs |
| GAIN | Gain on sale | Gain on sale of businesses, net |
| OTHER / IMPAIR / IPO | Other, net | Other, net; other nonrecurring items; write-down of PP&E held for sale; public equity offering costs; non-recurring IPO costs; one-time special bonus |
| DISC | Discontinued operations | EBITDA from discontinued operations (FY2011) |

## Self-checks (`check_data.py`, 1,538 checks)
- **Income statement:** gross profit − S&A − amortization − other operating items = income from operations; − interest − refinancing − other expense = pre-tax income; − tax + discontinued operations = net income.
- **Non-GAAP:**
  - EBITDA = continuing operations + tax + interest + D&A (published).
  - EBITDA + items = EBITDA As Defined (published), and items = gross adjustments.
  - Start + gross adjustments + backlog amortization + tax adjustment = adjusted net income (published).
  - Adjusted EPS = adjusted net income ÷ adjusted shares (±0.01; ±0.06 from FY2020).
  - GAAP EPS = (net income attributable − dividends on participating securities) ÷ two-class shares.
- **Segments and markets:** end markets sum to segment sales; organic + acquisition sales = net sales. Segment-basis differences to consolidated figures are reported as information.
- **Cash flow and balance sheet:** beginning cash + change = ending cash = balance-sheet cash + restricted cash; total assets = total liabilities, redeemable NCI and equity.
- **Quarters vs years:** Σ quarters = fiscal year (FY2013–26), with the 18 documented exceptions.
- **XBRL:** revenue and total assets vs the earliest-filed fact (FY2010+).
