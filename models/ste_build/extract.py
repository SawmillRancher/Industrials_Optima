"""Extract STERIS (STE) historical data from SEC EDGAR earnings releases (8-K Item 2.02, Ex. 99.1) into data/<period>.json.

Each release is read for its current period and its comparative columns:
  IS   consolidated statement of income / operations        SEG  segment revenues, segment operating income, adjustments
  SUP  supplemental revenue by type (capital / consumables / service, company and segment)
  NG   Non-GAAP reconciliations (adjusted gross profit, adjusted operating income, adjusted net income, adjusted EPS) and
       the organic / constant-currency revenue-growth bridge
  CF   condensed cash flow (year to date)                    BS   condensed balance sheet
Period keys: '2012'..'2026' = fiscal years ended 31 March; 'Q1-22' = quarter ended 30-Jun-2021 (FY2022 Q1); 'H1-22', '9M-22'.
Records are stored per (period, source document); normalize.py chooses which document wins for each period (own release =
as originally reported; Dental discontinued-operations restatements from the Q4 FY24 / FY25 releases for FY2023-24).
"""
import json, os, re, glob
from parse_release import sections, units, matrix_tables, pnum

SRC = os.environ.get('STE_SRC', '/tmp/ste_src')
TXT, DOCS = os.path.join(SRC, 'txt'), os.path.join(SRC, 'docs')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
FILINGS = json.load(open(os.path.join(SRC, 'filings.json'))) if os.path.exists(os.path.join(SRC, 'filings.json')) else []
EDGAR = 'https://www.sec.gov/Archives/edgar/data/'

def qk(fy, q): return f'Q{q}-{str(fy)[2:]}'
def ytdk(fy, q): return {1: qk(fy, 1), 2: f'H1-{str(fy)[2:]}', 3: f'9M-{str(fy)[2:]}', 4: str(fy)}[q]

def rel_period(date):
    y, m = int(date[:4]), int(date[5:7])
    if m in (4, 5, 6): return y, 4
    if m in (7, 8, 9): return y + 1, 1
    if m in (10, 11, 12): return y + 1, 2
    return y, 3

def releases():
    out = []
    for o in FILINGS:
        if o['form'] != '8-K' or o['acc'] == '0001140361-21-014412': continue   # 27-Apr-2021 = preliminary FY21 (pre-Cantel vote)
        ex = [x for x in o['files'] if re.search(r'ex-?99-?\.?1', x.lower())]
        if not ex: continue
        base = f"{o['date']}_8-K_{o['acc']}_{ex[0]}"
        fy, q = rel_period(o['date'])
        out.append(dict(date=o['date'], fy=fy, q=q, txt=os.path.join(TXT, base.rsplit('.', 1)[0] + '.txt'), htm=os.path.join(DOCS, base),
                        url=f"{EDGAR}{o['cik']}/{o['acc'].replace('-', '')}/{ex[0]}"))
    return out

# ---------------------------------------------------------------- column maps
def is_cols(fy, q, n):
    c = [qk(fy, q), qk(fy - 1, q)]
    if q > 1: c += [ytdk(fy, q), ytdk(fy - 1, q)]
    return c[:n]

def find(rows, pats, excl=None, nth=0):
    """values of the nth row matching the first pattern (in priority order) that matches any row."""
    for p in pats:
        hits = [vals for lab, vals, ctx in rows if re.search(p, lab, re.I) and not (excl and re.search(excl, lab, re.I))]
        if len(hits) > nth: return hits[nth]
    return None

REC = {}      # period -> source -> section -> {key: value}
def put(per, src, sec, key, v):
    if v is None or v == 'X': return
    d = REC.setdefault(per, {}).setdefault(src, {}).setdefault(sec, {})
    d.setdefault(key, v)

