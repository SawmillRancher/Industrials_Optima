# WWD data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `parse_release.py` reads the release tables. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md` (playbook branch).

## Sources
- **SEC EDGAR only** (Woodward, Inc., CIK 108312; "Woodward Governor Company" before Jan-2011). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$WWD_SRC/docs`, with text versions in `$WWD_SRC/txt` (one table row per line, cells joined by ` | `). Document URLs are recorded in each record's `sources`.
- **Release used:** the first full release for each fiscal quarter (statement of earnings + balance sheet + segment schedule). That makes each period as originally reported.
- **XBRL company facts:** `$WWD_SRC/cf_108312.json`, subset committed as `data/_xbrl.json`.

## Periods and columns
- **Annual FY2011–FY2025:** the Q4 release's twelve-month column; balance sheet at 30 September; cash flow for twelve months.
- **Quarters Q1 FY21 – Q3 FY26:** the release's three-month column. Q4 uses the Q4 release's three-month column.
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Columns:** resolved from the table headers to (months, current / prior, measure: pre-tax / net / per share). The positional fallback applies only to balance sheets (current period end first, prior fiscal year end second).

## Units and signs
- USD millions (release thousands ÷ 1,000); per share as published; shares in millions.
- Costs positive.
- `is.int_inc` is negative, as the release presents it (a negative cost); `normalize.py` flips it to income.
- `oth_inc` in the normalised data is other income (+).
- Adjusting items are signed as added back (charges +, gains −).
- "—" or "-" = 0. A line not presented is omitted. Nothing is estimated; computed values (Q4 sales by market = FY − 9M) are stated in `notes`.

## Record keys
```
period, fy, q, sources{release, release_date, filing}, notes[]
is:    rev, cogs, sga, rd, amort (separate line to FY2020), restr, int_exp, int_inc, oth, tot_costs, ebt, tax, ni, nci, eps_b, eps_d, sh_b, sh_d, dps,
       other_lines[[label, value]]   (lines shown separately between sales and total costs, e.g. swap gains)
seg:   sales_aero, sales_ind, earn_aero, earn_ind, nonseg, ebit, int_net, capex, dep, ind_name (Energy / Industrial)
em:    com_oem, com_aft, def_oem, def_aft, aero_tot; pg, trans, og (FY2023 10-K basis) or recip, ind_turb, renew (legacy), ind_tot
em_py / em_py2: the same keys as presented in the following one / two years' filings (recast Industrial markets)
ngaap: ebit_pub, adj_ebit_pub, ebitda_pub, adj_ebitda_pub, dep, amort, fcf_pub, adj_fcf_pub, nonseg_pub, adj_nonseg_pub, adj_seg_*, adj_tax_pub,
       adj{fmt, gaap_ni, gaap_ebt, gaap_eps, items[{label, pre, net, ps, cat}], subtotal, total, adj_ni, adj_ebt, adj_eps}
cf:    ytd_months, cfo, capex, acq, divest, cfi, div, stock_iss, bb, cff, fx, net, beg, end, lines_raw
bs:    cash, ar, inv, tca, ppe, gw, intang, ta, std, cltd, ap, tcl, ltd, tl, eq, tle, lines_raw
x:     sbc_ytd, deftax_ytd, dda_ytd, sh_issued, sh_treasury   (XBRL, as first filed)
py:    release, is, seg, ngaap   (prior-year comparative in the following year's release; detects restatements)
```

## Adjusting-item categories
| Code | Model line | Woodward labels (examples) |
|---|---|---|
| RESTR | Restructuring | Restructuring charges (incl. COVID-19), non-restructuring separation costs, special charges |
| ACQ | Acquisition / business development | L'Orange transaction & integration, warranty & indemnity insurance, German real-estate transfer tax, Duarte move, merger & divestiture transaction costs, business development |
| STEPUP / AMORT | Purchase accounting | L'Orange inventory step-up and backlog amortization |
| GAIN / SWAP | Gains / losses | Gains on property / business sales, product rationalization, cross-currency swap gains |
| IMPAIR | Impairments | Senvion-related assets, assets sold |
| OTHER | Other | Excess & obsolete inventory charge, customer-collections charge, non-recurring matters, stock-compensation acceleration, Forward Option costs |
| TAX / TAXD | Tax effect | Tax effect of adjustments; US tax-reform transition; German corporate tax-rate change |

## Self-checks (`check_data.py`, 724 checks)
- **Statement arithmetic:** sales − costs = earnings before taxes; earnings before taxes − tax = net earnings.
- **Segments and markets:** segment sales sum to consolidated sales; segment earnings + nonsegment expenses = EBIT = published EBIT; primary markets sum to segment sales.
- **Non-GAAP:** EBITDA = EBIT + depreciation + amortization (published); net earnings + items + tax effect = published adjusted net earnings; adjusted EPS = adjusted net earnings ÷ diluted shares (±0.01); adjusted EBIT / EBITDA vs published.
- **Cash flow:** beginning cash + change = ending cash = balance-sheet cash; CFO + capex = published FCF.
- **Balance sheet:** total assets = total liabilities and equity.
- **Quarters vs years:** Σ quarters = fiscal year (FY2021–25).
