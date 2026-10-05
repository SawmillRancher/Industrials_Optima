# CHRW segment data (2014-16) and volume/price KPIs (Q1/13-Q2/26)

## Files
- `segments_2015_2016.csv`: key, period, value, unit, source, note. Segment figures for Q1/15 through Q4/16 (three-month), plus FY2014, FY2015 and FY2016.
- `volume_metrics.csv`: same columns. Y/y % metrics from the earnings release narrative, stored as decimals (for example, -0.035 = down 3.5%). Each row quotes the release text (20 words or fewer).
- `raw/`: the downloaded EDGAR source documents and their text conversions. `segA.py`, `entries.py` and `buildB.py` rebuild the CSVs. `entries.py` holds the hand-curated values and quotes. `buildB.py` checks that each quote appears verbatim in the release, that the number matches and that the sign is right.

## Task A: segments
- **The 2015 10-Qs, the FY2015 10-K and the 2016 10-Qs (Q1-Q3) report ONE operating segment.** CHRW first adopted NAST / Global Forwarding / Robinson Fresh / All Other & Corporate in Q4 2016.
- Recast three-month data for all 8 quarters Q1/15-Q4/16 comes from **8-K filed 2017-01-31, Exhibit 99.3** (acc 0001193125-17-025853, "C.H. Robinson Business Segment Information"). These are direct quarterly figures, so no Q4 = FY − 9M derivation was needed.
- FY2014, FY2015 and FY2016 come from the **FY2016 10-K, Note 10** (filed 2017-03-01). The FY2015 10-K did not recast, so FY2014 comparatives exist only in the FY2016 10-K.
- Keys: `seg_<nast|gf|rf|other>_<rev|rev_gross|netrev|opinc|da|headcount>`, plus `seg_cons_*` (consolidated) and `seg_elim_rev_gross`.
  - `rev` = external revenues, excluding intersegment. This matches the release segment tables ("Total revenues (1) Excludes intersegment revenues").
  - `rev_gross` = revenues including intersegment (the filings' "Total Revenues"). The eliminations line is `seg_elim_rev_gross`.
  - Values are in USD thousands; headcount is the average number of employees.
- Checks, all passing:
  - The segments sum to consolidated for rev, netrev, opinc, D&A and headcount in every period, and for rev_gross once eliminations are included.
  - Q1+Q2+Q3+Q4 equals FY for 2015 and 2016 for every segment and field.
  - Q1/16, Q2/16 and Q3/16 match the comparatives in the 2017 10-Qs exactly, except one headcount item.
- **Data-quality flag:** Q3/16 GF average headcount is 3,715 (total 13,862) in Ex 99.3. The Q3/17 10-Q recast shows 3,559 (total 13,706) and excludes APC employees added 9/30/16. The CSV carries the Ex 99.3 value and notes the alternative.
- Not captured: total assets by segment (available in the same sources if needed).

## Task B: volume and price metrics
Period = the quarter the release reports. Q4 releases use the Q4 three-month metrics.

| key | coverage | gaps / notes |
|---|---|---|
| nast_tl_vol | Q1/13-Q2/26 | **Q2/25 not stated** (that release gives only TL AGP/shipment +2.5%). Q1/13-Q2/14 and Q1-Q3/16 = company total TL volume, including Europe. **Q3/14-Q4/15 = North American TL volume**: the total-company figure was not stated, and the note says so. Q4/16 onward = NAST. Q2/21-Q1/22 = "truckload shipments". |
| na_tl_vol | Q1/13-Q3/16 | Extra key: North American TL volume where the pre-NAST releases give it separately. Q1/15-Q4/15 include Freightquote (organic figure in notes). |
| nast_ltl_vol | Q1/13-Q2/26 | **Q1/14 not stated.** 2013-14 values are "total shipments" in the LTL paragraph. 2015 values include Freightquote. |
| nast_total_vol | Q1/18, Q2/21-Q2/26 | Not stated for Q2/22, Q3/22 and Q3/24 (the release says only "increased modestly"). Q4/21 is reported as flat (+1.5% per business day). Q1/21 is given only per business day. |
| nast_*_vol_pbd | Q1/21, Q4/21 | Extra keys for per-business-day volume growth. |
| tl_price_per_mile / tl_cost_per_mile | all 54 quarters | Ex fuel. Pre-Q3/20 = "rate per mile charged" / "truckload transportation costs". From Q3/20 = linehaul. Q2/13 is a single "approximately one percent" for both rate and cost, and that release does not say ex-fuel. Q3/24 cost is "also decreased 0.5%" (odd wording, value kept as -0.5%). |
| tl_agp_per_ship | Q1/21-Q2/26 | Q1/21-Q1/22 are "per load". **Q3/25 not stated.** Q2/26 "held flat" = 0. |
| tl_agp_per_mile | Q1/22-Q2/26 | Complete from Q1/22. |
| ltl_agp_per_order | Q3/21-Q2/26 | Complete from Q3/21. |
| ocean_ship_vol | Q2/15, Q1/19, Q1/20-Q2/26 | Q2/15 and Q1/19 are "flat" = 0. Earlier releases are qualitative only. |
| ocean_agp_per_ship | Q3/21-Q2/26 | |
| air_tons_vol / air_agp_per_ton | from Q2/21 / Q3/21 | Q1/20-Q1/21 give air **shipments** instead; those are under the separate key `air_ship_vol`. |
| customs_vol | Q1/20-Q2/26 | Earlier quarters are qualitative only. |
| customs_agp_per_txn | Q3/22, Q4/23-Q2/26 | Q4/22-Q3/23 not stated. |
| headcount_avg_yoy | 45 of 54 quarters | Company-wide average headcount. **Not stated in the narrative for Q1/18-Q3/19 (only segment-level) or for Q4/22 and Q1/23.** Those could be computed from the release segment tables' average headcount. Values in 2013-15 and Q3/20-Q1/21 include acquisitions; the notes give the contributions. Q1/22-Q3/22 are taken from the personnel-expense sentence. |
| cass_index_yoy | Q4/19-Q4/20, Q3/25-Q2/26 | Present only where the release mentions the index. |

Segment-level headcount sentences (NAST, GF, RF) were deliberately left out of `headcount_avg_yoy`.
