# GD data extraction: schema and rules

Per-period extraction of General Dynamics Corporation (NYSE: GD) from SEC EDGAR into `models/gd_build/data/<period>.json`.
`extract.py` implements it (text-based parser `parse_release.py`); this file documents the rules it follows. Derived from the
DHR / TDY / WAB / WWD schemas.

## Sources
- **SEC EDGAR only** (CIK 0000040533; no predecessor registrants). The investor-relations site is blocked; its releases are the
  8-K Item 2.02 Ex. 99.1 exhibits (the Q4-2009 release is embedded in the 8-K body, `d8k.htm`).
- **Text versions** of every document are in `$GD_SRC/txt`: one table row per line, cells joined by ` | `. File names embed
  `<date>_<form>_<accession>_<doc>`. A document's URL is `https://www.sec.gov/Archives/edgar/data/40533/<accession-no-dashes>/<doc>`.
  Record those URLs in `sources`.
- **Text quirks:** a cell that was only ")" is dropped, so "(25,433" is negative; "—" means zero; footnote markers (") *", "(a)")
  are dropped; the FY2012 release prints the prior year first ("2011 | 2012"), so every value column is resolved from the year
  header, never by position.
- **Cross-check:** `$GD_SRC/cf_40533.json` (XBRL company facts, 10-K / 10-Q facts, as first filed). The subset the model uses is
  committed as `data/_xbrl.json`.
- **EDGAR requests:** send a User-Agent and stay under 5 per second.

## Basis rules
- **Quarters:** statement of earnings, segment table, backlog, deliveries and free cash flow come from that quarter's release
  (three-month columns), **as originally reported**. Q4 = the Q4 release's three-month column (every GD release prints it).
- **Balance sheet:** the quarter-end statement from the release. Annual records: the 10-K balance sheet **wins** when it differs
  (FY2017: total assets 35,046 vs 34,994 preliminary). FY2006: the release had no balance sheet; the 10-K is used.
- **Cash flow:** the **year-to-date** statement; `cf.ytd_months` = 3, 6, 9 or 12. Discrete quarters are derived in `normalize.py`.
- **Annual records:** the Q4 release twelve-month columns, plus the 10-K extras (employees, dividends declared per share, debt
  ladder, amortization schedule).
- **Prior-year comparatives (`py`):** the prior-year column as presented in the following year's release (restatement checks:
  ASC 606 (2017), ASU 2017-07 (2018), the 2020 change in accounting principle, the 2014 axle discontinued operations).
- **Units:** USD millions as published (whole dollars); shares in millions (releases print whole shares to 2018: ÷ 1,000,000);
  per-share as published; units for aircraft; percentages as numbers.
- **Stock splits:** none in the history (the 2-for-1 split of 24-Mar-2006 pre-dates the FY2006 figures as published).
- **Signs:** costs and tax positive (modern releases print them in parentheses; `ext_is` normalises by the sign of operating
  costs); interest, net and other, net signed by their effect on earnings; cash flow as presented.
- **Null vs zero:** "—" = 0.0; a line not presented = null, except "Other, net" which is 0 when the income statement arithmetic
  ties without it. **Never estimate.** Computed values (FY − 9M) are stated in `notes` / `dl_note` / `dps_note`.

## Output
One JSON file per period: `data/<period_key>.json`. Keys: `2006` … `2025`, `Q1-13` … `Q3-26`.

