"""Extract James Hardie (JHX) historical data from the SEC EDGAR results packages into data/<period>.json.

Each quarterly package (6-K to Q3 FY26; 8-K Ex. 99.1 + 10-Q / 10-K from Q4 FY26) is read for its current period and the
prior-year comparative. Records are stored per (period, source filing date, section); normalize.py picks the document that
wins for each period (own package = as originally reported).
  IS   statement of operations (three-month and year-to-date columns)     SEG  segment net sales / EBIT, volumes, prices
  NG   non-GAAP bridges (adjusted EBIT, adjusted net income / EPS, adjusted EBITDA, adjusted tax)
  CF   cash flow (year to date)      BS   balance sheet (quarter end)      AICF asbestos roll-forward and funding
Period keys: '2006'..'2026' fiscal years (31 March), 'Q1-13'.. quarters (Q1 = June quarter), 'H1-13' / '9M-13' YTD cash flow.
Run: JHX_SRC=/path/to/src python3 extract.py
"""
import json, os, re, glob, sys
from parse_release import Doc, vals, pick, num

SRC = os.environ.get('JHX_SRC', '/tmp/jhx_src')
TXT = os.path.join(SRC, 'txt')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
EDGAR = 'https://www.sec.gov/Archives/edgar/data/1159152/'
FIL = json.load(open(os.path.join(SRC, 'filings.json')))

def qk(fy, q): return f'Q{q}-{str(fy)[2:]}'
def ytdk(fy, q): return {1: qk(fy, 1), 2: f'H1-{str(fy)[2:]}', 3: f'9M-{str(fy)[2:]}', 4: str(fy)}[q]
def rel_period(date):
    y, m = int(date[:4]), int(date[5:7])
    if m in (4, 5, 6, 7): return y, 4
    if m in (8, 9, 10): return y + 1, 1
    if m in (11, 12): return y + 1, 2
    return y, 3

REC = {}
LOG = []
def put(per, src, sec, key, v, force=False):
    if v is None: return
    d = REC.setdefault(per, {}).setdefault(src, {}).setdefault(sec, {})
    if force or key not in d: d[key] = v
def log(m): LOG.append(m)

