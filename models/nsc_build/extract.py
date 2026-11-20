"""Per-period extraction from the Norfolk Southern EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2025 (fourth-quarter release, twelve-month column; 10-K market-group tables) and quarters Q1-13 - Q3-26
(that quarter's release three-month column; Q4 from the fourth-quarter release three-month column). Each record carries:
  is     consolidated statement of income (USD m; per share in $; shares in m): revenues by commodity group, expenses by classification
  bs     balance sheet at period end
  cf     cash flow, year to date (cf.ytd_months)
  mg     revenues / units / revenue per unit by market group (10-Q / 10-K MD&A tables; Q4 units = year - nine months, noted)
  kpi    coal tonnage by market, intermodal units by market, fuel surcharge revenue (10-Q / 10-K MD&A), where parsed
  ngaap  company non-GAAP reconciliation (press release), where published
  x      XBRL company facts (share-based compensation, deferred taxes, shares outstanding, dividends declared)
  py     prior-year comparative columns as presented in this period's release (restatement check)
  sources / notes
"""
import json, os, re, datetime as dt
import parse_release as P
import xbrl

S = os.environ.get('NSC_SRC', '/tmp/nsc_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '702165'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc
def dpath(o, doc): return os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{doc}")

def fyq_of_release(date):
    d = dt.date.fromisoformat(date)
    if d.month <= 2: return d.year - 1, 4
    if d.month <= 5: return d.year, 1
    if d.month <= 8: return d.year, 2
    return d.year, 3

_PARSED = {}
def parsed(path):
    if path not in _PARSED:
        _PARSED[path] = P.parse(open(path, 'rb').read()) if os.path.exists(path) else []
    return _PARSED[path]

def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings, press = {}, {}, {}
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            fy, q = fyq_of_release(o['date'])
            for doc in o['files']:
                if doc == o['primary'] or not doc.lower().endswith('.htm'): continue
                p = dpath(o, doc)
                tabs = parsed(p)
                types = {t['type'] for t in tabs}
                if {'is', 'bs'} <= types:
                    if (fy, q) not in rel: rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), path=p, tabs=tabs)
                elif os.path.exists(p):
                    press.setdefault((fy, q), []).append(dict(date=o['date'], url=url(o, doc), path=p))
        if o['form'] in ('10-Q', '10-K'):
            e = dt.date.fromisoformat(o['report'])
            q = {3: 1, 6: 2, 9: 3, 12: 4}[e.month]
            filings[(e.year, q)] = dict(date=o['date'], url=url(o, o['primary']), path=dpath(o, o['primary']), form=o['form'])
    return rel, filings, press

# ------------------------------------------------------------------ statements
IS_MAP = [('rev_coal', r'^coal'), ('rev_merch', r'^(general )?merchandise'), ('rev_im', r'^intermodal'),
          ('rev', r'^total railway operating revenues'),
          ('comp', r'^compensation and benefits'), ('psr', r'^purchased services and rents|^materials, services and rents'),
          ('conrail', r'^conrail rents'), ('fuel', r'^fuel|^diesel fuel'), ('dep', r'^depreciation'),
          ('mat', r'^materials and other'), ('claims', r'^casualties and other claims'), ('oth_opex', r'^other$'),
          ('merger', r'^merger[- ]related'), ('restr', r'^restructuring'), ('eoi', r'^eastern ohio'),
          ('opex', r'^total railway operating expenses'), ('oi', r'^income from railway operations'),
          ('oth_inc', r'^other income'), ('int', r'^interest expense on debt'), ('ebt', r'^income before income taxes'),
          ('loss_disp', r'^loss on asset disposal'),
          ('tax_cur', r'^current$'), ('tax_def', r'^deferred$'), ('tax', r'^total income tax|^income taxes$|^provision for income taxes$|^income tax expense$'),
          ('ni', r'^net income'),
          ('eps_d', r'^earnings per share\s*-\s*diluted|^diluted earnings per share'), ('eps_b', r'^earnings per share\s*-\s*basic|^basic earnings per share'),
          ('sh_d', r'^weighted average shares outstanding\s*-\s*diluted'), ('sh_b', r'^weighted average shares outstanding\s*-\s*basic')]

