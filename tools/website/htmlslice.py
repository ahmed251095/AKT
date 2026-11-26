"""Cut raw HTML out of the mirrored pages and make it parse as XML.

The slices are taken off the original text instead of being re-serialised by
an HTML parser, because every HTML parser lower-cases attribute names and the
site's inline icons carry `viewBox` - `viewbox` is a different attribute to
SVG and the icons collapse. So the markup is located by scanning tags and
counting depth, and the text between the boundaries is handed over untouched
apart from the three things QWeb's XML parser will not accept: unclosed void
elements, named entities, and attributes written without a value.
"""
import html.entities as _he
import re

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link',
        'meta', 'param', 'source', 'track', 'wbr'}

TAG = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9:-]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*?)(/?)>')

# One attribute inside a tag: a name, and optionally = and a value that may be
# quoted either way or bare.
ATTR = re.compile(r'''\s+([^\s=/>"']+)(\s*=\s*("[^"]*"|'[^']*'|[^\s/>]*))?''')


def slice_element(src, start_pat):
    """Return the raw text of the first element whose opening tag matches."""
    m = start_pat.search(src)
    if not m:
        return None
    name = TAG.match(src, m.start()).group(2).lower()
    depth = 0
    pos = m.start()
    while True:
        t = TAG.search(src, pos)
        if not t:
            raise ValueError('unterminated <%s>' % name)
        if t.group(2).lower() == name:
            if t.group(1) == '/':
                depth -= 1
                if depth == 0:
                    return src[m.start():t.end()]
            elif not t.group(4) and name not in VOID:
                depth += 1
        pos = t.end()


def inner(raw):
    """Strip the outermost tag off a raw element."""
    return raw[TAG.match(raw).end():raw.rfind('</')]


_ENT = re.compile(r'&([a-zA-Z][a-zA-Z0-9]*);')
_BARE_AMP = re.compile(r'&(?!#?\w+;)')


def _entities(text):
    """XML predefines five entities; every other name becomes its code point."""
    def one(m):
        n = m.group(1)
        if n in ('amp', 'lt', 'gt', 'quot', 'apos'):
            return m.group(0)
        cp = _he.html5.get(n + ';') or _he.html5.get(n)
        if cp is None:
            return '&amp;' + n + ';'
        return ''.join('&#%d;' % ord(c) for c in cp)
    return _BARE_AMP.sub('&amp;', _ENT.sub(one, text))


def _attrs(body):
    """Rewrite a tag's attribute text so every attribute carries a quoted value.

    HTML allows `muted` and `data-partner-slider` to stand alone and allows an
    unquoted value; XML allows neither. A valueless attribute is given its own
    name as the value, which is what a browser reads back for a boolean.
    """
    out = []
    pos = 0
    while True:
        m = ATTR.match(body, pos)
        if not m:
            break
        name, value = m.group(1), m.group(3)
        if value is None:
            value = name
        elif value[:1] in '"\'':
            value = value[1:-1]
        # Attribute values carry bare "&" too - map query strings do.
        out.append(' %s="%s"' % (name, _entities(value).replace('"', '&quot;')))
        pos = m.end()
    return ''.join(out)


def xmlify(raw):
    """Make a raw HTML slice parse as XML."""
    pieces = []
    pos = 0
    for t in TAG.finditer(raw):
        pieces.append(_entities(raw[pos:t.start()]))
        name = t.group(2)
        if t.group(1):
            pieces.append('</%s>' % name)
        else:
            closed = bool(t.group(4)) or name.lower() in VOID
            pieces.append('<%s%s%s>' % (name, _attrs(t.group(3)),
                                        '/' if closed else ''))
        pos = t.end()
    pieces.append(_entities(raw[pos:]))
    return ''.join(pieces)