# ---------------------------------------------------------------- package discovery
def packages():
    out = []
    for o in FIL:
        if o['form'] not in ('6-K', '6-K/A', '8-K', '10-K', '10-Q'): continue
        n = o['acc'].replace('-', '')
        docs = {}
        for f in glob.glob(os.path.join(TXT, f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_*.txt")):
            base = os.path.basename(f)
            name = base.split('_', 3)[3]
            t = open(f, errors='ignore').read()
            head = t[:6000].lower()
            size = len(t)
            kind = None
            if 'iar' in name.lower() or 'annualreport' in name.lower(): kind = 'iar'
            elif re.search(r"management.?s analysis of results", head) and size > 20000 and re.search(r'\n(Net [Ss]ales|Total Net Sales)[^\n]* \| ', t): kind = 'ma'
            elif re.search(r'earnings release', head[:400]) or (re.search(r'earnings release', head) and 'james hardie reports' in head): kind = 'er'
            elif re.search(r'(condensed )?consolidated (balance sheets|financial statements)', head) and re.search(r'\nTotal assets \| ', t) and size > 20000: kind = 'fs'
            elif 'media release' in head and size > 5000: kind = 'mr'
            if kind == 'ma' and 'ma' in docs and size < len(open(docs['ma'][0], errors='ignore').read()): continue
            if kind == 'mr' and 'mr' in docs and not re.search(r'mr|mediarelease', name.lower()): continue
            if kind:
                docs[kind] = (f, EDGAR + n + '/' + name.replace('.txt', '.htm'))
        if not docs: continue
        fy, q = rel_period(o['date'])
        if o['form'] in ('10-K', '10-Q'):
            rd = o['report']; fy = int(rd[:4]) + (1 if int(rd[5:7]) > 3 else 0); q = {6: 1, 9: 2, 12: 3, 3: 4}[int(rd[5:7])]
            docs = {'fs': (os.path.join(TXT, f"{o['date']}_{o['form']}_{o['acc']}_{o['primary'].replace('.htm', '.txt')}"), EDGAR + n + '/' + o['primary'])}
            if not os.path.exists(docs['fs'][0]): continue
        if o['form'] == '8-K' and 'er' not in docs: continue
        out.append(dict(date=o['date'], form=o['form'], acc=o['acc'], fy=fy, q=q, docs=docs))
    return out

# ---------------------------------------------------------------- label maps
IS_LABELS = [
    ('rev', r'^(Total )?[Nn]et [Ss]ales$'),
    ('cogs', r'^Cost of goods sold'),
    ('gp', r'^Gross profit$'),
    ('sga', r'^Selling, general (and|&) administrative expenses?'),
    ('rd', r'^Research (and|&) development expenses?'),
    ('sci', r'^SCI and other related expenses'),
    ('impair', r'^(Asset )?[Ii]mpairment( charges?| expenses?)?( - [a-z ]+)?$|^Asset impairments?$'),
    ('restr', r'^Restructuring( expenses|, net)?$'),
    ('acq_exp', r'^Acquisition (and divestiture )?related expenses|^Merger costs$'),
    ('asb_adj', r'^Asbestos (adjustments|provision)( \(?(gain|loss) ?\)?( \(?(loss|gain)\)?)?)?$'),
    ('other_op', r'^Other operating (expense|loss|income)'),
    ('debt_ext', r'^Loss on early debt extinguishment'),
    ('cum_eff', r'^Cumulative effect of change in accounting'),
    ('op', r'^(EBIT|Operating income|Operating \(loss\) income|Operating income \(loss\)|Operating loss)$'),
    ('int_exp', r'^Interest expense'),
    ('int_inc', r'^Interest income'),
    ('int_net', r'^(Net [Ii]nterest|Interest, net)'),
    ('other_nonop', r'^Other (\(income\) expense|income \(expense\)|\(expense\) income|expense|income|\(income\)|expense \(income\))'),
    ('ebt', r'^(Operating|\(Loss\)|Income|Loss)[^|]*before income tax'),
    ('tax', r'^Income tax'),
    ('ni', r'^(Net income|Net operating profit|Net \(loss\) income|Net operating \(loss\) profit|Net income \(loss\)|Net operating profit \(loss\)|Net \(loss\) profit|Net income \(loss\) from continuing|Net \(loss\) income from continuing)'),
    ('disc', r'^Income from discontinued operations, net of tax$'),
    ('ni_total', r'^Net income \(loss\)$|^Net income$'),
    ('ni_cont_a', r'^Operations$'), ('ni_total_a', r'^Discontinued Operations$'),
]
SEG_NAMES = {
    'na': r'^(USA Fibre Cement|USA (and|&) Europe Fib(re|er) Cement|North America (and|&) Europe Fib(re|er) Cement|North America Fiber Cement|Siding & Trim)( segment)?( \d)?$',
    'apac': r'^(Asia Pacific Fib(re|er) Cement|Australia & New Zealand)( segment)?( \d)?$',
    'int': r'^International Fiber Cement( \d)?$',
    'eu': r'^(Europe Building Products|European Building Products|Europe)( segment)?( \d)?$',
    'dra': r'^Deck, Rail & Accessories$',
    'oth': r'^Other( Businesses)?( \d)?$',
    'rd': r'^Research (and|&) Development( \d)?$',
    'corp': r'^(General [Cc]orporate( costs| \d| [Cc]osts \d)?|General corporate costs|General Corporate SG&A expenses|General Corporate and Unallocated R&D costs)( \d)?$',
}

def locate_is(doc, start=0, end=None, need_shares=True):
    """index of the 'Net sales' row that heads an income statement: directly followed by cost of goods sold and (if need_shares)
    by weighted-average share rows within 45 lines. Falls back to the first 'Net sales' + COGS pair."""
    end = doc.n if end is None else end
    cands = []
    for i in range(start, end):
        l = doc.lines[i]
        if ' | ' not in l: continue
        lab = l.split(' | ')[0].strip()
        if not re.search(r'^(Total )?[Nn]et [Ss]ales$', lab): continue
        nxt = ' '.join(doc.lines[i + 1:i + 3])
        if not re.search(r'Cost of goods sold', nxt): continue
        cands.append(i)
    if not cands: return None
    if need_shares:
        for i in cands:
            for j in range(i, min(i + 50, doc.n)):
                lab = doc.lines[j].split(' | ')[0].strip()
                if re.search(r'^(Basic|Diluted|Weighted average)', lab):
                    v = vals(doc.lines[j])
                    if v and v[0] > 100: return i
    return cands[0]

def shares_rows(doc, i0, i1, mode, per, pyper, yt, pyt, ann=None, pann=None):
    for key, pat in [('sh_b', r'^Basic$|^Weighted average[^|]*basic|^\(Millions\) [—–-] Basic'), ('sh_d', r'^Diluted$|^Weighted average[^|]*diluted|^\(Millions\) [—–-] Diluted')]:
        for j in range(i0, min(i1, doc.n)):
            lab = doc.lines[j].split(' | ')[0].strip()
            if not re.search(pat, lab, re.I): continue
            v = vals(doc.lines[j])
            if len(v) >= 3 and float(v[0]).is_integer() and 0 < v[0] <= 30 and v[1] > 100: v = v[1:]   # note-reference column
            if not v or v[0] < 100: continue
            p = pick(v, mode)
            yield key, p
            break

def is_end(doc, i0, span=50):
    """end of the income statement that starts at i0: the diluted weighted-average share row (so the cash-flow statement's
    'Net income' row that follows is not read), else i0 + span."""
    for j in range(i0 + 5, min(i0 + span, doc.n)):
        lab = doc.lines[j].split(' | ')[0].strip()
        v = vals(doc.lines[j])
        if re.search(r'^Diluted$|^Weighted average[^|]*diluted|^\(Millions\) [—–-] Diluted', lab, re.I) and v and v[0] > 100: return j + 1
    return i0 + span

def is_from(doc, mode, start, end, per, src, sec='is', scale_cents=True):
    """income statement rows in [start, end) of doc -> REC."""
    got = {}
    for key, pat in IS_LABELS:
        i = doc.find(pat, start, end)
        if i is None: continue
        v = vals(doc.lines[i]); p = pick(v, mode)
        if not p: continue
        got[key] = (p, doc.lines[i].split(' | ')[0])
    # EPS / shares
    for key, pat in [('eps_d', r'(diluted|Diluted)'), ('eps_b', r'(basic|Basic)')]:
        i = doc.find(r'(per share|Earnings per share|EPS)[^|]*' + pat + r'|^' + pat.split('|')[1].strip('()') + r'$', start, end)
        if i is not None:
            lab = doc.lines[i].split(' | ')[0]
            if re.search(r'share|per|^Basic$|^Diluted$', lab):
                v = vals(doc.lines[i])
                if 'cents' not in lab.lower() and len(v) >= 3 and float(v[0]).is_integer() and 0 < v[0] <= 30 and abs(v[1]) < 100: v = v[1:]   # note-reference column (FY2006-08 statements)
                p = pick(v, mode)
                if p:
                    if 'cents' in lab.lower() and scale_cents: p = {k: round(x / 100.0, 4) for k, x in p.items()}
                    got[key] = (p, lab)
    return got

def store_is(got, per, src, pyper=None, ytdper=None, ytdpyper=None, sec='is'):
    for key, (p, lab) in got.items():
        if 'cur' in p: put(per, src, sec, key, p['cur'])
        if pyper and 'prior' in p: put(pyper, src, sec, key, p['prior'])
        if ytdper and 'ytd' in p: put(ytdper, src, sec, key, p['ytd'])
        if ytdpyper and 'ytd_prior' in p: put(ytdpyper, src, sec, key, p['ytd_prior'])
        put(per, src, sec, '_label_' + key, lab)

# ---------------------------------------------------------------- statements from the financial statements exhibit (fpages / exv99w4)
def fs_statements(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q)
    annual = q == 4
    # ---- income statement: first table after 'Net sales |' with COGS beneath; three-month columns + YTD
    i0 = locate_is(doc)
    if i0 is None: log(f'{src}: FS no IS'); return
    i1 = is_end(doc, i0)
    mode = 'qy' if (q > 1 and not annual) else 'q'
    if annual:
        got = is_from(doc, 'q', i0, i1, per, src)
        store_is(got, str(fy), src, str(fy - 1))
    else:
        got = is_from(doc, mode, i0, i1, per, src)
        store_is(got, per, src, pyper, ytdk(fy, q) if q > 1 else None, ytdk(fy - 1, q) if q > 1 else None)
    for key, p in shares_rows(doc, i0, i1, 'q' if annual else mode, per, pyper, None, None):
        if annual: put(str(fy), src, 'is', key, p['cur']); put(str(fy - 1), src, 'is', key, p.get('prior'))
        else:
            put(per, src, 'is', key, p['cur']); put(pyper, src, 'is', key, p.get('prior'))
            if q > 1: put(ytdk(fy, q), src, 'is', key, p.get('ytd')); put(ytdk(fy - 1, q), src, 'is', key, p.get('ytd_prior'))
    # ---- balance sheet
    b0 = doc.find(r'^Cash and cash equivalents$')
    b1 = doc.find(r'^Total liabilities and shareholders', b0) if b0 is not None else None
    if b0 is not None and b1 is not None:
        bs_from(doc, b0, b1 + 1, per if not annual else str(fy), src, 'q', prior_key=(str(fy - 1) if annual else None))
    # ---- cash flow (year to date)
    c0, c1 = cf_anchor(doc, (b1 or 0))
    if c0 is not None and c1 is not None:
        cf_from(doc, c0, c1 + 1, ytdk(fy, q), ytdk(fy - 1, q), src, q)
    else:
        log(f'{src}: FS no CF')

BS_LABELS = [
    ('cash', r'^Cash and cash equivalents$'), ('restr_cash', r'^Restricted cash( and cash equivalents)?$'),
    ('restr_cash_asb', r'^Restricted cash( and cash equivalents)? [—–-] ?Asbestos'), ('restr_inv_asb', r'^Restricted short.term investments [—–-] ?Asbestos'),
    ('ar', r'^Accounts and (notes|other) receivable|^Accounts receivable|and 31 March \d{4}, respectively$|respectively \| '), ('inv', r'^Inventories$'),
    ('prepaid', r'^Prepaid expenses and other current assets'), ('ins_rec_asb_c', r'^Insurance receivables?( [—–-] ?Asbestos)?$'),
    ('wc_asb_c', r'^Workers.? compensation( [—–-] ?Asbestos)?$'), ('dta_c', r'^Deferred income taxes$'), ('dta_asb_c', r'^Deferred income taxes [—–-] ?Asbestos$'),
    ('hfs', r'^Assets held for sale$'), ('tca', r'^Total current assets$'),
    ('restr_cash_nc', r'^Restricted cash( and cash equivalents)?$'), ('ppe', r'^Property, plant and equipment, net'),
    ('rou', r'^Operating lease right-of-use'), ('frou', r'^Finance lease right-of-use'), ('gw', r'^Goodwill$'), ('intang', r'^Intangible assets, net'),
    ('restr_lt_inv_asb', r'^Restricted long.term investments [—–-] ?Asbestos'),
    ('ins_rec_asb_nc', r'^Insurance receivables?( [—–-] ?Asbestos)?$'), ('wc_asb_nc', r'^Workers.? compensation( [—–-] ?Asbestos)?$'),
    ('dta', r'^Deferred income taxes$'), ('dta_asb', r'^Deferred income taxes [—–-] ?Asbestos$'), ('ato_deposit', r'^Deposit with Australian Taxation Office'),
    ('other_nca', r'^Other assets$'), ('ta', r'^Total assets$'),
    ('ap', r'^Accounts payable and accrued liabilities$'), ('std', r'^Short.term debt$|^Current portion of long.term debt|^Long-term debt, current portion'),
    ('std_asb', r'^Short.term debt [—–-] ?Asbestos'), ('div_payable', r'^Dividends payable'), ('accrued_payroll', r'^Accrued payroll'),
    ('lease_c', r'^Operating lease liabilities$'), ('flease_c', r'^Finance lease liabilities$'),
    ('warranty_c', r'^Accrued product warranties$'), ('tax_payable', r'^Income taxes payable$'), ('asb_liab_c', r'^Asbestos (liability|provision)$'),
    ('wc_asb_lc', r'^Workers.? compensation( [—–-] ?Asbestos)?$'), ('lhfs', r'^Liabilities held for sale$'), ('other_cl', r'^Other liabilities$'), ('tcl', r'^Total current liabilities$'),
    ('ltd', r'^Long.term debt$'), ('dtl', r'^Deferred income taxes$'), ('lease_nc', r'^Operating lease liabilities$'), ('flease_nc', r'^Finance lease liabilities$'),
    ('warranty_nc', r'^Accrued product warranties$'), ('tax_payable_nc', r'^Income taxes payable$'),
    ('asb_liab_nc', r'^Asbestos (liability|provision)$'), ('wc_asb_lnc', r'^Workers.? compensation( [—–-] ?Asbestos)?$'), ('other_ncl', r'^Other liabilities$'),
    ('tl', r'^Total liabilities$'), ('equity', r'^Total shareholders.? (equity|deficit|equity \(deficit\)|\(deficit\) equity)'), ('tle', r'^Total liabilities and shareholders'),
]
def bs_from(doc, b0, b1, per, src, mode, prior_key=None, last=False):
    """balance sheet rows between b0 and b1: labels repeat (current / non-current), so they are matched in order."""
    pos = b0
    tca_i = doc.find(r'^Total current assets$', b0, b1)
    ta_i = doc.find(r'^Total assets$', b0, b1)
    tcl_i = doc.find(r'^Total current liabilities$', b0, b1)
    tl_i = doc.find(r'^Total liabilities$', b0, b1)
    for key, pat in BS_LABELS:
        lo, hi = b0, b1
        if key in ('cash', 'restr_cash', 'restr_cash_asb', 'restr_inv_asb', 'ar', 'inv', 'prepaid', 'ins_rec_asb_c', 'wc_asb_c', 'dta_c', 'dta_asb_c', 'hfs', 'tca'):
            hi = (tca_i or b1) + 1
        elif key in ('restr_cash_nc', 'ppe', 'rou', 'frou', 'gw', 'intang', 'restr_lt_inv_asb', 'ins_rec_asb_nc', 'wc_asb_nc', 'dta', 'dta_asb', 'ato_deposit', 'other_nca', 'ta'):
            lo, hi = (tca_i or b0) + 1, (ta_i or b1) + 1
        elif key in ('ap', 'std', 'std_asb', 'div_payable', 'accrued_payroll', 'lease_c', 'flease_c', 'warranty_c', 'tax_payable', 'asb_liab_c', 'wc_asb_lc', 'lhfs', 'other_cl', 'tcl'):
            lo, hi = (ta_i or b0) + 1, (tcl_i or b1) + 1
        elif key in ('ltd', 'dtl', 'lease_nc', 'flease_nc', 'warranty_nc', 'tax_payable_nc', 'asb_liab_nc', 'wc_asb_lnc', 'other_ncl', 'tl'):
            lo, hi = (tcl_i or b0) + 1, (tl_i or b1) + 1
        else:
            lo = (tl_i or b0) + 1
        i = doc.find(pat, lo, hi)
        if i is None: continue
        v = vals(doc.lines[i])
        if not v: continue
        if last: put(per, src, 'bs', key, v[-1]); continue
        p = pick(v, mode)
        put(per, src, 'bs', key, p.get('cur'))
        if prior_key and 'prior' in p: put(prior_key, src, 'bs', key, p['prior'])
    # shares outstanding from the common stock caption
    i = doc.find(r'^Common stock', b0, b1 + 3)
    if i is not None:
        m = re.search(r'([\d,]{9,}) shares issued and outstanding at', doc.lines[i])
        if m: put(per, src, 'bs', 'shares_out', round(float(m.group(1).replace(',', '')) / 1e6, 3))

CF_LABELS = [
    ('ni', r'^Net (income|\(loss\) income|income \(loss\)|loss|Income)( \(loss\))?$'), ('dna', r'^Depreciation( and amorti[sz]ation)?$'),
    ('lease_exp', r'^Lease expense'), ('deferred_tax', r'^Deferred income taxes'), ('sbc', r'^(Stock|Share)-based compensation'),
    ('asb_adj', r'^Asbestos (adjustments|provision)'), ('impair_nc', r'^(Asset )?[Ii]mpairment( charges)?s?$'), ('gain_land', r'^Gain on sale of (land|property)'),
    ('claims_paid', r'^Claims and handling costs paid'),
    ('restr_nc', r'^Non-cash restructuring'), ('int_nc', r'^Non-cash interest'), ('stepup', r'^Non-cash charge related to step up'),
    ('cfo', r'^Net cash (provided by|used in|\(used in\) provided by|provided by \(used in\)) operating activities'),
    ('capex', r'^Purchases of property, plant and equipment'), ('ppe_proceeds', r'^Proceeds from (the )?sale of property, plant'),
    ('cap_int', r'^Capitalized interest'), ('acq', r'^(Acquisition of business|Cash consideration for The AZEK)'),
    ('asb_inv_purch', r'^Purchases? of restricted (short.term )?investments'), ('asb_inv_proc', r'^Proceeds from restricted (short.term )?investments'),
    ('cfi', r'^Net cash (used in|provided by|\(used in\) provided by|provided by \(used in\)) investing activities'),
    ('div', r'^Dividends paid'), ('buyback', r'^(Shares repurchased|Treasury stock purchased|Purchase of treasury|Repurchase of shares)'),
    ('share_iss', r'^Proceeds from (issuance of shares|exercise of vested stock options)'),
    ('cff', r'^Net cash (used in|provided by|\(used in\) provided by|provided by \(used in\)) financing activities'),
    ('fx', r'^Effects? of exchange rate'), ('net_change', r'^Net (increase|decrease|\(decrease\) increase|increase \(decrease\)|\(increase\) decrease|decrease \(increase\))'),
    ('cash_begin', r'at beginning of (period|year|the)'), ('cash_end', r'at end of (period|year|the)'),
]
def cf_anchor(doc, after):
    """(start, end) of the cash-flow statement: the 'Net income' row nearest above 'Net cash provided by operating activities'
    (the statement of changes in equity between the balance sheet and the cash flow also carries a 'Net income' row)."""
    cfo = doc.find(r'^Net cash (provided by|used in|\(used in\) provided by|provided by \(used in\)) operating activities', after)
    if cfo is None: return None, None
    c0 = None
    for j in range(cfo - 1, max(after - 1, cfo - 60), -1):
        if re.search(r'^Net (income|\(loss\) income|income \(loss\)|loss|Income)( \(loss\))?$', doc.lines[j].split(' | ')[0].strip()): c0 = j; break
    if c0 is None: return None, None
    c1 = doc.find(r'at end of (period|year)', cfo)
    return c0, c1

def cf_from(doc, c0, c1, per, pyper, src, q, last=False):
    mode = 'last' if last else 'q'
    for key, pat in CF_LABELS:
        i = doc.find(pat, c0, c1)
        if i is None: continue
        v = vals(doc.lines[i])
        if not v: continue
        p = pick(v, mode)
        put(per, src, 'cf', key, p.get('cur'))
        if pyper and 'prior' in p: put(pyper, src, 'cf', key, p['prior'])
    put(per, src, 'cf', 'ytd_months', q * 3)
    lab = doc.lines[doc.find(r'at end of (period|year)', c0, c1)].split(' | ')[0] if doc.find(r'at end of (period|year)', c0, c1) is not None else ''
    put(per, src, 'cf', 'cash_basis', 'cash+restricted+asbestos' if 'restricted' in lab.lower() else 'cash')
    # raw lines for the derived rows
    raw = []
    for j in range(c0, c1):
        l = doc.lines[j]
        if ' | ' not in l: continue
        v = vals(l)
        if v: raw.append([l.split(' | ')[0].strip(), v[0] if not last else v[-1]])
    put(per, src, 'cf', 'lines_raw', raw)
    # AICF supplemental
    i = doc.find(r'^Cash paid to AICF', c1, c1 + 20)
    if i is not None:
        v = vals(doc.lines[i]); put(per, src, 'cf', 'aicf_paid', v[0]);
        if pyper and len(v) > 1: put(pyper, src, 'cf', 'aicf_paid', v[1])

# ---------------------------------------------------------------- Management's Analysis
def ma_tables(doc, fy, q, src, has_fs):
    per, pyper = qk(fy, q), qk(fy - 1, q)
    ann, pann = str(fy), str(fy - 1)
    yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = 'qy' if q > 1 else 'q'
    # ---- summary IS table (first 'Net sales' row) — also segment net sales for FY06-FY16 formats
    i0 = locate_is(doc, need_shares=False)
    f0 = doc.find(r'^(Total )?[Nn]et [Ss]ales$')
    if i0 is None: i0 = f0
    hdr = ' '.join(doc.lines[max(0, (i0 or 0) - 6):(i0 or 0)]) if i0 is not None else ''
    annual_only = q == 4 and bool(re.search(r'Full Year Ended|Fiscal Year Ended|Years? Ended 31 March', hdr)) and not re.search(r'Three Months|Q4 FY', hdr)
    if annual_only: mode = 'q'
    ctx(fy, q, annual_only)
    if i0 is not None:
        # segment net sales rows just above Total Net Sales (FY06-FY16)
        if doc.find(r'^Total Net Sales$', 0, i0 + 1) is not None:
            t = doc.find(r'^Total Net Sales$')
            for j in range(max(0, t - 6), t):
                lab = doc.lines[j].split(' | ')[0].strip()
                for sk, pat in SEG_NAMES.items():
                    if re.search(pat, lab):
                        p = pick(vals(doc.lines[j]), mode)
                        seg_put(p, sk, 'rev', per, pyper, yt, pyt, src, q)
        i1 = i0 + 1
        while i1 < min(doc.n, i0 + 40) and (' | ' in doc.lines[i1] or (i1 + 1 < doc.n and ' | ' in doc.lines[i1 + 1] and len(doc.lines[i1].strip()) < 90 and 'Analysis of Results' not in doc.lines[i1])
                                             or re.search(r'^(Excluding|Asbestos|General Corporate):?$', doc.lines[i1].strip())): i1 += 1
        got = is_from(doc, mode, i0, i1, per, src)
        if annual_only:
            store_is(got, ann, src, pann)
            put(ann, src, 'is', 'ma_annual_only', 1)
        else:
            store_is(got, per, src, pyper, yt if q > 1 else None, pyt if q > 1 else None)
            if q == 4:   # 12-month columns = fiscal year
                for key, (p, lab) in got.items():
                    if 'ytd' in p: put(ann, src, 'is', key, p['ytd']); put(pann, src, 'is', key, p.get('ytd_prior'))
    # ---- volumes & prices (segment tables) ----
    if not (fy >= 2026 and has_fs): seg_tables(doc, fy, q, src)
    # ---- EBIT by segment / adjusted EBIT bridge ----
    ebit_bridge(doc, fy, q, src)
    # ---- net operating profit / adjusted NI bridge ----
    ni_bridge(doc, fy, q, src)
    # ---- EBITDA ----
    ebitda_bridge(doc, fy, q, src)
    # ---- adjusted tax ----
    tax_table(doc, fy, q, src)
    # ---- net interest components ----
    int_table(doc, fy, q, src)
    # ---- supplemental as-reported statements (FY06-FY13) when no FS exhibit ----
    if not has_fs:
        supp_statements(doc, fy, q, src)

CTX = {}
def ctx(fy, q, annual_only=False):
    """period keys / column mode for the MA sub-functions."""
    if annual_only:
        CTX.update(per=str(fy), pyper=str(fy - 1), yt=None, pyt=None, mode='q', q=1, ann=str(fy), pann=str(fy - 1))
    else:
        CTX.update(per=qk(fy, q), pyper=qk(fy - 1, q), yt=ytdk(fy, q), pyt=ytdk(fy - 1, q), mode='qy' if q > 1 else 'q', q=q,
                   ann=str(fy) if q == 4 else None, pann=str(fy - 1) if q == 4 else None)
    return CTX

def seg_put(p, sk, key, per, pyper, yt, pyt, src, q):
    if not p: return
    if CTX.get('per'):
        per, pyper, yt, pyt, q = CTX['per'], CTX['pyper'], CTX['yt'], CTX['pyt'], CTX['q']
    put(per, src, 'seg', f'{sk}_{key}', p.get('cur'))
    if 'prior' in p: put(pyper, src, 'seg', f'{sk}_{key}', p['prior'])
    if q > 1 and 'ytd' in p: put(yt, src, 'seg', f'{sk}_{key}', p['ytd'])
    if q > 1 and 'ytd_prior' in p: put(pyt, src, 'seg', f'{sk}_{key}', p['ytd_prior'])
    if CTX.get('ann') and 'ytd' in p: put(CTX['ann'], src, 'seg', f'{sk}_{key}', p['ytd']); put(CTX['pann'], src, 'seg', f'{sk}_{key}', p.get('ytd_prior'))

def seg_tables(doc, fy, q, src):
    """volumes / ASP / segment net sales and EBIT from the per-segment tables and the 'Volume (mmsf)' lines."""
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = CTX.get('mode', 'qy' if q > 1 else 'q')
    # old format: Volume / ASP rows labelled with the segment name (two blocks after the IS summary)
    vol_hdr = doc.find(r'^Volume \(mmsf\)$', 0, 80) or doc.findtext(r'^Volume \(mmsf\)$', 0, 80)
    if vol_hdr is not None and doc.find(r'^(USA|USA and Europe|Asia Pacific)', vol_hdr, vol_hdr + 8) is not None:
        for sk in ('na', 'apac'):
            j = doc.find(SEG_NAMES[sk], vol_hdr, vol_hdr + 8)
            if j is not None: seg_put(pick(vals(doc.lines[j]), mode), sk, 'vol', per, pyper, yt, pyt, src, q)
            j2 = doc.find(SEG_NAMES[sk], vol_hdr + 2, vol_hdr + 16, nth=1)
            if j2 is not None and re.search(r'\$', doc.lines[j2]):
                seg_put(pick(vals(doc.lines[j2]), mode), sk, 'asp', per, pyper, yt, pyt, src, q)
    # new format: segment section headings followed by a table with Volume (mmsf) / Average net sales price / Net sales / EBIT
    heads = [('na', r'^(USA (and|&) Europe Fib(re|er) Cement|North America (and|&) Europe Fib(re|er) Cement|North America Fiber Cement)( Segment)?$'), ('apac', r'^(Asia Pacific Fib(re|er) Cement|International Fiber Cement|Australia & New Zealand)( Segment)?$'),
             ('eu', r'^Europe Building Products( Segment)?$'), ('oth', r'^Other Businesses( Segment)?$'), ('rd', r'^Research and Development( Segment)?$'), ('corp', r'^General Corporate( Costs)?$')]
    for sk, pat in heads:
        h = None
        for nth in range(6):
            hh = doc.findtext(pat, 0, None, nth=nth)
            if hh is None: break
            if re.search(r'(FY ?\d\d|Q\d FY|Months Ended|Year Ended)', ' '.join(doc.lines[hh + 1:hh + 7])): h = hh; break
        if h is None:
            # heading wrapped over two lines ('Asia Pacific Fiber' / 'Cement Segment', Q3 FY16)
            for i in range(doc.n - 1):
                a, b = doc.lines[i].strip(), doc.lines[i + 1].strip()
                if ' | ' in a or ' | ' in b or not a or len(a) > 40: continue
                if re.search(pat, a + ' ' + b) and re.search(r'(FY ?\d\d|Q\d FY|Months Ended|Year Ended)', ' '.join(doc.lines[i + 2:i + 8])): h = i + 1; break
        if h is None: continue
        end = h + 45
        tv = doc.find(r'^Volume \(mmsf\)( excluding)?', h, end)
        if tv is not None and doc.lines[tv].count(' | ') >= 2:
            seg_put(pick(vals(doc.lines[tv]), mode), sk, 'vol', per, pyper, yt, pyt, src, q)
        ta = doc.find(r'^Average net sales price per unit', h, end)
        if ta is not None:
            l = doc.lines[ta]
            ccy = 'AUD' if 'A$' in l else 'USD'
            seg_put(pick(vals(l), mode), sk, 'asp', per, pyper, yt, pyt, src, q)
            put(per, src, 'seg', f'{sk}_asp_ccy', ccy)
        rows_ = [('rev', r'^(Net [Ss]ales( \(US\$ Millions\))?|Fiber cement net sales)$'), ('fg_rev', r'^Fiber gypsum net sales'), ('rev_total', r'^Net sales$'),
                 ('ebit', r'^(EBIT( \(US\$ Millions\))?|EBIT \d)$'), ('ebit_ex', r'^EBIT excluding')]
        if sk == 'rd': rows_ = [('ebit', r'^Total R&D EBIT$')]
        # corporate: the section's 'General Corporate EBIT' includes the asbestos adjustments (FY14-FY18 formats); the segment EBIT
        # table's 'General Corporate' row (ex asbestos) is the corp_ebit used, so the section total is kept separately
        if sk == 'corp': rows_ = [('ebit_incl_asb', r'^General Corporate EBIT$'), ('sga', r'^General Corporate SG&A expenses$')]
        for key, rp in rows_:
            tj = doc.find(rp, h, (h + 12) if sk in ('rd', 'corp') else end)
            if tj is None: continue
            l = doc.lines[tj]
            if 'A$' in l or '(A$' in doc.lines[max(0, tj - 6)]: pass
            v = vals(l)
            if key == 'rev' and sk == 'eu' and doc.find(r'^Fiber gypsum net sales', h, end) is not None:
                # Europe: fibre cement + fibre gypsum = net sales
                seg_put(pick(v, mode), sk, 'fc_rev', per, pyper, yt, pyt, src, q)
                tn = doc.find(r'^Net sales$', tj, end)
                if tn is not None: seg_put(pick(vals(doc.lines[tn]), mode), sk, 'rev', per, pyper, yt, pyt, src, q)
                continue
            if key == 'rev_total': continue
            seg_put(pick(v, mode), sk, key, per, pyper, yt, pyt, src, q)
        # local-currency table (A$ Millions / € Millions) directly after
        for ccy, cpat in [('AUD', r'^A\$ Millions'), ('EUR', r'^€ Millions')]:
            tc = doc.find(cpat, h, end + 20)
            if tc is not None and sk in ('apac', 'eu'):
                tn = doc.find(r'^(Net [Ss]ales( \(A\$ Millions\))?|Fiber cement net sales)$', tc, tc + 12)
                if tn is not None:
                    l = doc.lines[tn]
                    seg_put(pick(vals(l), mode), sk, 'rev_lc', per, pyper, yt, pyt, src, q)
                    if sk == 'eu':
                        tn2 = doc.find(r'^Net sales$', tn, tc + 12)
                        if tn2 is not None: seg_put(pick(vals(doc.lines[tn2]), mode), sk, 'rev_lc', per, pyper, yt, pyt, src, q)
        # FY16 style: Net Sales (A$ Millions) inside the same block
        tn = doc.find(r'^Net Sales \(A\$ Millions\)', h, end)
        if tn is not None: seg_put(pick(vals(doc.lines[tn]), mode), sk, 'rev_lc', per, pyper, yt, pyt, src, q)

def annual_block(doc, i, q):
    """True when a Q4-package table at line i has fiscal-year columns only (FY 2006 | FY 2005) rather than Q4 + FY."""
    if q != 4: return False
    hdr = ' '.join(doc.lines[max(0, i - 6):i])
    return bool(re.search(r'(FY ?20\d\d \| FY ?20\d\d|Full Year|Twelve Months|Years? Ended)', hdr)) and not re.search(r'(Three Months|Q4|Fourth Quarter)', hdr)

def put_items(key, items, src, per):
    """bridge items under the block's period; a Q4 | Q4 py | FY | FY py block also gives the fiscal-year items (ytd columns)."""
    put(per, src, 'ng', key, items)
    if CTX.get('ann') and any(it[3] is not None for it in items):
        put(CTX['ann'], src, 'ng', key, [[it[0], it[3], it[4], None, None] for it in items])
        if CTX.get('pann') and any(it[4] is not None for it in items):
            put(CTX['pann'], src, 'ng', key, [[it[0], it[4], None, None, None] for it in items])
    # prior-year comparative column (fills periods whose own package had no bridge, e.g. Q4 FY25 from the Q4 FY26 release)
    if CTX.get('pyper') and any(it[2] is not None for it in items):
        put(CTX['pyper'], src, 'ng', key, [[it[0], it[2], None, it[4], None] for it in items])

def with_block_ctx(doc, i, fy, q):
    """switch CTX to annual keys for an annual-only block in a Q4 package; returns the previous CTX copy."""
    old = dict(CTX)
    if annual_block(doc, i, q) and not CTX.get('ann_only'):
        ctx(fy, q, True); CTX['ann_only'] = True
    return old

def ebit_bridge(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = CTX.get('mode', 'qy' if q > 1 else 'q')
    # segment EBIT table: starts at a segment row and ends at 'EBIT' or 'Adjusted EBIT'
    napat = SEG_NAMES['na'][:-1] + r'( excluding[^|]*)?$'
    starts = [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(napat, doc.lines[i].split(' | ')[0].strip())]
    done = False
    seen_kinds = set()
    for s in starts:
        old = with_block_ctx(doc, s, fy, q)
        kind_ = 'A' if CTX.get('ann_only') else 'Q'
        if kind_ in seen_kinds: CTX.clear(); CTX.update(old); continue
        blk = doc.block(napat, r'^(EBIT|Adjusted EBIT|EBIT excluding[^|]*)$', s, s + 1, CTX.get('mode', mode), maxrows=22)
        if not blk: CTX.clear(); CTX.update(old); continue
        labs = [b[0] for b in blk]
        if not any(re.search(r'^(EBIT|Adjusted EBIT)$', l) for l in labs): continue
        if any(re.search(r'Total Net Sales|Cost of goods sold|Gross profit|Fiber cement revenues|Worldwide total', l) for l in labs): continue
        for lab, p, j in blk:
            for sk, pat in SEG_NAMES.items():
                if re.search(pat, lab.strip()): seg_put(p, sk, 'ebit', per, pyper, yt, pyt, src, q)
                elif re.search(pat[:-1] + r' excluding', lab.strip()): seg_put(p, sk, 'ebit_ex', per, pyper, yt, pyt, src, q); put(CTX.get('per', per), src, 'seg', f'{sk}_ebit_ex_label', lab.strip())
            if re.search(r'^Adjusted EBIT$', lab): seg_put(p, 'tot', 'adj_ebit', per, pyper, yt, pyt, src, q)
            if re.search(r'^EBIT$', lab): seg_put(p, 'tot', 'ebit', per, pyper, yt, pyt, src, q)
            if re.search(r'^Asbestos adjustments', lab): seg_put(p, 'tot', 'asb_adj_in_ebit', per, pyper, yt, pyt, src, q)
            if re.search(r'^AICF SG&A', lab): seg_put(p, 'tot', 'aicf_sga_in_ebit', per, pyper, yt, pyt, src, q)
        # items between the first total and the second total (EBIT -> Adjusted EBIT or Adjusted EBIT -> EBIT)
        items = []
        seen_total = 0
        for lab, p, j in blk:
            if re.search(r'^(EBIT|Adjusted EBIT|EBIT excluding[^|]*)$', lab): seen_total += 1; continue
            if seen_total == 1 and 'cur' in p: items.append([lab, p.get('cur'), p.get('prior'), p.get('ytd'), p.get('ytd_prior')])
        if items: put_items('ebit_items', items, src, CTX.get('per', per))
        done = True
        seen_kinds.add(kind_)
        CTX.clear(); CTX.update(old)
        if q != 4 or fy > 2008: break
    # the clean definitions-section bridge: EBIT -> [items] -> Adjusted EBIT / EBIT excluding asbestos ...
    # segment sections (FY19-FY21) carry their own 'EBIT -> impairments -> EBIT excluding 1' tables, so a block that ends in
    # 'Adjusted EBIT' wins; 'EBIT excluding ...' only stands for the group bridge in the FY06-FY13 formats that had no Adjusted EBIT
    cands = []
    for s in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(r'^EBIT$', doc.lines[i].split(' | ')[0].strip())]:
        e = doc.find(r'^(Adjusted EBIT|EBIT excluding[^|]*)$', s, s + 12)
        if e is None: continue
        # FY21-FY23 Q4 packages: fiscal-year summary context, but the definitions bridge is Q4 | Q4 py | FY | FY py
        isq4 = q == 4 and CTX.get('mode') == 'q' and len(vals(doc.lines[e])) >= 4 and fy > 2008
        blk = doc.block(r'^EBIT$', r'^(Adjusted EBIT|EBIT excluding[^|]*)$', s, s + 1, 'qy' if isq4 else mode, maxrows=12)
        if not blk or not re.search(r'^(Adjusted EBIT|EBIT excluding)', blk[-1][0]): continue
        labs = ' '.join(b[0] for b in blk)
        if re.search(r'EBIT margin', labs): continue                       # segment-section table
        cands.append((0 if re.search(r'^Adjusted EBIT$', blk[-1][0]) else 1, 0 if re.search(r'Asbestos', labs) else 1, blk, isq4))
    cands.sort(key=lambda c: c[:2])
    if cands and re.search(r'^EBIT excluding', cands[0][2][-1][0]) and doc.find(r'^Adjusted EBIT$') is not None: cands = []
    for _, _, blk, isq4 in cands[:1]:
        old = dict(CTX)
        if isq4: ctx(fy, q, False)
        items = [[lab, p.get('cur'), p.get('prior'), p.get('ytd'), p.get('ytd_prior')] for lab, p, j in blk[1:-1] if 'cur' in p and not re.search(r'^Excluding|^Asbestos:$', lab)]
        lab, p, j = blk[-1]
        seg_put(p, 'tot', 'adj_ebit', per, pyper, yt, pyt, src, q)
        put(CTX.get('per', per), src, 'ng', 'adj_ebit_label', lab)
        put_items('ebit_items_def', items, src, CTX.get('per', per))
        if CTX.get('ann') and 'ytd' in p: put(CTX['ann'], src, 'ng', 'adj_ebit_label', lab)
        CTX.clear(); CTX.update(old)

NI_START = r'^(Net operating profit|Net operating \(loss\) profit|Net operating profit \(loss\)|Net income|Net \(loss\) income|Net income \(loss\)|Net income \(loss\) from continuing operations|Net income from continuing operations)( \(loss\))?$'
NI_END = r'^(Adjusted net operating profit|Net operating profit excluding[^|]*|Net operating profit \(loss\) excluding[^|]*|Adjusted net income|Adjusted Net Income)$'
def ni_bridge(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = CTX.get('mode', 'qy' if q > 1 else 'q')
    per = CTX.get('per', per)
    best = None; best_ann = None; best_q4 = None
    for s in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(NI_START, doc.lines[i].split(' | ')[0].strip())]:
        isann = annual_block(doc, s, q) and fy <= 2008
        # Q4 packages whose summary tables are fiscal-year only (FY21-FY23) still carry a Q4 | Q4 py | FY | FY py bridge:
        # a bridge whose total row has 4+ numeric tokens is a quarterly table whatever the package context says.
        e = doc.find(NI_END, s, s + 20)
        isq4 = q == 4 and CTX.get('mode') == 'q' and e is not None and len(vals(doc.lines[e])) >= 4 and fy > 2008
        blk = doc.block(NI_START, NI_END, s, s + 1, 'q' if isann else ('qy' if isq4 else mode), maxrows=20)
        if not blk or not re.search(NI_END, blk[-1][0]): continue
        if isann:
            if best_ann is None or len(blk) > len(best_ann): best_ann = blk
        elif isq4:
            if best_q4 is None or len(blk) > len(best_q4): best_q4 = blk
        elif best is None or len(blk) > len(best): best = blk
    for best, isann, isq4 in ((best, False, False), (best_ann, True, False), (best_q4, False, True)):
      if not best: continue
      old = dict(CTX)
      if isann: ctx(fy, q, True)
      if isq4: ctx(fy, q, False); mode = 'qy'; per = CTX['per']
      if True:
          items = [[lab, p.get('cur'), p.get('prior'), p.get('ytd'), p.get('ytd_prior')] for lab, p, j in best[1:-1] if 'cur' in p and not re.search(r'^Excluding|^Asbestos:$', lab)]
          lab, p, j = best[-1]
          seg_put(p, 'tot', 'adj_ni', per, pyper, yt, pyt, src, q)
          put(per, src, 'ng', 'adj_ni_label', lab)
          put_items('ni_items', items, src, per)
          if CTX.get('ann') and 'ytd' in p: put(CTX['ann'], src, 'ng', 'adj_ni_label', lab)
          # adjusted EPS and diluted shares (rows after the bridge)
          epat = r'^(Adjusted diluted earnings per share|Diluted earnings per share excluding[^|]*|Adjusted Diluted Earnings Per Share)'
          wpat = r'^Weighted average common shares outstanding'
          ntok = len(vals(doc.lines[j]))
          same_shape = lambda k: (len(vals(doc.lines[k])) >= 4) == (ntok >= 4)     # a Q4|Q4py|FY|FYpy bridge must not take a FY|FYpy EPS row
          e = doc.find(epat, j, j + 40)
          if e is not None and not same_shape(e): e = None
          if e is None and not isann:       # the definitions section repeats the bridge with the same columns
              for k in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(epat, doc.lines[i].split(' | ')[0].strip())]:
                  if same_shape(k): e = k; break
          if e is not None:
              l = doc.lines[e]; p2 = pick(vals(l), mode)
              if 'cents' in l.lower(): p2 = {k: round(x / 100.0, 4) for k, x in p2.items()}
              seg_put(p2, 'tot', 'adj_eps', per, pyper, yt, pyt, src, q)
          w = doc.find(wpat, j, j + 40)
          if w is not None and not same_shape(w): w = None
          if w is None and not isann:
              for k in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(wpat, doc.lines[i].split(' | ')[0].strip())]:
                  if same_shape(k) and vals(doc.lines[k]) and vals(doc.lines[k])[0] > 100: w = k; break
          if w is not None: seg_put(pick(vals(doc.lines[w]), mode), 'tot', 'adj_sh_d', per, pyper, yt, pyt, src, q)
      CTX.clear(); CTX.update(old)