def ext_is(tabs, mo, cp):
    cands = [t for t in tabs if t['type'] == 'is' and any(c == (mo, cp) for c in t['cols'])]
    if not cands: return None
    t = cands[0]
    ci = next(i for i, c in enumerate(t['cols']) if c == (mo, cp))
    out, other, state = {}, [], 'pre'
    hdr = ' '.join(t['hdr']).lower() + ' ' + ' '.join(l.lower() for l, v in t['rows'] if not v)
    sh_thousands = "000's" in hdr or '(000' in hdr
    for lab, vals in t['rows']:
        L = P.norm_label(lab)
        if not vals:
            if L.startswith('earnings per share'): state = 'eps'
            elif L.startswith(('weighted average shares', 'average shares')): state = 'sh'
            elif L.startswith('railway operating expenses'): state = 'opex'
            elif L.startswith(('provision for income taxes', 'income tax expense', 'income taxes')): state = 'tax'
            continue
        if len(vals) > len(t['cols']): vals = vals[-len(t['cols']):]
        if ci >= len(vals): continue
        v = vals[ci]
        if state == 'eps' and L in ('basic', 'diluted'):
            out.setdefault('eps_' + L[0], v); continue
        if state == 'sh' and L in ('basic', 'diluted'):
            out.setdefault('sh_' + L[0], v); continue
        key = next((k for k, p in IS_MAP if re.search(p, L)), None)
        if key in ('tax_cur', 'tax_def') and state != 'tax': key = None
        if key and key not in out:
            out[key] = v
            if key == 'rev': state = 'opex'
            elif key == 'opex': state = 'post'
            elif key == 'tax': state = 'post'
        elif state == 'opex' and not key:
            other.append([lab, v])
    if sh_thousands or (out.get('sh_d') or 0) > 5000:
        for k in ('sh_b', 'sh_d'):
            if k in out: out[k] = round(out[k] / 1000.0, 3)
        out['shares_converted'] = 'thousands -> millions'
    out['other_lines'] = other
    return out

BS_MAP = [('cash', r'^cash and cash equivalents|^cash, cash equivalents'), ('sti', r'^short-term investments'),
          ('ar', r'^accounts receivable'), ('ms', r'^materials and supplies'), ('dta', r'^deferred income taxes'),
          ('oca', r'^other current assets'), ('tca', r'^total current assets'), ('inv', r'^investments'),
          ('ppe', r'^properties'), ('oa', r'^other assets'), ('ta', r'^total assets'),
          ('ap', r'^accounts payable'), ('std', r'^short-term debt'), ('taxes_pay', r'^income and other taxes'),
          ('ocl', r'^other current liabilities'), ('cmltd', r'^current maturities'), ('tcl', r'^total current liabilities'),
          ('ltd', r'^long-term debt'), ('ol', r'^other liabilities'), ('dtl', r'^deferred income taxes'), ('tl', r'^total liabilities$'),
          ('cs', r'^common stock'), ('apic', r'^additional paid-in capital'), ('urs', r'^unearned restricted stock'),
          ('aoci', r'^accumulated other comprehensive'), ('re', r'^retained income'), ('tsy', r'^less treasury stock'),
          ('teq', r"^total stockholders'? equity"), ('tle', r"^total liabilities and stockholders")]

