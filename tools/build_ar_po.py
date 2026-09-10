# -*- coding: utf-8 -*-
"""Build an Arabic .po for both construction modules.

The references are derived from the module sources the same way Odoo names
them, so the importer can find each record:

  fields      module.field_<model_underscored>__<field>
  selections  module.selection__<model_underscored>__<field>__<value>
  models      module.model_<model_underscored>
  views/menus/actions   module.<xml id>
"""
import re, glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ar_terms import AR

BASE = '/home/ahmed-salah/Desktop/cluade/AKT'
MODULES = ['aos_construction_management', 'aos_construction_ext']


def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')


def auto_label(name):
    stem = name[:-4] if name.endswith('_ids') else \
        name[:-3] if name.endswith('_id') else name
    return stem.replace('_', ' ').title()


def model_key(model):
    return model.replace('.', '_')


def iter_fields(body):
    """Yield (field_name, full_call_args) walking balanced parentheses."""
    for m in re.finditer(r'^    (\w+)\s*=\s*fields\.(\w+)\(', body, re.M):
        fname, ftype = m.group(1), m.group(2)
        i = m.end() - 1
        depth, j, in_str, quote = 0, i, False, ''
        while j < len(body):
            ch = body[j]
            if in_str:
                if ch == '\\':
                    j += 2
                    continue
                if ch == quote:
                    in_str = False
            elif ch in "'\"":
                in_str, quote = True, ch
            elif ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    break
            j += 1
        yield fname, ftype, body[i + 1:j]


# A field's xmlid belongs to the module that first declared it. Redefining
# one in an extension does not move it, so keying the translation on the
# extension leaves the entry unresolvable and the old wording in place.
FIELD_ORIGIN = {}


def index_field_origins():
    for module in MODULES:
        for path in sorted(glob.glob(f'{BASE}/{module}/models/*.py') +
                           glob.glob(f'{BASE}/{module}/wizard/*.py')):
            text = open(path).read()
            for body in re.split(r'\nclass\s+\w+\([^)]*\):', text)[1:]:
                name = re.search(r"_name\s*=\s*'([\w.]+)'", body)
                inherit = (re.search(r"_inherit\s*=\s*'([\w.]+)'", body)
                           or re.search(r"_inherit\s*=\s*\[\s*'([\w.]+)'", body))
                model = (name.group(1) if name
                         else (inherit.group(1) if inherit else None))
                if not model:
                    continue
                for fname, _ftype, _args in iter_fields(body):
                    FIELD_ORIGIN.setdefault((model, fname), module)


def owner_of(model, fname, module):
    return FIELD_ORIGIN.get((model, fname), module)


def parse_python(module):
    """Yield (occurrence, source) for every field, selection and model name."""
    for path in sorted(glob.glob(f'{BASE}/{module}/models/*.py') +
                       glob.glob(f'{BASE}/{module}/wizard/*.py')):
        text = open(path).read()
        classes = re.split(r'\nclass\s+\w+\([^)]*\):', text)[1:]
        for body in classes:
            name = re.search(r"_name\s*=\s*'([\w.]+)'", body)
            inherit = (re.search(r"_inherit\s*=\s*'([\w.]+)'", body)
                       or re.search(r"_inherit\s*=\s*\[\s*'([\w.]+)'", body))
            model = name.group(1) if name else (inherit.group(1) if inherit else None)
            if not model:
                continue
            mk = model_key(model)

            desc = re.search(r"_description\s*=\s*'([^']+)'", body)
            if desc and name:
                yield (f'model:ir.model,name:{module}.model_{mk}', desc.group(1))

            relational = ftype_is_relational = None
            for fname, ftype, args in iter_fields(body):
                relational = ftype in ('Many2one', 'One2many', 'Many2many')
                label = re.search(r"string=(['\"])(.*?)\1", args, re.S)
                if not label and not relational:
                    # Non-relational fields may carry the label positionally;
                    # on relational ones the first argument is the comodel.
                    label = re.match(r"\s*(['\"])([^'\"]+)\1", args)
                if label:
                    text_ = label.group(2)
                elif 'related=' in args:
                    # Related fields inherit their label from the source field.
                    continue
                else:
                    text_ = auto_label(fname)
                owner = owner_of(model, fname, module)
                yield (f'model:ir.model.fields,field_description:'
                       f'{owner}.field_{mk}__{fname}', text_)
                # The tooltip behind every "?" on a form. Reading only the
                # label left all of them in English.
                tip = re.search(
                    rf"help=\s*\(?\s*((?:{STRING_RE}\s*)+)", args, re.S)
                if tip:
                    joined = ''.join(
                        unescape(m.group(0)[1:-1])
                        for m in re.finditer(STRING_RE, tip.group(1)))
                    joined = ' '.join(joined.split())
                    if joined:
                        yield (f'model:ir.model.fields,help:'
                               f'{owner}.field_{mk}__{fname}', joined)
                for sm in re.finditer(r"\(\s*'([\w.+-]+)'\s*,\s*'([^']+)'\s*\)", args):
                    if sm.group(2) in AR:
                        yield (f'model:ir.model.fields.selection,name:'
                               f'{owner}.selection__{mk}__{fname}__{sm.group(1)}',
                               sm.group(2))


