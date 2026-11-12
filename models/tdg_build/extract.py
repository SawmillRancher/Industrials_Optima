"""Per-period extraction from the TransDigm EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2025 and quarters Q1 FY13 - Q3 FY26. Each record carries:
  is     statement of income (earnings release, three-month / twelve-month column; cross-checked to the 10-Q / 10-K)
  ngaap  EBITDA -> EBITDA As Defined and adjusted net income / adjusted EPS reconciliations (release), with the company's
         item labels; two-class EPS data (dividends on participating securities, weighted shares)
  seg    segment net sales and EBITDA As Defined and the reconciliation to pre-tax income (10-Q / 10-K segment note;
         quarters = the three-month column of that quarter's 10-Q, fiscal years = the 10-K; Q4 derived later as FY - 9M)
  em     net sales by end market and segment (10-Q / 10-K, fiscal 2019 onwards; FY2017-18 from the FY2019 10-K comparatives)
  cf     cash flow, year to date (cf.ytd_months), from the 10-Q / 10-K
  bs     balance sheet at period end (10-Q / 10-K), incl. shares issued / treasury from the equity captions
  x      XBRL company facts (cross-checks)
  py     prior-year comparative as presented in the following year's release (restatement detection)
  sources / notes
Units: documents are in USD thousands to the fiscal 2019 10-K and in millions from fiscal 2020; everything is stored in
millions (per share as published; shares in millions). Fiscal years end 30 September; quarters are 13-week periods ending on
the Saturday nearest the calendar quarter end.
"""
import json, os, re, datetime as dt
import parse_filing as PF
import xbrl

