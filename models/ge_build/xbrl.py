"""Cross-check of the normalised data against EDGAR XBRL company facts (us-gaap, General Electric Company, CIK 40545).

For each period the fact is taken from the same filing the model uses (accession match), so that recast comparatives are compared
with recast facts. Three-month facts only exist for the 10-Q quarters; Q4 and derived quarters are skipped. Run after extract.py:
`python3 xbrl.py` (needs $GE_SRC/cf_40545.json, or data/_xbrl.json written by dump_subset())."""
import json, os, datetime as dt
import normalize
S = os.environ.get('GE_SRC', '/tmp/ge_src')
SUBSET = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '_xbrl.json')
# ni_cont_co: GE tags IncomeLossFromContinuingOperations as the amount attributable to the company (after NCI)
CHECKS = [('rev', ['Revenues']), ('ebt', ['IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest']),
          ('ni_cont_co', ['IncomeLossFromContinuingOperations']), ('eps_cont_d', ['IncomeLossFromContinuingOperationsPerDilutedShare']),
          ('cf_cfo', ['NetCashProvidedByUsedInOperatingActivitiesContinuingOperations']), ('bs_ta', ['Assets']),
          ('sh_d', ['WeightedAverageNumberOfDilutedSharesOutstanding'])]

def facts():
    raw = os.path.join(S, 'cf_40545.json')
    if os.path.exists(raw):
        d = json.load(open(raw))['facts']['us-gaap']
        keep = {k for _, ks in CHECKS for k in ks}
        F = {k: [f for u in v['units'].values() for f in u if f.get('form') in ('10-K', '10-Q')] for k, v in d.items() if k in keep}
        json.dump(F, open(SUBSET, 'w'), separators=(',', ':'))
        return F
    return json.load(open(SUBSET))

def months(f):
    if 'start' not in f: return 0
    return round((dt.date.fromisoformat(f['end']) - dt.date.fromisoformat(f['start'])).days / 30.4)

END = {1: '03-31', 2: '06-30', 3: '09-30', 4: '12-31'}
def run():
    D = normalize.run(); F = facts(); out, n = [], 0
    for p in normalize.periods():
        x = dict(D.get(p, {}).get('x', {}))
        if x.get('ni_cont') is not None: x['ni_cont_co'] = x['ni_cont'] - x.get('nci_cont', 0.0)
        rec = normalize.REC.get(p, {})
        accs = {u.split('/')[-2] for u in rec.get('sources', []) if '/Archives/' in u}
        y, q = normalize.fyq(p)
        end = f'{y}-{END[q]}'; m = 12 if p.isdigit() else 3
        for key, cs in CHECKS:
            v = x.get(key)
            if v is None: continue
            for c in cs:
                hits = [f for f in F.get(c, []) if f['end'] == end and (key == 'bs_ta' or months(f) == m) and f['accn'].replace('-', '') in accs]
                if not hits: continue
                fv = hits[0]['val']
                fv = fv if key == 'eps_cont_d' else fv / 1e6
                n += 1
                tol = 0.011 if key == 'eps_cont_d' else 1.01
                if abs(fv - v) > tol: out.append(f'{p} {key}: model {v:,.2f} vs XBRL {c} {fv:,.2f}')
                break
    return n, out

if __name__ == '__main__':
    n, out = run()
    print('\n'.join(out) or 'XBRL cross-check: all match'); print(n, 'facts compared')
