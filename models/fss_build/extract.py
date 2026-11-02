"""Per-period extraction from the Federal Signal EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2025 and quarters Q1/13 - Q3/26 (Q4 is derived in normalize.py as FY - 9M on the same basis).
Every record stores the same statement blocks from each document that presents the period, so that normalize.py can apply the
basis policy (continuing-operations recasts) without re-reading the filings:
  k    the period's own 10-K (annual) / 10-Q (quarter): is, seg, bs, cf (year to date), segda, segcapex, segassets, selected
  k1   the following year's 10-K / same-quarter 10-Q, prior-year columns (restated comparative)
  k2   the 10-K two years later, prior-year-2 columns (annual only)
  rel  the period's earnings release (Ex. 99.1 of the 10-Q / 10-K; Form 8-K Item 2.02 for Q4/08): grp (orders, backlog, segment
       D&A, segment adjusted EBITDA), adjeps (adjusted EPS reconciliation items), ebitda (adjusted EBITDA reconciliation), lev,
       corporate expenses (text), outlook (text), dps
  rel1 the following year's release, prior-year columns
  x    XBRL company facts (share-based compensation, deferred taxes, dividends declared, shares outstanding) as first filed
Units: USD millions as published (the filings are in millions to one decimal); per share in $; shares in millions.
Signs: costs positive (the 2006-2009 release tables, which print costs as negatives, are not used for statements); two-sided
items signed by their effect on income; cash flow as presented. '—' = 0.0; a line not presented is omitted. Nothing is estimated.
"""
import json, os, re, datetime as dt, warnings
import parse_fss as P
import xbrl
warnings.filterwarnings('ignore')

