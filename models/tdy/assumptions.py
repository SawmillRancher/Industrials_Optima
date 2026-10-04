"""Forecast inputs (blue cells) for the Teledyne model. All are analyst assumptions unless a source is cited."""

Y = (2026, 2027, 2028, 2029, 2030)


def by_year(*vals):
    return dict(zip(Y, vals))


ASSUMP = {
    # cost drivers
    "cogs_pct": by_year(None, 0.564, 0.562, 0.560, 0.558),
    "adj_da_pct": by_year(None, 0.0195, 0.0195, 0.0195, 0.0195),
    "sbc_pct": by_year(None, 0.0065, 0.0065, 0.0065, 0.0065),
    "corp_pct": by_year(None, 0.0135, 0.0133, 0.0131, 0.0130),
    # corporate adjusting items (transaction & integration costs), USDm
    "corp_items_q": 0.5, "corp_items": by_year(None, 5.0, 5.0, 5.0, 5.0),
    # incremental acquisition sales for Q3/Q4-26E (Excelitas A&D annualised Feb-2026; 2026 bolt-ons)
    "acq_sales_q": 8.0,
    # below the line
    "pension": by_year(None, 10.0, 10.0, 10.0, 10.0),
    "etr": by_year(None, 0.215, 0.215, 0.215, 0.215),
    "adj_taxrate": by_year(None, 0.235, 0.235, 0.235, 0.235),
    # future M&A (lever inputs other than spend)
    "ma_mult": by_year(None, 3.0, 3.0, 3.0, 3.0),
    "ma_g": by_year(None, 0.04, 0.04, 0.04, 0.04),
    "ma_mg": by_year(None, 0.20, 0.20, 0.20, 0.20),
    "ma_ip": by_year(None, 0.35, 0.35, 0.35, 0.35),
    "ma_life": by_year(None, 12.0, 12.0, 12.0, 12.0),
    # cash flow
    "dtax": by_year(-20.0, -20.0, -20.0, -20.0, -20.0),
    "capex_pct": by_year(None, 0.020, 0.020, 0.020, 0.020),
    "options_proceeds": by_year(50.0, 40.0, 40.0, 40.0, 40.0),
    "bb_issued": by_year(0.15, 0.15, 0.15, 0.15, 0.15),
    # schedules
    "amort_sched": by_year(226.0, 211.8, 208.9, 165.0, 138.8),
    "amort_note": ("Existing acquired intangibles: FY2025 10-K expected amortization 2027 $211.8m, 2028 $208.9m, 2029 "
                   "$165.0m, 2030 $138.8m. 2026E $226m = FY26 outlook bridge ($3.70/$3.65 per share after tax ≈ "
                   "$225–227m pre-tax; 10-K schedule $219.1m excl. 2026 deals); 1H/26 actual $113.6m."),
    "acq_ip26": by_year(0.30, None, None, None, None),
    "acq_ip26_note": "1H/26 acquisitions $53.4m (bolt-ons); intangibles share estimated at 30% (Excelitas A&D 2025: $208.2m of $702.8m).",
    "dil_sec": by_year(0.6, 0.6, 0.6, 0.6, 0.6),
    "px": 615.0,
    "px_g": by_year(None, 0.07, 0.07, 0.07, 0.07),
    "debt_mand": by_year(-450.1, 0.0, -700.0, 0.0, -427.3),
    "debt_note": ("Debt at 28-Jun-26 $2,027.0m: 2.25% notes $700m due Apr-2028, 2.50% $427.3m due Aug-2030, 2.75% "
                  "$910.8m due Apr-2031 ($450m 1.60% notes repaid Apr-2026); $1.2bn revolver (undrawn, Jun-2029). "
                  "Maturities repaid from cash / revolver."),
    "min_cash": by_year(300.0, 300.0, 300.0, 300.0, 300.0),
    "int_rate": by_year(None, 0.027, 0.030, 0.034, 0.038),
    "int_note": "Gross rate on opening debt: fixed coupons 2.25–2.75% (blended ~2.5% + fees); maturities refinanced on the revolver at ~5%.",
    "cash_rate": by_year(None, 0.030, 0.030, 0.030, 0.030),
    # working capital
    "d_ar": by_year(58.0, 58.0, 58.0, 58.0, 58.0),
    "unb_pct": by_year(0.065, 0.065, 0.065, 0.065, 0.065),
    "d_inv": by_year(112.0, 110.0, 108.0, 106.0, 105.0),
    "d_ap": by_year(50.0, 50.0, 50.0, 50.0, 50.0),
    "acc_pct": by_year(0.09, 0.09, 0.09, 0.09, 0.09),
    "cl_pct": by_year(0.065, 0.065, 0.065, 0.065, 0.065),
}

