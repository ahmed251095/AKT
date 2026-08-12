# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class ConstructionTender(models.Model):
    _name = 'construction.tender'
    _description = 'Tender / Bid'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submission_deadline, id desc'

    name = fields.Char(required=True, tracking=True)
    ref = fields.Char('Tender No.', readonly=True, default='New', copy=False)
    client_id = fields.Many2one('res.partner', string='Tendering Authority / Client', tracking=True)
    tender_type = fields.Selection([
        ('public', 'Public'),
        ('private', 'Private'),
        ('negotiated', 'Negotiated'),
    ], default='private', tracking=True)
    responsible_id = fields.Many2one('res.users', string='Tender Engineer',
                                      default=lambda self: self.env.user)
    issue_date = fields.Date('Issue Date')
    submission_deadline = fields.Datetime('Submission Deadline', tracking=True)
    location = fields.Char()
    scope_of_work = fields.Text()
    notes = fields.Text()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Preparing Bid'),
        ('submitted', 'Submitted'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
    ], default='draft', tracking=True)
    loss_reason = fields.Text()

    line_ids = fields.One2many('construction.tender.line', 'tender_id', string='Tender Items', copy=True)
    estimated_value = fields.Monetary(
        'Estimated Bid Value', compute='_compute_amounts', store=True, currency_field='currency_id')
    estimated_cost = fields.Monetary(
        compute='_compute_amounts', store=True, currency_field='currency_id')
    estimated_margin = fields.Monetary(
        compute='_compute_amounts', store=True, currency_field='currency_id')
    estimated_margin_percent = fields.Float(compute='_compute_amounts', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    project_id = fields.Many2one('construction.project', string='Awarded Project', readonly=True, copy=False)
    project_count = fields.Integer(compute='_compute_project_count')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code('construction.tender') or 'New'
        return super().create(vals_list)

    @api.depends('line_ids.amount', 'line_ids.budget_cost')
    def _compute_amounts(self):
        for rec in self:
            rec.estimated_value = sum(rec.line_ids.mapped('amount'))
            rec.estimated_cost = sum(rec.line_ids.mapped('budget_cost'))
            rec.estimated_margin = rec.estimated_value - rec.estimated_cost
            rec.estimated_margin_percent = (
                rec.estimated_margin / rec.estimated_value * 100.0) if rec.estimated_value else 0.0

    def _compute_project_count(self):
        for rec in self:
            rec.project_count = 1 if rec.project_id else 0

    @api.constrains('submission_deadline', 'issue_date')
    def _check_dates(self):
        for rec in self:
            if rec.issue_date and rec.submission_deadline and rec.submission_deadline.date() < rec.issue_date:
                raise ValidationError(_('Submission deadline cannot be earlier than the issue date.'))

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_submit(self):
        for rec in self:
            if not rec.line_ids:
                raise UserError(_('Add at least one priced item before submitting the tender.'))
        self.write({'state': 'submitted'})

    def action_lose(self):
        self.write({'state': 'lost'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_reset(self):
        self.write({'state': 'draft'})

    def action_mark_won(self):
        """Win the tender and convert it into a Construction Project + initial BOQ."""
        self.ensure_one()
        if self.project_id:
            raise UserError(_('This tender has already been converted into a project.'))
        if not self.line_ids:
            raise UserError(_('Add tender items before converting to a project.'))

        project = self.env['construction.project'].create({
            'name': self.name,
            'client_id': self.client_id.id,
            'project_manager_id': self.responsible_id.id,
            'contract_value': self.estimated_value,
            'currency_id': self.currency_id.id,
            'location': self.location,
            'description': self.scope_of_work,
            'tender_id': self.id,
        })

        boq = self.env['construction.boq'].create({
            'name': _('%s - Initial BOQ') % self.name,
            'project_id': project.id,
            'notes': self.notes,
            'line_ids': [
                Command.create({
                    'sequence': line.sequence,
                    'item_no': line.item_no,
                    'description': line.description,
                    'is_section': line.is_section,
                    'work_type': line.work_type,
                    'product_id': line.product_id.id,
                    'uom_id': line.uom_id.id,
                    'qty': line.qty,
                    'unit_rate': line.unit_rate,
                    'cost_rate': line.cost_rate,
                }) for line in self.line_ids
            ],
        })

        self.write({'state': 'won', 'project_id': project.id})
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project'),
            'res_model': 'construction.project',
            'res_id': project.id,
            'view_mode': 'form',
            'context': {'boq_created_id': boq.id},
        }

    def action_view_project(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Project'),
            'res_model': 'construction.project',
            'res_id': self.project_id.id,
            'view_mode': 'form',
        }


class ConstructionTenderLine(models.Model):
    _name = 'construction.tender.line'
    _description = 'Tender Item'
    _order = 'sequence, id'

    tender_id = fields.Many2one('construction.tender', ondelete='cascade')
    sequence = fields.Integer(default=10)
    item_no = fields.Char('Item No.')
    description = fields.Char(required=True)
    work_type = fields.Selection([
        ('civil', 'Civil'),
        ('structural', 'Structural'),
        ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing/MEP'),
        ('finishing', 'Finishing'),
        ('external', 'External Works'),
        ('other', 'Other'),
    ], default='civil')
    product_id = fields.Many2one('product.product', string='Product / Service')
    uom_id = fields.Many2one('uom.uom', string='UOM')
    qty = fields.Float(digits=(12, 3))
    unit_rate = fields.Monetary('Bid Unit Rate', currency_field='currency_id')
    cost_rate = fields.Monetary('Estimated Cost Rate', currency_field='currency_id')
    amount = fields.Monetary(compute='_compute_amount', store=True, currency_field='currency_id')
    budget_cost = fields.Monetary(compute='_compute_amount', store=True, currency_field='currency_id')
    margin = fields.Monetary(compute='_compute_amount', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', related='tender_id.currency_id')
    is_section = fields.Boolean('Section Header')

    @api.depends('qty', 'unit_rate', 'cost_rate', 'is_section')
    def _compute_amount(self):
        for rec in self:
            if rec.is_section:
                rec.amount = rec.budget_cost = rec.margin = 0.0
                continue
            rec.amount = rec.qty * rec.unit_rate
            rec.budget_cost = rec.qty * rec.cost_rate
            rec.margin = rec.amount - rec.budget_cost
