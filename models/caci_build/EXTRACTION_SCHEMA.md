# CACI data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources; `supp.py` adds the 10-K / 10-Q and XBRL items. It is scripted, not agent-transcribed: `parse_release.py` reads the release tables. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (CACI International Inc, CIK 0000016058). The IR site is blocked; its releases are the 8-K Ex. 99 / 99.1 exhibits.
- **Raw files** live in `$CACI_SRC/docs`, with text versions in `$CACI_SRC/txt` (one table row per line, cells joined by ` | `; inline-XBRL tags unwrapped). Document URLs are recorded in each record's `sources`.
- **Release used:** the first release for each fiscal quarter (the 8-K/A of 24-Apr-2025 is skipped), so each period is as originally reported.
- **XBRL company facts:** `$CACI_SRC/cf_16058.json` (as first filed).

## Periods and columns
- **Annual FY2006–FY2026:** the Q4 release's twelve-month column; balance sheet at 30 June; cash flow for twelve months.
- **Quarters Q1 FY13 – Q1 FY27:** the release's three-month column (Q4 from the Q4 release).
- **Cash flow:** year to date (`cf.ytd_months`); `normalize.py` derives discrete quarters.
- **Columns:** each data row is resolved to (quarter current, quarter prior, year-to-date current, year-to-date prior) from the header lines; interleaved % change columns are detected.

## Units and signs
- USD millions (release thousands ÷ 1,000); per share as published; shares in millions.
- Costs positive; cash flow as presented; adjusting items signed as added.
- "—" or "-" = 0. A line not presented is omitted. Nothing is estimated; derived values are stated in `notes` or in `normalize.py` comments.

## Record keys
```
period, fy, q, period_end, sources{release, release_date, filing}, notes[]
is:      rev, direct, indirect, da, tot_costs, oi, int_net, ebt, tax, ni_tot, nci, ni, eps_b, eps_d, sh_b, sh_d
cust:    dod (Department of Defense / War), ic (from Q1 FY26), fedciv, comm, state (to FY2013), total
ctype:   cpf, ffp, tm, total      prime: prime, sub, total      exptech: exp, tech, total      dcost: labor, odc, total
orders, awards                    (contract funding orders to FY2019; contract awards from Q3 FY19)
organic: acq, org_rev, base       (published reconciliation, FY2006–FY2013)
ngaap:   ebitda_pub, adj_ebitda_pub, rec_da, rec_int, rec_tax, earnout, prod_adj, fp_adj,
         adj_ni_pub, adj_eps_pub, a_sbc, a_da, a_amfin, a_ncint, a_tax, a_intang, pf_*,
         fcf_cfo, fcf_marpa, fcf_cfo_ex, fcf_capex, fcf_fcf
bs:      cash, ar, oca, tca, gw_int | gw + intang, ppe, rou, srsp_a, ar_lt, onca, ta, cur_debt, ap, accr_comp, ocl, tcl, ltd,
         srsp_l, def_tax, lease_l, oltl, tl, teq, tle, lines_raw
cf:      ytd_months, lines[[label, stage (op / inv / fin / end), value]]
kpi:     backlog_total, backlog_funded (+ quoted text), awards_text, organic_text_pct (+ quote), employees_release
seg:     rev_dom, rev_intl, p_dom, p_intl, measure      (supp.py; 10-K / 10-Q segment note)
x:       amort, gw, intang, sh_out                      (supp.py; XBRL as first filed)
k10:     employees, amort_text, organic_pct (+ quote), gw, intang      (supp.py; 10-K text)
py:      is, cust, ctype, prime, exptech, ngaap, bs, cf   (prior-year comparative in the same release)
raw:     recon rows as parsed
```

## Self-checks (`check_data.py`)
- **Statement arithmetic:** revenue − costs = income from operations; − interest and other = pre-tax income; − tax = net income; EPS.
- **Revenue tables:** customer types, contract types, prime / sub, Technology / Expertise sum to revenue; direct-cost categories to direct costs; segments to revenue and to net income / income from operations.
- **Non-GAAP:** EBITDA bridge vs published; adjusted net income bridge (both definitions) vs published; adjusted EPS (±0.01); free cash flow.
- **Cash flow:** buckets sum to the subtotals; beginning cash + flows = ending cash = balance-sheet cash.
- **Balance sheet:** total assets = total liabilities and equity.
- **Quarters vs years:** Σ quarters = fiscal year (FY2013–26).
- **XBRL:** revenue, income from operations, net income, diluted EPS, CFO and total assets vs company facts (FY2010–26).
