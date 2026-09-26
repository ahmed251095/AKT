# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round

from .approval_lock import refuse, typed_fields

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

    def _advance_outstanding(self):
        """Advance left to recover before this certificate."""
        self.ensure_one()
        advance, _value = self._advance_source()
        recovered = sum(self.search(
            self._certificate_series_domain() +
            [('state', 'in', CONFIRMED_STATES)]).mapped('advance_recovery'))
        return max(advance - recovered, 0.0)

    @api.depends('billing_type', 'subcontract_id.advance_amount',
                 'project_id.advance_amount', 'previous_billed')
    def _compute_advance_outstanding(self):
        for record in self:
            record.advance_outstanding = record._advance_outstanding()

    # Sums the lines rather than reading total_amount: the base computes the
    # total and the net payable together, so reading the total here would ask
    # for a figure that is still being computed and get a zero back -- leaving
    # the net payable with no recovery deducted.
    #
    # Depending on stored fields only matters just as much: a stored field
    # that leans on a computed one that is not stored never gets recomputed.
    @api.depends('line_ids.amount', 'billing_type',
                 'subcontract_id.advance_amount',
                 'subcontract_id.contract_value', 'project_id.advance_amount',
                 'project_id.contract_value')
    def _compute_advance_recovery(self):
        for record in self:
            advance, contract_value = record._advance_source()
            if not advance or not contract_value:
                record.advance_recovery = 0.0
                continue
            certified = sum(record.line_ids.mapped('amount'))
            due = float_round(
                certified * advance / contract_value,
                precision_rounding=record.currency_id.rounding or 0.01)
            record.advance_recovery = min(due, record._advance_outstanding())

    @api.constrains('advance_recovery')
    def _check_advance_recovery(self):
        for record in self:
            outstanding = record._advance_outstanding()
            if float_compare(record.advance_recovery, outstanding,
                             precision_digits=2) > 0:
                raise ValidationError(self.env._(
                    'Recovering %(recovery)s exceeds the %(outstanding)s of '
                    'advance still outstanding on this contract.',
                    recovery=record.advance_recovery,
                    outstanding=outstanding))


class ConstructionRABillingFrozen(models.Model):
    """An approved certificate is frozen, its lines included.

    From approval on, the certificate is what the client or the
    subcontractor is owed: it counts in the certified revenue and the
    certified subcontract cost, it caps what the next certificate may
    measure, and once invoiced it stands behind an accounting entry. The way
    back is to cancel it and reset it to draft, both of which the chatter
    records.
    """
    _inherit = 'construction.ra.billing'

    def _approved_certificate_message(self):
        # Spelled out inside ``_()`` so the term is picked up for translation.
        return self.env._(
            'This certificate is approved and counted against the contract, '
            'so it can no longer be edited. Cancel it and reset it to draft '
            'to change it:')

    def write(self, vals):
        # The state, the invoice the button stamps on the record and the
        # number the sequence assigns are the workflow's own, not a person's.
        if typed_fields(self, vals, unlocked=('state', 'move_id', 'ra_number')):
            frozen = self.filtered(
                lambda billing: billing.state in CONFIRMED_STATES)
            if frozen:
                refuse(frozen, self._approved_certificate_message())
        return super().write(vals)


class ConstructionRABillingLine(models.Model):
    _inherit = 'construction.ra.billing.line'

    def _approved_certificate_message(self):
        return self.env._(
            'This certificate is approved and counted against the contract, '
            'so it can no longer be edited. Cancel it and reset it to draft '
            'to change it:')

    def write(self, vals):
        if typed_fields(self, vals):
            frozen = self.filtered(
                lambda line: line.billing_id.state in CONFIRMED_STATES)
            if frozen:
                refuse(frozen.billing_id, self._approved_certificate_message())
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        billings = self.env['construction.ra.billing'].browse([
            vals['billing_id'] for vals in vals_list if vals.get('billing_id')])
        frozen = billings.filtered(
            lambda billing: billing.state in CONFIRMED_STATES)
        if frozen:
            refuse(frozen, self._approved_certificate_message())
        return super().create(vals_list)

    def unlink(self):
        frozen = self.billing_id.filtered(
            lambda billing: billing.state in CONFIRMED_STATES)
        if frozen:
            refuse(frozen, self._approved_certificate_message())
        return super().unlink()
