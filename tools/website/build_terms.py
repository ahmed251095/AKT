"""Write the Arabic wording of each view, in the order its terms appear.

A .po file keys a translation on the English text alone, so one English
string could only ever have one Arabic one across the whole site - and the
site needs otherwise: "Send an enquiry" is أرسل طلبك on a service page and
اطلب التواصل on a sector page, "Careers" is الوظائف in the nav bar and فرص
العمل in the footer. Odoo keeps a view's translation on the view, so the
table here is per view and goes through update_field_translations.

Odoo's storage is keyed on the source term within a view, so a term
repeated inside one view with two different translations cannot be
expressed; those are reported at the end rather than silently resolved in
favour of whichever was read first.

The term lists come out of the same functions that write the module's XML,
run once per language, so a term can only land here if it is really in the
view and spelled the way the view spells it. Odoo's own xml_translate
decides what counts as a term, and the two language versions of every page
were shown to have the same structure, so they line up.
"""
import html
import json
import os
import sys

sys.path.insert(0, '/home/ahmed-salah/Desktop/cluade/upgrade14to19/src')

import build_module
import common
from odoo.tools.translate import xml_translate


def terms(children):
    """Every translatable term of a template body, in document order.

    Odoo stores a template as its body inside a single element, so wrapping
    the body in one here gives the same list it will read back - the
    wrapping element contributes no term of its own.
    """
    found = []

    def grab(term):
        found.append(term)
        return term
    xml_translate(grab, '<t>%s</t>' % children)
    return found


# Wording the Odoo build adds, which has no counterpart on the site being
# copied and so cannot be paired out of the two mirrors.
EXTRA = {
    'akt_website.layout': {'Log in': 'تسجيل الدخول'},
}


def main():
    table = {}
    problems = []

    def pair(key, en_children, ar_children):
        en, ar = terms(en_children), terms(ar_children)
        if len(en) != len(ar):
            problems.append('%s: %d English terms vs %d Arabic'
                            % (key, len(en), len(ar)))
            return
        mapping = {}
        for e, a in zip(en, ar):
            e, a = e.strip(), a.strip()
            if not e or e == a:
                continue
            if e in mapping and mapping[e] != a:
                problems.append('%s: %r is both %r and %r; keeping the first'
                                % (key, e[:50], mapping[e][:30], a[:30]))
                continue
            mapping[e] = a
        if mapping:
            table.setdefault(key, {})['arch_db'] = mapping

    pair('akt_website.layout',
         build_module.layout_children('en'), build_module.layout_children('ar'))

    ar_pages = dict(common.pages('ar'))
    for url, path in common.pages('en'):
        key = 'akt_website.%s' % common.page_key(url)
        pair(key, build_module.page_children(url, 'en'),
             build_module.page_children(url, 'ar'))

        # The title and the description are plain fields, stored on the view
        # that website.page delegates to.
        en_head, ar_head = common.head_bits(path), common.head_bits(ar_pages[url])
        for field, name in (('title', 'website_meta_title'),
                            ('description', 'website_meta_description')):
            value = html.unescape(ar_head[field]).strip()
            if value and value != html.unescape(en_head[field]).strip():
                table.setdefault(key, {})[name] = value

    for key, terms_ in EXTRA.items():
        table.setdefault(key, {}).setdefault('arch_db', {}).update(terms_)

    path = os.path.join(common.MOD, 'i18n/ar_terms.json')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(table, fh, ensure_ascii=False, indent=1, sort_keys=True)

    total = sum(len(v.get('arch_db', {})) for v in table.values())
    print('wrote %s: %d views, %d terms' % (path, len(table), total))
    for p in problems:
        print('  PROBLEM', p)


if __name__ == '__main__':
    main()
