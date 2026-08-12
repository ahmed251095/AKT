# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class ConstructionMaterialRequisition(models.Model):
    _name = 'construction.material.requisition'
    _description = 'Material Requisition'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_requested desc, id desc'

    name = fields.Char(required=True, tracking=True)
    ref = fields.Char(readonly=True, default='New', copy=False)
    project_id = fields.Many2one('construction.project', required=True, tracking=True)
    work_order_id = fields.Many2one('construction.work.order', domain="[('project_id','=',project_id)]")
    vendor_id = fields.Many2one('res.partner', string='Preferred Vendor', domain="[('supplier_rank', '>', 0)]")
    date_requested = fields.Date(default=fields.Date.today)
    date_required = fields.Date()
    requested_by = fields.Many2one('res.users', default=lambda self: self.env.user)
    approved_by = fields.Many2one('res.users', readonly=True)
    purchase_order_ids = fields.One2many('purchase.order', 'construction_requisition_id', string='RFQs / Purchase Orders')
    purchase_order_count = fields.Integer(compute='_compute_purchase_order_count')
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'), ('approved', 'Approved'),
        ('rfq', 'RFQ Created'), ('ordered', 'Ordered'), ('received', 'Received'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    line_ids = fields.One2many('construction.material.requisition.line', 'requisition_id', copy=True)
    total_estimated_cost = fields.Monetary(compute='_compute_total', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='project_id.currency_id', store=True)
    notes = fields.Text()

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('construction.material.requisition') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids.subtotal')
    def _compute_total(self):
        for rec in self:
            rec.total_estimated_cost = sum(rec.line_ids.mapped('subtotal'))

    @api.depends('purchase_order_ids')
    def _compute_purchase_order_count(self):
        for rec in self:
            rec.purchase_order_count = len(rec.purchase_order_ids)

    @api.constrains('date_required', 'date_requested')
    def _check_dates(self):
        for rec in self:
            if rec.date_required and rec.date_requested and rec.date_required < rec.date_requested:
                raise ValidationError(_('Required date cannot be earlier than request date.'))

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Add at least one material line before submitting.'))
        self.write({'state': 'submitted'})

    def action_approve(self):
        self.write({'state': 'approved', 'approved_by': self.env.user.id})

    def action_create_rfq(self):
        self.ensure_one()
        if self.state not in ('approved', 'rfq'):
            raise UserError(_('The requisition must be approved before creating an RFQ.'))
        if not self.vendor_id:
            raise UserError(_('Select a preferred vendor first.'))
        lines = self.line_ids.filtered(lambda l: l.product_id and (l.qty_approved or l.qty_requested) > 0)
        if not lines:
            raise UserError(_('No approved product quantities are available.'))
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor_id.id,
            'origin': self.ref,
            'construction_project_id': self.project_id.id,
            'construction_requisition_id': self.id,
            'date_order': fields.Datetime.now(),
            'order_line': [Command.create({
                'product_id': line.product_id.id,
                'name': line.description or line.product_id.display_name,
                'product_qty': line.qty_approved or line.qty_requested,
                'product_uom_id': line.uom_id.id or line.product_id.uom_id.id,
                'price_unit': line.unit_price,
                'date_planned': fields.Datetime.now(),
                'analytic_distribution': self.project_id._get_analytic_distribution(),
                'construction_wbs_id': self.wbs_id.id,
                'construction_boq_line_id': line.boq_line_id.id,
                'construction_work_order_id': self.work_order_id.id,
            }) for line in lines],
        })
        self.state = 'rfq'
        return {'type': 'ir.actions.act_window', 'res_model': 'purchase.order', 'res_id': po.id, 'view_mode': 'form'}

    def action_view_purchase_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': _('RFQs / Purchase Orders'),
            'res_model': 'purchase.order', 'view_mode': 'list,form',
            'domain': [('construction_requisition_id', '=', self.id)],
            'context': {'default_construction_project_id': self.project_id.id,
                        'default_construction_requisition_id': self.id},
        }

    def action_receive(self):
        self.state = 'received'

    def action_cancel(self):
        self.state = 'cancelled'

    def action_reset(self):
        self.state = 'draft'


class ConstructionMaterialRequisitionLine(models.Model):
    _name = 'construction.material.requisition.line'
    _description = 'Material Requisition Line'

    requisition_id = fields.Many2one('construction.material.requisition', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Material', required=True)
    description = fields.Char(required=True)
    uom_id = fields.Many2one('uom.uom', string='UOM', required=True)
    qty_requested = fields.Float(digits=(12, 3), default=1.0)
    qty_approved = fields.Float(digits=(12, 3))
    qty_received = fields.Float(digits=(12, 3))
    unit_price = fields.Monetary(currency_field='currency_id')
    subtotal = fields.Monetary(compute='_compute_subtotal', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='requisition_id.currency_id', store=True)

    @api.depends('qty_requested', 'unit_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = rec.qty_requested * rec.unit_price

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.description = self.product_id.display_name
            self.uom_id = self.product_id.uom_id
            self.unit_price = self.product_id.standard_price