STRING_RE = r"""(?:'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")"""
ESCAPES = {'\\n': '\n', '\\t': '\t', '\\r': '\r',
           '\\"': '"', "\\'": "'", '\\\\': '\\'}


def unescape(text):
    """Turn the escapes written in the source into the characters Python sees."""
    out, i = [], 0
    while i < len(text):
        pair = text[i:i + 2]
        if pair in ESCAPES:
            out.append(ESCAPES[pair])
            i += 2
        else:
            out.append(text[i])
            i += 1
    return ''.join(out)


def parse_code(module):
    """Messages raised from Python are referenced by their source path.

    The literals are matched per quote style, so a quote inside a message --
    'the rate for "%(item)s" is too high' -- does not cut the match short.
    """
    for path in sorted(glob.glob(f'{BASE}/{module}/models/*.py') +
                       glob.glob(f'{BASE}/{module}/wizard/*.py') +
                       glob.glob(f'{BASE}/{module}/controllers/*.py')):
        rel = os.path.relpath(path, BASE)
        text = open(path).read()
        for m in re.finditer(r"(?:self\.env\._|\b_)\(\s*((?:" + STRING_RE + r"\s*)+)",
                             text):
            parts = re.findall(STRING_RE, m.group(1))
            src = ''.join(unescape(part[1:-1]) for part in parts)
            if src:
                yield (f'code:addons/{rel}:0', src)


#: Seeded configuration whose names people read on screen.
DATA_MODELS = {
    'construction.document.type': 'name',
    'construction.authority.type': 'name',
    'construction.labour.type': 'name',
}


def parse_data(module):
    """Yield the translatable names of records the module seeds."""
    for path in sorted(glob.glob(f'{BASE}/{module}/data/*.xml')):
        text = open(path).read()
        for rec in re.finditer(
                r'<record\s+id="([\w.]+)"\s+model="([\w.]+)"(.*?)</record>',
                text, re.S):
            xmlid, model, body = rec.group(1), rec.group(2), rec.group(3)
            field = DATA_MODELS.get(model)
            if not field:
                continue
            value = re.search(rf'<field name="{field}">([^<]+)</field>', body)
            if value:
                yield (f'model:{model},{field}:{module}.{xmlid}',
                       value.group(1).strip())


def is_human_text(src):
    """Wording a person reads, as opposed to a field path or an expression."""
    if not re.search(r'[A-Za-z]{3}', src):
        return False
    if re.fullmatch(r'[\w.]+', src) and '.' in src:   # model.field paths
        return False
    if any(ch in src for ch in '$#'):
        return False
    if re.match(r'https?://', src):        # placeholder URLs
        return False
    return True


# Block tags: their text stands alone as a message.
BLOCK_TAGS = 'div|h1|h2|h3|h4|h5|p|th|td|caption|label|li'
# Inline tags: Odoo folds these into the message of the block around them, so
# the message key carries the markup. A translation has to carry it too.
INLINE_TAGS = 'span|strong|b|i|em|small|u'

TEXT_NODE_PATTERN = (
    rf'<({BLOCK_TAGS}|{INLINE_TAGS})(\b[^>]*)>'
    r'([^<>{}]*[A-Za-z]{3}[^<>{}]*)'
    rf'</(?:{BLOCK_TAGS}|{INLINE_TAGS})>'
)

