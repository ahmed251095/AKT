from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare


class ConstructionMaterialRequisition(models.Model):
    _inherit = 'construction.material.requisition'

    def action_approve(self):
        """Approving a requisition is approving quantities.

        The base only flipped the state, so a line could reach the request for
        quotation with nothing approved on it and fall back to whatever the
        site asked for. Approving now states the quantity: the requested
        amount unless the approver cut it down.
        """
        for line in self.line_ids.filtered(lambda l: not l.qty_approved):
            line.qty_approved = line.qty_requested
        return super().action_approve()

    def action_create_rfq(self):
        """Send the vendor quantities, not a price.

        The base copied the requisition's own figure into the quotation as
        price_unit, so a number typed in to get the request approved arrived
        at the vendor as an agreed price -- and from there became the
        project's actual cost. Pricing belongs to the quotation, where it has
        its own approval.
        """
        result = super().action_create_rfq()
        self.purchase_order_ids.filtered(
            lambda order: order.state in ('draft', 'sent')
        ).order_line.price_unit = 0.0
        return result


class ConstructionMaterialRequisitionLine(models.Model):
    _inherit = 'construction.material.requisition.line'

    @api.constrains('qty_approved', 'qty_requested')
    def _check_qty_approved(self):
        for line in self:
            if float_compare(line.qty_approved, line.qty_requested,
                             precision_digits=3) > 0:
                raise ValidationError(self.env._(
                    'Approving %(approved)s of "%(item)s" is more than the '
                    '%(requested)s the site asked for.',
                    approved=line.qty_approved,
                    item=line.description or line.display_name,
                    requested=line.qty_requested))
