from odoo import api, fields, models


class ConstructionWbs(models.Model):
    _inherit = 'construction.wbs'

    # What the phase is actually made of.
    #
    # A bill of quantities item is not owned by a phase: part of it can be
    # built in one and part in another, and part of it handed to a
    # subcontractor. So the phase is read off the documents that carry the
    # work -- the work order for what we build ourselves, the subcontract for
    # what we hand out -- and each of those names its phase once. The two
    # sides cannot overlap either: an item's in-house scope is its quantity
    # less what was assigned to subcontractors, and the work orders are held
    # to it.
    work_order_line_ids = fields.One2many(
        'construction.work.order.line', 'wbs_id', string='In-house Items',
        readonly=True)
    subcontract_line_ids = fields.One2many(
        'construction.subcontract.line', 'wbs_id',
        string='Subcontracted Items', readonly=True)

    def _inhouse_scope(self):
        """Our own items in this phase. A cancelled order carries nothing."""
        return self.work_order_line_ids.filtered(
            lambda line: line.work_order_id.state != 'cancelled')

    def _subcontract_scope(self):
        """Assigned items in this phase.

        A draft contract counts -- the work is planned even before it is
        signed -- but a terminated one no longer is.
        """
        return self.subcontract_line_ids.filtered(
            lambda line: line.subcontract_id.state != 'terminated')

    # Computed from the work in the phase, but still writable: marking a
    # phase complete sets it to 100, and a planner may override it.
    progress = fields.Float(
        compute='_compute_progress_from_scope', store=True, readonly=False,
        help='Weighted by item value, so a large item moves the phase more '
             'than a small one. What we build and what a subcontractor builds '
             'count the same way.')

    @api.depends('work_order_line_ids.planned_qty',
                 'work_order_line_ids.accepted_qty',
                 'work_order_line_ids.boq_line_id.unit_rate',
                 'work_order_line_ids.work_order_id.state',
                 'subcontract_line_ids.qty',
                 'subcontract_line_ids.progress_percent',
                 'subcontract_line_ids.boq_unit_rate',
                 'subcontract_line_ids.subcontract_id.state')
    def _compute_progress_from_scope(self):
        for phase in self:
            rows = phase._scope_progress_rows()
            # By value, or by quantity while the items carry no price yet.
            value_total = sum(value for value, _qty, _done in rows)
            if value_total:
                phase.progress = sum(
                    value * done for value, _qty, done in rows) / value_total
                continue
            qty_total = sum(qty for _value, qty, _done in rows)
            phase.progress = sum(
                qty * done for _value, qty, done in rows
            ) / qty_total if qty_total else 0.0

    def _scope_progress_rows(self):
        """(value, quantity, percent done) for every item in the phase."""
        self.ensure_one()
        rows = []
        for line in self._inhouse_scope():
            done = (100.0 * line.accepted_qty / line.planned_qty) \
                if line.planned_qty else 0.0
            rows.append((line.planned_qty * line.boq_line_id.unit_rate,
                         line.planned_qty, min(done, 100.0)))
        for line in self._subcontract_scope():
            rows.append((line.qty * line.boq_unit_rate, line.qty,
                         line.progress_percent))
        return rows

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

    # Same compute as the base keeps it on, on purpose: that method assigns
    # this field among others, so moving it elsewhere would leave two writers
    # racing for it.
    forecast_cost = fields.Monetary(
        string='Forecast Cost at Completion', compute='_compute_cost_control',
        currency_field='currency_id',
        help='What the phase is heading to cost: the finished work at what it '
             'actually cost, plus the work still to do at the subcontractor '
             'and cost rates.')
    forecast_margin = fields.Monetary(
        help='Contract value for the phase less what it is now heading to '
             'cost: what the finished work actually cost, plus the work still '
             'to do at the subcontractor and cost rates. It moves with the '
             'spending, unlike the budget margin it replaced.')

    def _compute_cost_control(self):
        """Read the phase off the work it carries, not off the bill items.

        The base takes every figure from the bill of quantities items whose
        phase field points here, and that field is not filled any more: an
        item belongs to no phase, the work orders and the subcontracts do.
        Left alone, every budget figure on a phase reads zero and the forecast
        collapses onto what has already been spent.

        The margin goes the same way as the cost. The base reads it as budget
        revenue less budget cost, the margin the estimator priced, which never
        moves again however the site spends. A forecast has to carry what the
        work already cost and price only the rest at the rates.
        """
        super()._compute_cost_control()
        for phase in self:
            inhouse = phase._inhouse_scope()
            subbed = phase._subcontract_scope()

            # What the phase is worth to us: every quantity at the rate the
            # client pays for it, whoever ends up building it.
            phase.budget_revenue = sum(
                line.planned_qty * line.boq_line_id.unit_rate
                for line in inhouse
            ) + sum(line.qty * line.boq_unit_rate for line in subbed)

            # What it was budgeted to cost: our own work at the item cost
            # rate, the assigned work at what the subcontractor charges.
            phase.budget_cost = sum(
                line.planned_qty * line.unit_cost for line in inhouse
            ) + sum(line.amount for line in subbed)

            # The other half of what has been spent: our own work not yet
            # accepted, and assigned quantities not yet certified. Each
            # complements a spent figure below, so nothing is counted twice.
            remaining = sum(
                max(line.planned_qty - line.accepted_qty, 0.0) * line.unit_cost
                for line in inhouse
            ) + sum(
                max(line.qty - line.certified_qty, 0.0) * line.unit_price
                for line in subbed)

            spent = phase.actual_cost + phase.certified_subcontract_cost
            phase.forecast_cost = spent + remaining
            phase.forecast_margin = phase.budget_revenue - phase.forecast_cost


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
