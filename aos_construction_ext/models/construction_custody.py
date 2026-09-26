from odoo import api, fields, models
from odoo.exceptions import UserError

from .approval_lock import refuse, typed_fields


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

    # Grows with every disbursement. Kept writable so a custody run without
    # accounting -- no journals configured -- can still be typed in.
    amount = fields.Monetary(
        string='Amount Issued', currency_field='currency_id', tracking=True,
        compute='_compute_amount_issued', store=True, readonly=False)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id)
    payment_id = fields.Many2one(
        'account.payment', string='Disbursement Payment', copy=False,
        help='The payment that handed the cash over, if it was recorded in '
             'accounting.')
    # A custody is topped up as the site spends, so the cash goes out in as
    # many payments as it takes -- each with its own journal, date and entry.
    payment_ids = fields.One2many(
        'account.payment', 'construction_custody_id', string='Disbursements',
        readonly=True)
    payment_count = fields.Integer(compute='_compute_amount_issued')

    @api.depends('payment_ids.amount', 'payment_ids.state')
    def _compute_amount_issued(self):
        for custody in self:
            live = custody.payment_ids.filtered(
                lambda payment: payment.state != 'canceled')
            custody.payment_count = len(custody.payment_ids)
            if live:
                custody.amount = sum(live.mapped('amount'))

    line_ids = fields.One2many(
        'construction.custody.line', 'custody_id', string='Settlement',
        copy=False)
    settled_amount = fields.Monetary(
        string='Settled Amount', compute='_compute_amounts', store=True,
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

    move_ids = fields.One2many(
        'account.move', 'construction_custody_id', string='Journal Entries',
        readonly=True)
    move_count = fields.Integer(compute='_compute_amounts')

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
                 'line_ids.expense_id', 'move_ids')
    def _compute_amounts(self):
        for custody in self:
            custody.settled_amount = sum(custody.line_ids.mapped('amount'))
            custody.balance = (custody.amount - custody.settled_amount
                               - custody.returned_amount)
            custody.line_count = len(custody.line_ids)
            custody.posted_count = len(
                custody.line_ids.filtered('expense_id'))
            custody.move_count = len(custody.move_ids)

    @api.depends('ref', 'employee_id')
    def _compute_display_name(self):
        for custody in self:
            parts = [part for part in (custody.ref, custody.employee_id.name)
                     if part and part != 'New']
            custody.display_name = ' - '.join(parts) or self.env._('Custody')

    # ------------------------------------------------------------------
    # Accounting
    # ------------------------------------------------------------------
    def _custody_setup(self):
        """The accounts the entries need, or a message naming what is missing.

        Posting is optional: a company that has not configured the accounts
        runs the custody as a pure operational record, which is how it worked
        before the entries existed.
        """
        company = self.company_id or self.env.company
        return {
            'account': company.construction_custody_account_id,
            'cash_journal': company.construction_custody_journal_id,
            'settlement_journal':
                company.construction_custody_settlement_journal_id,
            'expense_account':
                company.construction_custody_expense_account_id,
        }

    def _post_custody_move(self, journal, lines, ref):
        """Create and post one entry against this custody."""
        self.ensure_one()
        move = self.env['account.move'].create({
            'move_type': 'entry',
            'journal_id': journal.id,
            'date': self.date,
            'ref': ref,
            'construction_custody_id': self.id,
            'line_ids': [(0, 0, vals) for vals in lines],
        })
        move.action_post()
        return move

    def _cash_account(self, setup):
        journal = setup['cash_journal']
        account = journal.default_account_id
        if not account:
            raise UserError(self.env._(
                'Journal "%s" has no account to take the cash from.',
                journal.display_name))
        return account

    # ------------------------------------------------------------------
    # Flow
    # ------------------------------------------------------------------
    def action_open(self):
        """Ask how much is going out, and out of which cash box or bank."""
        self.ensure_one()
        if self.state not in ('draft', 'open'):
            raise UserError(self.env._(
                'Cash can only be handed to a custody that is open or still '
                'a draft.'))
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Disburse Custody'),
            'res_model': 'construction.custody.disburse',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_custody_id': self.id},
        }

    def _disburse(self, journal, amount, date, memo=None):
        """Pay the holder, and put the cash on the custody account.

        The payment is the disbursement -- not a plain journal entry -- so
        the money shows up where the accountant looks for money: in Payments,
        reconcilable against the bank statement like any other.

        Its destination is forced to the custody account rather than the
        holder's payable: the cash has not been spent yet, it is the
        company's money sitting with a person.
        """
        self.ensure_one()
        setup = self._custody_setup()
        if not setup['account']:
            raise UserError(self.env._(
                'Set the cash custody account in the construction settings '
                'before handing cash over.'))
        partner = self.employee_id.work_contact_id
        if not partner:
            raise UserError(self.env._(
                'Employee "%s" has no contact to pay. Set the work contact on '
                'the employee record.', self.employee_id.display_name))
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': partner.id,
            'journal_id': journal.id,
            'destination_account_id': setup['account'].id,
            'amount': amount,
            'date': date,
            'memo': memo or self.env._(
                'Custody %(ref)s - %(holder)s', ref=self.ref,
                holder=self.employee_id.name or ''),
            'construction_custody_id': self.id,
        })
        payment.action_post()
        if self.state == 'draft':
            self.state = 'open'
        if not self.payment_id:
            self.payment_id = payment
        self.message_post(body=self.env._(
            '%(amount)s handed over from %(journal)s.',
            amount=amount, journal=journal.display_name))
        return payment

    def action_view_payments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Disbursements'),
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [('construction_custody_id', '=', self.id)],
        }

    def _post_disbursement(self):
        """Dr the custody account, Cr the cash it came out of.

        Skipped when the cash already left through a payment recorded in
        accounting -- that entry exists, and posting again would double it.
        """
        self.ensure_one()
        setup = self._custody_setup()
        if self.payment_id or not (setup['account'] and setup['cash_journal']):
            return False
        cash = self._cash_account(setup)
        label = self.env._('Custody %(ref)s - %(holder)s',
                           ref=self.ref, holder=self.employee_id.name)
        return self._post_custody_move(setup['cash_journal'], [
            {'account_id': setup['account'].id, 'name': label,
             'debit': self.amount, 'credit': 0.0},
            {'account_id': cash.id, 'name': label,
             'debit': 0.0, 'credit': self.amount},
        ], label)

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
                    # Says the cost is already in the accounts through the
                    # settlement entry below, so the expense never raises one
                    # of its own.
                    'custody_line_id': line.id,
                    'account_id': line.account_id.id,
                })
            custody._post_settlement_move(pending)
            custody.message_post(body=self.env._(
                '%(count)s settlement lines charged to their projects.',
                count=len(pending)))
        return True

    def _post_settlement_move(self, lines):
        """Dr each line's expense account with the project on it, Cr the custody.

        The analytic distribution is the project's own account, so the cost
        lands on the project in the accounts exactly as it does in the
        project's own figures.
        """
        self.ensure_one()
        setup = self._custody_setup()
        if not (setup['account'] and setup['settlement_journal']):
            return False
        move_lines = []
        for line in lines:
            # A project opened before the module created cost centres has no
            # analytic account, and the entry would carry the cost with
            # nothing to read it against. Open one rather than post it blind.
            project = line.project_id
            if not project.analytic_account_id:
                project.analytic_account_id = project._create_analytic_account()
            account = line.account_id or setup['expense_account']
            if not account:
                raise UserError(self.env._(
                    'Set an expense account on "%s", or a default one in the '
                    'construction settings.', line.description))
            move_lines.append({
                'account_id': account.id,
                'name': line.description,
                'debit': line.amount,
                'credit': 0.0,
                'analytic_distribution':
                    project._get_analytic_distribution(),
            })
        total = sum(lines.mapped('amount'))
        label = self.env._('Custody settlement %s', self.ref)
        move_lines.append({
            'account_id': setup['account'].id, 'name': label,
            'debit': 0.0, 'credit': total,
        })
        return self._post_custody_move(
            setup['settlement_journal'], move_lines, label)

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
            custody._post_return()
            custody.state = 'settled'
        return True

    def _post_return(self):
        """Dr the cash it went back into, Cr the custody account."""
        self.ensure_one()
        setup = self._custody_setup()
        if not self.returned_amount or not (
                setup['account'] and setup['cash_journal']):
            return False
        cash = self._cash_account(setup)
        label = self.env._('Custody %s returned', self.ref)
        return self._post_custody_move(setup['cash_journal'], [
            {'account_id': cash.id, 'name': label,
             'debit': self.returned_amount, 'credit': 0.0},
            {'account_id': setup['account'].id, 'name': label,
             'debit': 0.0, 'credit': self.returned_amount},
        ], label)

    def action_view_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Journal Entries'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.move_ids.ids)],
        }

    def action_cancel(self):
        for custody in self:
            if custody.move_ids:
                raise UserError(self.env._(
                    'This custody has posted journal entries. Reverse them '
                    'before cancelling it.'))
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
    # Otherwise a line reads as "construction.custody.line,12" wherever one is
    # named -- which is exactly where a message is trying to be helpful.
    _rec_name = 'description'
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
    account_id = fields.Many2one(
        'account.account', string='Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        default=lambda self:
            self.env.company.construction_custody_expense_account_id,
        help='Left empty, the default account from the construction '
             'settings is used.')
    expense_id = fields.Many2one(
        'construction.expense', string='Charged Expense', readonly=True,
        copy=False, ondelete='set null')
    is_posted = fields.Boolean(
        string='Charged', compute='_compute_is_posted', store=True)

    def _charged_line_message(self):
        # Spelled out inside ``_()`` so the term is picked up for translation.
        return self.env._(
            'These settlement lines are already charged: each one is an '
            'approved expense on its project and sits in a posted entry. '
            'Delete the expense and reverse the entry before changing them:')

    def write(self, vals):
        """A charged line is spent money, so it stops being editable.

        By the time it is charged it has become an approved expense on the
        project and it sits inside the custody's settlement entry. Moving the
        amount here would leave three figures disagreeing -- the receipt, the
        project cost and the books -- with nothing to reconcile them.

        The receipts stay attachable: evidence can always be added.
        """
        if typed_fields(self, vals, unlocked=('expense_id', 'attachment_ids')):
            charged = self.filtered('expense_id')
            if charged:
                refuse(charged, self._charged_line_message())
        return super().write(vals)

    def unlink(self):
        charged = self.filtered('expense_id')
        if charged:
            refuse(charged, self._charged_line_message())
        return super().unlink()

    @api.depends('expense_id')
    def _compute_is_posted(self):
        for line in self:
            line.is_posted = bool(line.expense_id)

    @api.onchange('custody_id')
    def _onchange_custody(self):
        """Default the line to the custody's project, when it has one."""
        if self.custody_id.project_id and not self.project_id:
            self.project_id = self.custody_id.project_id
