# BA data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed. `tables.py` reads each release's HTML tables positionally (colspan-aware), so a value is assigned to the period header it sits under even when neighbouring cells are empty. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (The Boeing Company, CIK 0000012927; no predecessor registrant in the window). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$BA_SRC/docs`, with text versions in `$BA_SRC/txt` (one table row per line, cells joined by ` | `). Document URLs are recorded in each record's `sources`.
- **Release used:** the 8-K Item 2.02 exhibit that contains a statement of operations and a balance sheet. Preliminary pre-announcements and charge 8-Ks without full statements are skipped (e.g. 15-Jul-2015, 21-Jan-2016, 18-Jul-2019, 11-Oct-2024).
- **XBRL company facts:** `$BA_SRC/cf_12927.json`, subset committed as `data/_xbrl.json`. Used for cross-checks (revenue, net income, total assets) and for treasury shares at the 2017–19 year ends.

## Periods and columns
- **Annual FY2006–FY2025:** the Q4 release's twelve-month columns; balance sheet at 31 December; twelve-month cash flow.
- **Quarters Q1-13 – Q2-26:** the release's three-month column. Q4 comes from the Q4 release's three-month column.
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Columns:** resolved from the group headers ("Three / Six / Nine / Twelve months ended", "Fourth Quarter", "4th Quarter", "Full Year", "First Half") and the year row. When the group-header spans do not overlap the year cells, years are assigned to groups in order (equal consecutive chunks).
- **Balance sheet:** the first date column. Unlabelled total-assets / total-liabilities-and-equity rows (2006–09 releases) are taken as the first / last unlabelled row.

## Units and signs
- USD millions as published; deliveries in units; shares in millions; per share as published.
- **Statement of operations:** costs are negative as presented. `normalize.py` turns costs positive and two-sided lines into income +.
- **Pension line:** `pens_item` = the FAS/CAS service cost adjustment (2018+, income +), or −(unallocated pension + postretirement expense) from the unallocated-items detail (to 2017).
- **Non-operating pension:** `nonop_inc` = −(non-operating pension + postretirement expense), as presented in the core reconciliation (2018+).
- **Separated parentheses:** a "(" sitting in its own cell is merged into the next number (negative). Footnote markers such as "(1)" in the deliveries table are ignored.
- **Nulls:** "—" = 0. A line not presented is omitted. Nothing is estimated. Computed values (Σ sub-segments where no BDS total is printed in 2010–11; FY2011 core from the Q4-12 comparative) are logged by `normalize.py`.

## Record keys
```
period, fy, q, sources{release, release_date, filing}, notes[]
is:          rev_prod, rev_serv, rev, cogs_prod, cogs_serv, bcc_int, tot_costs, opinv, ga, rd, gain_disp, efo, oth_inc, int_exp, ebt, tax, ni_cont, ni,
             nci, ni_attr, pref, eps_b, eps_d, dps, sh_d            (signs as presented)
is_other_lines: [[label, value]]   (unmapped lines between total costs and earnings from operations)
seg:         rev{bca, bds, bma, nss, gss, pems, ss, bgs, bcc, oth, unal, tot}, efo{... , segop, fascas, doj, tot}
unal:        [[label, value]]  unallocated items detail (share-based plans ... pension, postretirement / FAS/CAS ... total)
deliveries:  {737, 747, 767, 777, 787, tot}   (717 = total − Σ programs, 2006)
core_pub:    {core_oe, core_eps, sh_d, fcf}   summary-table values
core_recon:  {item: {usd, ps}} for fascas_pen, fascas_pr, fascas, nonop_pen, nonop_pr, dtax, sub, unal_pp, gaap_eps, core_eps, core_oe, efo, sh
cf:          ytd_months, ni, sbc, dda | dep + amort_int, ar, unbilled, adv, inv, oca, ap, accr, itx, oltl, pens, cfin, cfo, capex, ppe_red, acq,
             inv_contrib, inv_proc, cfi, borrow, repay, opt, bb, div, pref_div, eq_iss, cff, fx, net, beg, end_r (incl. restricted), end
cf_raw / bs_raw: [[label, value]] every line as presented (401(k) treasury shares, dispositions, equity issuance, restricted cash read from here)
bs:          cash, sti, ar, unbilled, cfin_cur, dta_cur, inv, oca_l, tca, cfin, ppe, gw, intang, invest, pens_a, ota_l, ta, ap, accr, adv, itp, std, tcl,
             rhc, pens_l, nc_itp, oltl, ltd, tl, pref_eq, sh_eq, nci_eq, te, tle
backlog:     {bca, bds, bgs, contract, unob, tot}  (USD m; tables published in billions are × 1,000)
py:          the same blocks as presented one year later (restatement detection; FY2011 core figures)
```

## Core reconciliation items (2018+)
| Key | Release label | Sign in the bridge |
|---|---|---|
| fascas_pen / fascas_pr / fascas | Pension / Postretirement FAS/CAS service cost adjustment | deducted (income in earnings from operations) |
| nonop_pen / nonop_pr | Non-operating pension expense / (income); non-operating postretirement expense / (income) | expense added back, income deducted |
| dtax | Provision for deferred income taxes on adjustments (U.S. statutory rate) | as published |
| sub | Subtotal of adjustments ($ and per share) | check |

2011–17: `unal_pp` = unallocated pension / postretirement expense (pre-tax $, first row), plus its after-tax per-share effect (second row). In 2016–17 there are three per-share lines (pension income, postretirement income, deferred taxes). The model derives the tax line as (published core EPS − GAAP EPS) × diluted shares − the pre-tax item.

## Self-checks (`check_data.py`, 1,522 checks)
- **Statement arithmetic:** gross − G&A − R&D + operating investments + gains − other = earnings from operations; + other income − interest = EBT; EBT − tax + disc ops = net earnings.
- **Segments:** Σ segment revenues + unallocated = revenues; Σ segment earnings + unallocated + FAS/CAS = earnings from operations.
- **Core:** earnings from operations − FAS/CAS (or + unallocated pension) = published core operating earnings; subtotal of adjustments = published; core EPS = (EPS numerator + adjustments) ÷ diluted shares (±0.015).
- **EPS:** numerator ÷ diluted shares = published diluted EPS (if-converted numerator in Q4-25).
- **Deliveries:** Σ programs = total.
- **Cash flow:** beginning + change = ending; CF ending cash (ex restricted) = balance-sheet cash; CFO − capex = published FCF.
- **Balance sheet:** total assets = total liabilities and equity; current-asset components sum to total current assets.
- **Quarters vs years:** Σ quarters = year (2013–2025).
- **XBRL:** revenue, net income attributable and total assets vs the as-first-filed facts.
- **Known exceptions (8):** FY2006 EPS denominator; Q4-20 core EPS rounding; FY2017 segment Σ quarters (×6, Global Services formed Q3-17).