S = os.environ.get('TDG_SRC', '/tmp/tdg_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '1260221'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc
def docpath(o, doc): return os.path.join(S, 'docs', f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{doc}")

# ------------------------------------------------------------------ units
def doc_units(html):
    t = html.decode('utf-8', 'ignore').lower()
    th = len(re.findall(r'in thousands', t)); mi = len(re.findall(r'in millions', t))
    return 1000.0 if th >= mi else 1.0
def tab_units(t, default):
    h = PF.hdr_text(t).lower()
    if 'thousands' in h: return 1000.0
    if 'millions' in h: return 1.0
    return default

class Doc:
    def __init__(self, path):
        self.path = path
        self.html = open(path, 'rb').read()
        self.tabs = PF.parse(self.html)
        self.du = doc_units(self.html)
        self.ok = len(self.tabs) > 0 and b'File Unavailable' not in self.html[:3000]
    def tables(self, ty, must=(), months=None, cp='cur', first_label=None):
        out = []
        for t in self.tabs:
            if t['type'] != ty: continue
            if re.search(r'guidance|ending september 30, 20\d\d', PF.hdr_text(t).lower()): continue
            labs = ' || '.join(l.lower() for l, _ in t['rows'])
            if any(m not in labs for m in must): continue
            if first_label:
                fl = next((l.lower() for l, v in t['rows'] if v), '')
                if not re.search(first_label, fl): continue
            if months is not None and not any(c[0] == months and c[1] == cp for c in t['cols']): continue
            out.append(t)
        return out
    def val(self, t, label_re, months, cp='cur', nth=0, exclude=None, start_after=None, raw=False):
        idx = [i for i, c in enumerate(t['cols']) if c[0] == months and c[1] == cp]
        if not idx: return None
        i = idx[0]; hits = 0; on = start_after is None
        for lab, vals in t['rows']:
            if not on:
                if re.search(start_after, lab, re.I): on = True
                continue
            if not vals or i >= len(vals): continue
            if re.search(label_re, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
                if hits == nth:
                    v = vals[i]
                    return v if raw else round(v / tab_units(t, self.du), 6)
                hits += 1
        return None

# ------------------------------------------------------------------ indices
def fyq_of_release(date):
    d = dt.date.fromisoformat(date)
    if d.month >= 10: return d.year, 4
    if d.month <= 3: return d.year, 1
    if d.month <= 6: return d.year, 2
    return d.year, 3

def fyq_of_report(rep):
    e = dt.date.fromisoformat(rep)
    fy = e.year + (1 if e.month >= 10 else 0)
    q = {12: 1, 1: 1, 3: 2, 4: 2, 6: 3, 7: 3, 9: 4, 10: 4}[e.month]
    return fy, q

def build_indices():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings, others = {}, {}, []
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            for doc in o['files']:
                if doc == o['primary']: continue
                p = docpath(o, doc)
                if not os.path.exists(p): continue
                d = Doc(p)
                if not d.ok: continue
                ist = d.tables('is', months=3)
                if not ist or not d.tables('ebitda'): continue
                fy, q = fyq_of_release(o['date'])
                if (fy, q) not in rel: rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), doc=d, acc=o['acc'])
        elif o['form'] in ('10-Q', '10-K'):
            fy, q = fyq_of_report(o['report'])
            p = docpath(o, o['primary'])
            if not os.path.exists(p): continue
            d = Doc(p)
            if not d.ok: continue
            if (fy, q) not in filings or o['form'] == '10-K': filings[(fy, q)] = dict(date=o['date'], url=url(o, o['primary']), doc=d, form=o['form'], report=o['report'])
        elif o['form'] == '8-K':
            others.append(o)
    return rel, filings, others

# ------------------------------------------------------------------ statement of income
def norm(lab):
    """lower-case label without '(loss)' / '(benefit)' / 'net' qualifiers and footnote marks."""
    L = lab.lower().strip(' :*')
    L = re.sub(r'\((loss|losses|benefit|income|expense|decrease|increase)\)\s*', '', L)
    L = re.sub(r'\s*\(\d\)$', '', L)
    L = re.sub(r'\s+', ' ', L).replace('—', ' ').replace(' - ', ' ').replace('-net', ' net').strip()
    return L

IS_MAP = [('rev', r'^net sales$'), ('cogs', r'^cost of sales'), ('gp', r'^gross profit'), ('sga', r'^selling and administrative'),
          ('amort', r'^amortization of intangible'), ('oi', r'^income from operations$'), ('int_net', r'^interest expense'),
          ('refin', r'^refinancing costs|^loss on (debt )?extinguishment'), ('other', r'^other (expense|income|\(income\))'),
          ('gain', r'^gain on sale of business|^loss on sale of business'),
          ('ebt', r'income (from (continuing )?operations )?before income taxes'), ('tax', r'^income tax provision|^income taxes$|^income tax$'),
          ('ni_cont', r'^income from continuing operations( including noncontrolling interests)?$'), ('disc', r'discontinued operations'),
          ('ni', r'^net income( including noncontrolling interests)?$'), ('nci', r'^less: net income attributable to noncontrolling|^net income attributable to noncontrolling|^less: net attributable to noncontrolling'),
          ('ni_td_cont', r'^net income from continuing operations attributable to td group'),
          ('ni_td', r'^net income attributable to td group'), ('ni_common', r'^net income applicable to (td group )?common stock'),
          ('dps', r'^cash dividends (declared|paid) per')]
EPS_MAP = [('eps_cont', r'per share from continuing'), ('eps_disc', r'per share from discontinued'),
           ('eps_b', r'^basic earnings per share|^basic$|earnings per share basic$|per share basic$'),
           ('eps_d', r'^diluted earnings per share|^diluted$|basic and diluted$|^(net )?earnings per share$|^earnings per share$|^net earnings per share$')]
PS = {'eps_b', 'eps_d', 'eps_cont', 'eps_disc', 'dps'}

def ext_is(doc, mo, cp='cur'):
    ts = doc.tables('is', months=mo, cp=cp)
    ts = [t for t in ts if 'eliminations' not in PF.hdr_text(t).lower() and 'guarantor' not in PF.hdr_text(t).lower()]
    if not ts: return None
    t = max(ts, key=lambda t: len(t['rows']))
    idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp][0]
    u = tab_units(t, doc.du)
    out, other_op, below, state, shares, eps = {}, [], [], 'pre', False, False
    for lab, vals in t['rows']:
        L = norm(lab)
        if 'weighted' in L and 'shares' in L: shares, eps = True, False
        elif 'per share' in L and not vals: eps = True
        if not vals or idx >= len(vals): continue
        v = vals[idx]
        if shares:
            sv = round(v / (1000.0 if u == 1000 else 1.0), 6)
            if 'basic and diluted' in L: out.setdefault('sh_b', sv); out.setdefault('sh_d', sv); continue
            if re.search(r'^basic', L): out.setdefault('sh_b', sv); continue
            if re.search(r'^diluted', L): out.setdefault('sh_d', sv); continue
        if eps or 'per share' in L:
            if 'dividend' in L:
                out['dps'] = v; out['dps_label'] = lab; continue
            key = next((k for k, p in EPS_MAP if re.search(p, L)), None)
            if key and key not in out:
                out[key] = v; out[key + '_label'] = lab
                if 'basic and diluted' in L and key == 'eps_d': out.setdefault('eps_b', v)
            continue
        key = next((k for k, p in IS_MAP if re.search(p, L)), None)
        if key and key not in out:
            out[key] = round(v / u, 6)
            if key == 'refin' and state == 'ops': out['refin_op'] = out.pop('refin')
            if key == 'rev': state = 'ops'
            if key == 'oi': state = 'below'
            if key == 'ebt': state = 'post'
        elif state == 'ops' and key is None and 'total' not in L: other_op.append([lab, round(v / u, 6)])
        elif state == 'below' and key is None: below.append([lab, round(v / u, 6)])
    if 'ni' not in out and 'ni_cont' in out: out['ni'] = round(out['ni_cont'] + out.get('disc', 0.0), 6); out['ni_derived'] = 'income from continuing operations incl. NCI + discontinued operations'
    out['other_op_lines'] = other_op; out['below_oi_lines'] = below
    out['units'] = 'thousands' if u == 1000 else 'millions'
    return out

