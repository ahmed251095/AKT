import base64
import json
import logging
import os

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)

ARABIC = 'ar_001'
HERE = os.path.dirname(__file__)


def post_init(env):
    """Put the website into the shape the site is served in.

    Three things cannot be expressed as data records. The languages, because
    the prefix Odoo puts on a language has to be the one every link in the
    pages already uses. The home page, because Odoo makes one per website at
    its own install and that record shadows anything a module declares at
    "/". And the menu bar, because it has to hang off the root menu Odoo
    created for this website - that is the tree the builder edits, so a bar
    built anywhere else would ignore the client's changes.
    """
    if not hasattr(env, 'cr'):  # older signature: (cr, registry)
        env = api.Environment(env, SUPERUSER_ID, {})

    arabic = _languages(env)
    website = env['website'].search([], limit=1)
    if not website:
        _logger.warning('AKT website: no website record to configure')
        return

    vals = {'name': 'AKT Group'}
    if arabic:
        english = env['res.lang'].search([('code', '=', 'en_US')], limit=1)
        vals['language_ids'] = [(6, 0, (arabic | english).ids)]
        vals['default_lang_id'] = arabic.id
    website.write(vals)

    if arabic:
        # The module's own data loads before this hook runs, and the loader
        # only reads a .po for a language that was already active - so with
        # Arabic switched on a moment ago, its terms have to be asked for.
        env['ir.module.module'].search([('name', '=', 'akt_website')]) \
            ._update_translations([ARABIC])

    _translations(env, arabic)
    _visitor_language(env, website, arabic)
    _homepage(env, website)
    _menus(env, website)
    _favicon(env, website)


def _languages(env):
    """Arabic active and prefixed /ar, English prefixed /en."""
    lang = env['res.lang'].with_context(active_test=False).search(
        [('code', '=', ARABIC)], limit=1)
    if not lang:
        _logger.warning('AKT website: %s is not available; the site stays '
                        'in English only', ARABIC)
        return env['res.lang']
    if not lang.active:
        env['res.lang']._activate_lang(ARABIC)
        lang = env['res.lang'].search([('code', '=', ARABIC)], limit=1)
    lang.url_code = 'ar'
    english = env['res.lang'].search([('code', '=', 'en_US')], limit=1)
    if english:
        english.url_code = 'en'
    return lang


def _translations(env, arabic):
    """Apply the Arabic wording, view by view.

    The wording cannot be shipped in a .po file, which keys a translation on
    the English text alone: the site needs the same English to read
    differently in different places - "Send an enquiry" is أرسل طلبك on a
    service page and اطلب التواصل on a sector page. Odoo keeps a view's
    translation on the view, so the table is per view.

    Odoo's own storage is keyed on the source term within a view, so a term
    repeated in one view cannot carry two translations. One page is affected
    - the placeholder badges on the credentials page, which agree with a
    different noun each time - and the generator reports it rather than
    letting it pass unnoticed.
    """
    if not arabic:
        return
    path = os.path.join(HERE, 'i18n/ar_terms.json')
    try:
        with open(path, encoding='utf-8') as fh:
            table = json.load(fh)
    except OSError:
        _logger.warning('AKT website: no Arabic wording at %s', path)
        return

    done = 0
    for key, fields in sorted(table.items()):
        view = env.ref(key, raise_if_not_found=False)
        if not view:
            _logger.warning('AKT website: no view %s to translate', key)
            continue
        for field, value in fields.items():
            view.update_field_translations(field, {arabic.code: value})
        done += 1
    _logger.info('AKT website: Arabic wording applied to %d views', done)


def _visitor_language(env, website, arabic):
    """Make a first-time visitor land on the Arabic site.

    Odoo reads the language of a request with no prefix off the environment,
    which for an unauthenticated visitor means the public user - not the
    website's default language. Left in English, every visitor to "/" is
    redirected to /en and the Arabic site is never the one that opens.
    """
    if not arabic:
        return
    public = website.user_id or env.ref('base.public_user',
                                        raise_if_not_found=False)
    if public:
        public.sudo().lang = arabic.code


def _homepage(env, website):
    """Every page sitting at "/" renders the AKT home page, in both languages."""
    ours = env.ref('website.homepage_page', raise_if_not_found=False)
    view = env.ref('akt_website.homepage', raise_if_not_found=False)
    if not view:
        return
    pages = env['website.page'].search([('url', '=', '/')])
    for page in pages:
        page.view_id = view.id
        # No metadata to copy: website.page stores the title and the
        # description on the view it delegates to, and both pages at "/" now
        # point at the same one.
        page.is_published = True


def _menus(env, website):
    """Rebuild the nav bar under the website's own root menu."""
    path = os.path.join(HERE, 'data/menus.json')
    try:
        with open(path, encoding='utf-8') as fh:
            tree = json.load(fh)
    except OSError:
        _logger.warning('AKT website: no menu table at %s', path)
        return

    root = website.menu_id
    if not root:
        _logger.warning('AKT website: website %s has no root menu', website.id)
        return

    Menu = env['website.menu']
    # Odoo's starter bar is Home and Contact us; the site has its own.
    root.child_id.unlink()

    for i, entry in enumerate(tree):
        parent = _menu(Menu, entry, root, 10 * (i + 1), website)
        for j, child in enumerate(entry.get('children', [])):
            _menu(Menu, child, parent, 10 * (j + 1), website)


def _menu(Menu, entry, parent, sequence, website):
    menu = Menu.create({
        'name': entry['en'],
        'url': entry['url'],
        'parent_id': parent.id,
        'sequence': sequence,
        'website_id': website.id,
    })
    if entry.get('ar'):
        menu.with_context(lang=ARABIC).name = entry['ar']
    return menu


def _favicon(env, website):
    path = os.path.join(HERE, 'static/src/img/favicon.ico')
    try:
        with open(path, 'rb') as fh:
            website.favicon = base64.b64encode(fh.read())
    except OSError:
        _logger.info('AKT website: no favicon at %s', path)
