from odoo import api, fields, models
from odoo.exceptions import UserError


class ConstructionCustodyDisburse(models.TransientModel):
    """Hand cash to the holder, once or as many times as the site needs.

    A custody is not one payment. The engineer is given something to start
    with, spends it, and is topped up before the receipts are even in --
    which is why the amount issued has to be able to grow, each top-up
    carrying its own payment, its own date and its own entry.

    Where the money comes from is asked here rather than assumed: a small
    float leaves the cash box, a large one goes out by bank transfer, and
    both are the same custody.
    """
    _name = 'construction.custody.disburse'
    _description = 'Disburse Cash Custody'

    custody_id = fields.Many2one(
        'construction.custody', string='Custody', required=True,
        ondelete='cascade')
    employee_id = fields.Many2one(
        related='custody_id.employee_id', string='Custody Holder')
    currency_id = fields.Many2one(related='custody_id.currency_id')
    already_issued = fields.Monetary(
        related='custody_id.amount', string='Already Issued')

    journal_id = fields.Many2one(
        'account.journal', string='Pay From', required=True,
        domain="[('type', 'in', ('cash', 'bank'))]",
        default=lambda self:
            self.env.company.construction_custody_journal_id,
        help='The cash box or bank the money leaves.')
    amount = fields.Monetary(string='Amount', required=True)
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    memo = fields.Char(string='Memo')

    @api.onchange('custody_id')
    def _onchange_custody_id(self):
        if self.custody_id and not self.memo:
            self.memo = self.env._(
                'Custody %(ref)s - %(holder)s',
                ref=self.custody_id.ref,
                holder=self.custody_id.employee_id.name or '')

    def action_disburse(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(self.env._('The amount has to be more than zero.'))
        self.custody_id._disburse(
            journal=self.journal_id, amount=self.amount, date=self.date,
            memo=self.memo)
        return {'type': 'ir.actions.act_window_close'}