def ext_bs(tabs, cp='cur'):
    t = next((t for t in tabs if t['type'] == 'bs'), None)
    if not t: return None
    ci = 0 if cp == 'cur' else 1
    out, raw, side, pend, pend_txt = {}, [], 'asset', None, ''
    for lab, vals in t['rows']:
        L = P.norm_label(lab)
        if not vals:
            if L.startswith('liabilities'): side = 'liab'
            if L.startswith('properties'): pend, pend_txt = 'ppe', lab
            elif L.startswith('common stock'): pend, pend_txt = 'cs', lab
            elif pend: pend_txt += ' ' + lab
            continue
        if len(vals) > 2: vals = vals[-2:]
        if ci >= len(vals): continue
        v = vals[ci]; raw.append([lab, v])
        hit = None
        for k, p in BS_MAP:
            if re.search(p, L):
                if k in ('dta', 'dtl'): k = 'dta' if side == 'asset' and 'tca' not in out else 'dtl'
                if k == 'ltd' and 'tcl' not in out: continue
                hit = k
                if k not in out: out[k] = v
                break
        if pend and (hit is None or L.startswith(('respectively', 'authorized', 'net of treasury'))):
            out.setdefault(pend, v); pend_txt += ' ' + lab
            if pend == 'cs':
                m = re.search(r'outstanding\s+([\d,]+)\s+and\s+([\d,]+)\s+shares', pend_txt)
                if m: out['shares_out'] = round(float(m.group(1 if cp == 'cur' else 2).replace(',', '')) / 1e6, 6)
        pend = None
        if hit == 'cs' or (hit is None and L.startswith('common stock')):
            m = re.search(r'outstanding\s+([\d,]+)\s+and\s+([\d,]+)\s+shares', lab)
            if m: out['shares_out'] = round(float(m.group(1 if cp == 'cur' else 2).replace(',', '')) / 1e6, 6)
        if 'ta' in out: side = 'liab'
    if 'cash' in out and 'sti' not in out and re.search(r'short-term investments', ' '.join(l.lower() for l, _ in raw if l.lower().startswith('cash'))):
        out['cash_incl_sti'] = True
    out['lines_raw'] = raw
    return out

CF_MAP = [('ni', r'^net income'), ('dep', r'^depreciation'), ('deftax', r'^deferred income taxes'),
          ('gains', r'^gains? (and losses )?on properties'), ('conrail_eq', r'^equity in earnings'),
          ('ar_chg', r'^accounts receivable'), ('ms_chg', r'^materials and supplies'), ('oca_chg', r'^other current assets'),
          ('cl_chg', r'^current liabilities other than debt'), ('oth_chg', r'^other - net|^other-net|^other – net'),
          ('cfo', r'^net cash provided by operating'),
          ('capex', r'^property additions'), ('acq', r'^acquisition'), ('prop_sales', r'^property sales'),
          ('inv_purch', r'^investments, including|^investment purchases'), ('inv_sales', r'^investment sales'),
          ('cfi', r'^net cash used (in|for) investing'),
          ('div', r'^dividends'), ('stock', r'^common stock'), ('bb', r'^purchase and retirement'),
          ('borrow', r'^proceeds from borrowings'), ('repay', r'^debt repayments'), ('cff', r'^net cash (provided by|used in|used for|provided by \(used in\)|used in \(provided by\)|\(used in\) provided by).*financing'),
          ('net', r'^net (increase|decrease|\(decrease\)|increase \(decrease\)|decrease \(increase\)).*cash'),
          ('beg', r'^at beginning'), ('end', r'^at end')]

def ext_cf(tabs, mo, cp):
    t = next((t for t in tabs if t['type'] == 'cf' and any(c == (mo, cp) for c in t['cols'])), None)
    if not t: return None
    ci = next(i for i, c in enumerate(t['cols']) if c == (mo, cp))
    out, raw, state = {'ytd_months': mo}, [], 'op'
    for lab, vals in t['rows']:
        L = P.norm_label(lab)
        if not vals:
            if 'investing' in L: state = 'inv'
            elif 'financing' in L: state = 'fin'
            continue
        if len(vals) > len(t['cols']): vals = vals[-len(t['cols']):]
        if ci >= len(vals): continue
        v = vals[ci]; raw.append([lab, v])
        if re.search(r'^interest|^income taxes', L) and 'end' in out: continue       # supplemental disclosures
        for k, p in CF_MAP:
            if re.search(p, L):
                if k == 'dep' and state != 'op': continue
                if k not in out: out[k] = v
                break
        if 'cfo' in out and state == 'op': state = 'inv'
        if 'cfi' in out and state == 'inv': state = 'fin'
    out['lines_raw'] = raw
    return out