# ------------------------------------------------------------------ non-GAAP (release)
CAT = [('TAX', r'^tax adjustment|tax effect'), ('AMORT', r'backlog amortization'),
       ('STEPUP', r'inventory purchase accounting|inventory step'),
       ('ACQ', r'acquisition|transaction|integration'), ('SBC', r'stock|deferred compensation|option expense|compensation'),
       ('DEBT', r'refinanc|extinguishment|debt'), ('GAIN', r'gain|loss on sale|sale of business'), ('IMPAIR', r'impair|write[- ]?down'),
       ('IPO', r'public offering|equity offering'), ('DISC', r'discontinued'), ('OTHER', r'.')]
def cat(lab):
    L = lab.lower()
    return next(c for c, p in CAT if re.search(p, L))

def ext_ebitda(doc, mo, cp='cur'):
    ts = [t for t in doc.tables('ebitda', months=mo, cp=cp) if re.search(r'^net income|^income from continuing', norm(next((l for l, v in t['rows'] if v), '')))]
    ts = [t for t in ts if any('ebitda as defined' in l.lower() for l, _ in t['rows'])]
    if not ts: return None
    t = ts[0]; u = tab_units(t, doc.du)
    idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp][0]
    out, items, state = {'items': [], 'post_items': []}, [], 'pre'
    nc = len(t['cols'])
    for lab, vals in t['rows']:
        L = norm(lab)
        if vals and 1 < len(vals) < nc:      # a dropped empty cell: right-align (FY2006 'Non-Recurring IPO Costs', see manual_items.json)
            vals = [None] * (nc - len(vals)) + list(vals); out.setdefault('realigned', []).append(lab)
        if not vals or idx >= len(vals) or vals[idx] is None:
            continue
        v = round(vals[idx] / u, 6)
        if state == 'pre':
            if re.match(r'^ebitda', L): out['ebitda_pub'] = v; out['ebitda_label'] = lab; state = 'items'
            elif re.match(r'^net income', L): out['ni'] = v
            elif 'discontinued' in L: out['disc'] = v
            elif re.match(r'^income from continuing', L): out['ni_cont'] = v
            elif re.match(r'^depreciation', L): out['dda'] = v
            elif re.match(r'^interest', L): out['int_net'] = v
            elif re.match(r'^income tax', L): out['tax'] = v
            elif re.match(r'^ebitda', L): out['ebitda_pub'] = v; out['ebitda_label'] = lab; state = 'items'
        elif state == 'items':
            if re.match(r'^gross adjustments', L): out['gross_adj'] = v
            elif re.match(r'^ebitda as defined', L) and 'margin' not in L: out['ebitda_ad_pub'] = v; state = 'post'
            elif 'margin' in L: continue
            else: out['items'].append({'label': lab, 'val': v, 'cat': cat(lab)})
        else:
            if 'margin' in L: out['ebitda_ad_margin_pub'] = vals[idx]
            elif re.match(r'^adjusted ebitda as defined', L): out['adj_ebitda_ad_pub'] = v
            else: out['post_items'].append({'label': lab, 'val': v, 'cat': cat(lab)})
    return out

