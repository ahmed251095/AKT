"""Generate the akt_website module from the mirrored site.

Everything under AKT/akt_website except static/ is written by this script, so
the module can be regenerated when the preview site changes rather than being
patched by hand.
"""
import html
import json
import os
import re

import common
import htmlslice
import forms
import navtree

MOD = common.MOD
HEAD = '<?xml version="1.0" encoding="utf-8"?>\n<odoo>\n'
TAIL = '</odoo>\n'


def write(rel, text):
    path = os.path.join(MOD, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(text)
    return rel


def indent(text, n):
    pad = ' ' * n
    return '\n'.join(pad + l if l.strip() else l for l in text.splitlines())


# --------------------------------------------------------------- manifest
MANIFEST = '''\
{
    'name': 'AKT Group Website',
    'summary': 'The AKT Group public site, as an Odoo website',
    'description': """
The public site of AKT Group for General Contracting and Development,
rebuilt page for page on Odoo's website so every page stays editable from
the builder. Arabic is the site's language and English is the translation;
the quotation, contact, appointment and supplier forms open CRM leads.
""",
    'author': 'AKT Group',
    'website': 'https://www.akt-grp.com',
    'category': 'Website',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['website', 'crm'],
    'data': [
        'views/assets.xml',
        'data/crm_data.xml',
        'views/layout.xml',
        'views/pages.xml',
        'views/form_messages.xml',
        'data/sync.xml',
    ],
    'post_init_hook': 'post_init',
    'installable': True,
    'application': True,
}
'''

INIT = '''\
from . import controllers
from . import models
from .hooks import post_init
'''


# ----------------------------------------------------------------- assets
# The stylesheets are linked from the page instead of joining Odoo's
# frontend bundle, which is how the site serves them anyway. Odoo mirrors
# that bundle with rtlcss on an Arabic page, and these sheets must not be
# mirrored: the vendor bootstrap is the RTL build already, and the site's own
# CSS is written with logical properties that are right in both directions.
# Mirroring turned direction:ltr into direction:rtl and put the hero caption
# back to front. rtlcss can be told to skip a block, but Odoo strips CSS
# comments before handing the bundle over, so the instruction never arrives.
#
# Both lists are read off the mirrored pages rather than written out here,
# so that a change of theme - the look is a theme laid over the base sheets -
# is picked up by re-running the generator instead of being missed.
_CSS_RE = re.compile(r'<link rel="stylesheet" href="([^"]+)"')
_JS_RE = re.compile(r'<script src="([^"]+)"')


def _page_assets(pattern, lang):
    """The longest asset list any page of a language carries, in its order.

    Most pages share one list; the three with a map add Leaflet part-way
    through it. Taking the longest keeps both the extra file and its place.
    """
    best = ()
    for _url, path in common.pages(lang):
        found = tuple(pattern.findall(open(path, encoding='utf-8').read()))
        if len(found) > len(best):
            best = found
    return [common.URL_MAP.get(u, u) for u in best]


PRINTS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                     'fingerprints.json')))


def stamped(rel):
    """A module static URL carrying the hash of its own bytes.

    The stylesheets are linked from the page, not bundled, so nothing else
    tells a browser that one of them changed.
    """
    return '/akt_website/static/src/%s?v=%s' % (rel, PRINTS[rel])


def css_files(lang):
    # akt_odoo.css is the Odoo build's own, and goes last so it wins.
    return _page_assets(_CSS_RE, lang) + [stamped('css/akt_odoo.css')]


def js_files(lang='en'):
    # The scripts go into Odoo's frontend bundle, whose own URL already
    # changes with its contents - and an ir.asset path cannot carry a query
    # string anyway, so the stamp comes back off here.
    files = _page_assets(_JS_RE, lang) + ['/akt_website/static/src/js/akt_faq_filter.js']
    return [f.partition('?')[0] for f in files]


def assets_xml():
    rows = []
    for i, f in enumerate(js_files()):
        rows.append('''\
  <record id="asset_%(key)s" model="ir.asset">
    <field name="name">AKT %(f)s</field>
    <field name="bundle">web.assets_frontend</field>
    <field name="path">%(f)s</field>
    <field name="sequence">%(seq)d</field>
  </record>''' % {'key': re.sub(r'\W', '_', f.rsplit('/src/', 1)[-1]),
                  'f': f.lstrip('/'), 'seq': 20 + i})
    note = '''\
  <!--
    The site's scripts, at the end of Odoo's frontend bundle and in the order
    the site loads them: the libraries first, then the site's own. The
    stylesheets are not here - see CSS in tools/build_module.py for why they
    are linked from the page instead.
  -->
'''
    return HEAD + note + '\n'.join(rows) + '\n' + TAIL


# ------------------------------------------------------------------ menus
def menus_json():
    """The nav bar, in both languages, for the install hook to create."""
    import json
    en, ar = navtree.tree('en'), navtree.tree('ar')
    out = []
    for m_en, m_ar in zip(en, ar):
        out.append({
            'url': m_en['url'], 'en': m_en['name'], 'ar': m_ar['name'],
            'children': [{'url': c_en['url'], 'en': c_en['name'], 'ar': c_ar['name']}
                         for c_en, c_ar in zip(m_en['children'], m_ar['children'])],
        })
    return json.dumps(out, ensure_ascii=False, indent=2) + '\n'