# ---------------------------------------------------------------- income statement
IS_MAP = [('rev', [r'^Revenues, net$', r'^(Total )?revenues$']), ('gp', [r'^Gross profit$']), ('sga', [r'^Selling, general,? and administrative']),
          ('rd', [r'^Research and development']), ('restr', [r'^Restructuring expense']), ('opex', [r'^Total operating expenses']),
          ('op', [r'^Income from operations']), ('int_exp', [r'^Interest expense']), ('int_inc', [r'^Interest (and miscellaneous )?income']),
          ('nonop', [r'^(Total )?non-operating expense']),
          ('ebt', [r'^Income (from continuing operations )?before income tax']), ('tax', [r'^Income tax(es)? (\(\w+\) )?(expense|benefit)']),
          ('ni_cont', [r'^Income from continuing operations, net of income tax']), ('disc', [r'from discontinued operations, net of income tax']),
          ('ni', [r'^Net (income|\(loss\) income|income \(loss\))$']), ('nci', [r'attributable to noncontrolling']),
          ('ni_attr', [r'^Net (income|\(loss\) income|income \(loss\)) attributable to shareholders']),
          ('ni_cont_attr', [r'^Net income from continuing operations attributable']),
          ('dps', [r'^Cash dividends declared']), ('sh_b', [r'^Basic number of']), ('sh_d', [r'^Diluted number of'])]
PS = {'dps', 'eps_b', 'eps_d', 'eps_d_cont', 'eps_b_cont'}

def scale(key, v, u):
    if v is None: return None
    if key in PS or key.startswith('eps') or key.endswith('_pct') or key.startswith('g_'): return v
    return round(v / 1000.0, 6) if u == 'k' else v

def do_is(rel, sec, u, src):
    rows = sec.get('IS', [])
    if not rows: return
    n = len(find(rows, [r'^Gross profit$']) or [])
    cols = is_cols(rel['fy'], rel['q'], n)
    for key, pats in IS_MAP:
        v = find(rows, pats, excl=r'attributable' if key == 'ni' else (r'held for sale' if key == 'rev' else None))
        if v is None: continue
        for p, x in zip(cols, v): put(p, src, 'is', key, scale(key, x, u))
    # interest expense: first match is in the non-operating block
    # EPS: modern = 'Continuing Operations' / 'Total' rows under Basic / Diluted headers; old = 'Basic' / 'Diluted' rows
    cont = [v for lab, v, c in rows if re.match(r'^Continuing Operations$', lab, re.I)]
    tot = [v for lab, v, c in rows if re.match(r'^Total$', lab, re.I)]
    b = find(rows, [r'^Basic$']); d = find(rows, [r'^Diluted$'])
    if len(cont) >= 2:
        for p, x, y in zip(cols, cont[0], cont[1]): put(p, src, 'is', 'eps_b_cont', x); put(p, src, 'is', 'eps_d_cont', y)
        if len(tot) >= 2:
            for p, x, y in zip(cols, tot[0], tot[1]): put(p, src, 'is', 'eps_b', x); put(p, src, 'is', 'eps_d', y)
    elif b and d:
        for p, x, y in zip(cols, b, d):
            put(p, src, 'is', 'eps_b', x); put(p, src, 'is', 'eps_d', y); put(p, src, 'is', 'eps_d_cont', y); put(p, src, 'is', 'eps_b_cont', x)

# ---------------------------------------------------------------- segments
SEGN = [('hcp', r'^Healthcare Products$'), ('hss', r'^Healthcare Specialty Services$'), ('hc', r'^Healthcare, net$'), ('hc', r'^Healthcare$'),
        ('ls', r'^Life Sciences$'), ('ast', r'^(AST|Applied Sterilization Technologies|STERIS Isomedix Services|Isomedix|Isomedix Services)$'),
        ('dental', r'^Dental$'), ('corp', r'^Corporate( and Other)?$')]
