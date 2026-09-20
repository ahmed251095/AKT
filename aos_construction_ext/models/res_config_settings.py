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
    group_construction_quality = fields.Boolean(
        string='Quality Control',
        implied_group='aos_construction_ext.group_construction_quality')
    construction_site_warehouse_id = fields.Many2one(
        related='company_id.construction_site_warehouse_id', readonly=False)
    construction_custody_account_id = fields.Many2one(
        related='company_id.construction_custody_account_id', readonly=False)
    construction_custody_journal_id = fields.Many2one(
        related='company_id.construction_custody_journal_id', readonly=False)
    construction_custody_settlement_journal_id = fields.Many2one(
        related='company_id.construction_custody_settlement_journal_id',
        readonly=False)
    construction_custody_expense_account_id = fields.Many2one(
        related='company_id.construction_custody_expense_account_id',
        readonly=False)
    construction_reminder_days = fields.Integer(
        related='company_id.construction_reminder_days', readonly=False)
    construction_bid_bond_percent = fields.Float(
        related='company_id.construction_bid_bond_percent', readonly=False)
    construction_performance_bond_percent = fields.Float(
        related='company_id.construction_performance_bond_percent', readonly=False)
