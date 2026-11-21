# UPS data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `parse_release.py` reads the release schedules and the 10-K / 10-Q face statements. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (United Parcel Service, Inc., CIK 1090727; no predecessor registrant is needed for 2006+). The IR site is blocked; its releases are the 8-K Ex. 99.1 / 99.2 exhibits.
- **Raw files** live in `$UPS_SRC/docs`, with text versions in `$UPS_SRC/txt` (one table row per line, cells joined by ` | `). File names embed `<date>_<form>_<accession>_<doc>`. Document URLs are recorded in each record's `sources`.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(141" is negative.
  - "—" means zero; "N/A" is kept as null.
  - The Feb-2007 release is fixed-width text; cells are split on runs of two or more spaces.
- **Release used:** the last 8-K Item 2.02 filed in the weeks after the quarter end that carries a "Selected Financial Data" schedule. Pre-announcement 8-Ks without schedules are skipped.
- **Filing used:** the 10-Q (10-K for Q4 and annual records) whose report date is the period end.
- **XBRL company facts:** `$UPS_SRC/cf_1090727.json`, subset committed as `data/_xbrl.json`. Used for annual amortization of intangibles and for cross-checks only.
- **EDGAR requests:** a User-Agent on every request, under 5 per second.

## Periods and columns
- **Annual FY2006–FY2025:** the Q4 release's twelve-month ("Year to Date") schedules plus that year's 10-K.
- **Quarters Q1-13 – Q3-26:** the release's three-month schedules plus the 10-Q (10-K for Q4).
- **Balance sheet:** first column of the face statement (period end).
- **Cash flow:** year to date (`cf.ytd_months` = 3, 6, 9 or 12); `normalize.py` derives discrete quarters.
- **Face income statement:** three-month column in `face_is`, year-to-date column in `face_is_ytd` (used for Q4 operating-expense detail = FY − 9M).
- **Q3-2026:** the 8-K has no Ex. 99.2, so `is`, `ops` and `opex` come from the 10-Q (face statement, MD&A segment tables, earnings-per-share note) and segment / adjusted data from the release narrative tables and reconciliations. The record's `notes` says so.

## Units and signs
- USD millions as published; per share as published; shares in millions; average daily volume in thousands; revenue per piece in dollars.
- `is.int_exp` is positive (expense). `is.inv_inc` and `is.pen_inc` are signed as income.
- Cash flow as presented (outflows negative).
- Nothing is estimated. A line not presented is omitted. Derived values are computed in `normalize.py` and stated there and in the workbook notes.

## Record keys
```
period, fy, q, period_end, sources{release[], release_date, filing, filing_date}, notes[]
is:     rev, rev_us, rev_intl, rev_scs, opex, comp + oth_opex (to 2020) or opex_us / opex_intl / opex_scs (2021+),
        op, op_us, op_intl, op_scs, pen_inc (2018+), inv_inc, int_exp, oth, ebt, tax, ni, eps_b, eps_d, sh_b, sh_d,
        a_op, a_op_us, a_op_intl, a_op_scs, a_oth (2018+), a_ebt, a_ni, a_eps_b, a_eps_d   (as adjusted / non-GAAP adjusted; only when published),
        a_footnotes   (the release's footnote wording for the adjustments)
ops:    rev_<seg>_<product>, rev_<seg>, rev_tot, vol, days, adv_<seg>_<product>, adv_<seg>, adv_tot, rpp_<seg>_<product>, rpp_<seg>, rpp_tot
        us: nda, def, gnd, cargo (2024+) · intl: dom, exp, cargo · scs: fwdlog (to Q3-18), fwd, log, frt (to Q2-21), oth
opex:   comp, rm, da, pt, fuel, occ, othx, opex   (release "Detail of Operating Expenses", 2021+)
recon:  {op | ebt | oth | tax | ni: {gaap, adj, items[[company label, amount as added back]]}}   (reconciliation schedules, where parseable)
adj_notes: footnotes of the reconciliation schedules
ngaap:  fcf_pub_ytd, fcf_disp_ytd   (free-cash-flow reconciliation, year to date)
face_is / face_is_ytd: rev, comp, rm, da, pt, fuel, occ, othx, opex, op, pen_inc, inv_inc, int_exp, oth, ebt, tax, ni, eps_b, eps_d
bs:     cash, ms, ar, tca, ppe, rou, gw, intang, ta, cur_debt, cur_lease, ap, wages, tcl, ltd, nc_lease, pension, dtl,
        apic, re, aoci, eq, nci, teq, tle, sh_a, sh_b   (shares issued by class, from the captions)
cf:     ytd_months, ni, da, pen_exp, pen_contrib, def_tax, sbc, cfo, capex, disp, ms_buy, ms_sell, fin_rec, acq, oth_inv, cfi,
        st_debt, debt_in, debt_out, bb, iss, div, oth_fin, cff, fx, net, beg, end
dps_declared_ytd: "Dividends declared per share" from the filing (year to date)
py:     is, ops   (prior-year columns of the same schedules; used for the Q1–Q3 2024 segment recast)
raw:    bs[[label, value]], cf[[label, value]]   (every face-statement row as shown, for audit)
```

