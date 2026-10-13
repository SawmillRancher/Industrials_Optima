# FICO data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `ptab.py` parses the HTML tables of the releases and 10-Q / 10-K documents. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Fair Isaac Corporation, CIK 814547). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$FICO_SRC/docs`, with text versions in `$FICO_SRC/txt` (one table row per line, cells joined by ` | `). `$FICO_SRC/period_index.json` maps each period to its release and periodic report. Document URLs are recorded in each record's `sources`.
- **Release used:** the last Item 2.02 8-K in each quarter's window. Preliminary announcements (16-Apr-2007, 14-Jan-2008, 15-Oct-2013) are superseded by the full release.
- **XBRL company facts:** `$FICO_SRC/cf_814547.json`; the subset is committed as `data/_xbrl.json`.

## Periods and columns
- **Annual FY2006–FY2012:** the 10-K (income statement, balance sheet, cash flow; first value column).
- **Annual FY2013–FY2025:** the Q4 release twelve-month column (income statement, non-GAAP) and the 30-Sep balance sheet and twelve-month cash flow, plus the 10-K for the segment summary, interest split and KPIs.
- **Quarters Q1 FY13 – Q3 FY26:** the release three-month column (column 0); year to date = column 2 (`is_ytd`, `ng_ytd`).
- **10-Q items:**
  - the MD&A segment operating-income summary, split into blocks at each "Operating income" row (block 0 = quarter, block 1 = year to date; column 1 = prior year);
  - the segment-note revenue, matched to each segment column by its operating income;
  - the segment note "unallocated interest / other";
  - the B2B / B2C and platform / non-platform revenue tables.
- **Q4 10-Q items** are derived in `normalize.py` as FY − 9M.
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.

## Units and signs
- USD millions (documents in thousands ÷ 1,000); per share as published; shares in millions.
- Costs positive. Non-operating lines are signed as presented (income +).
- Segment-summary items are stored as presented (reductions of operating income negative); `normalize.py` flips them to costs.
- Non-GAAP items are signed as added to net income.
- "—" or "-" = 0. A line not presented is omitted. Nothing is estimated; computed values (FY − 9M, YTD − prior YTD) are logged by `normalize.py`.

## Record keys
```
period, sources{release, filing}, basis, notes[]
is / is_ytd: rev, rev_lines[[label, v]], cogs, rd, sga, amort, restr, other_op[[label, v]], opinc, nonop[[label, v]], ebt, tax, disc, cont,
             ni, eps_b, eps_d, eps_b_cont, eps_d_cont, sh_b, sh_d, dps
bs:   cash, mkt_cur, mkt_lt, ar, tca, ppe, gw (goodwill + intangibles), ta, ap (+ other accrued), accomp, defrev, std, tcl, ltd, tl, eq, tle, lines[]
cf:   ytd_months, ni, dda, sbc, cfo, capex, capsw, acq, divest, cfi, bb, div, stock, taxw, debt (net of all revolver / term-loan / notes lines),
      cff, fx, net, beg, end, lines[]
ng / ng_ytd: gaap_ni, items[[label, v]], ni_pub, gaap_eps, eps_items, eps_pub, fcf_pub, fcf_lines[[label, v]]
seg / seg_py / seg_ytd / seg_ytd_py: segs[[name, oi]], corp, items[[label, v]], total, opinc, rev[[name, revenue]]
int / int_ytd: int_inc, int_exp, int_net, oth, opinc, ebt
kpi:  {b2b, b2c, plat, nonplat}_{cur, py, py2 | ytd, ytd_py}
```

## Non-GAAP item categories (`normalize.py`)
| Code | Model line | FICO labels |
|---|---|---|
| SBC | Share-based compensation | Stock-based / share-based compensation expense (net of tax to Q2/16) |
| AMORT | Amortization | Amortization of intangible assets |
| RESTR | Restructuring | Restructuring and acquisition-related; restructuring and impairment charges; restructuring charges |
| GAIN | Gains on sales | Gain(s) on product line asset sale(s) and business divestiture |
| NONOP | Excluded non-operating | Realized gain on cost-method investment (FY2018–19) |
| TAX | Income tax adjustments | Income tax adjustments (tax effect of the items) |
| ETB | Excess tax benefit | Excess tax benefit (from FY2017) |
| TAXD | Discrete tax | Adjustment to tax valuation allowance / tax reserves / foreign tax credit; Tax Cuts and Jobs Act |

## Self-checks (`check_data.py`, 1,671 checks, 0 exceptions)
- **Income statement:** revenue − costs = operating income; + non-operating = pre-tax; − tax + disc ops = net income; diluted EPS = NI ÷ shares (±0.015).
- **Segments:** segment summary (segments + corporate − unallocated items) = operating income = income statement; B2B + B2C = Scores; platform + non-platform = on-premises & SaaS; Scores income-statement line = Scores segment.
- **Interest:** the interest split reproduces the income statement's non-operating total.
- **Non-GAAP:**
  - company pre-tax items = model items (pre-tax format periods);
  - non-GAAP EPS = non-GAAP NI ÷ diluted shares;
  - the derived tax effect on items (ex excess tax benefit / discrete) is within 0–45% of the items.
- **Cash flow:** flows = change in cash; BS cash = CF ending cash; FCF (CFO − capex − capitalized software) = published + dividends deducted.
- **Balance sheet:** TA = TL&E; TL + equity = TL&E.
- **Quarters vs years:** Σ quarters = fiscal year for flows, segments, interest, KPIs, non-GAAP NI and FCF (FY2013–25).
- **XBRL** (earliest-filed facts): revenue, operating income, net income, CFO (FY2010+) and total assets, annual and quarterly.
