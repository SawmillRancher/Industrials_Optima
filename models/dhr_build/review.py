"""Print key Model rows of a recalculated workbook for review: python3 review.py <file> [row keys…]"""
import sys, openpyxl
from openpyxl.utils import column_index_from_string as CI
from rows import R
v = openpyxl.load_workbook(sys.argv[1], data_only=True)['Model']
cols = ['BL', 'BQ', 'BV', 'BW', 'BX', 'BY', 'BZ', 'CA', 'CB', 'CC', 'CD', 'CE']
keys = sys.argv[2:] or ['is_rev', 'g_core', 'bio_rev', 'bio_core', 'ls_rev', 'ls_core', 'dx_rev', 'dx_core', 'ms_rev', 'st_rev', 'm_rev', 'bio_adjm', 'ls_adjm',
        'dx_adjm', 'ms_adjm', 'c_op', 'o_adj', 'o_adj_m', 'cal_g', 'cal_m', 'is_amort', 'is_op', 'is_intexp', 'is_intinc', 'is_tax', 'is_etr', 'e_etr', 'is_ni',
        'sh_dil', 'eps_cont', 'e_eps', 'e_eps_g', 'r_adj', 'r_adj_pf', 'fcf', 'cf_capex', 'cf_acq', 'cf_bb', 'cf_divs', 'dps', 'ds_total', 'ds_fac', 'bs_cash',
        'lv_x', 'ra_roic', 'v_pea', 'bs_ta', 'bs_gw', 'bs_int']
print('key'.ljust(10), ' '.join(f'{v.cell(6, CI(c)).value!s:>8}' for c in cols))
for k in keys:
    out = []
    for c in cols:
        x = v[f'{c}{R[k]}'].value
        out.append((f'{x:8.3f}' if abs(x) < 2 else f'{x:8.0f}' if abs(x) >= 100 else f'{x:8.2f}') if isinstance(x, (int, float)) else f'{str(x or "")[:8]:>8}')
    print(k.ljust(10), ' '.join(out))