ADJ = [('amort', r'amortization (and impairment )?of (acquired|purchased) intangible'), ('stepup', r'step.{0,8}(up|down)'),
       ('taxrestr', r'tax restructuring|redomiciliation'), ('restr', r'restructuring'), ('acq', r'acquisition|integration|transaction'),
       ('divest', r'divestiture|sale of business'), ('impair', r'goodwill impairment'),
       ('litig', r'litigation|settlement|class action|SYSTEM 1|rebate'), ('covid', r'covid'), ('other', r'.')]
def adj_cat(lab):
    lab = lab.lower()
    if 'contingent consideration' in lab: return 'acq'
    if 'settlement of pension' in lab: return 'other'
    for k, p in ADJ:
        if re.search(p, lab, re.I): return k
    return 'other'

def do_seg(rel, sec, u, src):
    rows = sec.get('SEG', [])
    if not rows: return
    phase = 'rev'
    n = max(len(v) for _, v, _ in rows)
    cols = is_cols(rel['fy'], rel['q'], n)
    for lab, vals, ctx in rows:
        if len(vals) != len(cols): continue
        l = lab.strip()
        if re.match(r'^Total (Segment )?revenues', l, re.I) or re.match(r'^Total Reportable Segments', l, re.I) and phase == 'rev':
            if re.match(r'^Total (Segment )?revenues', l, re.I):
                for p, x in zip(cols, vals): put(p, src, 'seg', 'rev_tot', scale('x', x, u))
                phase = 'oi'
            continue
        if re.match(r'^Total (income|operating income|segment operating income|reportable)', l, re.I) and phase == 'oi':
            if re.search(r'before adjustments|segment operating income', l, re.I):
                for p, x in zip(cols, vals): put(p, src, 'seg', 'oi_tot_bef', scale('x', x, u))
            phase = 'adj' if re.search(r'before adjustments|segment operating income', l, re.I) else 'oi'
            continue
        if re.match(r'^(Total )?(Operating Income|Income from operations)', l, re.I) and phase in ('oi', 'adj'):
            for p, x in zip(cols, vals): put(p, src, 'seg', 'op', scale('x', x, u))
            phase = 'done'; continue
        if phase == 'adj':
            k = adj_cat(l)
            for p, x in zip(cols, vals):
                d = REC.setdefault(p, {}).setdefault(src, {}).setdefault('segadj', {})
                d[k] = round(d.get(k, 0.0) + scale('x', x, u), 6)
            continue
        if re.match(r'^Healthcare, net$', l, re.I):          # FY2012-13: Healthcare revenue net of the SYSTEM 1 rebate program
            for p, x in zip(cols, vals): REC.setdefault(p, {}).setdefault(src, {}).setdefault('seg', {})[f'{phase}_hc'] = scale('x', x, u)
            continue
        for k, pat in SEGN:
            if re.match(pat, l, re.I):
                for p, x in zip(cols, vals): put(p, src, 'seg', f'{phase}_{k}', scale('x', x, u))
                break

# ---------------------------------------------------------------- supplemental revenue by type
TYPES = [('cap', r'^Capital( Equipment)?$'), ('cons', r'^Consumables$'), ('serv', r'^Service$')]
SEGT = [('hcp', r'Healthcare Products'), ('hss', r'Healthcare Specialty'), ('hc', r'Healthcare'), ('ls', r'Life Sciences'),
        ('ast', r'AST|Applied Sterilization|Isomedix'), ('dental', r'Dental')]

def sup_cols(rel, ctx, n):
    """map SUP columns: header lines like 'FY 2025 | FY 2024 | FY 2025 | FY 2024' + 'Q4 | Q4 | YTD | YTD'."""
    fys, kinds = None, None
    for c in ctx:
        cells = [x.strip() for x in c.split('|')]
        f = [re.search(r'(?:FY|Fiscal)\s*(\d{4})', x) for x in cells]
        if sum(1 for m in f if m) >= 2: fys = [int(m.group(1)) for m in f if m]
        k = [x for x in cells if re.fullmatch(r'Q[1-4]|YTD', x)]
        if len(k) >= 2: kinds = k
    if not fys or not kinds or len(fys) != len(kinds): return None
    out = []
    for fy, k in zip(fys, kinds):
        out.append(qk(fy, int(k[1])) if k.startswith('Q') else ytdk(fy, rel['q']))
    return out[:n]

