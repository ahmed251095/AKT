from odoo import api, fields, models
from odoo.exceptions import UserError

from .approval_lock import refuse, typed_fields


class ConstructionBoq(models.Model):
    _inherit = 'construction.boq'

    tender_id = fields.Many2one(
        'construction.tender', string='Awarded From',
        compute='_compute_tender_id',
        help='The won tender this project came from, if it came from one.')

    @api.depends('project_id')
    def _compute_tender_id(self):
        for boq in self:
            boq.tender_id = self.env['construction.tender'].search(
                [('project_id', '=', boq.project_id.id)],
                order='id desc', limit=1) if boq.project_id else False

    def action_pull_tender_pricing(self):
        """Fill the item rates from the tender the project was won on.

        The award already carries the pricing across, but a bill written
        afterwards - or one whose items were retyped - arrives empty. Items
        are matched on their description, which is what the estimation office
        and the site both read; anything unmatched is left alone rather than
        guessed at.
        """
        self.ensure_one()
        if not self.tender_id:
            raise UserError(self.env._(
                'This project did not come from a tender, so there is no '
                'pricing to pull. Type the rates on the items.'))
        tender_lines = self.tender_id.line_ids
        filled = 0
        for line in self.line_ids.filtered(lambda line: not line.is_section):
            match = tender_lines.filtered(
                lambda tender_line: tender_line.description == line.description
                and not tender_line.is_section)[:1]
            if not match:
                continue
            line._write_pricing(self.tender_id._pricing_values(match))
            filled += 1
        if not filled:
            raise UserError(self.env._(
                'None of the items match an item on %s by description, so '
                'there was nothing to pull.', self.tender_id.display_name))
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': self.env._('%s items priced from the tender.',
                                      filled),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }

    def action_import_sheet(self):
        """Open the reader that fills the items from the office's workbook."""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'aos_construction_ext.action_construction_boq_import')
        action['context'] = {
            'active_model': self._name,
            'active_id': self.id,
        }
        return action

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