SCENARIOS = {
    "outlook_hdr": "FY26 outlook — Q2-26 release (22-Jul-26)",
    "outlook_comment": ("FY26 outlook per Teledyne Q2-2026 earnings release (Form 8-K Ex. 99.1, 22-Jul-2026): GAAP diluted "
                        "EPS $20.73–$20.99 and non-GAAP diluted EPS $24.45–$24.65 (raised from $20.08–$20.44 / "
                        "$23.85–$24.15); Q3-26 GAAP EPS $5.10–$5.25, non-GAAP $6.05–$6.15. Bridge: acquired-intangible "
                        "amortization $3.70/$3.65 and transaction & integration costs $0.02/$0.01 per share. No sales, "
                        "tax-rate, capex or FCF guidance."),
    "eps_fy": (24.65, 24.55, 24.45),
    "eps_q3": (6.15, 6.10, 6.05),
    "gaap_fy": (20.99, 20.86, 20.73),
    "tax": 0.215,
    "capex": 125.0,
    "point_note": ("Not guided — analyst estimates: tax rate ≈ 1H/26 ETR before discrete items (Q2-26 21.7%); capex ≈ "
                   "2% of sales (FY25 $117m)."),
    "gr": {
        "di": {"base": (0.060, 0.055, 0.050, 0.050), "d": (0.030, -0.040),
               "note": "Digital Imaging: defense IR / unmanned systems, space sensors, industrial machine vision; "
                       "commercial IR and semis capex cyclical."},
        "inst": {"base": (0.045, 0.045, 0.045, 0.045), "d": (0.020, -0.030),
                 "note": "Instrumentation: marine (offshore energy, defense subsea), environmental (regulation), ETM."},
        "ade": {"base": (0.060, 0.055, 0.050, 0.050), "d": (0.030, -0.040),
                "note": "A&DE: defense electronics (budget growth), commercial aerospace build rates."},
        "es": {"base": (0.040, 0.040, 0.040, 0.040), "d": (0.030, -0.040),
               "note": "Engineered Systems: US Government programs (missile defense, space), energy systems."},
    },
    "mg": {
        "di": {"base": (0.245, 0.250, 0.255, 0.260), "d": (0.010, -0.020),
               "note": "FY25 non-GAAP margin 22.6%; 1H/26 ~24% (mix, tariff refunds)."},
        "inst": {"base": (0.290, 0.293, 0.296, 0.300), "d": (0.010, -0.020), "note": "FY25 28.4%."},
        "ade": {"base": (0.280, 0.283, 0.286, 0.290), "d": (0.010, -0.020), "note": "FY25 27.3% (incl. Excelitas A&D)."},
        "es": {"base": (0.120, 0.120, 0.125, 0.125), "d": (0.010, -0.020), "note": "FY25 10.7%; program-mix driven."},
    },
    "ma": {"base": (750.0, 1000.0, 1000.0, 1000.0), "d": (750.0, -500.0),
           "note": "Acquisition spend ($m). Teledyne 2017–25 ex FLIR averaged ~$0.4bn p.a.; balance-sheet capacity "
                   "(~1x leverage, ~$1.1bn FCF) supports $1bn+ p.a."},
    "buyb": {"base": (0.0, 250.0, 250.0, 250.0, 250.0), "d": (250.0, -250.0),
             "note": "Repurchases are opportunistic (M&A first)."},
}

