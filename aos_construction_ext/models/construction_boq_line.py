from odoo import api, fields, models

from . import pricing


class ConstructionBoqLine(models.Model):
    _inherit = 'construction.boq.line'

    tender_line_id = fields.Many2one(
        'construction.tender.line', string='Tender Item', copy=False,
        help='The priced tender item this BOQ item was created from.')

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

    # ------------------------------------------------------------------
    # Quantity control - what the site actually used against what was priced
    # ------------------------------------------------------------------
    qty_variance = fields.Float(
        string='Quantity Variance', compute='_compute_qty_variance',
        help='Executed quantity less the quantity in the bill of quantities. '
             'A positive figure is work done beyond what the client priced.')
    variance_cost = fields.Monetary(
        string='Variance Cost', compute='_compute_qty_variance',
        help='What the quantity variance costs us at the item cost rate.')
    is_overrun = fields.Boolean(
        string='Over-run', compute='_compute_qty_variance')

    @api.depends('executed_qty', 'qty', 'cost_rate')
    def _compute_qty_variance(self):
        for line in self:
            variance = line.executed_qty - line.qty
            line.qty_variance = variance
            line.variance_cost = variance * line.cost_rate
            line.is_overrun = variance > 0

    # ------------------------------------------------------------------
    # Subcontracting - how much of this item is handed to others
    # ------------------------------------------------------------------
    subcontract_line_ids = fields.One2many(
        'construction.subcontract.line', 'boq_line_id',
        string='Subcontract Assignments')
    subcontracted_qty = fields.Float(
        string='Assigned Quantity', compute='_compute_subcontracting',
        store=True, digits=(12, 3))
    subcontract_cost = fields.Monetary(
        string='Assigned Cost', compute='_compute_subcontracting', store=True,
        help='What the subcontractors charge for the quantities assigned.')
    unassigned_qty = fields.Float(
        string='Unassigned Quantity', compute='_compute_subcontracting',
        store=True, digits=(12, 3))
    is_over_assigned = fields.Boolean(
        string='Over-assigned', compute='_compute_subcontracting', store=True,
        help='More of this item has been handed to subcontractors than the '
             'bill of quantities carries.')
    subcontract_margin = fields.Monetary(
        string='Margin after Subcontracting',
        compute='_compute_subcontracting', store=True,
        help='What the client pays for the assigned quantity, less what the '
             'subcontractors charge for it.')
    subcontract_margin_percent = fields.Float(
        string='Margin after Subcontracting (%)',
        compute='_compute_subcontracting', store=True)

    @api.depends('subcontract_line_ids.qty', 'subcontract_line_ids.amount',
                 'qty', 'unit_rate')
    def _compute_subcontracting(self):
        for line in self:
            assigned = sum(line.subcontract_line_ids.mapped('qty'))
            cost = sum(line.subcontract_line_ids.mapped('amount'))
            line.subcontracted_qty = assigned
            line.subcontract_cost = cost
            line.unassigned_qty = line.qty - assigned
            line.is_over_assigned = assigned > line.qty
            revenue = assigned * line.unit_rate
            line.subcontract_margin = revenue - cost
            line.subcontract_margin_percent = (
                100.0 * line.subcontract_margin / revenue) if revenue else 0.0

    # ------------------------------------------------------------------
    # Forecast: what this item will really cost when it is finished
    # ------------------------------------------------------------------
    expected_cost = fields.Monetary(
        string='Expected Cost', compute='_compute_expected_cost', store=True,
        help='The assigned quantity at what the subcontractors charge, plus '
             'the rest at our own cost rate. What the item will cost once it '
             'is done, rather than what it was budgeted at.')
    expected_margin = fields.Monetary(
        string='Expected Margin', compute='_compute_expected_cost',
        store=True)
    expected_margin_percent = fields.Float(
        string='Expected Margin (%)', compute='_compute_expected_cost',
        store=True)

    @api.depends('qty', 'cost_rate', 'amount', 'subcontracted_qty',
                 'subcontract_cost', 'is_section')
    def _compute_expected_cost(self):
        for line in self:
            if line.is_section:
                line.expected_cost = line.expected_margin = 0.0
                line.expected_margin_percent = 0.0
                continue
            own_qty = max(line.qty - line.subcontracted_qty, 0.0)
            line.expected_cost = line.subcontract_cost + own_qty * line.cost_rate
            line.expected_margin = line.amount - line.expected_cost
            line.expected_margin_percent = (
                100.0 * line.expected_margin / line.amount) \
                if line.amount else 0.0

    # ------------------------------------------------------------------
    # Progress
    # ------------------------------------------------------------------
    own_progress_qty = fields.Float(
        string='Done In-house', compute='_compute_overall_progress',
        digits=(12, 3),
        help='Accepted on work orders, counted only up to the part of the '
             'item that was not handed to a subcontractor.')
    subcontract_progress_qty = fields.Float(
        string='Done by Subcontractors', compute='_compute_overall_progress',
        digits=(12, 3),
        help='Certified to subcontractors, counted only up to what they were '
             'assigned.')
    progress_qty = fields.Float(
        string='Completed Quantity', compute='_compute_overall_progress',
        digits=(12, 3))
    progress_percent = fields.Float(
        compute='_compute_overall_progress',
        help='In-house execution plus certified subcontract work. Each side '
             'is capped at its own share of the item, so an item that is part '
             'self-performed and part subcontracted is never counted twice.')

    def _compute_overall_progress(self):
        for line in self:
            assigned = min(line.subcontracted_qty, line.qty) if line.qty \
                else line.subcontracted_qty
            own_scope = max(line.qty - assigned, 0.0)
            own = min(line.executed_qty, own_scope)
            subbed = min(line.subcontract_certified_qty, assigned)
            line.own_progress_qty = own
            line.subcontract_progress_qty = subbed
            line.progress_qty = own + subbed
            line.progress_percent = min(
                100.0, line.progress_qty / line.qty * 100.0) if line.qty else 0.0

    @api.depends('item_no', 'description')
    def _compute_display_name(self):
        """The base module gives these lines no name, so Odoo falls back to
        "construction.boq.line,3" wherever one is referenced."""
        for line in self:
            parts = [part for part in (line.item_no, line.description) if part]
            line.display_name = ' - '.join(parts) or self.env._('Item')
