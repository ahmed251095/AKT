from odoo import api, fields, models
from odoo.exceptions import UserError


class ConstructionCustodyReturn(models.TransientModel):
    """Take the unspent cash back from the holder.

    The mirror of a disbursement, and asked the same way: cash that went out
    of the site box can come back to the bank, and a custody handed out in
    two instalments can be returned in one.
    """
    _name = 'construction.custody.return'
    _description = 'Return Cash Custody'

    custody_id = fields.Many2one(
        'construction.custody', string='Custody', required=True,
        ondelete='cascade')
    employee_id = fields.Many2one(
        related='custody_id.employee_id', string='Custody Holder')
    currency_id = fields.Many2one(related='custody_id.currency_id')
    balance = fields.Monetary(
        related='custody_id.balance', string='Balance with Holder')

    journal_id = fields.Many2one(
        'account.journal', string='Return To', required=True,
        domain="[('type', 'in', ('cash', 'bank'))]",
        default=lambda self:
            self.env.company.construction_custody_journal_id,
        help='The cash box or bank the money goes back into.')
    amount = fields.Monetary(
        string='Amount', required=True,
        compute='_compute_amount', store=True, readonly=False)
    date = fields.Date(
        string='Date', required=True, default=fields.Date.context_today)
    memo = fields.Char(string='Memo')

    @api.depends('custody_id')
    def _compute_amount(self):
        for wizard in self:
            wizard.amount = max(wizard.custody_id.balance, 0.0)

    def action_return(self):
        self.ensure_one()
        if self.amount <= 0:
            raise UserError(self.env._('The amount has to be more than zero.'))
        self.custody_id._return_cash(
            journal=self.journal_id, amount=self.amount, date=self.date,
            memo=self.memo)
        return {'type': 'ir.actions.act_window_close'}