def ext_adjni(doc, mo, cp='cur'):
    """Adjusted net income / adjusted EPS (release): two-class EPS block, then the 'Adjusted Earnings Per Share' block
    (start line + gross adjustments to EBITDA + purchase-accounting backlog amortization + tax adjustment = adjusted net income),
    then the per-share bridge (dividend-equivalent inclusion). First matching table wins."""
    for t in doc.tables('adjni', months=mo, cp=cp):
        u = tab_units(t, doc.du); su = 1000.0 if u == 1000 else 1.0
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp][0]
        rows = [(norm(l), l, (v[idx] if v and idx < len(v) else None)) for l, v in t['rows']]
        hi = next((k for k, (L, l, v) in enumerate(rows) if v is None and re.match(r'^adjusted earnings per share$', L)), None)
        out = {'items': []}
        pre = rows[:hi] if hi is not None else rows
        for L, l, v in pre:
            if v is None: continue
            if re.search(r'dividends.*participating', L): out.setdefault('div_part', round(v / u, 6))
            elif re.match(r'^weighted[- ]average common shares', L): out.setdefault('sh_common', round(v / su, 6))
            elif re.match(r'^vested options deemed', L): out.setdefault('sh_part', round(v / su, 6))
            elif re.search(r'adjusted basis', L): out['sh_adj'] = round(v / su, 6)
            elif re.match(r'^total shares|^weighted[- ]average shares outstanding$|^diluted weighted', L): out.setdefault('sh_total', round(v / su, 6))
            elif re.search(r'attributable to noncontrolling', L): out.setdefault('nci', round(v / u, 6))
        blk = rows[hi + 1:] if hi is not None else rows
        state = 'start'
        for L, l, v in blk:
            if v is None:
                continue
            if state == 'start':
                out['start'] = round(v / u, 6); out['start_label'] = l; state = 'items'; continue
            if state == 'items':
                if re.match(r'^gross adjustments', L): out['gross_adj'] = round(v / u, 6)
                elif re.match(r'^purchase accounting backlog', L): out['backlog_amort'] = round(v / u, 6)
                elif re.match(r'^tax adjustment', L): out['tax_adj'] = round(v / u, 6)
                elif re.match(r'^adjusted net income', L): out['adj_ni_pub'] = round(v / u, 6); state = 'post'
                else: out['items'].append({'label': l, 'val': round(v / u, 6), 'cat': cat(l)})
                continue
            if re.match(r'^adjusted (diluted )?earnings per share|^adjusted diluted', L) and 'adj_eps_pub' not in out: out['adj_eps_pub'] = v
            elif re.match(r'^adjusted basic', L): out['adj_eps_b_pub'] = v
            elif re.match(r'^inclusion of the dividend', L): out.setdefault('eps_div_equiv', v)
            elif re.match(r'^basic$', L): out.setdefault('sh_b', round(v / su, 6))
            elif re.match(r'^diluted$', L): out.setdefault('sh_d', round(v / su, 6))
        if out.get('adj_ni_pub') is not None:
            if 'sh_adj' not in out: out['sh_adj'] = out.get('sh_total', out.get('sh_d'))
            return out
    return None

def ext_narrative(doc):
    """organic growth %, end-market growth % and guidance text from the release narrative."""
    txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', doc.html.decode('utf-8', 'ignore')))
    out = {}
    m = re.search(r'organic sales growth[^.]{0,80}?was (?:approximately )?([\d.]+)\s?%', txt, re.I)
    if m: out['organic_growth_pct'] = float(m.group(1))
    m = re.search(r'(Fiscal \d{4} Outlook.*?)(Earnings Conference Call|About TransDigm)', txt, re.I | re.S)
    if m: out['guidance_text'] = m.group(1)[:6000]
    for k, p in (('com_oem', r'commercial OEM[^.]{0,120}'), ('com_aft', r'commercial aftermarket[^.]{0,120}'), ('defense', r'defense[^.]{0,120}')):
        ms = re.findall(p, txt, re.I)
        if ms: out[f'narr_{k}'] = [x.strip() for x in ms[:4]]
    return out

# ------------------------------------------------------------------ 10-Q / 10-K: segments, end markets, cash flow, balance sheet
SEGN = {'power': 'pc', 'airframe': 'af', 'non-aviation': 'na', 'non- aviation': 'na', 'nonaviation': 'na', 'esterline': 'es', 'total esterline': 'es'}
def segkey(L):
    for k, v in SEGN.items():
        if L.startswith(k): return v
    return None

ITEM_MAP = [('dda', r'^depreciation'), ('int_net', r'^interest'), ('acq', r'^acquisition'), ('sbc', r'^(stock|non-cash stock)'),
            ('refin', r'^refinancing'), ('other', r'^other'), ('ebt', r'income (from (continuing )?operations )?before income taxes'),
            ('corp', r'unallocated corporate'), ('seg_ebitda_tot', r'^total segment ebitda'), ('ebitda_ad', r'^total company ebitda'),
            ('disc', r'discontinued')]