def do_sup(rel, sec, u, src):
    rows = sec.get('SUP', [])
    pend, seen_total = {}, False
    for lab, vals, ctx in rows:
        cols = sup_cols(rel, ctx, len(vals))
        if not cols: continue
        l = lab.strip()
        if re.search(r'^Adjusted', l, re.I) or re.search(r'Ireland|United States|International|Backlog|Tax Rate|Free Cash|Net Debt|%', l, re.I):
            continue
        hit = None
        for k, p in TYPES:
            if re.match(p, l, re.I): hit = k; break
        if hit:
            pend[hit] = vals; continue
        m = re.match(r'^Total (.*?)\s*Revenues', l, re.I)
        if m:
            name = m.group(1)
            seg = None
            if name == '' or re.match(r'^Company', name, re.I): seg = 'co'
            else:
                for k, p in SEGT:
                    if re.search(p, name, re.I): seg = k; break
            if seg:
                for t, v in pend.items():
                    for p, x in zip(cols, v): put(p, src, 'sup', f'{seg}_{t}', scale('x', x, u))
                for p, x in zip(cols, vals): put(p, src, 'sup', f'{seg}_tot', scale('x', x, u))
            pend = {}
            continue
        if re.match(r'^(Revenues|Total Recurring)$', l, re.I) or re.match(r'^\d', l):
            if l.lower() == 'revenues' and not pend:
                # single-line segment revenue (Isomedix / AST, Corporate and Other): assigned at the following Operating Income row
                pend['_single'] = vals
            continue
        if re.match(r'^(Segment )?Operating Income', l, re.I):
            pend = {}

# ---------------------------------------------------------------- cash flow (year to date) & balance sheet
CF_MAP = [('cf_ni', [r'^Net (\(loss\) )?income( \(loss\))?$']), ('cf_noncash', [r'^Non-cash items']), ('cf_cfo', [r'^Net cash provided by operating']),
          ('cf_capex', [r'^Purchases of property']), ('cf_ppesale', [r'^Proceeds from (the )?sale of property']),
          ('cf_acq', [r'^(Acquisition of businesses|Investments? in businesses|Acquisitions of businesses)']),
          ('cf_divest', [r'^Proceeds from (the )?sale of business']), ('cf_cfi', [r'^Net cash .{0,40}investing']),
          ('cf_bb', [r'^Repurchases? of (ordinary|common)']), ('cf_div', [r'^Cash dividends paid']),
          ('cf_cff', [r'^Net cash .{0,40}financing']), ('cf_fx', [r'^Effect of exchange']),
          ('cf_beg', [r'beginning of (period|year)']), ('cf_end', [r'end of (period|year)'])]
BS_MAP = [('cash', [r'^Cash and cash equivalents']), ('ar', [r'^Accounts receivable']), ('inv', [r'^Inventories']),
          ('tca', [r'^Total current assets']), ('ppe', [r'^Property, plant,? and equipment']), ('rou', [r'^Lease right-of-use']),
          ('gwi', [r'^Goodwill and intangible']), ('gw', [r'^Goodwill$']), ('intang', [r'^Intangibles?, net', r'^Intangible assets, net']),
          ('ta', [r'^Total assets']), ('ap', [r'^Accounts payable']), ('std', [r'^(Short-term indebtedness|Current portion of long-term)']),
          ('tcl', [r'^Total current liabilities']), ('ltd', [r'^Long-term (indebtedness|debt)']), ('ol', [r'^Other liabilities']),
          ('teq', [r'^Total equity', r'^Equity$']), ('tle', [r'^Total liabilities and equity'])]

