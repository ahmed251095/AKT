from odoo import fields, models

EXPENSE_ACCOUNT_DOMAIN = "[('account_type', 'in', ('expense', 'expense_direct_cost'))]"


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
    construction_site_warehouse_id = fields.Many2one(
        'stock.warehouse', string='Site Warehouse',
        help='Warehouse the per-project site locations are created under. '
             'Left empty, the company\'s first warehouse is used.')

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

    # ---- expense posting, one account per category ----
    # What an expense hits depends on what it was, so the category picks the
    # account rather than the site being asked to know the chart of accounts.
    construction_expense_journal_id = fields.Many2one(
        'account.journal', string='Default Expense Journal',
        domain="[('type', 'in', ('cash', 'bank'))]",
        help='Suggested on a new expense as where the money comes out of. '
             'Each expense can be paid from another cash box or bank.')
    construction_expense_material_account_id = fields.Many2one(
        'account.account', string='Materials Account',
        domain=EXPENSE_ACCOUNT_DOMAIN)
    construction_expense_labour_account_id = fields.Many2one(
        'account.account', string='Labour Account',
        domain=EXPENSE_ACCOUNT_DOMAIN)
    construction_expense_equipment_account_id = fields.Many2one(
        'account.account', string='Equipment Account',
        domain=EXPENSE_ACCOUNT_DOMAIN)
    construction_expense_subcontract_account_id = fields.Many2one(
        'account.account', string='Subcontract Account',
        domain=EXPENSE_ACCOUNT_DOMAIN)
    construction_expense_overhead_account_id = fields.Many2one(
        'account.account', string='Overhead Account',
        domain=EXPENSE_ACCOUNT_DOMAIN)
    construction_expense_other_account_id = fields.Many2one(
        'account.account', string='Other Expenses Account',
        domain=EXPENSE_ACCOUNT_DOMAIN)

    def construction_expense_account(self, category):
        """The account an expense of this category is booked to."""
        self.ensure_one()
        return self[
            'construction_expense_%s_account_id' % category
        ] if category else self.env['account.account']

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