def ext_seg(doc, mo, cp='cur'):
    out = {}
    # ASU 2023-07 format (segments as columns, period in the title)
    for t in doc.tabs:
        if t['type'] != 'seg2' or not t.get('period'): continue
        k, end = t['period']
        if k != mo: continue
        if cp == 'cur' and not doc.path.split('_')[0] or False: pass
        fy, q = fyq_of_report(end)
        tag = (fy, q)
        out.setdefault('_seg2', {})[tag] = t
    segs2 = out.pop('_seg2', None)
    if segs2:
        # choose the current-period table (latest end date) or prior-year (cp='py')
        keys = sorted(segs2.keys(), reverse=True)
        t = segs2[keys[0] if cp == 'cur' else keys[1]] if (cp == 'cur' or len(keys) > 1) else None
        if t:
            u = tab_units(t, doc.du); cols = t['cols']
            ci = {segkey(c.lower()): i for i, c in enumerate(cols) if segkey(c.lower())}
            ti = len(cols) - 1
            em = {}
            for lab, vals in t['rows']:
                L = lab.lower().strip(' :')
                if not vals: continue
                def g(i): return round(vals[i] / u, 6) if i is not None and i < len(vals) else None
                if re.match(r'^commercial (and non-aerospace )?oem', L): em['pc_coem'], em['af_coem'] = g(ci['pc']), g(ci['af']); em['coem'] = g(len(vals) - 1)
                elif re.match(r'^commercial (and non-aerospace )?aftermarket', L): em['pc_caft'], em['af_caft'] = g(ci['pc']), g(ci['af']); em['caft'] = g(len(vals) - 1)
                elif re.match(r'^defense', L): em['pc_def'], em['af_def'] = g(ci['pc']), g(ci['af']); em['def'] = g(len(vals) - 1)
                elif re.match(r'^non-aviation', L): em['na'] = g(len(vals) - 1)
                elif re.match(r'^net sales', L):
                    for s, i in ci.items(): out[f'{s}_sales'] = g(i)
                    out['seg_sales_tot'] = g(ti)
                elif re.match(r'^total segment ebitda', L):
                    for s, i in ci.items(): out[f'{s}_ebitda'] = g(i)
                    out['seg_ebitda_tot'] = g(ti)
                elif re.match(r'^other segment expenses', L):
                    for s, i in ci.items(): out[f'{s}_other_exp'] = g(i)
                else:
                    key = next((k for k, p in ITEM_MAP if re.search(p, L)), None)
                    if key and key not in out: out[key] = g(0)
            if em: out['em'] = em
            if 'corp' in out and 'seg_ebitda_tot' in out: out['ebitda_ad'] = round(out['seg_ebitda_tot'] - out['corp'], 6)
            out['format'] = 'asu2023-07'
            return out
    # pre-2025 format: 'seg' tables with period columns
    for t in doc.tables('seg', months=mo, cp=cp):
        u = tab_units(t, doc.du)
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp][0]
        labs = ' || '.join(l.lower() for l, _ in t['rows']) + ' ' + PF.hdr_text(t).lower()
        section = 'sales' if 'net sales to external' in labs and 'ebitda as defined' not in ' || '.join(l.lower() for l, _ in t['rows']) else 'ebitda'
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :')
            if not vals:
                if 'net sales to external' in L: section = 'sales'
                elif 'ebitda as defined' in L: section = 'ebitda'
                continue
            if idx >= len(vals): continue
            v = round(vals[idx] / u, 6)
            s = segkey(L)
            if s:
                key = f'{s}_sales' if section == 'sales' else f'{s}_ebitda'
                if key not in out: out[key] = v
            elif re.match(r'^total$|^total net sales|^net sales$', L) and section == 'sales': out['seg_sales_tot'] = v
            else:
                key = next((k for k, p in ITEM_MAP if re.search(p, L)), None)
                if key and key not in out: out[key] = v
        # total row printed as a label-only line ("590,761 | 465,609 | ...") -> parse
        for lab, vals in t['rows']:
            if not vals and section == 'sales' and re.match(r'^[\d,]+(\s*\|\s*[\d,]+)+$', lab.strip()):
                parts = [PF.pnum(x) for x in lab.split('|')]
                if idx < len(parts) and parts[idx] is not None: out.setdefault('seg_sales_tot', round(parts[idx] / u, 6))
    if out: out['format'] = 'legacy'
    return out or None

EM_MAP = [('coem', r'^commercial (and non-aerospace )?oem'), ('caft', r'^commercial (and non-aerospace )?aftermarket'), ('def', r'^defense'), ('est', r'^esterline'),
          ('tot', r'^total (power|airframe)')]
def ext_em(doc, mo, cp='cur'):
    out = {}
    for t in doc.tables('em', months=mo, cp=cp):
        u = tab_units(t, doc.du)
        idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp][0]
        hdr = PF.hdr_text(t).lower()
        seg = 'pc' if 'power' in hdr.split('net sales to external customers')[-1][:40] or 'power' in hdr[-40:] else None
        if 'power' in hdr: seg = 'pc'
        for lab, vals in t['rows']:
            L = lab.lower().strip(' :')
            if not vals:
                s = segkey(L)
                if s: seg = s
                continue
            if idx >= len(vals): continue
            v = round(vals[idx] / u, 6)
            if re.match(r'^total non-aviation|^non-aviation', L): out['na'] = v; continue
            if re.match(r'^total esterline', L): out['es'] = v; continue
            key = next((k for k, p in EM_MAP if re.search(p, L)), None)
            if key == 'tot':
                s = 'pc' if 'power' in L else 'af'
                out[f'{s}_tot'] = v; seg = 'af' if s == 'pc' else None; continue
            if key and seg: out[f'{seg}_{key}'] = v
        if out: break
    return out or None

