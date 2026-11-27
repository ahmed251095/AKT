import base64
import json
import logging
import os

from odoo import api, models

_logger = logging.getLogger(__name__)

ARABIC = 'ar_001'
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AktWebsiteSetup(models.AbstractModel):
    """The setting-up the module cannot express as data records.

    Split in two on purpose.

    `apply` runs on every install *and* every upgrade, through the
    <function> tag in data/sync.xml. A post_init_hook would not do: Odoo
    only calls it on install, so the Arabic wording of a page that changed
    would never reach a database that already had the module - which is
    exactly what happened when the site moved to its new theme and the
    header's "Start a project" stayed in English on the live site while
    reading correctly on a fresh database.

    `first_install` runs once, from the hook. What it sets up - the nav bar
    and the favicon - is the client's to change afterwards from Odoo, and
    redoing it on every upgrade would throw their edits away.
    """
    _name = 'akt.website.setup'
    _description = 'AKT website setup'

    # ------------------------------------------------------------ always
    @api.model
    def apply(self):
        arabic = self._languages()
        website = self.env['website'].search([], limit=1)
        if not website:
            _logger.warning('AKT website: no website record to configure')
            return

        vals = {'name': 'AKT Group'}
        if arabic:
            english = self.env['res.lang'].search([('code', '=', 'en_US')], limit=1)
            vals['language_ids'] = [(6, 0, (arabic | english).ids)]
            vals['default_lang_id'] = arabic.id
        website.write(vals)

        self._translations(arabic)
        self._visitor_language(website, arabic)
        self._homepage()

    # ------------------------------------------------------- once, on install
    @api.model
    def first_install(self):
        website = self.env['website'].search([], limit=1)
        if not website:
            return
        self._menus(website)
        self._favicon(website)

    # ---------------------------------------------------------------- parts
    def _languages(self):
        """Arabic active and prefixed /ar, English prefixed /en."""
        lang = self.env['res.lang'].with_context(active_test=False).search(
            [('code', '=', ARABIC)], limit=1)
        if not lang:
            _logger.warning('AKT website: %s is not available; the site stays '
                            'in English only', ARABIC)
            return self.env['res.lang']
        if not lang.active:
            self.env['res.lang']._activate_lang(ARABIC)
            lang = self.env['res.lang'].search([('code', '=', ARABIC)], limit=1)
        lang.url_code = 'ar'
        english = self.env['res.lang'].search([('code', '=', 'en_US')], limit=1)
        if english:
            english.url_code = 'en'
        return lang

    def _translations(self, arabic):
        """Apply the Arabic wording, view by view.

        The wording cannot be shipped in a .po file, which keys a
        translation on the English text alone: the site needs the same
        English to read differently in different places - "Send an enquiry"
        is أرسل طلبك on a service page and اطلب التواصل on a sector page.
        Odoo keeps a view's translation on the view, so the table is per
        view.

        Odoo's own storage is keyed on the source term within a view, so a
        term repeated in one view cannot carry two translations. One page is
        affected - the placeholder badges on the credentials page, which
        agree with a different noun each time - and the generator reports it
        rather than letting it pass unnoticed.
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
            view = self.env.ref(key, raise_if_not_found=False)
            if not view:
                _logger.warning('AKT website: no view %s to translate', key)
                continue
            for field, value in fields.items():
                view.update_field_translations(field, {arabic.code: value})
            done += 1
        _logger.info('AKT website: Arabic wording applied to %d views', done)

    def _visitor_language(self, website, arabic):
        """Make a first-time visitor land on the Arabic site.

        Odoo reads the language of a request with no prefix off the
        environment, which for an unauthenticated visitor means the public
        user - not the website's default language.
        """
        if not arabic:
            return
        public = website.user_id or self.env.ref('base.public_user',
                                                 raise_if_not_found=False)
        if public:
            public.sudo().lang = arabic.code

    def _homepage(self):
        """Every page sitting at "/" renders the AKT home page.

        Odoo makes a home page of its own per website at its install, and
        that record shadows anything a module declares at "/".
        """
        view = self.env.ref('akt_website.homepage', raise_if_not_found=False)
        if not view:
            return
        for page in self.env['website.page'].search([('url', '=', '/')]):
            page.view_id = view.id
            page.is_published = True

    def _menus(self, website):
        """Build the nav bar under the website's own root menu.

        That is the tree the builder edits, so a bar built anywhere else
        would ignore the client's changes - and for the same reason this
        runs on install only.
        """
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

        # Odoo's starter bar is Home and Contact us; the site has its own.
        root.child_id.unlink()
        for i, entry in enumerate(tree):
            parent = self._menu(entry, root, 10 * (i + 1), website)
            for j, child in enumerate(entry.get('children', [])):
                self._menu(child, parent, 10 * (j + 1), website)

    def _menu(self, entry, parent, sequence, website):
        menu = self.env['website.menu'].create({
            'name': entry['en'],
            'url': entry['url'],
            'parent_id': parent.id,
            'sequence': sequence,
            'website_id': website.id,
        })
        if entry.get('ar'):
            menu.with_context(lang=ARABIC).name = entry['ar']
        return menu

    def _favicon(self, website):
        path = os.path.join(HERE, 'static/src/img/favicon.ico')
        try:
            with open(path, 'rb') as fh:
                website.favicon = base64.b64encode(fh.read())
        except OSError:
            _logger.info('AKT website: no favicon at %s', path)
