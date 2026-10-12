# V data extraction: schema and rules

Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. Visa Inc. (NYSE: V), US GAAP, USD millions, fiscal year ends
30 September (FY2026 = Oct-2025 – Sep-2026; Q1 = Oct–Dec). Give this file, unchanged, to every extraction agent.

## Sources
- **SEC EDGAR only** (CIK 0001403161, Visa Inc.; registrant since the Oct-2007 reorganization; IPO 19-Mar-2008). The IR site
  (investor.visa.com) is blocked; its releases are the 8-K Item 2.02 Ex. 99.1 exhibits.
- **Text versions** of every document are in `$V_SRC/txt`: one table row per line, cells joined by ` | `. File names embed
  `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/1403161/<accession-no-dashes>/<doc>`.
- **Image-based releases** (Q1 FY2018 – Q2 FY2021 except Q4 FY18 – Q2 FY19, which are plain text): the tables are slide images with a
  hidden white text layer, written to `$V_SRC/txt_hidden/<date>_<doc>_hidden.txt` (one block per slide; table rows are separated
  by runs of spaces, not newlines). Read the numbers from that layer.
- **Period index:** `$V_SRC/period_index.json` maps each period key to `release` (URL), `release_txt` / `release_hidden_txt`
  (local text), `filing` (10-Q, or 10-K for annual keys), `filing_txt`, and `next_release` / `next_filing` (one year later).
- **Text quirks:** a cell that was only ")" is dropped, so "(25,433" is negative; "( 1,705" is negative; "—" means zero.
  A cell such as "(3)" right after a number in a non-GAAP row is usually a footnote marker, not a value: check the column count.
- **XBRL company facts** (`$V_SRC/cf_1403161.json`) are a cross-check only.

## Basis rules
- **Statements (`is`, `bs`, `cf`, `eps`):** Q1–Q3 from the 10-Q (three-month column; identical to the release as originally
  reported); Q4 three-month from the Q4 release where its tables are text, otherwise fiscal year (10-K) − nine months (Q3 10-Q),
  noted. Annual = 10-K. Cash flow is year to date (`ytd_months`).
- **Non-GAAP (`ngaap`):** each period's own earnings release (quarters: three-month table; fiscal years: the twelve-month table in
  the Q4 release), **as originally published**.
- **Units:** USD millions as published (whole millions from FY2008); shares in millions; per-share as published.
- **Stock split:** 4-for-1, effective 18-Mar-2015 (documents filed before then are pre-split). Record shares / EPS / DPS **exactly
  as published**; `normalize.py` adjusts by filing date.
- **Null vs zero:** "—" = 0.0; a line not presented = null. **Never estimate.** State any computed value in `notes`.

## Statement record — `data/<period>.json` (written by `extract.py`)
- `period`, `sources` (`filing`, `release`, `release_date`), `notes`.
- `is`: three-month (quarter) or twelve-month (annual) statement of operations as printed. Keys: `rev_svc`, `rev_dp`, `rev_itr`, `rev_oth`, `rev_ci` (client / volume and
  support incentives, negative as printed), `rev_net`, `personnel`, `marketing`, `network`, `prof`, `dna`, `ga`, `litig`, `other_op` ([label, value] lines), `opex`,
  `opinc`, `int_exp` (as printed, negative), `nonop`, `other_nonop`, `ebt`, `tax`, `ni_tot`, `nci`, `ni`, `eps_b`, `sh_b`, `eps_d`, `sh_d` (class A, as published).
  `is_ytd` (Q2 / Q3: year to date, for Q4 = FY − 9M); `is_rel` (Q4: the Q4 release three-month column where tabular); `is_raw` (rows parsed).
- `bs`: period-end balance sheet (`cash`, `escrow`, `inv_cur`, `inv_nc`, `settle_rec`, `ar`, `collat_a`, `tca`, `ppe`, `gw`, `intang`, `ta`, `ap`, `settle_pay`,
  `collat_l`, `accomp`, `ci_l`, `accrued`, `std`, `litig_acc` (current), `tcl`, `ltd`, `dtl`, `oth_l`, `tl`, `te` (= TL&E − TL), `tle`) and `bs_raw`.
