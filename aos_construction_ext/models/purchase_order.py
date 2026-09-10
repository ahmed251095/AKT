from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    construction_work_order_id = fields.Many2one(
        'construction.work.order', string='Work Order', index=True,
        compute='_compute_construction_work_order', store=True, readonly=False,
        help='The work order this purchase serves. Filled from the material '
             'requisition, and editable for a purchase raised directly.')

    @api.depends('construction_requisition_id')
    def _compute_construction_work_order(self):
        for order in self:
            requisition = order.construction_requisition_id
            if requisition.work_order_id:
                order.construction_work_order_id = requisition.work_order_id


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    construction_work_order_id = fields.Many2one(
        related='order_id.construction_work_order_id', store=True, index=True,
        string='Work Order')
    # Pricing is judged here, on the quotation, against the rate the item was
    # priced on -- not on the requisition, which only says what is needed.
    boq_cost_rate = fields.Monetary(
        string='Item Cost Rate', currency_field='currency_id',
        related='construction_boq_line_id.cost_rate',
        help='The rate the bill of quantities item was priced on. What the '
             'job can afford to pay for one unit.')
    price_over_boq_rate = fields.Monetary(
        string='Over Item Rate', compute='_compute_price_over_boq_rate',
        currency_field='currency_id',
        help='Quoted price less the item cost rate, per unit. A positive '
             'figure eats into the margin the item was priced with.')

    @api.depends('boq_cost_rate', 'price_unit')
    def _compute_price_over_boq_rate(self):
        for line in self:
            # Nothing to compare while the quotation is still waiting on the
            # vendor: an empty price would otherwise read as a big saving.
            line.price_over_boq_rate = (
                line.price_unit - line.boq_cost_rate
                if line.boq_cost_rate and line.price_unit else 0.0)
