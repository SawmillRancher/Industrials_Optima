"""Per-period extraction from the CACI EDGAR sources into data/<period>.json (see EXTRACTION_SCHEMA.md).

Periods: annual FY2006-FY2026 (fourth-quarter release, twelve-month column) and quarters Q1 FY13 - Q1 FY27 (that quarter's release,
three-month column). CACI's fiscal year ends 30 June (FY2027 = Jul-2026 - Jun-2027). Release units are thousands; everything is
stored in USD millions (per share as published, shares in millions). Each record also carries the prior-year comparative as
presented in the same release ("py"), the release-table rows it was built from ("raw") and its source URLs.
Run with: CACI_SRC=<dir> python3 -I extract.py   (after make_index.py and fetch.py)."""
import json, os, re, sys, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse_release as P

S = os.environ.get('CACI_SRC', '/tmp/caci_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
ARCH = 'https://www.sec.gov/Archives/edgar/data/16058/'
FQ0 = 2013          # first fiscal year with quarterly records

def m(v, per_share=False):
    return None if v is None else (v if per_share else round(v / 1000.0, 6))

IS_MAP = [('rev', r'^revenues?$'), ('direct', r'^direct costs$|^costs of revenue$'), ('indirect', r'^indirect costs'),
          ('da', r'^depreciation and amortization'), ('tot_costs', r'^total (costs of revenues?|operating expenses)'),
          ('oi', r'^(operating income|income from operations)'), ('int_net', r'^interest expense'), ('ebt', r'^income before income taxes'),
          ('tax', r'^income tax'), ('ni', r'^net income attributable to caci'),
          ('ni_tot', r'^net income( before| including).*|^net income\d?$'), ('nci', r'^noncontrolling interest'),
          ('eps_b', r'^basic earnings per share'), ('eps_d', r'^diluted earnings per share'),
          ('sh_b', r'^basic$|basic shares outstanding'), ('sh_d', r'^diluted\d?$|diluted shares outstanding')]
PS = {'eps_b', 'eps_d'}
BS_MAP = [('cash', r'^cash and cash equivalents'), ('ar', r'^(total )?accounts receivable, net$'), ('oca', r'^(prepaid expenses and )?other current assets'),
          ('tca', r'^total current assets'), ('gw_int', r'^goodwill (and|&) intangible assets'), ('gw', r'^goodwill$'), ('intang', r'^intangible assets, net'),
          ('ppe', r'^property(, plant,?)? and equipment, net'), ('rou', r'^operating lease right-of-use'), ('srsp_a', r'^supplemental retirement savings plan assets'),
          ('ar_lt', r'^accounts receivable, long-term'), ('onca', r'^other( long-term)?( assets)?$'), ('ta', r'^total assets'),
          ('cur_debt', r'^(current portion of long-term debt|notes payable)$'), ('ap', r'^accounts payable$'), ('accr_comp', r'^accrued compensation'),
          ('ocl', r'^other (accrued expenses|current liabilities)'), ('tcl', r'^total current liabilities'),
          ('ltd', r'^(long-term debt, net of current portion|notes payable, (long-term|net of current portion))'),
          ('srsp_l', r'^supplemental retirement savings plan obligations'), ('def_tax', r'^deferred income taxes'),
          ('lease_l', r'^operating lease liabilities'), ('oltl', r'^other (long-term )?(liabilities|obligations)'), ('tl', r'^total liabilities$'),
          ('nci', r'^noncontrolling interest'), ('eq_caci', r'^total caci shareholders'), ('teq', r'^(total )?shareholders.? equity'),
          ('tle', r'^total liabilities (and|&) shareholders')]
CUST = [('dod', r'^department of (defense|war)'), ('ic', r'^intelligence community'), ('fedciv', r'^federal civilian'), ('comm', r'^commercial'),
        ('state', r'^state and local'), ('total', r'^total')]
CTYPE = [('cpf', r'^cost[- ](reimbursable|plus)'), ('ffp', r'^(firm )?fixed[- ]price'), ('tm', r'^time[- ]and[- ]materials'), ('total', r'^total')]
PRIME = [('prime', r'^prime'), ('sub', r'^subcontractor'), ('total', r'^total')]
EXPT = [('exp', r'^expertise'), ('tech', r'^technology'), ('total', r'^total')]
DCOST = [('labor', r'^direct labor'), ('odc', r'^other direct costs'), ('total', r'^total')]

def period_of(d):
    for b in d['sections'].get('is', []) + d['sections'].get('bs', []):
        for h in b['hdr']:
            mm = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', h)
            if mm:
                mo, y = int(mm.group(1)), int(mm.group(3)); y += 2000 if y < 100 else 0
                return y + (1 if mo >= 7 else 0), {9: 1, 12: 2, 3: 3, 6: 4}[mo], dt.date(y, mo, 30 if mo in (6, 9) else 31).isoformat()
    return None

def slots(blocks, maps, per_share=()):
    """IS-type rows -> {slot: {key: value}} for slots qc, qp, yc, yp (first occurrence wins)."""
    out = {'qc': {}, 'qp': {}, 'yc': {}, 'yp': {}}
    for b in blocks or []:
        if b['mode'] == 'I': continue
        for lab, vals, res in b['rows']:
            L = lab.lower()
            key = next((k for k, p in maps if re.search(p, L)), None)
            if not key or res is None: continue
            for sl, v in zip(('qc', 'qp', 'yc', 'yp'), res):
                if v is not None and key not in out[sl]:
                    out[sl][key] = v if key in per_share else round(v / 1000.0, 6)
    return out

def share_tables(blocks, maps):
    """revenue tables 'label | cur | cur% | prior | prior% | $chg | %chg' -> {slot: {key: v}}"""
    out = {'qc': {}, 'qp': {}, 'yc': {}, 'yp': {}}
    for b in blocks or []:
        if b['mode'] not in ('Q', 'Y'): continue
        c, p = ('qc', 'qp') if b['mode'] == 'Q' else ('yc', 'yp')
        for lab, vals, _ in b['rows']:
            key = next((k for k, pt in maps if re.search(pt, lab.lower())), None)
            if not key or len(vals) < 3 or key in out[c]: continue
            out[c][key] = m(vals[0]); out[p][key] = m(vals[2] if len(vals) >= 5 else vals[1])
    return out

def single(blocks, rx):
    out = {}
    for b in blocks or []:
        if b['mode'] not in ('Q', 'Y'): continue
        c, p = ('qc', 'qp') if b['mode'] == 'Q' else ('yc', 'yp')
        for lab, vals, _ in b['rows']:
            if re.search(rx, lab.lower()) and len(vals) >= 2 and c not in out:
                out[c] = m(vals[0]); out[p] = m(vals[1])
    return out

def bs_of(d):
    for b in d['sections'].get('bs', []):
        if b['mode'] != 'I' or not any(re.search(r'^total assets', l.lower()) for l, _, _ in b['rows']): continue
        cur, py, raw = {}, {}, []
        for lab, vals, _ in b['rows']:
            if len(vals) < 2 or vals[0] is None: continue
            raw.append([lab, m(vals[0]), m(vals[1])])
            key = next((k for k, p in BS_MAP if re.search(p, lab.lower())), None)
            if key and key not in cur: cur[key] = m(vals[0]); py[key] = m(vals[1])
        cur['lines_raw'] = [[l, a] for l, a, _ in raw]; py['lines_raw'] = [[l, b_] for l, _, b_ in raw]
        return cur, py
    return None, None

def cf_of(d):
    for sec in ('cf', 'bs'):
        for b in d['sections'].get(sec, []):
            if not any(re.search(r'^net cash provided by operating', l.lower()) for l, _, _ in b['rows']): continue
            if b['mode'] not in ('Q', 'Y'): continue
            lines, stage = [], 'op'
            for lab, vals, _ in b['rows']:
                if len(vals) < 2: continue
                L = lab.lower()
                lines.append([lab, stage, m(vals[0]), m(vals[1])])
                if re.search(r'^net cash.*operating activities', L): stage = 'inv'
                elif re.search(r'^net cash.*investing activities', L): stage = 'fin'
                elif re.search(r'^net cash.*financing activities', L): stage = 'end'
            return {'ytd_months': b['months'] or 3, 'lines': lines}
    return None

def recon_of(d):
    rows = []
    for b in d['sections'].get('recon', []):
        if b['mode'] == 'I': continue
        for lab, vals, res in b['rows']:
            if res is None or len(vals) < 2: continue
            rows.append([lab] + list(res))
    def get(rx, ps=False, nth=0):
        hits = [r for r in rows if re.search(rx, r[0].lower())]
        if len(hits) <= nth: return [None] * 4
        return [m(v, ps) for v in hits[nth][1:5]]
    return rows, get

def fcf_of(d):
    out = {}
    for b in d['sections'].get('fcf', []):
        if b['mode'] == 'I': continue
        for lab, vals, res in b['rows']:
            L = lab.lower()
            key = ('cfo_ex' if 'excluding marpa' in L else 'cfo' if L.startswith('net cash provided by operating') else 'marpa' if 'marpa' in L
                   else 'capex' if L.startswith('capital exp') else 'fcf' if L.startswith('free cash flow') else None)
            need = 4 if b['mode'] == 'QY' else 2
            if key and key not in out and len(vals) >= need and res: out[key] = [m(v) for v in res]
    return out

BN = r'\$\s?([\d.,]+)\s+(billion|million)'
def money(mm, i=1):
    v = float(mm.group(i).replace(',', '')); return round(v * (1000 if mm.group(i + 1) == 'billion' else 1), 3)

def text_kpis(d):
    t = re.sub(r'\s+', ' ', ' '.join(d['lines']))
    out = {}
    mm = re.search(r'[Tt]otal backlog (?:as of|at)[^$]{0,110}?' + BN, t)
    if mm: out['backlog_total'] = money(mm); out['backlog_total_text'] = t[mm.start():mm.end() + 70]
    mm = re.search(r'Funded backlog (?:as of|at)?[^$]{0,110}?' + BN, t)
    if mm: out['backlog_funded'] = money(mm); out['backlog_funded_text'] = t[mm.start():mm.end() + 70]
    mm = re.search(r'[Cc]ontract awards (?:in|for) (?:the )?(?:Q\d FY\d\d|[a-z]+ quarter)[^$]{0,40}? totaled ' + BN, t)
    if mm: out['awards_text'] = money(mm)
    mm = re.search(r'Days sales outstanding(?: \(DSO\))?(?: \d)? \| (\d+)', t)
    if mm: out['dso'] = int(mm.group(1))
    mm = re.search(r'organic(?:ally)?(?: revenue)? growth of (?:approximately )?([\d.]+)(?:%| percent)', t) or re.search(r'including ([\d.]+)(?:%| percent) organic', t) \
        or re.search(r'([\d.]+)(?:%| percent) organic(?:ally)?', t)
    if mm: out['organic_text_pct'] = float(mm.group(1)); out['organic_text'] = t[max(0, mm.start() - 150):mm.end() + 40]
    mm = re.search(r'approximately ([\d,]+) (?:talented )?employees|[Oo]ur ([\d,]+) talented employees', t)
    if mm: out['employees_release'] = int((mm.group(1) or mm.group(2)).replace(',', ''))
    return out

def build(d, fy, q, slot_c, slot_p, months):
    """one record (current column) + its prior-year comparative from the same release. slot_c: 'qc' or 'yc'."""
    is_ = slots(d['sections'].get('is'), IS_MAP, PS)
    rec = {'is': dict(is_[slot_c]), 'py': {'is': dict(is_[slot_p])}}
    for r in (rec['is'], rec['py']['is']):
        if 'ni' not in r and 'ni_tot' in r: r['ni'] = r['ni_tot']
        for k in ('sh_b', 'sh_d'):
            if k in r: r[k] = round(r[k], 6)
    for name, sec, mp in (('cust', 'cust', CUST), ('ctype', 'ctype', CTYPE), ('prime', 'prime', PRIME), ('exptech', 'exptech', EXPT), ('dcost', 'dcost', DCOST)):
        st = share_tables(d['sections'].get(sec), mp)
        if st[slot_c]: rec[name] = st[slot_c]; rec['py'][name] = st[slot_p]
    for name, sec, rx in (('orders', 'orders', r'^contract funding orders'), ('awards', 'awards', r'^contract awards')):
        sg = single(d['sections'].get(sec), rx)
        if slot_c in sg: rec[name] = sg[slot_c]; rec['py'][name] = sg.get(slot_p)
    i = 0 if slot_c == 'qc' else 2
    org = {}
    for b in d['sections'].get('organic', []):
        if slot_c == 'yc' and b['months'] != months and b['mode'] != 'Q': continue
        for lab, vals, res in b['rows']:
            L = lab.lower()
            if res is None: continue
            if 'acquired revenue' in L and 'acq' not in org and res[i] is not None: org['acq'] = m(res[i])
            if L.startswith('organic revenue') and 'org_rev' not in org and res[i] is not None:
                org['org_rev'] = m(res[i]); org['base'] = m(res[i + 1])
            if L.startswith('revenue, as adjusted') and 'rev_adj' not in org and res[i] is not None: org['rev_adj'] = m(res[i])
    if org: rec['organic'] = org
    rows, get = recon_of(d)
    ng = {}
    def put(key, rx, ps=False, nth=0):
        v = get(rx, ps, nth)
        if v[i] is not None: ng[key] = v[i]; rec['py'].setdefault('ngaap', {})[key] = v[i + 1]
    put('ebitda_pub', r'^ebitda$'); put('adj_ebitda_pub', r'^(adjusted|pro ?forma) ebitda\d?$')
    put('rec_da', r'^depreciation and amortization'); put('rec_int', r'^interest'); put('rec_tax', r'^income taxes')
    put('earnout', r'earn-?out adjustments?$'); put('prod_adj', r'^product sale adjustment'); put('fp_adj', r'^fixed price contract adjustment')
    put('adj_ni_pub', r'^(adjusted net income|cash net income)( attributable to caci)?$')
    put('adj_eps_pub', r'^(adjusted diluted eps|diluted adjusted earnings per share|diluted cash earnings per share)$', True)
    put('a_sbc', r'^stock-based compensation'); put('a_amfin', r'^amortization of financing costs'); put('a_ncint', r'^non-cash interest expense')
    put('a_tax', r'^related tax effect|^tax effect of intangible amortization'); put('a_intang', r'^intangible amortization expense')
    put('a_da', r'^depreciation and amortization', nth=1)
    put('pf_oi', r'^pro forma operating income|^operating income, as adjusted'); put('pf_ni', r'^pro forma net income|^net income, as adjusted')
    put('pf_eps', r'^pro forma diluted earnings per share|^diluted earnings per share, as adjusted', True)
    put('pf_adj_ni', r'^pro forma adjusted net income'); put('pf_adj_eps', r'^pro forma diluted adjusted earnings per share', True)
    f = fcf_of(d)
    for k, v in f.items():
        if v[i] is not None: ng['fcf_' + k] = v[i]; rec['py'].setdefault('ngaap', {})['fcf_' + k] = v[i + 1]
    if ng: rec['ngaap'] = ng
    rec['raw'] = {'recon': [[r[0], m(r[1 + i]) if abs(r[1 + i] or 0) > 50 else r[1 + i], m(r[2 + i]) if abs(r[2 + i] or 0) > 50 else r[2 + i]] for r in rows if r[1 + i] is not None]}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    fl = json.load(open(os.path.join(S, 'filings.json')))
    filings = {}
    for o in fl:
        if o['form'] in ('10-K', '10-Q'):
            e = dt.date.fromisoformat(o['report'])
            fy = e.year + (1 if e.month >= 7 else 0); q = {9: 1, 12: 2, 3: 3, 6: 4}[e.month]
            filings[(fy, q)] = ARCH + o['acc'].replace('-', '') + '/' + o['primary']
    done, index = set(), {}
    for o in fl:
        if not o['form'].startswith('8-K') or '2.02' not in o['items']: continue
        for doc in o['files']:
            if doc == o['primary'] or doc.endswith('.txt'): continue
            p = os.path.join(S, 'txt', f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")
            if not os.path.exists(p): continue
            d = P.parse(p)
            if 'is' not in d['sections'] or 'bs' not in d['sections']: continue
            per = period_of(d)
            if not per: continue
            fy, q, end = per
            if (fy, q) in done: continue            # first release for the quarter = as originally reported (8-K/A of 24-Apr-2025 skipped)
            done.add((fy, q))
            url = ARCH + o['acc'].replace('-', '') + '/' + doc
            index[f'Q{q}-{str(fy)[2:]}'] = {'release': url, 'release_date': o['date'], 'filing': filings.get((fy, q))}
            bs, bs_py = bs_of(d); cf = cf_of(d); kp = text_kpis(d)
            jobs = []
            if fy >= FQ0: jobs.append((f'Q{q}-{str(fy)[2:]}', 'qc', 'qp', 3))
            if q == 4: jobs.append((str(fy), 'yc', 'yp', 12))
            for key, sc, sp, months in jobs:
                rec = build(d, fy, q, sc, sp, months)
                out = {'period': key, 'fy': fy, 'q': None if sc == 'yc' else q, 'period_end': end,
                       'sources': {'release': url, 'release_date': o['date'], 'filing': filings.get((fy, q))}}
                out.update(rec)
                out['bs'] = bs; out['py']['bs'] = bs_py
                if cf:
                    out['cf'] = {'ytd_months': cf['ytd_months'], 'lines': [[l, st, a] for l, st, a, _ in cf['lines']]}
                    out['py']['cf'] = {'ytd_months': cf['ytd_months'], 'lines': [[l, st, b] for l, st, _, b in cf['lines']]}
                out['kpi'] = kp
                out['notes'] = []
                json.dump(out, open(os.path.join(OUT, key + '.json'), 'w'), indent=1, ensure_ascii=False)
    json.dump(index, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    print(len(done), 'releases;', len(os.listdir(OUT)), 'files')

if __name__ == '__main__':
    main()
