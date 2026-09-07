from odoo import api, fields, models

#: A payment counts as settled once it has left the draft stage.
SETTLED_STATES = ('in_process', 'paid')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    construction_tender_id = fields.Many2one(
        'construction.tender', string='Tender Document Fee For', index=True,
        copy=False,
        help='The tender whose conditions booklet this payment pays for. '
             'Settling the payment marks the booklet as purchased.')

    @api.model_create_multi
    def create(self, vals_list):
        payments = super().create(vals_list)
        payments._sync_tender_booklet()
        return payments

    def write(self, vals):
        result = super().write(vals)
        if {'state', 'date', 'construction_tender_id'} & vals.keys():
            self._sync_tender_booklet()
        return result

    def _sync_tender_booklet(self):
        """Keep the tender's booklet status in step with its fee payment.

        The office should not have to tick a box that the accounting entry
        already answers: once the fee is actually paid the booklet is bought,
        and if the payment is pulled back to draft it is not.
        """
        for payment in self:
            tender = payment.construction_tender_id
            if not tender:
                continue
            if payment.state in SETTLED_STATES:
                if (tender.tender_doc_payment_id == payment
                        and tender.tender_doc_purchased
                        and tender.tender_doc_purchase_date == payment.date):
                    # Already in step. Writing again would bounce back here
                    # through the tender's own mirror and never settle.
                    continue
                tender.write({
                    'tender_doc_payment_id': payment.id,
                    'tender_doc_purchased': True,
                    'tender_doc_purchase_date': payment.date,
                })
                tender.message_post(body=tender.env._(
                    'Conditions booklet fee settled by %s.',
                    payment.display_name))
            elif tender.tender_doc_payment_id == payment \
                    and tender.tender_doc_purchased:
                tender.write({
                    'tender_doc_purchased': False,
                    'tender_doc_purchase_date': False,
                })
