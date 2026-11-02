"""Extract Theon's statements from the text versions of its regulated reports into data/<period>.json.

Each document spec gives the line ranges (and character columns for side-by-side pages) of the income statement,
balance sheet, cash flow statement, adjusted EBIT / EBITDA reconciliation and revenue disaggregation. A single label
map (below) turns statement lines into keys. Values are EUR millions (6 dp, = whole euros / 1e6), signed as printed:
income / inflows positive, expenses / outflows negative. Per-share data as printed.

Every period record keeps the figures of the document that first presented it (`is`, `bs`, `cf`, `ng`, `rev`),
plus every later comparative under `cmp[<doc>]`, so normalize.py can choose the basis and checks can compare.

Usage: THEON_SRC=/path/to/src python3 -I extract.py   (reads $THEON_SRC/txt, writes data/)
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_stmt import table, read

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('THEON_SRC') or os.path.join(os.path.expanduser('~'), 'theon_src')
TXT = os.path.join(SRC, 'txt')
MEDIA = 'https://media.theon.com/'
URL = {}
for ln in open(os.path.join(HERE, 'doc_urls.txt')):
    ln = ln.strip()
    if ln: URL[ln.rsplit('/', 1)[1][:-4]] = ln

# ------------------------------------------------------------------ label map
IS_MAP = [('rev', r'^revenue$|^turnover'), ('ogain', r'^other income and gains'), ('cogs', r'^cost of sales'), ('gp', r'^gross pro'), ('oinc', r'^other (operating )?income'),
          ('admin', r'^administrative'), ('sell', r'^selling'), ('rnd', r'^research'), ('imp', r'^impairment (loss|of)'),
          ('oexp', r'^other (operating )?expenses'), ('assoc', r'share of (profit|result)'), ('op', r'^operating pro|earnings before interest and tax|rnings before interest'),
          ('finc', r'^finance income|^interest income'), ('fcost', r'^finance costs|^financial expenses|^interest charges'), ('netfin', r'^net finance'),
          ('ebt', r'^profit before tax'), ('taxc', r'^income tax'), ('taxd', r'^deferred tax'),
          ('ni', r'^profit (for|after tax)|^net profit'), ('ni_par', r'owners of the company|shareholders of the company|^owners'),
          ('nci', r'non-controlling interests?$|^minority'), ('eps_b', r'basic earnings per share|^basic$|^basic eps'),
          ('eps_d', r'diluted earnings per share|^diluted$|^diluted eps')]
BS_A = [('ppe', r'^property,? plant'), ('intang', r'^intangible'), ('rou', r'^right.of.use'), ('invprop', r'^investment property'),
        ('assoc_bs', r'^investment in (associates|equity)|^investments in (associates|equity)'), ('ltloan', r'^long term loans? receivable'),
        ('onca', r'^other non-current assets'), ('ofa', r'^other financial assets|^financial assets at fair value'), ('dta', r'^deferred tax assets'),
        ('tnca', r'^(total )?non-current assets$'), ('inv', r'^inventor'), ('ar', r'^trade (accounts )?receivable'), ('orec', r'^other receivables'),
        ('prep', r'^prepayments'), ('td', r'^term deposits|^time deposits'), ('cash', r'^cash and cash equivalents'),
        ('tca', r'^(total )?current assets$'), ('ta', r'^total assets')]
BS_L = [('eqp', r'equity at+ributable|^total equity attributable|owners of the company$'), ('nci_bs', r'non-controlling interests?$|^minority'),
        ('te', r'^total equity$'), ('debt', r'^loans and borrowings|^borrowings|^bank loans'), ('bbl', r'share buy-?back'),
        ('sri', r'staff retirement|retirement indemn|employee benefit'), ('lease', r'^lease liabilit'), ('grants', r'^government grants'),
        ('dtl', r'^deferred tax liabilit'), ('accr', r'^accrued and other|^other (current |non-current )?liabilities$|^accrued'),
        ('tncl', r'^(total )?non-current liabilities$|^(total )?long.term liabilities$'), ('ap', r'^trade (accounts )?payable'),
        ('cl', r'^contract liabilit'), ('itp', r'^income tax payable|^current tax liabilit'), ('tcl', r'^(total )?current liabilities$|^(total )?short.term liabilities$'),
        ('tl', r'^total liabilities$'), ('tle', r'^total equity and liabilities|^total liabilities and equity')]
CF_MAP = [('noncash', r'^non cash items'), ('cashgen', r'^cash\b.*(operating|operation)'), ('taxp', r'^income tax(es)? paid|^taxes paid'),
          ('intp', r'^interest paid'), ('cfo', r'^net cash.*operating|^operating activities$'),
          ('capex', r'^payments? for (property|intangible|investment property|non.current assets|the acquisition of (property|intangible))|^purchase of (property|intangible)'),
          ('acq', r'business combinations|^combinations, net of cash|acquisition of (associates|subsidiar)|payments for (financial assets|acquisition of associates)|investment in associates'),
          ('cfi', r'^net cash.*investing|^investing activities$'), ('debt_rep', r'^repayment of (borrowings|loans|bank)'), ('debt_pro', r'^proceeds from (borrowings|loans|bank)'),
          ('lease_cf', r'lease liab'), ('eq_iss', r'^proceeds from (share capital increase|issues? of shares|ipo)'),
          ('buyback', r'treasury shares|share buy ?back'), ('div', r'^dividends paid'), ('cff', r'^net cash.*financing|^financing activities$'),
          ('net', r'^net (increase|decrease|\(decrease\)|change).*cash'), ('beg', r'january'), ('fx', r'^foreign exchange differences|^effect of exchange'),
          ('end', r'^closing|at 31 december|at 30 june|at 30 september|at 31 march|^(march|june|september|december)$')]
NG_MAP = [('ebit_pub', r'^ebit$'), ('nri', r'non.?recurring'), ('adj_ebit', r'^adjusted ebit$|^adj\.? ebit$'), ('adj_ebitda', r'^adjusted ebitda$|^adj\.? ebitda$')]
REGIONS = {'europe': 'europe', 'asia': 'asia', 'americas': 'americas', 'america': 'americas', 'africa': 'africa', 'oceania': 'oceania',
           'middle east': 'middle_east', 'greece': 'greece'}
PRODUCTS = {'night': 'night', 'thermal': 'thermal', 'platform based': 'platform', 'platform-based': 'platform', 'isr': 'isr',
            'misc': 'misc', 'miscellaneous': 'misc', 'other': 'other', 'digital': 'digital'}

def m(rx, lab): return re.search(rx, lab.strip(), re.I) is not None
def clean(lab):
    lab = re.sub(r'\s+', ' ', lab).strip(' :*')
    lab = re.sub(r'[\u0080-￿]', lambda c: {'ﬁ': 'fi', 'ﬂ': 'fl', '�': 'ti'}.get(c.group(0), c.group(0)), lab)
    lab = lab.replace('ﬁ', 'fi').replace('ﬀ', 'ff').replace('ﬂ', 'fl').replace('ﬃ', 'ffi').replace('�', 'ti')
    return re.sub(r'(\s+\d{1,2}[a-z]?\.?(,\s*\d{1,2}[a-z]?\.?)*)+$', '', lab).strip()

def rows(doc, rng):
    if not rng: return []
    a, b = rng[0], rng[1]; c0 = rng[2] if len(rng) > 2 else 0; c1 = rng[3] if len(rng) > 3 else None
    return [(i, clean(lab), v) for i, lab, v in table(read(os.path.join(TXT, doc['f'] + '.txt'), a, b, c0, c1), doc.get('sep', ','))]

def pick(vals, slot):
    return vals[slot] if len(vals) > slot else None

def map_is(doc, slot):
    out, seen_op, assoc_pos = {}, False, None
    for i, lab, v in rows(doc, doc.get('is')):
        for k, rx in IS_MAP:
            if k in out: continue
            if k == 'taxd' and 'taxc' not in out: continue
            if k in ('ni_par', 'nci') and 'ni' not in out: continue
            if m(rx, lab):
                x = pick(v, slot)
                if x is None: break
                out[k] = x
                if k == 'op': seen_op = True
                if k == 'assoc': assoc_pos = 'in_op' if not seen_op else 'below_op'
                break
    if assoc_pos: out['assoc_pos'] = assoc_pos
    return out

def map_bs(doc, slot):
    out, aside, lside = {}, 'nc', 'nc'
    for rng in doc.get('bs', []):
        for i, lab, v in rows(doc, rng):
            x = pick(v, slot)
            if x is None: continue
            done = False
            for k, rx in BS_A:
                if m(rx, lab):
                    key = k + ('_c' if k == 'ofa' and aside == 'c' else '')
                    if k == 'tnca': aside = 'c'
                    if key not in out: out[key] = x
                    done = True; break
            if done: continue
            for k, rx in BS_L:
                if m(rx, lab):
                    if k in ('debt', 'bbl', 'lease', 'accr'): key = k + ('_c' if lside == 'c' else '')
                    else: key = k
                    if k == 'tncl': lside = 'c'
                    if key not in out: out[key] = x
                    break
    return out

def map_cf(doc, slot):
    out, wc_on, wc = {}, False, 0.0
    start_done = False
    for rng in doc.get('cf', []):
        for i, lab, v in rows(doc, rng):
            x = pick(v, slot)
            mm = re.match(r'^changes in(?: working capital)?:?\s*(.*)$', lab, re.I)
            if mm:
                wc_on = True; lab = mm.group(1)
                if not lab: continue
            if x is None: continue
            if not start_done and m(r'^profit (for|after)', lab):
                out['start'] = x; start_done = True; continue
            hit = None
            for k, rx in CF_MAP:
                if m(rx, lab): hit = k; break
            if hit == 'cashgen' and m(r'^net ', lab): hit = 'cfo' if 'operat' in lab.lower() else None
            if hit is None and 'start' in out and 'cashgen' not in out and not m(r'impairment|^net |^amorti|^depreci', lab) and \
                    m(r'increase|decrease|^provision for staff|contract liabilities|payables|receivables|inventor|^prepayments', lab):
                wc += x; out.setdefault('wc_lines', []).append([lab, x]); continue
            if hit is None:
                out.setdefault('other_lines', []).append([lab, x]); continue
            if hit == 'cashgen': wc_on = False
            if hit in ('capex', 'acq', 'buyback', 'eq_iss', 'lease_cf', 'debt_rep', 'debt_pro'):
                out[hit] = round(out.get(hit, 0.0) + x, 6); out.setdefault(hit + '_lines', []).append([lab, x])
            elif hit == 'beg' and 'net' not in out and 'cff' not in out:
                out.setdefault('other_lines', []).append([lab, x])
            elif hit not in out:
                out[hit] = x
    if wc: out['wc'] = round(wc, 6)
    if 'cashgen' in out and 'start' in out:
        out['noncash_derived'] = round(out['cashgen'] - out['start'] - out.get('wc', 0.0), 6)
    return out

def map_ng(doc, slot):
    out = {}
    for i, lab, v in rows(doc, doc.get('ng')):
        x = pick(v, slot)
        if x is None: continue
        for k, rx in NG_MAP:
            if k not in out and m(rx, lab): out[k] = x; break
    if out.get('adj_ebit') is not None and out.get('ebit_pub') is not None:
        out['nri'] = round(out['adj_ebit'] - out['ebit_pub'], 6)     # = the published non-recurring line (Q1-26 prints it above its label)
    return out

def map_rev(doc, slot):
    reg, prod, mode = {}, {}, None
    rngs = doc.get('rev')
    rngs = rngs if isinstance(rngs, list) else [rngs]
    for i, lab, v in [x for r in rngs for x in rows(doc, r)]:
        x = pick(v, slot)
        if x is None: continue
        l = lab.lower().strip()
        l = re.sub(r'^(primary geographic(al)? markets?|major products?( categories)?)\s*', '', l)
        if l in REGIONS and REGIONS[l] not in reg: reg[REGIONS[l]] = x
        elif l in PRODUCTS and PRODUCTS[l] not in prod: prod[PRODUCTS[l]] = x
    return {'region': reg, 'product': prod}

def extract(doc, slot):
    return {'is': map_is(doc, slot), 'bs': map_bs(doc, slot), 'cf': map_cf(doc, slot), 'ng': map_ng(doc, slot), 'rev': map_rev(doc, slot)}

# ------------------------------------------------------------------ documents
# slots: 0 = current period, 1 = comparative (BS comparative = prior year end), 2 = second comparative (AR23 opening BS)
DOCS = [
    dict(id='AR21', f='annual-report-2021', sep=',', months=12, cur='2021', py='2020', is_=None,
         **{'is': (513, 559), 'bs': [(560, 660)], 'cf': [], 'ng': None, 'rev': None}),
    dict(id='AR22', f='annual-report-2022', sep=',', months=12, cur='2022', py='2021',
         **{'is': (651, 691), 'bs': [(692, 790)], 'cf': [], 'ng': None, 'rev': None}),
    dict(id='AR23', f='theon-international-plc_annual-report-2023', sep='.', months=12, cur='2023', py='2022', py2='2021',
         **{'is': (2736, 2790), 'bs': [(2650, 2735)], 'cf': [(2825, 2890)], 'ng': (5990, 6006), 'rev': (4015, 4040)}),
    dict(id='Q1-24', f='q1_2024_trading_update', sep='.', months=3, cur='Q1-24', py='Q1-23', bs_py='2023',
         **{'is': (282, 306), 'bs': [(195, 214), (235, 262)], 'cf': [(365, 399)], 'ng': (309, 322), 'rev': (330, 352)}),
    dict(id='H1-24', f='condensed-consolidated-financial-statements-30062024', sep=',', months=6, cur='H1-24', py='H1-23', bs_py='2023',
         **{'is': (1748, 1830, 21), 'bs': [(1614, 1747, 21)], 'cf': [(1888, 2025, 21, 147), (1888, 2025, 147)], 'ng': (3550, 3576, 21), 'rev': (2268, 2300, 72)}),
    dict(id='9M-24', f='condensed-consolidated-financial-statements-30092024_final-to-upload', sep=',', months=9, cur='9M-24', py='9M-23', bs_py='2023',
         **{'is': (520, 565, 18), 'bs': [(385, 476, 18)], 'cf': [(620, 670, 18)], 'ng': (580, 604, 18, 110), 'rev': (580, 608, 110, None)}),
    dict(id='AR24', f='2024-annual-report', sep=',', months=12, cur='2024', py='2023',
         **{'is': (4432, 4500), 'bs': [(4296, 4431)], 'cf': [(4632, 4725)], 'ng': (7890, 7915, 0, 75), 'rev': (5690, 5715)}),
    dict(id='Q1-25', f='trading-update-q1-2025', sep=',', months=3, cur='Q1-25', py='Q1-24', bs_py='2024',
         **{'is': (445, 465), 'bs': [(355, 411)], 'cf': [(545, 570)], 'ng': (478, 488), 'rev': (518, 530)}),
    dict(id='H1-25', f='theon-group-semi-annual-report-30-06-2025', sep=',', months=6, cur='H1-25', py='H1-24', bs_py='2024',
         **{'is': (1258, 1300), 'bs': [(1210, 1257, 0, 91), (1210, 1257, 91)], 'cf': [(1347, 1400, 0, 101), (1347, 1400, 101)], 'ng': (2274, 2296),
            'rev': [(1520, 1572, 0, 100), (1520, 1572, 100)]}),
    dict(id='9M-25', f='theon-group-trading-update-q3-2025_vf', sep=',', months=9, cur='9M-25', py='9M-24', bs_py='2024',
         **{'is': (299, 322), 'bs': [(240, 272, 0, 80), (240, 272, 80)], 'cf': [(380, 412)], 'ng': (334, 346), 'rev': (355, 372)}),
    dict(id='AR25', f='theon_annualreport2025', sep=',', months=12, cur='2025', py='2024',
         **{'is': (6304, 6346, 0, 92), 'bs': [(6257, 6303, 0, 92), (6257, 6303, 92, None)], 'cf': [(6438, 6485, 0, 104), (6438, 6485, 104, None), (6486, 6530, 0, 116), (6486, 6530, 116, None)],
            'ng': (9560, 9590, 0, 112), 'rev': (7394, 7430, 0, 97)}),
    dict(id='Q1-26', f='theon-group-trading-update-q1_2026_vff', sep=',', months=3, cur='Q1-26', py='Q1-25', bs_py='2025',
         **{'is': (298, 322), 'bs': [(250, 278)], 'cf': [(388, 434)], 'ng': (338, 349), 'rev': (365, 382)}),
    dict(id='H1-26', f='theon-semi-ar-2026', sep=',', months=6, cur='H1-26', py='H1-25', bs_py='2025',
         **{'is': (1892, 1932), 'bs': [(1845, 1891, 0, 91), (1845, 1891, 91)], 'cf': [(2011, 2062, 0, 101), (2011, 2062, 101)], 'ng': (3050, 3070, 95),
            'rev': (2208, 2232, 0, 100)}),
]

def run(verbose=True):
    recs = {}
    def put(per, docid, months, data, primary):
        r = recs.setdefault(per, {'period': per, 'cmp': {}})
        if primary:
            r.update({k: v for k, v in data.items()}); r['source_doc'] = docid; r['months'] = months
        else:
            r['cmp'][docid] = data
    for d in DOCS:
        src = {'doc': d['f'], 'url': URL.get(d['f'])}
        cur, py = extract(d, 0), extract(d, 1)
        bs_py = py.pop('bs')
        put(d['cur'], d['id'], d['months'], dict(cur, sources=src), True)
        put(d['py'], d['id'], d['months'], py, False)
        # balance sheet comparative is the prior year end for interim documents
        bper = d.get('bs_py', d['py'])
        recs.setdefault(bper, {'period': bper, 'cmp': {}})['cmp'].setdefault(d['id'], {})['bs'] = bs_py
        if d.get('py2'):
            recs.setdefault(d['py2'], {'period': d['py2'], 'cmp': {}})['cmp'].setdefault(d['id'], {})['bs'] = extract(d, 2)['bs']
    return recs

if __name__ == '__main__':
    recs = run()
    os.makedirs(os.path.join(HERE, 'data'), exist_ok=True)
    for per, r in recs.items():
        json.dump(r, open(os.path.join(HERE, 'data', f'{per}.json'), 'w'), indent=1)
    print('wrote', len(recs), 'periods:', sorted(recs))
