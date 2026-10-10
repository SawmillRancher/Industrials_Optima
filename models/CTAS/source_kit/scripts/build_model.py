"""Build CTAS_Model.xlsx from the MLM template workbook (same formatting & structure)."""
import json, sys, os, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import openpyxl
from openpyxl.utils import get_column_letter as L
from openpyxl.styles import Font, PatternFill, Border, Side, Alignment
from openpyxl.worksheet.datavalidation import DataValidation
import mdl_core as M
from mdl_core import Row, Sheet, PERIODS, BYNAME, HIST, FCQ, FCA, resolve, style_label, style_value, FMT, fill, font
import curated as C
from mdl_rows1 import build_part1
from mdl_rows2 import build_part2
from mdl_rows3 import build_part3

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = json.load(open(os.path.join(BASE, 'edgar/hist.json')))

# ------------------------------------------------------------------ historical helpers
for p, h in H.items():
    if 'rev_urfs_line' in h and 'cogs_urfs' in h and h.get('rev_urfs_line') is not None:
        h.setdefault('gm_urfs_line', h['rev_urfs_line'] - h['cogs_urfs'])

def a_other(p):
    h = H.get(p.name, {})
    if 'rev' not in h: return None
    pub = C.adj_eps(p.name)
    if pub is None: return 0.0
    items = h['sp_trans'] + h['sp_other_op'] + C.INV_CHARGE.get(p.name, 0) + C.SGA_ITEMS.get(p.name, 0) - h['nonop_gain']
    etr = h['tax'] / h['pbt'] if h['pbt'] else 0.25
    rate = min(max(etr, 0.15), 0.40)
    nic = h['pbt'] - h['tax'] + h['eq_at']
    model = nic + items - items * rate - h['eq_at'] + C.TAX_ITEMS.get(p.name, 0)
    return round(pub * h['sh_dil'] - model, 3)

# ------------------------------------------------------------------ scenario / input table spec
OUTLOOK = [('rev', '  FY27 revenues ($m)', 12270, 12210, 12150, '#,##0', 'Raised to $12.15–12.27bn in the Q1/27 release (from $12.10–12.25bn); excludes UniFirst & future M&A.'),
           ('eps', '  FY27 adjusted diluted EPS ($)', 5.54, 5.495, 5.45, '0.00', 'Raised to $5.45–5.54 (from $5.36–5.50); excludes UniFirst transaction costs; FY26 adj. $4.94.')]
def fy26(k):
    return H['FY2026'][k]
