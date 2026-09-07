from odoo import fields, models


class ConstructionExpense(models.Model):
    _inherit = 'construction.expense'

    # Without these an expense only knows its project, so wages and materials
    # can never be told apart per work order or per item.
    work_order_id = fields.Many2one(
        'construction.work.order', string='Work Order', index=True,
        domain="[('project_id', '=', project_id)]")
    boq_line_id = fields.Many2one(
        'construction.boq.line', string='BOQ Item', index=True,
        domain="[('boq_id.project_id', '=', project_id), "
               "('is_section', '=', False)]")