CF_MAP = [('ni', r'^net income'), ('dep', r'^depreciation$|^depreciation expense|^depreciation and amortization'), ('amort', r'^amortization of intangible|^amortization of intangibles'),
          ('amort_debt', r'^amortization of debt issuance|^amortization of debt discount|^amortization of (original issue|debt)'),
          ('gain', r'gain on sale|loss on sale|gain.*disposition'), ('refin', r'refinancing|loss on extinguishment|debt extinguishment'),
          ('sbc', r'^non-cash (stock|equity) (and deferred )?compensation|^stock compensation|^stock option|^non-cash compensation|^equity compensation'),
          ('deferred_tax', r'^deferred income taxes|^deferred tax'), ('cfo', r'^net cash .*operating'),
          ('capex', r'^capital expenditures|^purchases? of property'), ('acq', r'^acquisition of businesses|^acquisitions? of businesses|^payments? for acquisition|^cash paid for acquisition|^acquisition of business'),
          ('divest', r'^proceeds from (the )?sale of business|^cash proceeds from sale'), ('cfi', r'^net cash .*investing'),
          ('stock_proc', r'^proceeds from exercise of stock options|^proceeds from stock option|^proceeds from exercise'),
          ('dividends', r'^dividends|^cash dividends|^special dividend'), ('buyback', r'^repurchase of common|^repurchases of common|^treasury stock|^purchase of treasury'),
          ('cff', r'^net cash .*financing'), ('fx', r'^effect of exchange'), ('net', r'^net .*(increase|decrease|change).* in cash'),
          ('beg', r'beginning of'), ('end', r'end of')]
def ext_organic(doc, mo):
    """MD&A 'organic sales / acquisition sales' table (current period; first two value columns = current, prior year)."""
    for t in doc.tables('organic', months=mo):
        u = tab_units(t, doc.du); out = {}
        for lab, vals in t['rows']:
            L = norm(lab)
            if not vals or len(vals) < 2: continue
            if L.startswith('organic sales'): out['org_sales'], out['org_sales_py'] = round(vals[0] / u, 6), round(vals[1] / u, 6)
            elif L.startswith('acquisition sales'): out['acq_sales'], out['acq_sales_py'] = round(vals[0] / u, 6), round(vals[1] / u, 6)
            elif L.startswith('net sales'): out['rev'], out['rev_py'] = round(vals[0] / u, 6), round(vals[1] / u, 6)
        if 'org_sales' in out: return out
    return None

def ext_cf(doc, mo, cp='cur'):
    ts = [t for t in doc.tables('cf', months=mo, cp=cp) if 'eliminations' not in PF.hdr_text(t).lower() and 'guarantor' not in PF.hdr_text(t).lower()]
    if not ts: return None
    t = max(ts, key=lambda t: len(t['rows'])); u = tab_units(t, doc.du)
    idx = [i for i, c in enumerate(t['cols']) if c[0] == mo and c[1] == cp][0]
    out, raw, debt_lines, wc = {'ytd_months': mo}, [], [], 0.0
    section = 'op'
    for lab, vals in t['rows']:
        L = lab.lower().strip(' :')
        if not vals:
            if 'investing' in L: section = 'inv'
            elif 'financing' in L: section = 'fin'
            elif 'changes in assets' in L: section = 'wc'
            continue
        if idx >= len(vals): continue
        v = round(vals[idx] / u, 6); raw.append([lab, v])
        key = next((k for k, p in CF_MAP if re.search(p, L)), None)
        if key == 'acq' and 'liabilities' in L: key = None
        if key:
            if key in ('acq', 'divest', 'dividends', 'buyback', 'stock_proc'): out[key] = round(out.get(key, 0.0) + v, 6)
            elif key not in out: out[key] = v
            if key == 'cfo': section = 'inv'
            if key == 'cfi': section = 'fin'
            if key == 'cff': section = 'post'
        elif section == 'wc': wc += v
        elif section == 'fin' and re.search(r'debt|notes|term loan|borrowing|securitization|credit facility|revolving|financing costs', L): debt_lines.append([lab, v])
    out['wc_change'] = round(wc, 6) if wc else out.get('wc_change', 0.0)
    out['debt_lines'] = debt_lines
    out['debt_net'] = round(sum(v for _, v in debt_lines), 6)
    out['lines_raw'] = raw
    return out