rev26 = fy26('rev'); cogs26 = fy26('cogs_urfs') + fy26('cogs_other'); revu26 = fy26('rev_urfs_line')
POINT = [  # key, label, value, fmt, note
    ('g_int', '  FY27 interest expense, net — guidance ($m)', 103.0, 'n1', 'Q1/27 release: ~$103.0m (FY26 $101.2m), incl. bridge-loan fee amortization; excludes UniFirst funding.'),
    ('g_etr', '  FY27 effective tax rate — guidance', 0.204, 'p1', 'Q1/27 release: 20.4% (FY26 20.2%).'),
    ('g_shares', '  FY27 guidance diluted shares (m; ex-future buybacks)', 404.29, 'n1', 'Q1/27 weighted diluted shares 404.3m (guidance excludes future buybacks).'),
    ('etr_in', '  Effective tax rate FY28E+', 0.21, 'p1', 'Higher UniFirst mix (US-heavy, fewer stock-comp benefits).'),
    ('unf_toggle', '  UniFirst included (1 = yes, 0 = no)', 1, 'gen', 'Default ON per your instruction; set 0 for standalone Cintas (matches company guidance basis).'),
    ('unf_close', '  UniFirst assumed closing date', datetime.date(2026, 12, 31), 'dt', '"Prior to the end of calendar 2026" (Q1/27 release); FTC Second Request 11-Jun-26.'),
    ('unf_sh', '  CTAS shares issued to UNF holders (m)', 14.071, 'n1', '424B3 pro forma: 18.227m UNF shares × 0.7720.'),
    ('unf_debt', '  UniFirst acquisition debt ($m)', 2800.0, 'n1', '424B3 pro forma permanent financing $2.8bn.'),
    ('unf_rate', '  Interest rate on acquisition debt', 0.05, 'p1', '424B3 assumption (±1/8% = $3.5m p.a.).'),
    ('unf_syn_tgt', '  Run-rate cost synergies ($m)', 375.0, 'n1', 'Deal 8-K: ~$375m within four years.'),
    ('unf_syn_cogs', '  Share of synergies in cost of sales', 0.65, 'p1', 'Material, production & delivery (vs G&A).'),
    ('unf_ppe_dep', '  Net PP&E step-up depreciation ($m p.a.)', 0.405, 'n1', '$27.936m new − $27.531m eliminated (424B3).'),
    ('unf_amort_y', '  PPA intangible amortization yrs 1–3 ($m p.a.)', 98.257, 'n1', 'Customer relationships $1,241m/15y + trade names $50m/3y.'),
    ('unf_amort_y2', '  PPA intangible amortization yr 4+ ($m p.a.)', 1241 / 15, 'n1', 'Customer relationships only.'),
    ('unf_gm_in', '  UniFirst standalone gross margin (Cintas presentation)', 0.318, 'p1', 'LTM cost of revenues ex-D&A 63.3% + ~85% of D&A in cost of sales.'),
    ('unf_sga_in', '  UniFirst standalone S&A % of revenue', 0.250, 'p1', 'LTM SG&A ex merger costs 24.3% + non-production D&A.'),
    ('unf_da_in', '  UniFirst standalone D&A % of revenue', 0.050, 'p1', 'LTM D&A 5.7% less acquired-intangible amortization (~0.7%).'),
    ('unf_rent_sh', '  UniFirst revenue mapped to UR&FS line', 0.95, 'p1', 'U&F Service Solutions + Specialty Garments ~95% of UNF revenue.'),
    ('unf_pre_q', '  Pre-close transaction costs per quarter ($m)', 15.0, 'n1', 'Q1/27 $14.4m; Q4/26 $14.0m.'),
    ('unf_close_costs', '  Costs at closing ($m): transaction + retention', 72.7, 'n1', 'Cintas transaction costs $34.0m + retention bonuses $38.7m (424B3).'),
    ('unf_int_tot', '  Integration costs to achieve synergies ($m, total)', 350.0, 'n1', 'Not disclosed; "proportional to G&K" (~$138m for a $2.2bn deal) → ~$350m.'),
    ('unf_int_y1', '  … phasing FY27E', 0.15, 'p1', ''), ('unf_int_y2', '  … phasing FY28E', 0.45, 'p1', ''),
    ('unf_int_y3', '  … phasing FY29E', 0.30, 'p1', ''), ('unf_int_y4', '  … phasing FY30E', 0.10, 'p1', ''),
    ('ma_mult_in', '  Bolt-on EV / sales (x)', 2.0, 'x1', 'Tuck-in uniform / first-aid / fire businesses.'),
    ('ma_oim_in', '  Bolt-on operating margin (after amortization)', 0.15, 'p1', ''),
    ('ma_gmp_in', '  Bolt-on gross margin', 0.45, 'p1', ''),
    ('ma_gw_in', '  Goodwill % of bolt-on spend', 0.70, 'p1', 'FY2026 acquisitions mostly goodwill & service contracts.'),
    ('ma_life_in', '  Bolt-on intangible life (years)', 10, 'n1', ''),
    ('da_pct_in', '  Legacy D&A % of legacy revenues (FY28E+)', 0.043, 'p1', 'FY26 4.6%; Q1/27 4.2%.'),
    ('dps_g_in', '  Dividend per share growth FY28E+', 0.12, 'p1', '10-yr DPS CAGR ~17%; FY27 +15.6%.'),
    ('adj_tax_in', '  Tax rate on adjusting items (forecast)', 0.25, 'p1', '424B3 blended statutory rate.'),
    ('capex27_in', '  Capex % of revenues FY27E', 0.037, 'p1', 'FY26 3.5%; Q1/27 3.6%; + UniFirst from closing.'),
    ('capex_in', '  Capex % of revenues FY28E+', 0.039, 'p1', 'UniFirst ~6.3% of revenue + integration/automation.'),
    ('bb27_in', '  FY27E buybacks after Q1 ($m)', 229.0, 'n1', '$544.7m repurchased in Q1 and to 22-Sep-2026 (Q1 $315.7m) → $229.0m; assumed paused thereafter.'),
    ('bb_q_sh', '  Net diluted share reduction per quarter, Q2–Q4/27E (m)', 1.0, 'n1', 'Sep-2026 buybacks ($229m ≈ 1.1m shares) roll through Q2; modest net reduction thereafter.'),
    ('sh_iss_in', '  Shares issued under equity plans (m p.a.)', 1.2, 'n1', ''),
    ('dso_in', '  DSO (days)', fy26('bs_ar') / rev26 * 365, 'n1', 'FY2026 level.'),
    ('dio_in', '  Inventory days', fy26('bs_inv') / cogs26 * 365, 'n1', 'FY2026 level.'),
    ('unif_in', '  Garments in service % of UR&FS-line revenue', fy26('bs_uniforms') / revu26, 'p1', 'FY2026 level.'),
    ('oca_in', '  Prepaid & other CA % of revenue', (fy26('bs_prepaid')) / rev26, 'p1', 'FY2026 level.'),
    ('dpo_in', '  Payable days', fy26('bs_ap') / cogs26 * 365, 'n1', 'FY2026 level.'),
    ('acomp_in', '  Accrued compensation % of revenue', fy26('bs_accr_comp') / rev26, 'p1', 'FY2026 level.'),
    ('aliab_in', '  Accrued liabilities % of revenue', fy26('bs_accr_liab') / rev26, 'p1', 'FY2026 level.'),
    ('dtl_rate', '  Deferred tax rate on PPA amortization', 0.25, 'p1', '424B3.'),
    ('dep_sh_in', '  Depreciation share of legacy D&A', 0.62, 'p1', 'FY2026: $318.6m of $512.8m.'),
    ('amort_leg_in', '  Legacy intangible amortization FY27E ($m)', 58.0, 'n1', 'Service contracts (est. from 10-K schedule).'),
    ('mat27_in', '  Note maturities FY27E ($m)', -1000.0, 'n1', '3.70% senior notes due 2027.'),
    ('mat28_in', '  Note maturities FY28E ($m)', -400.0, 'n1', '4.20% senior notes due 1-May-2028.'),
    ('refi_in', '  % of maturities refinanced', 1.0, 'p1', ''),
    ('mincash_in', '  Minimum cash balance ($m)', 250.0, 'n1', 'Cintas runs ~$150–350m cash.'),
    ('notes_rate_in', '  Blended rate on notes & term debt FY28E+', 0.048, 'p1', ''),
    ('fac_rate_in', '  Rate on CP / revolver', 0.045, 'p1', 'SOFR + 70–114bp revolver; A2/P2 CP.'),
    ('cash_yld_in', '  Yield on cash', 0.035, 'p1', ''),
    ('dil_in', '  Dilutive securities (m shares)', 4.0, 'n1', 'Q1/27 diluted − basic = 4.2m.'),
    ('px_in', '  Share price ($) — valuation input', 198.95, 'n2', 'Latest observable on EDGAR: Form 4 phantom-unit credit price 15-Sep-2026 ($198.95). Overwrite with live price.'),
    ('px_g_in', '  Share-price appreciation % p.a. (buyback pricing)', 0.08, 'p1', ''),
]
LEVERS = [  # key, title, years, base values, bull delta, bear delta, fmt, note
    ('URFS_org', 'URFS_org (UR&FS organic revenue growth)', [2028, 2029, 2030, 2031], [.070, .065, .065, .060], .015, -.020, 'p1', 'FY26 UR&FS organic ~7.5%; Q1/27 ~8%. Bull: share gains from UniFirst disruption, hygiene/water penetration; Bear: employment slowdown.'),
    ('FAS_org', 'FAS_org (First Aid & Safety organic growth)', [2028, 2029, 2030, 2031], [.12, .11, .10, .09], .03, -.04, 'p1', 'FY26 14.0%; runway in AEDs, eyewash, safety training.'),
    ('OTH_org', 'OTH_org (All Other: Fire Protection + Uniform Direct Sale)', [2028, 2029, 2030, 2031], [.09, .08, .08, .07], .02, -.03, 'p1', 'FY26 +9.2% reported; fire inspection is recurring/regulatory.'),
    ('URFS_GM', 'URFS_GM (UR&FS gross margin, level)', [2028, 2029, 2030, 2031], [.510, .513, .516, .519], .0075, -.010, 'p1', 'FY26 50.0%; Q1/27 50.8% (SAP, SmartTruck routing, garment reuse).'),
    ('FAS_GM', 'FAS_GM (First Aid & Safety gross margin)', [2028, 2029, 2030, 2031], [.582, .585, .588, .590], .010, -.015, 'p1', 'FY26 57.7%.'),
    ('OTH_GM', 'OTH_GM (All Other gross margin)', [2028, 2029, 2030, 2031], [.494, .498, .501, .504], .010, -.015, 'p1', 'FY26 47.6%; Q1/27 49.5%.'),
    ('SA_pct', 'SA_pct (legacy S&A % of revenues)', [2028, 2029, 2030, 2031], [.271, .269, .267, .265], -.005, .0075, 'p1', 'FY26 27.4%; Bull = more leverage (Δ negative).'),
    ('UNF_g', 'UNF_g (UniFirst standalone revenue growth)', [2027, 2028, 2029, 2030, 2031], [.030, .030, .035, .035, .035], .015, -.025, 'p1', 'UNF 9M/FY26 +3.3%; FY25 +0.2% (53-wk FY24). Bear includes customer attrition during integration / FTC remedies.'),
    ('UNF_syn', 'UNF_syn (synergy realisation, % of $375m run-rate)', [2027, 2028, 2029, 2030, 2031], [.03, .25, .55, .85, 1.0], .10, -.20, 'p1', '"Within four years" of closing; G&K synergies were achieved ahead of plan.'),
    ('MA_spend', 'MA_spend (bolt-on acquisitions, $m)', [2028, 2029, 2030, 2031], [300, 350, 400, 450], 200, -200, 'n1', 'FY24–26 acquisitions $0.1–0.4bn p.a.'),
    ('LEV', 'LEV (target net debt / Adjusted EBITDA for buybacks, x)', [2028, 2029, 2030, 2031], [1.25, 1.25, 1.25, 1.25], 0.5, -0.5, 'x2', 'Cintas ran 0.7–1.4x FY2019–26; 1.5x at the UniFirst close (deal 8-K). Bull = more aggressive capital return; Bear = deleveraging bias.'),
]

