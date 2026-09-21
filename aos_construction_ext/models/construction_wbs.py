from odoo import api, fields, models


class ConstructionWbs(models.Model):
    _inherit = 'construction.wbs'

    # Computed from the items in the phase, but still writable: marking a
    # phase complete sets it to 100, and a planner may override it.
    progress = fields.Float(
        compute='_compute_progress_from_boq', store=True, readonly=False,
        help='Weighted by item value, so a large item moves the phase more '
             'than a small one.')

    @api.depends('boq_line_ids.progress_percent', 'boq_line_ids.amount',
                 'boq_line_ids.qty')
    def _compute_progress_from_boq(self):
        for phase in self:
            phase.progress = _weighted_progress(phase.boq_line_ids)

    # The base module stores this one and depends on the work order's actual
    # cost -- which this module computes live from purchase orders and
    # expenses. A stored field cannot be told that a purchase order was just
    # confirmed, so the phase kept whatever was written the day it was
    # created, usually zero. Read it live instead; the figure is a sum over a
    # handful of work orders.
    actual_cost = fields.Monetary(
        compute='_compute_actual_cost', store=False,
        currency_field='currency_id')

    @api.depends('work_order_ids.actual_cost')
    def _compute_actual_cost(self):
        for phase in self:
            phase.actual_cost = sum(phase.work_order_ids.mapped('actual_cost'))


def _weighted_progress(boq_lines):
    """Physical progress by value: what a contractor means by 'percent done'.

    Averaging item percentages would let a trivial item count as much as the
    structure, so each item is weighted by its value -- or by quantity when
    the items carry no price yet.
    """
    lines = boq_lines.filtered(lambda line: not line.is_section)
    if not lines:
        return 0.0
    weights = [line.amount for line in lines]
    if not sum(weights):
        weights = [line.qty for line in lines]
    total = sum(weights)
    if not total:
        return 0.0
    return sum(
        weight * line.progress_percent
        for line, weight in zip(lines, weights)
    ) / total
