# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ConstructionBOQLine(models.Model):
    _inherit = 'construction.boq.line'

    product_id = fields.Many2one('product.product', string='Product / Service')
    cost_rate = fields.Monetary(string='Budget Cost Rate', currency_field='currency_id')
    budget_cost = fields.Monetary(compute='_compute_budget_control', store=True, currency_field='currency_id')
    budget_margin = fields.Monetary(compute='_compute_budget_control', store=True, currency_field='currency_id')
    budget_margin_percent = fields.Float(compute='_compute_budget_control', store=True)

    work_order_line_ids = fields.One2many('construction.work.order.line', 'boq_line_id', string='Work Execution')
    requisition_line_ids = fields.One2many('construction.material.requisition.line', 'boq_line_id', string='Material Requests')
    purchase_line_ids = fields.One2many('purchase.order.line', 'construction_boq_line_id', string='Purchase Lines')
    billing_line_ids = fields.One2many('construction.ra.billing.line', 'boq_line_id', string='Certificate Lines')

    executed_qty = fields.Float(compute='_compute_control_quantities', digits=(12, 3))
    purchased_qty = fields.Float(compute='_compute_control_quantities', digits=(12, 3))
    customer_certified_qty = fields.Float(compute='_compute_control_quantities', digits=(12, 3))
    subcontract_certified_qty = fields.Float(compute='_compute_control_quantities', digits=(12, 3))
    remaining_execution_qty = fields.Float(compute='_compute_control_quantities', digits=(12, 3))
    progress_percent = fields.Float(compute='_compute_control_quantities')

    @api.depends('qty', 'unit_rate', 'cost_rate', 'is_section')
    def _compute_budget_control(self):
        for line in self:
            if line.is_section:
                line.budget_cost = line.budget_margin = line.budget_margin_percent = 0.0
                continue
            line.budget_cost = line.qty * line.cost_rate
            line.budget_margin = line.amount - line.budget_cost
            line.budget_margin_percent = (line.budget_margin / line.amount * 100.0) if line.amount else 0.0

    def _compute_control_quantities(self):
        for line in self:
            execution = line.work_order_line_ids.filtered(lambda x: x.work_order_id.state != 'cancelled')
            purchases = line.purchase_line_ids.filtered(lambda x: x.order_id.state in ('purchase', 'done'))
            certificates = line.billing_line_ids.filtered(
                lambda x: x.billing_id.state in ('approved', 'invoiced', 'paid'))
            line.executed_qty = sum(execution.mapped('accepted_qty'))
            line.purchased_qty = sum(purchases.mapped('product_qty'))
            line.customer_certified_qty = sum(certificates.filtered(
                lambda x: x.billing_id.billing_type == 'customer').mapped('qty_current'))
            line.subcontract_certified_qty = sum(certificates.filtered(
                lambda x: x.billing_id.billing_type == 'subcontractor').mapped('qty_current'))
            line.remaining_execution_qty = max(line.qty - line.executed_qty, 0.0)
            line.progress_percent = min((line.executed_qty / line.qty * 100.0) if line.qty else 0.0, 100.0)


class ConstructionWBS(models.Model):
    _inherit = 'construction.wbs'

    boq_line_ids = fields.One2many('construction.boq.line', 'wbs_id', string='BOQ Items')
    budget_revenue = fields.Monetary(compute='_compute_cost_control', currency_field='currency_id')
    budget_cost = fields.Monetary(compute='_compute_cost_control', currency_field='currency_id')
    committed_cost = fields.Monetary(compute='_compute_cost_control', currency_field='currency_id')
    certified_revenue = fields.Monetary(compute='_compute_cost_control', currency_field='currency_id')
    certified_subcontract_cost = fields.Monetary(compute='_compute_cost_control', currency_field='currency_id')
    forecast_margin = fields.Monetary(compute='_compute_cost_control', currency_field='currency_id')

    def _compute_cost_control(self):
        PurchaseLine = self.env['purchase.order.line']
        BillingLine = self.env['construction.ra.billing.line']
        for phase in self:
            boq_lines = phase.boq_line_ids
            phase.budget_revenue = sum(boq_lines.mapped('amount'))
            phase.budget_cost = sum(boq_lines.mapped('budget_cost'))
            po_lines = PurchaseLine.search([
                ('construction_wbs_id', '=', phase.id),
                ('order_id.state', 'in', ('purchase', 'done')),
            ])
            phase.committed_cost = sum(po_lines.mapped('price_subtotal'))
            cert_lines = BillingLine.search([
                ('wbs_id', '=', phase.id),
                ('billing_id.state', 'in', ('approved', 'invoiced', 'paid')),
            ])
            phase.certified_revenue = sum(cert_lines.filtered(
                lambda x: x.billing_id.billing_type == 'customer').mapped('amount'))
            phase.certified_subcontract_cost = sum(cert_lines.filtered(
                lambda x: x.billing_id.billing_type == 'subcontractor').mapped('amount'))
            phase.forecast_margin = phase.budget_revenue - phase.budget_cost
            if boq_lines:
                total_weight = sum(boq_lines.mapped('amount')) or sum(boq_lines.mapped('qty'))
                if total_weight:
                    phase.progress = sum(
                        (line.amount or line.qty) * line.progress_percent for line in boq_lines
                    ) / total_weight


