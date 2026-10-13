# RBC data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `parse.py` reads the text tables and `period_index.py` maps each period to its documents. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (RBC Bearings Incorporated, CIK 1324948). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$RBC_SRC/docs`, with text versions in `$RBC_SRC/txt` (one table row per line, cells joined by ` | `; whitespace inside a cell is collapsed, because the 2005–2012 filings wrap labels across lines). Document URLs are recorded in each record's `sources`.
- **Period index:** `period_index.py` maps each period to:
  - its release: the latest Item 2.02 8-K filed after the period end and on or before the 10-Q / 10-K;
  - its 10-Q / 10-K;
  - the same documents one year later, for the prior-year comparatives.
- **XBRL company facts:** `$RBC_SRC/cf_1324948.json`, subset committed as `data/_xbrl.json`.

## Periods and columns
- **Fiscal years FY2006–FY2026:** the 10-K statements of operations, balance sheet, cash flow and segment note (current-year column). Non-GAAP reconciliations, selected data and segment sales come from the Q4 release's twelve-month columns (column 3).
- **Quarters Q1 FY13 – Q1 FY27:** the release's three-month column (column 1) for the statement of operations, reconciliations and segment sales. The 10-Q supplies the quarter-end balance sheet, the year-to-date cash flow and the segment note. Q4 uses the Q4 release's three-month column, and Q4 segment-note data = fiscal year − nine months.
- **Prior-year comparatives (`py`):** the next year's release column 2 (quarters) or column 4 (years), and the next filing's segment note. They are used for the Aerospace & Defense / Industrial re-presentation and for the current-definition adjusted EPS of Q1 FY22–Q1 FY23.
- **Column rule:** the first numeric column is the current period in every RBC statement except the FY2006 10-K segment table, which runs oldest-first and is detected by matching the column total to net sales.

## Units and signs
- USD millions. The scale is set per document from the magnitude of statement net sales (or total assets), because unit captions are unreliable in the FY2023–24 documents. Per share as published; shares in millions.
- Costs positive. `onop` is other non-operating expense (+) / income (−), as presented.
- Adjusting items are signed as added back (charges +, gains −). The old-definition net-income items are after tax, as published.
- "—" or "-" = 0. A line not presented is omitted. Nothing is estimated.
- **Blank cells:** `h2t.py` drops blank cells, so a 4-column reconciliation row with 2 values is ambiguous (current-period columns or prior-year columns). `extract.block()` resolves it by the choice that makes the published reconciliation close (Q2 FY15, Q2 FY19).

## Record keys
```
period, fy, q, period_end, sources{release, release_date, filing, filing_form, filing_date}, notes[]
is:    rev, cogs, gp, sga, oth, opex, oi, int, loe, onop, ebt, tax, ni, pref, pref_part, ni_c, eps_b, eps_d, sh_b, sh_d, dps, _scale
ng:    gm{rep, items[[label, value, CAT]], adj}, oi{rep, items, adj}, ni{rep, items, adj, end_label, pref, adj_c, eps_b, eps_d, sh_b, sh_d},
       new{adj_c, items, eps_d, ...} (Q1 FY23 'new adjusted'), cash{...} (Q3-Q4 FY22 'adjusted cash net'),
       ebitda, adj_ebitda, ebitda_rec[[label, value, CAT]], proxy_ebitda (adjusted OI + D&A + incentive stock compensation, Q2 FY16-Q2 FY22),
       sel{dda, sbc, cfo, capex, debt, backlog, bb}, backlog_text, seg_sales{aero, ind | plain, roller, ball, other, eng}, outlook
segn:  sales / cogs / gm / sga / oi -> {aero, ind, corp | plain, roller, ball, other, eng, corp}   (10-Q / 10-K segment note)
segn_ytd: the same, year-to-date column (Q3 records; used for Q4 = FY - 9M)
bs:    cash, sti, ar, inv, tca, ppe, rou, gw, intang, ta, ap, accr, cltd, std, tcl, ltd, tl, pref, teq, tle, lines_raw
cf:    ytd_months, ni, dda | dep + amort, sbc, deftax, cfo, capex, acq, cfi, div, prefdiv, bb, cff, fx, net, beg, end, lines_raw
py:    segn, segn_ytd, seg_sales, ng{oi, ni, adj_ebitda, ebitda, new, gm}, is, source{filing, release}
```

## Adjusting-item categories
| Code | Model line | RBC labels (examples) |
|---|---|---|
| RESTR | Restructuring & consolidation | Restructuring and consolidation; integration and restructuring; plant / facility consolidation; RBC API facility moving costs |
| ACQ | Transaction costs | Transaction and related costs; transition services; acquisition costs |
| STEPUP | Inventory purchase accounting | Inventory purchase accounting adjustment; inventory fair-value step-up |
| LEGAL | Litigation | Litigation reserve; legal settlement |
| GAIN | Disposals | Disposal of fixed assets; gain on sale of Nice building |
| SBC | Stock compensation | Stock options compensation expense (FY2006–07 operating item); stock compensation expense (current-definition EPS add-back) |
| AMORT | M&A amortization | M&A related amortization (current definition) |
| DEBT | Debt items | Loss on (early) extinguishment of debt; amortization of deferred finance fees (current definition) |
| FX | FX translation | Foreign exchange translation loss / (gain) |
| OTHER | Other | Non-recurring compensation and management service fees (FY2006 IPO), CDSOA payment |
| TAX | Tax | Tax impact of adjustments and other tax matters; discrete tax loss / (benefit) |
| PREF | Preferred | Preferred stock dividends; participation rights of preferred stock |

## Self-checks (`check_data.py`, 1,387 checks)
- **Statement arithmetic:** net sales − cost of sales = gross margin; gross margin − SG&A − other, net = operating income; operating income − interest − loss on extinguishment − other non-operating = income before taxes; − tax = net income; (net income − preferred) ÷ diluted shares = diluted EPS.
- **Segments:**
  - Aerospace & Defense + Industrial = net sales;
  - segment gross margins = gross margin;
  - segment operating income + corporate = operating income;
  - legacy segments = net sales.
- **Non-GAAP:**
  - operating income + items = published adjusted operating income;
  - gross margin + items = published adjusted gross margin;
  - adjusted net income available to common ÷ company diluted shares = published adjusted EPS (±0.01);
  - operating income + D&A + stock compensation + items = published adjusted EBITDA (±0.15).
- **Cash flow:** beginning cash + change = ending cash = balance-sheet cash; CFO net income = statement net income.
- **Balance sheet:** total assets = total liabilities and equity.
- **Quarters vs years:** Σ quarters = fiscal year (FY2013–26) for the P&L, segment, bridge and cash-flow lines.
- **XBRL cross-check** (`xbrl_check.py`): sales, operating income, net income, diluted EPS, total assets and CFO vs XBRL facts as first filed, FY2010+: 341 checks, 0 differences.
