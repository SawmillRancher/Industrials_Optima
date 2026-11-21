# JBHT data extraction: schema and rules

Derived from `models/templates/EXTRACTION_SCHEMA_TEMPLATE.md`. `extract.py` implements it; the same rules apply to any manual extraction.

## Sources
- **SEC EDGAR only** (J.B. Hunt Transport Services, Inc., CIK 0000728535; no predecessor registrants). The IR site (jbhunt.com) is blocked; its releases are the 8-K Ex. 99.1 exhibits.
- **Raw documents** are in `$JBHT_SRC/docs` and their text versions in `$JBHT_SRC/txt` (one table row per line, cells joined by ` | `). File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/728535/<accession-no-dashes>/<doc>`. URLs are recorded in `sources`.
- **Release index:** `data/_releases.json` maps each year-quarter to the first-filed release that contains the statements.
- **XBRL company facts:** `$JBHT_SRC/cf_728535.json`; the concepts used are saved to `data/_xbrl.json` so the build runs without the raw downloads.
- **Text quirks:**
  - A cell that was only ")" is dropped, so "(25,433" is negative.
  - "—" and "-" mean zero.
  - Several filings split the last letter of a word ("revenue s", "Balance Sheet s", "December 3 1"); `parse_release.py` repairs labels and matches headings with whitespace removed.
  - The FY2006 and FY2008 releases omit the schedule headings; sections are typed by their contents.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Quarters:** statement of earnings, segments and operating statistics from that quarter's release (three-month columns), **as originally reported**. The Q4 release prints a three-month column, so no FY − 9M derivation is needed for the P&L.
- **Annual records:** the Q4 release twelve-month columns.
- **Balance sheet:** the period-end column of the release balance sheet, plus "actual shares outstanding" from the supplemental data.
- **Cash flow:** **year to date**, from XBRL company facts as first filed in the 10-Q / 10-K (`cf.ytd_months` = 3, 6, 9 or 12). The releases carry only two supplemental cash-flow figures (net cash from operations, net capital expenditures), kept as a cross-check (`cfo_rel`, `netcapex_rel`). FY2006–07 come from the FY2008 10-K (`manual_items.json`).
- **Prior-year comparatives (`py`):** the prior-year column as presented in each release (`is`, `seg`, `stat`). They supply the two segment recasts (FY2006 for ICS; 2019 for Final Mile Services) and the Q3-19 correction.
- **Units:** USD millions (release thousands ÷ 1,000); shares in millions; per-share as published; statistics as published (loads and stops in units; the model shows thousands).
- **Stock splits:** none since May-2005; nothing is adjusted.
- **Signs:** costs positive; cash-flow payments positive in `cf` (the normaliser applies the statement signs).
- **Null vs zero:** "—" = 0.0; a line not presented is omitted. **Never estimate.** Derived values (Q4 basic shares, Q4 dividends per share, discrete quarterly cash flow) are computed in `normalize.py` and noted there.

## Output
One JSON file per period in `data/`: `2006` … `2025` (annual) and `Q1-12` … `Q3-26` (quarters; 2012 quarters are only a cash-flow base).

```json
{
  "period": "Q3-26", "units": "USD millions ...", "sources": ["release url", "10-Q / 10-K url"], "notes": [],
  "is":  {"rev_xfuel": 0, "fuel_rev": 0, "rev": 0, "pt": 0, "sw": 0, "fuel": 0, "da": 0, "supplies": 0, "ins": 0, "ga": 0,
          "taxlic": 0, "comm": 0, "opex": 0, "oi": 0, "net_int": 0, "equity_loss": 0, "ebt": 0, "tax": 0, "ni": 0,
          "sh_d": 0, "eps_d": 0, "sh_b": "2006 release only", "eps_b": "2006 release only"},
  "seg": {"rev_jbi": 0, "rev_dcs": 0, "rev_ics": 0, "rev_fms": 0, "rev_jbt": 0, "rev_sub": 0, "rev_elim": 0, "rev_tot": 0,
          "oi_jbi": 0, "oi_dcs": 0, "oi_ics": 0, "oi_fms": 0, "oi_jbt": 0, "oi_other": 0, "oi_tot": 0},
  "stat": {"jbi_loads": 0, "jbi_rpl": 0, "jbi_loh": 0, "jbi_trucks_avg": 0, "jbi_trailing_eop": 0,
           "dcs_loads": 0, "dcs_rptw": 0, "dcs_trucks_avg": 0, "ics_loads": 0, "ics_rpl": 0, "ics_gpm": 0, "ics_emp": 0,
           "fms_stops": 0, "fms_trucks_avg": 0, "jbt_loads": 0, "jbt_rpl": 0, "jbt_loh": 0, "jbt_trucks_avg": 0},
  "bs":  {"cash": 0, "ar": 0, "tca": 0, "ppe_gross": 0, "accdep": 0, "ppe": 0, "oa": 0, "ta": 0, "debt_cur": 0, "ap": 0, "claims": 0,
          "payroll": 0, "oth_accr": 0, "dit_cur": 0, "tcl": 0, "ltd": 0, "lt_claims": 0, "oltl": 0, "dit": 0, "eq": 0, "tle": 0, "shares": 0},
  "cf":  {"ytd_months": 9, "ni": 0, "da": 0, "sbc": 0, "gain": 0, "deftax": 0, "cfo": 0, "capex": 0, "sale": 0, "acq": 0, "cfi": 0,
          "bb": 0, "div": 0, "cff": 0, "cfo_rel": 0, "netcapex_rel": 0},
  "x":   {"sh_b": 0, "eps_b": 0, "eps_d": 0, "dps": 0, "dps_paid": 0, "oi": 0, "ni": 0, "amort": 0, "gwint": 0, "gw": 0, "rou": 0},
  "py":  {"is": {}, "seg": {}, "stat": {}}
}
```

## Company-specific keys
- **Segments:** Intermodal (`jbi`), Dedicated Contract Services (`dcs`), Integrated Capacity Solutions (`ics`, from 2007), Final Mile Services (`fms`, from Q1-20) and Truckload (`jbt`; "Truck" to Q2-21). Segment revenue is gross of intersegment eliminations and includes fuel surcharge.
- **Statistics:** a statistic belongs to the segment named by the last segment heading. Sub-headings such as "Tractors (end of period)" or "Trucks (end of period)" are not segment headings (the latter must not be read as the Truck segment).
- **Non-GAAP:** J.B. Hunt publishes none. `manual_items.json` → `company_items` lists the charges and benefits the company quantified in release text, each with its wording, pre-tax amount, after-tax amount where stated, and source URL. Nothing else is adjusted.
- **Outlook:** `manual_items.json` → `outlook_2026` holds the only forward statements filed on EDGAR (annual tax rate, net capital expenditures). Anything from an earnings call or investor presentation is not a source and must be labelled unverified.

## Self-checks (run before saving; failures go to `notes`)
- Σ expense lines = total operating expenses; revenue − expenses = operating income; operating income − net interest − equity loss = pre-tax earnings; − tax = net earnings (±0.011).
- Σ segment revenue + eliminations = consolidated revenue; Σ segment operating income + other = operating income.
- Net earnings ÷ diluted shares = diluted EPS (±0.005).
- Total assets = total liabilities and equity.

`check_data.py` repeats these on the normalised data and adds XBRL cross-checks, cash and balance-sheet tie-outs, published revenue per load vs revenue ÷ loads, and quarters vs years (1,541 checks).