- `cf`: year-to-date cash flow (`ni`, `sbc`, `dna`, `deftax`, `cfo`, `capex`, `acq`, `cfi`, `bb`, `div`, `debt_iss`, `debt_rep`, `cp`, `cff`, `fx`, `net`, `beg`, `end`,
  `ytd_months`) and `cf_raw`.
- `kpi`: `pv`, `pv_us`, `pv_intl` (nominal payments volume, $bn, the quarter / twelve months ended one quarter before the period), `ptx` (processed transactions,
  millions); Q3 records also carry the nine-month figures (`*_9m`). Annual records carry `dps_10k` (selected financial data) where printed.

## Non-GAAP record — `data/ngaap/<period>.json`
```json
{
  "period": "Q2-16",                      // Qn-yy for quarters (three months), yyyy for fiscal years (twelve months)
  "source": "https://www.sec.gov/Archives/edgar/data/1403161/.../<release>.htm",
  "release_date": "YYYY-MM-DD",
  "published": true,                      // false if this period's release presents no GAAP-to-non-GAAP reconciliation
  "measure_names": "exact names used, e.g. 'adjusted' / 'non-GAAP'",
  "columns": ["exact column headers of the reconciliation table, in order"],
  "gaap":     {"opex": null, "op_margin": null, "nonop": null, "ebt": null, "tax": null, "etr": null, "ni": null, "eps": null},
  "items": [
    {"label": "exact row label", "cat": "LITIG",
     "opex": null,      // value in the Operating Expenses column, signed as printed: (450) -> -450 (an expense removed)
     "nonop": null,     // value in the Non-operating income (expense) column as printed
     "ebt": null,       // Income Before Income Taxes column, if the table has one
     "tax": null,       // Income Tax Provision column as printed
     "ni": null,        // Net Income column as printed (after tax)
     "eps": null,       // Diluted EPS column as printed
     "where": "op | nonop | tax"}
  ],
  "adjusted": {"opex": null, "op_margin": null, "nonop": null, "ebt": null, "tax": null, "etr": null, "ni": null, "eps": null,
               "shares": null},          // shares = diluted class A (as-converted) shares shown in the table, if shown
  "definition": "one-line summary of what this period's non-GAAP excludes, in the company's words",
  "notes": "anything computed, any self-check that does not pass and why"
}
```
Categories (`cat`): LITIG (litigation provision / accretion on litigation settlements), EQINV ((gains) losses on equity
investments), AMORT (amortization of acquired intangibles / asset step-up), ACQ (acquisition-related costs), RESTR (severance,
restructuring, lease consolidation), VE (Visa Europe framework agreement loss, put-option revaluation, currency forwards / FX
gains tied to the Visa Europe consideration), TAX (tax-only items: deferred tax remeasurement, reversal of tax reserves,
elimination of deferred tax balances), OTHER (anything else; keep the company label, e.g. charitable contribution, indirect
taxes, investment income on IPO proceeds).

For pre-FY2013 tables that adjust pre-tax income and then apply a normalized tax rate (e.g. FY2008, 41%), record each item's
pre-tax amount in `ebt` (sign = effect on pre-tax income) with `where`, leave `ni` null, and record the adjusted tax and adjusted
NI under `adjusted`.

## Self-checks before writing each period
- gaap.ni + Σ items.ni = adjusted.ni (±1); gaap.eps + Σ items.eps = adjusted.eps (±0.02);
- gaap.opex + Σ items.opex = adjusted.opex (±1); gaap.nonop + Σ items.nonop = adjusted.nonop (±1);
- gaap.tax + Σ items.tax = adjusted.tax (±1).
Report any failure that remains, with the reason, in `notes`.