S = os.environ.get('FSS_SRC', '/tmp/fss_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '277509'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc
def dpath(o, doc): return os.path.join(S, 'docs', f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{doc}")

_PC = {}
def parsed(path):
    if path not in _PC:
        _PC[path] = P.parse(open(path, 'rb').read()) if os.path.exists(path) else []
    return _PC[path]
_TC = {}
def text(path):
    if path not in _TC:
        t = os.path.join(S, 'txt', os.path.basename(path).rsplit('.', 1)[0] + '.txt')
        _TC[path] = open(t).read() if os.path.exists(t) else ''
    return _TC[path]

# ------------------------------------------------------------------ document index
def index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    docs = {}      # (fy, q) -> {'form', 'primary', 'release', 'date', 'urls'}
    for o in fl:
        if o['form'] not in ('10-K', '10-Q', '8-K'): continue
        if o['form'] == '8-K':
            if '2.02' not in o['items']: continue
            d = dt.date.fromisoformat(o['date'])
            if d.year == 2009 and d.month == 2: key = (2008, 4)          # FY2008 release (the FY2008 10-K carries no Ex. 99.1)
            else: continue
            ex = [x for x in o['files'] if re.search(r'exv99w1', x)]
            if not ex: continue
            docs.setdefault(key, {})['release'] = dpath(o, ex[0]); docs[key]['release_url'] = url(o, ex[0]); docs[key]['release_date'] = o['date']
            continue
        e = dt.date.fromisoformat(o['report'])
        q = {3: 1, 6: 2, 9: 3, 12: 4}[e.month]
        key = (e.year, q)
        rec = docs.setdefault(key, {})
        rec.update(form=o['form'], primary=dpath(o, o['primary']), primary_url=url(o, o['primary']), date=o['date'])
        ex = [x for x in o['files'] if x != o['primary'] and x.lower().endswith('.htm') and re.search(r'ex[a-z]*99(w|x|_)?1|dex991|exhx991|exh991|exx991|exx992', x.lower())
              and not re.search(r'earni|presentation', x.lower())]
        # the Q3/14 release is Ex. 99.2 (99.1 is a different document); otherwise the first 99.1-type exhibit
        ex.sort(key=lambda x: (0 if re.search(r'991|99w1', x.lower()) else 1))
        if key == (2014, 3): ex = [x for x in ex if '992' in x] or ex
        ex = [x for x in ex if any(t['type'] == 'is' for t in parsed(dpath(o, x)))] or ex
        if ex:
            rec['release'] = dpath(o, ex[0]); rec['release_url'] = url(o, ex[0]); rec['release_date'] = o['date']
    return docs

# ------------------------------------------------------------------ income statement
IS_MAP = [('rev', r'^(net )?(sales|revenues?)( \(a\))?$'), ('cogs', r'^cost of (sales|products)'), ('gp', r'^gross (profit|margin)$'),
          ('sga', r'^selling,? (engineering,? )?general,? (and|&) administrative|^operating expenses$|^selling, general'),
          ('amort', r'^amortization( expense)?$'), ('acq', r'^acquisition and integration'),
          ('impair', r'impairment'), ('restr', r'^restructuring'), ('gain_pl', r'^gain on sale of product line|^\(gain\) loss on sale'),
          ('hearing', r'hearing loss'),
          ('oi', r'^operating (\(loss\) )?income|^operating income \(loss\)|^operating \(loss\)$|^income from operations'),
          ('int_exp', r'^interest expense'), ('debt_settle', r'^debt settlement'), ('pension_settle', r'^pension settlement'),
          ('oth', r'^other (\(income\) expense|expense \(income\)|income \(expense\)|\(expense\) income|expense|income),? ?net$|^other (income|expense)( \(expense\)| \(income\))?,? net$|^other \(income\) expense$|^other income \(expense\)$'),
          ('ebt', r'^(\(loss\) )?income (\(loss\) )?(from continuing operations )?before income taxes|^income \(loss\) (from continuing operations )?before income taxes|^\(loss\) income (from continuing operations )?before'),
          ('tax', r'^income tax (expense|benefit|\(benefit\)|\(expense\)|provision|charge)|^income tax(es)?( benefit| \(charge\))?$|^provision for income taxes|^income tax benefit \(charge\)'),
          ('cont', r'^(\(loss\) )?income (\(loss\) )?from continuing operations$|^income \(loss\) from continuing operations$|^\(loss\) income from continuing'),
          ('disc', r'from discontinued operations|^discontinued operations|^\(loss\) gain from discontinued|^gain \(loss\) from discontinued|^loss from discontinued|^income from discontinued'),
          ('ni', r'^net (income|earnings|\(loss\) income|income \(loss\)|loss)( \(loss\))?$|^net earnings \(loss\)$|^net \(loss\) income$|^net loss$')]
PS = {'eps_b', 'eps_d', 'eps_b_cont', 'eps_d_cont', 'eps_b_disc', 'eps_d_disc', 'dps'}

def ext_is(tabs, mo, cp):
    cands = []
    for t in tabs:
        if t['type'] != 'is': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        ci = idx[0]
        out, misal, state, sec = {}, [], 'pre', None
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :*')
            if not vals:
                if re.search(r'basic and diluted', L): sec = 'bd'
                elif re.search(r'basic', L): sec = 'b'
                elif re.search(r'diluted', L): sec = 'd'
                elif re.search(r'per share|earnings per|share earns', L): sec = 'eps'
                elif re.search(r'weighted|average (common )?shares|shares outstanding', L): sec = 'sh'
                elif re.search(r'^(costs and expenses|add|less|operating data|other data)', L): pass
                else: sec = None
                continue
            if len(vals) != len(t['cols']):
                misal.append([lab, vals]); continue
            v = vals[ci]
            if re.search(r'^basic and diluted', L):          # 2006-2011: "Basic and diluted earnings (loss) per share Earnings from continuing operations"
                sec = 'bd'
                if 'continuing' in L:
                    out.setdefault('eps_b_cont', v); out.setdefault('eps_d_cont', v)
                continue
            if re.search(r'^average shares outstanding\W+basic', L): out.setdefault('sh_b', v); continue
            if re.search(r'^diluted shares outstanding', L): out.setdefault('sh_d', v); continue
            # EPS / share rows
            if sec in ('b', 'd', 'bd', 'eps', 'sh') or re.search(r'per share|per diluted share|earnings per|share earns', L):
                keys = []
                if re.search(r'^basic', L) and 'per share' not in L and sec == 'sh': keys = ['sh_b']
                elif re.search(r'^diluted', L) and 'per share' not in L and sec == 'sh': keys = ['sh_d']
                elif re.search(r'^basic', L): keys = ['eps_b']; sec = sec if sec in ('b', 'd', 'bd') else 'eps'
                elif re.search(r'^diluted', L): keys = ['eps_d']
                elif re.search(r'continuing', L): keys = [f'eps_{s}_cont' for s in (('b', 'd') if sec == 'bd' else [sec])] if sec in ('b', 'd', 'bd') else []
                elif re.search(r'discontinued', L): keys = [f'eps_{s}_disc' for s in (('b', 'd') if sec == 'bd' else [sec])] if sec in ('b', 'd', 'bd') else []
                elif re.search(r'^net (income|earnings|loss|\(loss\))', L): keys = [f'eps_{s}' for s in (('b', 'd') if sec == 'bd' else [sec])] if sec in ('b', 'd', 'bd') else []
                elif re.search(r'dividends', L): keys = ['dps']
                elif re.search(r'basic$', L) and sec == 'sh': keys = ['sh_b']
                for key in keys:
                    if key not in out: out[key] = v
                continue
            if re.search(r'weighted average|average (common )?shares', L):
                if 'dilut' in L and 'sh_d' not in out: out['sh_d'] = v
                elif 'sh_b' not in out: out['sh_b'] = v
                continue
            if re.search(r'cash dividends', L) and 'per' in L:
                out.setdefault('dps', v); continue
            if re.search(r'^(adjusted ebitda|operating margin|total orders|orders|backlog|depreciation and amortization|adjusted ebitda margin|diluted earnings per share|effective tax)', L):
                k = {'adjusted ebitda': 'adj_ebitda', 'adjusted ebitda margin': 'adj_ebitda_m', 'total orders': 'orders', 'orders': 'orders', 'backlog': 'backlog',
                     'depreciation and amortization': 'dda', 'operating margin': 'op_m', 'diluted earnings per share': 'eps_d_x', 'effective tax rate': 'etr'}
                for kk, vv in k.items():
                    if L.startswith(kk): out.setdefault(vv, v); break
                continue
            key = next((k for k, p in IS_MAP if re.search(p, L)), None)
            if key == 'ni' and 'ni' in out: continue
            if key and key not in out:
                out[key] = v
            elif key and key in out:
                out.setdefault('dups', []).append([lab, v])
            elif state != 'post' and not re.search(r'^(total|costs and)', L):
                out.setdefault('other_lines', []).append([lab, v])
            if key == 'ni': state = 'post'
        if 'rev' in out and ('ebt' in out or 'ni' in out):
            if misal: out['misaligned'] = misal
            cands.append(out)
    if not cands: return None
    # the face statement (it carries the share counts) first, then the table with the most lines
    cands.sort(key=lambda o: (-(('sh_d' in o) + ('eps_d' in o)), -len([k for k in o if k not in ('other_lines', 'dups', 'misaligned')])))
    return cands[0]

# ------------------------------------------------------------------ segments (10-K / 10-Q note; releases 2006-2012)
SEGN = {'ssg': r'^safety and security', 'frg': r'^fire rescue', 'esg': r'^environmental (solutions|products)', 'fst': r'^federal signal technolog', 'tool': r'^tool',
        'corp': r'^corporate', 'tot': r'^total (net sales|operating|segment operating|company)|^operating (\(loss\) )?income$|^operating income \(loss\)$'}

def ext_seg(tabs, mo, cp):
    out = {}
    for t in tabs:
        if t['type'] != 'seg': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        ci = idx[0]; sec = None
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :*')
            if not vals:
                if 'sales' in L or 'revenue' in L: sec = 'sales'
                elif 'operating' in L or 'income' in L: sec = 'oi'
                elif 'depreciation' in L: sec = 'da'
                elif 'capital' in L: sec = 'capex'
                elif 'assets' in L: sec = 'assets'
                else: sec = None
                continue
            if len(vals) != len(t['cols']):
                out.setdefault('misaligned', []).append([lab, vals]); continue
            v = vals[ci]
            for k, p in SEGN.items():
                if re.search(p, L):
                    if k == 'tot':
                        if sec == 'sales' and 'sales' in L: out.setdefault('sales_tot', v)
                        elif sec == 'oi' or 'operating' in L: out.setdefault('oi_tot', v)
                        break
                    if sec is None:
                        sec = 'sales' if f'sales_{k}' not in out else 'oi'
                    if sec == 'sales': out.setdefault(f'sales_{k}', v)
                    elif sec == 'oi': out.setdefault(f'oi_{k}', v)
                    elif sec == 'da': out.setdefault(f'da_{k}', v)
                    elif sec == 'capex': out.setdefault(f'capex_{k}', v)
                    elif sec == 'assets': out.setdefault(f'assets_{k}', v)
                    break
            else:
                if sec == 'oi' and re.search(r'^(interest|other|income|\(loss\))', L): sec = None
        if 'sales_esg' in out: break
    # 2025+ format: one table per period with segments as columns
    if 'sales_esg' not in out:
        for t in tabs:
            if t['type'] != 'seg2': continue
            if t['mo'] != mo or t['cp'] != cp: continue
            for lab, vals in t['rows']:
                L = lab.lower().strip(' :*')
                if not vals: continue
                if re.match(r'^net sales', L): out['sales_esg'], out['sales_ssg'], out['sales_tot'] = vals[0], vals[1], vals[-1]
                elif re.match(r'^segment operating income', L): out['oi_esg'], out['oi_ssg'] = vals[0], vals[1]; out['oi_segtot'] = vals[-1]
                elif re.match(r'^(less: )?corporate', L): out['oi_corp'] = -abs(vals[-1])
                elif re.match(r'^(consolidated )?operating income', L): out['oi_tot'] = vals[-1]
                elif re.match(r'^less: cost of sales|^cost of sales', L): out['cogs_esg'], out['cogs_ssg'] = vals[0], vals[1]
                elif re.match(r'^gross profit', L): out['gp_esg'], out['gp_ssg'] = vals[0], vals[1]
                elif re.match(r'^selling', L): out['sga_esg'], out['sga_ssg'] = vals[0], vals[1]
                elif re.match(r'^other segment items', L): out['osi_esg'], out['osi_ssg'] = vals[0], vals[1]
            if 'sales_esg' in out: break
    for ty, pre in (('segda', 'da'), ('segcapex', 'capex'), ('segassets', 'assets')):
        for t in tabs:
            if t['type'] != ty: continue
            idx = [i for i, c in enumerate(t['cols']) if c[0] == (0 if ty == 'segassets' else mo) and c[1] == cp]
            if not idx: continue
            ci = idx[0]
            for lab, vals in t['rows']:
                L = lab.lower().strip(' :*')
                if not vals or len(vals) != len(t['cols']): continue
                for k, p in SEGN.items():
                    if k == 'tot': continue
                    if re.search(p, L): out.setdefault(f'{pre}_{k}', vals[ci]); break
                if re.match(r'^total (depreciation|capital|assets$|identifiable)', L) and not re.search(r'segment', L): out.setdefault(f'{pre}_tot', vals[ci])
    return out or None

# ------------------------------------------------------------------ group results (releases / MD&A)
GRP_MAP = [('orders', r'^(total )?orders$'), ('sales', r'^net (sales|revenues?)$|^revenues?$|^sales$'), ('oi', r'^operating (\(loss\) )?income|^operating income \(loss\)|income, adjusted'),
           ('backlog', r'^backlog$|^year[- ]end backlog$'), ('dda', r'^depreciation and amortization'), ('adj_ebitda', r'^adjusted ebitda$'), ('ebitda', r'^ebitda$'),
           ('op_m', r'^operating margin'), ('adj_ebitda_m', r'^adjusted ebitda margin')]

def ext_grp(tabs, mo, cp):
    out = {}
    for t in tabs:
        if t['type'] != 'grp': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        ci = idx[0]
        g = t.get('grp')
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :*')
            if not vals:
                g2 = P.group_of(lab)
                if g2: g = g2
                continue
            if g is None: continue
            if len(vals) != len(t['cols']):
                if len(vals) == 2 and L == 'backlog' and ci in (0, 1) and len(t['cols']) in (4, 6): v = vals[0 if cp == 'cur' else 1]
                else:
                    out.setdefault('misaligned', []).append([g, lab, vals]); continue
            else: v = vals[ci]
            for k, p in GRP_MAP:
                if re.search(p, L):
                    out.setdefault(f'{k}_{g}', v); break
    return out or None

def ext_corp_text(txt, mo):
    """'Corporate operating expenses were $12.8 million and $13.2 million for the three months ended September 30, 2026 and 2025' -> (cur, py)."""
    pats = {3: r'three months', 6: r'six months', 9: r'nine months', 12: r'(twelve months|years? ended|full year)'}
    out = {}
    for m in re.finditer(r'corporate (operating )?expenses?[^.$]{0,80}?\$([\d.]+) million(?: and \$([\d.]+) million)?[^.]{0,60}?(three|six|nine|twelve) months', txt, re.I):
        k = {'three': 3, 'six': 6, 'nine': 9, 'twelve': 12}[m.group(4).lower()]
        if k == mo and 'cur' not in out:
            out['cur'] = float(m.group(2)); out['py'] = float(m.group(3)) if m.group(3) else None
    return out or None

# ------------------------------------------------------------------ non-GAAP
def cat(lab):
    L = lab.lower()
    for c, p in [('TAXD', r'special (income )?tax|tax (benefit|item|planning|valuation)|valuation allowance|discrete'), ('TAX', r'income tax|tax effect|tax expense'),
                 ('ACQ', r'acquisition|integration|transaction'), ('STEPUP', r'purchase accounting'), ('RESTR', r'restructuring|severance|executive'),
                 ('DEBT', r'debt settlement|financing'), ('PENSION', r'pension'), ('IMPAIR', r'impairment'), ('LEGAL', r'hearing loss|legal|litigation'),
                 ('DISC', r'discontinued'), ('COVID', r'coronavirus|covid'), ('GAIN', r'gain|loss on sale|divestiture')]:
        if re.search(p, L): return c
    return 'OTHER'

def _adj_table(t, ci):
    out = {'items': []}
    state = 'start'
    for lab, vals in t['rows']:
        L = lab.lower().strip(' :*')
        if not vals or len(vals) != len(t['cols']): continue
        v = vals[ci]
        if state == 'start':
            if re.match(r'^(income|net income|net earnings|\(loss\) income|income \(loss\)|net \(loss\)|diluted|eps|earnings per share|\(loss\) earnings per|loss per)', L):
                out['start'] = v; out['start_label'] = lab; state = 'tax'
            continue
        if state == 'tax':
            if re.match(r'^income tax', L): out['tax'] = v
            elif re.match(r'^(\(loss\) )?income (\(loss\) )?before income taxes|^income before income taxes|^\(loss\) income before', L): out['ebt'] = v; state = 'items'
            elif re.match(r'^adjusted|^diluted .*adjusted|, adjusted$|^normalized', L): out['adj'] = v; out['adj_label'] = lab; out['fmt'] = 'net'; state = 'done'
            else:
                out['items'].append({'label': lab, 'v': v, 'cat': cat(lab)}); out['fmt'] = 'net'
            continue
        if state == 'items':
            if re.match(r'^adjusted (\(loss\) )?income (\(loss\) )?before', L): out['adj_ebt'] = v; state = 'adjtax'; continue
            if re.match(r'^(adjusted )?(income )?tax expense|^adjusted income tax|^tax expense', L): out['adj_tax'] = v; state = 'adjtax'; continue
            if re.match(r'^(adjusted|normalized) (net income|net earnings|income from|net \(loss\)|diluted|eps|earnings|\(loss\))', L): out['adj'] = v; out['adj_label'] = lab; state = 'done'; continue
            out['items'].append({'label': lab, 'v': v, 'cat': cat(lab)}); out['fmt'] = 'pre'
            continue
        if state == 'adjtax':
            if re.match(r'^adjusted income tax|^(income )?tax expense', L): out['adj_tax'] = v
            elif re.match(r'^(adjusted|normalized) (net income|net earnings|income from|net \(loss\)|diluted|eps|earnings|\(loss\))', L): out['adj'] = v; out['adj_label'] = lab; state = 'done'
            continue
        if state == 'done':
            # per-share block inside the same table (2013-2015 releases)
            if re.match(r'^(diluted|eps|earnings per|\(loss\) earnings per|loss per|net income per)', L) and 'adjusted' not in L and 'ps' not in out:
                out['ps'] = {'start': v, 'items': []}
            elif 'ps' in out and 'adj' not in out['ps']:
                if re.match(r'^adjusted (\(loss\) )?income (\(loss\) )?before', L): out['ps']['adj_ebt'] = v
                elif re.match(r'^adjusted income tax', L): out['ps']['adj_tax'] = v
                elif re.match(r'^(adjusted|normalized)', L): out['ps']['adj'] = v
                elif re.match(r'^income tax|^tax expense', L): out['ps']['tax'] = v
                elif re.match(r'^(\(loss\) )?income (\(loss\) )?before|^income before', L): out['ps']['ebt'] = v
                elif re.match(r'^adjusted', L): pass
                else: out['ps']['items'].append({'label': lab, 'v': v})
    return out if 'adj' in out else None

def ext_adjeps(tabs, mo, cp):
    """adjusted EPS reconciliation -> {'start', 'tax', 'ebt', 'items'[label, v, cat], 'adj_ebt', 'adj_tax', 'adj_ni', 'adj_eps', 'eps', 'fmt'}.
    fmt 'pre' = items before tax with an adjusted tax line (2014+); 'net' = items net of tax (2010-2013). Dollar and per-share tables merged."""
    dollars, pershare = None, None
    for t in tabs:
        if t['type'] != 'adjeps': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        o = _adj_table(t, idx[0])
        if not o: continue
        hdr = (' '.join(t['hdr']) + ' ' + t['pre'][-80:]).lower()
        is_ps = ('per share' in o['start_label'].lower() or o['start_label'].lower().startswith(('diluted', 'eps')) or 'per diluted share' in hdr
                 or 'dollars per' in hdr) and abs(o['start']) < 25 and abs(o['adj']) < 25
        if is_ps:
            if pershare is None: pershare = o
        elif dollars is None: dollars = o
        if dollars and 'ps' in dollars and pershare is None:
            pershare = dict(dollars['ps']); pershare['start_label'] = 'ps block'
    if not dollars and not pershare: return None
    out = {'fmt': (dollars or {}).get('fmt', 'ps')}
    if dollars:
        out.update({k: dollars[k] for k in ('start', 'start_label', 'tax', 'ebt', 'adj_ebt', 'adj_tax') if k in dollars})
        out['adj_ni'] = dollars['adj']; out['adj_label'] = dollars['adj_label']; out['items'] = dollars['items']
    if pershare:
        out['eps'] = pershare['start']; out['adj_eps'] = pershare['adj']; out['items_ps'] = pershare['items']
        if not dollars:
            out['items'] = [dict(i, ps=True) for i in pershare['items']]; out['fmt'] = 'ps'
            for k in ('tax', 'ebt', 'adj_tax', 'adj_ebt'):
                if k in pershare: out[k + '_ps'] = pershare[k]
    return out

def ext_ebitda(tabs, mo, cp):
    out = {}
    for t in tabs:
        if t['type'] not in ('ebitda', 'lev'): continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        ci = idx[0]
        g = t.get('grp')
        pre = (t['pre'] + ' ' + ' '.join(t['hdr'])).lower()
        cons = g is None or 'consolidated' in pre
        items, blk, start = [], None, None
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :*')
            if not vals:
                g2 = P.group_of(lab)
                if g2: g = g2; cons = False; items = []
                continue
            if len(vals) != len(t['cols']): continue
            v = vals[ci]
            if re.match(r'^(net income|net \(loss\)|net loss|income from continuing|net earnings|\(loss\) income|income \(loss\))', L) and start is None:
                start = v; start_lab = lab; continue
            if re.match(r'^operating (\(loss\) )?income', L) and not cons and start is None:
                start = v; start_lab = lab; continue
            if re.match(r'^(consolidated )?(adjusted )?ebitda$|^total (adjusted )?ebitda$|^adjusted ebitda', L) and 'margin' not in L:
                key = ('adj_ebitda' if 'adjusted' in L else 'ebitda') + ('' if cons else f'_{g}')
                if key not in out:
                    out[key] = v; out[key + '_items'] = items; out[key + '_start'] = start; out[key + '_start_label'] = start_lab if start is not None else None
                items = []; start = None
                continue
            if re.match(r'^net sales', L): continue
            if re.search(r'margin', L): continue
            if re.match(r'^total debt', L): out['debt_ttm'] = v; continue
            if start is not None: items.append({'label': lab, 'v': v, 'cat': cat(lab)})
    return out or None

# ------------------------------------------------------------------ cash flow & balance sheet
CF_MAP = [('cfo', r'^net cash (provided by|used (for|in)|\(used (for|in)\) provided by|provided by \(used (for|in)\)) (continuing )?operating'),
          ('capex', r'^purchases of propert|^capital expenditures|^purchases of properties'), ('capex_disp', r'^proceeds from sales? of propert'),
          ('acq', r'^payments for acquisition|^payments for acquisitions|^acquisition of businesses|^payments for business acquisition'),
          ('divest', r'proceeds from (the )?sale of (discontinued|businesses|fstech|bronto|the fire rescue)|^gross proceeds from sale|^net proceeds from (the )?sale'),
          ('rental', r'rental equipment'),
          ('cfi', r'^net cash (provided by|used (for|in)|\(used (for|in)\) provided by|provided by \(used (for|in)\)) (continuing )?investing'),
          ('div', r'^cash dividends paid'), ('bb', r'^purchases? of treasury|^repurchases? of common'), ('withhold', r'^redemptions? of common stock'),
          ('stock_iss', r'^proceeds from stock|^proceeds from (the )?exercise|^proceeds from issuance of common|^proceeds from equity offering'),
          ('rev_net', r'revolving|^borrowing activity, net|^(increase|decrease|\(decrease\) increase|increase \(decrease\)) in (short-term|revolving)'),
          ('debt_proc', r'^proceeds from (issuance of )?(long-term )?(borrowings|debt)|^borrowings'), ('debt_repay', r'^payments? (on|of) (long-term )?(borrowings|debt)|^repayments? of'),
          ('cff', r'^net cash (provided by|used (for|in)|\(used (for|in)\) provided by|provided by \(used (for|in)\)) (continuing )?financing'),
          ('fx', r'^effects? of (foreign )?exchange'), ('net', r'^(net )?(increase|decrease|\(decrease\) increase|increase \(decrease\)|change) in cash'),
          ('beg', r'beginning of'), ('end', r'end of (period|year)'),
          ('dda', r'^depreciation and amortization'), ('sbc', r'^stock[- ]based compensation|^stock option and award'), ('deftax', r'^deferred income taxes|^deferred taxes'),
          ('disc_cfo', r'operating activities of discontinued'), ('disc_cfi', r'investing activities of discontinued'), ('disc_cff', r'financing activities of discontinued'),
          ('wc', r'^changes in operating assets')]

def ext_cf(tabs, mo, cp):
    for t in tabs:
        if t['type'] != 'cf': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp]
        if not idx: continue
        ci = idx[0]
        out, raw, misal = {'ytd_months': mo}, [], []
        for lab, vals in t['rows']:
            if not vals: continue
            if len(vals) != len(t['cols']): misal.append([lab, vals]); continue
            v = vals[ci]; raw.append([lab, v])
            L = lab.lower().strip(' :*')
            for k, p in CF_MAP:
                if re.search(p, L):
                    if k in ('acq', 'divest', 'capex_disp', 'rental', 'debt_proc', 'debt_repay', 'rev_net', 'disc_cfo', 'disc_cfi', 'disc_cff'): out[k] = round(out.get(k, 0.0) + v, 6)
                    elif k not in out: out[k] = v
                    break
        if 'cfo' in out and 'end' in out:
            out['lines_raw'] = raw
            if misal: out['misaligned'] = misal
            return out
    return None

BS_MAP = [('cash', r'^cash and cash equivalents'), ('restricted', r'^restricted cash'), ('sti', r'^short[- ]term investments'), ('ar', r'^(trade )?accounts receivable'),
          ('inv', r'^inventories'), ('disc_ca', r'^current assets of discontinued|assets held for sale'), ('tca', r'^total current assets'),
          ('ppe', r'^propert(y|ies)(,| and|, plant,?) (and )?equipment'), ('rental', r'^rental equipment'), ('rou', r'^operating lease right'),
          ('gw', r'^goodwill'), ('intang', r'^intangible assets'), ('disc_lta', r'^(long-term|non-?current) assets of discontinued|^assets of discontinued'),
          ('ta_cont', r'^total assets of continuing'), ('ta', r'^total assets$'),
          ('std', r'^short[- ]term borrowings|^current portion of long-term (borrowings|debt)|^current maturities'),
          ('ap', r'^accounts payable'), ('cust_dep', r'^customer deposits'), ('disc_cl', r'^current liabilities of discontinued'), ('tcl', r'^total current liabilities'),
          ('ltd', r'^long-term (borrowings|debt)'), ('disc_ltl', r'^(long-term|non-?current) liabilities of discontinued'),
          ('pension', r'^long-term pension|^pension'), ('dtl', r'^deferred (income )?tax liabilities'), ('tl_cont', r'^total liabilities of continuing'),
          ('disc_ltl2', r'^liabilities of discontinued'), ('tl', r'^total liabilities$'),
          ('eq', r"^total (stockholders|shareholders)['’]? equity|^total (common )?(stockholders|shareholders)"), ('tle', r"^total liabilities and")]

def ext_bs(tabs, cp='cur'):
    for t in tabs:
        if t['type'] != 'bs': continue
        idx = [i for i, c in enumerate(t['cols']) if c[0] == 0 and c[1] == cp]
        if not idx: continue
        ci = idx[0]
        out, raw, misal = {}, [], []
        for lab, vals in t['rows']:
            if not vals: continue
            if len(vals) != len(t['cols']): misal.append([lab, vals]); continue
            v = vals[ci]; raw.append([lab, v])
            L = lab.lower().strip(' :*')
            for k, p in BS_MAP:
                if re.search(p, L):
                    if k in ('std', 'ltd', 'disc_ca', 'disc_cl', 'disc_lta', 'disc_ltl', 'ppe'): out[k] = round(out.get(k, 0.0) + v, 6)
                    elif k not in out: out[k] = v
                    break
            m = re.search(r'(\d[\d.,]*) and (\d[\d.,]*) shares issued', L)
            if m: out['sh_issued'] = float(m.group(1 if cp == 'cur' else 2).replace(',', ''))
            m = re.search(r'treasury stock.*?(\d[\d.,]*) and (\d[\d.,]*) shares', L)
            if m: out['sh_treasury'] = float(m.group(1 if cp == 'cur' else 2).replace(',', ''))
        if 'ta' in out and 'tle' in out:
            out['lines_raw'] = raw
            if misal: out['misaligned'] = misal
            return out
    return None

def ext_selected(tabs):
    out = {}
    for t in tabs:
        if t['type'] != 'selected': continue
        yrs = {}
        for i, c in enumerate(t['cols']):
            yrs.setdefault(c[1], i)
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :*')
            if not vals or len(vals) != len(t['cols']): continue
            k = None
            if re.match(r'^net sales', L): k = 'rev'
            elif re.match(r'^operating income', L): k = 'oi'
            elif re.match(r'^(income|\(loss\) income|income \(loss\)) (\(loss\) )?from continuing', L) and 'diluted' not in L and 'per' not in L: k = 'cont'
            elif re.match(r'^income before|^\(loss\) income before', L): k = 'ebt'
            if k: out[k] = {cp: vals[i] for cp, i in yrs.items()}
        if out: return {'table': out, 'hdr': t['hdr']}
    return None

def ext_outlook(txt):
    m = re.search(r'Outlook(.{0,1500}?)(CONFERENCE CALL|Conference Call|About Federal Signal)', txt, re.S)
    if m: return re.sub(r'\s+', ' ', m.group(1)).strip()[:1500]
    return None

# ------------------------------------------------------------------ seg2 tables (2025+ format): tag with period
def tag_seg2(tabs):
    for t in tabs:
        if t['type'] != 'is': continue
        h = ' '.join(t['hdr'])
        labs = [l.lower() for l, _ in t['rows']]
        if any(l.startswith('segment operating income') for l in labs) and 'Environmental Solutions' in h:
            t['type'] = 'seg2'
            hl = h.lower()
            t['mo'] = 3 if 'three months' in hl else 6 if 'six months' in hl else 9 if 'nine months' in hl else 12
            yrs = [int(y) for y in re.findall(r'(20\d\d)', h)]
            t['year'] = yrs[0] if yrs else None
    # cur/py by year among seg2 tables of the same months
    by = {}
    for t in tabs:
        if t['type'] == 'seg2': by.setdefault(t['mo'], set()).add(t['year'])
    for t in tabs:
        if t['type'] == 'seg2':
            ys = sorted(by[t['mo']], reverse=True); t['cp'] = ['cur', 'py', 'py2'][ys.index(t['year'])]
    return tabs

def doc_tables(path, docyear=None):
    tabs = parsed(path)
    if docyear is not None: P.relabel(tabs, docyear)
    if tabs and not any(t['type'] == 'seg2' for t in tabs): tag_seg2(tabs)
    # releases 2017+: group tables include Adjusted EBITDA rows; classify by orders / backlog first
    for t in tabs:
        if t['type'] == 'ebitda' and any(re.match(r'^(total )?orders|^backlog', l.lower()) for l, _ in t['rows']): t['type'] = 'grp'
    if docyear is not None: P.relabel(tabs, docyear)
    return tabs

# ------------------------------------------------------------------ records
def block_k(path, mo, cp, annual, bs_cp, docyear):
    tabs = doc_tables(path, docyear)
    o = {'is': ext_is(tabs, mo, cp), 'seg': ext_seg(tabs, mo, cp), 'cf': ext_cf(tabs, mo, cp)}
    if bs_cp: o['bs'] = ext_bs(tabs, bs_cp)
    if annual and cp == 'cur': o['selected'] = ext_selected(tabs)
    g = ext_grp(tabs, mo, cp)
    if g: o['grp'] = g
    return {k: v for k, v in o.items() if v}

def block_rel(path, mo, cp, docyear, ytd=None):
    tabs = doc_tables(path, docyear)
    txt = text(path)
    o = {'is': ext_is(tabs, mo, cp), 'grp': ext_grp(tabs, mo, cp), 'adjeps': ext_adjeps(tabs, mo, cp), 'ebitda': ext_ebitda(tabs, mo, cp),
         'corp_text': ext_corp_text(txt, mo), 'bs': ext_bs(tabs, 'cur' if cp == 'cur' else 'py') if cp == 'cur' else None}
    if ytd: o['cf'] = ext_cf(tabs, ytd, cp)
    if cp == 'cur': o['outlook'] = ext_outlook(txt)
    return {k: v for k, v in o.items() if v}

def rec_period(docs, fy, q, annual):
    key = (fy, 4 if annual else q)
    d = docs.get(key)
    if not d or 'primary' not in d: return None
    mo = 12 if annual else 3
    ytd = 12 if annual else 3 * q
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'sources': {'filing': d['primary_url'], 'filing_date': d['date']}, 'notes': []}
    if d.get('release_url'): rec['sources']['release'] = d['release_url']; rec['sources']['release_date'] = d.get('release_date')
    # own filing: 3M (quarter) or 12M (annual); YTD cash flow; balance sheet
    rec['k'] = block_k(d['primary'], mo, 'cur', annual, 'cur', fy)
    if not annual:
        rec['k']['cf'] = ext_cf(doc_tables(d['primary'], fy), ytd, 'cur') or rec['k'].get('cf')
        rec['k']['is_ytd'] = ext_is(doc_tables(d['primary'], fy), ytd, 'cur') if q > 1 else None
        rec['k']['seg_ytd'] = ext_seg(doc_tables(d['primary'], fy), ytd, 'cur') if q > 1 else None
    # following year's filing, prior-year columns
    d1 = docs.get((fy + 1, 4 if annual else q))
    if d1 and 'primary' in d1:
        rec['sources']['filing_next'] = d1['primary_url']
        rec['k1'] = block_k(d1['primary'], mo, 'py', annual, 'py' if annual else None, fy + 1)
        if not annual:
            rec['k1']['cf'] = ext_cf(doc_tables(d1['primary'], fy + 1), ytd, 'py') or rec['k1'].get('cf')
            rec['k1']['is_ytd'] = ext_is(doc_tables(d1['primary'], fy + 1), ytd, 'py') if q > 1 else None
            rec['k1']['seg_ytd'] = ext_seg(doc_tables(d1['primary'], fy + 1), ytd, 'py') if q > 1 else None
    if annual:
        d2 = docs.get((fy + 2, 4))
        if d2 and 'primary' in d2:
            rec['sources']['filing_next2'] = d2['primary_url']
            rec['k2'] = block_k(d2['primary'], 12, 'py2', True, None, fy + 2)
    # releases
    if d.get('release'):
        rec['rel'] = block_rel(d['release'], mo, 'cur', fy, ytd)
        if annual: rec['rel_q4'] = block_rel(d['release'], 3, 'cur', fy)
    if d1 and d1.get('release'):
        rec['rel1'] = block_rel(d1['release'], mo, 'py', fy + 1, ytd)
        if annual: rec['rel1_q4'] = block_rel(d1['release'], 3, 'py', fy + 1)
    if annual and rec['k'].get('is') and rec['k']['is'].get('sh_d') is None:
        for dd, cpx in ((d, 'cur'), (d1, 'py'), (docs.get((fy + 2, 4)), 'py2')):
            if not dd or 'primary' not in dd or rec['k']['is'].get('sh_d') is not None: continue
            dy = fy + {'cur': 0, 'py': 1, 'py2': 2}[cpx]
            for t in P.html_tables(open(dd['primary'], 'rb').read()):
                if not any(re.search(r'^average shares outstanding\W+basic', l, re.I) for l, _ in t['rows']): continue
                cols = P.columns(t)
                if not cols: continue
                t2 = dict(t, cols=cols); P.relabel([t2], dy)
                b = P.rowval(t2, r'^average shares outstanding\W+basic', 12, cpx); dl = P.rowval(t2, r'^diluted shares outstanding', 12, cpx)
                if isinstance(b, float) and isinstance(dl, float):
                    rec['k']['is']['sh_b'], rec['k']['is']['sh_d'] = b, dl
                    rec['notes'].append(f'Weighted-average shares from the EPS note table of {dd["primary_url"]}.')
                    break
        t = re.sub(r'\s+', ' ', text(d['primary']))
        m = re.search(r'weighted average common shares outstanding, which totaled ([\d.]+) million, ([\d.]+) million and ([\d.]+) million', t)
        m2 = re.search(r'weighted average number of shares outstanding for diluted earnings \(loss\) per share were ([\d.]+) million, ([\d.]+) million and ([\d.]+) million', t)
        if m: rec['k']['is']['sh_b'] = float(m.group(1)); rec['notes'].append('Basic weighted-average shares from the 10-K Note 1 text (earnings per share policy).')
        if m2: rec['k']['is']['sh_d'] = float(m2.group(1))
        elif m: rec['k']['is']['sh_d'] = float(m.group(1)); rec['notes'].append('10-K text gives one weighted-average share count (no dilutive shares); used as diluted.')
    # XBRL extras (as first filed)
    kind = 'FY' if annual else 'YTD'
    qq = 4 if annual else q
    rec['x'] = {'sbc_ytd': xbrl.first_of(['ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense'], fy, kind, qq),
                'deftax_ytd': xbrl.first_of(['DeferredIncomeTaxExpenseBenefit'], fy, kind, qq),
                'dda_ytd': xbrl.first_of(['DepreciationDepletionAndAmortization'], fy, kind, qq),
                'div_paid_ytd': xbrl.first_of(['PaymentsOfDividendsCommonStock'], fy, kind, qq),
                'dps_declared': xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY' if annual else 'Q', qq),
                'sh_out': xbrl.first_of(['CommonStockSharesOutstanding'], fy, 'I', qq),
                'sh_cover': xbrl.value('EntityCommonStockSharesOutstanding', fy, 'cover', qq),
                'rev': xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'], fy, 'FY' if annual else 'Q', qq),
                'oi': xbrl.value('OperatingIncomeLoss', fy, 'FY' if annual else 'Q', qq),
                'ni': xbrl.value('NetIncomeLoss', fy, 'FY' if annual else 'Q', qq),
                'cont': xbrl.value('IncomeLossFromContinuingOperations', fy, 'FY' if annual else 'Q', qq),
                'eps_d': xbrl.value('EarningsPerShareDiluted', fy, 'FY' if annual else 'Q', qq),
                'ta': xbrl.value('Assets', fy, 'I', qq),
                'rev_last': xbrl.first_of(['Revenues', 'RevenueFromContractWithCustomerExcludingAssessedTax', 'SalesRevenueNet'], fy, 'FY' if annual else 'Q', qq, pick='last'),
                'oi_last': xbrl.value('OperatingIncomeLoss', fy, 'FY' if annual else 'Q', qq, pick='last'),
                'cont_last': xbrl.value('IncomeLossFromContinuingOperations', fy, 'FY' if annual else 'Q', qq, pick='last')}
    rec['x'] = {k: v for k, v in rec['x'].items() if v is not None}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    docs = index()
    json.dump({f'{k[0]}-Q{k[1]}': {kk: vv for kk, vv in v.items() if kk.endswith('url') or kk == 'date' or kk == 'form' or kk == 'release_date'} for k, v in sorted(docs.items())},
              open(os.path.join(OUT, '_docs.json'), 'w'), indent=1)
    n = 0
    for fy in range(2006, 2026):
        r = rec_period(docs, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
        else: print('missing annual', fy)
    for fy in range(2013, 2027):
        for q in (1, 2, 3):
            if fy == 2026 and q > 3: break
            r = rec_period(docs, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
            else: print('missing', fy, q)
    xbrl.dump_subset()
    print(n, 'period files')

if __name__ == '__main__':
    main()
