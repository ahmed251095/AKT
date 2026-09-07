from odoo import api, fields, models


class ConstructionSubcontract(models.Model):
    _inherit = 'construction.subcontract'

    line_ids = fields.One2many(
        'construction.subcontract.line', 'subcontract_id',
        string='Assigned Items')
    line_count = fields.Integer(
        string='Assigned Items', compute='_compute_line_totals')
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

    # Re-declared so a contract priced item by item totals itself up. Kept
    # writable for the lump-sum contracts that carry no item breakdown.
    contract_value = fields.Monetary(
        compute='_compute_contract_value', store=True, readonly=False)

    @api.depends('line_ids.amount', 'line_ids.margin')
    def _compute_line_totals(self):
        for contract in self:
            contract.line_count = len(contract.line_ids)
            contract.assigned_total = sum(contract.line_ids.mapped('amount'))
            contract.assigned_margin = sum(contract.line_ids.mapped('margin'))
            revenue = contract.assigned_total + contract.assigned_margin
            contract.assigned_margin_percent = (
                100.0 * contract.assigned_margin / revenue) if revenue else 0.0

    @api.depends('line_ids.amount')
    def _compute_contract_value(self):
        for contract in self:
            if not contract.line_ids:
                # Lump-sum contract: leave the figure the buyer negotiated.
                continue
            contract.contract_value = sum(contract.line_ids.mapped('amount'))

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
