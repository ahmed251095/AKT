from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class ConstructionSubcontractLine(models.Model):
    """One BOQ item handed to a subcontractor, at the price we pay them.

    A lump-sum subcontract hides the only number that decides whether a
    contractor makes money: what an item sells for against what it costs to
    have someone else build it. Assigning items line by line puts that
    difference on the record, item by item.
    """
    _name = 'construction.subcontract.line'
    _description = 'Subcontract Item'
    _order = 'sequence, id'

    subcontract_id = fields.Many2one(
        'construction.subcontract', string='Subcontract', required=True,
        ondelete='cascade', index=True)
    project_id = fields.Many2one(
        related='subcontract_id.project_id', string='Project', store=True)
    sequence = fields.Integer(string='Sequence', default=10)

    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item', required=True, index=True,
        domain="[('boq_id.project_id', '=', project_id), "
               "('is_section', '=', False)]")
    description = fields.Char(
        string='Description', compute='_compute_from_boq', store=True,
        readonly=False)
    uom_id = fields.Many2one(
        'uom.uom', string='UOM', compute='_compute_from_boq', store=True,
        readonly=False)
    work_type = fields.Selection(
        related='boq_line_id.work_type', string='Work Type', store=True)

    boq_qty = fields.Float(
        related='boq_line_id.qty', string='BOQ Quantity')
    boq_unit_rate = fields.Monetary(
        related='boq_line_id.unit_rate', string='Selling Rate')
    boq_cost_rate = fields.Monetary(
        related='boq_line_id.cost_rate', string='Own Cost Rate')

    qty = fields.Float(
        string='Assigned Quantity', digits=(12, 3), required=True, default=0.0)
    unit_price = fields.Monetary(
        string='Subcontractor Rate',
        help='What we pay the subcontractor for one unit.')
    amount = fields.Monetary(
        string='Assigned Value', compute='_compute_amounts', store=True)

    margin = fields.Monetary(
        string='Item Margin', compute='_compute_amounts', store=True,
        help='What the client pays us for this quantity, less what the '
             'subcontractor charges for it.')
    margin_percent = fields.Float(
        string='Item Margin (%)', compute='_compute_amounts', store=True)

    progress_percent = fields.Float(
        string='Progress (%)',
        help='How much of this item the engineer accepts as complete. This is '
             'what the next certificate is measured from.')
    progress_qty = fields.Float(
        string='Completed Quantity', compute='_compute_progress', store=True,
        digits=(12, 3))

    certified_qty = fields.Float(
        string='Certified Quantity', compute='_compute_certified',
        help='Quantity of this item already certified to the subcontractor.')
    remaining_qty = fields.Float(
        string='Remaining Quantity', compute='_compute_certified')
    qty_to_certify = fields.Float(
        string='Quantity to Certify', compute='_compute_certified',
        digits=(12, 3),
        help='Completed less already certified: what the next certificate '
             'covers.')
    amount_to_certify = fields.Monetary(
        string='Value to Certify', compute='_compute_certified')

    price_headroom = fields.Monetary(
        string='Headroom to Cost', compute='_compute_amounts', store=True,
        help='Our own cost rate for the item less what the subcontractor '
             'charges. What is left of the item budget before handing it out '
             'starts eating the priced margin.')

    currency_id = fields.Many2one(
        related='subcontract_id.currency_id', string='Currency')
    notes = fields.Char(string='Notes')

    @api.depends('boq_line_id')
    def _compute_from_boq(self):
        for line in self:
            if not line.boq_line_id:
                continue
            line.description = line.boq_line_id.description
            line.uom_id = line.boq_line_id.uom_id

    @api.depends('qty', 'unit_price', 'boq_unit_rate', 'boq_cost_rate')
    def _compute_amounts(self):
        for line in self:
            line.amount = line.qty * line.unit_price
            revenue = line.qty * line.boq_unit_rate
            line.margin = revenue - line.amount
            line.margin_percent = (
                100.0 * line.margin / revenue) if revenue else 0.0
            line.price_headroom = line.boq_cost_rate - line.unit_price

    @api.constrains('unit_price', 'boq_line_id')
    def _check_price_within_item_cost(self):
        """An item may not be handed out for more than it was priced to cost.

        The cost rate is the budget the bid was built on. Paying a
        subcontractor above it spends margin that was already promised to the
        client's price, and nothing else in the system would notice.
        """
        for line in self:
            budget = line.boq_line_id.cost_rate
            if not budget:
                # An item priced by hand carries no cost budget to check.
                continue
            if float_compare(line.unit_price, budget, precision_digits=2) > 0:
                raise ValidationError(self.env._(
                    'The subcontractor rate for "%(item)s" is %(rate)s, above '
                    'the %(budget)s the item was priced to cost.\n'
                    'Either negotiate the rate down, or correct the item cost '
                    'in the bill of quantities if the estimate was wrong.',
                    item=line.boq_line_id.display_name,
                    rate=line.unit_price, budget=budget))

    @api.depends('qty', 'progress_percent')
    def _compute_progress(self):
        for line in self:
            line.progress_qty = line.qty * line.progress_percent / 100.0

    def _compute_certified(self):
        Billing = self.env['construction.ra.billing.line']
        for line in self:
            # A draft certificate claims its quantity too, or the same work
            # gets certified again while the first one is being checked.
            certified = Billing.search([
                ('billing_id.subcontract_id', '=', line.subcontract_id.id),
                ('billing_id.state', '!=', 'cancelled'),
                ('boq_line_id', '=', line.boq_line_id.id),
            ])
            line.certified_qty = sum(certified.mapped('qty_current'))
            line.remaining_qty = line.qty - line.certified_qty
            # Never bill backwards: a certificate covers what has been
            # completed since the last one, never a negative correction.
            line.qty_to_certify = max(
                line.progress_qty - line.certified_qty, 0.0)
            line.amount_to_certify = line.qty_to_certify * line.unit_price

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        """Offer the quantity nobody has been given yet."""
        if not self.boq_line_id:
            return
        if not self.qty:
            self.qty = max(self.boq_line_id.unassigned_qty, 0.0)
        if not self.unit_price:
            self.unit_price = self.boq_line_id.cost_rate
