from odoo import fields, models
from odoo.exceptions import UserError


class ConstructionExpense(models.Model):
    _inherit = 'construction.expense'

    # Once approved, the expense is a booked cost: it is counted in the work
    # order's actual cost and in the phase's spend. Changing the amount or
    # moving it to another item afterwards would shift money nobody reviewed,
    # and nothing downstream would ask again. The record is reachable by
    # sending it back to draft, which the chatter records.
    _LOCKED_ON_APPROVAL = (
        'name', 'project_id', 'wbs_id', 'work_order_id', 'boq_line_id',
        'date', 'category', 'amount', 'employee_id', 'description',
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
