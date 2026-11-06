# JHX data extraction: schema and rules

Derived from `templates/EXTRACTION_SCHEMA_TEMPLATE.md` for James Hardie Industries plc (NYSE / ASX: JHX, CIK 1159152).

## Sources
- **SEC EDGAR only.** One registrant throughout (James Hardie Industries N.V. → SE → plc, CIK 0001159152). The IR site
  (ir.jameshardie.com) is blocked; its results packages are the Form 6-K exhibits (to Q3 FY26) and the Form 8-K Ex. 99.1
  earnings releases (from Q4 FY26).
- **Text versions** of every document are in `$JHX_SRC/txt`: one table row per line, cells joined by ` | `. File names
  embed `<filing date>_<form>_<accession>_<document>`. A document's URL is
  `https://www.sec.gov/Archives/edgar/data/1159152/<accession-no-dashes>/<document>`.
- **Documents per results package** (quarterly 6-K, filed mid-May / mid-Aug / mid-Nov / mid-Feb):
  - FY2006–FY2008: one exhibit holding the media release, Management's Analysis of Results (MA) and the financial statements
    (US$ and A$ columns; note-reference columns in the full statements). The "Supplemental Financial Information" tables
    (fibre cement ex-asbestos | asbestos compensation | as reported) give clean as-reported statements.
  - Aug-2008 – May-2017: Ex. 99.3 (or dex993) = MA; Ex. 99.4 / dex995 = condensed consolidated financial statements (FS).
  - Aug-2017 – Feb-2026: `ex99x ma…` = MA; `ex99x fpages…` = FS (quarterly 10-Q-style package with notes: segments, debt,
    asbestos roll-forward, share counts, dividends).
  - Q4 FY24 (May-2024) and Q4 FY25 (May-2025) have no MA / FS exhibit; the annual report 6-K (`…iar.htm`, filed the next day)
    and the earnings release (`ex993erq4fy25`) are used, with Q4 = FY − 9M where only the year is presented.
  - From Q4 FY26 (19-May-2026): Form 8-K Ex. 99.1 earnings release (IS, BS, CF, segment and non-GAAP tables) plus the
    10-K / 10-Q.
- **XBRL company facts** (`companyfacts.json`, 20-F from FY2011, 10-K / 10-Q from FY2026) cross-check annual sales,
  operating income, net income, EPS, CFO and total assets, and supply D&A / SBC / deferred tax where a release lacks them.
- **EDGAR requests:** User-Agent on every request, under 5 per second.

## Basis rules
- **Fiscal year** ends 31 March; FY2027 = Apr-2026 – Mar-2027. Period keys: `2006` … `2026` (fiscal years), `Q1-13` …
  `Q2-27` (quarters; Q1 = Jun quarter), `H1-13` / `9M-13` (year-to-date cash flow).
- **Quarters:** income statement, segments, volumes / prices and non-GAAP bridges from that quarter's package, three-month
  columns, **as originally reported**. Q4 = the Q4 package's three-month column; where only the year is presented, FY − 9M
  (said so in `notes`).
- **Balance sheet:** the quarter-end statement. **Cash flow:** year-to-date (`ytd_months` 3 / 6 / 9 / 12); discrete quarters
  derived in `normalize.py`.
- **Annual records:** the Q4 package twelve-month columns; the 20-F / 10-K wins where they differ.
- **Prior-year comparatives (`py`):** as presented in that package; `restated` with the reason where they differ from the
  original print (segment recasts FY2017, FY2019, Q2 FY26; Europe discontinued operations from Q1 FY27; non-GAAP
  redefinitions Q1 FY27).
- **Units:** USD millions to one decimal; shares in millions; per-share in USD (releases to FY2022 print EPS in US cents —
  divided by 100 at extraction, flagged `eps_basis: cents`); volumes in million square feet (mmsf); average net sales
  price in USD or AUD per thousand square feet (msf) as published; percentages as numbers.
- **Signs:** costs positive; two-sided items signed by their effect on earnings (asbestos adjustments: gain positive);
  cash flow as presented. Pre-FY2019 releases print expenses in parentheses — the sign convention is normalised in
  extraction (`cogs`, `sga`, `rd`, `tax` positive = expense).
- **Null vs zero:** "—" = 0.0; a line not presented = null (key omitted). **Never estimate.** Any computed value is stated in
  `notes`.

