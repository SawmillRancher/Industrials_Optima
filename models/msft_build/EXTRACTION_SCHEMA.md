# MSFT data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `tables.py` reads the HTML tables cell by cell, and statements are identified by their row content (headings sometimes sit in a preceding table or inside the table). The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Microsoft Corporation, CIK 0000789019). The IR site is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw files** live in `$MSFT_SRC/docs` (text versions in `$MSFT_SRC/txt`). Document URLs are recorded in each record's `sources`.
- **Release used:** the quarter's own earnings release (8-K Item 2.02, Ex. 99.1), so each period is as originally reported. FY2006–FY2012: the 10-K (the releases of that era carry no financial tables before FY2008 and the 10-K wins in any case).
- **XBRL company facts:** `$MSFT_SRC/cf_789019.json`, subset committed as `data/_xbrl.json`.
- **FY27-basis history:** `recast27.py` parses the 8-K of 2-Sep-2026 (slide text; label followed by ten numbers) into `data/_recast27.json`.
- **Non-GAAP:** the release reconciliation layouts vary by era (vertical "YYYY As Reported / items / As Adjusted" rows; horizontal As Reported / Impact / As Adjusted columns in FY2026), so the bridges are curated in `ngaap.json` from the release tables, with source URL and basis per period, and verified arithmetically.

## Periods and columns
- **Annual FY2006–FY2012:** 10-K Item 8 (current-year column); segment note revenue and operating-income tables.
- **Quarters Q1 FY13 – Q4 FY26:** the release's three-month columns (income statement, cash flow, segments) and the quarter-end balance sheet.
- **Annual FY2013–FY2026:** the Q4 release twelve-month columns (cross-checked to the 10-K XBRL facts).
- **Prior-year comparatives (`py`, `seg_py`):** the prior-year columns of the same release.

## Units and signs
- USD millions as published; shares in millions; per share as published.
- Costs positive as presented; other income (expense) signed as presented; cash flow as presented.
- "—" or "-" = 0. A line not presented is omitted. Nothing is estimated; computed values are stated in `notes` / the README.

## Record keys
```
period, fy, q, period_end, sources{release, release_date, filing}, notes[]
is:    rev, rev_prod, rev_serv, cogs, cogs_prod, cogs_serv, gp, rd, sm, ga, impair (impairment / integration / restructuring / severance), opex,
       oi, oth, ebt, tax, ni, eps_b, eps_d, sh_b, sh_d, dps, lines_raw[[section / label, value]]
bs:    cash, sti, ar, inv, tca, ppe, rou, eqinv, gw, intang, ta, ap, std, cltd, ucr, tcl, ltd, lucr, lease_ltl, tl (derived = TL&E − equity
       where not presented), eq, tle, sh_out (from the paid-in-capital caption), lines_raw
cf:    months (3 for the release three-month column), ni, dda, sbc, def, cfo, debt_st, debt_iss, debt_rep, iss, bb, div, cff, capex, acq, cfi,
       fx, net, beg, end, lines_raw;  cf_ytd: the same keys for the year-to-date column (ytd_months)
seg:   {'metric||segment': value} — metric rev / oi / gm / cogs / opex; segment names exactly as published; seg_py: prior-year column
py:    is (prior-year column of the same release)
ngaap: auto-parsed reconciliation (superseded by ngaap.json)
```

## ngaap.json
Per period: `src`, `release_date`, `basis` (own release / re-presented in a later release), `gaap` and `adj` = [revenue, operating income, net income, diluted EPS], `items` = [{label (company wording), cat, rev, oi, ni, eps}]. Categories: REVDEF (revenue deferrals / recognition), RESTR (impairment, integration, restructuring, severance), IMPAIR (goodwill impairment), LEGAL (EC fine), TAX (discrete tax items), OPENAI (impact from investments in OpenAI, after tax).

## Self-checks (`check_data.py`, 2,094 checks)
- **Statement arithmetic:** gross margin − opex − impairment = operating income; + other income = pre-tax; − tax = net income; product + service revenue = total; EPS = net income ÷ diluted shares (±0.01).
- **Segments:** each structure (divisions, D&C / Commercial, PBP / IC / MPC, FY27) sums to consolidated revenue and operating income (gross margin for FY2014–15); FY27 lines sum to segments.
- **Non-GAAP:** bridge bases = reported GAAP figures; GAAP + items = published adjusted operating income / net income; adjusted EPS = adjusted net income ÷ diluted shares (±0.015) or GAAP EPS + per-share items (±0.01).
- **Cash flow and balance sheet:** CFO = Σ operating lines; beginning cash + change = ending cash = balance-sheet cash; TA = TL&E.
- **Quarters vs years:** Σ quarters = fiscal year, FY2013–FY2026 (documented exceptions only).
- **XBRL:** revenue, operating income, net income, diluted EPS, total assets (quarters and years) and CFO (years) vs the earliest-filed facts.
