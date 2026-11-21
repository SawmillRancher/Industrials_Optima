# HWM data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `parse_release.py` splits each release into its schedules and reads rows by label. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Howmet Aerospace Inc., CIK 4281; Arconic Inc. to 31-Mar-2020). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$HWM_SRC/docs`, with text versions in `$HWM_SRC/txt` (one table row per line, cells joined by ` | `, whitespace inside a cell collapsed). Document URLs are recorded in each record's `sources`.
- **Release used:** the release that first reported the quarter, which makes each period as originally reported.
- **Forms 10-Q / 10-K:** end-market revenue note only.
- **XBRL company facts:** `$HWM_SRC/cf_4281.json`, subset committed as `data/_xbrl.json`. Used for cross-checks, not as a primary input.

## Periods and columns
- **Quarters Q2-20 – Q3-26:** the first value column of the release statements (current quarter); balance sheet at the quarter end; cash flow year to date.
- **Years 2020–2025:** the full-year statement of the fourth-quarter release.
- **Q1-20:** prior-year column of the Q1-21 release (recast continuing operations). No balance sheet.
- **FY2019:** prior-year column of the Q4-20 release. No balance sheet or cash flow.
- **H1-20 cash flow:** prior-year column of the Q2-21 release (as revised in Q3-20).
- **Segment panels:** every release prints 5–10 periods headed `1Q25 | 2Q25 | … | 2025`. A period takes the values of its own release; values a later release prints differently are kept as `<key>_rc` (recast detection), and keys only a later release has (Segment Adjusted EBITDA for 2021) are listed in `_from_later`.
- **Reconciliation tables:** column layouts drift (quarter / year-to-date blocks, dates or `3Q25` labels). The column is chosen by value: the one whose anchor row (net income, operating income or operating cash flow) equals the period's own reported figure.

## Units and signs
- USD millions as published (whole millions); per share as published; shares in millions (releases to 2023 print units, which are divided by 1,000,000).
- Costs positive. Special items are signed as added back (charges +, credits −). Cash flow as presented.
- "—" = 0. A line not presented is omitted. Nothing is estimated; computed values (Q4 end markets = year − nine months; FY2019–20 total EPS = continuing + discontinued) are stated in `notes`.

## Record keys
```
period, year, q, sources{release, release_date, filing}, notes[]
is:    rev, cogs, sga, rd, da, restr, oi, loss_debt, int, oth, ebt, tax, cont, disc, ni,
       eps_b, eps_d, eps_b_cont, eps_d_cont, sh_b, sh_d, sh_out, eps_total_computed
seg:   <ep|fs|es|fw>_{tps, inter, da, op, ebitda, restr, capex}, tot_op, tot_ebitda, seg_da, corp, unalloc_restr, oi, *_rc, _from_later
ngaap: adj_oi, oi_items[[label, value]], adj_ebitda, ebitda_pre_special, adj_ni, adj_eps, adj_sh, items[[label, value]],
       fcf, fcf_label, fcf_lines, organic{segment: {py_sales, py_ad, py_org, sales, ad, org, g, g_org}}
em:    ca (commercial aerospace), df (defense aerospace), aero, ct (commercial transportation), io (industrial and other), gt (gas turbines), og, gi, oth, tot
cf:    ytd_months, ni, da, deftax, restr, sbc, pension_cost, pension_contrib, cfo, capex, acq, divest, sold_rec, cfi,
       st_change, debt_add, debt_pay, debt_costs, debt_prem, options, tax_withheld, pref_red, arconic, div, bb, cff, fx, net, beg, end
bs:    cash, ar, oth_rec, inv, prepaid, disc_ca, tca, ppe, gw, dta, intang, onca, disc_nca, ta, ap, accr_comp, taxes, accr_int, defrev, ocl,
       std, cltd, disc_cl, tcl, ltd, pension, opeb, oncl, disc_ncl, tl, pref, common, apic, re, aoci, nci, teq, tle
x:     dps_decl   (XBRL dividends declared per share; information only)
```

## Special items → model lines
Howmet reconciles "special items" in three tables. `normalize.py` maps them to four model lines and keeps the company labels as cell comments.

| Model line | Derivation | Company labels (examples) |
|---|---|---|
| Restructuring and other charges | Statement of operations line | Severance, asset impairments, pension settlements, gains / losses on asset sales (Savannah $93m gain, Q1-26) |
| Other operating special items | Published adjusted operating income (or Adjusted EBITDA) − operating income − restructuring | Arconic separation costs, plant fire costs / reimbursements, Grenfell Tower legal costs, closures and supply-chain items, collective bargaining, acquisition and acquisition-related costs |
| Non-operating special items | Pre-tax special items in the adjusted-net-income table − operating special items | Loss on debt redemption, new financing and tender fees, separation interest, legal settlement |
| Tax impact & discrete tax items | Published adjusted net income − income from continuing operations − pre-tax special items | Tax impact of pre-tax special items, discrete and other tax special items, allocation adjustments |

## Self-checks (`check_data.py`, 924 checks)
- **Statement arithmetic:** sales − costs = operating income; operating income − interest − loss on debt − other = income before taxes; − tax = continuing operations; + discontinued = net income (±1–2, whole-million rounding).
- **Segments and markets:** segment sales sum to consolidated sales; Σ Segment Adjusted EBITDA = published total; end markets sum to the disclosed total and to sales.
- **Non-GAAP:** adjusted operating income + D&A − items in D&A = Adjusted EBITDA; continuing operations + special items = published adjusted net income; adjusted EPS = adjusted net income ÷ shares (±0.01; FY2019 ±0.02).
- **Cash flow:** beginning cash + change = ending cash; cash from operations − capex (+ receipts from sold receivables to 2021) = published free cash flow.
- **Balance sheet:** total assets = total liabilities and equity; restricted cash = cash-flow cash − balance-sheet cash.
- **Quarters vs years:** Σ quarters = year for 2020–2025 (±2; 2020 cash flow and end markets ±4).
- **XBRL cross-check (190 checks):** sales, operating income, net income, diluted EPS, year-to-date operating cash flow, total assets and cash vs the 10-K / 10-Q facts as first filed.
