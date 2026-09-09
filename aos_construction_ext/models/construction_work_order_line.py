from odoo import api, fields, models
from odoo.tools import float_compare
from odoo.exceptions import ValidationError

#: Purchases only count once the order is committed.
PURCHASE_STATES = ('purchase', 'done')


class ConstructionWorkOrder(models.Model):
    _inherit = 'construction.work.order'

    # The base module leaves these as plain fields nobody fills, so a work
    # order whose lines carry real money shows zero at the top.
    # Not stored: the line figures are computed live from purchase and
    # expense records, and a stored total cannot be told when those change.
    planned_cost = fields.Monetary(
        compute='_compute_line_costs', store=False)
    actual_cost = fields.Monetary(
        compute='_compute_line_costs', store=False)
    earned_cost = fields.Monetary(
        string='Earned Cost', compute='_compute_line_costs',
        help='Accepted work valued at the item cost rates: what it should '
             'have cost.')
    cost_variance = fields.Monetary(
        string='Cost Variance', compute='_compute_line_costs',
        help='Earned cost less what was actually spent. Negative means the '
             'work cost more than the rates allowed.')

    def _compute_line_costs(self):
        for order in self:
            order.planned_cost = sum(order.line_ids.mapped('planned_cost'))
            order.actual_cost = sum(order.line_ids.mapped('actual_cost'))
            order.earned_cost = sum(order.line_ids.mapped('earned_cost'))
            order.cost_variance = order.earned_cost - order.actual_cost


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

    # ------------------------------------------------------------------
    # Cost: what this item actually cost, from the money spent on it
    # ------------------------------------------------------------------
    purchase_cost = fields.Monetary(
        string='Purchases', compute='_compute_actual_costs', store=False,
        help='Purchase orders, plus material and equipment expenses, booked '
             'against this item on this work order.')
    labour_cost = fields.Monetary(
        string='Labour', compute='_compute_actual_costs',
        help='Approved labour expenses booked against this item.')
    other_cost = fields.Monetary(
        string='Other Costs', compute='_compute_actual_costs',
        help='Approved overhead and miscellaneous expenses booked against '
             'this item.')
    actual_cost = fields.Monetary(
        compute='_compute_actual_costs', store=False)
    actual_unit_cost = fields.Monetary(
        string='Actual Unit Cost', compute='_compute_actual_costs',
        help='What one unit really cost: total spend divided by the accepted '
             'quantity.')
    earned_cost = fields.Monetary(
        string='Earned Cost', compute='_compute_actual_costs',
        help='Accepted quantity at the item cost rate: what it should have '
             'cost.')
    cost_variance = fields.Monetary(
        string='Cost Variance', compute='_compute_actual_costs')

    def _compute_actual_costs(self):
        PurchaseLine = self.env['purchase.order.line']
        Expense = self.env['construction.expense']
        for line in self:
            order, boq = line.work_order_id, line.boq_line_id
            purchases = labour = other = 0.0
            if order and boq:
                po_lines = PurchaseLine.search([
                    ('construction_work_order_id', '=', order.id),
                    ('construction_boq_line_id', '=', boq.id),
                    ('order_id.state', 'in', PURCHASE_STATES),
                ])
                purchases = sum(po_lines.mapped('price_subtotal'))
                expenses = Expense.search([
                    ('work_order_id', '=', order.id),
                    ('boq_line_id', '=', boq.id),
                    ('state', '=', 'approved'),
                ])
                for expense in expenses:
                    if expense.category == 'labour':
                        labour += expense.amount
                    elif expense.category in ('material', 'equipment'):
                        purchases += expense.amount
                    else:
                        other += expense.amount
            line.purchase_cost = purchases
            line.labour_cost = labour
            line.other_cost = other
            line.actual_cost = purchases + labour + other
            line.actual_unit_cost = (
                line.actual_cost / line.accepted_qty) if line.accepted_qty \
                else 0.0
            line.earned_cost = line.accepted_qty * line.unit_cost
            line.cost_variance = line.earned_cost - line.actual_cost

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
            scope = max(boq.qty - boq.subcontracted_qty, 0.0)
            if float_compare(accepted, scope, precision_digits=3) > 0:
                raise ValidationError(self.env._(
                    'Work orders accept %(accepted)s of "%(item)s", but only '
                    '%(scope)s is ours to execute: %(assigned)s of the '
                    '%(qty)s in the bill is assigned to subcontractors.\n'
                    'Reduce the assignment first if we are doing this work '
                    'ourselves.',
                    accepted=accepted, item=boq.display_name, scope=scope,
                    assigned=boq.subcontracted_qty, qty=boq.qty))
