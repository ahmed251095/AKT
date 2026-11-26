import logging

from odoo import models, SUPERUSER_ID
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    """Open the site in Arabic unless the visitor asked for something else.

    Odoo decides the language of a URL that carries no prefix by negotiating
    the browser's Accept-Language header, so a visitor whose browser is set
    to English is redirected from / to /en and never sees the Arabic site.
    The site this one replaces never did that: / always went to Arabic, and
    English was something the visitor chose.

    Only the browser's header is overruled. A language named in the URL and
    a language the visitor picked - which arrives in the frontend_lang
    cookie the switch in the header sets - are both resolved ahead of the
    header, and neither is touched here.
    """
    _inherit = 'ir.http'

    @classmethod
    def _match(cls, path):
        cls._akt_default_lang(path)
        return super()._match(path)

    @classmethod
    def _akt_default_lang(cls, path):
        if not request or hasattr(request, 'is_frontend'):
            return
        if request.cookies.get('frontend_lang'):
            return
        try:
            # No user is bound to the request this early, so the website is
            # read as the superuser. res.lang._get_frontend() is avoided on
            # purpose: it is cached, and priming that cache from here would
            # store a value computed without a visitor.
            env = request.env(user=SUPERUSER_ID)
            website = env['website'].get_current_website()
            if not website or not website.default_lang_id:
                return
            prefix = path.split('/')[1] if path.count('/') >= 1 else ''
            if prefix in website.language_ids.mapped('url_code'):
                return
            code = website.default_lang_id.code
            if request.env.context.get('lang') != code:
                request.update_context(lang=code)
        except Exception:  # noqa: BLE001 - routing must survive this
            _logger.warning('AKT website: could not open the site in the '
                            'default language', exc_info=True)
