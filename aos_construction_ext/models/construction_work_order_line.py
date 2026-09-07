from odoo import api, fields, models
from odoo.tools import float_compare
from odoo.exceptions import ValidationError


class ConstructionWorkOrderLine(models.Model):
    _inherit = 'construction.work.order.line'

    inhouse_scope_qty = fields.Float(
        string='In-house Scope', compute='_compute_inhouse_availability',
        digits=(12, 3),
        help='The part of the BOQ item that was not handed to a '
             'subcontractor, so it is ours to execute.')
    inhouse_available_qty = fields.Float(
        string='Still Available', compute='_compute_inhouse_availability',
        digits=(12, 3),
        help='In-house scope less what other work orders already plan for '
             'this item.')

    @api.depends('boq_line_id', 'work_order_id.state')
    def _compute_inhouse_availability(self):
        for line in self:
            boq = line.boq_line_id
            if not boq:
                line.inhouse_scope_qty = line.inhouse_available_qty = 0.0
                continue
            scope = max(boq.qty - boq.subcontracted_qty, 0.0)
            planned_elsewhere = sum(
                other.planned_qty for other in boq.work_order_line_ids
                if other != line and other.work_order_id.state != 'cancelled')
            line.inhouse_scope_qty = scope
            line.inhouse_available_qty = max(scope - planned_elsewhere, 0.0)

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        """Offer what is actually ours to do.

        The base module offers the whole remaining bill quantity, which counts
        neither the part handed to a subcontractor nor what other work orders
        already plan -- so the first work order on an item proposes all of it.
        """
        result = super()._onchange_boq_line_id()
        if self.boq_line_id:
            self.planned_qty = self.inhouse_available_qty
        return result

    @api.constrains('accepted_qty', 'boq_line_id')
    def _check_total_execution(self):
        """Own work plus certified subcontract work cannot exceed the item."""
        for line in self:
            boq = line.boq_line_id
            if not boq or not boq.qty:
                continue
            accepted = sum(
                other.accepted_qty for other in boq.work_order_line_ids
                if other.work_order_id.state != 'cancelled')
            total = accepted + boq.subcontract_certified_qty
            if float_compare(total, boq.qty, precision_digits=3) > 0:
                raise ValidationError(self.env._(
                    'Execution of "%(item)s" would reach %(total)s against a '
                    'bill quantity of %(qty)s.\n'
                    'Accepted on work orders: %(accepted)s\n'
                    'Certified to subcontractors: %(certified)s',
                    item=boq.display_name, total=total, qty=boq.qty,
                    accepted=accepted, certified=boq.subcontract_certified_qty))