def ebitda_bridge(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = CTX.get('mode', 'qy' if q > 1 else 'q')
    per = CTX.get('per', per)
    for s in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(r'^(EBIT|Net income|Net income \(loss\) from continuing operations|Net \(loss\) income|Net income \(loss\))$', doc.lines[i].split(' | ')[0].strip())]:
        j = doc.find(r'^Depreciation and amorti[sz]ation$', s, s + 8)
        if j is None: continue
        old = with_block_ctx(doc, s, fy, q)                 # Q4 packages: a 'FY 2014 | FY 2013' table is annual
        mode = CTX.get('mode', mode); per = CTX.get('per', per)
        blk = doc.block(r'^(EBIT|Net income|Net income \(loss\) from continuing operations|Net \(loss\) income|Net income \(loss\))$', r'^(Adjusted EBITDA( excluding Asbestos)?|EBITDA)$', s, s + 1, mode, maxrows=16)
        if not blk or not re.search(r'EBITDA', blk[-1][0]): CTX.clear(); CTX.update(old); continue
        for lab, p, k in blk:
            if re.search(r'^Depreciation and amorti', lab): seg_put(p, 'tot', 'dna', per, pyper, yt, pyt, src, q)
            if re.search(r'^EBITDA$', lab): seg_put(p, 'tot', 'ebitda', per, pyper, yt, pyt, src, q)
            if re.search(r'^Adjusted EBITDA$', lab): seg_put(p, 'tot', 'adj_ebitda', per, pyper, yt, pyt, src, q)
            if re.search(r'^Adjusted EBITDA excluding Asbestos$', lab): seg_put(p, 'tot', 'adj_ebitda_ex_asb', per, pyper, yt, pyt, src, q)
        items = [[lab, p.get('cur'), p.get('prior'), p.get('ytd'), p.get('ytd_prior')] for lab, p, k in blk[1:] if 'cur' in p and not re.search(r'EBITDA$', lab)]
        put(per, src, 'ng', 'ebitda_items', items)
        # continuation: Adjusted EBITDA -> excluding asbestos
        k = blk[-1][2]
        if re.search(r'^Adjusted EBITDA$', blk[-1][0]):
            x = doc.find(r'^Adjusted EBITDA excluding Asbestos$', k, k + 6)
            if x is not None: seg_put(pick(vals(doc.lines[x]), mode), 'tot', 'adj_ebitda_ex_asb', per, pyper, yt, pyt, src, q)
        CTX.clear(); CTX.update(old)
        break

