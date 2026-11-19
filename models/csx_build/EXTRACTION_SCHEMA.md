# CSX data extraction: schema and rules

## Sources
- **SEC EDGAR only** (CSX Corporation, CIK 0000277948; no predecessor registrants in the history window). The IR site (investors.csx.com) is blocked; its releases are the 8-K Item 2.02 exhibits: Ex. 99.1 press release and Ex. 99.2 "Quarterly Financial Report" (QFR), which holds every table used here.
- **Text versions** of every document are in `$CSX_SRC/txt`: one table row per line, cells joined by ` | `. File names embed `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/277948/<accession-no-dashes>/<doc>`. Record those URLs in `sources`.
- **Release index:** `data/_releases.json` maps each (fiscal year, quarter) to the first release that prints the full set of tables (income statement, balance sheet, cash flow, volume & revenue).
- **Text quirks:**
  - 2006–07 exhibits put ")" in a separate cell (dropped), so "(25,433" is negative; 2008–19 exhibits break labels across lines inside a cell (collapsed by `parse_release.py`); 2020+ exhibits print "NM" in change columns (kept as null so column positions stay aligned).
  - "—" / "-" means zero.
  - Quarter and year-to-date schedules sometimes share one HTML table; `extract.split_blocks` splits them at the in-table year row.
- **Cross-check:** `$CSX_SRC/cf_277948.json` (XBRL company facts); the subset used by the model is committed as `data/_xbrl.json`.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Quarters:** income statement, markets and special items come from that quarter's release (three-month columns), **as originally reported**. Q4 = the fourth-quarter release's three-month column (never FY − 9M).
- **Annual records:** the fourth-quarter release twelve-month columns (FY2006–FY2025). The 10-K is used for notes (debt, goodwill, acquisitions) in `manual_items.json`.
- **Balance sheet:** the period-end statement (condensed from 2010; the 2010 – Q2/13 releases combine cash and short-term investments, so cash is taken from the cash-flow statement and short-term investments are the remainder).
- **Cash flow:** the **year-to-date** statement; `cf.ytd_months` = 3, 6, 9 or 12. Discrete quarters are derived in `normalize.py`.
- **Markets:** the quarter (or twelve-month) "Volume and Revenue" table, labels as published. Current basis (Chemicals / Agricultural & Food Products / Minerals / Automotive / Metals & Equipment / Forest Products / Fertilizers / Intermodal / Coal / Trucking / Other) from the Q3-2016 release; Q3/15–Q2/16 and FY2015 on that basis come from the recast prior-year comparatives (`py.mkt`) of the Q3-16 … Q2-17 releases. Legacy bases (2006–Q1/10: automotive outside merchandise, coke & iron ore inside coal, international / domestic intermodal; Q2/10–Q4/12: eight merchandise markets; Q1/13–Q2/16: Emerging Markets split into Minerals and Waste & Equipment) are kept as `l_*` memo keys.
- **53-week years:** FY2010 and FY2016 (14-week fourth quarters; the Q4 releases also print a 52-week comparable table, which is not used). Calendar quarters from 2017; last-Friday quarter ends before.
- **Prior-year comparatives (`py`):** the prior-year columns as presented in this release (income statement and markets), for recast detection.
- **Units:** USD millions as published (whole dollars in millions; 2006–08 share counts in thousands are converted to millions); volumes in thousands of units; revenue per unit in $; per share as published.
- **Stock splits:** record shares / EPS / DPS **exactly as published**. `normalize.py` restates by document filing date: ×9 before 1-Jun-2011 (3-for-1 effective 31-May-2011 plus 3-for-1 of 28-Jun-2021), ×3 between, ×1 after.
- **Signs:** as printed in the release (expenses positive, interest expense and tax negative in the 2008+ layout); `normalize.py` makes costs positive and signs two-sided items by their effect on earnings.
- **Null vs zero:** "—" = 0.0. A line not presented = null. **Never estimate.** Any computed value (sum, difference, de-cumulated quarter) is noted.

## Output
One JSON file per period: `data/<period_key>.json`, keys `2006` … `2025`, `Q1-13` … `Q3-26`.

