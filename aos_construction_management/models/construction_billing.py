# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class ConstructionRABilling(models.Model):
    _name = 'construction.ra.billing'
    _description = 'Construction Payment Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'billing_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    ref = fields.Char(readonly=True, default='New', copy=False)
    ra_number = fields.Integer('Certificate No.', readonly=True)
    billing_type = fields.Selection([('customer', 'Customer Certificate'), ('subcontractor', 'Subcontractor Certificate')],
                                    default='customer', required=True, tracking=True)
    project_id = fields.Many2one('construction.project', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer / Subcontractor', required=True)
    subcontract_id = fields.Many2one('construction.subcontract', domain="[('project_id','=',project_id)]")
    purchase_order_id = fields.Many2one('purchase.order', string='Related Purchase Order')
    move_id = fields.Many2one('account.move', string='Invoice / Vendor Bill', readonly=True, copy=False)
    billing_date = fields.Date(default=fields.Date.today)
    billing_period_start = fields.Date()
    billing_period_end = fields.Date()
    line_ids = fields.One2many('construction.ra.billing.line', 'billing_id', copy=True)
    total_amount = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    previous_billed = fields.Monetary(compute='_compute_previous', store=True, currency_field='currency_id')
    net_amount = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    retention_percent = fields.Float('Retention %', default=5.0)
    retention_amount = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    advance_recovery = fields.Monetary('Advance Recovery', currency_field='currency_id')
    other_deductions = fields.Monetary('Other Deductions', currency_field='currency_id')
    tax_ids = fields.Many2many('account.tax', string='Taxes')
    net_payable = fields.Monetary(compute='_compute_amounts', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'),
        ('invoiced', 'Invoiced/Billed'), ('paid', 'Paid'), ('cancelled', 'Cancelled')
    ], default='draft', tracking=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('construction.ra.billing') or 'New'
            if vals.get('project_id') and not vals.get('partner_id'):
                project = self.env['construction.project'].browse(vals['project_id'])
                vals['partner_id'] = project.client_id.id
        return super().create(vals_list)

    @api.depends('project_id', 'billing_type', 'subcontract_id', 'billing_date')
    def _compute_previous(self):
        for rec in self:
            domain = [('project_id', '=', rec.project_id.id), ('id', '!=', rec.id),
                      ('state', 'in', ('approved', 'invoiced', 'paid')),
                      ('billing_type', '=', rec.billing_type)]
            if rec.subcontract_id:
                domain.append(('subcontract_id', '=', rec.subcontract_id.id))
            rec.previous_billed = sum(self.search(domain).mapped('net_amount'))

    @api.depends('line_ids.amount', 'previous_billed', 'retention_percent', 'advance_recovery', 'other_deductions')
    def _compute_amounts(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('amount'))
            rec.net_amount = rec.total_amount
            rec.retention_amount = rec.net_amount * rec.retention_percent / 100
            rec.net_payable = rec.net_amount - rec.retention_amount - rec.advance_recovery - rec.other_deductions

    @api.onchange('project_id', 'billing_type', 'subcontract_id')
    def _onchange_parties(self):
        if self.billing_type == 'customer' and self.project_id:
            self.partner_id = self.project_id.client_id
        elif self.billing_type == 'subcontractor' and self.subcontract_id:
            self.partner_id = self.subcontract_id.subcontractor_id
            self.purchase_order_id = self.subcontract_id.purchase_order_id
            self.retention_percent = self.subcontract_id.retention_percent

    @api.constrains('billing_period_start', 'billing_period_end', 'net_payable')
    def _check_certificate(self):
        for rec in self:
            if rec.billing_period_start and rec.billing_period_end and rec.billing_period_end < rec.billing_period_start:
                raise ValidationError(_('Billing period end cannot be earlier than start.'))
            if rec.net_payable < 0:
                raise ValidationError(_('Net payable cannot be negative.'))

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Add certificate lines before submitting.'))
        self.write({'state': 'submitted'})

    def action_approve(self): self.write({'state': 'approved'})

    def action_create_account_move(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Approve the certificate first.'))
        if self.move_id:
            return self.action_view_account_move()
        move_type = 'out_invoice' if self.billing_type == 'customer' else 'in_invoice'
        invoice_lines = []
        analytic_distribution = self.project_id._get_analytic_distribution()
        for line in self.line_ids.filtered(lambda l: l.amount):
            invoice_lines.append(Command.create({
                'product_id': line.product_id.id,
                'name': line.boq_line_description,
                'quantity': line.qty_current or 1.0,
                'price_unit': line.unit_rate if line.qty_current else line.amount,
                'tax_ids': [Command.set(self.tax_ids.ids)],
                'analytic_distribution': analytic_distribution,
                'construction_wbs_id': line.wbs_id.id,
                'construction_boq_line_id': line.boq_line_id.id,
                'construction_work_order_id': line.work_order_id.id,
            }))
        # Deductions are represented as negative commercial lines, preserving the accounting audit trail.
        deductions = [
            (_('Retention Deduction'), self.retention_amount),
            (_('Advance Recovery'), self.advance_recovery),
            (_('Other Deductions'), self.other_deductions),
        ]
        for label, amount in deductions:
            if amount:
                invoice_lines.append(Command.create({
                    'product_id': self.line_ids[0].product_id.id,
                    'name': label, 'quantity': 1.0, 'price_unit': -amount,
                    'analytic_distribution': analytic_distribution,
                }))
        move = self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.partner_id.id,
            'invoice_date': self.billing_date,
            'invoice_origin': self.ref,
            'currency_id': self.currency_id.id,
            'construction_project_id': self.project_id.id,
            'construction_billing_id': self.id,
            'construction_subcontract_id': self.subcontract_id.id,
            'invoice_payment_term_id': self.subcontract_id.payment_term_id.id if self.subcontract_id else False,
            'invoice_line_ids': invoice_lines,
        })
        self.write({'move_id': move.id, 'state': 'invoiced'})
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': move.id, 'view_mode': 'form'}

    def action_view_account_move(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'res_model': 'account.move', 'res_id': self.move_id.id, 'view_mode': 'form'}

    def action_mark_paid(self):
        self.write({'state': 'paid'})

    def action_cancel(self): self.write({'state': 'cancelled'})
    def action_reset(self): self.write({'state': 'draft'})


