"""Per-period extraction from the Lockheed Martin EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2025 (fourth-quarter release, twelve-month column) and quarters Q1/13 - Q3/26 (that quarter's release,
three-month column; Q4 from the fourth-quarter release three-month column). Each record carries:
  is       consolidated statement of earnings (USD m; per share in $; shares in m)
  seg      segment net sales / operating profit, unallocated items (company labels and categories), consolidated operating profit
  pension  FAS / CAS detail where the release prints it (FAS expense, CAS cost, FAS/CAS adjustment, service cost, non-service cost)
  cf       cash flow, year to date (cf.ytd_months), classified lines plus the raw lines
  bs       balance sheet at period end (plus the prior year-end column of the same release in bs_py)
  backlog  backlog by segment at period end (+ prior year end)
  deliv    aircraft deliveries
  summary  release summary table (free cash flow, cash from operations) where printed
  py       the prior-year comparative as presented in the following year's release (is, seg, pension): used for the hybrid recast
  x        XBRL facts (dividends declared per share)
  sources / notes
Release units are USD millions and are stored as published (per share in $; shares in millions). Costs are stored positive;
two-sided items (other income, unallocated items) are signed by their effect on earnings.
"""
import json, glob, os, re, datetime as dt
import parse_release as P
import xbrl

S = os.environ.get('LMT_SRC', '/tmp/claude-0/-home-user-Industrials-Optima/cd6a9311-fae6-575a-8d7a-343480d8adb0/scratchpad/lmt_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '936468'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'

def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc

# ------------------------------------------------------------------ release index: (fy, q) -> release
def fyq_of_release(date):
    d = dt.date.fromisoformat(date)
    if d.month <= 2: return d.year - 1, 4
    if d.month <= 5: return d.year, 1
    if d.month <= 8: return d.year, 2
    return d.year, 3

def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, filings = {}, {}
    for o in fl:
        if o['form'] == '8-K' and '2.02' in o['items']:
            for doc in o['files']:
                if doc == o['primary']: continue
                p = os.path.join(S, 'docs', f"{o['date']}_8-K_{o['acc']}_{doc}")
                if not os.path.exists(p): continue
                tabs = P.parse(open(p, 'rb').read())
                types = {t['type'] for t in tabs}
                if not {'is', 'bs', 'cf'} <= types: continue
                fy, q = fyq_of_release(o['date'])
                if (fy, q) not in rel:
                    rel[(fy, q)] = dict(date=o['date'], url=url(o, doc), tabs=tabs, path=p)
        if o['form'] in ('10-Q', '10-K'):
            e = dt.date.fromisoformat(o['report'])
            fy = e.year
            q = {3: 1, 4: 1, 6: 2, 7: 2, 9: 3, 10: 3, 12: 4}[e.month]
            filings[(fy, q)] = dict(date=o['date'], url=url(o, o['primary']), path=os.path.join(S, 'docs', f"{o['date']}_{o['form']}_{o['acc']}_{o['primary']}"), form=o['form'])
    return rel, filings

# ------------------------------------------------------------------ label classifiers
SEGMAP = [('aero', r'^aeronautics'), ('mfc', r'^missiles(&|and)firecontrol'), ('rms', r'^(rotary(&|and)missionsystems|missionsystems(&|and)training)'),
          ('space', r'^space(systems)?\d*$'), ('es', r'^electronicsystems'), ('isgs', r'^(informationsystems(&|and)global|is&gs)'),
          ('itgs', r'^information(&|and)?technology(&|and)globalservices|^it(&|and)globalservices'),
          ('iss', r'^integratedsystems(&|and)solutions'), ('sitg', r'^systems(&|and)itgroup')]
def segkey(cl):
    for k, p in SEGMAP:
        if re.search(p, cl): return k
    return None

def ucat(cl):
    """unallocated / pension line -> category."""
    if re.search(r'fas/cas(pension)?operatingadjustment', cl): return 'fascas_op'
    if re.search(r'nonservicefaspension|nonoperatingfaspension', cl): return 'nonsvc'
    if 'settlement' in cl: return 'settle'
    if 'fas/cas' in cl: return 'fascas'
    if 'faspensionservicecost' in cl: return 'fas_svc'
    if 'faspensionexpense' in cl or re.search(r'^fas87expense', cl): return 'fas_exp'
    if re.search(r'(^|less)cas(pension|expense|cost)', cl): return 'cas'
    if 'severance' in cl or 'restructuring' in cl: return 'sev'
    if 'impairment' in cl: return 'impair'
    if re.search(r'stockbasedcompensation|stockcompensation', cl): return 'sbc'
    if 'intangibleasset' in cl or 'amortization' in cl: return 'amort'
    if re.search(r'^totalunallocated|^unallocated(corporate|expense|items|income)', cl): return 'unalloc_tot'
    if re.search(r'^other', cl): return 'other'
    return 'special'

# ------------------------------------------------------------------ section extractors
def ext_is(tabs, mo, cp):
    for t in P.tables_with(tabs, 'is', mo, cp):
        ci = P.colidx(t, mo, cp)
        out, state, sub, found = {}, None, None, False
        for lab, cl, vals in t['rows']:
            v = vals.get(ci) if vals else None
            if not vals:
                if re.search(r'earnings.*percommonshare$|^(basic|diluted)(loss)?earnings', cl): state = 'eps'
                elif re.search(r'^weightedaverage|^averagenumberofshares', cl): state = 'sh'
                if state == 'eps' and cl in ('basic', 'diluted'): sub = cl
                continue
            if v is None: continue
            if state is None:
                for k, p in (('rev', r'^(net)?sales\d*$'), ('cos', r'^cost(s)?ofsales|^operatingcostsandexpenses'), ('gp', r'^grossprofit'),
                             ('othinc', r'^other(expense)?income|^otherincomeandexpense'), ('op', r'^operatingprofit'), ('int', r'^interestexpense'),
                             ('nonsvc', r'^nonservicefaspension'), ('othnonop', r'^othernonoperating'), ('ebt', r'^earnings.*beforeincometax'),
                             ('tax', r'^incometax'), ('cont', r'^(net)?(loss)?earnings(loss)?fromcontinuingoperations'), ('disc', r'fromdiscontinuedoperations'),
                             ('ni', r'^net(loss)?earnings(loss)?\d*$'), ('etr', r'^effectivetaxrate'), ('sh_end', r'^commonsharesreported'),
                             ('eps_b', r'^basic$|^basicearnings'), ('eps_d', r'^diluted$|^dilutedearnings')):
                    if re.search(p, cl) and k not in out:
                        out[k] = v; found = True
                        if k in ('eps_b', 'eps_d'): state = 'eps'
                        break
            elif state == 'eps':
                if re.search(r'^continuingoperations', cl): out[('eps_b_cont' if sub == 'basic' else 'eps_d_cont')] = v
                elif re.search(r'^discontinuedoperations', cl): out[('eps_b_disc' if sub == 'basic' else 'eps_d_disc')] = v
                elif re.search(r'^basic', cl): out['eps_b'] = v; sub = 'basic'
                elif re.search(r'^diluted', cl): out['eps_d'] = v; sub = 'diluted'
                elif re.search(r'^commonsharesreported', cl): out['sh_end'] = v
            elif state == 'sh':
                if re.search(r'^basic', cl): out['sh_b'] = v
                elif re.search(r'^diluted', cl): out['sh_d'] = v
                elif re.search(r'^commonsharesreported', cl): out['sh_end'] = v
        if not found or 'rev' not in out: continue
        for k in ('cos', 'int'):
            if k in out: out[k] = abs(out[k])
        if 'tax' in out:
            if 'ebt' in out and ('cont' in out or 'ni' in out):
                base = out['cont'] if 'cont' in out else out['ni'] - out.get('disc', 0.0)
                out['tax'] = abs(out['tax']) if abs(out['ebt'] - abs(out['tax']) - base) < 1.5 else -abs(out['tax'])
            else: out['tax'] = abs(out['tax'])
        if 'gp' not in out and 'cos' in out: out['gp'] = round(out['rev'] - out['cos'], 3); out['gp_derived'] = True
        return out
    return None

def ext_seg(tabs, mo, cp, ty='seg'):
    best = None
    for t in P.tables_with(tabs, ty, mo, cp):
        ci = P.colidx(t, mo, cp)
        out = {'sales': {}, 'op': {}, 'unalloc': [], 'margin': {}}
        sec = 'sales'
        for lab, cl, vals in t['rows']:
            v = vals.get(ci) if vals else None
            if not vals or v is None:
                if re.search(r'^(net)?sales', cl): sec = 'sales'
                elif re.search(r'^operatingprofit|^segmentoperatingprofit', cl): sec = 'op'
                elif re.search(r'^unallocated', cl): sec = 'unalloc'
                elif re.search(r'^(operating)?margins?', cl): sec = 'margin'
                continue
            sk = segkey(cl)
            if sec == 'sales':
                if sk: out['sales'][sk] = v
                elif re.search(r'^total|^netsales\d*$|^sales\d*$', cl): out['sales_tot'] = v; sec = 'sales_done'
                continue
            if sec == 'margin':
                if sk: out['margin'][sk] = v
                continue
            if re.search(r'^totalbusinesssegmentoperatingprofit|^segmentoperatingprofit|^totaloperatingsegments|^businesssegmentoperatingprofit|^totalsegmentoperatingprofit|^totalbusinesssegments', cl) \
                    or (sec == 'op' and re.search(r'^total\d*$', cl)):
                out['op_tot'] = v; sec = 'unalloc'; continue
            if sec == 'op':
                if sk: out['op'][sk] = v; continue
                c = ucat(cl)
                if c == 'special' and 'unallocated' not in cl: continue
                sec = 'unalloc'
            if sec == 'unalloc':
                if re.search(r'^totalconsolidatedoperatingprofit|^consolidatedoperatingprofit|^operatingprofit\d*$|^total\d*$|^totaloperatingprofit', cl): out['op_cons'] = v; sec = 'done'; continue
                if re.search(r'^netearnings|^diluted|^cashfrom|^capital|^freecash|^basic', cl): sec = 'done'; continue
                c = ucat(cl)
                if c == 'unalloc_tot': out['unalloc_tot'] = v
                else: out['unalloc'].append([lab, c, v])
        score = len(out['sales']) + len(out['unalloc']) + ('op_tot' in out) + ('op_cons' in out)
        if out['sales'] and (best is None or score > best['_score']):
            out['_score'] = score; best = out
    if best: best.pop('_score', None)
    return best

def ext_unalloc_sfd(tabs, mo, cp):
    """unallocated corporate items from the 'Selected Financial Data' schedules (2006-2012 releases)."""
    for ty in ('pension', 'unalloc'):
        for t in P.tables_with(tabs, ty, mo, cp):
            ci = P.colidx(t, mo, cp)
            items, tot = [], None
            for lab, cl, vals in t['rows']:
                v = vals.get(ci) if vals else None
                if v is None: continue
                c = ucat(cl)
                if c in ('fas_exp', 'cas', 'fas_svc'): continue
                if c == 'unalloc_tot': tot = v; break
                items.append([lab, c, v])
            if items and tot is not None: return items, tot
    return [], None

def ext_pension(tabs, mo, cp, year=None):
    """FAS / CAS detail. Tables that list the FAS cost components (costs shown positive) are skipped; the FAS/CAS reconciliation tables
    (income effect signs) are used. year: for the 'YYYY Outlook | YYYY Actual' tables, only accept an 'Actual' column of that year."""
    out = {}
    for ty in ('pension', 'unalloc', 'seg'):
        for t in P.tables_with(tabs, ty, mo, cp):
            labs = ' '.join(cl for _, cl, _ in t['rows'])
            if 'expectedreturn' in labs or 'interestcost' in labs: continue
            hl = ' '.join(t['hdr']).lower()
            if t['cols'][0][1] == 'out':
                if year is None or f'{year} actual' not in hl: continue
            ci = P.colidx(t, mo, cp)
            for lab, cl, vals in t['rows']:
                v = vals.get(ci) if vals else None
                if v is None: continue
                c = ucat(cl)
                if c in ('fas_exp', 'cas', 'fas_svc', 'fascas_op', 'nonsvc', 'fascas', 'settle') and c not in out:
                    out[c] = v
                    if c == 'cas': out['cas_label'] = lab
    return out or None

CF_MAP = [('ni', r'^net(loss)?earnings'), ('dda', r'^depreciation|^amortizationofpurchasedintangibles'), ('sbc', r'^stockbasedcompensation'), ('deftax', r'^deferredincometaxes'),
          ('sev', r'severance|impairment|restructuring'), ('settle', r'pensionsettlement'), ('rfl', r'^reachforward'),
          ('pens', r'^qualifieddefinedbenefitpension|^postretirementbenefitplans|^pension(plan|contribution)|^definedbenefit'),
          ('wc_ar', r'^receivables'), ('wc_ca', r'^contractassets'), ('wc_inv', r'^inventories'), ('wc_ap', r'^accountspayable'),
          ('wc_cl', r'^contractliabilities|^customeradvances'), ('wc_tax', r'^incometaxes'), ('wc_oth', r'^other'),
          ('cfo', r'^netcashprovidedby(usedfor)?operatingactivities|^netcash.*operating'),
          ('capex', r'^capitalexpenditures|^additionstoproperty|^expendituresforproperty|^expendituresforcapitalizedinternalusesoftware'),
          ('acq', r'acquisition'), ('divest', r'divestiture|saleofbusiness|proceedsfromsaleof'), ('cfi', r'^netcash.*investing'),
          ('debt_iss', r'^issuanceoflongtermdebt|^proceedsfromissuance'), ('debt_rep', r'^repayments?oflongtermdebt|^repaymentoflongtermdebt'),
          ('bb', r'^repurchasesofcommonstock|^commonstockactivitynet'), ('div', r'^dividendspaid|^commonstockdividends'),
          ('stock_iss', r'^issuancesofcommonstock|^proceedsfrom(stock|issuance)'),
          ('cff', r'^netcash.*financing'), ('fx', r'^effectofexchange'), ('net', r'^net(change|increase|decrease).*cash'),
          ('beg', r'beginningof'), ('end', r'endof')]

def ext_cf(tabs, mo, cp):
    for t in P.tables_with(tabs, 'cf', mo, cp):
        ci = P.colidx(t, mo, cp)
        out, raw, sec = {'ytd_months': mo}, [], 'op'
        for lab, cl, vals in t['rows']:
            v = vals.get(ci) if vals else None
            if not vals or v is None:
                if 'investingactivities' in cl: sec = 'inv'
                elif 'financingactivities' in cl: sec = 'fin'
                continue
            raw.append([lab, v])
            for k, p in CF_MAP:
                if re.search(p, cl):
                    if k in ('wc_oth', 'wc_ar', 'wc_ca', 'wc_inv', 'wc_ap', 'wc_cl', 'wc_tax', 'pens', 'sev', 'settle', 'rfl', 'deftax', 'sbc', 'dda') and sec != 'op': continue
                    if k in ('capex', 'acq') and sec != 'inv': continue
                    if k in ('bb', 'div', 'stock_iss', 'debt_iss', 'debt_rep') and sec != 'fin': continue
                    if k in ('acq', 'divest', 'sev', 'debt_rep', 'debt_iss', 'capex', 'dda'): out[k] = round(out.get(k, 0.0) + v, 3)
                    elif k not in out: out[k] = v
                    break
            else:
                if sec == 'inv' and 'other' in cl: out['inv_oth'] = out.get('inv_oth', 0.0) + v
                if sec == 'fin' and 'other' in cl: out['fin_oth'] = out.get('fin_oth', 0.0) + v
            if re.search(r'^netcash.*operating', cl): sec = 'inv'
            if re.search(r'^netcash.*investing', cl): sec = 'fin'
        out['lines_raw'] = raw
        if 'cfo' in out: return out
    return None

BS_MAP = [('cash', r'^cashandcashequivalents'), ('ar', r'^receivables'), ('ca', r'^contractassets'), ('inv', r'^inventories'),
          ('dta_c', r'^deferredincometaxes'), ('oca', r'^othercurrentassets'), ('tca', r'^totalcurrentassets'),
          ('ppe', r'^property'), ('gw', r'^goodwill'), ('intang', r'^intangibleassets'), ('dta', r'^deferredincometaxes'),
          ('onca', r'^othernoncurrentassets|^otherassets'), ('ta', r'^totalassets'),
          ('ap', r'^accountspayable'), ('sal', r'^salaries'), ('cl', r'^contractliabilities|^customeradvances'),
          ('std', r'^currentmaturitiesoflongtermdebt|^shorttermborrowings|^commercialpaper'), ('ocl', r'^othercurrentliabilities'),
          ('tcl', r'^totalcurrentliabilities'), ('ltd', r'^longtermdebt'), ('pens', r'^accruedpensionliabilities'),
          ('opeb', r'^otherpostretirementbenefit'), ('oncl', r'^othernoncurrentliabilities|^otherliabilities'), ('tl', r'^totalliabilities\d*$'),
          ('cs', r'^commonstock'), ('apic', r'^additionalpaidincapital'), ('re', r'^retainedearnings'), ('aoci', r'^accumulatedothercomprehensive'),
          ('eq', r"^totalstockholdersequity|^stockholdersequity\d*$"), ('nci', r'noncontrollinginterests?'), ('te', r'^totalequity'),
          ('tle', r'^totalliabilitiesand(stockholders)?equity')]

def ext_bs(tabs, cp='cur'):
    for t in P.tables_with(tabs, 'bs', 0, cp):
        ci = P.colidx(t, 0, cp)
        out, raw, cur = {}, [], True
        for lab, cl, vals in t['rows']:
            v = vals.get(ci) if vals else None
            if v is None: continue
            raw.append([lab, v])
            for k, p in BS_MAP:
                if re.search(p, cl):
                    if k == 'dta_c' and not cur: continue
                    if k == 'dta' and cur: continue
                    if k not in out: out[k] = v
                    break
            if re.search(r'^totalcurrentassets', cl): cur = False
        out['lines_raw'] = raw
        if 'ta' in out: return out
    return None

def ext_backlog(tabs, cp='cur'):
    out = {}
    for t in P.tables_with(tabs, 'backlog', 0, cp):
        ci = P.colidx(t, 0, cp)
        for lab, cl, vals in t['rows']:
            v = vals.get(ci) if vals else None
            if v is None: continue
            sk = segkey(cl)
            if sk: out[sk] = v
            elif 'total' in cl: out['total'] = v
    return out or None

def ext_deliv(tabs, mo, cp='cur'):
    out = {}
    for t in P.tables_with(tabs, 'deliv', mo, cp):
        ci = P.colidx(t, mo, cp)
        for lab, cl, vals in t['rows']:
            v = vals.get(ci) if vals else None
            if v is None: continue
            out[cl] = v
    return out or None

def ext_summary(tabs, mo, cp='cur'):
    o = {'fcf_pub': P.get(tabs, 'summary', r'^freecashflow', mo, cp), 'cfo': P.get(tabs, 'summary', r'^cashfromoperations', mo, cp),
         'capex': P.get(tabs, 'summary', r'^capitalexpenditures', mo, cp), 'seg_op': P.get(tabs, 'summary', r'^(business)?segmentoperatingprofit', mo, cp)}
    return {k: v for k, v in o.items() if v is not None} or None

# ------------------------------------------------------------------ 10-K segment tables (for recast years: FY2011 from the FY2013 10-K)
def ext_10k_seg(path):
    """-> {year: {'sales': {seg: v}, 'op': {seg: v}}} from the 10-K segment-note tables (three fiscal years)."""
    out = {}
    if not os.path.exists(path): return out
    for t in P.html_tables(open(path, 'rb').read()):
        labs = ' || '.join(P.compact(l) for l, _ in t['rows'])
        if 'aeronautics' not in labs or 'spacesystems' not in labs and 'space' not in labs: continue
        h = ' | '.join(t['hdr'] + [l for l, v in t['rows'][:2] if not v])
        years = [int(y) for y in re.findall(r'(?<!\d)(20\d\d)(?!\d)', h)]
        if len(years) < 2: continue
        sec = 'sales' if re.search(r'netsales|sales', P.compact(' '.join(t['hdr']))) else None
        for lab, vals in t['rows']:
            cl = P.compact(lab)
            if not vals:
                if re.search(r'^netsales|^sales', cl): sec = 'sales'
                elif re.search(r'^operatingprofit', cl): sec = 'op'
                elif re.search(r'^(total)?backlog|^assets|^depreciation|^capital|^intersegment', cl): sec = None
                continue
            sk = segkey(cl)
            if not sk or not sec or len(vals) < len(years): continue
            for y, v in zip(years, vals[:len(years)]):
                out.setdefault(y, {'sales': {}, 'op': {}})[sec].setdefault(sk, v)
            if re.search(r'^total', cl): sec = None
    return out

# ------------------------------------------------------------------ pro forma (realigned) segment tables, Q4-2015 release
def ext_segpf(path):
    """Jan-2016 release: 'Proforma Business Segment Net Sales, Operating Profit and Operating Margins' tables re-presenting 2014 and 2015
    (quarters and years) for the Q4-2015 program realignment: 4 columns per period (previously reported, two reclassifications, as
    adjusted). -> {period key: {'sales': {seg: v}, 'op': {seg: v}, 'unalloc_tot': v, 'op_cons': v}} using the 'as adjusted' column."""
    out = {}
    for t in P.html_tables(open(path, 'rb').read()):
        h = ' | '.join(t['hdr'])
        hl = h.lower()
        if 'as adjusted' not in hl or 'reclassification' not in hl: continue
        if 'backlog' in hl: continue
        if re.search(r'six months|nine months|three months', hl): continue        # year-to-date tables: not needed
        m = re.search(r'twelve months ended dec\.? 31, (20\d\d)', hl)
        if m: keys = [m.group(1)]
        else:
            dates = re.findall(r'quarter ended (march|june|sept\.?|dec\.?)\s*\d+,?\s*(20\d\d)', hl)
            if not dates: continue
            keys = [f"Q{ {'march': 1, 'june': 2, 'sept': 3, 'sept.': 3, 'dec': 4, 'dec.': 4}[m] }-{y[2:]}" for m, y in dates]
        sec = 'sales' if 'netsales' in P.compact(h) else None
        for lab, vals in t['rows']:
            cl = P.compact(lab)
            if not vals:
                if re.search(r'^netsales|^sales', cl): sec = 'sales'
                elif re.search(r'^operatingprofit', cl): sec = 'op'
                elif re.search(r'^operatingmargins?', cl): sec = None
                continue
            if sec is None or len(vals) < 4 * len(keys): continue
            adj = vals[3::4][:len(keys)]
            sk = segkey(cl)
            for k, v in zip(keys, adj):
                d = out.setdefault(k, {'sales': {}, 'op': {}})
                if sk: d[sec][sk] = v
                elif re.search(r'^totalbusinesssegmentoperatingprofit', cl): d['op_tot'] = v
                elif re.search(r'^unallocated', cl): d['unalloc_tot'] = v
                elif re.search(r'^totalconsolidatedoperatingprofit', cl): d['op_cons'] = v
                elif re.search(r'^totalnetsales', cl): d['sales_tot'] = v
    return out

# ------------------------------------------------------------------ build records
def rec_period(rel, filings, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    tabs = r['tabs']
    mo = 12 if annual else 3
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'sources': {'release': r['url'], 'release_date': r['date']}, 'notes': []}
    rec['is'] = ext_is(tabs, mo, 'cur')
    rec['seg'] = ext_seg(tabs, mo, 'cur')
    if rec['seg'] is not None and not rec['seg']['unalloc']:
        items, tot = ext_unalloc_sfd(tabs, mo, 'cur')
        if items:
            rec['seg']['unalloc'] = items; rec['seg']['unalloc_src'] = 'selected financial data'
            if tot is not None and 'unalloc_tot' not in rec['seg']: rec['seg']['unalloc_tot'] = tot
    rec['pension'] = ext_pension(tabs, mo, 'cur', fy if annual else None)
    if annual:          # FAS / CAS actuals also appear in the following year's releases ('YYYY+1 Outlook | YYYY Actual' tables)
        for qq in (1, 2, 3):
            nx = rel.get((fy + 1, qq))
            if not nx: continue
            pe = ext_pension(nx['tabs'], 12, 'cur', fy) or {}
            for k, v in pe.items():
                if k not in (rec['pension'] or {}):
                    rec['pension'] = rec['pension'] or {}; rec['pension'][k] = v; rec['pension'].setdefault('src_next', nx['url'])
    if annual and rec['is'] is not None and 'sh_end' not in rec['is']:
        q3 = ext_is(tabs, 3, 'cur') or {}
        if 'sh_end' in q3: rec['is']['sh_end'] = q3['sh_end']
    ytd = 12 if annual else 3 * q
    rec['cf'] = ext_cf(tabs, ytd, 'cur')
    if rec['cf'] is None and annual: rec['cf'] = ext_cf(tabs, 0, 'cur')
    rec['bs'] = ext_bs(tabs, 'cur'); rec['bs_py'] = ext_bs(tabs, 'py')
    rec['backlog'] = ext_backlog(tabs, 'cur'); rec['backlog_py'] = ext_backlog(tabs, 'py')
    rec['deliv'] = ext_deliv(tabs, mo, 'cur')
    rec['summary'] = ext_summary(tabs, mo, 'cur')
    if not annual and q == 4:
        rec['segpf'] = ext_seg(tabs, mo, 'cur', 'segpf')
    f = filings.get((fy, 4 if annual else q))
    if f: rec['sources']['filing'] = f['url']
    nxt = rel.get((fy + 1, 4 if annual else q))
    if nxt:
        pseg = ext_seg(nxt['tabs'], mo, 'py')
        if pseg is not None and not pseg['unalloc']:
            items, tot = ext_unalloc_sfd(nxt['tabs'], mo, 'py')
            if items: pseg['unalloc'] = items
            if tot is not None and 'unalloc_tot' not in pseg: pseg['unalloc_tot'] = tot
        rec['py'] = {'release': nxt['url'], 'release_date': nxt['date'], 'is': ext_is(nxt['tabs'], mo, 'py'), 'seg': pseg,
                     'pension': ext_pension(nxt['tabs'], mo, 'py', fy if annual else None)}
        if annual: rec['py']['cf'] = ext_cf(nxt['tabs'], 12, 'py')
    rec['x'] = {'dps': xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'FY' if annual else 'Q', 4 if annual else q),
                'dps_ytd': None if annual else xbrl.value('CommonStockDividendsPerShareDeclared', fy, 'YTD', q)}
    return rec

