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
    estimated_unit_cost = fields.Monetary(
        string='Estimated Unit Cost', currency_field='currency_id',
        help='What the material requisition expected this to cost. Compare it '
             'with the price the vendor quoted.')
    estimate_variance = fields.Monetary(
        string='Against Estimate', compute='_compute_estimate_variance',
        currency_field='currency_id',
        help='Estimate less quoted price, per unit. Negative means the vendor '
             'is dearer than the request assumed.')

    @api.depends('estimated_unit_cost', 'price_unit')
    def _compute_estimate_variance(self):
        for line in self:
            line.estimate_variance = (
                line.estimated_unit_cost - line.price_unit
                if line.estimated_unit_cost else 0.0)

    def _clear_price_for_quotation(self):
        """Leave the price for the vendor to fill.

        A request for quotation with no price is what it should look like
        before the vendor answers. Carrying the requisition's estimate through
        as the price is how an estimate turned into the project's real cost.
        """
        self.filtered('estimated_unit_cost').price_unit = 0.0
