"""Per-period extraction from the Northrop Grumman EDGAR sources into data/<period>.json.

Periods: annual FY2006-FY2008 (each year's own Form 10-K: statements and segment note, as originally reported), annual
FY2009-FY2025 (the fourth-quarter release's twelve-month columns) and quarters Q1/13 - Q3/26 (that quarter's release, three-month
columns; Q4 = the fourth-quarter release's three-month column). Each record carries:
  is     statement of earnings (USD m; per share in $; shares in m)
  seg    sales and operating income by segment, intersegment eliminations, segment operating income, the reconciliation to operating
         income (FAS/CAS or net pension adjustment, unallocated corporate expense and its components, royalty reversal, divestiture
         items) and the lines below operating income, all as printed in the release's consolidated table
  ng     pension-adjusted / MTM-adjusted / free-cash-flow / backlog rows (company labels, quarter and year-to-date values)
  cf     cash flow, year to date (cf.ytd_months), company labels mapped to model keys plus lines_raw
  bs     balance sheet at period end
  py     the prior-year comparative as presented in the following year's release (restatement / realignment detection)
  x      XBRL company facts (as first filed): cross-check values and items the releases omit
  sources / notes
Nothing is estimated; computed values are stated in notes."""
import json, glob, os, re, datetime as dt
import parse_release as P
import xbrl

S = os.environ.get('NOC_SRC', '/tmp/noc_src')
BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, 'data')
CIK = '1133421'
ARCH = f'https://www.sec.gov/Archives/edgar/data/{CIK}/'
def url(o, doc): return ARCH + o['acc'].replace('-', '') + '/' + doc