class ConstructionRABillingLine(models.Model):
    _name = 'construction.ra.billing.line'
    _description = 'Certificate Line'

    billing_id = fields.Many2one('construction.ra.billing', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product / Service', required=True)
    boq_line_id = fields.Many2one('construction.boq.line', string='BOQ Item', domain="[('boq_id.project_id', '=', parent.project_id), ('is_section', '=', False)]")
    wbs_id = fields.Many2one('construction.wbs', string='WBS Phase', domain="[('project_id', '=', parent.project_id)]")
    work_order_id = fields.Many2one('construction.work.order', string='Work Order', domain="[('project_id', '=', parent.project_id)]")
    boq_line_description = fields.Char('Description', required=True)
    work_type = fields.Selection([
        ('civil', 'Civil'), ('structural', 'Structural'), ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing/MEP'), ('finishing', 'Finishing'),
        ('external', 'External Works'), ('other', 'Other'),
    ], default='civil')
    uom_id = fields.Many2one('uom.uom')
    boq_qty = fields.Float('Contract Qty', digits=(12, 3))
    qty_previous = fields.Float('Prev. Qty', digits=(12, 3))
    qty_current = fields.Float('Current Qty', digits=(12, 3))
    qty_cumulative = fields.Float(compute='_compute_cumulative', store=True, digits=(12, 3))
    qty_remaining = fields.Float(compute='_compute_cumulative', store=True, digits=(12, 3))
    progress_percent = fields.Float(compute='_compute_cumulative', store=True)
    unit_rate = fields.Monetary(currency_field='currency_id')
    amount = fields.Monetary(compute='_compute_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='billing_id.currency_id', store=True)

    @api.depends('qty_previous', 'qty_current', 'boq_qty')
    def _compute_cumulative(self):
        for rec in self:
            rec.qty_cumulative = rec.qty_previous + rec.qty_current
            rec.progress_percent = rec.qty_cumulative / rec.boq_qty * 100 if rec.boq_qty else 0
            rec.qty_remaining = max(rec.boq_qty - rec.qty_cumulative, 0.0)

    @api.onchange('boq_line_id')
    def _onchange_boq_line_id(self):
        if not self.boq_line_id:
            return
        line = self.boq_line_id
        self.product_id = line.product_id
        self.boq_line_description = line.description
        self.work_type = line.work_type
        self.uom_id = line.uom_id
        self.boq_qty = line.qty
        self.unit_rate = line.unit_rate if self.billing_id.billing_type == 'customer' else (line.cost_rate or line.unit_rate)
        self.wbs_id = line.wbs_id
        domain = [
            ('boq_line_id', '=', line.id),
            ('billing_id.id', '!=', self.billing_id.id or 0),
            ('billing_id.state', 'in', ('approved', 'invoiced', 'paid')),
            ('billing_id.billing_type', '=', self.billing_id.billing_type),
        ]
        if self.billing_id.billing_type == 'subcontractor' and self.billing_id.subcontract_id:
            domain.append(('billing_id.subcontract_id', '=', self.billing_id.subcontract_id.id))
        previous = self.env['construction.ra.billing.line'].search(domain)
        self.qty_previous = sum(previous.mapped('qty_current'))

    @api.depends('qty_current', 'unit_rate')
    def _compute_amount(self):
        for rec in self:
            rec.amount = rec.qty_current * rec.unit_rate

    @api.constrains('qty_cumulative', 'boq_qty')
    def _check_quantity(self):
        for rec in self:
            if rec.boq_qty and rec.qty_cumulative > rec.boq_qty:
                raise ValidationError(_('Cumulative quantity cannot exceed contract quantity.'))

    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.boq_line_description = self.product_id.display_name
            self.uom_id = self.product_id.uom_id


class ConstructionProgressBilling(models.Model):
    _name = 'construction.progress.billing'
    _description = 'Progress Billing'
    _inherit = ['mail.thread']

    name = fields.Char(required=True)
    ref = fields.Char(readonly=True, default='New')
    project_id = fields.Many2one('construction.project', required=True)
    billing_date = fields.Date(default=fields.Date.today)
    contract_value = fields.Monetary(related='project_id.contract_value', currency_field='currency_id')
    percent_complete = fields.Float('% Complete')
    amount_earned = fields.Monetary(compute='_compute_earned', store=True, currency_field='currency_id')
    amount_previously_billed = fields.Monetary(currency_field='currency_id')
    amount_this_period = fields.Monetary(compute='_compute_this_period', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id')
    state = fields.Selection([('draft', 'Draft'), ('approved', 'Approved'), ('invoiced', 'Invoiced')], default='draft', tracking=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('construction.progress.billing') or 'New'
        return super().create(vals_list)

    @api.depends('contract_value', 'percent_complete')
    def _compute_earned(self):
        for rec in self: rec.amount_earned = rec.contract_value * rec.percent_complete / 100

    @api.depends('amount_earned', 'amount_previously_billed')
    def _compute_this_period(self):
        for rec in self: rec.amount_this_period = rec.amount_earned - rec.amount_previously_billed

    def action_approve(self): self.write({'state': 'approved'})
    def action_invoice(self): self.write({'state': 'invoiced'})
    def action_reset(self): self.write({'state': 'draft'})
