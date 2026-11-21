"""Extract the 2026 quarters (Q1-26 .. Q3-26) from the earnings releases (8-K Item 2.02, Ex. 99.1; same table layout in all three)
into data/<period>.json (schema: EXTRACTION_SCHEMA.md). Quarter columns for the income statement / segments; year-to-date for the
cash flow. Orders / backlog from the release text and the Q3-26 earnings appendix (Ex. 99.2) are in manual_items.json."""
import json, os, re
import rel_tables as rt
S = rt.S
BASE = os.path.dirname(os.path.abspath(__file__))
PI = json.load(open(os.path.join(S, 'period_index.json')))
SEGN = ['Space & Mission Systems', 'Communications & Spectrum Dominance', 'Missile Solutions']
KPI = {  # release text ($bn): orders, book-to-bill, total backlog
    'Q1-26': (7800.0, 1.4, 40700.0), 'Q2-26': (7300.0, 1.2, 42000.0), 'Q3-26': (19300.0, 3.2, 53200.0)}
SHARES = {'Q1-26': 186.601408, 'Q2-26': 186.155804, 'Q3-26': 186.144686}      # shares issued and outstanding at period end (10-Q equity note)
ORG = {'Q1-26': 15.0, 'Q2-26': 8.0, 'Q3-26': 9.0}
GUID = {
    'Q1-26': 'FY26 (30-Apr-2026): revenue $23B-$23.5B; segment operating margin low 16%; GAAP diluted EPS $11.40-$11.60 (prior $11.30-$11.50); free cash flow $3.0B (cash from operations ~$3.6B, capex ~$600M).',
    'Q2-26': 'FY26 (29-Jul-2026): revenue $23.2B-$23.7B (prior $23B-$23.5B); segment operating margin low 16%; GAAP diluted EPS $11.80-$12.00 (prior $11.40-$11.60); cash from operations $3.6B; free cash flow $3.0B (capex ~$600M). Segments: SMS revenue ~$11,700M (prior ~$11,500M), margin mid 10%; CSD ~$8,000M, mid 25% (prior ~25%); MS ~$4,100M, low 12%.',
    'Q3-26': 'FY26 (29-Oct-2026): revenue $23.5B-$23.7B (prior $23.2B-$23.7B); segment operating margin low 16% (unchanged); GAAP diluted EPS $12.25-$12.35 (prior $11.80-$12.00); cash from operations $3.6B; free cash flow $3.0B (capex ~$600M; from Q3-26 FCF = CFO - capex, PP&E disposal proceeds no longer included). Segments: SMS revenue ~$11.9B (prior ~$11.7B), margin mid 10%; CSD ~$7.9B (prior ~$8B), mid 25%; MS ~$4.1B, low 12%.'}

def row(t, lab, col=0, nth=0, starts=False):
    hits = [r for r in t['rows'] if (r[0].startswith(lab) if starts else r[0] == lab) and r[1] and r[1][0] is not None]
    if len(hits) <= nth: return None
    return hits[nth][1][col]

def raw(t, col):
    return [[r[0], r[1][col]] for r in t['rows'] if len(r[1]) > col and r[1][col] is not None and not r[0].startswith('($')]

