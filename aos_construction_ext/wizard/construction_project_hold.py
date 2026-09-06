from odoo import fields, models


class ConstructionProjectHold(models.TransientModel):
    _name = 'construction.project.hold'
    _description = 'Hold Project'

    project_id = fields.Many2one(
        'construction.project', string='Project', required=True,
        ondelete='cascade')
    reason = fields.Text(string='Reason', required=True)

    def action_confirm(self):
        self.ensure_one()
        self.project_id.action_confirm_hold(self.reason)
        return {'type': 'ir.actions.act_window_close'}