def ext_is_10k(path, cp):
    """expense classification from a 10-K income statement (three-year columns); used for the FY2008 10-K recast of 2006-07."""
    if not path or not os.path.exists(path): return None
    for t in P.html_tables(open(path, 'rb').read()):
        labs = ' || '.join(l.lower() for l, _ in t['rows'])
        if 'compensation and benefits' not in labs or 'total railway operating expenses' not in labs: continue
        cols = P.columns(t)
        if not cols or (12, cp) not in cols: continue
        ci = cols.index((12, cp)); out = {}
        for lab, vals in t['rows']:
            if not vals or ci >= len(vals): continue
            L = P.norm_label(lab)
            key = next((k for k, p in IS_MAP if re.search(p, L)), None)
            if L.startswith('railway operating revenues'): key = 'rev'
            if key and key not in out: out[key] = vals[ci]
        if out.get('opex'): return out
    return None

# ------------------------------------------------------------------ market groups (10-Q / 10-K MD&A)
_HTML = {}
def html_of(path):
    if path not in _HTML: _HTML[path] = open(path, 'rb').read() if os.path.exists(path) else b''
    return _HTML[path]

def ext_mg(path, mo, cp='cur'):
    if not path or not os.path.exists(path): return None
    v = P.market_values(html_of(path), mo, cp)
    return v or None

def ext_kpi(path, mo, cp='cur'):
    if not path or not os.path.exists(path): return {}
    h = html_of(path); out = {}
    coal = P.simple_table(h, [r'^utility', r'^export', r'^total'], mo, cp)
    if coal: out['coal_tons'] = {k: v for k, v in coal.items() if k in ('utility', 'export', 'domestic metallurgical', 'industrial', 'total')}
    im = P.simple_table(h, [r'^domestic$', r'^international$', r'^total'], mo, cp)
    if im and im.get('domestic') and im.get('international') and (im.get('total') or 0) > 200:
        out['im_units'] = {k: v for k, v in im.items() if k in ('domestic', 'international', 'total')}
    opx = P.simple_table(h, [r'^purchased services$', r'^equipment rents', r'^total|^purchased services and rents'], mo, cp)
    if opx:
        keep = ('compensation and benefits', 'purchased services', 'equipment rents', 'fuel', 'depreciation', 'materials', 'claims', 'other', 'total',
                'purchased services and rents', 'materials and other', 'restructuring and other charges', 'eastern ohio incident', 'merger-related expenses',
                'total railway operating expenses')
        out['opex_detail'] = {k: v for k, v in opx.items() if k in keep}
    return out

def fuel_surcharge(path, fy, q):
    """fuel surcharge revenue quoted in the MD&A narrative ($m) for the current period, where the sentence pattern is recognised."""
    if not path or not os.path.exists(path): return None
    txt = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html_of(path).decode('utf-8', 'ignore')))
    txt = txt.replace('&#160;', ' ').replace('&nbsp;', ' ').replace('&#8217;', "'")
    pats = [r'[Ff]uel surcharge revenues? (?:totaled|was|were|of) \$\s*([\d,]+)\s*(million|billion)',
            r'[Rr]evenues associated with these surcharges totaled \$\s*([\d,]+)\s*(million|billion)',
            r'[Ff]uel surcharge revenues? (?:in|for) (?:the )?(?:first|second|third|fourth) quarter[^$]{0,80}\$\s*([\d,]+)\s*(million|billion)']
    for p in pats:
        m = re.search(p, txt)
        if m:
            v = float(m.group(1).replace(',', ''))
            return v * (1000 if m.group(2) == 'billion' else 1)
    return None