def do_cf(rel, sec, u, src):
    rows = sec.get('CF', [])
    if not rows: return
    fy, q = rel['fy'], rel['q']
    cols = [ytdk(fy, q), ytdk(fy - 1, q)]
    for key, pats in CF_MAP:
        v = find(rows, pats, excl=r'attributable')
        if v is None: continue
        for p, x in zip(cols, v): put(p, src, 'cf', key, scale('x', x, u))
    f = find(sec.get('FCF', []), [r'^Free Cash Flow$'])
    if f:
        for p, x in zip(cols, f): put(p, src, 'cf', 'fcf_pub', scale('x', x, u))

def do_bs(rel, sec, u, src):
    rows = sec.get('BS', [])
    if not rows: return
    fy, q = rel['fy'], rel['q']
    cols = [qk(fy, q) if q < 4 else str(fy), str(fy - 1)]
    for key, pats in BS_MAP:
        v = find(rows, pats)
        if v is None: continue
        for p, x in zip(cols, v): put(p, src, 'bs', key, scale('x', x, u))

# ---------------------------------------------------------------- Non-GAAP
MKEY = {'gp': 'adj_gp', 'op': 'adj_op', 'ni_cont': 'adj_ni_cont', 'ni_attr': 'adj_ni_attr', 'eps_cont': 'adj_eps_cont', 'eps': 'adj_eps', 'disc': 'adj_disc'}

def mat_cols(rel, period):
    fy, q = rel['fy'], rel['q']
    m = re.search(r'(Three|Six|Nine|Twelve) months ended (\w+)', period, re.I)
    if not m: return None
    n = {'three': 1, 'six': 2, 'nine': 3, 'twelve': 4}[m.group(1).lower()]
    mon = m.group(2).lower()[:3]
    qe = {'jun': 1, 'sep': 2, 'dec': 3, 'mar': 4}[mon]
    if n == 1: return [qk(fy, qe) if qe <= q else qk(fy - 1, qe), None]
    return [ytdk(fy, q), ytdk(fy - 1, q)]

def do_matrix(rel, src, u):
    if not os.path.exists(rel['htm']): return
    blocks = matrix_tables(open(rel['htm'], 'rb').read())
    fy, q = rel['fy'], rel['q']
    for i, b in enumerate(blocks):
        cols = mat_cols(rel, b['period'])
        if not cols: continue
        if cols[1] is None:
            p0 = cols[0]
            y = int('20' + p0[-2:]); qq = int(p0[1])
            cols = [p0, qk(y - 1, qq)]
        s = src if i < (2 if q > 1 else 1) else src + '#recast'
        for lab, vals in b['rows']:
            l = lab.strip()
            if re.match(r'^(As reported|GAAP)', l, re.I):
                for (mk, j), v in vals.items(): put(cols[j], s, 'ngm', 'gaap_' + mk, scale('eps' if 'eps' in mk else 'x', v, u))
            elif re.match(r'^Adjusted$', l, re.I):
                for (mk, j), v in vals.items(): put(cols[j], s, 'ngm', MKEY.get(mk, 'adj_' + mk), scale('eps' if 'eps' in mk else 'x', v, u))
            elif re.match(r'^Net impact of adjustments after tax', l, re.I):
                for (mk, j), v in vals.items(): put(cols[j], s, 'ngm', 'aftertax_' + mk, scale('x', v, u))
            elif re.match(r'^Net EPS impact', l, re.I):
                for (mk, j), v in vals.items(): put(cols[j], s, 'ngm', 'epsimpact_' + mk, v)
            elif re.match(r'^\d{4}$', l): continue
            else:
                k = adj_cat(l)
                for (mk, j), v in vals.items():
                    if mk in ('gp', 'op') or (mk in ('ni_cont', 'ni_attr') and not any(m2 == 'op' for (m2, _) in vals)):
                        tgt = {'gp': 'gpadj', 'op': 'opadj'}.get(mk, 'niadj')
                        if tgt == 'niadj' and mk == 'ni_attr' and any(m2 == 'ni_cont' for (m2, _) in vals): continue
                        d = REC.setdefault(cols[j], {}).setdefault(s, {}).setdefault(tgt, {})
                        d[k] = round(d.get(k, 0.0) + scale('x', v, u), 6)
                        d.setdefault('_labels', [])
                        if l[:60] not in d['_labels']: d['_labels'].append(l[:60])

