# FSS data extraction: schema and rules

`extract.py` writes one JSON per period to `data/<period>.json` from the EDGAR sources. It is scripted, not agent-transcribed: `parse_fss.py` reads the tables. The rules follow `templates/EXTRACTION_SCHEMA_TEMPLATE.md`.

## Sources
- **SEC EDGAR only** (Federal Signal Corporation, CIK 277509). The IR site is not used; its releases are filed on EDGAR.
- **Earnings releases** are Ex. 99.1 to each 10-Q / 10-K (Federal Signal files only three Item 2.02 8-Ks; the FY2008 release is one of them). The Q3/14 release is Ex. 99.2.
- **Raw files** live in `$FSS_SRC/docs`, with text versions in `$FSS_SRC/txt` (one table row per line, cells joined by ` | `). Document URLs are recorded in each record's `sources`.
- **XBRL company facts:** `$FSS_SRC/cf_277509.json`; the subset used is committed as `data/_xbrl.json`.
- **EDGAR requests** send a User-Agent and stay under 5 per second.

## Periods and blocks
- **Annual FY2006–FY2025; quarters Q1/13–Q3/26.** Q4 is derived in `normalize.py` from the Q4 release three-month column (`rel_q4`).
- **Blocks per record:**
  - `k`: the period's own 10-K / 10-Q — `is`, `seg`, `cf` (year to date, `ytd_months`), `bs`, `grp` (MD&A group tables), and for quarters `is_ytd` / `seg_ytd`.
  - `k1`: the following year's filing, prior-year columns (restated comparatives). `k2` (annual only): the filing two years later.
  - `rel` / `rel1`: the period's release and the following year's release (prior-year columns): `is`, `grp` (orders, backlog, segment D&A, segment adjusted EBITDA), `adjeps`, `ebitda`, `corp_text`, `outlook`. Annual records add `rel_q4` / `rel1_q4` (three-month columns).
  - `x`: XBRL facts as first filed (SBC, deferred taxes, D&A, dividends paid / declared, shares, revenue, operating income, net income, EPS, assets).
- **Columns:** every value column is resolved to (months, year) from the header row with the year tokens; "Change" / "vs." columns are recognised; years are then re-expressed as `cur` / `py` / `py2` against the document's own fiscal year, so a 10-K's MD&A "2024 vs 2023" table is never read as current-year data.

## Units and signs
- USD millions as published (the filings are in millions to one decimal); per share as published; shares in millions.
- Costs positive. `oth` (other expense / income) is taken as presented; `normalize.py` derives non-operating items as operating income − interest − pre-tax income, and tax as pre-tax income − continuing income, because the label and sign of these lines changed over time.
- Adjusting items are signed as added back (charges +, gains −).
- "—" = 0. A line not presented is omitted. Nothing is estimated; derived values are stated in `notes` and in the workbook comments.

## Adjusting-item categories (`normalize.icat`)
| Code | Model line | Federal Signal labels (examples) |
|---|---|---|
| ACQ | Acquisition & integration | Acquisition and integration-related expenses, net (incl. contingent-consideration remeasurement) |
| RESTR | Restructuring | Restructuring; executive severance costs |
| STEPUP | Purchase accounting | Purchase accounting effects (inventory and rental-equipment step-up; the EBITDA bridge excludes the part in D&A) |
| OTHER | Other operating items | Coronavirus-related expenses, hearing loss settlement charges, environmental remediation costs, charges associated with previously discontinued operations, pension settlement inside operating income (2017) |
| PENSION / DEBT | Non-operating | Pension settlement / pension-related charges, debt settlement charges |
| TAXD | Special tax items | Valuation-allowance releases, tax planning benefits, worthless-stock deduction |
| INT, TAXL, DA, NONOP, DISCOPS | EBITDA components | Interest, income tax, depreciation and amortization, other expense, discontinued operations |

## Self-checks (`check_data.py`, 1,344 checks)
- **Statement arithmetic:** gross profit − operating lines = operating income; operating income − interest − non-operating = pre-tax income; − tax = continuing income; + discontinued = net income; EPS = net income ÷ diluted shares (±0.015).
- **Groups:** Σ group net sales = consolidated net sales; derived corporate = the published corporate line (to 2023).
- **Non-GAAP:** operating income + D&A + operating items = published adjusted EBITDA; published adjusted net income ÷ diluted shares = published adjusted EPS (±0.015).
- **Cash flow:** beginning cash + net change (+ cash-basis line) = ending cash; ending cash = balance-sheet cash (+ discontinued-operations cash).
- **Balance sheet:** total assets = total liabilities and equity.
- **XBRL (as first filed):** revenue, net income and total assets.
- **Quarters vs years:** Σ quarters = year (2013–2025) for the statement, group, cash-flow and non-GAAP lines.