```json
{
  "period": "Q3-26", "fy": 2026, "q": 3,
  "sources": {"release": "https://...", "release_date": "2026-10-30", "filing": "https://..."},
  "is": {"rev": null, "costs": "positive", "oi": null, "int": "signed (expense negative)", "oth": "signed", "ebt": null,
         "tax": "positive = expense", "cont": null, "disc": "signed", "ni": null,
         "eps_b_cont": null, "eps_b_disc": null, "eps_b_ni": null, "eps_d_cont": null, "eps_d_disc": null, "eps_d_ni": null,
         "sh_b": null, "sh_d": null},
  "seg": {"rev": {"aero": null, "combat": null, "marine": null, "ist | it + ms | tech": null, "total": null},
          "oi": {"...": null, "corp": "signed", "total": null}, "margin": {"...": "percent"}},
  "backlog": {"<segment>": {"funded": null, "unfunded": null, "total": null, "pcv": null, "tecv": null}, "total": {}},
  "deliv": {"large_q": null, "mid_q": null, "total_q": null, "*_ytd": null, "preowned_q": null, "aero_orders_q": null,
            "basis": "green | outfitted"},
  "deliv_mdna": [{"green": ["current", "prior"], "outfitted": ["current", "prior"], "hdr": "..."}],
  "fin": {"fcf_q": null, "fcf_ytd": null, "shares_out": "m", "employment": null, "rnd_q": null},
  "cf": {"ytd_months": 9, "ni": null, "dep": null, "amort": null, "sbc": null, "deferred_tax": null, "wc_ar": null,
         "wc_unbilled": null, "wc_inv": null, "wc_ap": null, "wc_adv": null, "wc_ocl": null, "other_op": null, "cfo": null,
         "capex": "negative", "acq": "negative", "cfi": null, "div": "negative", "bb": "negative", "notes_proc": null,
         "notes_rep": "negative", "cp": null, "cff": null, "disc_cash": null, "net": null, "beg": null, "end": null,
         "lines_raw": [["exact label", "value", "op | inv | fin"]]},
  "bs": {"cash": null, "ar": null, "unbilled": null, "inv": null, "oca": null, "tca": null, "ppe": null, "intang": null,
         "gw": null, "oa": null, "tnca": null, "ta": null, "std": null, "ap": null, "adv": null, "ocl": null, "tcl": null,
         "ltd": null, "ol": null, "tncl": null, "cs": null, "surplus": null, "re": null, "ts": null, "aoci": null, "te": null,
         "tle": null, "lines_raw": [["exact label", "value"]]},
  "x": {"sbc_ytd": null, "deftax_ytd": null, "dep_ytd": null, "amort_ytd": null, "dps": "declared, quarter", "ga": null,
        "oi_xbrl": null, "ni_xbrl": null, "rev_xbrl": null, "ta_xbrl": null, "cfo_xbrl": null, "shares_cover": "m (dei)"},
  "py": {"release": "https://...", "is": {}, "seg": {}},
  "extra": {"employees": null, "dps_fy": null, "dps_src": "...", "src": "https://..."},
  "notes": ["computed values; fallbacks used"]
}
```

## Company keys
- **Segments as reported:** `aero`, `combat`, `marine`, `ist` (Information Systems and Technology, 2006 – Q1-18), `it` and `ms`
  (Information Technology, Mission Systems, Q2-18 – 2019), `tech` (Technologies, 2020+), `corp`, `total`. `normalize.py` maps
  IS&T and IT + Mission Systems onto one continuous Technologies line and keeps the originals as memo keys.
- **Backlog:** funded, unfunded, total, estimated potential contract value (IDIQ + unexercised options), total estimated
  contract value, by segment (first block of the exhibit = current quarter end).
- **Gulfstream deliveries:** release exhibit 2006–2009 (green deliveries, completions, pre-owned); 10-Q / 10-K MD&A tables
  2010–2016 ("Green" / "Outfitted"; Q4 = FY − 9M); release exhibit 2017+ (outfitted deliveries under ASC 606, large-cabin /
  mid-cabin / pre-owned); Aerospace orders and book-to-bill from Q4-2018.
- **Non-GAAP:** GD publishes only free cash flow (CFO − capex) and net debt. The one-off FY2012 / Q4-12 and FY2017 / Q4-17
  adjusted-earnings reconciliations are transcribed in `manual_items.json` (`adjusted`) with the company's labels.

## Self-checks (`check_data.py`)
- **IS:** revenue − operating costs = operating earnings; OI + interest, net + other, net = EBT; EBT − tax = continuing ops;
  + discontinued = net earnings (±0.6); NI ÷ diluted shares = diluted EPS (±0.01).
- **Segments:** Σ segment revenue = revenue; Σ segment OI + corporate = OI (±0.6); backlog Σ segments = total (±1).
- **Adjusted (2012, 2017):** continuing ops + items + tax effect = published adjusted earnings; ÷ company diluted shares = adjusted EPS.
- **Cash flow:** beginning + net change = ending; CF ending cash = BS cash; CFO − capex = published FCF; Σ operating lines = CFO.
- **Balance sheet:** TA = TL&E; TL + TE = TL&E.
- **XBRL (2008+):** revenue, OI, NI, total assets vs company facts as first filed (±1.1).
- **Quarters vs years:** Σ Q1–Q4 = FY for every P&L, segment, cash-flow and deliveries key (±1.1).
- **Known exceptions** (documented in `manual_items.json`, `sumq_exceptions` / `fcf_exceptions`): FY2014 axle discontinued
  operations (Q1–Q2 2014 as reported include $59m of axle revenue), FY2016 discontinued operations restated in Q4-16, FY2020
  change in accounting principle ($26m operating costs / other, net), and the Q2-2016 published FCF ($324m) that does not
  reconcile with the release's own year-to-date figures.