def do_ng_vertical(rel, sec, u, src):
    """FY2012-FY2015 releases: vertical blocks (Gross Profit ... Adjusted gross profit; Operating income ... Adjusted operating income;
    Net income ... Adjusted net income; Net Income per diluted share ... Adjusted net income per diluted share)."""
    rows = sec.get('NG', [])
    if not rows: return
    starts = {'gp': r'^Gross profit$', 'op': r'^Operating income$', 'ni': r'^Net income$', 'eps': r'^Net income per diluted share$'}
    ends = {'gp': r'^Adjusted gross profit$', 'op': r'^Adjusted operating income$', 'ni': r'^Adjusted net income$', 'eps': r'^Adjusted net income per diluted share$'}
    cur = None
    for lab, vals, ctx in rows:
        l = lab.strip()
        n = len(vals)
        if n not in (2, 4): continue
        cols = is_cols(rel['fy'], rel['q'], n)
        hit = [k for k, p in starts.items() if re.match(p, l, re.I)]
        if hit and cur is None:
            cur = hit[0]
            for p, x in zip(cols, vals): put(p, src, 'ngv', f'gaap_{cur}', scale('eps' if cur == 'eps' else 'x', x, u))
            continue
        if cur and re.match(ends[cur], l, re.I):
            for p, x in zip(cols, vals): put(p, src, 'ngv', f'adj_{cur}', scale('eps' if cur == 'eps' else 'x', x, u))
            cur = None; continue
        m = re.match(r'^Adjusted (Healthcare|Life Sciences|Isomedix|STERIS Isomedix Services|Applied Sterilization Technologies|AST) operating income', l, re.I)
        if m and n:
            seg = {'healthcare': 'hc', 'life sciences': 'ls'}.get(m.group(1).lower(), 'ast')
            for p, x in zip(cols, vals): put(p, src, 'ngv', f'adjseg_{seg}', scale('x', x, u))
            continue
        if cur in ('gp', 'op', 'ni'):
            k = adj_cat(l)
            tgt = {'gp': 'gpadj', 'op': 'opadj', 'ni': 'niadj_at'}[cur]
            for p, x in zip(cols, vals):
                d = REC.setdefault(p, {}).setdefault(src, {}).setdefault(tgt, {})
                d[k] = round(d.get(k, 0.0) + scale('x', x, u), 6)

def do_organic(rel, sec, u, src):
    """Organic / constant-currency revenue bridge table (FY2016+): label | rev cur | rev prior | acquisitions | divestitures | FX |
    GAAP growth % | organic % | constant-currency organic %."""
    rows = sec.get('NG', []) + sec.get('FCF', [])
    blocks, cur = [], None
    for lab, vals, ctx in rows:
        if len(vals) != 8: continue
        l = lab.strip()
        if re.match(r'^Segment revenues', l, re.I) or 'Discontinued' in l or l.startswith('Total Company'): continue
        if re.match(r'^Total - Continuing Operations$', l, re.I): l = 'Total'
        if cur is None or (blocks and l == 'Total' and 'Total' in cur): cur = {}; blocks.append(cur)
        cur[l] = vals
        if l == 'Total': cur['Total'] = vals; cur = None
    fy, q = rel['fy'], rel['q']
    pers = [qk(fy, q)] + ([ytdk(fy, q)] if q > 1 else [])
    for p, b in zip(pers, blocks):
        for lab, v in b.items():
            seg = 'tot' if lab == 'Total' else next((k for k, pat in SEGN if re.match(pat, lab.split(' - ')[0], re.I)), None)
            if 'Discontinued' in lab: seg = 'disc_' + (seg or 'x')
            if not seg: continue
            put(p, src, 'org', f'{seg}_rev', scale('x', v[0], u)); put(p, src, 'org', f'{seg}_rev_py', scale('x', v[1], u))
            put(p, src, 'org', f'{seg}_acq', scale('x', v[2], u)); put(p, src, 'org', f'{seg}_div', scale('x', v[3], u))
            put(p, src, 'org', f'{seg}_fx', scale('x', v[4], u)); pc = lambda x: None if x is None else round(x / 100, 6)
            put(p, src, 'org', f'{seg}_g', pc(v[5])); put(p, src, 'org', f'{seg}_og', pc(v[6])); put(p, src, 'org', f'{seg}_ccog', pc(v[7]))