def tax_table(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = CTX.get('mode', 'qy' if q > 1 else 'q')
    for key, pat in [('adj_tax', r'^Adjusted income tax expense|^Income tax expense excluding'), ('adj_etr', r'^(Adjusted effective tax rate|Effective tax rate excluding)'),
                     ('adj_ebt', r'^(Adjusted (operating profit|income) before income taxes|Operating profit before income taxes excluding)')]:
        i = doc.find(pat)
        if i is not None:
            l = doc.lines[i]
            v = vals(l)
            seg_put(pick(v, mode), 'tot', key, per, pyper, yt, pyt, src, q)

def int_table(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = CTX.get('mode', 'qy' if q > 1 else 'q')
    for key, pat in [('gross_int', r'^Gross interest expense'), ('cap_int', r'^Capitali[sz]ed [Ii]nterest'), ('int_inc', r'^Interest income$'),
                     ('aicf_int', r'^Net AICF interest|^AICF interest (income|expense)')]:
        i = doc.find(pat)
        if i is not None: seg_put(pick(vals(doc.lines[i]), mode), 'tot', key, per, pyper, yt, pyt, src, q)

def supp_statements(doc, fy, q, src):
    """FY2006-FY2013 MA documents: 'Fibre Cement ex-asbestos | Asbestos | As Reported' supplemental statements (year to date)."""
    ann = str(fy) if q == 4 else None
    per = ann or ytdk(fy, q)
    s = doc.findtext(r'^(Consolidated Balance Sheet|Condensed Consolidated Balance Sheet)', 0)
    b0 = doc.find(r'^Cash and cash equivalents$', s or 0)
    b1 = doc.find(r'^Total liabilities\s*(and|&) shareholders', b0) if b0 is not None else None
    if b0 is not None and b1 is not None and doc.lines[b0].count(' | ') >= 2:
        bs_from(doc, b0, b1 + 1, str(fy) if q == 4 else qk(fy, q), src, 'last', last=True)
    c0 = doc.find(r'^Net [Ii]ncome( \(loss\))?$', (b1 or 0))
    c1 = doc.find(r'^Cash and cash equivalents at end of (period|year)', c0) if c0 is not None else None
    if c0 is not None and c1 is not None and doc.lines[c0].count(' | ') >= 2:
        cf_from(doc, c0, c1 + 1, per, None, src, q, last=True)
    # as-reported IS (12-month) for the annual records
    if q == 4:
        i0 = doc.find(r'^(Total )?Net Sales$', (b1 or 0), c0 or doc.n)
        if i0 is not None and doc.lines[i0].count(' | ') >= 2:
            got = is_from(doc, 'last', i0, i0 + 25, str(fy), src)
            store_is(got, str(fy), src, sec='is_supp')

# ---------------------------------------------------------------- financial-statement notes (fpages era)
def fs_notes(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = 'qy' if (q > 1 and q < 4) else 'q'
    ctx(fy, q, annual_only=(q == 4))
    seg_columns_note(doc, fy, q, src)
    # segment net sales & operating income tables (note: 'Worldwide total' / 'Total operating income')
    for key, endpat in [('rev', r'^(Worldwide total|Total( net sales| revenues)?)$'), ('ebit', r'^(Total operating income|Total EBIT|Total operating income \(loss\)|Segment operating income)$')]:
        for s in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(SEG_NAMES['na'], doc.lines[i].split(' | ')[0].strip())]:
            blk = doc.block(SEG_NAMES['na'], endpat, s, s + 1, mode, maxrows=12)
            if not blk or not re.search(endpat, blk[-1][0]): continue
            labs = [b[0] for b in blk]
            if key == 'ebit' and not any(re.search(r'General Corporate|Research', l) for l in labs): continue
            if key == 'rev' and any(re.search(r'General Corporate|Research', l) for l in labs): continue
            if key == 'rev' and 'ebit' in ' '.join(labs).lower(): continue
            if len(set(labs)) < len(labs): continue
            if key == 'ebit' and any(re.search(r'Worldwide total|Total net sales|Total revenues', l) for l in labs): continue
            for lab, p, j in blk:
                for sk, pat in SEG_NAMES.items():
                    if re.search(pat, lab.strip()): seg_put(p, sk, key + '_fs', per, pyper, yt, pyt, src, q if q < 4 else 1)
            break
    # diluted shares, dividends declared per share, SBC, D&A by segment
    i = doc.find(r'^Diluted common shares outstanding')
    if i is not None: seg_put(pick(vals(doc.lines[i]), mode), 'tot', 'sh_d_note', per, pyper, yt, pyt, src, q if q < 4 else 1)

# ---------------------------------------------------------------- column-style segment note (FY23+ financial statements, 10-K / 10-Q, annual reports)
MONTHS = {'march': 3, 'june': 6, 'september': 9, 'december': 12}
def period_from_heading(txt):
    m = re.search(r'(three|six|nine|twelve) months ended (\d{1,2} )?(March|June|September|December)( \d{1,2},?)? (\d{4})|(year|years) ended (\d{1,2} )?(March)( \d{1,2},?)? (\d{4})', txt, re.I)
    if not m: return None
    if m.group(1):
        span, mon, yr = m.group(1).lower(), m.group(3).lower(), int(m.group(5))
    else:
        span, mon, yr = 'year', 'march', int(m.group(10))
    mm = MONTHS[mon]; fy = yr + (1 if mm > 3 else 0); q = {6: 1, 9: 2, 12: 3, 3: 4}[mm]
    if span == 'three': return qk(fy, q)
    if span == 'six': return f'H1-{str(fy)[2:]}'
    if span == 'nine': return f'9M-{str(fy)[2:]}'
    return str(fy)

SEG_COL = {'na': r'^(North America Fiber Cement|Siding & Trim)$', 'dra': r'^Deck, Rail & Accessories$', 'apac': r'^(Asia Pacific Fiber Cement|Australia & New Zealand)$',
           'eu': r'^(Europe Building Products|Europe)$', 'oth': r'^Other Businesses$'}
def seg_columns_note(doc, fy, q, src):
    for i in range(doc.n):
        l = doc.lines[i]
        if not l.startswith('(Millions of US dollars) | ') and not l.startswith('(Millions of U.S. dollars) | '): continue
        cols = [c.strip() for c in l.split(' | ')[1:]]
        keys = []
        for c in cols:
            k = next((sk for sk, pat in SEG_COL.items() if re.search(pat, c)), 'tot' if re.search(r'^(Total|Consolidated)$', c) else None)
            keys.append(k)
        if sum(1 for k in keys if k and k != 'tot') < 2: continue
        # period heading: the line above (FY23 revenue note) or the lines below ('For the ... ended ...')
        per = period_from_heading(' '.join(doc.lines[max(0, i - 2):i]))
        j = i + 1
        while j < doc.n and j < i + 80:
            lj = doc.lines[j]
            if lj.startswith('(Millions of U') : break
            pj = period_from_heading(lj) if ' | ' not in lj else None
            if pj: per = pj; j += 1; continue
            if ' | ' in lj and per:
                lab = lj.split(' | ')[0].strip(); v = vals(lj)
                key = None
                if re.search(r'^(Net sales|Total revenues)$', lab): key = 'rev'
                elif re.search(r'^Segment operating income( \(loss\))?$|^Operating income( \(loss\))?$', lab): key = 'ebit'
                elif re.search(r'^Fiber cement revenues', lab): key = 'fc_rev'
                elif re.search(r'^Fiber gypsum revenues', lab): key = 'fg_rev'
                elif re.search(r'General Corporate', lab) and v: put(per, src, 'seg', 'corp_ebit_fs', v[0]); j += 1; continue
                elif re.search(r'^Consolidated operating income', lab) and v: put(per, src, 'seg', 'op_fs', v[0]); j += 1; continue
                if key and len(v) == len(keys):
                    for k, x in zip(keys, v):
                        if k: put(per, src, 'seg', f'{k}_{key}_fs', x)
            j += 1

def mr_tables(doc, fy, q, src):
    """Q4 FY21-FY24 media releases: quarterly net sales / adjusted EBIT / adjusted net income for the group and segments."""
    if q != 4: return
    ctx(fy, 4)
    group = None
    for i in range(doc.n):
        l = doc.lines[i]
        if ' | ' not in l:
            t = l.strip()
            for sk, pat in [('na', r'^North America Fiber Cement'), ('apac', r'^Asia Pacific Fiber Cement'), ('eu', r'^Europe Building Products'), ('tot', r'^(Group|Consolidated|Q4 FY)')]:
                if re.search(pat, t): group = sk
            continue
        lab = l.split(' | ')[0].strip()
        if re.search(r'^Q4 FY\d\d \| Q4 FY', l): group = 'tot'; continue
        if group is None: continue
        v = vals(l)
        if len(v) < 4: continue
        key = {'Net Sales': 'rev', 'Adjusted EBIT': 'adj_ebit', 'Adjusted Net Income': 'adj_ni', 'EBIT': 'ebit', 'Adjusted EBITDA': 'adj_ebitda',
               'Adjusted Diluted EPS - US$ per share': 'adj_eps', 'Operating Cash Flow': None}.get(lab)
        if not key: continue
        if key in ('adj_ebitda', 'adj_eps') and group != 'tot': continue
        lc = ('A$' in l or '€' in l)
        p = pick(v, 'qy')
        seg_put(p, group, key + ('_lc' if lc and key == 'rev' else '') + '_mr', None, None, None, None, src, 4)
    CTX.clear()

# ---------------------------------------------------------------- earnings release (Q4 FY26 onward: 8-K Ex. 99.1) and Q1-Q3 FY26 ER exhibits
def er_tables(doc, fy, q, src):
    per, pyper = qk(fy, q), qk(fy - 1, q); yt, pyt = ytdk(fy, q), ytdk(fy - 1, q)
    mode = 'qy' if q > 1 else 'q'
    ctx(fy, q)
    # IS
    i0 = locate_is(doc)
    if i0 is not None:
        i1 = is_end(doc, i0)
        got = is_from(doc, mode, i0, i1, per, src)
        store_is(got, per, src, pyper, yt if q > 1 else None, pyt if q > 1 else None)
        if q == 4:
            for key, (p, lab) in got.items():
                if 'ytd' in p: put(str(fy), src, 'is', key, p['ytd']); put(str(fy - 1), src, 'is', key, p.get('ytd_prior'))
        for key, p in shares_rows(doc, i0, i1, mode, per, pyper, yt, pyt):
            put(per, src, 'is', key, p['cur']); put(pyper, src, 'is', key, p.get('prior'))
            if q > 1: put(yt, src, 'is', key, p.get('ytd')); put(pyt, src, 'is', key, p.get('ytd_prior'))
            if q == 4: put(str(fy), src, 'is', key, p.get('ytd')); put(str(fy - 1), src, 'is', key, p.get('ytd_prior'))
    # BS
    b0 = doc.find(r'^Cash and cash equivalents$')
    b1 = doc.find(r'^Total liabilities and shareholders', b0) if b0 is not None else None
    if b0 is not None and b1 is not None:
        bs_from(doc, b0, b1 + 1, qk(fy, q) if q < 4 else str(fy), src, 'q', prior_key=(str(fy - 1) if q == 4 else None))
    # CF (YTD)
    c0, c1 = cf_anchor(doc, (b1 or 0))
    if c0 is not None and c1 is not None:
        cf_from(doc, c0, c1 + 1, yt, pyt, src, q)
    # segments (summary tables): heading line 'Siding & Trim | (US$ millions)' etc.
    heads = [('na', r'^(North America Fiber Cement|Siding & Trim)$'), ('dra', r'^Deck, Rail & Accessories$'), ('apac', r'^(Asia Pacific Fiber Cement|Australia & New Zealand)$'), ('eu', r'^(Europe Building Products|Europe)$')]
    for sk, pat in heads:
      hs = [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(pat, doc.lines[i].split(' | ')[0].strip()) and 'millions' in doc.lines[i].lower()]
      if not hs:
          hs = [i for i in range(doc.n) if ' | ' not in doc.lines[i] and re.search(pat, doc.lines[i].strip()) and re.search(r'^(Q\d FY\d\d \||FY\d\d \| FY\d\d)', ' '.join(doc.lines[i + 1:i + 4]), re.M)]
      for h in hs[:2]:
        # the nearest column header above the table decides: 'Q4 FY25 | Q4 FY24 ...' (quarter) or 'FY25 | FY24 ...' (fiscal year)
        annual_tbl = False
        for k in range(h, max(0, h - 40), -1):
            if re.search(r'Q\d FY\d\d \|', doc.lines[k]): break
            if re.search(r'^FY\d\d \| FY\d\d', doc.lines[k].strip()): annual_tbl = q == 4; break
        ctx(fy, q, annual_tbl)
        # Deck, Rail & Accessories in FY26 (acquired 1-Jul-2025): the table has no prior-year columns ('Q2 FY26 | 6 Months FY26',
        # 'Q4 FY26 | FY26'); its two tokens are current quarter and year-to-date, not current and prior
        hdr_line = ' '.join(doc.lines[max(0, h - 3):h + 1])
        no_prior = bool(re.search(r'Q\d FY\d\d \| (\d Months |9 Months |6 Months )?FY\d\d\b', hdr_line)) and not re.search(r'FY%02d' % ((fy - 1) % 100), hdr_line)
        end = h + 14
        for key, rp in [('rev', r'^Net [Ss]ales$'), ('rev_lc', r'^Net Sales \((A\$|€)( millions)?\)'), ('ebit', r'^(Operating Income( \(Loss\))?|Operating Loss|EBIT)$'),
                        ('adj_ebit', r'^Adjusted EBIT$'), ('adj_ebitda', r'^(Adjusted EBITDA|EBITDA)$')]:
            tj = doc.find(rp, h, end)
            if tj is None: continue
            v = vals(doc.lines[tj])
            if key == 'rev_lc' and len(v) <= 1: continue
            # FY25-era: US$ then A$/€ columns side by side (cur, prior, change, cur_lc, prior_lc, change)
            if len(v) >= 6 and sk in ('apac', 'eu') and fy <= 2025 and key != 'rev_lc' and re.search(r'\((A\$|€) millions\)', ' '.join(doc.lines[h:h + 2])):
                seg_put({'cur': v[0], 'prior': v[1]}, sk, key, per, pyper, yt, pyt, src, 1)
                seg_put({'cur': v[3], 'prior': v[4]}, sk, 'rev_lc' if key == 'rev' else key + '_lc', per, pyper, yt, pyt, src, 1)
                continue
            if no_prior and q > 1:
                p = {'cur': v[0]} if len(v) == 1 else {'cur': v[0], 'ytd': v[1]}
                if len(v) >= 2:
                    put(per, src, 'seg', f'{sk}_{key}', v[0]); put(yt, src, 'seg', f'{sk}_{key}', v[1])
                    if q == 4: put(str(fy), src, 'seg', f'{sk}_{key}', v[1])
                else: put(per, src, 'seg', f'{sk}_{key}', v[0])
                continue
            p = pick(v, CTX['mode'])
            seg_put(p, sk, key, per, pyper, yt, pyt, src, q)
      ctx(fy, q)
    # non-GAAP bridges
    ni_bridge(doc, fy, q, src); ebitda_bridge(doc, fy, q, src); tax_table(doc, fy, q, src)
    # group adjusted EBITDA / adjusted net income headline rows (first summary table)
    # FY26+ releases: one group table with quarter and year-to-date columns; the FY25 release has a Q4 table and a separate FY table
    for key, rp in [('adj_ebitda', r'^Adjusted EBITDA$'), ('adj_ni', r'^Adjusted Net Income$'), ('adj_eps', r'^Adjusted Diluted (Earnings Per Share|EPS)'), ('adj_ebit', r'^Adjusted EBIT$'),
                    ('ebit', r'^EBIT$')]:
        seen = set()
        for i in [k for k in range(doc.n) if ' | ' in doc.lines[k] and re.search(rp, doc.lines[k].split(' | ')[0].strip())]:
            hdr = '\n'.join(doc.lines[max(0, i - 16):i])
            grp = re.search(r'^Group \|', hdr, re.M) or re.search(r'\(US\$ millions, except per share', hdr) or i < 80
            if not grp: continue
            tbl = 'FY' if (q == 4 and re.search(r'^FY\d\d \| FY\d\d', hdr, re.M) and not re.search(r'Q4 FY\d\d \| Q4 FY', hdr)) else 'Q'
            if tbl in seen: continue
            seen.add(tbl)
            v = vals(doc.lines[i])
            if tbl == 'FY':
                put(str(fy), src, 'seg', f'tot_{key}_hl', v[0]); put(str(fy - 1), src, 'seg', f'tot_{key}_hl', v[1] if len(v) > 1 else None)
                continue
            p = pick(v, mode)
            seg_put(p, 'tot', key + '_hl', per, pyper, yt, pyt, src, q)
            if q == 4 and 'ytd' in p: put(str(fy), src, 'seg', f'tot_{key}_hl', p['ytd']); put(str(fy - 1), src, 'seg', f'tot_{key}_hl', p.get('ytd_prior'))
    # segment adjusted EBITDA reconciliation tables
    for sk, pat in [('na', r'^(North America Fiber Cement|Siding & Trim) Segment operating income'), ('dra', r'^Deck, Rail & Accessories( Segment)? operating (income|loss)'),
                    ('apac', r'^(Asia Pacific Fiber Cement|Australia & New Zealand) Segment operating income'), ('eu', r'^Europe( Building Products)? Segment operating income')]:
        s = doc.find(pat)
        if s is None: continue
        blk = doc.block(pat, r'(Adjusted EBITDA|EBITDA)$', s, s + 1, mode, maxrows=12)
        if not blk: continue
        for lab, p, j in blk:
            if re.search(r'^Depreciation and amortization', lab): seg_put(p, sk, 'dna', per, pyper, yt, pyt, src, q)
            if re.search(r'^Amortization of intangible assets resulting from AZEK', lab): seg_put(p, sk, 'azek_amort', per, pyper, yt, pyt, src, q)
            if re.search(r'EBITDA$', lab) and j != s: seg_put(p, sk, 'adj_ebitda_rec', per, pyper, yt, pyt, src, q)
        if q == 4:
            for lab, p, j in blk:
                if 'ytd' in p:
                    k = 'dna' if lab.startswith('Depreciation') else 'azek_amort' if lab.startswith('Amortization of intangible') else 'adj_ebitda_rec' if lab.endswith('EBITDA') and j != s else None
                    if k: put(str(fy), src, 'seg', f'{sk}_{k}', p['ytd']); put(str(fy - 1), src, 'seg', f'{sk}_{k}', p.get('ytd_prior'))
    # corporate
    s = doc.find(r'^General Corporate (and Unallocated R&D )?costs')
    if s is not None:
        p = pick(vals(doc.lines[s]), mode); seg_put(p, 'corp', 'ebit', per, pyper, yt, pyt, src, q)
        if q == 4 and 'ytd' in p: put(str(fy), src, 'seg', 'corp_ebit', p['ytd']); put(str(fy - 1), src, 'seg', 'corp_ebit', p.get('ytd_prior'))
        a = doc.find(r'^Adjusted General Corporate', s, s + 10)
        if a is not None:
            p = pick(vals(doc.lines[a]), mode); seg_put(p, 'corp', 'adj_ebitda', per, pyper, yt, pyt, src, q)
            if q == 4 and 'ytd' in p: put(str(fy), src, 'seg', 'corp_adj_ebitda', p['ytd']); put(str(fy - 1), src, 'seg', 'corp_adj_ebitda', p.get('ytd_prior'))
    # FCF published
    f = doc.find(r'^Free Cash Flow$')
    if f is not None:
        v = vals(doc.lines[f])
        put(yt, src, 'cf', 'fcf_pub', v[0])
        if len(v) > 1: put(pyt, src, 'cf', 'fcf_pub', v[1])

# ---------------------------------------------------------------- annual report / 20-F (fiscal-year statements, segment notes)
def iar_tables(doc, fy, src):
    ann, pann = str(fy), str(fy - 1)
    i0 = locate_is(doc)
    if i0 is None: return
    i1 = i0 + 50
    got = is_from(doc, 'q', i0, i1, ann, src)
    store_is(got, ann, src, pann)
    for key, p in shares_rows(doc, i0, i1, 'q', ann, pann, None, None):
        put(ann, src, 'is', key, p['cur']); put(pann, src, 'is', key, p.get('prior'))
    b0 = doc.find(r'^Cash and cash equivalents$')
    b1 = doc.find(r'^Total liabilities and shareholders', b0) if b0 is not None else None
    if b0 is not None and b1 is not None: bs_from(doc, b0, b1 + 1, ann, src, 'q', prior_key=pann)
    c0, c1 = cf_anchor(doc, (b1 or 0))
    if c0 is not None and c1 is not None: cf_from(doc, c0, c1 + 1, ann, pann, src, 4)
    seg_columns_note(doc, fy, 4, src)
    # segment note: net sales and operating income by segment (annual, three years)
    for key, endpat in [('rev', r'^(Worldwide total|Total( net sales)?)$'), ('ebit', r'^(Total operating income|Total EBIT|Total operating income \(loss\)|Operating income)$')]:
        for s in [i for i in range(doc.n) if ' | ' in doc.lines[i] and re.search(SEG_NAMES['na'], doc.lines[i].split(' | ')[0].strip())]:
            blk = doc.block(SEG_NAMES['na'], endpat, s, s + 1, 'q', maxrows=12)
            if not blk or not re.search(endpat, blk[-1][0]): continue
            labs = [b[0] for b in blk]
            if key == 'ebit' and not any(re.search(r'General Corporate|Research', l) for l in labs): continue
            if key == 'rev' and any(re.search(r'General Corporate|Research', l) for l in labs): continue
            if len(set(labs)) < len(labs): continue
            if key == 'ebit' and any(re.search(r'Worldwide total|Total net sales|Total revenues', l) for l in labs): continue
            for lab, p, j in blk:
                for sk, pat in SEG_NAMES.items():
                    if re.search(pat, lab.strip()):
                        put(ann, src, 'seg', f'{sk}_{key}_fs', p.get('cur')); put(pann, src, 'seg', f'{sk}_{key}_fs', p.get('prior'))
            break

# ---------------------------------------------------------------- driver
def run():
    pk = packages()
    for p in pk:
        fy, q, src = p['fy'], p['q'], p['date']
        has_fs = 'fs' in p['docs'] or 'er' in p['docs']
        for kind in ('er', 'fs', 'ma', 'iar', 'mr'):
            if kind not in p['docs']: continue
            path, url = p['docs'][kind]
            doc = Doc(path)
            put(qk(fy, q), src, 'sources', kind, url)
            if q == 4: put(str(fy), src, 'sources', kind, url)
            try:
                if kind == 'fs': fs_statements(doc, fy, q, src); fs_notes(doc, fy, q, src)
                elif kind == 'ma': ma_tables(doc, fy, q, src, has_fs)
                elif kind == 'mr': mr_tables(doc, fy, q, src)
                elif kind == 'er': er_tables(doc, fy, q, src)
                elif kind == 'iar': iar_tables(doc, fy, src)
            except Exception as e:
                import traceback; log(f'{src} {kind}: {e!r} {traceback.format_exc()[-400:]}')
    os.makedirs(OUT, exist_ok=True)
    for per, d in REC.items():
        json.dump(d, open(os.path.join(OUT, per + '.json'), 'w'), indent=1, sort_keys=True)
    json.dump([dict(date=p['date'], fy=p['fy'], q=p['q'], form=p['form'], acc=p['acc'], docs={k: v[1] for k, v in p['docs'].items()}) for p in pk],
              open(os.path.join(OUT, '_packages.json'), 'w'), indent=1)
    print(len(pk), 'packages;', len(REC), 'periods')
    print('\n'.join(LOG))
    return pk

if __name__ == '__main__':
    run()