def _unused_menus_xml():
    nav = navtree.tree('en')
    rows = ['''\
  <record id="menu_top" model="website.menu">
    <field name="name">AKT Group</field>
    <field name="website_id" ref="website.default_website"/>
  </record>''']
    for i, m in enumerate(nav):
        mid = 'menu_%s' % re.sub(r'\W', '_', m['url'].strip('/') or 'more')
        rows.append('''\
  <record id="%(id)s" model="website.menu">
    <field name="name">%(name)s</field>
    <field name="url">%(url)s</field>
    <field name="parent_id" ref="menu_top"/>
    <field name="sequence">%(seq)d</field>
    <field name="website_id" ref="website.default_website"/>
  </record>''' % {'id': mid, 'name': esc(m['name']), 'url': m['url'],
                  'seq': 10 * (i + 1)})
        for j, c in enumerate(m['children']):
            rows.append('''\
  <record id="%(id)s" model="website.menu">
    <field name="name">%(name)s</field>
    <field name="url">%(url)s</field>
    <field name="parent_id" ref="%(parent)s"/>
    <field name="sequence">%(seq)d</field>
    <field name="website_id" ref="website.default_website"/>
  </record>''' % {'id': 'menu_%s' % re.sub(r'\W', '_', c['url'].strip('/')),
                  'name': esc(c['name']), 'url': c['url'], 'parent': mid,
                  'seq': 10 * (j + 1)})
    return (HEAD + '  <data noupdate="0">\n'
            + '\n'.join(indent(r, 2) for r in rows) + '\n  </data>\n' + TAIL)


