from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_compare, float_is_zero


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    construction_monthly_cost = fields.Monetary(
        string='Monthly Cost to Projects', currency_field='currency_id',
        help='What this person costs the company in a month -- salary plus '
             'insurance and allowances. This is the figure spread over the '
             'projects they work on.')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)


class ConstructionSalaryDistribution(models.Model):
    """Spread a month of staff cost over the projects they worked on.

    An engineer on three sites costs all three, and the share is a judgement
    the office makes each month. Without this the whole salary sits in
    overheads and no project ever carries the people who ran it.
    """
    _name = 'construction.salary.distribution'
    _description = 'Salary Distribution'
    _order = 'date_to desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Period', required=True, tracking=True)
    date_from = fields.Date(string='From', required=True, tracking=True)
    date_to = fields.Date(string='To', required=True, tracking=True)
    line_ids = fields.One2many(
        'construction.salary.distribution.line', 'distribution_id',
        string='Allocations')
    total_allocated = fields.Monetary(
        string='Total Allocated', currency_field='currency_id',
        compute='_compute_totals', store=True)
    employee_count = fields.Integer(
        string='Employees', compute='_compute_totals')
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    state = fields.Selection(
        [('draft', 'Draft'), ('posted', 'Posted'), ('cancelled', 'Cancelled')],
        string='Status', default='draft', required=True, tracking=True)
    note = fields.Text(string='Notes')

    @api.depends('line_ids.amount', 'line_ids.employee_id')
    def _compute_totals(self):
        for record in self:
            record.total_allocated = sum(record.line_ids.mapped('amount'))
            record.employee_count = len(record.line_ids.employee_id)

    @api.constrains('date_from', 'date_to')
    def _check_period(self):
        for record in self:
            if record.date_to < record.date_from:
                raise ValidationError(self.env._(
                    'The period ends before it starts.'))

    def action_post(self):
        """Book each allocation as a labour expense on its project."""
        Expense = self.env['construction.expense']
        for record in self:
            if record.state != 'draft':
                raise UserError(self.env._(
                    'Only a draft distribution can be posted.'))
            if not record.line_ids:
                raise UserError(self.env._(
                    'Add the allocations before posting.'))
            for line in record.line_ids:
                if float_is_zero(line.amount, precision_digits=2):
                    continue
                line.expense_id = Expense.create({
                    'name': self.env._(
                        '%(employee)s - %(period)s',
                        employee=line.employee_id.name, period=record.name),
                    'project_id': line.project_id.id,
                    'date': record.date_to,
                    'category': 'labour',
                    'amount': line.amount,
                    'description': self.env._(
                        '%(percent)s%% of the monthly cost of %(employee)s.',
                        percent=line.percent, employee=line.employee_id.name),
                    'state': 'approved',
                })
            record.state = 'posted'
        return True

    def action_reset(self):
        """Pull the expenses back so the shares can be corrected."""
        for record in self:
            expenses = record.line_ids.expense_id
            billed = expenses.filtered(lambda e: e.state != 'approved')
            if billed:
                raise UserError(self.env._(
                    'Some expenses from this distribution are no longer in '
                    'the approved state. Handle them by hand before '
                    'resetting.'))
            expenses.unlink()
            record.state = 'draft'
        return True

    def action_view_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Expenses'),
            'res_model': 'construction.expense',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.line_ids.expense_id.ids)],
        }


class ConstructionSalaryDistributionLine(models.Model):
    _name = 'construction.salary.distribution.line'
    _description = 'Salary Allocation'
    _order = 'employee_id, id'

    distribution_id = fields.Many2one(
        'construction.salary.distribution', string='Distribution',
        required=True, ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Employee', required=True, index=True)
    employee_cost = fields.Monetary(
        string='Monthly Cost', compute='_compute_employee_cost', store=True,
        readonly=False,
        help='Taken from the employee, and editable for a month that differs.')
    project_id = fields.Many2one(
        'construction.project', string='Project', required=True, index=True)
    percent = fields.Float(string='Share (%)', required=True, default=0.0)
    amount = fields.Monetary(
        string='Allocated', compute='_compute_amount', store=True)
    expense_id = fields.Many2one(
        'construction.expense', string='Expense', readonly=True, copy=False)
    currency_id = fields.Many2one(
        related='distribution_id.currency_id', string='Currency')

    @api.depends('employee_id')
    def _compute_employee_cost(self):
        for line in self:
            if line.employee_id:
                line.employee_cost = line.employee_id.construction_monthly_cost

    @api.depends('employee_cost', 'percent')
    def _compute_amount(self):
        for line in self:
            line.amount = line.employee_cost * line.percent / 100.0

    @api.constrains('percent', 'employee_id', 'distribution_id')
    def _check_share(self):
        """Nobody can be spread over more than the whole of themselves."""
        for line in self:
            if line.percent < 0:
                raise ValidationError(self.env._(
                    'A share cannot be negative.'))
            siblings = line.distribution_id.line_ids.filtered(
                lambda other: other.employee_id == line.employee_id)
            total = sum(siblings.mapped('percent'))
            if float_compare(total, 100.0, precision_digits=2) > 0:
                raise ValidationError(self.env._(
                    '%(employee)s is allocated %(total)s%% across the '
                    'projects in this period, which is more than a whole '
                    'month.',
                    employee=line.employee_id.name, total=total))