def main():
    os.makedirs(OUT, exist_ok=True)
    rel, filings = release_index()
    idx = [{'fy': fy, 'q': q, 'date': r['date'], 'url': r['url']} for (fy, q), r in sorted(rel.items())]
    json.dump(idx, open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    n = 0
    for fy in range(2006, 2026):
        r = rec_period(rel, filings, fy, 4, True)
        if r: json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
        else: print('missing annual', fy)
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if fy == 2026 and q == 4: break
            r = rec_period(rel, filings, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
            else: print('missing', fy, q)
    # 10-K segment tables for the recast years (FY2013 10-K: 2011-2013 on the five-segment structure)
    tenk = {}
    for fy in (2008, 2013, 2016, 2018):
        f = filings.get((fy, 4))
        if f: tenk[str(fy)] = {'url': f['url'], 'seg': ext_10k_seg(f['path'])}
    json.dump(tenk, open(os.path.join(OUT, '_10k_segments.json'), 'w'), indent=1)
    r15 = rel.get((2015, 4))
    if r15:
        pf = ext_segpf(r15['path']); pf['_source'] = r15['url']
        json.dump(pf, open(os.path.join(OUT, '_segpf_2015.json'), 'w'), indent=1)
    xbrl.dump_subset()
    print(n, 'period files')

if __name__ == '__main__':
    main()
