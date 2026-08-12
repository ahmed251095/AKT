# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class ConstructionSubcontract(models.Model):
    _name = 'construction.subcontract'
    _description = 'Subcontract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'start_date desc, id desc'

    name = fields.Char(required=True, tracking=True)
    ref = fields.Char(readonly=True, default='New', copy=False)
    project_id = fields.Many2one('construction.project', required=True, tracking=True)
    wbs_id = fields.Many2one('construction.wbs', domain="[('project_id','=',project_id)]")
    subcontractor_id = fields.Many2one('res.partner', string='Subcontractor', required=True, tracking=True)
    product_id = fields.Many2one('product.product', string='Service Product', domain="[('type', '=', 'service')]")
    scope_of_work = fields.Text(required=True)
    contract_value = fields.Monetary(currency_field='currency_id', tracking=True)
    certified_amount = fields.Monetary(compute='_compute_financials', currency_field='currency_id')
    billed_amount = fields.Monetary(compute='_compute_financials', currency_field='currency_id')
    paid_amount = fields.Monetary(compute='_compute_financials', currency_field='currency_id')
    amount_remaining = fields.Monetary(compute='_compute_financials', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True)
    start_date = fields.Date()
    end_date = fields.Date()
    purchase_order_id = fields.Many2one('purchase.order', string='Subcontract Purchase Order', readonly=True, copy=False)
    billing_ids = fields.One2many('construction.ra.billing', 'subcontract_id', string='Certificates')
    billing_count = fields.Integer(compute='_compute_financials')
    state = fields.Selection([
        ('draft', 'Draft'), ('active', 'Active'), ('completed', 'Completed'),
        ('terminated', 'Terminated'),
    ], default='draft', tracking=True)
    payment_terms = fields.Text()
    payment_term_id = fields.Many2one('account.payment.term', string='Vendor Payment Terms')
    retention_percent = fields.Float('Retention %', default=10.0)
    advance_percent = fields.Float('Advance %')
    retention_amount = fields.Monetary(compute='_compute_retention', currency_field='currency_id')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('construction.subcontract') or 'New'
        return super().create(vals_list)

    @api.depends('billing_ids.state', 'billing_ids.net_payable', 'billing_ids.move_id.payment_state',
                 'billing_ids.move_id.amount_total', 'contract_value')
    def _compute_financials(self):
        for rec in self:
            approved = rec.billing_ids.filtered(lambda b: b.state in ('approved', 'invoiced', 'paid'))
            rec.certified_amount = sum(approved.mapped('net_amount'))
            posted_moves = approved.mapped('move_id').filtered(lambda m: m.state == 'posted')
            rec.billed_amount = sum(posted_moves.mapped('amount_total'))
            rec.paid_amount = sum(posted_moves.filtered(lambda m: m.payment_state == 'paid').mapped('amount_total'))
            rec.amount_remaining = rec.contract_value - rec.certified_amount
            rec.billing_count = len(rec.billing_ids)

    @api.depends('contract_value', 'retention_percent')
    def _compute_retention(self):
        for rec in self:
            rec.retention_amount = rec.contract_value * rec.retention_percent / 100

    @api.constrains('start_date', 'end_date', 'contract_value')
    def _check_values(self):
        for rec in self:
            if rec.end_date and rec.start_date and rec.end_date < rec.start_date:
                raise ValidationError(_('End date cannot be earlier than start date.'))
            if rec.contract_value < 0:
                raise ValidationError(_('Contract value cannot be negative.'))

    def action_create_purchase_order(self):
        self.ensure_one()
        if self.purchase_order_id:
            return {'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'res_id': self.purchase_order_id.id, 'view_mode': 'form'}
        if not self.product_id:
            raise UserError(_('Select a service product for the subcontract.'))
        po = self.env['purchase.order'].create({
            'partner_id': self.subcontractor_id.id,
            'origin': self.ref,
            'construction_project_id': self.project_id.id,
            'construction_subcontract_id': self.id,
            'payment_term_id': self.payment_term_id.id,
            'order_line': [Command.create({
                'product_id': self.product_id.id,
                'name': self.scope_of_work or self.name,
                'product_qty': 1.0,
                'product_uom_id': self.product_id.uom_id.id,
                'price_unit': self.contract_value,
                'date_planned': fields.Datetime.now(),
                'analytic_distribution': self.project_id._get_analytic_distribution(),
            })],
        })
        self.purchase_order_id = po
        return {'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'res_id': po.id, 'view_mode': 'form'}

    def action_create_certificate(self):
        self.ensure_one()
        certificate = self.env['construction.ra.billing'].create({
            'name': _('%s Certificate') % self.name,
            'project_id': self.project_id.id,
            'billing_type': 'subcontractor',
            'partner_id': self.subcontractor_id.id,
            'subcontract_id': self.id,
            'purchase_order_id': self.purchase_order_id.id,
            'retention_percent': self.retention_percent,
        })
        return {'type': 'ir.actions.act_window', 'res_model': 'construction.ra.billing', 'res_id': certificate.id, 'view_mode': 'form'}

    def action_view_certificates(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': _('Subcontractor Certificates'),
                'res_model': 'construction.ra.billing', 'view_mode': 'list,form',
                'domain': [('subcontract_id', '=', self.id)],
                'context': {'default_project_id': self.project_id.id,
                            'default_billing_type': 'subcontractor',
                            'default_partner_id': self.subcontractor_id.id,
                            'default_subcontract_id': self.id}}

    def action_activate(self): self.write({'state': 'active'})
    def action_complete(self): self.write({'state': 'completed'})
    def action_terminate(self): self.write({'state': 'terminated'})
    def action_reset(self): self.write({'state': 'draft'})
