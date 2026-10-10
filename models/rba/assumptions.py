"""Forecast inputs (blue cells) for the RB Global model. All are analyst assumptions unless a source is cited."""

Y = (2026, 2027, 2028, 2029, 2030)


def by_year(*vals):
    return dict(zip(Y, vals))


ASSUMP = {
    # GTV per lot y/y (2026E applies to Q3/Q4-26E vs prior-year quarter)
    "gplg_auto": by_year(0.03, 0.025, 0.025, 0.02, 0.02),
    "gplg_het": by_year(0.02, 0.02, 0.02, 0.02, 0.02),
    "gplg_oth": by_year(0.0, 0.0, 0.0, 0.0, 0.0),
    # revenue drivers
    "take": by_year(None, 0.200, 0.200, 0.200, 0.200),
    "take_d26": 0.0,
    "inv_pct": by_year(None, 0.080, 0.080, 0.080, 0.080),
    "inv_rate": by_year(None, 0.070, 0.070, 0.070, 0.070),
    "cs_pct": by_year(None, 0.405, 0.403, 0.401, 0.400),
    "adj_da_pct": by_year(None, 0.043, 0.043, 0.043, 0.043),
    # adjusting items (USDm): quarterly for Q3/Q4-26E, annual 2027E+
    "adj_SBC_q": 18.0, "adj_SBC": by_year(None, 75.0, 80.0, 85.0, 90.0),
    "adj_ACQ_q": 6.0, "adj_ACQ": by_year(None, 10.0, 10.0, 10.0, 10.0),
    "adj_RESTR_q": 2.5, "adj_RESTR": by_year(None, 5.0, 5.0, 5.0, 5.0),
    "adj_LEGAL_q": 2.0, "adj_LEGAL": by_year(None, 6.0, 6.0, 6.0, 6.0),
    "adj_taxrate": 0.25,
    # tax / preferred / dividends
    "etr": by_year(None, 0.24, 0.24, 0.24, 0.24),
    "pref_div_q": 6.7, "pref_div_y": 26.7,
    "dps_q": 0.33,
    "acq_rev_2026": 120.0,
    # cash flow
    "dtax": by_year(-50.0, -45.0, -40.0, -35.0, -30.0),
    "debt_cost_amort": 9.0,
    "capi_pct": 0.024,
    "capex_pct": by_year(None, 0.0725, 0.0700, 0.0675, 0.0650),
    "shares_issued_cash": 40.0,
    "wht": -25.0,
    "bb_issued": 0.6,
    # schedules
    "amort_sched": by_year(297.0, 237.0, 183.0, 161.0, 154.0),
    "amort_note": ("Acquired-intangible amortization (adjusting item). Estimate = FY2025 10-K expected amortization of all "
                   "intangibles (2026 $379.0m, 2027 $304.1m, 2028 $229.8m, 2029 $193.4m, 2030 $175.9m) less amortization "
                   "of existing software (~$90m 2026 → ~$30m 2030), plus ~$8m p.a. for BigIron / Blackmon (2026 "
                   "PPA). 1H/26 actual $146.8m."),
    "capi_amort": by_year(95.0, 105.0, 115.0, 125.0, 135.0),
    "acq_intang_pct": by_year(0.25, 0.25, 0.25, 0.25, 0.25),
    "dil_sec": by_year(1.2, 1.2, 1.2, 1.2, 1.2),
    "dps_g": by_year(None, 0.06, 0.06, 0.06, 0.06),
    "px_g": by_year(None, 0.07, 0.07, 0.07, 0.07),
    "pref_alloc_pct": by_year(0.035, 0.035, 0.035, 0.035, 0.035),
    "debt": by_year(2800.0, 2700.0, 2600.0, 2500.0, 2400.0),
    "debt_note": ("Total debt $2,904m at 30-Jun-26 (revolver / TLA due Apr-2030, $550m 6.75% secured notes due Mar-2028, "
                  "$800m 7.75% unsecured notes due Mar-2031). Base: ~$100m p.a. net repayment; 2028 notes refinanced."),
    "int_rate": by_year(None, 0.060, 0.059, 0.058, 0.058),
    "int_note": "FY25 principal-weighted coupon ~6.4% (6.15% at 30-Jun-26); floating TLA / revolver at SOFR + margin.",
    "cash_rate": by_year(None, 0.025, 0.025, 0.025, 0.025),
    # working capital (days / %)
    "d_ar": by_year(16.0, 16.0, 16.0, 16.0, 16.0),
    "d_app": by_year(10.5, 10.5, 10.5, 10.5, 10.5),
    "d_inv": by_year(45.0, 45.0, 45.0, 45.0, 45.0),
    "tol_pct": by_year(0.175, 0.175, 0.175, 0.175, 0.175),
}

