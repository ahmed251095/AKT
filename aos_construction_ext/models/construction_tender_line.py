from odoo import api, fields, models

from . import pricing


class ConstructionTenderLine(models.Model):
    _inherit = 'construction.tender.line'

    use_pricing_formula = fields.Boolean(
        string='Build-up Pricing', default=True,
        help='Build the rate from cost and ratios. Uncheck to type the cost '
             'and selling rates by hand, for items quoted as a lump sum.')

    dry_cost = fields.Monetary(
        string='Dry Cost',
        help='Material cost of one unit, at the price the purchasing '
             'department can buy it today.')
    operating_cost = fields.Monetary(
        string='Operating Cost',
        help='Labour, equipment and execution cost of putting one unit in '
             'place.')

    profit_percent = fields.Float(
        string='Profit (%)', default=lambda self:
        self.env.company.construction_profit_percent)
    contingency_percent = fields.Float(
        string='Contingency (%)', default=lambda self:
        self.env.company.construction_contingency_percent)
    admin_percent = fields.Float(
        string='Administration (%)', default=lambda self:
        self.env.company.construction_admin_percent)
    expense_percent = fields.Float(
        string='General Expenses (%)', default=lambda self:
        self.env.company.construction_expense_percent)

    base_cost = fields.Monetary(
        string='Base Cost', compute='_compute_pricing', store=True,
        help='Dry cost plus operating cost, before any markup.')
    markup_percent = fields.Float(
        string='Total Markup (%)', compute='_compute_pricing', store=True,
        help='Profit + contingency + administration.')
    markup_amount = fields.Monetary(
        string='Markup Value', compute='_compute_pricing', store=True)
    price_before_expenses = fields.Monetary(
        string='Price before Expenses', compute='_compute_pricing', store=True)
    expense_amount = fields.Monetary(
        string='Expenses Value', compute='_compute_pricing', store=True)

    # Re-declared to become computed. The base module leaves both as plain
    # stored fields; keeping them writable lets an estimator override a single
    # line without switching the whole tender off the formula.
    cost_rate = fields.Monetary(
        compute='_compute_cost_rate', store=True, readonly=False)
    unit_rate = fields.Monetary(
        compute='_compute_unit_rate', store=True, readonly=False)

    @api.depends(*pricing.PRICING_DEPENDS)
    def _compute_pricing(self):
        pricing.compute_pricing(self)

    @api.depends('dry_cost', 'operating_cost', 'use_pricing_formula',
                 'is_section')
    def _compute_cost_rate(self):
        pricing.compute_cost_rate(self)

    @api.depends('price_before_expenses', 'expense_percent',
                 'use_pricing_formula', 'is_section')
    def _compute_unit_rate(self):
        pricing.compute_unit_rate(self)

    def action_apply_company_ratios(self):
        """Pull the company ratios back onto these items."""
        self.write(pricing.default_ratios(self.env.company))
