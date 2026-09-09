from odoo import api, fields, models, Command
from odoo.exceptions import UserError


class ConstructionSubcontract(models.Model):
    _inherit = 'construction.subcontract'

    line_ids = fields.One2many(
        'construction.subcontract.line', 'subcontract_id',
        string='Assigned Items')
    assigned_total = fields.Monetary(
        string='Assigned Value', compute='_compute_line_totals', store=True,
        help='Sum of the items handed to this subcontractor.')
    assigned_margin = fields.Monetary(
        string='Margin on Assignment', compute='_compute_line_totals',
        store=True,
        help='What the client pays for these quantities, less what this '
             'subcontractor charges for them.')
    assigned_margin_percent = fields.Float(
        string='Margin (%)', compute='_compute_line_totals', store=True)

    progress_percent = fields.Float(
        string='Progress (%)', compute='_compute_progress',
        help='Completed value against assigned value, so a big item counts '
             'for more than a small one.')
    amount_to_certify = fields.Monetary(
        string='Value to Certify', compute='_compute_progress')

    # The base carries an advance percentage that nothing ever acts on.
    advance_amount = fields.Monetary(
        string='Advance Amount', compute='_compute_advance', store=True,
        readonly=False,
        help='Paid up front against the contract and recovered from the '
             'certificates as work is done.')
    advance_recovered = fields.Monetary(
        string='Advance Recovered', compute='_compute_advance_recovered')
    advance_balance = fields.Monetary(
        string='Advance Outstanding', compute='_compute_advance_recovered')

    # Re-declared so a contract priced item by item totals itself up. Kept
    # writable for the lump-sum contracts that carry no item breakdown.
    contract_value = fields.Monetary(
        compute='_compute_contract_value', store=True, readonly=False)

    @api.depends('line_ids.amount', 'line_ids.margin')
    def _compute_line_totals(self):
        for contract in self:
            contract.assigned_total = sum(contract.line_ids.mapped('amount'))
            contract.assigned_margin = sum(contract.line_ids.mapped('margin'))
            revenue = contract.assigned_total + contract.assigned_margin
            contract.assigned_margin_percent = (
                100.0 * contract.assigned_margin / revenue) if revenue else 0.0

    def _compute_progress(self):
        for contract in self:
            assigned = sum(contract.line_ids.mapped('amount'))
            done = sum(line.progress_qty * line.unit_price
                       for line in contract.line_ids)
            contract.progress_percent = (
                100.0 * done / assigned) if assigned else 0.0
            contract.amount_to_certify = sum(
                contract.line_ids.mapped('amount_to_certify'))

    @api.depends('contract_value', 'advance_percent')
    def _compute_advance(self):
        for contract in self:
            contract.advance_amount = (
                contract.contract_value * contract.advance_percent / 100.0)

    @api.depends('billing_ids.state', 'billing_ids.advance_recovery',
                 'advance_amount')
    def _compute_advance_recovered(self):
        for contract in self:
            confirmed = contract.billing_ids.filtered(
                lambda b: b.state in ('approved', 'invoiced', 'paid'))
            contract.advance_recovered = sum(
                confirmed.mapped('advance_recovery'))
            contract.advance_balance = max(
                contract.advance_amount - contract.advance_recovered, 0.0)

    @api.depends('line_ids.amount')
    def _compute_contract_value(self):
        for contract in self:
            if not contract.line_ids:
                # Lump-sum contract: leave the figure the buyer negotiated.
                continue
            contract.contract_value = sum(contract.line_ids.mapped('amount'))

    def action_certify_progress(self):
        """Raise the interim certificate for the progress accepted so far.

        Deliberately a different method from the base module's
        ``action_create_certificate``, which opens an empty certificate for
        someone to fill in by hand. Both are useful: this one measures the
        assigned items, that one covers anything outside them.
        """
        self.ensure_one()
        pending = self.line_ids.filtered(lambda l: l.qty_to_certify > 0)
        if not pending:
            raise UserError(self.env._(
                'Nothing new to certify. Set the progress on the assigned '
                'items first.'))
        missing = pending.filtered(
            lambda l: not (self.product_id or l.boq_line_id.product_id))
        if missing:
            raise UserError(self.env._(
                'Set the service product on the subcontract, or on these BOQ '
                'items, before raising a certificate:\n%s',
                '\n'.join('- %s' % line.display_name for line in missing)))

        billing = self.env['construction.ra.billing'].create({
            'name': self.env._('Certificate - %s', self.display_name),
            'billing_type': 'subcontractor',
            'project_id': self.project_id.id,
            'partner_id': self.subcontractor_id.id,
            'subcontract_id': self.id,
            'purchase_order_id': self.purchase_order_id.id,
            'billing_date': fields.Date.context_today(self),
            'retention_percent': self.retention_percent,
            'line_ids': [
                Command.create({
                    'product_id': (self.product_id
                                   or line.boq_line_id.product_id).id,
                    'boq_line_id': line.boq_line_id.id,
                    'boq_line_description': line.description
                    or line.boq_line_id.description,
                    'work_type': line.boq_line_id.work_type,
                    'uom_id': line.uom_id.id,
                    # Measured against what this subcontractor was given, not
                    # against the whole bill of quantities.
                    'boq_qty': line.qty,
                    'qty_previous': line.certified_qty,
                    'qty_current': line.qty_to_certify,
                    # Their agreed rate, not our own cost rate.
                    'unit_rate': line.unit_price,
                    'wbs_id': line.boq_line_id.wbs_id.id,
                }) for line in pending
            ],
        })
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Subcontractor Certificate'),
            'res_model': 'construction.ra.billing',
            'res_id': billing.id,
            'view_mode': 'form',
        }

    def unlink(self):
        """Delete the items through the ORM before the contract goes.

        The cascade is a database constraint, so it removes the rows without
        telling the ORM, and the BOQ would keep showing quantities as assigned
        to a contract that no longer exists.
        """
        self.line_ids.unlink()
        return super().unlink()

    def action_add_remaining_boq_items(self):
        """Fill the contract with everything on the BOQ nobody has yet."""
        Line = self.env['construction.subcontract.line']
        for contract in self:
            taken = contract.line_ids.boq_line_id
            candidates = self.env['construction.boq.line'].search([
                ('boq_id.project_id', '=', contract.project_id.id),
                ('is_section', '=', False),
            ])
            for boq_line in candidates - taken:
                if boq_line.unassigned_qty <= 0:
                    continue
                Line.create({
                    'subcontract_id': contract.id,
                    'boq_line_id': boq_line.id,
                    'qty': boq_line.unassigned_qty,
                    'unit_price': boq_line.cost_rate,
                })
        return True
