from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionDocumentType(models.Model):
    """A paper that a tender or a project file has to contain.

    The tender conditions list what must be handed in -- commercial register,
    tax card, classification certificate and so on -- split between a technical
    envelope and a financial one. Configuring them here is what lets the system
    block a submission while a required paper is still missing.
    """
    _name = 'construction.document.type'
    _description = 'Construction Document Type'
    _order = 'file_type, sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    file_type = fields.Selection(
        [('technical', 'Technical File'),
         ('financial', 'Financial File'),
         ('legal', 'Legal File'),
         ('contract', 'Contract'),
         ('boq', 'Bill of Quantities'),
         ('drawing', 'Drawings'),
         ('other', 'Other')],
        string='File', required=True, default='technical')
    scope = fields.Selection(
        [('tender', 'Tender'), ('project', 'Project'), ('both', 'Both')],
        string='Used For', required=True, default='tender')
    is_default_required = fields.Boolean(
        string='Required by Default', default=True,
        help='Loaded as a required line when the standard checklist is pulled '
             'onto a tender or a project.')
    has_expiry = fields.Boolean(
        string='Expires',
        help='Papers such as the tax card or the classification certificate '
             'carry an expiry date that has to be valid on submission day.')
    note = fields.Text(string='Notes')

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            duplicate = self.search_count([
                ('name', '=ilike', record.name), ('id', '!=', record.id),
            ])
            if duplicate:
                raise ValidationError(
                    self.env._('"%s" already exists.', record.name))
