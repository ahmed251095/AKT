# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ConstructionProject(models.Model):
    _name = 'construction.project'
    _description = 'Construction Project'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(required=True, tracking=True)
    ref = fields.Char('Project Code', readonly=True, default='New')
    client_id = fields.Many2one('res.partner', string='Client', tracking=True)
    site_manager_id = fields.Many2one('res.users', string='Site Manager')
    project_manager_id = fields.Many2one('res.users', string='Project Manager')
    start_date = fields.Date()
    end_date = fields.Date()
    contract_value = fields.Monetary(currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    location = fields.Char()
    description = fields.Text()
    analytic_account_id = fields.Many2one('account.analytic.account', string='Project Analytic Account', tracking=True)
    purchase_order_count = fields.Integer(compute='_compute_accounting_counts')
    vendor_bill_count = fields.Integer(compute='_compute_accounting_counts')
    customer_invoice_count = fields.Integer(compute='_compute_accounting_counts')
    purchase_total = fields.Monetary(compute='_compute_accounting_counts', currency_field='currency_id')
    invoiced_revenue = fields.Monetary(compute='_compute_accounting_counts', currency_field='currency_id')
    committed_cost = fields.Monetary(compute='_compute_accounting_counts', currency_field='currency_id')
    actual_cost = fields.Monetary(compute='_compute_accounting_counts', currency_field='currency_id')
    gross_margin = fields.Monetary(compute='_compute_accounting_counts', currency_field='currency_id')

    # Smart button counts
    boq_count = fields.Integer(compute='_compute_counts')
    wbs_count = fields.Integer(compute='_compute_counts')
    work_order_count = fields.Integer(compute='_compute_counts')
    material_requisition_count = fields.Integer(compute='_compute_counts')
    subcontract_count = fields.Integer(compute='_compute_counts')
    billing_count = fields.Integer(compute='_compute_counts')
    quality_check_count = fields.Integer(compute='_compute_counts')
    expense_count = fields.Integer(compute='_compute_counts')

    total_expenses = fields.Monetary(compute='_compute_financials', currency_field='currency_id')
    progress = fields.Float(compute='_compute_progress', string='Overall Progress %')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('construction.project') or 'New'
        return super().create(vals_list)

    def _compute_counts(self):
        for rec in self:
            rec.boq_count = self.env['construction.boq'].search_count([('project_id', '=', rec.id)])
            rec.wbs_count = self.env['construction.wbs'].search_count([('project_id', '=', rec.id)])
            rec.work_order_count = self.env['construction.work.order'].search_count([('project_id', '=', rec.id)])
            rec.material_requisition_count = self.env['construction.material.requisition'].search_count([('project_id', '=', rec.id)])
            rec.subcontract_count = self.env['construction.subcontract'].search_count([('project_id', '=', rec.id)])
            rec.billing_count = self.env['construction.ra.billing'].search_count([('project_id', '=', rec.id)])
            rec.quality_check_count = self.env['construction.quality.check'].search_count([('project_id', '=', rec.id)])
            rec.expense_count = self.env['construction.expense'].search_count([('project_id', '=', rec.id)])

    def _compute_financials(self):
        """Compute approved direct project expenses shown separately in the summary."""
        Expense = self.env['construction.expense']
        for rec in self:
            expenses = Expense.search([
                ('project_id', '=', rec.id),
                ('state', '=', 'approved'),
            ])
            rec.total_expenses = sum(expenses.mapped('amount'))

    def _compute_progress(self):
        for rec in self:
            wbs = self.env['construction.wbs'].search([('project_id', '=', rec.id)])
            rec.progress = sum(wbs.mapped('progress')) / len(wbs) if wbs else 0.0


    def _get_analytic_distribution(self):
        self.ensure_one()
        return {str(self.analytic_account_id.id): 100.0} if self.analytic_account_id else {}

    def _compute_accounting_counts(self):
        """Compute the project's purchasing, accounting and total-cost indicators.

        Actual Cost follows the construction-management definition requested for
        this module: confirmed direct purchases + approved construction expenses
        + active/completed subcontract values.

        Purchase orders generated from a subcontract are excluded from the
        purchases component because their value is already included through the
        subcontract itself. This prevents the same subcontract cost being counted
        twice.
        """
        Purchase = self.env['purchase.order']
        Move = self.env['account.move']
        Expense = self.env['construction.expense']
        Subcontract = self.env['construction.subcontract']

        for rec in self:
            purchase_domain = [
                ('construction_project_id', '=', rec.id),
                ('state', 'in', ('purchase', 'done')),
            ]
            purchases = Purchase.search(purchase_domain)
            direct_purchases = purchases.filtered(lambda po: not po.construction_subcontract_id)

            approved_expenses = Expense.search([
                ('project_id', '=', rec.id),
                ('state', '=', 'approved'),
            ])
            active_subcontracts = Subcontract.search([
                ('project_id', '=', rec.id),
                ('state', 'in', ('active', 'completed')),
            ])

            vendor_bills = Move.search([
                ('construction_project_id', '=', rec.id),
                ('move_type', 'in', ('in_invoice', 'in_refund')),
                ('state', '=', 'posted'),
            ])
            customer_invoices = Move.search([
                ('construction_project_id', '=', rec.id),
                ('move_type', 'in', ('out_invoice', 'out_refund')),
                ('state', '=', 'posted'),
            ])

            purchase_cost = sum(direct_purchases.mapped('amount_total'))
            expense_cost = sum(approved_expenses.mapped('amount'))
            subcontract_cost = sum(active_subcontracts.mapped('contract_value'))

            rec.purchase_order_count = Purchase.search_count([
                ('construction_project_id', '=', rec.id),
            ])
            rec.vendor_bill_count = len(vendor_bills)
            rec.customer_invoice_count = len(customer_invoices)
            rec.purchase_total = sum(purchases.mapped('amount_total'))
            rec.committed_cost = rec.purchase_total
            rec.actual_cost = purchase_cost + expense_cost + subcontract_cost
            rec.invoiced_revenue = sum(customer_invoices.mapped('amount_total_signed'))
            rec.gross_margin = rec.invoiced_revenue - rec.actual_cost

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Purchase Orders', 'res_model': 'purchase.order',
                'view_mode': 'list,form', 'domain': [('construction_project_id', '=', self.id)],
                'context': {'default_construction_project_id': self.id}}

    def action_view_vendor_bills(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Vendor Bills', 'res_model': 'account.move',
                'view_mode': 'list,form',
                'domain': [('construction_project_id', '=', self.id), ('move_type', 'in', ('in_invoice', 'in_refund'))],
                'context': {'default_move_type': 'in_invoice', 'default_construction_project_id': self.id}}

    def action_view_customer_invoices(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': 'Customer Invoices', 'res_model': 'account.move',
                'view_mode': 'list,form',
                'domain': [('construction_project_id', '=', self.id), ('move_type', 'in', ('out_invoice', 'out_refund'))],
                'context': {'default_move_type': 'out_invoice', 'default_construction_project_id': self.id}}

    def action_activate(self):
        self.state = 'active'

    def action_hold(self):
        self.state = 'on_hold'

    def action_complete(self):
        self.state = 'completed'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset(self):
        self.state = 'draft'

    def action_view_boq(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'BOQ',
            'res_model': 'construction.boq',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_wbs(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'WBS Phases',
            'res_model': 'construction.wbs',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_work_orders(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Work Orders',
            'res_model': 'construction.work.order',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_requisitions(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Material Requisitions',
            'res_model': 'construction.material.requisition',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_subcontracts(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Subcontracts',
            'res_model': 'construction.subcontract',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_billing(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'RA Billing',
            'res_model': 'construction.ra.billing',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_quality(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Quality Checks',
            'res_model': 'construction.quality.check',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_expenses(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Expenses',
            'res_model': 'construction.expense',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
