"""Print key Model rows for a recalculated workbook: python3 review.py <file> [row keys]."""
import sys, openpyxl
sys.argv += [] 
import fw
from fw import R, ANN, QC
import build, spec, spec2
spec.scen_layout(build.V0); spec.build_spec(build.V0); spec2.build_spec2(build.V0); fw.number_rows(8)
wb = openpyxl.load_workbook(sys.argv[1], data_only=True); ws = wb['Model']
cols = [ANN[2024], ANN[2025], QC[(2025, 3)], QC[(2025, 4)], QC[(2026, 1)], QC[(2026, 2)], QC[(2026, 3)], QC[(2026, 4)]] + [ANN[y] for y in range(2026, 2031)]
keys = sys.argv[2:] or ['is_rev', 'gm_rev', 'pg_online_g', 'pg_tp_g', 'pg_ads_g', 'pg_awsg_g', 'cal_g', 'seg_na_m', 'seg_intl_m', 'seg_aws_m', 'cal_m', 'is_oi', 'is_oi_m',
                        'o_adj', 'is_cogs', 'is_gm', 'd_dep', 'd_oda', 'd_dda', 'is_intinc', 'is_intexp', 'is_ni', 'eps_dil', 'e_adjni', 'e_eps', 'r_adj', 'cf_cfo', 'cf_capex',
                        'fcf', 'cf_bb', 'bs_cash', 'ds_st', 'ds_total', 'lv_nd', 'lv_x', 'bs_ppe', 'bs_eq', 'ra_roic', 'v_ev', 'v_pea', 'bb_end']
print(f'{"":24s}' + ''.join(f'{str(c.label):>11s}' for c in cols))
for k in keys:
    vals = []
    for c in cols:
        v = ws[f'{c.c}{R[k]}'].value
        if isinstance(v, (int, float)):
            vals.append(f'{v:11.3f}' if abs(v) < 5 else f'{v:11,.0f}')
        else: vals.append(f'{str(v)[:10]:>11s}')
    print(f'{k:24s}' + ''.join(vals))
