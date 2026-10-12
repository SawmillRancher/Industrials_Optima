# MCO data extraction: schema and rules

Moody's Corporation (NYSE: MCO). Give this file, unchanged, to every extraction agent. Derived from
`templates/EXTRACTION_SCHEMA_TEMPLATE.md` (DHR / TDY / WAB schemas) with Moody's-specific keys (MIS lines of business, MA lines,
segment Adjusted Operating Income, ARR, recurring / transaction revenue, organic constant-currency growth).

## Sources
- **SEC EDGAR only** (CIK 0001059556; no predecessor registrant: Moody's Corporation was spun off from Dun & Bradstreet on
  30-Sep-2000 and has filed under this CIK since). The IR site (ir.moodys.com) is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Text versions** of every document are in `$MCO_SRC/txt`: one table row per line, cells joined by ` | `. File names embed
  `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/1059556/<accession-no-dashes>/<doc>`.
  Record those URLs in `sources`. 2007–2008 releases are plain-text exhibits (`...ex99-1.txt` / `...ex991.txt`) with fixed-width
  columns, not ` | ` rows.
- **Period index:** `$MCO_SRC/period_index.json` maps each period key to `release` (8-K Ex. 99.1 text file), `filing` (10-Q, or the 10-K
  for annual records) and `next_release` / `next_filing` (the same documents one year later, for comparatives).
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" or "(1.1" is negative.
  - "—" or "-" means zero.
  - From 2024 (check each release) Moody's prints whole USD millions; earlier releases print one decimal. Record as printed.
- **Cross-check:** `$MCO_SRC/cf_1059556.json` (XBRL company facts, 2008+).
- **EDGAR requests:** send a User-Agent and stay under 5 per second (you should not need to download anything).

## Basis rules
- **Quarters:** income statement, revenue by line, segment data and non-GAAP bridges come from that quarter's release (three-month
  columns), **as originally reported**. Where the release does not carry an item (e.g. segment Adjusted Operating Income before the
  releases included the segment table), take it from that quarter's 10-Q (segment note or MD&A), and say so in `notes`.
  - Q4 = the Q4 release's three-month column. If an item has no three-month Q4 figure anywhere (e.g. 10-K-only segment data), leave it
    null in the Q4 record and give the FY value in the annual record; the model derives FY − 9M.
