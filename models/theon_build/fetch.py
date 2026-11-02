"""Download Theon's regulated reports and releases (doc_urls.txt) into $THEON_SRC/pdf and convert them to text in $THEON_SRC/txt
(pdftotext -layout). Raw files stay outside the repository. Needs network access to media.theon.com (allow it in the environment).
Usage: THEON_SRC=/path/to/src python3 fetch.py"""
import os, subprocess, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('THEON_SRC') or os.path.join(os.path.expanduser('~'), 'theon_src')
UA = os.environ.get('SEC_UA', 'Industrials Optima research (contact via repository owner)')

def main():
    os.makedirs(os.path.join(SRC, 'pdf'), exist_ok=True); os.makedirs(os.path.join(SRC, 'txt'), exist_ok=True)
    for url in [u.strip() for u in open(os.path.join(HERE, 'doc_urls.txt')) if u.strip()]:
        name = url.rsplit('/', 1)[1]
        pdf = os.path.join(SRC, 'pdf', name); txt = os.path.join(SRC, 'txt', name[:-4] + '.txt')
        if not os.path.exists(pdf):
            for attempt in range(4):
                try:
                    req = urllib.request.Request(url, headers={'User-Agent': UA})
                    with urllib.request.urlopen(req, timeout=120) as r, open(pdf, 'wb') as f: f.write(r.read())
                    break
                except Exception as e:
                    print('retry', name, e); time.sleep(2 ** (attempt + 1))
            time.sleep(0.3)
        if os.path.exists(pdf) and not os.path.exists(txt):
            subprocess.run(['pdftotext', '-layout', pdf, txt], check=False, capture_output=True)
        print('ok' if os.path.exists(txt) else 'MISSING', name)

if __name__ == '__main__':
    main()