# Company non-GAAP definitions — flagged in the column where each change takes effect. "<flag>||<comment>"
DEF_OI = {
    "2006": "Not published (2006–Q3/16): GAAP operating income only||Teledyne published no adjusted operating income "
            "before the Q4-2016 release (the 2006–07 'pro forma' measure was EPS only). Current-definition memo below "
            "applies today's definition using 10-K amortization.",
    "2016": "FY2016: e2v charges excluded (Q4/16 only)||FY2016 adjusted OI as re-presented in the Q4-2017 release "
            "(e2v transaction costs in Q4/16).",
    "Q4/16": "Adjusted OI ex e2v acquisition charges (Q4/16–Q4/17)||Q4-2016 release (2-Feb-2017) introduced non-GAAP "
             "measures excluding e2v transaction costs, bridge-facility fees and the FX option contract; 2017 releases "
             "'Adjusted operating income'. Published on the pre-ASU 2017-07 basis — the difference to the recast GAAP "
             "OI is shown as a separate basis line. Severance / facility costs were never excluded.",
    "2018": "Not published (2018–2019): GAAP only||No adjusted measures in 2018–2019 releases (free cash flow only).",
    "Q1/20": "Recast in 2021 releases: ex acquired-intangible amortization||2020 comparatives on the FLIR-era "
             "definition were first published in the Q2-21 (Q1–Q2/20), Q3-21 (Q3/20) and Q4-21 (Q4/20, FY2020) "
             "releases. Only item in 2020: amortization of all acquired intangibles (severance / facility costs not "
             "excluded). Q1-21 release had shown Q1/20 'adjusted' = GAAP.",
    "2020": "FY2020 recast (Q4-21 release)||FY2020 non-GAAP OI 518.9 (16.8%) first published in the Q4-2021 release.",
    "Q1/21": "Current definition (Q2-21 recast): ex amortization, FLIR transaction / integration, step-up||Q1-21 "
             "release (28-Apr-2021) originally called the measure 'adjusted' and excluded only FLIR transaction costs "
             "(OI 141.1, 17.5%). From the Q2-21 release (first after the 14-May-2021 FLIR close) all acquired-intangible "
             "amortization, FLIR inventory step-up and transaction / integration costs are excluded; Q1/21 recast to "
             "150.9 (18.7%).",
    "2021": "FY2021: FLIR definition||FY2021 per the Q4-2022 release.",
    "Q4/22": "Integration-cost credit (Q4/22)||Q4/22: credit of $4.0m for FLIR integration costs.",
    "Q3/23": "'FLIR integration costs' added||Q3-23 release: new 'FLIR integration costs' item (5.8; Q4/23 3.0); 2024 "
             "Q1–Q3 'FLIR integration costs'.",
    "Q4/24": "Trademark impairment excluded; 'transaction & integration costs' label||Q4-24 release: non-cash "
             "impairment of indefinite-lived trademarks $52.5m (DI 49.5, Instrumentation 3.0) excluded — only use; "
             "integration item relabelled 'transaction and integration costs'.",
    "Q1/25": "Inventory step-up excluded again (Micropac / Excelitas A&D)||Q1-25 release: inventory step-up expense "
             "(Micropac 30-Dec-2024; Excelitas A&D / Qioptiq 3-Feb-2025) excluded.",
}
DEF_NI = {
    "2006": "'EPS excl. net pension expense, stock option expense & tax benefit' (2005–07)||Q4-2006 / Q4-2007 releases "
            "('Earnings per share summary'): EPS excluding net pension expense (incl. CAS pension recovery), stock option "
            "expense and income tax benefits — 2006 $2.36, 2007 $2.72 (GAAP $2.26 / $2.72). Per-share reconciliation "
            "only: $m amounts here = per-share items × weighted diluted shares (flagged).",
    "2008": "Not published (2008–Q3/16)||No adjusted EPS from 2008 to Q3-2016 (releases discussed discrete tax items "
            "and ex-discrete tax rates only).",
    "Q4/16": "Non-GAAP EPS ex e2v charges (per-share; $m = EPS × shares)||Q4-2016 release introduced EPS excluding e2v "
             "transaction costs, bridge-facility fees and FX option contract; 2017 'adjusted fully diluted EPS'. "
             "Per-share after-tax items only — $m at weighted diluted shares. Q2–Q3/17 do not exclude discrete tax "
             "benefits.",
    "2016": "FY2016: Q4/16 e2v charges||FY2016 5.37 → 5.53 as re-presented in the Q4-2017 release.",
    "Q4/17": "Tax Act provisional charge also excluded||Q4/17 and FY2017 also exclude the $4.7m provisional US Tax Act "
             "charge.",
    "2018": "Not published (2018–2019)||No adjusted EPS in 2018–2019 releases (Tax Act true-ups inside discrete tax "
            "items).",
    "Q1/20": "Recast in 2021 releases: ex acquired-intangible amortization||2020 comparatives (FLIR-era definition) "
             "first published in the 2021 releases; amortization the only item (tax effect derived from the company's "
             "after-tax amounts).",
    "2020": "FY2020 recast (Q4-21 release)||FY2020 non-GAAP NI 431.6, EPS $11.41.",
    "Q1/21": "Current definition (Q2-21 recast): amortization, FLIR transaction / integration, step-up, financing fees, "
             "tax-law remeasurement||Original Q1-21 'adjusted' EPS $3.02 excluded only FLIR transaction and debt "
             "costs; recast in the Q2-21 release to $3.19 incl. all acquired-intangible amortization. Bridge shows "
             "pre-tax items with the tax effect derived from the company's after-tax column.",
    "2021": "FY2021: FLIR definition||FY2021 non-GAAP EPS $16.86.",
    "Q3/21": "'Acquisition-related foreign tax matters' added||Q3-21: interest on FLIR income-tax reserves and the UK "
             "deferred-tax remeasurement grouped as a tax item.",
    "Q4/21": "'Acquisition-related tax matters' widened (FLIR reserve settlements)||Q4-21: tax benefits / costs from "
             "settlement or resolution of FLIR tax reserves added (Q4/21 −21.4).",
    "Q3/23": "'FLIR integration costs' added",
    "Q4/24": "Trademark impairment excluded (Q4/24); relabels||Q4-24 release: non-cash trademark impairment excluded; "
             "'FLIR acquisition-related tax matters' label.",
    "Q1/25": "Inventory step-up excluded (Micropac / Excelitas A&D)",
}
