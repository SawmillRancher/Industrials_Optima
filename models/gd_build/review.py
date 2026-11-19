"""Print key Model rows (annual columns 2023-2031E) from a recalculated workbook: python3 review.py <recalculated.xlsx>"""
import sys, openpyxl
from fw import ANN, R
import fw, spec, spec2, build
spec.scen_layout(build.V0); spec.build_spec(build.V0); spec2.build_spec2(build.V0); fw.number_rows(8)
wb = openpyxl.load_workbook(sys.argv[1], data_only=True); ws = wb['Model']
keys = ['is_rev', 'g_rev_g', 'aero_rev', 'marine_rev', 'combat_rev', 'tech_rev', 'aero_m', 'marine_m', 'combat_m', 'tech_m', 'corp', 'is_oi', 'is_oi_m', 'is_int', 'is_ebt', 'is_etr', 'is_ni',
        'sh_dil', 'eps_dil', 'dps', 'r_adj', 'g_bl', 'g_b2b', 'dl_out', 'cf_cfo', 'cf_wc', 'cf_capex', 'fcf', 'cf_div', 'cf_bb', 'cf_notes', 'cf_cp', 'cf_end', 'bs_ta', 'bs_te', 'ds_total',
        'ds_cp', 'lv_nd', 'lv_x', 'bb_sh', 'bb_end', 'ra_roic', 'rn_ronta', 'v_px', 'v_mc', 'v_ev', 'v_eveb', 'v_pe', 'v_fcfy', 'wc_nwc', 'cal_g', 'cal_m']
cols = [ANN[y].c for y in range(2023, 2032)] + [fw.QE]
print('key'.ljust(10), ''.join(f'{ws[c + "6"].value!s:>11}' for c in cols))
for k in keys:
    r = R[k]
    vals = []
    for c in cols:
        v = ws[f'{c}{r}'].value
        vals.append(f'{v:>11.3f}' if isinstance(v, float) and abs(v) < 10 else (f'{v:>11,.0f}' if isinstance(v, (int, float)) else f'{str(v)[:10]:>11}'))
    print(k.ljust(10), ''.join(vals))
d = wb['DCF']; b = wb['Bull-Base-Bear']
print('DCF WACC', d['C13'].value, 'EV', d['C47'].value, 'implied px', d['C51'].value, 'upside', d['C53'].value, 'Mauboussin px', d['C99'].value, 'mkt EV/NOPAT', d['C108'].value)
print('BBB base PT 2030/31', b['G27'].value, b['H27'].value, 'IRR', b['G29'].value, b['H29'].value)