def fq_of_release(date):
    m, y = int(date[5:7]), int(date[:4])
    return (y - 1, 4) if m <= 3 else (y, (m - 1) // 3)

def txt_path(o, doc): return os.path.join(S, 'txt', f"{o['date']}_{o['form'].replace('/', '')}_{o['acc']}_{doc.rsplit('.', 1)[0]}.txt")

# ------------------------------------------------------------------ release index
FILINGS = {}
def release_index():
    fl = json.load(open(os.path.join(S, 'filings.json')))
    rel, tenk = {}, {}
    for o in fl:
        if o['form'] in ('10-Q', '10-K') and o['report']:
            m_ = int(o['report'][5:7]); FILINGS[(int(o['report'][:4]), {3: 1, 6: 2, 9: 3, 12: 4}.get(m_, 4))] = txt_path(o, o['primary'])
        if o['form'].startswith('8-K') and '2.02' in (o['items'] or ''):
            for doc in o['files']:
                p = txt_path(o, doc)
                if not os.path.exists(p): continue
                t = open(p).read()
                if not re.search(r'Total sales|Sales and Service Revenues', t, re.I) or 'Intersegment' not in t: continue
                r = P.parse(t)
                if not r['cons']: continue
                k = fq_of_release(o['date'])
                if k in rel and o['form'] == '8-K/A': continue
                if k not in rel or o['form'] == '8-K':
                    rel[k] = dict(date=o['date'], url=url(o, doc), r=r, text=t, form=o['form'])
        if o['form'] == '10-K':
            fy = int(o['report'][:4])
            tenk[fy] = dict(date=o['date'], url=url(o, o['primary']), path=txt_path(o, o['primary']))
    return rel, tenk

# ------------------------------------------------------------------ label maps
def first_match(rows, rx, col, exclude=None, nth=0):
    hits = 0
    for lab, vals in rows:
        if not vals: continue
        if re.search(rx, lab, re.I) and not (exclude and re.search(exclude, lab, re.I)):
            if hits == nth: return vals[col] if col < len(vals) else None
            hits += 1
    return None

def ext_is(t, col):
    """Schedule 1 / 10-K statement of earnings -> dict (column index col of each row)."""
    if not t: return None
    rows = t['rows']; o = {}; other = []
    st = 'sales'; eps = None
    for lab, vals in rows:
        L = lab.lower().strip()
        v = vals[col] if vals and col < len(vals) else None
        if not vals:
            if re.match(r'^cost of sales|^operating costs', L): st = 'costs'
            elif re.match(r'^other income|^other \(expense\)', L): st = 'nonop'
            elif re.match(r'^basic earnings', L): eps = 'b'
            elif re.match(r'^diluted earnings', L): eps = 'd'
            continue
        if st == 'sales':
            if re.match(r'^product( sales)?$', L): o['prod_sales'] = v
            elif re.match(r'^service( revenues?| sales)?$', L): o['svc_sales'] = v
            elif re.match(r'^total sales|^sales and service revenues|^total sales and service|^sales$|^net sales', L): o['sales'] = v; st = 'costs'
        elif st == 'costs':
            if re.match(r'^product$|^cost of product', L): o['cost_prod'] = v
            elif re.match(r'^service$|^cost of service', L): o['cost_svc'] = v
            elif re.match(r'^general and administrative', L): o['ga'] = v
            elif re.match(r'^total operating costs|^total cost', L): o['total_costs'] = v
            elif re.match(r'^(total )?operating (\(loss\) )?(income|margin)', L): o['oi'] = v; st = 'nonop'
            else: other.append([lab, v])
        elif st == 'nonop':
            if re.match(r'^(net )?interest expense', L): o['int_exp'] = v
            elif re.match(r'^interest income', L): o['int_inc'] = v
            elif re.match(r'^mark-to-market|^mtm', L): o['mtm'] = v
            elif re.search(r'pension', L): o['nonop_fas'] = v
            elif re.match(r'^other,? ?net|^other income|^other \(expense\)|^other, income|^other\s*$', L): o['other_net'] = v
            elif re.search(r'before (income )?tax(es)?', L): o['ebt'] = v
            elif re.match(r'^federal and foreign income tax|^income tax', L): o['tax'] = v
            elif re.match(r'^(income|earnings)( \(loss\))? from continuing operations$|^\(loss\) income from continuing', L): o['cont_ops'] = v
            elif re.search(r'discontinued operations', L) and eps is None: o['disc_ops'] = v
            elif re.match(r'^net (\(loss\) )?(income|earnings)( \(loss\))?$|^net loss$', L) and 'ni' not in o: o['ni'] = v; st = 'eps'
            elif 'ebt' not in o and not re.search(r'per share|shares', L): o.setdefault('other_nonop', []).append([lab, v])
        if st in ('nonop', 'eps'):
            if re.match(r'^basic (\(loss\) )?earnings( \(loss\))? per share|^basic$', L): o['eps_b'] = v
            elif re.match(r'^diluted (\(loss\) )?earnings( \(loss\))? per share|^diluted$', L): o['eps_d'] = v
            elif re.match(r'^continuing operations$', L): o['eps_b_cont' if eps == 'b' else 'eps_d_cont'] = v
            elif re.match(r'^discontinued operations$', L) and st == 'eps': o['eps_b_disc' if eps == 'b' else 'eps_d_disc'] = v
            elif re.search(r'weighted[- ]average (common )?shares', L): o['sh_b'] = v
            elif re.search(r'weighted[- ]average diluted', L): o['sh_d'] = v
    o['other_op'] = other
    return o

BS_MAP = [('cash', r'^cash and cash equivalents'), ('ar', r'^accounts receivable'), ('unbilled', r'^unbilled receivables'), ('inv', r'^inventoried costs'),
          ('dta_cur', r'^deferred tax assets|^deferred income taxes$'), ('prepaid', r'^prepaid'), ('hfs_a', r'^assets of (disposal group|discontinued)'),
          ('tca', r'^total current assets'), ('ppe', r'^property, plant,? and equipment, net|^property, plant and equipment, net'),
          ('rou', r'^operating lease right'), ('gw', r'^goodwill'), ('intang', r'^(other purchased )?intangible'),
          ('dta', r'^(non-current |long-term )?deferred tax assets'), ('pension_asset', r'^pension and (other )?post-?retirement (benefit )?plan assets'),
          ('other_nca', r'^other non-current assets|^miscellaneous other assets|^other assets$'), ('ta', r'^total assets'),
          ('notes_pay', r'^notes payable'), ('cur_debt', r'^current portion of long-term debt'), ('ap', r'^trade accounts payable|^accounts payable'),
          ('accrued_comp', r'^accrued employee'), ('advances', r'^advance payments'), ('other_cl', r'^other current liabilities'),
          ('hfs_l', r'^liabilities of (disposal group|discontinued)'), ('tcl', r'^total current liabilities'), ('ltd', r'^long-term debt'),
          ('pension_liab', r'^pension and (other )?post-?retirement (benefit )?plan liabilities'), ('lease_liab', r'^operating lease liabilities'),
          ('other_ncl', r'^other (non-current|long-term) liabilities'), ('tl', r'^total liabilities$'), ('common', r'^common stock'),
          ('pic', r'^paid-in capital'), ('re', r'^retained earnings'), ('aoci', r'^accumulated other comprehensive'),
          ('equity', r"^total shareholders.? equity"), ('tle', r"^total liabilities and shareholders")]
def ext_bs(t, col=0):
    if not t: return None
    o, raw, seen_tca = {}, [], False
    for lab, vals in t['rows']:
        if not vals or col >= len(vals): continue
        v = vals[col]; raw.append([lab, v]); L = lab.lower().strip()
        for k, rx in BS_MAP:
            if re.search(rx, L):
                if k == 'dta_cur' and seen_tca: k = 'dta'
                if k == 'dta' and not seen_tca: k = 'dta_cur'
                if k not in o: o[k] = v
                break
        if re.match(r'^total current assets', L): seen_tca = True
    o['lines_raw'] = raw
    return o

CF_MAP = [('ni', r'^net (\(loss\) )?(earnings|income)( \(loss\))?$'), ('dda', r'^depreciation and amortization|^depreciation$|^amortization of (assets|intangible)'),
          ('sbc', r'^stock-based compensation|^stock compensation'), ('excess_tax', r'^excess tax benefits'), ('deftax', r'^deferred income taxes'),
          ('mtm', r'^mark-to-market'), ('gain_sale', r'^gain on sale of business|^gain on sale'), ('b21', r'^b-21'), ('pension_inc', r'^net periodic pension'),
          ('pension_contrib', r'^pension and opb contributions|^pension contributions'), ('retiree', r'^retiree benefits'),
          ('lease_noncash', r'^non-cash lease'), ('other_noncash', r'^other, net$|^other operating activities|^other noncash|^other non-cash'),
          ('wc_ar', r'^accounts receivable'), ('wc_unbilled', r'^unbilled receivables'), ('wc_inv', r'^inventoried costs'), ('wc_prepaid', r'^prepaid expenses'),
          ('wc_ap', r'^accounts payable and other liabilities|^trade accounts payable|^accounts payable$'), ('wc_tax', r'^income taxes payable'),
          ('wc_adv', r'^advance payments'), ('wc_other_liab', r'^other liabilities$'),
          ('cfo_cont', r'^cash provided by continuing operations$|^cash (provided by|used in) operating activities from continuing'),
          ('cfo_disc', r'^cash (provided by|used in|\(used in\) provided by|provided by \(used in\)) discontinued operations$'),
          ('cfo', r'^net cash (provided by|used in|\(used in\) provided by|provided by \(used in\)|\(used in\)) operating|^cash provided by operations$'),
          ('capex', r'^capital expenditures|^additions to property'), ('acq', r'^acquisition of|^payments for businesses|^business acquisitions'),
          ('divest', r'^divestiture|^proceeds from sale of business'), ('equip', r'^proceeds from sale of equipment'),
          ('net', r'in cash(, cash equivalents)? and (cash equivalents|restricted cash)$|^net (increase|decrease|change) in cash'), ('beg', r'beginning of'), ('end', r'end of'),
          ('sale_inv', r'^proceeds from sale of (investment|minority)'), ('restricted', r'restricted cash|^restriction of cash'), ('other_inv', r'^other investing|^other, net$'),
          ('cfi', r'^net cash .*investing'), ('debt_iss', r'^net proceeds from issuance|^proceeds from issuance of long-term'),
          ('debt_rep', r'^payments of long-term debt|^principal payments of long-term'), ('credit', r'^payments to credit facilities|^net borrowings|^proceeds from credit|^repayments of commercial'),
          ('bb', r'^common stock repurchases|^repurchases of common'), ('div', r'^cash dividends paid|^dividends paid'),
          ('tax_withheld', r'^payments of employee taxes withheld'), ('stock_iss', r'^proceeds from exercises|^proceeds from issuance of common'),
          ('other_fin', r'^other financing|^other, net$'), ('cff', r'^net cash .*financing'),
          ]
def ext_cf(t, col=0, months=None):
    if not t: return None
    o, raw, sect = {'ytd_months': months}, [], 'op'
    for lab, vals in t['rows']:
        L = lab.lower().strip()
        if not vals:
            if re.match(r'^investing', L): sect = 'inv'
            elif re.match(r'^financing', L): sect = 'fin'
            continue
        if col >= len(vals): continue
        v = vals[col]; raw.append([lab, v])
        for k, rx in CF_MAP:
            if re.search(rx, L):
                if k == 'other_inv' and sect == 'fin': k = 'other_fin'
                if k == 'other_fin' and sect == 'inv': k = 'other_inv'
                if k in ('other_noncash', 'other_inv', 'other_fin') and rx == r'^other, net$':
                    k = {'op': 'other_noncash', 'inv': 'other_inv', 'fin': 'other_fin'}[sect]
                if k in ('acq', 'divest', 'credit', 'sale_inv', 'equip'): o[k] = round(o.get(k, 0.0) + (v or 0.0), 6)
                elif k not in o: o[k] = v
                break
        if re.match(r'^net cash .*operating|^cash provided by (continuing )?operations$', L): sect = 'inv'
        if re.match(r'^net cash .*investing', L): sect = 'fin'
    o['lines_raw'] = raw
    return o

def seg_part(d):
    return None if d is None else {k: d[k] for k in ('sales', 'elim_sales', 'total_sales', 'oi', 'elim_oi', 'seg_oi', 'recon', 'oi_total', 'below')}

def ng_part(ng, qcol, ycol):
    out = []
    for x in ng:
        lay = x['layout']; nv = lay.count('v')
        q = x['vals'][qcol] if qcol is not None and qcol < nv else None
        y = x['vals'][ycol] if ycol is not None and ycol < nv else None
        if nv == 1 and qcol == 0: q, y = x['vals'][0], None
        out.append([x['label'], q, y, nv])
    return out

def xbrl_extras(fy, q, annual):
    kind = 'FY' if annual else 'YTD'
    qq = 4 if annual else q
    k3 = 'FY' if annual else 'Q'
    return {'rev': xbrl.first_of(['Revenues', 'SalesRevenueNet'], fy, k3, qq), 'oi': xbrl.value('OperatingIncomeLoss', fy, k3, qq),
            'ni': xbrl.value('NetIncomeLoss', fy, k3, qq), 'eps_d': xbrl.value('EarningsPerShareDiluted', fy, k3, qq),
            'cfo_ytd': xbrl.value('NetCashProvidedByUsedInOperatingActivities', fy, kind, qq), 'ta': xbrl.value('Assets', fy, 'I', qq),
            'sbc_ytd': xbrl.value('ShareBasedCompensation', fy, kind, qq),
            'deftax_ytd': xbrl.first_of(['DeferredIncomeTaxesAndTaxCredits', 'DeferredIncomeTaxExpenseBenefit', 'IncreaseDecreaseInDeferredIncomeTaxes'], fy, kind, qq),
            'dda_ytd': xbrl.value('DepreciationDepletionAndAmortization', fy, kind, qq),
            'retiree_ytd': xbrl.value('IncreaseDecreaseInPensionAndPostretirementObligations', fy, kind, qq),
            'excess_tax_ytd': xbrl.value('ExcessTaxBenefitFromShareBasedCompensationOperatingActivities', fy, kind, qq),
            'sh_out': xbrl.value('CommonStockSharesOutstanding', fy, 'I', qq), 'dei_sh_out': xbrl.value('EntityCommonStockSharesOutstanding', fy, 'I', qq),
            'dps': xbrl.value('CommonStockDividendsPerShareDeclared', fy, k3, qq),
            'amort_intang': xbrl.value('AmortizationOfIntangibleAssets', fy, 'FY') if annual else None,
            'rpo': xbrl.value('RevenueRemainingPerformanceObligation', fy, 'I', qq),
            'intang_bs': xbrl.value('IntangibleAssetsNetExcludingGoodwill', fy, 'I', qq),
            'ltd_cur': xbrl.first_of(['LongTermDebtCurrent', 'LongTermDebtAndCapitalLeaseObligationsCurrent'], fy, 'I', qq),
            'ltd_total': xbrl.first_of(['LongTermDebtAndCapitalLeaseObligations', 'LongTermDebt'], fy, 'I', qq) if annual else None,
            'pension_noncash_ytd': xbrl.value('PensionAndOtherPostretirementBenefitsExpenseReversalOfExpenseNoncash', fy, kind, qq),
            'pension_contrib_ytd': xbrl.first_of(['PensionAndOtherPostretirementBenefitContributions', 'PensionContributions'], fy, kind, qq)}

# ------------------------------------------------------------------ records
def rec_release(rel, fy, q, annual):
    r = rel.get((fy, q))
    if not r: return None
    R = r['r']; c = R['cons']
    blk = 'y' if annual else 'q'
    if annual and not c.get('y'): return None
    rec = {'period': str(fy) if annual else f'Q{q}-{str(fy)[2:]}', 'fy': fy, 'q': None if annual else q,
           'period_end': f'{fy}-12-31' if annual else f'{fy}-{3 * q:02d}-{[31, 30, 30, 31][q - 1]}',
           'sources': {'release': r['url'], 'release_date': r['date']}, 'notes': []}
    rec['seg'] = seg_part(c[blk]['cur'])
    rec['seg']['layout'] = c['layout']
    t = R['is']
    if t:
        nv = t['layout'].count('v')
        col = 0 if not annual else (2 if nv >= 4 else 0)
        if annual and nv < 4: rec['notes'].append('income statement: twelve-month column taken from a two-column schedule (first column)')
        rec['is'] = ext_is(t, col)
    rec['bs'] = ext_bs(R['bs'], 0)
    months = 12 if annual else 3 * q
    rec['cf'] = ext_cf(R['cf'], 0, months)
    qcol, ycol = (None, 2) if annual else (0, 2)
    if annual:
        rec['ng'] = ng_part(R['ng'], 2, 2)
        rec['ng'] = [[l, y, y, nv] if nv >= 4 else [l, (q_ if nv == 1 else None), (q_ if nv in (1, 2, 3) else y), nv] for l, q_, y, nv in ng_part(R['ng'], 0, 2)]
    else:
        rec['ng'] = ng_part(R['ng'], 0, 2)
    rec['backlog'] = R['backlog']
    rec['guidance'] = R['guidance']
    # prior-year comparative as presented one year later (same quarter release)
    nxt = rel.get((fy + 1, q))
    if nxt:
        cn = nxt['r']['cons']
        pyb = cn.get(blk, {}).get('py') if cn.get(blk) else None
        rec['py'] = {'release': nxt['url'], 'release_date': nxt['date'], 'seg': seg_part(pyb) if pyb else None}
        tn = nxt['r']['is']
        if tn:
            nv = tn['layout'].count('v')
            col = 1 if not annual else (3 if nv >= 4 else 1)
            rec['py']['is'] = ext_is(tn, col)
        rec['py']['ng'] = ng_part(nxt['r']['ng'], 1, 3) if not annual else [[l, y, y, nv] for l, q_, y, nv in ng_part(nxt['r']['ng'], 1, 3)]
    if not (rec['backlog'].get('total_row') or rec['backlog'].get('total_bn_text')):
        fq = FILINGS.get((fy, 4 if annual else q))
        if fq and os.path.exists(fq):
            b2 = P.backlog(P.Doc(open(fq).read()))
            if b2.get('total_bn_text') or b2.get('total_row'):
                rec['backlog'] = dict(b2, source='10-Q/10-K text'); rec['notes'].append('backlog from the Form 10-Q / 10-K text (not in the release)')
    rec['x'] = xbrl_extras(fy, q, annual)
    return rec

# ------------------------------------------------------------------ 10-K records (FY2006-FY2008)
def tenk_segments(text):
    """segment note table (three years) -> {'sales': {name: [y0, y1, y2]}, 'oi': ..., 'recon': ..., 'layout'}"""
    doc = P.Doc(text); lines = doc.lines
    # the note table: 'Sales and Service Revenues' header followed by business groups and 'Intersegment eliminations'
    cands = [i for i, l in enumerate(lines) if re.match(r'^Intersegment eliminations \|', l)]
    for i in cands:
        # walk back to the start of the table
        s = i
        while s > 0 and (('|' in lines[s - 1]) or re.match(r'^\s*(Sales and Service|Information &|Services|Aerospace|Revenues|Operating Margin)', lines[s - 1])): s -= 1
        lay = None
        for j in range(max(0, s - 4), i):
            lay = P.layout_from_header(lines[j])
            if lay: s = j + 1; break
        if lay is None or lay.count('v') != 3: continue
        rows = doc.rows(s, i + 40)
        out = {'sales': {}, 'oi': {}, 'elim_sales': None, 'total_sales': None, 'elim_oi': None, 'seg_oi': None, 'recon': [], 'oi_total': None, 'layout': lay}
        st = 'sales'
        for j, lab, toks in rows:
            L = lab.lower().strip()
            if not toks:
                if re.match(r'^(segment )?operating (margin|income)', L): st = 'oi'
                continue
            vals = P.assign(toks, lay); sn = P.segname(lab)
            if st == 'sales':
                if sn: out['sales'][sn] = vals
                elif re.match(r'^intersegment', L): out['elim_sales'] = vals
                elif re.match(r'^(total )?sales and service revenues|^total sales', L): out['total_sales'] = vals; st = 'oi'
            elif st == 'oi':
                if sn: out['oi'][sn] = vals
                elif re.match(r'^intersegment', L): out['elim_oi'] = vals
                elif re.match(r'^(total )?segment operating (margin|income|\(loss\) income)', L): out['seg_oi'] = vals; st = 'recon'
            elif st == 'recon':
                if re.match(r'^(total )?operating (margin|income|\(loss\) income)', L): out['oi_total'] = vals; break
                out['recon'].append((lab, vals))
        if out['sales'] and out['seg_oi'] is not None:
            if out['oi_total'] is None:
                rows_all = doc.rows(0, len(lines))
                for n_, (j, lab, toks) in enumerate(rows_all):
                    if re.match(r'^unallocated (corporate )?expenses?$', lab, re.I) and toks and len(P.assign(toks, lay)) == 3:
                        rec_ = []
                        for j2, lab2, toks2 in rows_all[n_:n_ + 6]:
                            if not toks2: continue
                            v2 = P.assign(toks2, lay)
                            if re.match(r'^(total )?operating (margin|income|\(loss\) income)', lab2, re.I): out['oi_total'] = v2; break
                            rec_.append((lab2, v2))
                        if out['oi_total'] is not None:
                            out['recon'] = rec_; out['recon_note'] = 'reconciliation to operating margin from the MD&A segment table (not in the note table)'; break
            if out['oi_total'] is not None: return out
    return None


def tenk_segments_all(text):
    """every three-year segment table in a 10-K (sales / operating income by segment, eliminations, totals, reconciliation) with the
    header years -> list of dicts; handles the pre-2024 note layout and the ASU 2023-07 layout (per-segment blocks)."""
    doc = P.Doc(text); lines = doc.lines
    out_all = []
    for i, l in enumerate(lines):
        if not re.match(r'^Intersegment eliminations \|', l): continue
        s = i
        while s > 0 and (('|' in lines[s - 1]) or (len(lines[s - 1].strip()) < 60 and not lines[s - 1].strip().endswith('.'))): s -= 1
        lay = None
        for j in range(max(0, s - 2), i):
            lay = P.layout_from_header(lines[j])
            if lay: s = j + 1; break
        if lay is None or lay.count('v') != 3: continue
        years = [int(x) for x in re.findall(r'(20\d\d)', lines[j])][:3]
        st = 'sales'; out = {'years': years, 'sales': {}, 'oi': {}, 'elim_sales': None, 'total_sales': None, 'elim_oi': None, 'seg_oi': None, 'recon': [], 'oi_total': None}
        for j2, lab, toks in doc.rows(s, i + 45):
            L = lab.lower().strip()
            if not toks:
                if re.match(r'^(segment )?operating (margin|income|\(loss\) income)', L): st = 'oi'
                continue
            vals = P.assign(toks, lay); sn = P.segname(lab)
            if st == 'sales':
                if sn: out['sales'][sn] = vals
                elif re.match(r'^intersegment', L): out['elim_sales'] = vals
                elif re.match(r'^(total )?sales and service revenues|^total sales', L): out['total_sales'] = vals; st = 'oi'
            elif st == 'oi':
                if sn: out['oi'][sn] = vals
                elif re.match(r'^intersegment', L): out['elim_oi'] = vals
                elif re.match(r'^(total )?segment operating (margin|income|\(loss\) income)', L): out['seg_oi'] = vals; st = 'recon'
            elif st == 'recon':
                if re.match(r'^(total )?operating (margin|income|\(loss\) income)', L): out['oi_total'] = vals; break
                out['recon'].append((lab, vals))
        if out['sales'] and out['total_sales'] is not None:
            out_all.append(out)
    # ASU 2023-07 layout
    i = P.find(lines, r'^Total segment operating income \|')
    if i is not None:
        s = max(0, i - 70); lay = None
        for j in range(i, s, -1):
            lay = P.layout_from_header(lines[j])
            if lay and lay.count('v') == 3: s = j + 1; break
        if lay:
            years = [int(x) for x in re.findall(r'(20\d\d)', lines[j])][:3]
            out = {'years': years, 'sales': {}, 'oi': {}, 'recon': [], 'elim_oi': None, 'seg_oi': None, 'oi_total': None, 'elim_sales': None, 'total_sales': None, 'layout': 'asu2023-07'}
            cur = None
            for j2 in range(s, i + 12):
                l2 = lines[j2]
                if '|' not in l2:
                    sn = P.segname(l2.strip())
                    if sn: cur = sn
                    continue
                lab, toks = P.split_line(l2); L = lab.lower().strip(); sn = P.segname(lab)
                if not toks: continue
                vals = P.assign(toks, lay)
                if re.match(r'^sales$', L) and cur: out['sales'][cur] = vals
                elif sn and re.search(r'operating income', L): out['oi'][sn] = vals
                elif re.match(r'^intersegment profit eliminations', L): out['elim_oi'] = vals
                elif re.match(r'^total segment operating income', L): out['seg_oi'] = vals
                elif re.match(r'^total operating income', L): out['oi_total'] = vals; break
                elif out['seg_oi'] is not None: out['recon'].append((lab, vals))
            for prev in out_all:          # total sales and eliminations from the note's sales table (same years)
                if prev['years'] == years and prev['total_sales']:
                    out['total_sales'] = prev['total_sales']; out['elim_sales'] = prev['elim_sales']; break
            if out['sales'] and out['seg_oi'] is not None: out_all.append(out)
    return out_all

def rec_tenk(tenk, fy):
    o = tenk.get(fy)
    if not o or not os.path.exists(o['path']): return None
    text = open(o['path']).read()
    doc = P.Doc(text)
    rec = {'period': str(fy), 'fy': fy, 'q': None, 'period_end': f'{fy}-12-31', 'sources': {'filing': o['url'], 'filing_date': o['date']},
           'notes': ['FY%d from the Form 10-K (statements and segment note), as originally reported' % fy]}
    t_is = None
    for i, l in enumerate(doc.lines):
        if re.match(r'^Product sales \|', l) and any(re.match(r'^General and administrative', x) for x in doc.lines[i:i + 12]):
            t_is = P.statement(P.Doc('\n'.join(doc.lines[max(0, i - 12):i + 70])), r'.', r'^Product sales\s*\|', r'^The accompanying notes', 60)
            if t_is and t_is['layout'].count('v') == 3: break
            t_is = None
    rec['is'] = ext_is(t_is, 0) if t_is else None
    # balance sheet: the statement (not the five-year summary): first 'Cash and cash equivalents |' row followed by 'Accounts receivable'
    bs = None
    for i, l in enumerate(doc.lines):
        if re.match(r'^Cash and cash equivalents \|', l) and any(re.match(r'^Accounts receivable', x) for x in doc.lines[i + 1:i + 3]):
            sub = P.Doc('\n'.join(doc.lines[max(0, i - 12):i + 90]))
            bs = P.statement(sub, r'.', r'^Cash and cash equivalents\s*\|', r'^NORTHROP', 80, incl_stop=r"^total liabilities and shareholders")
            if bs and bs['layout'].count('v') == 2: break
            bs = None
    rec['bs'] = ext_bs(bs, 0)
    cf = None
    for i, l in enumerate(doc.lines):
        if re.match(r'^Sources of Cash', l.strip()) or re.match(r'^Progress payments \|', l) or re.match(r'^Collections on billings \|', l):
            sub = P.Doc('\n'.join(doc.lines[max(0, i - 14):i + 130]))
            cf = P.statement(sub, r'.', r'^(Progress payments|Collections on billings|Sources of Cash)', r'^Reconciliation of Net Income', 130,
                             incl_stop=r'^cash and cash equivalents,? end of year$')
            if cf and cf['layout'].count('v') == 3 and any(re.match(r'^cash and cash equivalents, end', lab, re.I) for lab, v in cf['rows']): break
            cf = None
    rec['cf'] = ext_cf(cf, 0, 12)
    if rec['cf']:
        # the reconciliation of net income to CFO follows the direct-method statement
        allrows = doc.rows(0, len(doc.lines))
        for n_, (i, lab_, toks_) in enumerate(allrows):
            if not re.match(r'^net cash provided by operating activities$', lab_, re.I): continue
            seg = allrows[max(0, n_ - 45):n_]
            d_idx = next((k for k, (_, l2, _) in enumerate(seg) if re.match(r'^Depreciation$', l2, re.I)), None)
            if d_idx is not None:
                s_idx = next((k for k, (_, l2, _) in enumerate(seg) if re.match(r'^Net (income|earnings)$', l2, re.I) and k < d_idx), max(0, d_idx - 2))
                lay2 = None
                for j in range(seg[s_idx][0] - 1, max(0, seg[s_idx][0] - 14), -1):
                    lay2 = P.layout_from_header(doc.lines[j])
                    if lay2: break
                sub = {'rows': [(l2, P.assign(t2, lay2)) for _, l2, t2 in (seg[s_idx:] + [allrows[n_]]) if t2]} if lay2 else None
                if sub:
                    for lab, vals in sub['rows']:
                        if not vals: continue
                        L = lab.lower().strip(); v = vals[0]
                        for k, rx in (('dda_dep', r'^depreciation$'), ('dda_amort', r'^amortization of (assets|intangible)'), ('sbc', r'^stock-based compensation|^stock compensation'),
                                      ('deftax', r'^deferred income taxes'), ('pension_noncash', r'^pension and other|^retiree benefits'), ('impairment', r'^goodwill impairment'),
                                      ('excess_tax', r'^excess tax')):
                            if re.search(rx, L) and k not in rec['cf']: rec['cf'][k] = v
                    rec['cf']['recon_raw'] = [[l, (v[0] if v else None)] for l, v in sub['rows']]
                break
        if 'dda_dep' in rec['cf']: rec['cf']['dda'] = (rec['cf'].get('dda_dep') or 0) + (rec['cf'].get('dda_amort') or 0)
    sg = tenk_segments(text)
    if sg:
        rec['seg'] = {'sales': {k: v[0] for k, v in sg['sales'].items()}, 'elim_sales': sg['elim_sales'][0], 'total_sales': sg['total_sales'][0],
                      'oi': {k: v[0] for k, v in sg['oi'].items()}, 'elim_oi': sg['elim_oi'][0] if sg['elim_oi'] else None, 'seg_oi': sg['seg_oi'][0],
                      'recon': [(l, v[0]) for l, v in sg['recon']], 'oi_total': sg['oi_total'][0], 'below': [], 'layout': sg['layout'], 'source': '10-K segment note'}
        rec['py_tenk'] = {'sales': {k: v[1] for k, v in sg['sales'].items()}, 'oi': {k: v[1] for k, v in sg['oi'].items()}, 'seg_oi': sg['seg_oi'][1], 'oi_total': sg['oi_total'][1]}
    nk = tenk.get(fy + 1)
    if nk and os.path.exists(nk['path']):
        sg2 = tenk_segments(open(nk['path']).read())
        if sg2:
            rec['py'] = {'filing': nk['url'], 'seg': {'sales': {k: v[1] for k, v in sg2['sales'].items()}, 'oi': {k: v[1] for k, v in sg2['oi'].items()},
                                                      'seg_oi': sg2['seg_oi'][1], 'oi_total': sg2['oi_total'][1], 'total_sales': sg2['total_sales'][1]}}
    rec['x'] = xbrl_extras(fy, 4, True)
    return rec

def tenk_cf_rows(tenk, fy):
    """[(label, tokens, layout)] of the FY<fy> 10-K direct-method cash-flow statement and its reconciliation section"""
    o = tenk.get(fy)
    if not o or not os.path.exists(o['path']): return []
    doc = P.Doc(open(o['path']).read())
    out = []
    for i, l in enumerate(doc.lines):
        if re.match(r'^Progress payments \|', l) or re.match(r'^Collections on billings \|', l):
            lay = None
            for j in range(i - 1, max(0, i - 16), -1):
                lay = P.layout_from_header(doc.lines[j])
                if lay: break
            if not lay or lay.count('v') != 3: continue
            for i2, lab, toks in doc.rows(i, i + 160):
                if toks: out.append((lab, toks, lay))
                if re.match(r'^net cash provided by operating activities$', lab, re.I) and any(re.match(r'^depreciation$', x[0], re.I) for x in out): break
            if out: break
    return out

def resolve_tenk_cf(tenk, fy):
    """cash-flow values for calendar year fy from the FY2006-FY2008 10-Ks. Blank cells are dropped by the text conversion, so a row
    with fewer than three values cannot be placed on its own; each label is therefore resolved across the three filings: every
    placement of each filing's values onto its three years is enumerated and only assignments on which the filings agree for the
    years they share are kept. The value for fy is used when all consistent assignments give the same answer (a missing year is
    a blank = 0.0). Complete rows resolve directly; the earliest filing wins."""
    import itertools
    KEYS = [('dda_dep', r'^depreciation$'), ('dda_amort', r'^amortization of (assets|intangible)'), ('pension_noncash', r'^pension and other|^retiree benefits'),
            ('impairment', r'^goodwill impairment|^impairment of goodwill')] + [kv for kv in CF_MAP if kv[0] != 'dda']
    rows = {}            # key -> {filing: [list of token vectors]}
    for f in (2006, 2007, 2008):
        for lab, toks, lay in tenk_cf_rows(tenk, f):
            L = lab.lower().strip()
            for k, rx in KEYS:
                if re.search(rx, L):
                    rows.setdefault(k, {}).setdefault(f, []).append([P.pnum(x) for x in toks])
                    break
    out, notes = {}, []
    ADD = ('acq', 'divest', 'credit', 'sale_inv', 'equip')
    for k, byf in rows.items():
        own = byf.get(fy, [])
        if k not in ADD and len(own) > 1: own = own[:1]            # the same total printed twice (statement and reconciliation): first wins
        if own and all(len(v) == 3 for v in own):
            out[k] = sum(v[0] for v in own); continue
        if not own:
            continue                                                 # the row is not printed in the year's own 10-K: blank
        if k in ADD and len(own) > 1:
            notes.append(f'{k}: several short rows in the FY{fy} 10-K; not placed'); continue
        v = own[0]; years = (fy, fy - 1, fy - 2)
        opts = [{years[p]: v[i] for i, p in enumerate(pos)} for pos in itertools.combinations(range(3), len(v))]
        def score(asg):
            sc = 0
            for f2, vecs in byf.items():
                if f2 == fy or not vecs: continue
                v2 = vecs[0]; y2 = (f2, f2 - 1, f2 - 2)
                best = -1
                for pos in itertools.combinations(range(3), len(v2)):
                    a2 = {y2[p]: v2[i] for i, p in enumerate(pos)}
                    agree = sum(1 for y in set(a2) | set(asg) if y in y2 and y in years and abs(a2.get(y, 0.0) - asg.get(y, 0.0)) < 0.5)
                    best = max(best, agree)
                sc += best
            return sc
        scored = sorted(((score(a), a) for a in opts), key=lambda x: -x[0])
        if len(scored) == 1 or scored[0][0] > scored[1][0]:
            out[k] = scored[0][1].get(fy, 0.0)
            notes.append(f'{k}: short row in the FY{fy} 10-K placed by consistency with the following filings -> {out[k]}')
        else:
            notes.append(f'{k}: short row in the FY{fy} 10-K cannot be placed ({v}); left blank, absorbed in the derived other lines')
    return out, notes


def recast_2018(rel):
    """Q4 2018 release Schedule 6: 2016-17 and Q1-Q3 2018 as recast for the MTM accounting change adopted in Q4 2018
    (columns: 2016, 2017, Q1-18, Q2-18, Q3-18, Q4-18 as reported, FY2018) -> {label: [7 values]}"""
    r = rel.get((2018, 4))
    if not r: return {}
    lines = r['text'].splitlines()
    i = P.find(lines, r'^AS RECAST FOR ACCOUNTING CHANGE')
    if i is None: return {}
    out = {'_src': r['url'], '_cols': ['2016', '2017', 'Q1-18', 'Q2-18', 'Q3-18', 'Q4-18', '2018']}
    for lab, toks in (P.split_line(l) for l in lines[i + 1:i + 40]):
        if not toks or len(toks) < 5: continue
        if re.search(r'margin rate|tax rate', lab, re.I): continue
        vals = [P.pnum(t) for t in toks]
        if len(vals) == 7: out[lab] = vals
    return out

def tenk_fascas(tenk):
    """FAS / CAS pension components from each 10-K's MD&A table (three years): CAS pension expense, FAS (service) pension expense,
    net FAS/CAS pension adjustment / FAS/CAS operating adjustment, non-operating FAS pension benefit, MTM -> {fy: {year: {...}}}"""
    out = {}
    for fy, o in sorted(tenk.items()):
        if fy < 2009 or not os.path.exists(o['path']): continue
        doc = P.Doc(open(o['path']).read()); lines = doc.lines
        for i, l in enumerate(lines):
            if not re.match(r'^CAS pension (expense|cost) \|', l): continue
            lay = None
            for j in range(i - 1, max(0, i - 25), -1):
                lay = P.layout_from_header(lines[j])
                if lay and lay.count('v') >= 3: break
                lay = None
            if not lay: continue
            years = [int(x) for x in re.findall(r'(20\d\d)', lines[j])][:3]
            if len(years) < 3: continue
            tab = {}
            for i2, lab, toks in doc.rows(i - 6, i + 14):
                if not toks: continue
                v = P.assign(toks, lay); L = lab.lower().strip()
                for k, rx in (('cas', r'^cas pension (expense|cost)'), ('fas_svc', r'^fas pension service (expense|cost)'), ('fas_total', r'^fas pension (expense|cost)$|^fas \(service\) pension'),
                              ('fascas_op', r'^fas/cas operating adjustment|^net fas \(service\)/cas|^net fas/cas pension adjustment|^net pension adjustment'),
                              ('nonop_fas', r'^non-operating fas|^fas \(non-service\)|^net fas \(non-service\)'), ('mtm', r'^mark-to-market|^mtm')):
                    if re.search(rx, L) and k not in tab: tab[k] = v; break
            if 'cas' in tab:
                for k_, y in enumerate(years):
                    out.setdefault(str(fy), {})[str(y)] = {kk: vv[k_] for kk, vv in tab.items()}
                out[str(fy)]['_src'] = o['url']
                break
    return out
def main():
    os.makedirs(OUT, exist_ok=True)
    rel, tenk = release_index()
    json.dump([{'fy': k[0], 'q': k[1], 'date': v['date'], 'url': v['url'], 'form': v['form']} for k, v in sorted(rel.items())], open(os.path.join(OUT, '_releases.json'), 'w'), indent=1)
    n = 0
    for fy in (2006, 2007, 2008):
        r = rec_tenk(tenk, fy)
        if r:
            res, rnotes = resolve_tenk_cf(tenk, fy)
            r['notes'] += ['cash flow ' + x for x in rnotes]
            cf = r['cf'] or {'ytd_months': 12}
            for k, v in res.items():
                if k in ('lines_raw', 'recon_raw'): continue
                cf[k] = v
            for k in [k for k in list(cf) if k not in res and k not in ('ytd_months', 'lines_raw', 'recon_raw', 'dda')]:
                cf.pop(k)            # rows with blank cells cannot be placed; dropped unless resolved above
            cf['dda'] = (cf.get('dda_dep') or 0) + (cf.get('dda_amort') or 0) if 'dda_dep' in cf else None
            r['cf'] = cf
            r['notes'].append('cash flow: values taken only from 10-K rows that print all three years (FY%d-FY2008 filings); rows with blank cells are not placed' % fy)
            json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
    for fy in range(2009, 2026):
        r = rec_release(rel, fy, 4, True)
        if r:
            if fy in tenk: r['sources']['filing'] = tenk[fy]['url']
            json.dump(r, open(os.path.join(OUT, f'{fy}.json'), 'w'), indent=1); n += 1
    for fy in range(2013, 2027):
        for q in (1, 2, 3, 4):
            if fy == 2026 and q == 4: break
            r = rec_release(rel, fy, q, False)
            if r: json.dump(r, open(os.path.join(OUT, f'Q{q}-{str(fy)[2:]}.json'), 'w'), indent=1); n += 1
    json.dump(recast_2018(rel), open(os.path.join(OUT, '_recast_2018.json'), 'w'), indent=1)
    json.dump(tenk_fascas(tenk), open(os.path.join(OUT, '_fascas_10k.json'), 'w'), indent=1)
    seg10k = {}
    for fy, o in sorted(tenk.items()):
        if fy < 2006 or not os.path.exists(o['path']): continue
        tabs = tenk_segments_all(open(o['path']).read())
        if tabs:
            t = [x for x in tabs if x['seg_oi'] is not None] or tabs
            seg10k[str(fy)] = dict(t[0], url=o['url'], date=o['date'])
    json.dump(seg10k, open(os.path.join(OUT, '_seg_10k.json'), 'w'), indent=1)
    xbrl.dump_subset()
    print(n, 'period files;', len(seg10k), '10-K segment tables')

if __name__ == '__main__':
    main()