# Wording that shares its element with a QWeb field -- "Subtotal (" before an
# amount, "days" after a duration. Matching whole elements only skipped these.
LOOSE_TEXT_PATTERN = (
    r'>([^<>{}]*[A-Za-z]{3}[^<>{}]*)<'
)
# The (?<!/) keeps a self-closing tag out: text after <span t-out=".."/> is
# the parent's wording, not the span's.
INLINE_WRAPPED = re.compile(
    rf'<({INLINE_TAGS})\b[^>]*(?<!/)>[^<>{{}}]*$')
# <attribute name="class">btn-secondary</attribute> is an inheritance
# directive, not wording. Only name="string" carries a label, and that has
# its own pattern.
DIRECTIVE = re.compile(r'<attribute\b[^>]*>[^<>{}]*$')

# Message keys the parsers build by wrapping a glossary term in its markup.
DERIVED = {}


def arabic_for(src):
    return AR.get(src) or DERIVED.get(src)


def loose_key(arch, match):
    """A bare text run's key, unless an inline tag already claims it."""
    before = arch[:match.start(1)]
    if DIRECTIVE.search(before):
        return None
    if INLINE_WRAPPED.search(before):
        return None          # message_key() emits this one with its markup
    text = ' '.join(match.group(1).replace('&amp;', '&').split())
    if not text or not is_human_text(text):
        return None
    return text if AR.get(text) else ('MISSING', text)


def message_key(tag, attrs, text):
    """The key Odoo will look this text up by, and its Arabic.

    Returns None when the text has no Arabic term yet, so the caller can
    report it rather than drop it.
    """
    text = ' '.join(text.replace('&amp;', '&').split())
    if not text or not is_human_text(text):
        return None
    arabic = AR.get(text)
    if not re.fullmatch(INLINE_TAGS, tag):
        return text if arabic else ('MISSING', text)
    if not arabic:
        return ('MISSING', text)
    key = f'<{tag}{attrs}>{text}</{tag}>'
    DERIVED[key] = f'<{tag}{attrs}>{arabic}</{tag}>'
    return key


def parse_reports(module):
    """QWeb report templates carry their own visible wording."""
    for path in sorted(glob.glob(f'{BASE}/{module}/report/*.xml') +
                       glob.glob(f'{BASE}/{module}/reports/*.xml')):
        text = open(path).read()
        for tpl in re.finditer(r'<template\s+id="([\w.]+)"(.*?)</template>',
                               text, re.S):
            xmlid, body = tpl.group(1), tpl.group(2)
            seen = set()
            for pattern in (r'\b(?:string|placeholder|title)="([^"]+)"',
                            TEXT_NODE_PATTERN, LOOSE_TEXT_PATTERN):
                for sm in re.finditer(pattern, body, re.S):
                    if pattern is TEXT_NODE_PATTERN:
                        src = message_key(sm.group(1), sm.group(2),
                                          sm.group(3))
                    elif pattern is LOOSE_TEXT_PATTERN:
                        src = loose_key(body, sm)
                    else:
                        src = ' '.join(
                            sm.group(1).replace('&amp;', '&').split())
                    if not src or src in seen:
                        continue
                    seen.add(src)
                    yield (f'model_terms:ir.ui.view,arch_db:{module}.{xmlid}',
                           src)


def parse_xml(module):
    for path in sorted(glob.glob(f'{BASE}/{module}/views/*.xml') +
                       glob.glob(f'{BASE}/{module}/wizard/*.xml')):
        text = open(path).read()
        for rec in re.finditer(
                r'<record\s+id="([\w.]+)"\s+model="(ir\.ui\.view|ir\.actions\.act_window)"(.*?)</record>',
                text, re.S):
            xmlid, model, body = rec.group(1), rec.group(2), rec.group(3)
            if model == 'ir.actions.act_window':
                nm = re.search(r'<field name="name">([^<]+)</field>', body)
                if nm:
                    yield (f'model:ir.actions.act_window,name:{module}.{xmlid}',
                           nm.group(1).replace('&amp;', '&'))
                continue
            arch = re.search(r'<field name="arch" type="xml">(.*?)</field>\s*</record>',
                             body + '</record>', re.S)
            if not arch:
                continue
            seen = set()
            patterns = (
                r'\b(?:string|placeholder|title)="([^"]+)"',
                # An inherited view sets a label through an attribute tag.
                r'<attribute name="(?:string|placeholder|title)">([^<]+)</attribute>',
                # Text a person actually reads on screen: smart-button labels,
                # empty-state copy, the wording inside an alert. Reading only
                # attributes left all of it in English.
                TEXT_NODE_PATTERN,
                LOOSE_TEXT_PATTERN,
            )
            for pattern in patterns:
                for sm in re.finditer(pattern, arch.group(1), re.S):
                    if pattern is TEXT_NODE_PATTERN:
                        src = message_key(sm.group(1), sm.group(2),
                                          sm.group(3))
                    elif pattern is LOOSE_TEXT_PATTERN:
                        src = loose_key(arch.group(1), sm)
                    else:
                        src = ' '.join(
                            sm.group(1).replace('&amp;', '&').split())
                    if not src or src in seen:
                        continue
                    seen.add(src)
                    yield (f'model_terms:ir.ui.view,arch_db:{module}.{xmlid}',
                           src)
        for mm in re.finditer(r'<menuitem[^>]*\bid="([\w.]+)"[^>]*?\bname="([^"]+)"', text, re.S):
            yield (f'model:ir.ui.menu,name:{module}.{mm.group(1)}', mm.group(2))
        for mm in re.finditer(r'<menuitem[^>]*\bname="([^"]+)"[^>]*?\bid="([\w.]+)"', text, re.S):
            yield (f'model:ir.ui.menu,name:{module}.{mm.group(2)}', mm.group(1))