def do_recast24(rel, sec, u, src):
    """Q4 FY2024 release: 'Quarterly as reported, U.S. GAAP Results' and 'Adjusted Quarterly Results' recast for Dental
    (continuing operations), fiscal 2024 and 2023: columns Full Year | Q4 | Q3 | Q2 | Q1."""
    txt = open(rel['txt']).read()
    for title, tag in (('Quarterly as reported, U.S. GAAP Results', 'gaap'), ('Adjusted Quarterly Results', 'adj')):
        i = txt.find(title)
        if i < 0: continue
        j = txt.find('Adjusted Quarterly Results', i + 10) if tag == 'gaap' else -1
        block = txt[i:j if j > 0 else i + 6000]
        fy = None
        for line in block.splitlines()[1:]:
            m = re.match(r'^Fiscal (\d{4})', line.strip())
            if m: fy = int(m.group(1)); continue
            if fy is None or '|' not in line: continue
            cells = [c.strip() for c in line.split('|')]
            if len(cells) != 6: continue
            lab = cells[0]; vals = [pnum(c) for c in cells[1:]]
            if 'X' in vals: continue
            key = {'Revenues': 'rev', 'Cost of revenues': 'cogs', 'Gross profit': 'gp', 'Income tax expense': 'tax',
                   'Net income (loss)': 'ni', 'Net income': 'ni', 'Continuing operations': 'eps_d_cont', 'Discontinued operations': 'eps_d_disc',
                   'Total': 'eps_d'}.get(lab)
            if lab.startswith('Income from continuing operations before'): key = 'ebt'
            elif lab.startswith('Income from continuing operations, net'): key = 'ni_cont'
            elif 'discontinued operations, net' in lab: key = 'disc'
            elif lab.startswith('Net income (loss) attributable') or lab.startswith('Net income attributable'): key = 'ni_attr'
            if not key: continue
            for p, v in zip([str(fy), qk(fy, 4), qk(fy, 3), qk(fy, 2), qk(fy, 1)], vals):
                put(p, src + '#recast', 'rc_' + tag, key, scale('eps' if key.startswith('eps') else 'x', v, u))

def run():
    for rel in releases():
        txt = open(rel['txt']).read()
        u = units(txt)
        sec = sections(txt)
        src = rel['date']
        REC.setdefault('_src', {})[src] = rel['url']
        do_is(rel, sec, u, src); do_seg(rel, sec, u, src); do_sup(rel, sec, u, src); do_cf(rel, sec, u, src); do_bs(rel, sec, u, src)
        if rel['date'] < '2016-01-01': do_ng_vertical(rel, sec, u, src)
        else: do_matrix(rel, src, u)
        do_organic(rel, sec, u, src)
        if rel['date'] == '2024-05-08': do_recast24(rel, sec, u, src)
    os.makedirs(OUT, exist_ok=True)
    import xbrl; xbrl.dump_subset()
    json.dump([{'date': r['date'], 'fy': r['fy'], 'q': r['q'], 'url': r['url']} for r in releases()],
              open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    for p, d in REC.items():
        json.dump(d, open(os.path.join(OUT, f'{p}.json'), 'w'), indent=1, sort_keys=True)
    return REC

if __name__ == '__main__':
    run()
    print(len(REC), 'periods')
