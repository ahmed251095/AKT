"""Read the navigation out of the mirrored header."""
import re

import common
import htmlslice

A = re.compile(r'<a href="([^"]+)"[^>]*>(.*?)</a>', re.S)


def tree(lang):
    """Top-level nav entries, each possibly with children.

    The header holds nine plain links and one <details> block; the block
    becomes a menu with children so the whole bar is editable from Odoo.
    """
    f = dict(common.pages(lang))['/']
    hdr = common.body(f, lang, common.HEADER)
    nav = htmlslice.slice_element(hdr, re.compile(r'<nav[^>]*id="primary-nav"'))
    more = htmlslice.slice_element(nav, re.compile(r'<details class="nav-more">'))
    flat = nav.replace(more, '')

    out = [{'url': u, 'name': _text(n), 'children': []} for u, n in A.findall(flat)]
    summary = re.search(r'<summary>(.*?)</summary>', more, re.S)
    out.append({
        'url': '#',
        'name': _text(summary.group(1)),
        'children': [{'url': u, 'name': _text(n), 'children': []}
                     for u, n in A.findall(more)],
    })
    return out


def _text(frag):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', frag)).strip()