# ------------------------------------------------------------------ non-GAAP (press release)
def ext_ngaap(press_docs, mo, fy, q):
    """company reconciliation table in the press release -> {'adj_oi_pub', 'adj_or_pub', 'adj_eps_pub', 'adj_ni_pub', 'items': [...], 'text'}."""
    out = {}
    for d in press_docs or []:
        html = html_of(d['path'])
        txt = html.decode('utf-8', 'ignore').lower()
        if 'non-gaap' not in txt and 'adjusted' not in txt: continue
        for t in P.html_tables(html):
            labs = [P.norm_label(l) for l, v in t['rows'] if v]
            if not any(l.startswith('adjusted') for l in labs): continue
            h = ' | '.join(t['hdr']).lower()
            # pick the column for this period: first numeric column of a single-period table (2023+ layout: one quarter per table),
            # or the column whose header names the quarter / year
            n = max(len(v) for _, v in t['rows'] if v)
            ci = 0
            if n >= 2:
                hdrs = re.findall(r'(fourth[- ]quarter|first[- ]quarter|second[- ]quarter|third[- ]quarter|year[- ]ended|full year|twelve months|year)', h)
                want = 'year' if mo == 12 else {1: 'first', 2: 'second', 3: 'third', 4: 'fourth'}[q]
                idx = [i for i, x in enumerate(hdrs) if x.startswith(want)]
                if idx: ci = idx[0]
                elif mo == 12 and n >= 2: ci = n - 1
            period_ok = (str(fy) in h) or ('20' not in h)
            if not period_ok: continue
            has_year = re.search(r'year|twelve|full', h) is not None
            has_qtr = re.search(r'quarter', h) is not None
            if mo == 12 and has_qtr and not has_year: continue
            if mo == 3 and not has_qtr: continue                      # a plain-year header is a full-year reconciliation
            items = []
            start_lab = None
            for lab, vals in t['rows']:
                if not vals or ci >= len(vals): continue
                L = P.norm_label(lab); v = vals[ci]
                if L.startswith('adjusted income from railway') or L.startswith('adjusted railway operating income'): out['adj_oi_pub'] = v
                elif L.startswith('adjusted operating ratio') or L.startswith('adjusted railway operating ratio'): out['adj_or_pub'] = v
                elif L.startswith('adjusted diluted earnings per share') or L.startswith('adjusted earnings per share'): out['adj_eps_pub'] = v
                elif L.startswith('adjusted net income'): out['adj_ni_pub'] = v
                elif L.startswith('adjusted railway operating expenses'): out['adj_opex_pub'] = v
                elif L.startswith('less: fuel surcharge') or L.startswith('fuel surcharge revenue'): out['fsc_pub'] = abs(v)
                elif L.startswith('railway operating revenues less fuel'): out['rev_xfsc_pub'] = v
                elif L.startswith(('income from railway operations', 'operating ratio', 'diluted earnings per share', 'net income', 'railway operating expenses', 'railway operating ratio')):
                    if L.startswith('income from railway operations') and 'adj_oi_pub' in out: break    # prior-year block follows in the same table
                    start_lab = L
                else:
                    items.append({'after': start_lab, 'label': lab, 'value': v})
            if any(k in out for k in ('adj_oi_pub', 'adj_eps_pub', 'adj_ni_pub', 'adj_or_pub')):
                out['items'] = items; out['source'] = d['url']
                return out
            out = {}
    return out or None

