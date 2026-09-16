from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Default build-up ratios applied to every new tender / BOQ item.
    # They mirror the pricing sheet the estimation office works with:
    #   (dry cost + operating cost) x (1 + profit + contingency + admin) x (1 + expenses)
    construction_profit_percent = fields.Float(
        string='Profit Ratio (%)', default=25.0,
        help='Net profit added on top of the item cost.')
    construction_contingency_percent = fields.Float(
        string='Contingency Ratio (%)', default=5.0,
        help='Allowance for unforeseen site conditions and price variations.')
    construction_admin_percent = fields.Float(
        string='Administration Ratio (%)', default=10.0,
        help='Share of head office administration carried by the item.')
    construction_expense_percent = fields.Float(
        string='General Expenses Ratio (%)', default=14.0,
        help='General expenses applied on the marked-up price, '
             'the last step of the build-up.')
    # ---- cash custody posting ----
    # Left empty on purpose: the chart of accounts is the accountant's, and a
    # guessed account posts real money to the wrong place.
    construction_custody_account_id = fields.Many2one(
        'account.account', string='Cash Custody Account',
        domain="[('account_type', '=', 'asset_current')]",
        help='Asset account the cash sits in while it is with the holder. '
             'Debited when the custody goes out, credited as it is settled.')
    construction_custody_journal_id = fields.Many2one(
        'account.journal', string='Custody Disbursement Journal',
        domain="[('type', 'in', ('cash', 'bank'))]",
        help='Where the cash leaves from, and where returned cash goes back.')
    construction_custody_settlement_journal_id = fields.Many2one(
        'account.journal', string='Custody Settlement Journal',
        domain="[('type', '=', 'general')]",
        help='Journal the settlement entry is booked in.')
    construction_custody_expense_account_id = fields.Many2one(
        'account.account', string='Default Custody Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        help='Used for a settlement line that carries no account of its own.')

    construction_reminder_days = fields.Integer(
        string='Tender Reminder (days)', default=2,
        help='How many days before a tender date the responsible users are '
             'reminded.')
    construction_bid_bond_percent = fields.Float(
        string='Bid Bond Ratio (%)', default=2.0,
        help='Default bid bond percentage of the estimated bid value.')
    construction_performance_bond_percent = fields.Float(
        string='Performance Bond Ratio (%)', default=10.0,
        help='Default performance bond percentage of the contract value.')
