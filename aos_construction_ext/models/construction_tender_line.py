from odoo import api, fields, models
from odoo.exceptions import ValidationError

from . import pricing


class ConstructionTenderLine(models.Model):
    _inherit = 'construction.tender.line'

    pricing_method = fields.Selection(
        pricing.PRICING_METHODS, string='Pricing Method', required=True,
        default=lambda self: self.env.company.construction_pricing_method,
        help='Build-up on Cost marks the cost up by the ratios. Share of '
             'Selling Price treats every ratio as a slice of the rate and '
             'solves for it, which is how the estimation sheets are written. '
             'Typed by Hand leaves both rates alone.')

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
    authority_percent = fields.Float(
        string='Authority Share (%)', default=lambda self:
        self.env.company.construction_authority_percent,
        help='The share of the rate that goes to the tendering body. Priced '
             'under Share of Selling Price only; a build-up has no slice of '
             'the rate for it.')

    tax_ids = fields.Many2many(
        'account.tax', string='Taxes',
        help='Taxes priced into the rate, picked from the taxes defined on '
             'the system. Percentage taxes only; a fixed-amount tax cannot '
             'be built into a unit rate.')
    tax_percent = fields.Float(
        string='Tax (%)', compute='_compute_tax_percent', store=True,
        readonly=False,
        help='Follows the taxes picked above. Type a figure straight into it '
             'where the sheet carries a rate rather than a tax record.')
    price_before_tax = fields.Monetary(
        string='Price before Tax', compute='_compute_pricing', store=True)
    tax_amount = fields.Monetary(
        string='Tax Value', compute='_compute_pricing', store=True)

    @api.depends('tax_ids')
    def _compute_tax_percent(self):
        for line in self:
            line.tax_percent = sum(
                tax.amount for tax in line.tax_ids
                if tax.amount_type == 'percent')

    base_cost = fields.Monetary(
        string='Base Cost', compute='_compute_pricing', store=True,
        help='Dry cost plus operating cost, before any markup.')
    markup_percent = fields.Float(
        string='Total Markup (%)', compute='_compute_markup', store=True,
        readonly=False,
        help='Profit + contingency + administration. Type over it to price '
             'this item at a different markup.')
    markup_amount = fields.Monetary(
        string='Markup Value', compute='_compute_pricing', store=True)
    price_before_expenses = fields.Monetary(
        string='Price before Expenses', compute='_compute_pricing', store=True)
    expense_amount = fields.Monetary(
        string='Expenses Value', compute='_compute_pricing', store=True)
    authority_amount = fields.Monetary(
        string='Authority Share Value', compute='_compute_pricing',
        store=True, help='The authority share carried by one unit.')

    # ------------------------------------------------------------------
    # What of the rate is actually ours to keep
    # ------------------------------------------------------------------
    # The base margin is the whole gap between the bid and the item cost, so it
    # counts two things the company never keeps: the tax, which is deducted
    # from the certificate and paid on, and the head-office administration
    # share, which is recovered overhead rather than profit.
    admin_amount = fields.Monetary(
        string='Administration Value', compute='_compute_net_margin',
        store=True, help='The administration share carried by one unit.')
    admin_total = fields.Monetary(
        string='Administration Total', compute='_compute_net_margin',
        store=True)
    tax_total = fields.Monetary(
        string='Tax Total', compute='_compute_net_margin', store=True)
    authority_total = fields.Monetary(
        string='Authority Share Total', compute='_compute_net_margin',
        store=True)
    net_margin = fields.Monetary(
        string='Margin', compute='_compute_net_margin', store=True,
        help='The bid less the item cost, the administration share and the '
             'tax: what the item actually leaves behind.')
    net_margin_percent = fields.Float(
        string='Margin (%)', compute='_compute_net_margin', store=True)

    @api.depends('amount', 'budget_cost', 'base_cost', 'admin_percent',
                 'tax_amount', 'qty', 'is_section', 'pricing_method',
                 'unit_rate', 'authority_amount')
    def _compute_net_margin(self):
        for line in self:
            if line.is_section:
                line.admin_amount = line.admin_total = line.tax_total = 0.0
                line.authority_total = 0.0
                line.net_margin = line.net_margin_percent = 0.0
                continue
            # Under the sheet convention the administration ratio is a
            # slice of the rate, not a markup on the cost, so it is read off
            # whichever figure it was priced against.
            line.admin_amount = (
                line.unit_rate if line.pricing_method == 'margin'
                else line.base_cost) * line.admin_percent / 100.0
            line.admin_total = line.admin_amount * line.qty
            line.tax_total = line.tax_amount * line.qty
            line.authority_total = line.authority_amount * line.qty
            line.net_margin = (line.amount - line.budget_cost
                               - line.admin_total - line.tax_total
                               - line.authority_total)
            line.net_margin_percent = (
                100.0 * line.net_margin / line.amount) if line.amount else 0.0

    # Re-declared to become computed. The base module leaves both as plain
    # stored fields; keeping them writable lets an estimator override a single
    # line without switching the whole tender off the formula.
    cost_rate = fields.Monetary(
        compute='_compute_cost_rate', store=True, readonly=False)
    unit_rate = fields.Monetary(
        compute='_compute_unit_rate', store=True, readonly=False)

    @api.depends(*pricing.MARKUP_DEPENDS)
    def _compute_markup(self):
        pricing.compute_markup(self)

    @api.depends(*pricing.PRICING_DEPENDS)
    def _compute_pricing(self):
        pricing.compute_pricing(self)

    @api.depends(*pricing.COST_RATE_DEPENDS)
    def _compute_cost_rate(self):
        pricing.compute_cost_rate(self)

    @api.depends(*pricing.UNIT_RATE_DEPENDS)
    def _compute_unit_rate(self):
        pricing.compute_unit_rate(self)

    @api.constrains('pricing_method', *pricing.MARGIN_RATIOS)
    def _check_margin_shares(self):
        for line in self:
            if line.is_section or line.pricing_method != 'margin':
                continue
            if pricing.shares(line) >= 1.0:
                raise ValidationError(self.env._(
                    'The ratios on "%(item)s" add up to %(total)s%% of the '
                    'selling price, so there is nothing left to cover the '
                    'cost and no rate to solve for. They have to stay under '
                    '100%%.',
                    item=line.display_name,
                    total=round(pricing.shares(line) * 100.0, 2)))

    def action_apply_company_ratios(self):
        """Pull the company ratios back onto these items."""
        self.write(pricing.default_ratios(self.env.company))

    @api.depends('item_no', 'description')
    def _compute_display_name(self):
        """The base module gives these lines no name, so Odoo falls back to
        "construction.boq.line,3" wherever one is referenced."""
        for line in self:
            parts = [part for part in (line.item_no, line.description) if part]
            line.display_name = ' - '.join(parts) or self.env._('Item')
