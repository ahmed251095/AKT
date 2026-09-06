from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ConstructionAuthorityType(models.Model):
    """Kind of body putting the work out to tender.

    Endowments, agricultural companies, ministries and private owners each come
    with their own paperwork and payment habits, and the estimation office
    prices them differently, so the tender has to say which one it is.
    """
    _name = 'construction.authority.type'
    _description = 'Tendering Authority Type'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    is_government = fields.Boolean(
        string='Government Body',
        help='Government bodies usually require a bid bond and a classification '
             'certificate.')
    default_bid_bond_percent = fields.Float(
        string='Default Bid Bond (%)',
        help='Bid bond this authority normally asks for.')
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
