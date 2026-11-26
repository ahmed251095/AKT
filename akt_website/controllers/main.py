import base64
import logging
import re

from odoo import _, http
from odoo.http import request

_logger = logging.getLogger(__name__)

# Each form, as: the lead title, the tag to file it under, and the answers
# that belong to it. Keeping this as data means a new question on a form is
# one line here and one field on the model, not another handler.
FORMS = {
    'quotation': {
        'title': 'Quotation request',
        'tag': 'akt_website.tag_quotation',
        'required': ('name', 'email', 'project_location', 'message'),
        'char': ('service', 'sector', 'project_type', 'project_location',
                 'governorate', 'budget_currency'),
        'selection': ('preferred_contact',),
        'number': ('area', 'budget_amount'),
        'date': ('desired_start',),
        'rename': {'approximate_area': 'area'},
    },
    'contact': {
        'title': 'Contact message',
        'tag': 'akt_website.tag_contact',
        'required': ('name', 'email', 'subject', 'message'),
        'char': (),
        'selection': (),
        'number': (),
        'date': (),
        'rename': {},
    },
    'appointment': {
        'title': 'Visit or call request',
        'tag': 'akt_website.tag_appointment',
        'required': ('name', 'email', 'phone', 'preferred_date', 'message'),
        'char': ('project_location', 'preferred_window', 'alternative_window'),
        'selection': ('visit_type',),
        'number': (),
        'date': ('preferred_date', 'alternative_date'),
        'rename': {'request_type': 'visit_type'},
    },
    'partner': {
        'title': 'Supplier registration',
        'tag': 'akt_website.tag_partner',
        'required': ('company_name', 'specialty', 'work_areas', 'name',
                     'email', 'phone', 'message'),
        'char': ('specialty', 'work_areas'),
        'selection': ('partner_type',),
        'number': (),
        'date': (),
        'rename': {},
    },
}

# Where each form lives, so the visitor is sent back to the page they posted
# from rather than to a bare thank-you page.
PAGES = {
    'quotation': '/quotation',
    'contact': '/contact',
    'appointment': '/appointments',
    'partner': '/partners/register',
}

MAX_UPLOAD = 10 * 1024 * 1024
MAX_FILES = 10
EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')


class AktForms(http.Controller):

    @http.route('/akt/form/<string:kind>', type='http', auth='public',
                methods=['POST'], website=True)
    def submit(self, kind, **post):
        spec = FORMS.get(kind)
        if not spec:
            return request.not_found()

        back = request.httprequest.referrer or PAGES.get(kind, '/')
        back = back.split('?')[0]

        # The hidden "website" input is a honeypot: a person never fills it
        # in, so anything in it is thrown away silently rather than answered,
        # which is what tells a bot its post failed.
        if post.get('website'):
            return request.redirect('%s?akt_sent=1' % back)

        error = self._validate(spec, post)
        if error:
            return request.redirect('%s?akt_error=%s' % (back, error))

        lead = request.env['crm.lead'].sudo().create(self._lead_values(kind, spec, post))
        self._attach(lead, request.httprequest.files.getlist('documents'))
        lead._message_log(body=_('Submitted from the website.'))
        return request.redirect('%s?akt_sent=1' % back)

    # ------------------------------------------------------------------
    def _validate(self, spec, post):
        for field in spec['required']:
            if not (post.get(field) or '').strip():
                return _('Please fill in every required field.')
        if not EMAIL.match((post.get('email') or '').strip()):
            return _('Please check the email address.')
        if not post.get('consent'):
            return _('Please agree to be contacted about this request.')
        return None

    def _lead_values(self, kind, spec, post):
        name = (post.get('name') or '').strip()
        company = (post.get('company_name') or '').strip()
        subject = (post.get('subject') or '').strip()

        title = '%s: %s' % (spec['title'], subject or company or name)
        vals = {
            'name': title[:200],
            'contact_name': name,
            'partner_name': company or False,
            'email_from': (post.get('email') or '').strip(),
            'phone': (post.get('phone') or '').strip(),
            'description': (post.get('message') or '').strip(),
            'akt_request_type': kind,
            'akt_consent': True,
            'type': 'lead',
        }
        tag = request.env.ref(spec['tag'], raise_if_not_found=False)
        if tag:
            vals['tag_ids'] = [(4, tag.id)]

        rename = spec['rename']
        for group, cast in (('char', self._as_char), ('selection', self._as_char),
                            ('number', self._as_float), ('date', self._as_date)):
            for field in spec[group]:
                raw = post.get(next((k for k, v in rename.items() if v == field), field))
                value = cast(raw)
                if value not in (None, ''):
                    vals['akt_%s' % field] = value

        if kind == 'partner':
            vals['akt_qualification_requested'] = bool(post.get('qualification_requested'))
        return vals

    def _as_char(self, raw):
        return (raw or '').strip() or None

    def _as_float(self, raw):
        try:
            return float((raw or '').strip())
        except ValueError:
            return None

    def _as_date(self, raw):
        raw = (raw or '').strip()
        return raw or None

    def _attach(self, lead, files):
        """Store the uploads on the lead, within a size the mailbox survives."""
        total = 0
        for upload in files[:MAX_FILES]:
            data = upload.read()
            total += len(data)
            if not data or total > MAX_UPLOAD:
                _logger.info('AKT form: upload for lead %s dropped (%s bytes so far)',
                             lead.id, total)
                break
            request.env['ir.attachment'].sudo().create({
                'name': upload.filename or 'attachment',
                'datas': base64.b64encode(data),
                'res_model': 'crm.lead',
                'res_id': lead.id,
            })