class ConstructionWorkOrder(models.Model):
    _inherit = 'construction.work.order'

    line_ids = fields.One2many('construction.work.order.line', 'work_order_id', string='Execution Lines', copy=True)
    planned_qty = fields.Float(compute='_compute_execution', digits=(12, 3))
    executed_qty = fields.Float(compute='_compute_execution', digits=(12, 3))
    accepted_qty = fields.Float(compute='_compute_execution', digits=(12, 3))
    progress_percent = fields.Float(compute='_compute_execution')

    @api.depends('line_ids.planned_qty', 'line_ids.executed_qty', 'line_ids.accepted_qty')
    def _compute_execution(self):
        for order in self:
            order.planned_qty = sum(order.line_ids.mapped('planned_qty'))
            order.executed_qty = sum(order.line_ids.mapped('executed_qty'))
            order.accepted_qty = sum(order.line_ids.mapped('accepted_qty'))
            order.progress_percent = min(
                order.accepted_qty / order.planned_qty * 100.0 if order.planned_qty else 0.0, 100.0)

    @api.onchange('wbs_id')
    def _onchange_wbs_id(self):
        if self.wbs_id and self.project_id != self.wbs_id.project_id:
            self.project_id = self.wbs_id.project_id


class ConstructionWorkOrderLine(models.Model):
    _name = 'construction.work.order.line'
    _description = 'Construction Work Order Execution Line'
    _order = 'sequence, id'

    sequence = fields.Integer(default=10)
    work_order_id = fields.Many2one('construction.work.order', required=True, ondelete='cascade')
    project_id = fields.Many2one(related='work_order_id.project_id', store=True, index=True)
    wbs_id = fields.Many2one(related='work_order_id.wbs_id', store=True, index=True)
    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item', required=True,
        domain="[('boq_id.project_id', '=', parent.project_id), ('wbs_id', '=', parent.wbs_id), ('is_section', '=', False)]")
    description = fields.Char(required=True)
    uom_id = fields.Many2one('uom.uom', string='UOM')
    planned_qty = fields.Float(digits=(12, 3))
    executed_qty = fields.Float(digits=(12, 3))
    accepted_qty = fields.Float(digits=(12, 3))
    rejected_qty = fields.Float(compute='_compute_quantities', store=True, digits=(12, 3))
    completion_percent = fields.Float(compute='_compute_quantities', store=True)
    unit_cost = fields.Monetary(currency_field='currency_id')
    planned_cost = fields.Monetary(compute='_compute_quantities', store=True, currency_field='currency_id')
    actual_cost = fields.Monetary(compute='_compute_quantities', store=True, currency_field='currency_id')
    currency_id = fields.Many2one(related='work_order_id.currency_id', store=True)

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        if self.boq_line_id:
            self.description = self.boq_line_id.description
            self.uom_id = self.boq_line_id.uom_id
            self.planned_qty = max(self.boq_line_id.remaining_execution_qty, 0.0)
            self.unit_cost = self.boq_line_id.cost_rate

    @api.depends('planned_qty', 'executed_qty', 'accepted_qty', 'unit_cost')
    def _compute_quantities(self):
        for line in self:
            line.rejected_qty = max(line.executed_qty - line.accepted_qty, 0.0)
            line.completion_percent = min(
                line.accepted_qty / line.planned_qty * 100.0 if line.planned_qty else 0.0, 100.0)
            line.planned_cost = line.planned_qty * line.unit_cost
            line.actual_cost = line.accepted_qty * line.unit_cost

    @api.constrains('planned_qty', 'executed_qty', 'accepted_qty')
    def _check_quantities(self):
        for line in self:
            if min(line.planned_qty, line.executed_qty, line.accepted_qty) < 0:
                raise ValidationError(_('Work order quantities cannot be negative.'))
            if line.accepted_qty > line.executed_qty:
                raise ValidationError(_('Accepted quantity cannot exceed executed quantity.'))
            if line.boq_line_id:
                other_qty = sum(line.boq_line_id.work_order_line_ids.filtered(
                    lambda x: x != line and x.work_order_id.state != 'cancelled'
                ).mapped('accepted_qty'))
                if other_qty + line.accepted_qty > line.boq_line_id.qty:
                    raise ValidationError(_('Accepted quantity exceeds the BOQ contract quantity.'))


class ConstructionMaterialRequisition(models.Model):
    _inherit = 'construction.material.requisition'

    wbs_id = fields.Many2one('construction.wbs', string='WBS Phase', domain="[('project_id', '=', project_id)]")

    @api.onchange('work_order_id')
    def _onchange_work_order(self):
        if self.work_order_id:
            self.wbs_id = self.work_order_id.wbs_id


class ConstructionMaterialRequisitionLine(models.Model):
    _inherit = 'construction.material.requisition.line'

    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item',
        domain="[('boq_id.project_id', '=', parent.project_id), ('wbs_id', '=', parent.wbs_id), ('is_section', '=', False)]")

    @api.onchange('boq_line_id')
    def _onchange_boq_line(self):
        if self.boq_line_id:
            self.product_id = self.boq_line_id.product_id
            self.description = self.boq_line_id.description
            self.uom_id = self.boq_line_id.uom_id
            self.unit_price = self.boq_line_id.cost_rate


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    construction_wbs_id = fields.Many2one('construction.wbs', string='WBS Phase', index=True)
    construction_boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Item', index=True)
    construction_work_order_id = fields.Many2one('construction.work.order', string='Work Order', index=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    construction_wbs_id = fields.Many2one('construction.wbs', string='WBS Phase', index=True)
    construction_boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Item', index=True)
    construction_work_order_id = fields.Many2one('construction.work.order', string='Work Order', index=True)
