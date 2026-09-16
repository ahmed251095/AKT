from odoo import api, fields, models
from odoo.exceptions import UserError


class ConstructionCustody(models.Model):
    """Cash handed to an employee to spend on the company's behalf.

    The site does not wait for a purchase order to buy a load of sand or pay a
    day labourer. Money goes out to a site engineer or a storekeeper, gets
    spent, and comes back as receipts. Until that round trip is recorded, the
    cash is neither in the bank nor on any project: it sits with a person.

    Settling is what turns the receipts into project cost -- each settlement
    line becomes an approved expense on the project it was spent for, which is
    what the project's actual cost reads.
    """
    _name = 'construction.custody'
    _description = 'Cash Custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    ref = fields.Char(string='Reference', readonly=True, default='New',
                      copy=False)
    employee_id = fields.Many2one(
        'hr.employee', string='Custody Holder', required=True, tracking=True,
        help='The person the cash is handed to. The custody stays open '
             'against this employee until it is settled.')
    project_id = fields.Many2one(
        'construction.project', string='Project', tracking=True,
        help='Left empty for an office custody spent across several sites; '
             'each settlement line still names the project it is charged to.')
    date = fields.Date(string='Issue Date', default=fields.Date.context_today,
                       required=True)
    purpose = fields.Text(string='Purpose')

    amount = fields.Monetary(
        string='Amount Issued', currency_field='currency_id', tracking=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    payment_id = fields.Many2one(
        'account.payment', string='Disbursement Payment', copy=False,
        help='The payment that handed the cash over, if it was recorded in '
             'accounting.')

    line_ids = fields.One2many(
        'construction.custody.line', 'custody_id', string='Settlement',
        copy=False)
    settled_amount = fields.Monetary(
        string='Settled', compute='_compute_amounts', store=True,
        currency_field='currency_id')
    returned_amount = fields.Monetary(
        string='Cash Returned', currency_field='currency_id', tracking=True,
        help='Unspent cash handed back.')
    balance = fields.Monetary(
        string='Balance with Holder', compute='_compute_amounts', store=True,
        currency_field='currency_id',
        help='Issued less what was settled and what came back. A negative '
             'figure is money the holder spent out of pocket.')
    line_count = fields.Integer(compute='_compute_amounts')
    posted_count = fields.Integer(compute='_compute_amounts')

    state = fields.Selection(
        [('draft', 'Draft'),
         ('open', 'With Holder'),
         ('settled', 'Settled'),
         ('cancelled', 'Cancelled')],
        string='Status', default='draft', tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ref', 'New') == 'New':
                vals['ref'] = self.env['ir.sequence'].next_by_code(
                    'construction.custody') or 'New'
        return super().create(vals_list)

    @api.depends('amount', 'returned_amount', 'line_ids.amount',
                 'line_ids.expense_id')
    def _compute_amounts(self):
        for custody in self:
            custody.settled_amount = sum(custody.line_ids.mapped('amount'))
            custody.balance = (custody.amount - custody.settled_amount
                               - custody.returned_amount)
            custody.line_count = len(custody.line_ids)
            custody.posted_count = len(
                custody.line_ids.filtered('expense_id'))

    @api.depends('ref', 'employee_id')
    def _compute_display_name(self):
        for custody in self:
            parts = [part for part in (custody.ref, custody.employee_id.name)
                     if part and part != 'New']
            custody.display_name = ' - '.join(parts) or self.env._('Custody')

    # ------------------------------------------------------------------
    # Flow
    # ------------------------------------------------------------------
    def action_open(self):
        """Hand the cash over."""
        for custody in self:
            if custody.state != 'draft':
                raise UserError(self.env._(
                    'Only a draft custody can be handed over.'))
            if custody.amount <= 0:
                raise UserError(self.env._(
                    'Set the amount handed to the holder first.'))
            custody.state = 'open'
        return True

    def action_post_settlement(self):
        """Turn the receipts into cost on the projects they were spent for.

        Only lines that have not been posted yet are taken, so the button can
        be pressed again as more receipts come in.
        """
        Expense = self.env['construction.expense']
        for custody in self:
            if custody.state != 'open':
                raise UserError(self.env._(
                    'Only a custody with the holder can be settled.'))
            pending = custody.line_ids.filtered(lambda l: not l.expense_id)
            if not pending:
                raise UserError(self.env._(
                    'Every settlement line has already been charged.'))
            for line in pending:
                line.expense_id = Expense.create({
                    'name': line.description,
                    'project_id': line.project_id.id,
                    'wbs_id': line.wbs_id.id,
                    'boq_line_id': line.boq_line_id.id,
                    'date': line.date,
                    'category': line.category,
                    'amount': line.amount,
                    'employee_id': custody.employee_id.user_id.id or False,
                    'description': line.description,
                    'state': 'approved',
                    'approved_by': self.env.user.id,
                })
            custody.message_post(body=self.env._(
                '%(count)s settlement lines charged to their projects.',
                count=len(pending)))
        return True

    def action_settle(self):
        """Close the custody once nothing is left with the holder."""
        for custody in self:
            if custody.state != 'open':
                raise UserError(self.env._(
                    'Only a custody with the holder can be closed.'))
            unposted = custody.line_ids.filtered(lambda l: not l.expense_id)
            if unposted:
                raise UserError(self.env._(
                    'Charge the settlement to the projects before closing '
                    'the custody.'))
            if custody.currency_id.compare_amounts(custody.balance, 0.0) > 0:
                raise UserError(self.env._(
                    'The holder still carries %(balance)s. Record the cash '
                    'returned or add the missing receipts.',
                    balance=custody.balance))
            custody.state = 'settled'
        return True

    def action_cancel(self):
        for custody in self:
            if custody.line_ids.filtered('expense_id'):
                raise UserError(self.env._(
                    'This custody has already been charged to a project and '
                    'cannot be cancelled.'))
            custody.state = 'cancelled'
        return True

    def action_reset(self):
        self.filtered(lambda c: c.state == 'cancelled').state = 'draft'
        return True

    def action_view_expenses(self):
        self.ensure_one()
        expenses = self.line_ids.expense_id
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Charged Expenses'),
            'res_model': 'construction.expense',
            'view_mode': 'list,form',
            'domain': [('id', 'in', expenses.ids)],
        }


class ConstructionCustodyLine(models.Model):
    """One receipt out of a custody, charged to one project."""
    _name = 'construction.custody.line'
    _description = 'Cash Custody Settlement Line'
    _order = 'date, id'

    custody_id = fields.Many2one(
        'construction.custody', string='Custody', required=True,
        ondelete='cascade', index=True)
    date = fields.Date(string='Date', default=fields.Date.context_today,
                       required=True)
    description = fields.Char(string='Description', required=True)
    category = fields.Selection(
        [('material', 'Materials'),
         ('labour', 'Labour'),
         ('equipment', 'Equipment'),
         ('subcontract', 'Subcontract'),
         ('overhead', 'Overhead'),
         ('other', 'Other')],
        string='Category', required=True, default='material')
    project_id = fields.Many2one(
        'construction.project', string='Project', required=True, index=True)
    wbs_id = fields.Many2one(
        'construction.wbs', string='WBS Phase',
        domain="[('project_id', '=', project_id)]")
    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item',
        domain="[('boq_id.project_id', '=', project_id), "
               "('is_section', '=', False)]")
    amount = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one(
        related='custody_id.currency_id', string='Currency')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'construction_custody_line_attachment_rel',
        'line_id', 'attachment_id', string='Receipt')
    expense_id = fields.Many2one(
        'construction.expense', string='Charged Expense', readonly=True,
        copy=False, ondelete='set null')
    is_posted = fields.Boolean(
        string='Charged', compute='_compute_is_posted', store=True)

    @api.depends('expense_id')
    def _compute_is_posted(self):
        for line in self:
            line.is_posted = bool(line.expense_id)

    @api.onchange('custody_id')
    def _onchange_custody(self):
        """Default the line to the custody's project, when it has one."""
        if self.custody_id.project_id and not self.project_id:
            self.project_id = self.custody_id.project_id
