"""Compare both language versions of every page against the preview site."""
import re
import sys
import urllib.request

from bs4 import BeautifulSoup

sys.path.insert(0, '/home/ahmed-salah/Desktop/cluade/akt_website_build/tools')
import common

BASE = 'http://127.0.0.1:8169'
# Arabic is the site's default language, so Odoo serves it unprefixed.
PREFIX = {'ar': '', 'en': '/en'}


def text(frag):
    s = BeautifulSoup(str(frag), 'html.parser')
    for t in s(['script', 'style']):
        t.decompose()
    return re.sub(r'\s+', ' ', s.get_text(' ')).strip()


def fetch(url):
    req = urllib.request.Request(url, headers={
        # A browser-shaped request: Odoo serves a bot the default language
        # whatever it asks for, which would hide the negotiation entirely.
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/140.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
    })
    with urllib.request.urlopen(req) as r:
        return r.read().decode('utf-8')


totals = {}
for lang in ('ar', 'en'):
    ok = bad = 0
    for url, path in common.pages(lang):
        page = PREFIX[lang] + ('' if url == '/' else url)
        got = BeautifulSoup(fetch(BASE + (page or '/')), 'html.parser')
        want = BeautifulSoup(open(path, encoding='utf-8').read(), 'html.parser')
        issues = []
        for part in ('main', 'header', 'footer'):
            g, w = got.find(part), want.find(part)
            if not g:
                issues.append('%s missing' % part)
            elif text(g) != text(w):
                issues.append('%s differs (%d vs %d)' % (part, len(text(g)), len(text(w))))
        gt = (got.title.string or '').strip()
        wt = (want.title.string or '').strip()
        if gt != wt:
            issues.append('title %r != %r' % (gt, wt))
        if issues:
            bad += 1
            print('%s DIFF %-32s %s' % (lang, url, '; '.join(issues)))
        else:
            ok += 1
    totals[lang] = (ok, bad)
for lang, (ok, bad) in totals.items():
    print('%s: identical %d / different %d' % (lang, ok, bad))
