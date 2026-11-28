"""Fetch the site's static files into the module and record the URL map.

The files are pulled from the running site by the exact URLs the pages ask
for, rather than copied out of the mirror or the source tree. The mirror is
no good for this: wget renames anything the server labels oddly, and it
saved hero-poster.webp as hero-poster.webp.html, which then never matched
the URL in the markup. The source tree is no good either: the theme files
are assembled by collectstatic and do not sit under static/ before that.
Asking the site for the URL in the page settles both.

Django stamps a content hash into every static filename. That hash is
dropped here - the files keep plain names inside the module - and comes
back as a ?v= stamp on the URL, computed from the bytes actually written.
Without it a browser keeps serving the copy it already has: these files are
linked from the page rather than bundled, so Odoo's own cache-busting never
reaches them, and a corrected stylesheet would not arrive until someone
thought to hard-refresh.

The map from old URL to new, stamp included, is written out for the page
rewriter; the bare hashes go to fingerprints.json for the two files the
Odoo build adds itself.
"""
import hashlib
import json
import os
import re
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
MIRROR = os.environ.get('AKT_MIRROR',
                        '/home/ahmed-salah/Desktop/cluade/akt_site_mirror2')
BASE = os.environ.get('AKT_BASE', 'https://aktgroup.pythonanywhere.com')
MOD = '/home/ahmed-salah/Desktop/cluade/AKT/akt_website'
STATIC = os.path.join(MOD, 'static/src')

UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                    '(KHTML, like Gecko) Chrome/140.0 Safari/537.36'}

# Where each kind of static file lands inside the module.
TREE = {'css': 'css', 'js': 'js', 'fonts': 'fonts', 'images': 'img',
        'videos': 'video', 'vendor': 'vendor', 'themes': 'themes'}

STATIC_REF = re.compile(r'/static/[A-Za-z0-9_./-]+')
ASSET_REF = re.compile(r'/assets/[0-9a-f-]{36}/')
CSS_URL = re.compile(r'url\((["\']?)([^)"\']+)\1\)')
HASH = re.compile(r'^(?P<stem>.+?)\.(?P<hash>[0-9a-f]{12})(?P<ext>\.[^.]+)$')


def dehash(name):
    m = HASH.match(name)
    return m.group('stem') + m.group('ext') if m else name


def target(url):
    """Module-relative path for a /static/... URL."""
    rest = url[len('/static/'):]
    head, _, tail = rest.rpartition('/')
    top, _, sub = head.partition('/')
    sub = os.path.join(TREE.get(top, top), sub) if top in TREE else head
    return os.path.join(sub, dehash(tail))


