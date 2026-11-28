from odoo import models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def _fill_bank_cash_dashboard_data(self, dashboard_data):
        """One figure on a bank or cash card: the balance of its account.

        Odoo splits that figure in two. "Balance" is what the statements
        and the direct payments come to, and whatever was posted straight
        to the account - a funding entry, an opening balance, a correction
        - is counted apart from it as "Misc. Operations". A till funded by
        journal entry and spent through payments therefore reads as two
        large opposite numbers, and the one number the bookkeeper came for
        is on neither line.

        So the balance is read off the ledger instead, and the second line
        goes away. What the split was there to flag - entries touching the
        account outside a statement - is still reachable from the account
        itself.
        """
        super()._fill_bank_cash_dashboard_data(dashboard_data)

        journals = self.filtered(lambda journal: journal.type in ('bank', 'cash', 'credit'))
        accounts = journals.default_account_id
        if not accounts:
            return

        # Both sums, because a journal kept in a currency of its own reads
        # its balance in that currency while the company's books are in the
        # company's.
        totals = {
            account.id: (balance, amount_currency)
            for account, balance, amount_currency in self.env['account.move.line']._read_group(
                domain=[
                    *self.env['account.move.line']._check_company_domain(self.env.companies),
                    ('account_id', 'in', accounts.ids),
                    ('parent_state', '=', 'posted'),
                ],
                groupby=['account_id'],
                aggregates=['balance:sum', 'amount_currency:sum'],
            )
        }

        for journal in journals:
            account = journal.default_account_id
            if not account or journal.id not in dashboard_data:
                continue
            company_currency = self.env['res.currency'].browse(journal.company_id.sudo().currency_id.id)
            currency = journal.currency_id or company_currency
            balance, amount_currency = totals.get(account.id, (0.0, 0.0))
            total = amount_currency if journal.currency_id and journal.currency_id != company_currency else balance
            dashboard_data[journal.id].update({
                'account_balance': currency.format(total),
                'nb_lines_bank_account_balance': (
                    account.id in totals
                    and journal.company_id.id in journal.company_id._accessible_branches().ids
                ),
                # Folded into the balance above.
                'nb_misc_operations': 0,
            })