SCENARIOS = {
    "gtv_g": (0.11, 0.10, 0.09),
    "ebitda": (1545.0, 1520.0, 1495.0),
    "tax": 0.24,
    "capex": 375.0,
    "auto": (0.050, 0.050, 0.045, 0.045), "auto_d": (0.02, -0.03),
    "het": (0.060, 0.045, 0.040, 0.040), "het_d": (0.02, -0.04),
    "oth": (0.050, 0.050, 0.050, 0.050), "oth_d": (0.02, -0.03),
    "margin": (0.305, 0.310, 0.315, 0.320), "margin_d": (0.010, -0.015),
    "buyb": (200.0, 400.0, 400.0, 450.0, 500.0), "buyb_d": (150.0, -200.0),
}

# Company adjusted-measure definitions — flagged in the column where each change takes effect.
# Format: "<short flag>||<cell comment detail>"
DEF_EBITDA = {
    "2006": "No EBITDA / adj. EBITDA published (2006–10, Canadian GAAP)||Ritchie Bros. did not publish EBITDA or "
            "adjusted EBITDA in its 2006–2010 40-F MD&A. Model EBITDA = net income + D&A + interest expense − interest "
            "income + tax; no adjusting items.",
    "2011": "IFRS: EBITDA margin only||2011–2012 (IFRS): the company published an EBITDA margin only (36.9% / 36.8%), "
            "defined as earnings from operations + D&A. Dollar amounts are model-computed.",
    "Q1/13": "IFRS EBITDA = earnings from operations + D&A||2013–2014 quarterly releases (Form 6-K) published EBITDA "
             "(IFRS earnings from operations + D&A) from Q2/13; Q1/13 margin only.",
    "Q4/14": "Adj. EBITDA introduced (ex property gains, impairment, reorg.)||Q4-14 release first published 'adjusted "
             "operating income' and 'adjusted EBITDA' excluding significant non-recurring items (gain on sale of "
             "excess property, Narita impairment, management reorganization, CEO separation).",
    "2013": "FY: US GAAP; EBITDA = operating income + D&A||FY2013–14 (US GAAP, FY2015 10-K): EBITDA defined as "
            "operating income + D&A, i.e. excluding other income (≈$2.5m in 2013), hence the residual vs the model "
            "EBITDA (net-income based).",
    "2014": "FY: US GAAP basis (FY2015 10-K recast)||FY2013 and FY2014 annual figures are US GAAP as recast in the FY2015 "
            "10-K (gains, impairment and FX move into operating income); quarters remain IFRS.",
    "Q1/15": "US GAAP; adj. EBITDA = adj. op. income + D&A (TTM only)||2015–Q1/16: adjusted EBITDA disclosed only as the "
             "trailing-12-month denominator of debt / adjusted EBITDA (adjusted operating income + D&A). Q1/15 and Q4 "
             "figures derived as FY − 9M.",
    "Q2/16": "EBITDA redefined from net income||Q2-16 10-Q: EBITDA = net income + D&A + interest expense − interest "
             "income + current tax − deferred tax recovery; adjusted EBITDA excludes 'adjusting items' (significant "
             "non-recurring items). Quarterly adjusted EBITDA published from Q3-16 (FY2015 restated to $212.4m).",
    "Q2/17": "IronPlanet items adjusted||From Q2/17 (IronPlanet close): accelerated vesting of assumed options, "
             "acquisition & finance-structure advisory fees and severance / retention are adjusting items; routine "
             "acquisition & integration costs remain in adjusted EBITDA.",
    "Q1/19": "Adj. EBITDA in earnings release (old definition)||Adjusted EBITDA first presented in the earnings release in "
             "Q1/19. Q1/19–Q2/19 were never republished under the 2021 definition and remain on the prior "
             "'significant non-recurring items' definition.",
    "Q3/19": "2021 definition (restated): + SBC, all acq. costs, PP&E gains||Q3-21 release (4-Nov-2021) redefined adjusted "
             "measures retroactively (Q3/19 onward): add back all share-based payments, all acquisition-related costs and "
             "(gains) losses on PP&E disposals; acquired-intangible amortization added back in adjusted NI only.",
    "Q2/21": "SOX-remediation & advisory/legal added (Q4-21 release)||Q4-21 release (17-Feb-2022) added 'non-recurring "
             "advisory, legal and restructuring costs' and change in fair value of derivatives; SOX remediation costs "
             "added back retroactively to Q2/21–Q3/21; 2020 severance moved into the new line.",
    "Q2/22": "'(Gain) loss on PP&E disposition and related costs'||Q2-22 release: PP&E item renamed to include related "
             "costs; loss on redemption of 2021 Notes adjusted (adjusted NI only).",
    "Q1/23": "RB Global definition (IAA): + IAA prepaid consigned vehicle charges, remeasurements||Q1/23 (IAA close "
             "20-Mar-2023): adds IAA prepaid consigned vehicle charges (purchase-accounting reversal, to Q2/25) and "
             "remeasurements in connection with business combinations (VeriTread); SBC and acquisition / integration "
             "costs continue to be added back.",
    "Q3/23": "Executive transition costs added||Q3-23 release: executive transition costs added; the Q2/23 adjustment for "
             "IAA purchase-accounting depreciation & rent dropped retroactively (Q2/23 adj. EBITDA 307.8 → 306.9).",
    "Q2/25": "Divestiture/deconsolidation (SYNETIQ) & debt refinancing added||Q2-25 release: loss on divestiture and "
             "deconsolidation (LKQ SYNETIQ transaction) and related costs, and debt refinancing costs added.",
    "Q3/25": "Restructuring shown separately||Q3-25 release: restructuring costs presented as a separate adjusting item "
             "(previously within 'other legal, advisory, restructuring and non-income tax expenses').",
    "Q1/26": "'Share-based payments' → 'stock-based compensation' (label only)||Q1-26 release relabelled the SBC item; no "
             "change in amounts.",
}

