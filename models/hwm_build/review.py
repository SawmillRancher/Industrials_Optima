"""Print key rows of a recalculated HWM model for review: python3 review.py <recalculated.xlsx> [key ...]."""
import sys, openpyxl
import fw, build
from spec import build_spec, scen_layout
from spec2 import build_spec2
scen_layout(build.V0); build_spec(build.V0); build_spec2(build.V0); fw.number_rows(8)
KEYS = ['ep_rev', 'ep_g', 'ep_m', 'fs_rev', 'fs_g', 'fs_m', 'es_rev', 'es_g', 'es_m', 'fw_rev', 'fw_g', 'fw_m', 'corp', 'g_rev', 'g_rev_g', 'g_adj', 'g_adjm', 'cal_g', 'cal_m',
        'cal_eps_d', 'cal_fcf_d', 'cal_q4_d', 'cal_27_d', 'd_da', 'is_cogs', 'is_sga', 'is_oi', 'is_int', 'is_oth', 'is_tax', 'is_ni', 'sh_dil', 'eps_dil', 'e_eps', 'dps',
        'cf_wc', 'cf_cfo', 'cf_capex', 'fcf', 'cf_bb', 'cf_div', 'cf_debt', 'cf_end', 'bs_ar', 'bs_inv', 'bs_ap', 'bs_ocl', 'bs_ppe', 'bs_ta', 'bs_eq', 'ds_notes', 'ds_cp',
        'lev_bb', 'bb_sh', 'bb_end', 'ra_roic', 'rn_ronta', 'lv_x', 'v_mc', 'v_ev', 'v_eveb', 'v_pea', 'v_fcfy']
if __name__ == '__main__':
    ws = openpyxl.load_workbook(sys.argv[1], data_only=True)['Model']
    cols = ['C', fw.ANN[2024].c, fw.ANN[2025].c, fw.Q3, fw.QE, fw.E26] + [fw.ANN[y].c for y in range(2027, 2031)]
    print('key'.ljust(10), [ws[f'{c}6'].value for c in cols])
    for k in (sys.argv[2:] or KEYS):
        out = []
        for c in cols:
            v = ws[f'{c}{fw.R[k]}'].value
            out.append(f'{v:.3f}' if isinstance(v, float) and abs(v) < 10 else (f'{v:.0f}' if isinstance(v, (int, float)) else str(v)))
        print(k.ljust(10), ' '.join(x.rjust(7) for x in out))