BS_MAP = [('cash', r'^cash and cash equivalents'), ('rcash', r'^restricted cash'), ('ar', r'^trade accounts receivable|^accounts receivable'), ('inv', r'^inventories'),
          ('tca', r'^total current assets'), ('ppe', r'^property, plant and equipment'), ('gw', r'^goodwill'), ('intang', r'^other intangible assets|^intangible assets'),
          ('ta', r'^total assets'), ('cltd', r'^current portion of long-term debt'), ('std', r'^short-term borrowings'), ('ap', r'^accounts payable'),
          ('accrued', r'^accrued (liabilities|and other|expenses)'), ('tcl', r'^total current liabilities'), ('ltd', r'^long-term debt'),
          ('deftax', r'^deferred income taxes'), ('other_ncl', r'^other non-current liabilities'), ('tl', r'^total liabilities$'),
          ('rnci', r'^redeemable noncontrolling'), ('eq_td', r"^total td group stockholders|^total stockholders[\u2019'] (equity|deficit)$"), ('nci', r'^noncontrolling interests$'),
          ('te', r"^total stockholders[\u2019'] (equity|deficit)$|^total equity"), ('tle', r'^total liabilities')]
def ext_bs(doc, cp='cur'):
    ts = [t for t in doc.tables('bs') if 'eliminations' not in PF.hdr_text(t).lower() and 'guarantor' not in PF.hdr_text(t).lower() and 'acquired' not in PF.hdr_text(t).lower()]
    ts = [t for t in ts if any(re.match(r'^total current assets', l.lower()) for l, _ in t['rows'])]
    if not ts: return None
    t = max(ts, key=lambda t: len(t['rows'])); u = tab_units(t, doc.du)
    idx = 0 if cp == 'cur' else 1
    out, raw = {}, []
    def nums_after(txt, word):
        m = re.search(word + r'(.*)', txt, re.I | re.S)
        if not m: return []
        return [int(x.replace(',', '')) for x in re.findall(r'(?<![\d.,])(\d{1,3}(?:,\d{3})+|\d{4,})(?![\d,])', m.group(1))]
    for lab, vals in t['rows']:
        L = norm(lab)
        if 'common stock' in L and 'issued' in L:
            n_ = [n for n in nums_after(lab, r'issued') if 10_000 < n < 200_000_000]
            if n_ and idx < len(n_): out['shares_issued'] = round(n_[idx] / 1e6, 6)
        if 'treasury stock' in L:
            n_ = [n for n in nums_after(lab, r'treasury stock') if 1_000 < n < 100_000_000]
            if n_ and idx < len(n_): out['shares_treasury'] = round(n_[idx] / 1e6, 6)
        if not vals or idx >= len(vals): continue
        v = round(vals[idx] / u, 6); raw.append([lab, v])
        if re.match(r'^total td group stockholders', L): out.setdefault('eq_td', v); continue
        if re.match(r'^total stockholders', L): out.setdefault('te', v); continue
        if re.match(r'^total liabilities,? (redeemable|and|& )', L) or re.match(r'^total liabilities and', L): out.setdefault('tle', v); continue
        for k, p in BS_MAP:
            if k in ('eq_td', 'te', 'tle'): continue
            if re.search(p, L):
                if k not in out: out[k] = v
                break
    if 'te' not in out and 'eq_td' in out: out['te'] = round(out['eq_td'] + out.get('nci', 0.0), 6)
    if 'eq_td' not in out and 'te' in out: out['eq_td'] = round(out['te'] - out.get('nci', 0.0), 6)
    out['lines_raw'] = raw
    return out