- **Balance sheet:** the quarter-end statement from the 10-Q / 10-K (full balance sheet, not the release's condensed table). Q4 records
  may omit `bs` (the annual record carries the year-end balance sheet).
- **Cash flow:** the **year-to-date** statement from the 10-Q / 10-K (or the release if it carries the full statement); set
  `cf.ytd_months` to 3, 6, 9 or 12. Q4 records may omit `cf`.
- **Annual records (`2006` … `2025`):** the Q4 release twelve-month columns plus that year's 10-K. **The 10-K wins** when they differ
  (write both in `notes`). Annual records always carry `is`, `seg`, `ngaap`, `cf` (ytd_months 12) and `bs`.
- **Prior-year comparatives (`py`):** the prior-year column of this period's release, for revenue by line and segment Adjusted
  Operating Income only. Set `py.restated` true, with the reason, where it differs from what was originally reported (MA line recasts:
  2008/2009 reclassifications, 2011 RD&A/ERS/PS, 2016–2017, 2022 DS/R&I/D&I, 2024 Banking/Insurance/KYC; MIS line moves).
- **Units:** USD millions as published (thousands ÷ 1,000); shares in millions; per-share as published; percentages as numbers in
  percent (3.5 = 3.5%).
- **Stock splits:** none since the spin-off (the last 2-for-1 split was May-2005). Record shares / EPS / DPS exactly as published.
- **Signs:**
  - costs positive (operating, SG&A, D&A, restructuring, other operating charges);
  - two-sided items signed by their effect on earnings (non-operating income +, expense −; an operating gain is a negative cost);
  - cash flow as presented (outflows negative).
- **Null vs zero:** a line shown as "—" = 0.0. A line not presented = null. **Never estimate.** Any computed value (sum, difference,
  FY − 9M) is stated in `notes`.

## Output
One JSON file per period: `models/mco_build/data/<period_key>.json`. Keys: `2006` … `2025` (annual) and `Q1-13` … `Q2-26`
(quarters). Write valid JSON: no comments, no trailing commas.

```json
{
  "period": "Q2-26", "period_end": "2026-06-30",
  "sources": {"release": "https://...", "filing": "https://..."},
  "is": {
    "rev": null,
    "opex_operating": "positive ('Operating' expense line)",
    "sga": "positive",
    "dna": "positive (Depreciation and amortization)",
    "restr": "positive (Restructuring; negative if a reversal)",
    "other_op_lines": [["exact label of every other operating expense / gain line on the IS face", "positive = expense"]],
    "tot_exp": null, "oi": null,
    "int_net": "signed (Interest (expense) income, net / Interest expense, net; expense negative)",
    "oth_nonop": "signed (Other non-operating (expense) income, net)",
    "nonop_lines": [["exact label of any other non-operating line on the IS face (e.g. Gain on business divestitures, CCXI gain)", "signed"]],
    "nonop_tot": "signed", "ebt": null, "tax": "positive = expense",
    "ni_tot": "Net income (incl. NCI)", "nci": "positive = deducted", "ni": "Net income attributable to Moody's",
    "disc_ops": "signed, only if presented (2006-2008: none expected)",
    "eps_b": null, "eps_d": null, "sh_b": null, "sh_d": null,
    "dps_decl": "dividends declared per share in the period (release / 10-Q); null if not stated"
  },
  "seg": {
    "mis_lines": {"exact label": "external revenue (e.g. Corporate Finance, Structured Finance, Financial Institutions, Public, Project and Infrastructure Finance, MIS Other)"},
    "mis_ratings_total": "Total ratings revenue (if shown)",
    "mis_ext": "Total MIS external revenue",
    "mis_interseg": "MIS intersegment revenue (royalty from MA / intersegment revenue)",
    "mis_recurring": null, "mis_transaction": null,
    "ma_lines": {"exact label": "external revenue on the basis shown in THIS release (e.g. Subscriptions / Software / Professional services; RD&A / ERS / PS; Decision Solutions / Research and Insights / Data and Information; Banking / Insurance / KYC)"},
    "ma_ext": "Total MA external revenue",
    "ma_interseg": "MA intersegment revenue",
    "ma_recurring": null, "ma_transaction": null,
    "ma_arr": "MA ARR at period end (if published)",
    "ma_arr_lines": {"exact label": "ARR by line"},
    "elim": "signed eliminations as shown",
    "mis_adj_oi": "MIS segment Adjusted Operating Income (company measure; includes intersegment revenue and expense)",
    "ma_adj_oi": "MA segment Adjusted Operating Income",
    "mis_adj_om": "MIS Adjusted Operating Margin % as published", "ma_adj_om": "MA Adjusted Operating Margin % as published",
    "mis_dna": null, "ma_dna": null, "mis_restr": null, "ma_restr": null,
    "mis_oi": "MIS segment operating income (GAAP basis, where a segment OI is published, e.g. pre-2013 10-K segment note)",
    "ma_oi": null,
    "seg_other_items": [["exact label (e.g. goodwill impairment, asset abandonment, reserve, duplicate rent)", "MIS value", "MA value"]],
    "us_rev": "United States revenue (if shown)", "intl_rev": "International revenue (if shown)",
    "legacy": {"exact label": "any other revenue cut shown (e.g. 2006-2007 'Moody's KMV', 'Moody's Investors Service', ratings by old LOB names)"},
    "seg_note": "structure in force / recasts / source (release or 10-Q note) of each segment item"
  },
  "ngaap": {
    "adj_oi_pub": "Adjusted Operating Income as published", "adj_om_pub": "Adjusted Operating Margin % as published",
    "adj_oi_items": [["exact label of each item added to operating income", "value as added (+)"]],
    "adj_ni_pub": "Adjusted (non-GAAP) net income attributable to Moody's as published",
    "adj_eps_pub": "Adjusted (non-GAAP) diluted EPS as published",
    "eps_bridge_start": "GAAP diluted EPS the bridge starts from",
    "eps_bridge": [["exact label", "per-share value as added (net of tax where the bridge shows net)"]],
    "item_amounts": [["exact label", "pretax $m as added", "after-tax $m as added", "op | nonop | tax | below_ni", "CAT"]],
    "tax_items": [["exact label of tax-only items (e.g. legacy tax, Tax Act, discrete tax)", "$m as added"]],
    "fcf_pub": "Free Cash Flow as published (CFO - capital additions)",
    "occ": {"mco": "organic constant currency revenue growth % (if published)", "mis": null, "ma": null},
    "guidance": "full verbatim outlook table for the current year from this release (each item: guidance text), including the EPS / margin / FCF reconciliation rows",
    "notes": "definition of each adjusted measure in this period (copy the release wording of what is excluded)"
  },
  "cf": {
    "ytd_months": 12, "ni_tot": null, "dna": null, "sbc": "stock-based compensation", "deferred_tax": null,
    "cfo": null, "capex": "negative (Capital additions)", "acquisitions": "negative (cash paid for acquisitions, net of cash acquired)",
    "divest": "positive (cash received upon divestitures)", "cfi": null,
    "debt_proceeds": "positive (issuance of notes / term loans / borrowings)", "debt_repay": "negative (repayment of notes / loans)",
    "cp_net": "signed (net commercial paper / revolver)", "buyback": "negative (Treasury shares)",
    "sbc_tax_withholding": "negative (repurchase of shares related to stock-based compensation)",
    "stock_plan_proceeds": "positive", "dividends": "negative (to Moody's shareholders)", "div_nci": "negative",
    "cff": null, "fx": null, "net_change": null, "cash_begin": null, "cash_end": null,
    "lines_raw": [["exact label", "value as shown"]]
  },
  "bs": {
    "cash": null, "sti": "short-term investments", "ar": "accounts receivable, net", "oca": "other current assets (sum of every other current asset line)",
    "tca": null, "ppe": "property and equipment, net", "rou": "operating lease right-of-use assets (2019+)", "goodwill": null,
    "intang": "intangible assets, net", "dta": "deferred tax assets, net", "onca": "other assets (sum of every other non-current asset line)",
    "ta": null,
    "ap_accr": "accounts payable and accrued liabilities",
    "cp": "commercial paper / notes payable / short-term borrowings / revolver (current)",
    "cltd": "current portion of long-term debt",
    "lease_cur": "current portion of operating lease liabilities",
    "defrev": "deferred revenue (current)", "ocl": "other current liabilities (sum of every other current liability line)",
    "tcl": null,
    "defrev_nc": "non-current portion of deferred revenue", "ltd": "long-term debt", "dtl": "deferred tax liabilities, net",
    "utp": "uncertain tax positions", "lease_nc": "operating lease liabilities (non-current)",
    "ol": "other liabilities (sum of every other non-current liability line, incl. unrecognized tax benefits if combined)",
    "tl": "total liabilities (null if not presented: derive nothing)",
    "redeemable_nci": "redeemable noncontrolling interest (mezzanine; 2011-2014)",
    "eq": "total Moody's shareholders' equity (deficit)", "nci": "noncontrolling interests in equity", "te": "total shareholders' equity (deficit)",
    "tle": null,
    "shares_out": "shares outstanding at period end (release 'actual number of shares outstanding', or 10-Q cover / equity note)",
    "lines_raw": [["exact label", "value"]]
  },
  "py": {"restated": false, "notes": null, "mis_lines": {}, "ma_lines": {}, "mis_adj_oi": null, "ma_adj_oi": null},
  "extra": {
    "employees": null, "acquisitions": [["name", "close date", "consideration $m", "segment"]],
    "divestitures": [["name", "date", "proceeds / notes"]], "debt_maturities": [["year", "$m"]],
    "amort_schedule": [["year", "$m"]], "notes": null
  },
  "notes": "computed values; any self-check that does not pass and why"
}
```

## Adjusting-item categories (CAT)
| Code | Meaning |
|---|---|
| AMORT | Acquired-intangible amortization |
| ACQ | Acquisition, transaction and integration costs (incl. purchase-price hedge losses on acquisitions) |
| RESTR | Restructuring (incl. charges related to asset abandonment) |
| GAIN | (Gain) / loss on business divestitures, remeasurement gains on step acquisitions (e.g. ICRA, MAKS) |
| IMPAIR | Goodwill / intangible impairment |
| LEGAL | Legal / regulatory settlements and reserves (e.g. 2016 CFG / DOJ settlement, international non-income tax reserve) |
| OTHER | Any other item; keep the company's label (e.g. duplicate rent) |
| TAX | Tax effect of the items |
| TAXD | Discrete tax items (legacy tax, Tax Act, Tax Reform, FIN 48 / UTP releases) |
| NCI | Share attributable to NCI |

## Self-checks before writing each period
Re-read the source if any of these fail, and report any failure that remains, with the reason, in `notes`.
- **IS:** opex_operating + sga + dna + restr + Σ other_op_lines = tot_exp; rev − tot_exp = oi; oi + int_net + oth_nonop + Σ nonop_lines
  = nonop_tot + oi = ebt; ebt − tax = ni_tot; ni_tot − nci = ni (±0.6; ±1.5 when the release prints whole millions).
- **Revenue:** Σ mis_lines = mis_ext; Σ ma_lines = ma_ext; mis_ext + ma_ext = rev (±0.6 / ±1.5).
- **Segments:** mis_adj_oi + ma_adj_oi = adj_oi_pub (±1.5); adj_oi_pub − Σ adj_oi_items = oi.
- **Non-GAAP:** eps_bridge_start + Σ eps_bridge = adj_eps_pub (±0.01); GAAP NI + Σ after-tax items = adj_ni_pub (±0.6 / ±1.5).
- **Cash flow:** cfo + cfi + cff + fx = net_change; cash_begin + net_change = cash_end (±0.6 / ±1.5).
- **Balance sheet:** ta = tle; components sum to subtotals (±1 / ±1.5).
