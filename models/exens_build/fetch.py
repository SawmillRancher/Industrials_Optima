"""Download the source documents listed in filings.csv into $EXENS_SRC/pdf and convert them to text ($EXENS_SRC/txt, pdftotext -layout).
Raw documents are not committed. The period files in data/ were transcribed from these text files following EXTRACTION_SCHEMA.md."""
import csv, os, subprocess, time, urllib.request

SRC = os.environ.get('EXENS_SRC', os.path.expanduser('~/exens_src'))
UA = os.environ.get('UA', 'Mozilla/5.0 (X11; Linux x86_64) research')
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    os.makedirs(os.path.join(SRC, 'pdf'), exist_ok=True); os.makedirs(os.path.join(SRC, 'txt'), exist_ok=True)
    for row in csv.DictReader(open(os.path.join(HERE, 'filings.csv'))):
        url = row['url']
        if not url.lower().endswith('.pdf'): continue
        pdf = os.path.join(SRC, 'pdf', row['key'] + '.pdf'); txt = os.path.join(SRC, 'txt', row['key'] + '.txt')
        if not os.path.exists(pdf):
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=300) as r, open(pdf, 'wb') as f: f.write(r.read())
            time.sleep(1.0)
        if not os.path.exists(txt):
            subprocess.run(['pdftotext', '-layout', pdf, txt], check=True)
        print(row['key'], os.path.getsize(pdf))

if __name__ == '__main__':
    main()
