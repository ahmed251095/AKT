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