for per, q in (('Q1-26', 1), ('Q2-26', 2), ('Q3-26', 3)):
    pi = PI[per]; T = rt.tables(pi['release'][0]['txt'])
    ytd = 0 if q == 1 else 2                      # year-to-date column (Q1: the only column)
    t1 = T['T1']; g = lambda lab, **k: row(t1, lab, 0, **k)
    I = {'lines_raw': raw(t1, 0), 'sales': g('Revenue'), 'cogs': -g('Cost of revenue'), 'sga': -g('General and administrative expenses'), 'other_op_lines': [],
         'op_income': g('Operating income'), 'nonop_lines': [[r[0], r[1][0]] for r in t1['rows'] if r[0].startswith(('Non-service FAS', 'Other non-operating'))],
         'interest_net': -g('Interest expense, net'), 'ebt': g('Income before income taxes'), 'tax': -g('Income tax', starts=True), 'net_income': g('Net income'),
         'nci': 0.0, 'ni_parent': g('Net income'), 'pref_div': -(g('Subsidiary preferred stock deemed dividend', starts=True) or 0.0),
         'shares_basic': g('Basic', nth=1), 'shares_diluted': g('Diluted', nth=1), 'eps_basic': g('Basic'), 'eps_dil': g('Diluted')}
    I['cont_ops'] = I['net_income']; I['disc_ops'] = 0.0; I['ni_common'] = I['net_income'] - I['pref_div']
    sm = T['SUM']
    segs = []
    for i, n in enumerate(SEGN):
        nn = n if row(sm, n) is not None else n.replace('Communications', 'Communication')
        segs.append({'name': n, 'sales': row(sm, nn, 0, 0), 'op_income': row(sm, nn, 0, 1)})
    tc = T['T4'] if 'Unallocated' in T['T4']['title'] or 'Reconciliation of Revenue' in T['T4']['title'] else None
    corp = []
    skip = ('Unallocated corporate items', 'Revenue', 'Segment', 'Operating', 'Other non-reportable', 'Other 1', 'Other')
    for r in tc['rows']:
        if not r[1] or r[1][0] is None or r[0].startswith('($'): continue
        if r[0] in ('Unallocated corporate items and other, net', 'Unallocated corporate items') or r[0].startswith(('Revenue', 'Segment revenue', 'Segment operating', 'Operating', 'Other non-reportable')) or r[0] == 'Other': continue
        corp.append([r[0], -r[1][0]])
    onr = row(tc, 'Other non-reportable businesses')
    if onr: corp.append(['Other non-reportable businesses', -onr])
    seg = {'basis': 'segment operating income (company non-GAAP total: operating income excluding unallocated corporate items and other, net)', 'segments': segs,
           'intersegment': row(sm, 'Intersegment'), 'other_rev': row(sm, 'Other') or 0.0, 'corp_lines': corp,
           'seg_op_total_pub': row(sm, 'Segment operating income'), 'adj_seg_op_pub': row(sm, 'Segment operating income'), 'adj_seg_margin_pub': row(sm, 'Segment operating margin'),
           'kpis': {'orders': KPI[per][0], 'book_to_bill': KPI[per][1], 'backlog': KPI[per][2], 'organic_growth': ORG[per]},
           'seg_note': 'Three segments from Q1-26: Space & Mission Systems, Communications & Spectrum Dominance, Missile Solutions (2025 comparatives recast). FAS/CAS operating adjustment no longer an unallocated item.'}
    t6 = T['T6']
    N = {'fcf_pub': row(t6, 'Free cash flow', 0), 'fcf_bridge': raw(t6, 0), 'guidance': GUID[per],
         'notes': ('No non-GAAP EPS published from Q1-26 (guidance and headline are GAAP diluted EPS). Segment operating income / margin and free cash flow are the non-GAAP measures. '
                   + ('Free cash flow = CFO - capital expenditures (PP&E disposal proceeds no longer included; prior periods recast).' if q == 3 else 'Free cash flow = CFO - capital expenditures + proceeds from disposal of PP&E.'))}
    t3 = T['T3']; c = lambda lab, **k: row(t3, lab, ytd, **k)
    C = {'ytd_months': 3 * q, 'lines_raw': raw(t3, ytd), 'net_income': c('Net income'), 'da': c('Depreciation and amortization'), 'sbc': c('Share-based compensation'),
         'deferred_tax': c('Deferred income taxes'), 'pension_income': c('Net periodic benefit income'), 'cfo': c('Net cash', starts=True), 'capex': c('Capital expenditures'),
         'ppe_proceeds': c('Proceeds from disposal of property, plant and equipment, net'), 'divest': c('Proceeds from sales of businesses, net of cash divested'),
         'cfi': c('Net cash', starts=True, nth=1), 'debt_repay': c('Repayments of long-term debt'), 'cp_net': c('Change in commercial paper, net'),
         'dividends': c('Dividends paid'), 'buyback': c('Repurchases of common stock'), 'cff': c('Net cash', starts=True, nth=2),
         'fx': c('Effect of exchange rate changes on cash and cash equivalents'), 'net_change': c('Net', starts=True, nth=4) if False else None,
         'cash_begin': c('Cash and cash equivalents, beginning of period'), 'cash_end': c('Cash and cash equivalents, end of period')}
    C['net_change'] = [r[1][ytd] for r in t3['rows'] if re.match(r'Net (increase|decrease)', r[0])][0]
    t2 = T['T2']; b = lambda lab, **k: row(t2, lab, 0, **k)
    B = {'lines_raw': raw(t2, 0), 'cash': b('Cash and cash equivalents'), 'st_inv': b('Short-term investments'), 'ar': b('Receivables, net'), 'contract_assets': b('Contract assets'),
         'inventories': b('Inventories, net'), 'held_for_sale_a': b('Assets of business held for sale'), 'tca': b('Total current assets'), 'ppe': b('Property, plant and equipment, net'),
         'goodwill': b('Goodwill'), 'intangibles': b('Intangible assets, net'), 'ta': b('Total assets'),
         'st_debt': (b('Short-term debt') or 0.0) + b('Current portion of long-term debt'), 'ap': b('Accounts payable'), 'contract_liab': b('Contract liabilities'),
         'comp_benefits': b('Compensation and benefits'), 'held_for_sale_l': b('Liabilities of business held for sale'), 'tcl': b('Total current liabilities'),
         'ltd': b('Long-term debt, net'), 'deferred_tax_l': b('Deferred income taxes', nth=1), 'tl': b('Total liabilities'),
         'pref_deriv': (b('Subsidiary Series A preferred stock conversion feature') or 0.0) + (b('Subsidiary warrants') or 0.0),
         'mezz': b('Redeemable subsidiary Series A convertible preferred stock') or 0.0, 'te': b('Total equity'), 'tle': b('Total liabilities', starts=True, nth=1)}
    B['equity_parent'] = B['te']; B['nci'] = 0.0; B['shares_out'] = SHARES[per]
    I['dps'] = 1.25                                # quarterly dividend $1.25 (10-Q; raised from $1.20 on 23-Jan-2026)
    rec = {'period': per, 'period_end': pi['period_end'], 'weeks': 13, 'sources': {'release': pi['release'][0]['url'], 'filing': pi['filing']['url']},
           'is': I, 'seg': seg, 'ngaap': N, 'cf': C, 'bs': B,
           'py': {'restated': True, 'notes': 'prior-year segments recast to the three-segment structure effective Q1-26',
                  'is': {'sales': row(t1, 'Revenue', 1), 'op_income': row(t1, 'Operating income', 1), 'ni_parent': row(t1, 'Net income', 1), 'eps_dil': row(t1, 'Diluted', 1)},
                  'segments': [{'name': n, 'sales': row(sm, n if row(sm, n) is not None else n.replace('Communications', 'Communication'), 1, 0),
                                'op_income': row(sm, n if row(sm, n) is not None else n.replace('Communications', 'Communication'), 1, 1)} for n in SEGN],
                  'adj_seg_op_pub': row(sm, 'Segment operating income', 1)},
           'notes': 'Extracted by extract_2026.py from the release tables (quarter columns; cash flow year to date). Orders / book-to-bill / backlog from the release text ($bn, rounded).'}
    # self-checks
    chk = []
    if abs(I['sales'] - I['cogs'] - I['sga'] - I['op_income']) > 1: chk.append('IS op income')
    if abs(I['op_income'] + sum(v for _, v in I['nonop_lines']) - I['interest_net'] - I['ebt']) > 1: chk.append('IS ebt')
    if abs(I['ebt'] - I['tax'] - I['net_income']) > 1: chk.append('IS ni')
    if abs(sum(s['sales'] for s in segs) + seg['intersegment'] + seg['other_rev'] - I['sales']) > 1: chk.append('seg sales')
    if abs(sum(s['op_income'] for s in segs) + sum(v for _, v in corp) - I['op_income']) > 1: chk.append(f"seg oi {sum(s['op_income'] for s in segs) + sum(v for _, v in corp)} vs {I['op_income']}")
    if abs(C['cfo'] + C['cfi'] + C['cff'] + C['fx'] - C['net_change']) > 1 or abs(C['cash_begin'] + C['net_change'] - C['cash_end']) > 1: chk.append('CF')
    if abs(B['ta'] - B['tle']) > 1 or abs(B['tl'] + B['mezz'] + B['te'] - B['tle']) > 1: chk.append('BS')
    if chk: rec['notes'] += ' SELF-CHECK FAILURES: ' + '; '.join(chk)
    json.dump(rec, open(os.path.join(BASE, 'data', per + '.json'), 'w'), indent=1, ensure_ascii=False)
    print(per, 'checks:', chk or 'ok', 'corp', corp)