def fetch(url):
    req = urllib.request.Request(BASE + url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


PRINTS = {}


def save(rel, data):
    path = os.path.join(STATIC, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as fh:
        fh.write(data)
    PRINTS[rel.replace(os.sep, '/')] = hashlib.sha1(data).hexdigest()[:12]
    return path


def stamped(rel):
    rel = rel.replace(os.sep, '/')
    return '/akt_website/static/src/%s?v=%s' % (rel, PRINTS[rel])


def referenced():
    """Every /static/ and /assets/ URL the mirrored pages ask for."""
    static, assets = set(), set()
    for lang in ('ar', 'en'):
        root = os.path.join(MIRROR, lang)
        for dirpath, _dirs, files in os.walk(root):
            if 'index.html' not in files:
                continue
            text = open(os.path.join(dirpath, 'index.html'), encoding='utf-8').read()
            static.update(STATIC_REF.findall(text))
            assets.update(ASSET_REF.findall(text))
    return sorted(static), sorted(assets)


# Two files belong to the Odoo build rather than to the site, and are
# written here so that wiping static/ and regenerating cannot lose them.
AKT_CSS = """/* What the Odoo build adds to the site. */

/* Take the writing direction from the attribute Odoo puts on <html>.
   Odoo's frontend stylesheet is mirrored for a right-to-left language by
   rtlcss, a node tool it shells out to; when that tool is not installed
   Odoo logs a warning and stores the stylesheet unmirrored anyway, under
   the .rtl name. The sheet then sets `body { direction: ltr }` on an
   Arabic page, and the whole site lays itself out left-to-right with the
   logo on the wrong side - while <html dir="rtl"> says otherwise.

   The site brings its own right-to-left bootstrap and writes its own rules
   with logical properties, so it does not need Odoo's mirroring; it only
   needs the direction not to be taken away from it. Installing rtlcss on
   the server is still worth doing, for Odoo's own screens. */
html[dir="rtl"] body { direction: rtl; }
html[dir="ltr"] body { direction: ltr; }

/* Drop the clearfix Odoo still puts on .container.

   Odoo's stylesheet carries the old Bootstrap clearfix:
   `.container::before, .container::after { content: ""; display: table }`.
   Harmless where a container holds floats - but this site puts `container`
   on elements that are CSS grids and flex rows, and a pseudo-element of a
   grid or flex container is an item in it. Two empty boxes then take the
   first and last cells: on the About page the image was pushed into the
   second column and the text onto a row of its own, which read as half the
   page having gone blank. The header and the footer are built the same way,
   on every page.

   Scoped to #wrapwrap so Odoo's own screens keep their clearfix. */
#wrapwrap .container::before,
#wrapwrap .container::after {
  content: none;
}

/* Odoo styles its own page header as `header#top { z-index: 1030 }`. The
   site's hero is also a <header id="top"> - that id is the anchor the
   back-to-top button points at - so Odoo's rule lifts the hero above the
   site header, and the "More about AKT" panel opens behind the hero image
   instead of over it. The hero needs no stacking order of its own: it
   isolates itself, so its own ::after overlay still sits where it should. */
main header#top {
  z-index: auto;
}

/* The result of a form post. */
.akt-form-result {
  border-radius: 10px;
  padding: 14px 16px;
  display: grid;
  gap: 4px;
  margin-bottom: 18px;
}
.akt-form-result strong { font-weight: 700; }
.akt-form-ok {
  background: #eef7f0;
  border: 1px solid #b7dcc2;
  color: #1d5b32;
}
.akt-form-error {
  background: #fdf0ef;
  border: 1px solid #efc2bd;
  color: #7d2a22;
}
"""

AKT_JS = """/* The FAQ list is one page of static entries, so its search box filters in
   the browser instead of asking the server - the Django build queried the
   database, and there is no database behind these entries any more. */
(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    var form = document.querySelector(".feature-search");
    if (!form) { return; }
    var q = form.querySelector('input[name="q"]');
    var cat = form.querySelector('select[name="category"]');
    var items = Array.prototype.slice.call(
      document.querySelectorAll("[data-faq-item], .faq-card, .faq-list > li")
    );
    if (!items.length) { return; }

    function apply(event) {
      if (event) { event.preventDefault(); }
      var needle = (q && q.value || "").trim().toLowerCase();
      var want = cat && cat.value || "";
      items.forEach(function (item) {
        var text = (item.textContent || "").toLowerCase();
        var itemCat = item.getAttribute("data-faq-category") || "";
        item.hidden = !((!needle || text.indexOf(needle) !== -1) &&
                        (!want || itemCat === want));
      });
    }

    form.addEventListener("submit", apply);
    if (q) { q.addEventListener("input", apply); }
    if (cat) { cat.addEventListener("change", apply); }
    apply();
  });
})();
"""


def main():
    url_map = {}
    static_urls, asset_urls = referenced()

    # A stylesheet names fonts and sprites of its own, by a path relative to
    # itself. Those are fetched too, and the reference is rewritten to the
    # absolute module path - Odoo serves the sheet from somewhere else.
    queue = list(static_urls)
    seen = set()
    while queue:
        url = queue.pop(0)
        if url in seen:
            continue
        seen.add(url)
        try:
            data = fetch(url)
        except Exception as exc:                        # noqa: BLE001
            print('   MISSING %s (%s)' % (url, exc))
            continue
        rel = target(url)

        if url.endswith('.css'):
            text = data.decode('utf-8')

            def one(m, base=os.path.dirname(url)):
                quote, ref = m.group(1), m.group(2)
                if ref.startswith(('data:', 'http', '/', '#')):
                    return m.group(0)
                child = os.path.normpath(os.path.join(base, ref))
                if child not in seen:
                    queue.append(child)
                return 'url(%s/akt_website/static/src/%s%s)' % (
                    quote, target(child).replace(os.sep, '/'), quote)
            data = CSS_URL.sub(one, text).encode('utf-8')

        save(rel, data)
        url_map[url] = stamped(rel)

    # The uploaded media the site serves from /assets/<uuid>/ with no
    # extension. They are WebP; the uuid is kept as the filename so the
    # mapping stays obvious if anybody compares the two sites.
    for url in asset_urls:
        uuid = url.strip('/').split('/')[-1]
        try:
            data = fetch(url)
        except Exception as exc:                        # noqa: BLE001
            print('   MISSING %s (%s)' % (url, exc))
            continue
        save('img/assets/%s.webp' % uuid, data)
        url_map[url] = stamped('img/assets/%s.webp' % uuid)

    save('css/akt_odoo.css', AKT_CSS.encode('utf-8'))
    save('js/akt_faq_filter.js', AKT_JS.encode('utf-8'))

    with open(os.path.join(HERE, 'url_map.json'), 'w') as fh:
        json.dump(url_map, fh, indent=1, sort_keys=True)
    with open(os.path.join(HERE, 'fingerprints.json'), 'w') as fh:
        json.dump(PRINTS, fh, indent=1, sort_keys=True)
    print('fetched %d static files and %d media files'
          % (len(seen), len(asset_urls)))


if __name__ == '__main__':
    main()
