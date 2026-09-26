from odoo import api, fields, models
from odoo.exceptions import UserError


class ConstructionExpense(models.Model):
    _inherit = 'construction.expense'

    # Once approved, the expense is a booked cost: it is counted in the work
    # order's actual cost and in the phase's spend, and it now stands behind a
    # journal entry. Changing the amount or moving it to another item
    # afterwards would shift money nobody reviewed, and nothing downstream
    # would ask again. The record is reachable by sending it back to draft,
    # which reverses the entry and which the chatter records.
    _LOCKED_ON_APPROVAL = (
        'name', 'project_id', 'wbs_id', 'work_order_id', 'boq_line_id',
        'date', 'category', 'amount', 'employee_id', 'description',
        'journal_id', 'account_id',
    )

    # Without these an expense only knows its project, so wages and materials
    # can never be told apart per work order or per item.
    work_order_id = fields.Many2one(
        'construction.work.order', string='Work Order', index=True,
        domain="[('project_id', '=', project_id)]")
    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item', index=True,
        domain="[('boq_id.project_id', '=', project_id), "
               "('is_section', '=', False)]")

    # ------------------------------------------------------------------
    # Where the money comes out of, and what it is booked against
    # ------------------------------------------------------------------
    journal_id = fields.Many2one(
        'account.journal', string='Paid From',
        domain="[('type', 'in', ('cash', 'bank'))]",
        default=lambda self: self.env.company.construction_expense_journal_id,
        help='The cash box or bank the money leaves. Its own account is what '
             'the entry credits.')
    account_id = fields.Many2one(
        'account.account', string='Expense Account',
        compute='_compute_account_id', store=True, readonly=False,
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        help='Taken from the category, using the accounts set in the '
             'construction settings. Type over it for a one-off.')
    move_id = fields.Many2one(
        'account.move', string='Journal Entry', readonly=True, copy=False,
        help='The entry raised when the expense was approved. Emptied when it '
             'goes back to draft and the entry is reversed.')
    move_ids = fields.One2many(
        'account.move', 'construction_expense_id', string='Journal Entries',
        readonly=True)
    move_count = fields.Integer(compute='_compute_move_count')

    # Set by the custody settlement. An expense that came off a custody is
    # already in the accounts -- the custody posts the settlement entry for
    # the whole batch -- so it must never raise one of its own, however many
    # times it is sent back and approved again.
    custody_line_id = fields.Many2one(
        'construction.custody.line', string='Settlement Line', readonly=True,
        copy=False, ondelete='set null')

    @api.depends('category')
    def _compute_account_id(self):
        company = self.env.company
        for expense in self:
            expense.account_id = company.construction_expense_account(
                expense.category)

    @api.depends('move_ids')
    def _compute_move_count(self):
        for expense in self:
            expense.move_count = len(expense.move_ids)

    # ------------------------------------------------------------------
    # Posting
    # ------------------------------------------------------------------
    def action_approve(self):
        """Approve, and book the cost where the money actually went."""
        result = super().action_approve()
        self._post_expense_move()
        return result

    def _post_expense_move(self):
        """Dr the category's account with the project on it, Cr the journal.

        The analytic distribution is the project's own account, so the cost
        lands on the project in the accounts exactly as it does in the
        project's own figures.
        """
        for expense in self:
            if expense.custody_line_id or expense.move_id or not expense.amount:
                continue
            journal, account = expense._posting_setup()
            project = expense.project_id
            # A project opened before the module created cost centres has no
            # analytic account, and the entry would carry the cost with
            # nothing to read it against. Open one rather than post it blind.
            if not project.analytic_account_id:
                project.analytic_account_id = project._create_analytic_account()
            label = expense.name or expense.ref
            move = self.env['account.move'].create({
                'move_type': 'entry',
                'journal_id': journal.id,
                'date': expense.date or fields.Date.context_today(expense),
                'ref': expense.ref,
                'construction_expense_id': expense.id,
                'line_ids': [
                    (0, 0, {
                        'account_id': account.id,
                        'name': label,
                        'debit': expense.amount,
                        'credit': 0.0,
                        'analytic_distribution':
                            project._get_analytic_distribution(),
                    }),
                    (0, 0, {
                        'account_id': journal.default_account_id.id,
                        'name': label,
                        'debit': 0.0,
                        'credit': expense.amount,
                    }),
                ],
            })
            move.action_post()
            expense.move_id = move
        return True

    def _posting_setup(self):
        """The journal and account to post with, or say what is missing.

        Deliberately loud. The custody was written to skip posting silently
        when its accounts were not configured, and the result was cash going
        out for months with nothing in the books to show for it. An approval
        that half-happens is worse than one that stops and says why.
        """
        self.ensure_one()
        if not self.journal_id:
            raise UserError(self.env._(
                'Choose the cash box or bank "%s" is paid from before '
                'approving it.', self.display_name))
        if not self.journal_id.default_account_id:
            raise UserError(self.env._(
                'Journal "%s" has no account to take the money from.',
                self.journal_id.display_name))
        if not self.account_id:
            raise UserError(self.env._(
                'There is no expense account for this category. Set one on '
                'the expense, or set the account for each category in the '
                'construction settings.'))
        return self.journal_id, self.account_id

    def action_reset(self):
        """Send it back to draft, and take the entry back out of the books."""
        self._reverse_expense_move()
        return super().action_reset()

    def _reverse_expense_move(self):
        for expense in self.filtered('move_id'):
            move = expense.move_id
            if move.state == 'posted':
                reversal = move._reverse_moves([{
                    'date': fields.Date.context_today(expense),
                    'ref': self.env._('Reversal of %s', move.name),
                }], cancel=True)
                expense.message_post(body=self.env._(
                    'Entry %(entry)s reversed by %(reversal)s.',
                    entry=move.name, reversal=reversal.name))
            elif move.state == 'draft':
                move.unlink()
            expense.move_id = False
        return True

    def action_view_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Journal Entries'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('construction_expense_id', '=', self.id)],
        }

    def write(self, vals):
        if any(field in vals for field in self._LOCKED_ON_APPROVAL):
            approved = self.filtered(lambda expense: expense.state == 'approved')
            if approved:
                raise UserError(self.env._(
                    'These expenses are approved and already counted in the '
                    'cost, so they can no longer be edited. Send one back to '
                    'draft to change it:\n%s',
                    '\n'.join('- %s' % expense.display_name
                              for expense in approved)))
        return super().write(vals)
