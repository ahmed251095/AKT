# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

CONFIRMED_STATES = ('approved', 'invoiced', 'paid')


class ConstructionRABilling(models.Model):
    _inherit = 'construction.ra.billing'

    # ------------------------------------------------------------------
    # Certificate numbering
    # ------------------------------------------------------------------
    # The base declares a certificate number and never fills it, so every
    # certificate reads "0". Contracts are argued certificate by certificate,
    # so each series -- one per subcontract, one per project for the client --
    # gets its own consecutive numbering.
    def _certificate_series_domain(self):
        self.ensure_one()
        domain = [
            ('project_id', '=', self.project_id.id),
            ('billing_type', '=', self.billing_type),
            ('id', '!=', self.id),
        ]
        if self.billing_type == 'subcontractor':
            domain.append(('subcontract_id', '=', self.subcontract_id.id))
        return domain

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if not record.ra_number:
                previous = self.search(
                    record._certificate_series_domain(), order='ra_number desc',
                    limit=1)
                record.ra_number = (previous.ra_number or 0) + 1
        return records

    # ------------------------------------------------------------------
    # Advance recovery
    # ------------------------------------------------------------------
    advance_outstanding = fields.Monetary(
        string='Advance Outstanding', compute='_compute_advance_outstanding',
        currency_field='currency_id',
        help='Advance still to be recovered from this party before this '
             'certificate.')
    advance_recovery = fields.Monetary(
        compute='_compute_advance_recovery', store=True, readonly=False,
        help='Recovered in proportion to the work certified, and never more '
             'than the advance still outstanding. Edit it if the contract '
             'recovers on a different schedule.')

    def _advance_source(self):
        """Who paid the advance and how much of the contract it covers."""
        self.ensure_one()
        if self.billing_type == 'subcontractor' and self.subcontract_id:
            contract = self.subcontract_id
            return contract.advance_amount, contract.contract_value
        return self.project_id.advance_amount, self.project_id.contract_value

    @api.depends('billing_type', 'subcontract_id.advance_amount',
                 'project_id.advance_amount', 'previous_billed')
    def _compute_advance_outstanding(self):
        for record in self:
            advance, _value = record._advance_source()
            recovered = sum(self.search(
                record._certificate_series_domain() +
                [('state', 'in', CONFIRMED_STATES)]).mapped('advance_recovery'))
            record.advance_outstanding = max(advance - recovered, 0.0)

    @api.depends('total_amount', 'advance_outstanding')
    def _compute_advance_recovery(self):
        for record in self:
            advance, contract_value = record._advance_source()
            if not advance or not contract_value:
                record.advance_recovery = 0.0
                continue
            share = advance / contract_value
            due = float_round(
                record.total_amount * share,
                precision_rounding=record.currency_id.rounding or 0.01)
            record.advance_recovery = min(due, record.advance_outstanding)

    @api.constrains('advance_recovery')
    def _check_advance_recovery(self):
        for record in self:
            if float_compare(record.advance_recovery,
                             record.advance_outstanding,
                             precision_digits=2) > 0:
                raise ValidationError(self.env._(
                    'Recovering %(recovery)s exceeds the %(outstanding)s of '
                    'advance still outstanding on this contract.',
                    recovery=record.advance_recovery,
                    outstanding=record.advance_outstanding))
