"""Data checks for the THEON kit: statement arithmetic in every extracted record (own period and comparatives), quarter sums vs
full years, balance-sheet and cash ties, and adjusted EBIT / EBITDA bridges. Known, explained exceptions are listed in EXCEPT.
Usage: python3 check_data.py   (exit code 1 if an unexplained check fails)"""
import json, os, glob, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import normalize as N

TOL = 0.0011          # EUR m: statements are printed in whole euros (dot / comma thousands); 6-dp storage
EXCEPT = {
    ('AR21', 'TA'): 'FY2021 annual report: printed non-current + current assets differ from total assets by EUR 1.9k (source rounding); the model uses the restated 1-Jan-2022 balance sheet (AR2023).',
    ('AR21:py', 'TA'): 'FY2020 comparative in the FY2021 report: subtotals exceed total assets by EUR 1.0m (a line the parser does not map); FY2020 is not used.',
    ('2025 ΣQ', 'adj_ebit_pub'): 'Definition changed mid-year (VMC rule): Q1-25 was published excluding the share of associates (EUR 0.759m), H1 / 9M / FY-25 including it.',
    ('AR22:py', 'TA'): 'FY2021 comparative in the FY2022 report: EUR 1.9k print difference; not used.',
    ('Q4-23', 'DNA'): 'Q4-23 D&A = FY23 (1.27) − 9M-23 comparative (1.30) = −0.03: the 9M-23 comparative (9M-24 document) and the FY2023 annual report are inconsistent; kept as published.',
}

def n(x): return 0.0 if x is None else x

def check_record(tag, rec, out):
    i, b, c, g = rec.get('is') or {}, rec.get('bs') or {}, rec.get('cf') or {}, rec.get('ng') or {}
    def eq(name, a, z):
        d = round(a - z, 6)
        ok = abs(d) <= TOL or (tag, name) in EXCEPT
        out.append((tag, name, d, ok))
    if i.get('rev') is not None and i.get('cogs') is not None and i.get('gp') is not None: eq('GP', i['rev'] + i['cogs'], i['gp'])
    if i.get('op') is not None and i.get('gp') is not None:
        op = sum(n(i.get(k)) for k in ('gp', 'oinc', 'ogain', 'admin', 'sell', 'rnd', 'imp', 'oexp')) + (n(i.get('assoc')) if i.get('assoc_pos') == 'in_op' else 0)
        eq('OP', op, i['op'])
    if i.get('ebt') is not None and i.get('op') is not None:
        eq('EBT', i['op'] + n(i.get('finc')) + n(i.get('fcost')) + (n(i.get('assoc')) if i.get('assoc_pos') == 'below_op' else 0), i['ebt'])
    if i.get('ni') is not None and i.get('ebt') is not None: eq('NI', i['ebt'] + n(i.get('taxc')) + n(i.get('taxd')), i['ni'])
    if b.get('ta') is not None and b.get('tnca') is not None: eq('TA', b['tnca'] + n(b.get('tca')), b['ta'])
    if b.get('tle') is not None and b.get('ta') is not None: eq('BS', b['ta'], b['tle'])
    if b.get('tle') is not None and b.get('eqp') is not None:
        te = b.get('te', b['eqp'] + n(b.get('nci_bs'))); tl = b.get('tl', n(b.get('tncl')) + n(b.get('tcl')))
        eq('TLE', te + tl, b['tle'])
    if c.get('cfo') is not None and c.get('net') is not None: eq('CF', c['cfo'] + n(c.get('cfi')) + n(c.get('cff')), c['net'])
    if c.get('end') is not None and c.get('beg') is not None: eq('CASH', c['beg'] + n(c.get('net')) + n(c.get('fx')), c['end'])
    if c.get('cfo') is not None and c.get('cashgen') is not None: eq('CFO', c['cashgen'] + n(c.get('taxp')) + n(c.get('intp')), c['cfo'])
    if g.get('adj_ebit') is not None and g.get('ebit_pub') is not None and i.get('op') is not None:
        eq('EBIT', g['ebit_pub'], i['op'])
    r = rec.get('rev') or {}
    if r.get('product') and i.get('rev') is not None: eq('PROD', sum(v for v in r['product'].values() if v is not None), i['rev'])
    if r.get('region') and i.get('rev') is not None and 'greece' not in r['region']: eq('REG', sum(v for v in r['region'].values() if v is not None), i['rev'])

def main():
    out = []
    here = os.path.dirname(os.path.abspath(__file__))
    for f in sorted(glob.glob(os.path.join(here, 'data', '*.json'))):
        rec = json.load(open(f)); per = rec['period']
        if rec.get('is') or rec.get('bs'):
            check_record(rec.get('source_doc', per), rec, out)
        for doc, cmp in (rec.get('cmp') or {}).items():
            check_record(f'{doc}:py', cmp, out)
    D = N.run()
    for y in ('2023', '2024', '2025'):
        yy = y[2:]
        for k in ('rev', 'op', 'ni', 'cf_cfo', 'cf_cfi', 'cf_cff', 'adj_ebit_pub', 'dna'):
            fy = D[y]['x'].get(k); qs = [D[f'Q{q}-{yy}']['x'].get(k) for q in (1, 2, 3, 4)]
            if fy is None or any(v is None for v in qs): continue
            d = round(sum(qs) - fy, 6)
            out.append((f'{y} ΣQ', k, d, abs(d) <= TOL or (f'{y} ΣQ', k) in EXCEPT))
    for p, v in D.items():
        x = v['x']
        if x.get('dna') is not None and x['dna'] < -TOL:
            out.append((p, 'DNA', x['dna'], (p, 'DNA') in EXCEPT))
        if x.get('bs_ta') is not None:
            tot = sum(n(x.get(k)) for k in ('bs_cash', 'bs_td', 'bs_ar', 'bs_inv', 'bs_oca', 'bs_ppe', 'bs_rou', 'bs_intang', 'bs_fin', 'bs_onca'))
            out.append((p, 'BS lines = TA', round(tot - x['bs_ta'], 6), abs(tot - x['bs_ta']) <= TOL))
    bad = [o for o in out if not o[3]]
    exc = [o for o in out if o[3] and abs(o[2]) > TOL]
    print(f'{len(out)} checks, {len(bad)} failures, {len(exc)} explained exceptions')
    for t, k, d, _ in exc: print(f'  exception {t} {k}: {d:+.6f} — {EXCEPT.get((t, k), "")}')
    for t, k, d, _ in bad: print(f'  FAIL {t} {k}: {d:+.6f}')
    return 1 if bad else 0

if __name__ == '__main__':
    sys.exit(main())
