# SPGI data extraction: schema and rules

Each earnings release (Form 8-K Item 2.02, Ex. 99.1) is transcribed to one JSON per period, `data/<period>.json`. The rules follow `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. The face statements are also taken from XBRL company facts (`xbrl.py`), and the release values are cross-checked against them in `check_data.py`.

## Sources
- **SEC EDGAR only.** S&P Global Inc., CIK 64040 (McGraw Hill Financial, Inc. May-2013 to Apr-2016; The McGraw-Hill Companies, Inc. before). The investor-relations site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$SPGI_SRC/docs`, with text versions in `$SPGI_SRC/txt` (one table row per line, cells joined by ` | `; a dropped `)` means the number is negative, e.g. `(25 |` = −25; `—` = 0).
- **Release used:** the period's own release (as originally reported). The 2025 and 1H-2026 periods without Mobility come from the 6-Jul-2026 8-K/A (Ex. 99.1 recast / pro forma) and the Q2-2026 release (Exhibits 5–6); they are entered in `manual_items.json` (`recast_2025_26`), not in the per-period files.

## Periods and columns
- **Quarter files** `Q<q>-<yy>.json`: the release's three-month column. Q4 uses the Q4 release's three-month column.
- **Annual files** `<yyyy>.json`: the Q4 release's twelve-month column (FY2011 = the comparative in the Q4-2012 release, continuing operations after the McGraw-Hill Education sale; FY2010 = the FY2012 10-K).
- **Cash flow:** year to date as presented (`cf.ytd_months` = 3, 6, 9 or 12).

## Units and signs
- USD millions as published; per share as published; shares in millions.
- Costs positive. Income lines (`gain_disp`, `eq_inc`, `oth_inc`, `disc`) are positive when they add to profit, whatever the release sign.
- `int` = net interest expense (positive = expense).
- Adjusting items are signed as added back to GAAP (charges +, gains −).
- "—" = 0. A line not presented is omitted (null). Nothing is estimated; computed values are stated in `notes`.

## Record keys
```
period, fy, q, sources{release, release_date, doc}, notes[]
is:    rev, exp (total expenses), op_rel, sga, dep, amort, da (if only combined), gain_disp, eq_inc, op, oth_inc, int, ebt, tax,
       ni_cont, disc, ni, nci, ni_attr, ni_attr_cont, eps_b, eps_d, eps_d_cont, sh_b, sh_d, sh_end
seg:   [{name (as published), code, rev, exp, op, nongaap (pre-tax items in segment OP, add-back sign), deal_amort, adj_op}]
       code: RAT Ratings | IDX Indices (S&P DJI) | CI Platts / Commodity Insights / Energy | MI Market Intelligence |
             CIQ S&P Capital IQ (2013-15) | CC Commodities & Commercial (2013-15) | MCI Market & Commodities Intelligence (2016-17) |
             MOB Mobility | ES Engineering Solutions | OTH other
seg_other: elim (intersegment elimination, negative), corp (unallocated expense, positive cost), corp_nongaap, corp_deal_amort, adj_corp,
       eq_inc, adj_eq_inc, seg_op_total, adj_seg_op_total
ngaap: adj_op, adj_ni, adj_eps, start_ni, start_eps, start_basis ('cont' | 'total'), items[{label, seg, pre, net, ps, cat}],
       deal_amort_pre, deal_amort_net, deal_amort_ps, adj_tax, adj_int, adj_oth_inc, definition (headline wording)
cfpub: ytd_months, cfo, capex, nci_dist, fcf_pub, fcf_items[{label, amount}], adj_fcf_pub
organic: rev_cc_organic_growth_pct (published, if any), organic_rev, organic_rev_cc
guidance (Q4 / updated quarters): [{item, low, high, basis}]
```

## Adjusting-item categories
| Code | Model line | SPGI labels (examples) |
|---|---|---|
| SEVER | Restructuring / severance | Employee severance charges, restructuring, Executive Leadership Team transition costs, employee-related costs |
| ACQ | Acquisition / merger / integration | IHS Markit merger costs, acquisition-related costs, Kensho / SNL / With Intelligence integration |
| DISP | Disposition-related costs | Disposition-related costs, Mobility separation costs |
| GAIN | (Gain) / loss on dispositions | Gain on dispositions, loss on sale, business-sale gains (sign: gain negative) |
| LEGAL | Legal settlements / costs | Legal settlement expenses, insurance recoveries, legal costs |
| IMPAIR | Impairments | Asset / lease / technology impairments, goodwill / intangible impairments |
| OTHER | Other operating items | Labor-law accrual, non-cash acquisition / disposition adjustments, other |
| EQ | Equity-method items | Equity in income adjustments (OSTTRA) |
| NONOP | Below operating profit | Premium amortization benefit (interest), pension settlements, investment gains / losses in other income |
| TAX | Discrete tax items | Tax-reform effects, divestiture tax, tax on gains |

Deal-related amortization is recorded separately (`deal_amort_*`), never as an item.

## Self-checks (`check_data.py`)
- **Statement arithmetic:** revenue − expenses + gains + equity income = operating profit; OP + other income − interest = EBT; EBT − tax = NI; NI − NCI = NI attributable.
- **Segments:** Σ segment revenue + elimination = revenue; Σ segment OP − unallocated (+ equity income where separate) = OP; segment OP + items + deal amortization = adjusted segment OP.
- **Non-GAAP:** start NI + Σ items (after tax) + deal amortization (after tax) = adjusted NI; adjusted NI ÷ diluted shares = adjusted EPS (±0.01).
- **Quarters vs years:** Σ quarters = year for flows (exceptions noted).
- **XBRL cross-check:** revenue, OP, NI attributable, diluted EPS, CFO and total assets vs the earliest-filed XBRL fact.