# ------------------------------------------------------------------ records
def rec_period(rel, filings, fy, q, annual):
    r = rel.get((fy, q))
    f = filings.get((fy, q))
    if not r and not f: return None
    mo = 12 if annual else 3
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q, 'sources': {}, 'notes': []}
    if r:
        rec['sources']['release'] = r['url']; rec['sources']['release_date'] = r['date']
        rec['is'] = ext_is(r['doc'], mo)
        ng = {}
        e = ext_ebitda(r['doc'], mo); a = ext_adjni(r['doc'], mo)
        if e: ng['ebitda'] = e
        if a: ng['adj'] = a
        ng.update(ext_narrative(r['doc']))
        rec['ngaap'] = ng
    if f:
        rec['sources']['filing'] = f['url']; rec['sources']['filing_date'] = f['date']; rec['period_end'] = f['report']
        d = f['doc']
        rec['is_filing'] = ext_is(d, mo)
        if not rec.get('is'): rec['is'] = rec['is_filing']; rec['notes'].append('Income statement from the 10-Q / 10-K (no release parsed).')
        rec['bs'] = ext_bs(d)
        rec['cf'] = ext_cf(d, 12 if annual else 3 * q)
        rec['seg'] = ext_seg(d, mo)
        og = ext_organic(d, mo)
        if og: rec['organic'] = og
        if not annual and q == 3:
            s9 = ext_seg(d, 9)
            if s9: rec['seg_9m'] = {k: v for k, v in s9.items() if k != 'em'}
            e9 = ext_em(d, 9) or (s9 or {}).get('em')
            if e9: rec['em_9m'] = e9
        em = ext_em(d, mo)
        if em: rec['em'] = em
        elif rec.get('seg') and rec['seg'].get('em'): rec['em'] = rec['seg'].pop('em')
    # prior-year comparative in the following year's release (restatement check)
    nxt = rel.get((fy + 1, q))
    if nxt:
        rec['py'] = {'release': nxt['url'], 'is': ext_is(nxt['doc'], mo, 'py'), 'ebitda': ext_ebitda(nxt['doc'], mo, 'py'), 'adj': ext_adjni(nxt['doc'], mo, 'py')}
    fn = filings.get((fy + 1, q))
    if fn:
        pseg = ext_seg(fn['doc'], mo, 'py')
        if pseg: rec['seg_py'] = pseg
        pem = ext_em(fn['doc'], mo, 'py')
        if pem: rec['em_py'] = pem
        elif pseg and pseg.get('em'): rec['em_py'] = rec['seg_py'].pop('em')
    if annual:
        fn2 = filings.get((fy + 2, 4))
        if fn2:
            pem2 = ext_em(fn2['doc'], 12, 'py2')
            if pem2: rec['em_py2'] = pem2
            pseg2 = ext_seg(fn2['doc'], 12, 'py2')
            if pseg2: pseg2.pop('em', None); rec['seg_py2'] = pseg2
    kind = 'FY' if annual or q == 4 else 'YTD'
    rec['x'] = {'sbc_ytd': xbrl.first_of(['ShareBasedCompensation', 'AllocatedShareBasedCompensationExpense'], fy, kind, 4 if annual else q),
                'deftax_ytd': xbrl.first_of(['DeferredIncomeTaxExpenseBenefit'], fy, kind, 4 if annual else q),
                'dep_ytd': xbrl.first_of(['Depreciation'], fy, kind, 4 if annual else q),
                'amort_ytd': xbrl.first_of(['AmortizationOfIntangibleAssets'], fy, kind, 4 if annual else q),
                'rev': xbrl.first_of(['Revenues', 'SalesRevenueNet', 'RevenueFromContractWithCustomerExcludingAssessedTax'], fy, 'FY' if annual else 'Q', 4 if annual else q),
                'ni': xbrl.first_of(['NetIncomeLoss', 'ProfitLoss'], fy, 'FY' if annual else 'Q', 4 if annual else q),
                'ta': xbrl.value('Assets', fy, 'I', 4 if annual else q),
                'sh_out': xbrl.first_of(['CommonStockSharesOutstanding'], fy, 'I', 4 if annual else q),
                'sh_issued': xbrl.value('CommonStockSharesIssued', fy, 'I', 4 if annual else q),
                'sh_treasury': xbrl.first_of(['TreasuryStockCommonShares', 'TreasuryStockShares'], fy, 'I', 4 if annual else q)}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings, others = build_indices()
    idx = [{'fy': fy, 'q': q, 'date': r['date'], 'url': r['url']} for (fy, q), r in sorted(rel.items())]
    json.dump(idx, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    json.dump([{'fy': fy, 'q': q, 'form': f['form'], 'date': f['date'], 'url': f['url'], 'report': f['report']} for (fy, q), f in sorted(filings.items())],
              open(os.path.join(OUT, '_filings.json'), 'w'), indent=1)
    n = 0
    for fy in range(2006, 2027):
        r = rec_period(rel, filings, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            r = rec_period(rel, filings, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
    xbrl.dump_subset()
    print(n, 'period files;', len(rel), 'releases;', len(filings), 'filings')
    missing_rel = [(fy, q) for fy in range(2006, 2027) for q in (1, 2, 3, 4) if (fy, q) not in rel and (fy, q) <= (2026, 4) and (fy >= 2013 or q == 4)]
    missing_fil = [(fy, q) for fy in range(2006, 2027) for q in (1, 2, 3, 4) if (fy, q) not in filings and (fy, q) <= (2026, 4) and (fy >= 2013 or q == 4)]
    print('missing releases:', missing_rel); print('missing filings:', missing_fil)

if __name__ == '__main__':
    main()
