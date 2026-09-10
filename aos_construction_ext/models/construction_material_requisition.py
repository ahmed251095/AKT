from odoo import api, fields, models


class ConstructionMaterialRequisition(models.Model):
    _inherit = 'construction.material.requisition'

    def action_create_rfq(self):
        """Let the vendor set the price.

        The base copies the requisition's estimate into the request for
        quotation, so a figure the site put in to get the request approved
        arrives at the vendor as an agreed price -- and from there it becomes
        the project's actual cost. The estimate is kept on the line for
        comparison instead, and the price comes from the vendor.
        """
        result = super().action_create_rfq()
        orders = self.purchase_order_ids.filtered(
            lambda order: order.state in ('draft', 'sent'))
        for line in orders.order_line:
            line.estimated_unit_cost = line.price_unit
        orders.order_line._clear_price_for_quotation()
        return result


class ConstructionMaterialRequisitionLine(models.Model):
    _inherit = 'construction.material.requisition.line'

    unit_price = fields.Monetary(
        string='Estimated Unit Cost',
        help='What this material is expected to cost, for approving the '
             'request against the budget. The price comes from the vendor on '
             'the purchase order.')
    boq_cost_rate = fields.Monetary(
        string='Item Cost Rate', related='boq_line_id.cost_rate',
        help='The rate the bill of quantities item was priced on.')

    @api.depends('qty_requested', 'qty_approved', 'unit_price')
    def _compute_subtotal(self):
        """Value what was approved, once somebody has approved something.

        The base always valued the requested quantity, so cutting a request
        down at approval left the estimate reading the original ask.
        """
        for line in self:
            quantity = line.qty_approved or line.qty_requested
            line.subtotal = quantity * line.unit_price

    @api.onchange('product_id', 'boq_line_id')
    def _onchange_product_id(self):
        """Estimate from the item the project was priced on.

        A product's standard cost is a warehouse average and is often zero on
        a construction catalogue; the bill of quantities rate is the figure
        the job was actually costed against.
        """
        result = super()._onchange_product_id()
        if self.boq_line_id and self.boq_line_id.cost_rate:
            self.unit_price = self.boq_line_id.cost_rate
        return result