```json
{
  "period": "Q3-26", "fy": 2026, "q": 3,
  "sources": {"release": "https://...", "release_date": "2026-10-21", "filing": "https://... (10-Q / 10-K)"},
  "notes": [],
  "is": {"rev": 4017.0, "labor": 834.0, "mso": 657.0, "dep": 413.0, "fuel": 451.0, "rents": 92.0, "inland": null, "conrail": null,
         "restr": null, "impair": 0.0, "gain_disp": null, "other_exp_lines": [["exact label", "value"]], "tot_exp": 2447.0,
         "st_oi": null, "oth_oi": null, "oi": 1570.0, "oth_inc": 21.0, "debt_rep": null, "int_exp": -207.0, "ebt": 1384.0, "tax": -332.0,
         "cont_ops": null, "disc_ops": null, "ni": 1052.0, "op_margin": 39.1, "sh_d": 1853.0, "sh_unit": "millions",
         "eps_d": 0.57, "eps_cont": null, "eps_disc": null, "dps": null},
  "mkt": [["Chemicals", 176.0, 790.0, 4489.0], ["...", "volume (k units)", "revenue ($m)", "revenue per unit ($)"]],
  "mkt_hdr": ["table caption lines"],
  "seg": {"rev": {"rail": 0, "intermodal": 0, "total": 0}, "oi": {}, "or": {}},
  "fuel": {"gallons": 90.6, "ppg": 4.24, "loco": 384.0, "nonloco": 67.0, "total": 451.0},
  "fsc": {"fsc": 466.0, "lag": -36.0},
  "coal": {"domestic": 10.7, "export": 10.6, "total": 21.3},
  "emp": {"avg_total": 21955.0},
  "stats": {"rtm": 50.7, "gtm": 98.9, "velocity": 18.6, "dwell": 10.6, "cars_online": 128828.0, "fuel_eff": 0.92, "fra_inj": 0.97, "fra_acc": 2.77},
  "adj_raw": [{"hdr": ["..."], "rows": [["GAAP Operating Results", [1087.0, 30.3, 694.0, 0.37]]]}],
  "fcf_pub": 2648.0,
  "cf": {"ytd_months": 9, "ni": 2861.0, "dep": 1239.0, "deftax": 115.0, "impair": 0.0, "cfo": 4216.0, "capex": -1712.0, "sti_buy": -515.0,
         "sti_sell": 153.0, "disp": 144.0, "acq": 0.0, "cfi": -1907.0, "bb": -1061.0, "div": -779.0, "debt_rep": -10.0, "debt_iss": 0.0,
         "std_net": null, "options": null, "cff": -1756.0, "net": 553.0, "beg": 670.0, "end": 1223.0, "lines_raw": [["label", "value"]]},
  "bs": {"cash": 1223.0, "sti": 382.0, "cash_sti": null, "ar": null, "tca": null, "ppe": 37142.0, "affil": 2707.0, "conrail": null, "olta": 1672.0,
         "ta": 45154.0, "cmltd": 1702.0, "std": null, "tcl": null, "ltd": 17102.0, "dit": 8030.0, "oltl": 1331.0, "tl": 30772.0, "te": 14382.0,
         "tle": 45154.0, "lines_raw": [["label", "value"]]},
  "py": {"is": {"...prior-year three-month / twelve-month column..."}, "mkt": [["label", "vol", "rev", "rpu"]]},
  "x": {"sbc": 20.0, "dda": 413.0, "deftax_ytd": 115.0, "goodwill": null, "intang_gw": 258.0, "ar": 1485.0, "sh_out_cover": 1843.398,
        "sh_out_cover_date": "2026-09-30", "sh_out": null, "oi": 1570.0, "ni": 1052.0, "rev": 4017.0, "eps_d": 0.57, "ta": 45154.0, "cfo_ytd": 4216.0,
        "employees": null}
}
```

## Special items (`manual_items.json` → `adjusting_items`)
The release reconciliations are irregular (2006–09 "comparable" tables mixing $m and per-share items; 2017 restructuring / Tax Reform; 2024–25 goodwill impairment), so they are transcribed by hand with the company's label, pre-tax amounts by category (`impair_pre`, `restr_pre`, `gain_pre`, `other_pre` inside operating income; `nonop_pre` below it; `tax_items` per share or $m as published) and the published adjusted operating income / net earnings / EPS, each with its source. Categories follow the playbook codes (IMPAIR, RESTR, GAIN, OTHER, TAXD).

## Self-checks (`check_data.py`)
- **IS:** labor + purchased services & other + fuel + D&A + rents + other lines = total expense; revenue − total expense = operating income; OI + other income − interest − debt repurchase expense = EBT; EBT − tax + discontinued = net earnings; NI ÷ diluted shares = EPS (±0.005).
- **Markets:** Σ markets = total revenue (±1); Σ seven merchandise markets = Total Merchandise (volume and revenue, ±1); volume × revenue per unit ≈ revenue (rounding tolerance).
- **Adjusted:** GAAP OI + items = published adjusted OI; adjusted NI ÷ shares = published adjusted EPS (±0.005).
- **Cash flow:** beginning + net change = ending; ending = balance-sheet cash; operating / investing / financing lines sum to their subtotals; CFO − property additions + disposition proceeds = published FCF.
- **Balance sheet:** TA = TL&E; condensed components sum to totals.
- **XBRL:** revenue, OI, NI, EPS and total assets vs the 10-K / 10-Q facts as first filed.
- **Quarters vs years:** Σ Q1–Q4 = FY for every flow line (±1) and DPS (±0.01).
