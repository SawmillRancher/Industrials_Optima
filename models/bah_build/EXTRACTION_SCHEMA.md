# BAH data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `parse_release.py` reads the release exhibits. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Booz Allen Hamilton Holding Corporation, CIK 1443646; no predecessor registrant on EDGAR). The IR site is blocked; its releases are the 8-K Item 2.02 Ex. 99.1 exhibits.
- **Raw files** live in `$BAH_SRC/docs`, with text versions in `$BAH_SRC/txt` (one table row per line, cells joined by ` | `). Document URLs are recorded in each record's `sources`.
- **Release formats:**
  - FY2011 – Q4 FY2019: HTML tables (in USD thousands; a dropped ")" means negative).
  - From Q1 FY2020: a PDF-rendered page whose tables flatten into one text block. The figures are in USD thousands to Q3 FY2025 and USD millions from Q4 FY2025.

  `parse_release.py` tokenises both into entries (label, [numbers]) per exhibit section: statement of operations, balance sheet, cash flows, non-GAAP, operating data.
- **Release used:** each period's own release, so every period is as originally reported. Annual FY2012–FY2026 come from the Q4 release's fiscal-year column; quarters from the three-month column. Cash flow is year to date.
- **10-Q / 10-K:** revenue by customer type (revenue note). Q4 = fiscal year (10-K) − nine months (Q3 10-Q). FY2017–18 come from the FY2019 10-K comparatives.
- **XBRL company facts** (`$BAH_SRC/cf_1443646.json`, subset committed as `data/_xbrl.json`):
  - weighted basic / diluted shares;
  - `UndistributedEarningsDiluted` (two-class earnings for diluted EPS);
  - quarterly deferred taxes and stock-based compensation;
  - shares outstanding;
  - cross-check values (revenue, operating income, net income, diluted EPS, CFO, total assets).

  All are as first filed. Where a quarter is missing from the company facts, the later comparative is used and noted.

## Periods and columns
- **Annual FY2012–FY2026:** Q4 release, fiscal-year column (column index 2 of 4); balance sheet at 31 March; cash flow for twelve months.
- **Quarters Q1 FY2022 – Q1 FY2027:** the release's three-month column (index 0). Cash flow is year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Release-to-period map:** Q1 = July–August, Q2 = October–November, Q3 = January–February, Q4 = May–June filing.

## Units and signs
- USD millions (thousands ÷ 1,000); per share as published; shares in millions; contract-type mix as fractions.
- Costs positive. `is.int_exp` is positive (the release shows it as a negative). `is.oth` is other income (+) / expense (−).
- **NCI income** = net income − net income attributable to common stockholders. The sign of the release's NCI line varies by year, so it is not used directly.
- **Adjusting items** are signed as added back (charges +, gains −).
- "—" = 0; a dash between words ("Cash and cash equivalents — beginning of period") is part of the label. A line not presented is omitted. Nothing is estimated; computed values (Q4 = FY − 9M) are stated in `notes`.

## Record keys
```
period, fy, q, sources{release, release_date, filing, cust}, units, notes[]
is:    rev, cost_rev, bill, ga, da, restr (FY2012), tot_costs, oi, int_exp, oth, ebt, tax, ni, nci (line as shown), ni_common, eps_b, eps_d, dps,
       sh_b, sh_d, earn_dil   (XBRL; Q4 diluted shares from the release)
bs:    cash, ar, tca, ppe, rou, intang, gw, ta, cltd, ap, acc_comp, tcl, ltd, lease_lt, tl, treas, apic, re, aoci, eq, nci_bs, teq, tle
cf:    ytd_months, ni, da, sbc, deftax, cfo, capex, acq, cfi, iss, opt, bb, div, cff, net, beg, end
ngaap: rev_xb_pub, ebitda_pub, ebitda_bridge{start, items, total}, adj_ebitda{start, items[[label, value, CAT]], total}, adj_ebitda_pub,
       adj_oi{...} (to Q3 FY2025), adj_ni{start, items, total}, adj_ni_pub, adj_sh, adj_eps_pub, fcf_pub, twoclass_note
op:    bl_funded, bl_unfunded, bl_options, bl_total, b2b_q, b2b_ytd, hc_total, hc_staff, ct_cr, ct_tm, ct_fp
cust:  def, intel, civ, com (to FY2024), ns, cc (derived when not reported: ns = def + intel; cc = civ + com)
x:     x_rev, x_oi, x_ni, x_eps_d, x_cfo, x_ta, x_sbc, x_deftax, x_dps, x_sh_out   (XBRL, as first filed)
```

## Adjusting-item categories
| Code | Model line | Booz Allen labels (examples) |
|---|---|---|
| ACQ | Acquisition, divestiture, transaction & other corporate expenses | Transaction expenses; Acquisition costs; Acquisition and divestiture costs; Other corporate expenses |
| RESTR | Restructuring | Net restructuring charge (FY2012); Restructuring costs (FY2022) |
| LEGAL | Legal & government-contracting matters | Legal matter reserve; Change in provision for claimed (indirect) costs; Insurance recoveries; DC tax assessment adjustment |
| COVID | COVID-19 | COVID-19 supplemental employee benefits |
| SBC | Carlyle-acquisition stock-based compensation | Certain stock-based compensation expense (FY2012–15) |
| DEBT | Financing transaction costs (operating) / debt costs (non-operating) | Financing transaction costs; Amortization or write-off of debt issuance costs and debt discount; Loss on debt extinguishment |
| AMORT | Acquisition amortization | Amortization of intangible assets (Carlyle); Significant acquisition amortization; Acquisition amortization |
| GAIN | Non-operating gains | Net gain on sale of state and local transportation business; Gain on consolidation of / associated with equity method investment; Gains associated with divestitures; Valuation adjustments to cost method investments |
| TAX / TAXD | Tax effect / discrete tax items | Adjustments for tax effect; Release of income tax reserves; Research and development tax credits; Re-measurement of deferred tax assets / liabilities |

## Self-checks (`check_data.py`, 1,084 checks)
- **Statement arithmetic:** revenue − costs = operating income; operating income − interest + other = income before taxes; − tax = net income; − NCI = net income attributable.
- **Two-class EPS:** earnings for diluted EPS ÷ diluted shares = reported diluted EPS (±0.01).
- **Bridges:**
  - EBITDA (start line + tax + interest & other + D&A) = published;
  - EBITDA + operating items = published adjusted EBITDA;
  - operating income + items = published adjusted operating income;
  - net income + items + tax effect = published adjusted net income;
  - adjusted net income ÷ adjusted shares = adjusted EPS (±0.01);
  - the operating items in each bridge agree with one another;
  - the NCI start-line difference equals NCI income.
- **Other:** revenue ex-billables vs published; free cash flow vs published; customers sum to revenue; backlog components sum to total.
- **Cash and balance sheet:** beginning cash + change = ending cash = balance-sheet cash; total assets = total liabilities and equity.
- **XBRL:** revenue, operating income, net income attributable, diluted EPS, CFO, total assets.
- **Quarters vs years:** Σ Q1–Q4 = fiscal year for FY2022–FY2026 (±0.25, ±2 in USD-million years).
- **Documented exceptions:** FY2017–18 customer revenue (ASC 606 recast basis) and the FY2025 interest / other income / G&A re-presentation.
