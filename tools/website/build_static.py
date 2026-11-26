"""Copy the mirrored static files into the module and record the URL map.

Django stamps a content hash into every static filename; Odoo does its own
cache-busting on the asset bundles, so the hash is dropped here and the map
from old URL to new one is written out for the page rewriter to use.
"""
import json
import os
import re
import shutil

MIRROR = '/home/ahmed-salah/Desktop/cluade/akt_site_mirror'
MOD = '/home/ahmed-salah/Desktop/cluade/AKT/akt_website'
STATIC = os.path.join(MOD, 'static/src')

# mirror subdir -> module subdir
TREE = {
    'static/css': 'css',
    'static/js': 'js',
    'static/fonts': 'fonts',
    'static/images': 'img',
    'static/videos': 'video',
    'static/vendor': 'vendor',
}

HASH = re.compile(r'^(?P<stem>.+?)\.(?P<hash>[0-9a-f]{12})(?P<ext>\.[^.]+)$')


def dehash(name):
    m = HASH.match(name)
    return m.group('stem') + m.group('ext') if m else name


# Two files belong to the Odoo build rather than to the mirrored site, and
# are written here so that wiping static/ and regenerating cannot lose them.
AKT_CSS = """/* What the Odoo build adds to the site: the result of a form post. */
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


def write_own():
    for rel, text in (('css/akt_odoo.css', AKT_CSS), ('js/akt_faq_filter.js', AKT_JS)):
        path = os.path.join(STATIC, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        print('   wrote', rel)


def main():
    url_map = {}
    for src_rel, dst_rel in TREE.items():
        src = os.path.join(MIRROR, src_rel)
        for root, _dirs, files in os.walk(src):
            for f in files:
                sub = os.path.relpath(os.path.join(root, f), src)
                out_sub = os.path.join(os.path.dirname(sub), dehash(f))
                dst = os.path.join(STATIC, dst_rel, out_sub)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(os.path.join(root, f), dst)
                url_map['/%s/%s' % (src_rel, sub.replace(os.sep, '/'))] = \
                    '/akt_website/static/src/%s/%s' % (dst_rel, out_sub.replace(os.sep, '/'))

    # The uploaded media the Django app served from /assets/<uuid>/ with no
    # extension. They are all WebP; the uuid is kept as the filename so the
    # mapping stays obvious if anybody compares the two sites.
    adir = os.path.join(STATIC, 'img/assets')
    os.makedirs(adir, exist_ok=True)
    for uuid in sorted(os.listdir(os.path.join(MIRROR, 'assets'))):
        src = os.path.join(MIRROR, 'assets', uuid, 'index.html')
        if not os.path.isfile(src):
            continue
        shutil.copy2(src, os.path.join(adir, uuid + '.webp'))
        url_map['/assets/%s/' % uuid] = \
            '/akt_website/static/src/img/assets/%s.webp' % uuid

    # The stylesheets point at the fonts and the Leaflet sprites by their
    # hashed names and by a path relative to the stylesheet. Odoo serves the
    # bundle from somewhere else entirely, so both are rewritten to the
    # absolute module path.
    rel = re.compile(r'url\((["\']?)((?:\.\./)?)([A-Za-z0-9_./-]+\.(?:ttf|woff2?|png|jpg|svg|gif))\1\)')

    def fix(css_path, base):
        text = open(css_path, encoding='utf-8').read()

        def one(m):
            quote, updir, ref = m.group(1), m.group(2), m.group(3)
            head, _, tail = ref.rpartition('/')
            target = os.path.normpath(os.path.join(base, updir, head, dehash(tail)))
            return 'url(%s/akt_website/static/src/%s%s)' % (
                quote, os.path.relpath(target, STATIC).replace(os.sep, '/'), quote)
        out = rel.sub(one, text)
        if out != text:
            open(css_path, 'w', encoding='utf-8').write(out)
            print('   rewrote url() in', os.path.relpath(css_path, STATIC))

    for sub in ('css', 'vendor', 'vendor/leaflet'):
        d = os.path.join(STATIC, sub)
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith('.css'):
                fix(os.path.join(d, f), os.path.join(STATIC, sub))

    write_own()

    with open(os.path.join(os.path.dirname(__file__), 'url_map.json'), 'w') as fh:
        json.dump(url_map, fh, indent=1, sort_keys=True)
    print('copied %d static files' % len(url_map))
    for k, v in sorted(url_map.items())[:6]:
        print('  ', k, '->', v)


if __name__ == '__main__':
    main()