## Output
One JSON per period in `data/<period>.json`, keyed by source document date, with sections:
- `is`: `rev`, `cogs`, `gp`, `sga`, `rd`, `asb_adj` (asbestos adjustments, gain +), `impair`, `restr`, `acq_exp`,
  `other_op`, `op` (EBIT / operating income), `int_net` (net interest expense +), `int_exp`, `int_inc`, `other_nonop`
  (income +), `ebt`, `tax`, `ni` (continuing), `disc` (discontinued operations, FY27), `ni_total`, `eps_b`, `eps_d`,
  `eps_d_cont`, `sh_b`, `sh_d`, `dps_declared`.
- `seg`: per segment (`na` North America / Siding & Trim lineage, `dra` Deck Rail & Accessories, `apac` Asia Pacific / ANZ,
  `eu` Europe Building Products, `int` International FC FY17–18, `oth` Other Businesses, `rd` R&D, `corp` General Corporate):
  `rev`, `ebit` (segment EBIT / operating income), `adj_ebit`, `adj_ebitda`, `vol` (mmsf), `asp` (per msf), `asp_ccy`,
  `rev_lc` (A$ / € sales), `fc_rev` / `fg_rev` (Europe fibre cement / fibre gypsum).
- `ng`: `adj_ebit_pub`, `adj_ebitda_pub`, `adj_ebitda_ex_asb_pub`, `adj_ni_pub`, `adj_eps_pub`, `adj_tax_pub`,
  `adj_etr_pub`, `dna` (D&A used in the EBITDA bridge), `ebitda_pub`, and `items`: ordered `[label, value]` lists for the
  EBIT bridge (`ebit_items`), the net-income bridge (`ni_items`) and the EBITDA bridge (`ebitda_items`), exactly as
  published (sign as added in the bridge).
- `cf` (year to date): `ytd_months`, `ni`, `dna`, `deferred_tax`, `sbc`, `asb_adj`, `other_noncash`, `wc` (Σ change lines,
  incl. asbestos claims paid), `cfo`, `capex`, `ppe_proceeds`, `acq`, `cap_int`, `asb_inv_net` (restricted investments −
  asbestos), `cfi`, `debt_proceeds`, `debt_repay`, `div`, `buyback`, `share_iss`, `other_fin`, `cff`, `fx`, `net_change`,
  `cash_begin`, `cash_end`, `cash_basis` (`cash` to FY2018; `cash+restricted+asbestos` from FY2019, ASU 2016-18),
  `aicf_paid` (cash paid to AICF, supplemental), `lines_raw`.
- `bs`: `cash`, `restr_cash`, `restr_cash_asb`, `restr_inv_asb`, `ar`, `inv`, `prepaid`, `ins_rec_asb_c`, `dta_c`, `tca`,
  `ppe`, `rou`, `gw`, `intang`, `ins_rec_asb_nc`, `dta`, `dta_asb`, `ato_deposit`, `other_nca`, `ta`, `ap`, `accrued_payroll`,
  `std`, `div_payable`, `warranty_c`, `tax_payable`, `asb_liab_c`, `other_cl`, `tcl`, `ltd`, `dtl`, `asb_liab_nc`,
  `warranty_nc`, `lease_liab`, `other_ncl`, `tl`, `equity`, `tle`, `shares_out`, `lines_raw`.
- `aicf`: asbestos liability (total), insurance receivable (total), restricted cash & investments, net unfunded AFFA
  liability (and net of tax), claims paid, AFFA contribution, where the package shows the roll-forward.
- `notes`: computed values and failed self-checks.

## Adjusting-item categories
ASB (asbestos adjustments, AICF SG&A, AICF interest, asbestos tax effect), ASIC (ASIC proceedings expenses FY2010–13),
NZ (New Zealand weathertightness claims FY2014–16), ACQ (Fermacell / AZEK transaction and integration, pre-close financing),
STEPUP (inventory fair value), AMORT (AZEK intangible amortization), IMPAIR, RESTR, DISC (product line discontinuation
FY2019), SBC (from Q1 FY27), TAX (tax adjustments), OTHER.

## Self-checks (per period)
- IS: gp = rev − cogs; op = gp − sga − rd − asbestos − other operating lines; ebt = op − int_net + other_nonop;
  ni = ebt − tax (±0.15).
- Segments: Σ segment net sales = rev; Σ segment EBIT + R&D + corporate (incl. asbestos) = op (±0.2).
- Non-GAAP: start + Σ items = published adjusted figure (±0.15); adj NI ÷ diluted shares = adjusted EPS (±0.01).
- Cash flow: cfo + cfi + cff + fx = net_change; cash_begin + net_change = cash_end (±0.15).
- Balance sheet: ta = tle; current and total subtotals (±0.2).
- Σ Q1–Q4 = FY for IS and segment lines (±0.3).
