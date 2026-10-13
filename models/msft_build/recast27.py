"""Extract the FY27-basis restated history from the 2-Sep-2026 8-K (Item 7.01, Ex. 99.1 "FY27 Segments and Investor Metrics"):
segments Agents and Infra / Devices and Consumer (revenue, cost of revenue, operating expenses, operating income) and the eight
restated product and service offerings, Q1-Q4 + fiscal year for FY2026 and FY2025, plus the FY27 Q1 outlook as filed.
The exhibit is a slide deck (text, not tables); each label is followed by ten numbers: FY2026 Q1-Q4, FY2026, FY2025 Q1-Q4, FY2025.
Writes data/_recast27.json; every block is checked (sum of quarters = fiscal year; segments and product lines sum to the total)."""
import json, os, re
from h2t import html_to_text

S = os.environ.get('MSFT_SRC', '/tmp/msft_src')
HERE = os.path.dirname(os.path.abspath(__file__))
ACC, DOC = '0001193125-26-380280', 'd291965dex991.htm'
URL = f'https://www.sec.gov/Archives/edgar/data/789019/{ACC.replace("-", "")}/{DOC}'

def text():
    p = os.path.join(S, 'docs', f'2026-09-02_8-K_{ACC}_{DOC}')
    return re.sub(r'\s+', ' ', html_to_text(open(p, 'rb').read()))

NUM = r'\$?([\d,]+)'
def ten(t, label, start=0):
    m = re.compile(re.escape(label) + r'\s+' + r'\s+'.join([NUM] * 10)).search(t, start)
    if not m: raise ValueError(label)
    v = [float(x.replace(',', '')) for x in m.groups()]
    return {'Q1-26': v[0], 'Q2-26': v[1], 'Q3-26': v[2], 'Q4-26': v[3], '2026': v[4],
            'Q1-25': v[5], 'Q2-25': v[6], 'Q3-25': v[7], 'Q4-25': v[8], '2025': v[9]}, m.end()