def build(out_path, switch='Base', snaps=None):
    wb = openpyxl.load_workbook(os.path.join(BASE, 'tmpl/MLM_Model.xlsx'))
    old = wb['Model']
    wb.remove(old)
    ws = wb.create_sheet('Model', 0)
    S = Sheet(start_row=8)

    # scenario table layout (rows from 9 in CS..CW) — registered first so formulas can reference them
    srow = 9
    scn_rows = []   # (row, kind, payload)
    scn_rows.append((srow, 'title', None)); srow += 2
    scn_rows.append((srow, 'outhead', None)); out_rows = {}; srow += 1
    for k, lab, hi, mid, lo, fmt, note in OUTLOOK:
        out_rows[k] = srow; scn_rows.append((srow, 'outrow', (k, lab, hi, mid, lo, fmt, note))); srow += 1
    srow += 1
    scn_rows.append((srow, 'pthead', None)); srow += 1
    for item in POINT:
        S.R[item[0]] = srow; scn_rows.append((srow, 'pt', item)); srow += 1
    srow += 1
    lever_rows = {}
    for lv in LEVERS:
        key, title, years, base, db, dr, fmt, note = lv
        hdr = srow; scn_rows.append((srow, 'levhead', lv)); srow += 1
        for y, v in zip(years, base):
            lever_rows[(key, y)] = srow; scn_rows.append((srow, 'levrow', (key, y, v, hdr, fmt))); srow += 1
        srow += 1
    SW = M.SWITCH
    def scn(key, p, fy27=False):
        r = lever_rows[(key, p.fy)]
        return 'CHOOSE(MATCH(%s,{"Bull","Base","Bear"},0),$%s$%d,$%s$%d,$%s$%d)' % (SW, L(M.SCN_BULL), r, L(M.SCN_BASE), r, L(M.SCN_BEAR), r)
    def outlook(k):
        r = out_rows[k]
        return 'CHOOSE(MATCH(%s,{"Bull","Base","Bear"},0),$%s$%d,$%s$%d,$%s$%d)' % (SW, L(M.SCN_BULL), r, L(M.SCN_BASE), r, L(M.SCN_BEAR), r)
    PPA = [
        ('ppa_cash', '  Cash consideration ($155.00 × 18.227m UNF shares & vested awards)', '=2825.669', 'Paid at closing; funded with $2.8bn acquisition debt + balance-sheet cash.'),
        ('ppa_eq', '  Share consideration (14.071m CTAS shares × $179.17 + $4.9m awards)', '=2525.987', '424B3 pro forma basis (Cintas price 17-Apr-2026); final value set at closing.'),
        ('ppa_cashacq', '  Cash acquired (net of $84.0m UniFirst seller costs paid at closing)', '=73.458', ''),
        ('ppa_nwc_a', '  Receivables, inventories, garments in service & prepaid acquired', '=291.58+147.477+236.251+49.598', 'No step-up on inventories or rental garments (424B3).'),
        ('ppa_ppe', '  Property & equipment (buildings & land at fair value)', '=1194.638', 'Net step-up $263.1m (buildings $558.7m / 20y; land $199.5m).'),
        ('ppa_int', '  Identifiable intangibles (customer relationships $1,241m; trade names $50m)', '=1241+50', ''),
        ('ppa_rou', '  Operating lease ROU assets', '=77.804', ''),
        ('ppa_oa', '  Other assets (ex trade names)', '=99.424-50', ''),
        ('ppa_gw', '  Goodwill', '=2854.275', 'Preliminary; historical UNF goodwill $670m eliminated.'),
        ('ppa_nwc_l', '  Payables, accrued compensation & accrued liabilities assumed', '=92.089+72.627+58.954+0.03', ''),
        ('ppa_cll', '  Operating lease liabilities, current', '=20.225', ''),
        ('ppa_dtl', '  Deferred income taxes', '=415.006', 'Incl. $283.8m DTL on purchase-price adjustments at 25%.'),
        ('ppa_lll', '  Operating lease liabilities, long-term', '=59.669', ''),
        ('ppa_lta', '  Accrued liabilities, long-term (incl. environmental policy alignment)', '=195.249', ''),
        ('ppa_nwc', '  Memo: net working capital acquired', '={ppa_nwc_a}-{ppa_nwc_l}', 'Excluded from forecast ΔNWC in FY2027E.'),
    ]
    X = dict(scn=scn, outlook=outlook, pt=None, a_other=a_other, ppa=PPA,
             val_note='VALUATION — share price input $198.95 (latest observable on EDGAR: Form 4 phantom-stock credit price 15-Sep-2026); overwrite with a live quote')
    build_part1(S, H, X)
    build_part2(S, H, X)
    build_part3(S, H, X)

    # ------------------------------------------------------------------ write grid
    NC = M.NOTE_COL
    def put(cell, v, p, row):
        if v is None: return False
        if isinstance(v, str) and v.startswith('='):
            cell.value = resolve(v, p, S.R)
            return True
        cell.value = v
        return False
    for row in S.rows:
        r = row.r
        b = ws.cell(r, 2)
        if row.style == 'blank':
            continue
        b.value = row.label
        style_label(b, row.style)
        if row.style in ('sec', 'sub'):
            for p in PERIODS:
                c = ws.cell(r, p.col); c.fill = fill(M.F_DARK if row.style == 'sec' else M.F_GREEN)
            ws.cell(r, 2).fill = fill(M.F_DARK if row.style == 'sec' else M.F_GREEN)
            n = ws.cell(r, NC); n.value = row.note; n.font = font(12, True, M.WHITE); n.fill = fill(M.F_DARK if row.style == 'sec' else M.F_GREEN)
            continue
        if row.style == 'head':
            continue
        for p in PERIODS:
            c = ws.cell(r, p.col)
            if not p.fc:
                src = row.h
            elif p.is_q:
                src = row.fq
            elif p.name == 'FY2027':
                src = row.f27
            else:
                src = row.fa
            v = src(p) if callable(src) else src
            if isinstance(v, float):
                v = round(v, 6)
            isf = put(c, v, p, row)
            if v is not None or p.fc:
                style_value(c, row.style, row.fmt, p, isf)
            if row.style == 'def' and v is not None:
                c.font = font(10, True, 'FFC00000')
        n = ws.cell(r, NC)
        if row.note:
            n.value = row.note
        n.font = font(10); n.fill = fill(M.F_FC)
        if row.cagr:
            P = BYNAME
            specs = [('FY2031', 'FY2026', 5), ('FY2026', 'FY2021', 5), ('FY2026', 'FY2016', 10), ('FY2026', 'FY2006', 20)]
            for cc, (e, s_, n_) in zip(M.CAGR_COLS, specs):
                cell = ws.cell(r, cc)
                cell.value = f'=IFERROR(({P[e].L}{r}/{P[s_].L}{r})^(1/{n_})-1,"n/m")'
                cell.font = font(12, True); cell.number_format = '0%;\\(0%\\);"n/m"'
                cell.fill = fill(M.F_TOTAL)
        if row.level:
            ws.row_dimensions[r].outlineLevel = row.level
            ws.row_dimensions[r].hidden = False

    # ------------------------------------------------------------------ header block
    ws['B2'] = 'Cintas Corporation (NASDAQ: CTAS) — 3-Statement Financial Model'
    ws['B2'].font = font(16, True, 'FF1F3864')
    ws.row_dimensions[2].height = 21
    ws['B3'] = ('US GAAP as reported · USD millions (per-share data in USD, restated for the 4-for-1 split of Sep-2024; shares in millions) · Fiscal years end 31-May · '
                'Source: Cintas Forms 10-K / 10-Q and Form 8-K earnings releases (Ex. 99), merger 8-K (10-Mar-2026), S-4 / 424B3 (UniFirst pro forma), UniFirst 10-K / 8-K, SEC EDGAR CIK 0000723254 '
                '(investor-relations releases are the same documents as filed on EDGAR)')
    ws['B3'].font = font(10, False, 'FF595959')
    ws['B4'] = ('Basis notes: fiscal year ends 31-May (Q1 = Jun–Aug). Quarters as originally reported. Segments: Rental / Uniform Direct Sales / First Aid, Safety & Fire / Document Management to FY2015; '
                'UR&FS / First Aid & Safety / All Other from FY2016 (FY2015 recast). Shred-it partnership Apr-2014 (Document Shredding deconsolidated); document storage sold FY2015–16; Shred-it stake sold FY2017 '
                '(discontinued operations FY2015–2020); G&K Services acquired 21-Mar-2017; 4-for-1 stock split 11-Sep-2024. UniFirst acquisition pending (FTC Second Request) — modelled from an assumed 31-Dec-2026 close '
                '(toggle); NOT in company FY27 guidance.')
    ws['B4'].font = font(10, False, 'FFC00000')
    ws.cell(1, NC).value = 'SCENARIO SWITCH ▼ (Bull / Base / Bear) — drives all scenario-linked forecast drivers'
    ws.cell(1, NC).font = font(10, True, 'FFC00000'); ws.cell(1, NC).fill = fill(M.F_FC)
    sw = ws.cell(2, NC); sw.value = switch; sw.font = font(12, True, M.BLUE); sw.fill = fill('FFFFFF00')
    sw.alignment = Alignment(horizontal='center'); sw.border = Border(top=Side(style='medium'), bottom=Side(style='thin'), left=Side(style='medium'), right=Side(style='medium'))
    dv = DataValidation(type='list', formula1='"Bull,Base,Bear"', allow_blank=False); ws.add_data_validation(dv); dv.add(sw)
    ws['B6'] = '(USDm)'
    for c_ in range(2, NC + 1):
        cell = ws.cell(6, c_); cell.font = font(12, True, M.WHITE); cell.fill = fill(M.F_DARK); cell.alignment = Alignment(horizontal='center' if c_ > 2 else 'left')
    for p in PERIODS:
        ws.cell(6, p.col).value = M.header(p)
        if p.fc:
            ws.cell(5, p.col).fill = fill(M.F_FC)
    ws.cell(6, NC).value = 'Modelling Notes'
    for cc, a, b_, c_ in zip(M.CAGR_COLS, ['Forecast', 'Historical', 'Historical', 'Historical'], ['5Y CAGR', '5Y CAGR', '10Y CAGR', '20Y CAGR'], ["26-'31", "21-'26", "16-'26", "06-'26"]):
        for rr, v in ((5, a), (6, b_)):
            cell = ws.cell(rr, cc); cell.value = v; cell.font = font(12, True, M.WHITE); cell.fill = fill(M.F_CAGRH); cell.alignment = Alignment(horizontal='center')
        cell = ws.cell(7, cc); cell.value = c_; cell.font = font(9, False, 'FF666666'); cell.fill = fill(M.F_FC); cell.alignment = Alignment(horizontal='center')

    # ------------------------------------------------------------------ scenario table
    cl, cb, cbase, cr, cn = M.SCN_LBL, M.SCN_BULL, M.SCN_BASE, M.SCN_BEAR, M.SCN_NOTE
    for r, kind, pl in scn_rows:
        if kind == 'title':
            ws.cell(r, cl).value = 'SCENARIO INPUT TABLE — driver assumptions per Bull / Base / Bear'; ws.cell(r, cl).font = font(11, True, M.BLACK)
            for c_, v in ((cb, 'Bull'), (cbase, 'Base'), (cr, 'Bear')):
                x = ws.cell(r, c_); x.value = v; x.font = font(12, True); x.fill = fill(M.F_TOTAL); x.alignment = Alignment(horizontal='center')
            ws.cell(r, cn).value = 'Bull / Bear = Base + Δ (Δ inputs on each block header). Outlook block = high / mid / low end of FY27 ranges. Blue = input.'
            ws.cell(r, cn).font = font(10)
        elif kind == 'outhead':
            for c_, v in ((cl, 'FY27 outlook — Q1/27 release (23-Sep-26); legacy Cintas, excludes UniFirst'), (cb, 'High'), (cbase, 'Mid'), (cr, 'Low'), (cn, 'Company guidance excludes the UniFirst acquisition — the model adds UniFirst separately.')):
                x = ws.cell(r, c_); x.value = v; x.font = font(12 if c_ != cn else 10, True, M.WHITE if c_ != cn else M.BLACK)
                if c_ != cn: x.fill = fill(M.F_GREEN)
        elif kind == 'outrow':
            k, lab, hi, mid, lo, fmt, note = pl
            ws.cell(r, cl).value = lab; ws.cell(r, cl).font = font(12)
            for c_, v in ((cb, hi), (cbase, mid), (cr, lo)):
                x = ws.cell(r, c_); x.value = v; x.font = font(12, False, M.BLUE); x.number_format = fmt
            ws.cell(r, cn).value = note; ws.cell(r, cn).font = font(10)
        elif kind == 'pthead':
            x = ws.cell(r, cl); x.value = 'Point estimates & structural inputs (all cases)'; x.font = font(12, True, M.WHITE); x.fill = fill(M.F_GREEN)
            for c_ in (cb, cbase, cr): ws.cell(r, c_).fill = fill(M.F_GREEN)
        elif kind == 'pt':
            k, lab, v, fmt, note = pl
            ws.cell(r, cl).value = lab; ws.cell(r, cl).font = font(12)
            x = ws.cell(r, cbase); x.value = v; x.font = font(12, False, M.BLUE); x.number_format = FMT[fmt]
            ws.cell(r, cn).value = note; ws.cell(r, cn).font = font(10)
        elif kind == 'levhead':
            key, title, years, base, db, dr, fmt, note = pl
            x = ws.cell(r, cl); x.value = title; x.font = font(12, True, M.WHITE); x.fill = fill(M.F_GREEN)
            y = ws.cell(r, cbase); y.value = 'Δ →'; y.font = font(12, True, M.WHITE); y.fill = fill(M.F_GREEN); y.alignment = Alignment(horizontal='center')
            dfmt = '\\+0.0%;\\-0.0%' if fmt == 'p1' else ('\\+#,##0;\\-#,##0' if fmt == 'n1' else '\\+0.00\\x;\\-0.00\\x')
            for c_, v in ((cb, db), (cr, dr)):
                z = ws.cell(r, c_); z.value = v; z.font = font(12, True, M.BLUE); z.fill = fill(M.F_SCHED); z.number_format = dfmt; z.alignment = Alignment(horizontal='center')
            ws.cell(r, cn).value = note; ws.cell(r, cn).font = font(10)
        elif kind == 'levrow':
            key, yv, v, hdr, fmt = pl
            ws.cell(r, cl).value = f'  FY{yv}E'; ws.cell(r, cl).font = font(12)
            x = ws.cell(r, cbase); x.value = v; x.font = font(12, False, M.BLUE); x.number_format = FMT[fmt]
            for c_ in (cb, cr):
                z = ws.cell(r, c_); z.value = f'={L(cbase)}{r}+${L(c_)}${hdr}'; z.font = font(12, False, M.BLACK); z.number_format = FMT[fmt]

    # ------------------------------------------------------------------ column layout
    ws.column_dimensions['A'].width = 2.43
    ws.column_dimensions['B'].width = 62
    for p in PERIODS:
        cd = ws.column_dimensions[p.L]
        if p.is_q:
            cd.width = 11.43 if p.fc else 9.57
            cd.outlineLevel = 1; cd.hidden = True
        else:
            cd.width = 14.14
    ws.column_dimensions[L(NC)].width = 86.86
    ws.column_dimensions[L(NC + 1)].width = 2.0
    for cc, w in zip(M.CAGR_COLS, (14.14, 12.43, 13.43, 13.43)):
        ws.column_dimensions[L(cc)].width = w
    ws.column_dimensions[L(M.CAGR_COLS[-1] + 1)].width = 2.0
    ws.column_dimensions[L(M.CAGR_COLS[-1] + 2)].width = 6.0
    ws.column_dimensions[L(cl)].width = 46; ws.column_dimensions[L(cn)].width = 60
    for c_ in (cb, cbase, cr): ws.column_dimensions[L(c_)].width = 11.57
    ws.sheet_format.outlineLevelRow = 2
    ws.sheet_format.outlineLevelCol = 1
    ws.sheet_view.showGridLines = False
    ws.sheet_view.zoomScale = 70
    ws.freeze_panes = 'C8'
    for r in range(1, S.next + 1):
        if ws.row_dimensions[r].height is None and r != 2:
            ws.row_dimensions[r].height = 15
    wb._sheets.insert(0, wb._sheets.pop(wb._sheets.index(ws)))
    import build_support as BS
    BS.build_bbb(wb, S.R); BS.build_dcf(wb, S.R); BS.build_charts(wb, S.R)
    if 'DCF_old' in wb.sheetnames:
        wb.remove(wb['DCF_old'])
    if snaps:
        bb = wb['Bull-Base-Bear']
        for r in range(9, 51):
            for c in list(range(15, 25)) + list(range(27, 37)):
                if not isinstance(bb.cell(r, c).value, str) or not str(bb.cell(r, c).value).startswith('='):
                    bb.cell(r, c).value = None
        for name, off in (('Bull', 12), ('Bear', 24)):
            vals = snaps.get(name, {})
            for (r, c), v in vals.items():
                bb.cell(r, c + off).value = v
            bb.cell(5, 15 if off == 12 else 27).value = name
            bb.cell(5, 16 if off == 12 else 28).value = f'Snapshot (values) — Model run with switch = {name}'
    json.dump({k: v for k, v in S.R.items()}, open(os.path.join(BASE, 'rowmap.json'), 'w'), indent=0)
    from openpyxl.workbook.properties import CalcProperties
    wb.calculation = CalcProperties(fullCalcOnLoad=True)
    wb.active = 0
    wb.save(out_path)
    return S

def recalc(path, outdir):
    import subprocess
    subprocess.run(['soffice', '--headless', '--calc', '--convert-to', 'xlsx', '--outdir', outdir, path], check=True, capture_output=True)
    return os.path.join(outdir, os.path.basename(path))

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, 'out', 'CTAS_Model.xlsx')
    tmpd = os.path.join(BASE, 'out/snap'); os.makedirs(tmpd, exist_ok=True)
    snaps = {}
    for name in ('Bull', 'Bear'):
        pth = os.path.join(tmpd, f'CTAS_{name}.xlsx')
        build(pth, switch=name)
        calc = recalc(pth, os.path.join(tmpd, 'calc'))
        wbv = openpyxl.load_workbook(calc, data_only=True)['Bull-Base-Bear']
        vals = {}
        for r in range(9, 51):
            for c in range(3, 13):
                v = wbv.cell(r, c).value
                if isinstance(v, (int, float)):
                    vals[(r, c)] = v
        snaps[name] = vals
    S = build(out, switch='Base', snaps=snaps)
    print('rows', S.next)