## Adjusting items
UPS's adjusted measures are published as "as adjusted" data (to Q3-2018) and "non-GAAP adjusted" data (after), by segment. The model does not classify items by category:
- **Operating items by segment** = published adjusted segment operating profit − GAAP segment operating profit.
- **Items below operating profit** = (adjusted − GAAP income before taxes) − operating items. From 2018 this is mainly the year-end pension mark-to-market.
- **Tax effect and discrete tax items** = published adjusted net income − net income − pre-tax items.
- **Company wording:** `a_footnotes`, `adj_notes` and `recon.items` carry the labels and amounts; `normalize.py` joins them into `oa_lab`, which the build writes as a cell comment on the total-items row.

## Normalisation (`normalize.py`)
- Basis: as originally reported, with two documented exceptions (FY2020 / Q4-2020 from the 10-K; Q1–Q3 2024 segments from the 2025 prior-year columns).
- Adjusted = GAAP where no adjusted data was published (`adj_pub` = 0); published keys (`aop_pub`, `a_ni_pub`, `a_eps_pub`) exist only in published periods.
- Discrete quarterly cash flow and dividends per share = year-to-date differences.
- "Other" balance-sheet and cash-flow lines are residuals to the reported subtotals.
- Business-disposal proceeds = cash-flow disposal line − PP&E disposals in the free-cash-flow reconciliation, where the difference exceeds $100m.
- Restricted cash memo = cash-flow ending cash − balance-sheet cash. Held-for-sale cash memo = ending − beginning − net change.

## Self-checks (`check_data.py`, 2,357 checks)
- **Income statement:** segment revenue and operating profit sum to the totals; revenue − operating expenses = operating profit; operating profit + other income − interest = income before taxes; − tax = net income; EPS = net income ÷ diluted shares (±0.011); expense lines sum to total operating expenses.
- **Operating data:** product revenue sums to segment revenue; average daily volume by product sums to the segment; volume × revenue per piece × days = product revenue (within the rounding of the published statistics).
- **Adjusted measures:** adjusted segment profit sums to the published total; adjusted EPS = adjusted net income ÷ shares (±0.011).
- **Cash flow and balance sheet:** CFO + CFI + CFF + FX = net change; beginning + change (+ held-for-sale memo) = ending; published free cash flow from 2016; cash-flow D&A = income-statement D&A.
- **Quarters vs years** (2013–2025) and **XBRL cross-checks** (revenue, operating profit, net income, EPS, CFO, total assets).
- **Known exceptions:** published free cash flow for Q1-2025 and FY2025 ($10m, reclassified in the 10-Q).
