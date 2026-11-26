"""Shared pieces of the akt_website generator."""
import json
import os
import re

import htmlslice

HERE = os.path.dirname(os.path.abspath(__file__))
MIRROR = '/home/ahmed-salah/Desktop/cluade/akt_site_mirror'
MOD = '/home/ahmed-salah/Desktop/cluade/AKT/akt_website'

URL_MAP = json.load(open(os.path.join(HERE, 'url_map.json')))

MAIN = re.compile(r'<main[^>]*id="main"')
HEADER = re.compile(r'<header class="site-header">')
FOOTER = re.compile(r'<footer class="site-footer">')
FLOAT = re.compile(r'<div class="contact-float">')

# The CSS and JS of the page head become asset bundle entries, so their old
# URLs are not rewritten - they are dropped from the markup altogether.
BUNDLED = re.compile(r'/static/(css|js|vendor)/')


def pages(lang):
    """Every mirrored page of one language as (url_path, file)."""
    out = []
    root = os.path.join(MIRROR, lang)
    for dirpath, _dirs, files in os.walk(root):
        if 'index.html' not in files:
            continue
        rel = os.path.relpath(dirpath, root).replace(os.sep, '/')
        url = '/' if rel == '.' else '/' + rel
        out.append((url, os.path.join(dirpath, 'index.html')))
    return sorted(out)


def page_key(url):
    """Template name for a page URL: / -> homepage, /a/b -> page_a_b."""
    if url == '/':
        return 'homepage'
    return 'page_' + url.strip('/').replace('/', '_').replace('-', '_')


_INTERNAL = re.compile(r'(href|action)="/(?:ar|en)(/[^"]*)?"')
_TRAILING = re.compile(r'(href|action)="(/[^"?#]*?)/(?=["?#])')


def rewrite_urls(raw, lang):
    """Point the markup at Odoo.

    Three things change: the language prefix comes off every internal link
    because Odoo puts it back per language; the trailing slash comes off
    because an Odoo page URL carries none and the redirect would cost a hop;
    and the static files move under the module.
    """
    out = _INTERNAL.sub(lambda m: '%s="%s"' % (m.group(1), m.group(2) or '/'), raw)
    # The closing quote is left to the lookahead, not written again.
    out = _TRAILING.sub(lambda m: '%s="%s' % (m.group(1), m.group(2) or '/'), out)
    for old, new in sorted(URL_MAP.items(), key=lambda kv: -len(kv[0])):
        if BUNDLED.search(old):
            continue
        out = out.replace(old, new)
    return out


def body(path, lang, pat=MAIN):
    src = open(path, encoding='utf-8').read()
    raw = htmlslice.slice_element(src, pat)
    if raw is None:
        raise SystemExit('no match for %s in %s' % (pat.pattern, path))
    return htmlslice.xmlify(rewrite_urls(raw, lang))


def head_bits(path):
    """The per-page head data Odoo cannot derive: title, description, ld+json."""
    src = open(path, encoding='utf-8').read()
    t = re.search(r'<title>(.*?)</title>', src, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', src)
    ld = re.search(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)
    leaflet = '/static/vendor/leaflet/' in src
    return {
        'title': t.group(1).strip() if t else '',
        'description': d.group(1) if d else '',
        'ld_json': ld.group(1).strip() if ld else '',
        'leaflet': leaflet,
    }
