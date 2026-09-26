from odoo import models

from .approval_lock import refuse, typed_fields


class ConstructionBoq(models.Model):
    _inherit = 'construction.boq'

    def write(self, vals):
        """An approved bill of quantities stops being editable.

        Everything downstream is priced from it: the phase budgets, what a
        work order may execute, what may be handed to a subcontractor and
        what a certificate measures. Changing a quantity or a rate underneath
        all of that moves figures nobody reviewed, on documents that have
        already been signed.

        The way back is the Revise button, which the base module already
        offers on an approved bill - and which the chatter records.
        """
        if typed_fields(self, vals, unlocked=('state',)):
            frozen = self.filtered(lambda boq: boq.state == 'approved')
            if frozen:
                refuse(frozen, self.env._(
                    'This bill of quantities is approved, and the budgets, '
                    'work orders and certificates are all priced from it. '
                    'Press Revise to open it up again:'))
        return super().write(vals)