# ------------------------------------------------------------------ records
def rec_period(rel, filings, press, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    tabs = r['tabs']
    mo = 12 if annual else 3
    key = str(fy) if annual else f'Q{q}-{str(fy)[2:]}'
    rec = {'period': key, 'fy': fy, 'q': None if annual else q, 'sources': {'release': r['url'], 'release_date': r['date']}, 'notes': []}
    rec['is'] = ext_is(tabs, mo, 'cur')
    if rec['is'] is None and not annual and q == 4:
        rec['notes'].append('No three-month column in the fourth-quarter release statements; quarter derived later as year - nine months.')
    ytd = 12 if annual else 3 * q
    rec['cf'] = ext_cf(tabs, ytd, 'cur')
    rec['bs'] = ext_bs(tabs, 'cur')
    rec['py'] = {'is': ext_is(tabs, mo, 'py'), 'cf': ext_cf(tabs, ytd, 'py')}
    if annual and fy in (2006, 2007):
        f08 = filings.get((2008, 4))
        if f08:
            rec['is_recast'] = ext_is_10k(f08['path'], 'py2' if fy == 2006 else 'py')
            rec['sources']['recast_10k'] = f08['url']
            rec['notes'].append('Operating-expense classification recast per the FY2008 10-K (five classifications used from 2008); totals as originally reported.')
    f = filings.get((fy, 4 if annual else q))
    if f:
        rec['sources']['filing'] = f['url']
        if annual or q == 4:
            rec['mg'] = ext_mg(f['path'], 12)
            rec['kpi'] = ext_kpi(f['path'], 12)
            rec['fsc'] = fuel_surcharge(f['path'], fy, q)
            if not annual:
                f9 = filings.get((fy, 3))
                m9 = ext_mg(f9['path'], 9) if f9 else None
                k9 = ext_kpi(f9['path'], 9) if f9 else {}
                if rec['mg'] and m9:
                    rec['mg'] = {meas: {g: round(v - m9[meas][g], 3) for g, v in d.items() if g in m9.get(meas, {})} for meas, d in rec['mg'].items() if meas != 'rpu'}
                    rec['notes'].append('Market-group revenues and units: Q4 = year (10-K) less nine months (Q3 10-Q); revenue per unit derived.')
                else: rec['mg'] = None
                rec['kpi'] = {k: {g: round(v - k9[k][g], 3) for g, v in d.items() if g in k9.get(k, {})} for k, d in rec['kpi'].items() if k in k9} if k9 else {}
                rec['fsc'] = None
        else:
            rec['mg'] = ext_mg(f['path'], 3)
            rec['kpi'] = ext_kpi(f['path'], 3)
            rec['fsc'] = fuel_surcharge(f['path'], fy, q)
            if q == 3:
                rec['mg_9m'] = ext_mg(f['path'], 9); rec['kpi_9m'] = ext_kpi(f['path'], 9)
    ng = ext_ngaap(press.get((fy, q)), mo, fy, q)
    if ng: rec['ngaap'] = ng
    rec['sources']['press'] = [d['url'] for d in press.get((fy, q), [])]
    kind = 'FY' if annual else 'YTD'
    qq = 4 if annual else q
    rec['x'] = {'sbc_ytd': xbrl.first_of(['AllocatedShareBasedCompensationExpense', 'ShareBasedCompensation'], fy, kind, qq),
                'deftax_ytd': xbrl.first_of(['DeferredIncomeTaxExpenseBenefit'], fy, kind, qq),
                'sh_out': xbrl.first_of(['CommonStockSharesOutstanding'], fy, 'I', qq),
                'dps_q': xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY' if annual else 'Q', qq),
                'div_paid_ytd': xbrl.first_of(['PaymentsOfDividendsCommonStock', 'PaymentsOfDividends'], fy, kind, qq),
                'oi_xb': xbrl.value('OperatingIncomeLoss', fy, 'FY' if annual else 'Q', qq),
                'sh_b_xb': xbrl.value('WeightedAverageNumberOfSharesOutstandingBasic', fy, 'FY' if annual else 'Q', qq),
                'eps_b_xb': xbrl.value('EarningsPerShareBasic', fy, 'FY' if annual else 'Q', qq),
                'ni_xb': xbrl.first_of(['NetIncomeLoss', 'ProfitLoss'], fy, 'FY' if annual else 'Q', qq)}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings, press = release_index()
    json.dump([{'fy': k[0], 'q': k[1], 'date': v['date'], 'url': v['url']} for k, v in sorted(rel.items())], open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    n = 0
    for fy in range(2006, 2026):
        r = rec_period(rel, filings, press, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
        else: print('missing annual', fy)
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if fy == 2026 and q == 4: break
            r = rec_period(rel, filings, press, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
            else: print('missing', fy, q)
    xbrl.dump_subset()
    print(n, 'period files')

if __name__ == '__main__':
    main()