def build():
    entries = {}   # source -> {module -> set(occurrences)}
    missing = set()
    for module in MODULES:
        for occ, src in (list(parse_python(module)) + list(parse_xml(module))
                         + list(parse_code(module)) + list(parse_data(module))
                         + list(parse_reports(module))):
            if isinstance(src, tuple):
                missing.add(src[1])
                continue
            if re.match(r'https?://', src):
                continue          # placeholder URLs are not wording
            if arabic_for(src) is None:
                # Silently dropping these is how English kept leaking into an
                # otherwise Arabic screen.
                missing.add(src)
                continue
            entries.setdefault(src, {}).setdefault(module, set()).add(occ)
    return entries, missing


HEADER = '''# Translation of Odoo Server.
# This file contains the translation of the following modules:
# \t* aos_construction_management
# \t* aos_construction_ext
#
msgid ""
msgstr ""
"Project-Id-Version: Odoo Server 19.0\\n"
"Report-Msgid-Bugs-To: \\n"
"Last-Translator: \\n"
"Language-Team: \\n"
"Language: ar_001\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=6; plural=n==0 ? 0 : n==1 ? 1 : n==2 ? 2 : n%100>=3 '''\
'''&& n%100<=10 ? 3 : n%100>=11 ? 4 : 5;\\n"
'''


def render(entries):
    out = [HEADER]
    for src in sorted(entries):
        for module in sorted(entries[src]):
            out.append('')
            out.append(f'#. module: {module}')
            occurrences = sorted(entries[src][module])
            if any(o.startswith('code:') for o in occurrences):
                out.append('#. odoo-python')
            for occ in occurrences:
                out.append(f'#: {occ}')
            out.append(f'msgid "{esc(src)}"')
            out.append(f'msgstr "{esc(arabic_for(src))}"')
    return '\n'.join(out) + '\n'


def render_module(entries, module):
    """Odoo ships each module's terms in its own i18n file."""
    out = [HEADER.replace(
        '# \t* aos_construction_management\n# \t* aos_construction_ext',
        f'# \t* {module}')]
    for src in sorted(entries):
        if module not in entries[src]:
            continue
        out.append('')
        out.append(f'#. module: {module}')
        occurrences = sorted(entries[src][module])
        if any(o.startswith('code:') for o in occurrences):
            out.append('#. odoo-python')
        for occ in occurrences:
            out.append(f'#: {occ}')
        out.append(f'msgid "{esc(src)}"')
        out.append(f'msgstr "{esc(arabic_for(src))}"')
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    index_field_origins()
    e, missing = build()
    if missing:
        print(f'MISSING {len(missing)} term(s) from ar_terms.py:',
              file=sys.stderr)
        for term in sorted(missing)[:12]:
            print(f'  {term[:100]!r}', file=sys.stderr)
        if len(missing) > 12:
            print(f'  ... and {len(missing) - 12} more', file=sys.stderr)
    for module in MODULES:
        path = f'{BASE}/{module}/i18n/ar_001.po'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        body = render_module(e, module)
        open(path, 'w').write(body)
        print(f'{module}: {body.count(chr(10) + "msgid ")} entries -> {path}',
              file=sys.stderr)