DEF_NI = {
    "2006": "Not published (statement only)||FY2006 MD&A stated only that earnings 'would have been' $56.2m ($1.61 "
            "pre-split diluted EPS) excluding excess-property items; no formal adjusted measure.",
    "2007": "Adj. net earnings: ex excess-property gains/losses & FX on financing||Ritchie Bros. 40-F MD&A (Canadian GAAP "
            "2007–10, IFRS 2011–12): adjusted net earnings exclude gains/losses on the sale of excess property "
            "(after tax) and one-off FX impacts on financing transactions.",
    "2011": "IFRS basis (2011–14)||IFRS adopted 1-Jan-2011 (2010 restated). FY2011–12 adjusted net earnings on IFRS.",
    "Q1/13": "Ex 'excess property sales and other non-recurring items'||2013 quarterly releases (6-K).",
    "Q4/13": "Base → NE attributable to stockholders; CEO separation adjusted||From Q4/13 the base is net earnings "
             "attributable to stockholders (RBFS 49% NCI).",
    "Q3/14": "Impairment added (Q4/14: management reorganization)||Q3-14: Narita impairment adjusted; Q4-14: management "
             "reorganization (termination benefits).",
    "2014": "FY: US GAAP (FY2015 10-K)||FY2013–14 adjusted NI per the FY2015 10-K (US GAAP, incl. tax-loss utilization).",
    "Q4/15": "US GAAP adj. NI & diluted adj. EPS introduced||Q4-15 release (first US GAAP release): adjusted net income "
             "attributable to stockholders and diluted adjusted EPS exclude significant non-recurring items, incl. "
             "deferred tax-loss utilization.",
    "Q4/16": "Debt extinguishment costs (first below-OI item)||Q4/16: debt extinguishment costs adjusted; acquisition "
             "costs explicitly not adjusted (Q4/16–Q1/17).",
    "Q1/17": "Change in uncertain tax provision adjusted",
    "Q2/17": "IronPlanet-specific items; EPS net of dilutive-securities effect||From Q2/17: accelerated vesting of assumed "
             "options, advisory fees, severance & retention; diluted adjusted EPS net of an 'effect of dilutive "
             "securities'.",
    "Q4/17": "US tax reform deferred-tax remeasurement adjusted",
    "Q3/18": "Gain on sale of equity-accounted investment adjusted",
    "Q3/19": "2021 definition (restated): + SBC, acq. costs, acquired-intangible amortization||Q3-21 release (4-Nov-2021) "
             "applied retroactively to Q3/19 onward: adds back all share-based payments, all acquisition-related costs, "
             "amortization of acquired intangible assets and (gains) losses on PP&E disposals, tax-effected. Q1/19–Q2/19 "
             "remain on the prior definition.",
    "Q2/21": "SOX remediation / advisory & legal; FV of derivatives (Q4-21)",
    "Q2/22": "Loss on redemption of 2021 Notes adjusted",
    "Q1/23": "Two-class EPS: base = NI available to common; allocation to preferred||Q1/23: Series A Senior Preferred "
             "(participating) → base becomes NI available to common stockholders (after preferred dividends and "
             "allocated earnings); adjustments' related allocation to preferred deducted. Adds IAA prepaid consigned "
             "vehicle charges, VeriTread remeasurement, debt redemption costs.",
    "Q3/23": "Executive transition costs added",
    "Q2/25": "SYNETIQ deconsolidation & debt refinancing costs added",
    "Q3/25": "Restructuring separate; RNCI adjustment; J.M. Wood accretion||Q3-25: restructuring shown separately; "
             "redeemable-NCI adjustment deducted in NI available to common and added back in adjusted NI; accretion of "
             "J.M. Wood deferred consideration added back (adjusted NI only).",
    "Q1/26": "'Stock-based compensation' relabel (no change)",
}
