from odoo import fields, models


class ConstructionTenderReject(models.TransientModel):
    """Management turning down a request to open an operation.

    The tender is kept rather than deleted: the booklet fee may already have
    been spent, and the reason is what the estimation office learns from.
    """
    _name = 'construction.tender.reject'
    _description = 'Reject Tender'

    tender_id = fields.Many2one(
        'construction.tender', string='Tender', required=True,
        ondelete='cascade')
    reason = fields.Text(string='Reason', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.tender_id.action_reject(reason=self.reason)
        return {'type': 'ir.actions.act_window_close'}
