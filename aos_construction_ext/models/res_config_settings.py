from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    construction_profit_percent = fields.Float(
        related='company_id.construction_profit_percent', readonly=False)
    construction_contingency_percent = fields.Float(
        related='company_id.construction_contingency_percent', readonly=False)
    construction_admin_percent = fields.Float(
        related='company_id.construction_admin_percent', readonly=False)
    construction_expense_percent = fields.Float(
        related='company_id.construction_expense_percent', readonly=False)
    construction_reminder_days = fields.Integer(
        related='company_id.construction_reminder_days', readonly=False)
    construction_bid_bond_percent = fields.Float(
        related='company_id.construction_bid_bond_percent', readonly=False)
    construction_performance_bond_percent = fields.Float(
        related='company_id.construction_performance_bond_percent', readonly=False)
