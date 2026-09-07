from odoo import api, fields, models


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

    certified_qty = fields.Float(
        string='Certified Quantity', compute='_compute_certified',
        help='Quantity of this item already certified to the subcontractor.')
    remaining_qty = fields.Float(
        string='Remaining Quantity', compute='_compute_certified')

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

    @api.depends('qty', 'unit_price', 'boq_unit_rate')
    def _compute_amounts(self):
        for line in self:
            line.amount = line.qty * line.unit_price
            revenue = line.qty * line.boq_unit_rate
            line.margin = revenue - line.amount
            line.margin_percent = (
                100.0 * line.margin / revenue) if revenue else 0.0

    def _compute_certified(self):
        Billing = self.env['construction.ra.billing.line']
        for line in self:
            certified = Billing.search([
                ('billing_id.subcontract_id', '=', line.subcontract_id.id),
                ('billing_id.state', 'in',
                 ('approved', 'invoiced', 'paid')),
                ('boq_line_id', '=', line.boq_line_id.id),
            ])
            line.certified_qty = sum(certified.mapped('qty_current'))
            line.remaining_qty = line.qty - line.certified_qty

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        """Offer the quantity nobody has been given yet."""
        if not self.boq_line_id:
            return
        if not self.qty:
            self.qty = max(self.boq_line_id.unassigned_qty, 0.0)
        if not self.unit_price:
            self.unit_price = self.boq_line_id.cost_rate