def run():
    t = text()
    out = {'src': URL, 'filed': '2026-09-02', 'seg': {}, 'seg_fy26': {}, 'prod': {}, 'prod_fy26': {}}
    i = t.index('Restated Historical Financials')
    for seg in ('Agents and Infra', 'Devices and Consumer', 'Total'):
        j = t.index(seg + ' Q1 Q2 Q3 Q4 Fiscal Year', i)
        for k, lab in (('rev', 'Revenue'), ('cogs', 'Cost of revenue'), ('opex', 'Operating expenses'), ('oi', 'Operating income')):
            out['seg'][f'{k}||{seg}'], j = ten(t, lab, j)
        i = j
    i = t.index('Segment History as Restated')
    for seg in ('Productivity and Business Processes', 'Intelligent Cloud', 'More Personal Computing', 'Total'):
        j = t.index(seg + ' Q1 Q2 Q3 Q4 Fiscal Year', i)
        for k, lab in (('rev', 'Revenue'), ('cogs', 'Cost of revenue'), ('opex', 'Operating expenses'), ('oi', 'Operating income')):
            out['seg_fy26'][f'{k}||{seg}'], j = ten(t, lab, j)
        i = j
    i = t.index('Revenue As Reported')
    for lab in ('Server products and cloud services', 'Microsoft 365 commercial products and cloud services', 'XBOX', 'LinkedIn', 'Windows and devices',
                'Search advertising', 'Microsoft 365 consumer products and cloud services', 'Dynamics products and cloud services',
                'Enterprise and partner services', 'Other', 'Total'):
        out['prod_fy26'][lab], i = ten(t, lab, i)
    i = t.index('As Restated 2026 2025', i)
    for lab in ('Azure', 'Microsoft 365 cloud', 'Productivity and server licensing', 'Search and advertising', 'XBOX', 'Industry solutions',
                'Windows OEM and devices', 'Frontier and support services', 'Total'):
        out['prod'][lab], i = ten(t, lab, i)
    # FY27 Q1 outlook as provided on 29-Jul-2026 and as mechanically adjusted (filed in this 8-K)
    o = t[t.index('FY27 Q1 Adjusted Outlook'):]
    rng = lambda pat: [float(x) for x in re.search(pat, o).groups()]
    out['outlook_q1fy27'] = {
        'total_rev_bn': rng(r'Total Company Revenue of \$([\d.]+) to \$([\d.]+) billion'),
        'pbp_rev_bn': rng(r'Productivity and Business Processes Revenue of \$([\d.]+) to \$([\d.]+) billion'),
        'ic_rev_bn': rng(r'Intelligent Cloud Revenue of \$([\d.]+) to \$([\d.]+) billion'),
        'mpc_rev_bn': rng(r'More Personal Computing Revenue of \$([\d.]+) to \$([\d.]+) billion'),
        'cogs_bn': rng(r'COGS of \$([\d.]+) to \$([\d.]+) billion'),
        'opex_bn': rng(r'Expenses of \$([\d.]+) to \$([\d.]+) billion'),
        'ai_rev_bn': rng(r'Agents and Infra Revenue of \$([\d.]+) to \$([\d.]+) billion'),
        'dc_rev_bn': rng(r'Devices and Consumer Revenue of \$([\d.]+) to \$([\d.]+) billion'),
        'other_inc_m': -100.0, 'etr': 0.20, 'capex_bn_min': 50.0,
        'text': ('As provided on 29-Jul-2026 and re-filed on 2-Sep-2026: other income and expense roughly $(100) million excluding any impact from '
                 'investments in OpenAI; operating margin relatively flat year-over-year; effective tax rate ~20%; capital expenditures over $50 billion '
                 'including the impact of the useful life update; FX decreases total revenue growth by <1 point. Azure growth 44-45% cc (restated basis); '
                 'Microsoft 365 commercial cloud ~17% cc; productivity and server licensing down low-single digits; Industry solutions cloud high-single '
                 'digits; search and advertising (ex TAC) mid- to high-single digits; XBOX content and services down mid-single digits, hardware down; '
                 'Windows OEM and devices down low-twenties.')}
    # checks
    bad = []
    def chk(n, a, b, tol=1.01):
        if abs(a - b) > tol: bad.append(f'{n}: {a} vs {b}')
    for blk in ('seg', 'seg_fy26', 'prod', 'prod_fy26'):
        for k, v in out[blk].items():
            for y in ('26', '25'):
                chk(f'{blk} {k} FY{y}', sum(v[f'Q{q}-{y}'] for q in (1, 2, 3, 4)), v['20' + y], 2.01)
    for p in out['prod']['Total']:
        chk(f'prod sum {p}', sum(v[p] for k, v in out['prod'].items() if k != 'Total'), out['prod']['Total'][p])
        chk(f'prod26 sum {p}', sum(v[p] for k, v in out['prod_fy26'].items() if k != 'Total'), out['prod_fy26']['Total'][p])
        for k in ('rev', 'cogs', 'opex', 'oi'):
            chk(f'seg sum {k} {p}', out['seg'][f'{k}||Agents and Infra'][p] + out['seg'][f'{k}||Devices and Consumer'][p], out['seg'][f'{k}||Total'][p])
            chk(f'seg26 sum {k} {p}', sum(out['seg_fy26'][f'{k}||{s}'][p] for s in ('Productivity and Business Processes', 'Intelligent Cloud', 'More Personal Computing')),
                out['seg_fy26'][f'{k}||Total'][p])
            chk(f'seg arith {k} {p}', out['seg'][f'rev||Total'][p] - out['seg'][f'cogs||Total'][p] - out['seg'][f'opex||Total'][p], out['seg'][f'oi||Total'][p])
    out['checks'] = bad
    json.dump(out, open(os.path.join(HERE, 'data', '_recast27.json'), 'w'), indent=1)
    return out

if __name__ == '__main__':
    o = run()
    print('issues:', o['checks'] or 'none')
    print({k: v['2026'] for k, v in o['prod'].items()})
    print(o['outlook_q1fy27'])
