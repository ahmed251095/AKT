from odoo import api, fields, models

GOVERNORATES = 'akt.governorates'


class CrmLead(models.Model):
    """The site's four forms all open a lead.

    A lead already holds a name, a contact and a description, but the forms
    ask for more than that - the area of the project, the budget, the window
    the visitor wants to be called in - and dropping those on the floor would
    mean the lead no longer says what was actually requested. So each answer
    that has nowhere standard to go gets a field here, and the form view shows
    them grouped by the form they came from.
    """
    _inherit = 'crm.lead'

    akt_request_type = fields.Selection(
        [('quotation', 'Quotation request'),
         ('contact', 'Contact message'),
         ('appointment', 'Visit or call request'),
         ('partner', 'Supplier registration')],
        string='Website form', index=True, readonly=True,
        help='Which form on the public site opened this lead.')

    # Quotation
    akt_service = fields.Char(string='Service requested', readonly=True)
    akt_sector = fields.Char(string='Sector', readonly=True)
    akt_project_type = fields.Char(string='Project type', readonly=True)
    akt_project_location = fields.Char(string='Project location', readonly=True)
    akt_governorate = fields.Char(string='Governorate', readonly=True)
    akt_area = fields.Float(string='Approximate area (m²)', readonly=True)
    akt_budget_amount = fields.Float(string='Budget', readonly=True)
    akt_budget_currency = fields.Char(string='Budget currency', readonly=True)
    akt_desired_start = fields.Date(string='Desired start', readonly=True)
    akt_preferred_contact = fields.Selection(
        [('email', 'Email'), ('phone', 'Phone call'), ('whatsapp', 'WhatsApp')],
        string='Preferred contact', readonly=True)

    # Appointment
    akt_visit_type = fields.Selection(
        [('call', 'Engineering call'), ('visit', 'Site visit')],
        string='Asked for', readonly=True)
    akt_preferred_date = fields.Date(string='Preferred date', readonly=True)
    akt_preferred_window = fields.Char(string='Preferred window', readonly=True)
    akt_alternative_date = fields.Date(string='Alternative date', readonly=True)
    akt_alternative_window = fields.Char(string='Alternative window', readonly=True)

    # Supplier / subcontractor
    akt_partner_type = fields.Selection(
        [('supplier', 'Supplier'), ('subcontractor', 'Subcontractor'),
         ('both', 'Supplier and subcontractor')],
        string='Registering as', readonly=True)
    akt_specialty = fields.Char(string='Specialty', readonly=True)
    akt_work_areas = fields.Char(string='Areas of work', readonly=True)
    akt_qualification_requested = fields.Boolean(
        string='Asks to be pre-qualified', readonly=True)

    akt_consent = fields.Boolean(string='Consented to be contacted', readonly=True)

    @api.model
    def akt_governorate_label(self, value):
        return value or ''