def esc(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


# ----------------------------------------------------------------- layout
def layout_children(lang):
    """The body of the layout template, for one language.

    Both languages go through this so the term lists the translation table
    ships line up with what Odoo will read back out of the stored view.
    """
    f = dict(common.pages(lang))['/']
    hdr = common.body(f, lang, common.HEADER)
    footer = common.body(f, lang, common.FOOTER)
    flt = common.body(f, lang, common.FLOAT)

    # The nav and the language switch become QWeb; the rest of the header is
    # the markup the preview site serves.
    nav = htmlslice.slice_element(hdr, re.compile(r'<nav[^>]*id="primary-nav"'))
    lang_a = htmlslice.slice_element(hdr, re.compile(r'<a class="language-switch"'))
    nav_label = re.search(r'aria-label="([^"]*)"', nav).group(1)

    qweb_nav = '''<nav id="primary-nav" aria-label="%s">
        <t t-foreach="website.menu_id.child_id" t-as="akt_menu">
          <details t-if="akt_menu.child_id" class="nav-more">
            <summary t-out="akt_menu.name"/>
            <div>
              <a t-foreach="akt_menu.child_id" t-as="akt_sub"
                 t-att-href="akt_sub.url" t-out="akt_sub.name"/>
            </div>
          </details>
          <a t-else="" t-att-href="akt_menu.url" t-out="akt_menu.name"/>
        </t>
      </nav>''' % nav_label

    # One link to the other language, labelled with its own code, the way the
    # preview site does it. url_localized keeps the visitor on the same page.
    # The switch posts the visitor through Odoo's own language route.
    #
    # A plain link cannot do it. Odoo strips the prefix of the default
    # language from every href it renders, so a link to /ar/services comes
    # out as /services - and arriving there with a frontend_lang cookie that
    # still says English sends the visitor straight back to /en/services.
    # Switching to Arabic appeared to do nothing at all.
    #
    # /website/lang/<url_code>?r=<path> sets the cookie and then redirects,
    # and is declared multilang=False so Odoo leaves the href alone. The
    # js_change_lang class is deliberately absent: its handler wraps an
    # href in this very route, and would wrap this one a second time.
    qweb_lang = '''<t t-set="akt_switch_labels" t-value="{'ar': 'عربي', 'en': 'EN'}"/>
      <t t-foreach="frontend_languages.values()" t-as="akt_lg">
        <t t-if="akt_lg.code != lang">
          <t t-set="akt_path" t-value="main_object.url if main_object and 'url' in main_object._fields and main_object.url else '/'"/>
          <a class="language-switch"
             t-att-lang="akt_lg.url_code"
             t-attf-href="/website/lang/#{akt_lg.url_code}?r=#{akt_path}"
             t-out="akt_switch_labels.get(akt_lg.url_code, akt_lg.url_code.upper())"/>
        </t>
      </t>
      <!-- The way in to Odoo. A visitor is offered the login page; someone
           already signed in gets their own name, linking to the backend,
           rather than an invitation to log in again. -->
      <t t-if="request.env.user._is_public()">
        <a class="akt-login" href="/web/login">Log in</a>
      </t>
      <t t-else="">
        <a class="akt-login" href="/odoo" t-out="request.env.user.name"/>
      </t>'''

    header = hdr.replace(nav, qweb_nav).replace(lang_a, qweb_lang)
    header = header.replace('<header class="site-header">',
                            '<header class="site-header" data-name="Header">', 1)
    footer = footer.replace('<footer class="site-footer">',
                            '<footer class="site-footer" id="bottom" data-name="Footer">', 1)

    skip = htmlslice.slice_element(
        open(f, encoding='utf-8').read(), re.compile(r'<a class="skip"'))
    back = htmlslice.xmlify(htmlslice.slice_element(
        open(f, encoding='utf-8').read(), re.compile(r'<button class="back-to-top"')))

    return '''\
  <!--
    Odoo's own header and footer are swapped for the site's, and <main> gets
    the id the skip link points at. The page's own markup still goes inside
    <main>, so the builder edits it exactly as it would any other page.
  -->
  <template id="layout" inherit_id="website.layout" name="AKT Group layout">

    <xpath expr="//header" position="replace">%(header)s</xpath>

    <xpath expr="//footer" position="replace">%(footer)s</xpath>

    <xpath expr="//main" position="attributes">
      <attribute name="id">main</attribute>
    </xpath>

    <xpath expr="//div[@id='wrapwrap']" position="before">
      %(skip)s
    </xpath>

    <xpath expr="//div[@id='wrapwrap']" position="inside">%(float)s%(back)s</xpath>

    <xpath expr="//head" position="inside">
%(css)s
      <meta name="theme-color" content="#0a1d37"/>
      <link rel="preload" as="image" fetchpriority="high"
            href="%(poster)s"/>
      <t t-if="akt_ld_json">
        <script type="application/ld+json" t-out="akt_ld_json"/>
      </t>
    </xpath>
  </template>
''' % {'header': header, 'footer': footer, 'float': flt,
       'skip': skip, 'back': back,
       'poster': stamped('img/hero-poster.webp'),
       'css': _css_block()}


def _css_block():
    """The stylesheet links, which are not the same in both languages.

    The Arabic pages load the RTL build of bootstrap and the English pages
    the ordinary one, so the two lists are emitted whole behind a test on
    the language's direction rather than diffed into a single list.
    """
    def links(lang, indent):
        return '\n'.join('%s<link rel="stylesheet" href="%s"/>' % (indent, f)
                         for f in css_files(lang))
    return (
        '      <t t-set="akt_rtl" t-value="request.env[\'res.lang\']'
        '._get_data(code=lang).direction == \'rtl\'"/>\n'
        '      <t t-if="akt_rtl">\n%s\n      </t>\n'
        '      <t t-else="">\n%s\n      </t>'
        % (links('ar', ' ' * 8), links('en', ' ' * 8)))


def layout_xml():
    return HEAD + layout_children('en') + TAIL


# ------------------------------------------------------------------ pages
def page_children(url, lang):
    """The body of a page template, for one language."""
    f = dict(common.pages(lang))[url]
    head = common.head_bits(f)
    inner = forms.rewrite(url, htmlslice.inner(common.body(f, lang)))
    ld = head['ld_json'].replace(']]>', ']]]]><![CDATA[>')
    return '''
    <t t-call="website.layout">
      <t t-set="akt_ld_json"><![CDATA[%(ld)s]]></t>
      <div id="wrap" class="oe_structure">%(body)s</div>
    </t>
  ''' % {'ld': ld, 'body': inner}


def pages_xml():
    out = [HEAD, '''\
  <!--
    One template and one website.page per page of the preview site. The body
    is the markup the site serves, with the language prefix taken off the
    links because Odoo puts it back, and the title and description kept as
    the page's SEO fields so the <title> reads the same.
  -->
''']
    for url, f in common.pages('en'):
        key = common.page_key(url)
        head = common.head_bits(f)
        children = page_children(url, 'en')
        out.append('''\
  <template id="%(key)s" name="%(name)s">%(children)s</template>

  <record id="%(page_id)s" model="website.page">
    <field name="url">%(url)s</field>
    <field name="view_id" ref="%(key)s"/>
    <field name="website_id" ref="website.default_website"/>
    <field name="is_published" eval="True"/>
    <field name="website_meta_title">%(title)s</field>
    <field name="website_meta_description">%(desc)s</field>
  </record>

''' % {'key': key, 'name': esc(html.unescape(head['title']).split('|')[0].strip() or 'Home'),
       'url': url, 'children': children,
       'title': esc(html.unescape(head['title'])),
       'desc': esc(html.unescape(head['description'])),
       'page_id': 'website.homepage_page' if url == '/' else key + '_page'})
    out.append(TAIL)
    return ''.join(out)


def main():
    files = [
        write('__manifest__.py', MANIFEST),
        write('__init__.py', INIT),
        write('views/assets.xml', assets_xml()),
        write('data/menus.json', menus_json()),
        write('views/layout.xml', layout_xml()),
        write('views/pages.xml', pages_xml()),
    ]
    for f in files:
        print('wrote', f, os.path.getsize(os.path.join(MOD, f)), 'bytes')


if __name__ == '__main__':
    main()
