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
    # Disbursement
    # ------------------------------------------------------------------
    #: What the certificate actually pays out. A certified item is not always
    #: disbursed in full -- the contract, the authority or the cash position
    #: releases a share of it -- and that share is set per item, because it
    #: differs item by item. This is the sum of those shares, read alongside
    #: the amount certified rather than in place of it: the deductions and
    #: the net payable below still answer what the certificate is worth.
    disbursement_total = fields.Monetary(
        string='Total Disbursement', compute='_compute_disbursement_total',
        store=True, currency_field='currency_id',
        help='The sum of every item\'s disbursement: its amount taken at '
             'the disbursement percentage set on the line.')

    @api.depends('line_ids.disbursement_amount')
    def _compute_disbursement_total(self):
        for billing in self:
            billing.disbursement_total = sum(
                billing.line_ids.mapped('disbursement_amount'))

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


class ConstructionRABillingFromBoq(models.Model):
    """Measuring a certificate against whole bills of quantities.

    A certificate is written against the bill: the surveyor goes down the
    items in order and writes this period's quantity next to each one.
    Picking those items back one at a time out of a dialog is not how the
    sheet is read - so the bills themselves are picked here, and every item
    on them is laid out below ready to be measured.
    """
    _inherit = 'construction.ra.billing'

    boq_ids = fields.Many2many(
        'construction.boq', string='Bills of Quantities',
        domain="[('project_id', '=', project_id)]",
        help='Every item of the bills picked here is listed below, ready '
             'for this period\'s quantity. Pick several and their items are '
             'listed together, in the order each bill carries them.')

    def _certified_before(self, boq_lines):
        """What the earlier certificates of this series measured, per item.

        Read in one go rather than item by item: a bill runs to hundreds of
        items and this is answered while someone waits on the form.
        """
        self.ensure_one()
        domain = [
            ('boq_line_id', 'in', boq_lines.ids),
            ('billing_id.state', 'in', CONFIRMED_STATES),
            ('billing_id.billing_type', '=', self.billing_type),
        ]
        if self._origin:
            domain.append(('billing_id', '!=', self._origin.id))
        if self.billing_type == 'subcontractor' and self.subcontract_id:
            domain.append(
                ('billing_id.subcontract_id', '=', self.subcontract_id.id))
        groups = self.env['construction.ra.billing.line']._read_group(
            domain, ['boq_line_id'], ['qty_current:sum'])
        return {item.id: measured for item, measured in groups}

    def _boq_line_values(self, boq_line, certified_before):
        """A certificate line as the bill item defines it.

        The same reading the by-hand onchange does, so an item picked one at
        a time and an item that arrived with its bill land identically.
        """
        self.ensure_one()
        rate = boq_line.unit_rate if self.billing_type == 'customer' \
            else (boq_line.cost_rate or boq_line.unit_rate)
        return {
            'boq_line_id': boq_line.id,
            'item_no': boq_line.item_no,
            'product_id': boq_line.product_id.id,
            'boq_line_description': boq_line.description,
            'work_type': boq_line.work_type,
            'uom_id': boq_line.uom_id.id,
            'wbs_id': boq_line.wbs_id.id,
            'boq_qty': boq_line.qty,
            'unit_rate': rate,
            'qty_previous': certified_before.get(boq_line.id, 0.0),
        }

    @api.onchange('boq_ids')
    def _onchange_boq_ids(self):
        # Everything is read through ``_origin``. While a form is open the
        # certificate is a record that does not exist yet, and Odoo hands an
        # unsaved record its x2many values as new records too - so the bill
        # picked here arrives as a copy of bill 35, not as bill 35, and it
        # matches nothing the lines point at. The origins are the real rows.
        bills = self.boq_ids._origin
        on_certificate = self.line_ids.boq_line_id._origin

        # Taking a bill off the certificate takes its items off with it -
        # but never an item someone has already measured. That one keeps its
        # figure and keeps its bill on the certificate; emptying the quantity
        # is what releases it.
        taken_off = on_certificate.boq_id - bills
        measured = taken_off.filtered(lambda bill: any(
            line.qty_current for line in self.line_ids
            if line.boq_line_id._origin.boq_id == bill))
        dropped = taken_off - measured
        if dropped:
            self.line_ids -= self.line_ids.filtered(
                lambda line: line.boq_line_id._origin.boq_id in dropped)
        if measured:
            self.boq_ids |= measured
            bills |= measured

        items = bills.line_ids.filtered(lambda item: not item.is_section)
        items -= on_certificate
        if items:
            # Assigning a recordset rather than a list of commands: on a
            # certificate that has not been saved yet, commands are applied
            # to an empty value and the lines already on the form would go.
            certified_before = self._certified_before(items)
            lines = self.line_ids
            for item in items:
                lines |= self.env['construction.ra.billing.line'].new(
                    self._boq_line_values(item, certified_before))
            self.line_ids = lines

        if measured:
            return {'warning': {
                'title': self.env._('Quantities already measured'),
                'message': self.env._(
                    'Items of %(bills)s already carry a quantity on this '
                    'certificate, so the bill stays on it. Empty those '
                    'quantities first to take it off.',
                    bills=', '.join(measured.mapped('display_name'))),
            }}


class ConstructionRABillingLine(models.Model):
    _inherit = 'construction.ra.billing.line'

    # What a certificate line is measured against is the bill item and its
    # description; a product record behind it is a convenience for the
    # invoice, and a surveyed sheet does not carry one for every item. The
    # base module makes it required, which stops a whole bill from being
    # laid out at once.
    product_id = fields.Many2one(string='Product / Service', required=False)

    #: The number the item carries on the bill of quantities. The site, the
    #: surveyor and the authority all call the item by this number rather
    #: than by its description, so the certificate has to read the same way
    #: the sheet does. It is filled from the item it measures, and typing it
    #: is the other way round: the item is looked up and pulled in.
    item_no = fields.Char(
        string='Item No.', index=True,
        help='The number of the item on the bill of quantities. Type a '
             'number here and the item it belongs to is filled in below.')

    #: The share of this item's amount that is actually paid out. A hundred
    #: is the whole of it, which is what a line is worth until someone says
    #: otherwise -- so a certificate nobody touches disburses exactly what it
    #: certifies.
    disbursement_percent = fields.Float(
        string='Disbursement %', default=100.0,
        help='How much of this item\'s amount is paid out. 100 is all of '
             'it; 80 on an amount of 100 disburses 80.')
    disbursement_amount = fields.Monetary(
        string='Disbursement Amount', compute='_compute_disbursement_amount',
        store=True, currency_field='currency_id',
        help='The amount at the disbursement percentage.')

    @api.depends('amount', 'disbursement_percent')
    def _compute_disbursement_amount(self):
        for line in self:
            line.disbursement_amount = \
                line.amount * line.disbursement_percent / 100.0

    #: How much of the item's disbursement the earlier certificates of this
    #: series have not taken yet -- a hundred less what they released. It is
    #: the ceiling this certificate is writing against, so the percentage
    #: being typed on this line is deliberately not counted: a fresh line
    #: carries the default hundred, and counting it would show nothing left
    #: on every line before anyone had decided anything.
    disbursement_percent_remaining = fields.Float(
        string='Remaining Disbursement %',
        compute='_compute_disbursement_percent_remaining',
        help='A hundred less the disbursement percentages the earlier '
             'approved certificates already released on this item. What '
             'this certificate releases is not taken off it.')

    def _disbursement_released_before(self):
        """What earlier certificates released on each item, per certificate.

        Read in one query per certificate rather than item by item: a
        certificate runs to hundreds of items and this is answered while
        someone waits on the form.
        """
        released = {}
        for billing in self.billing_id:
            items = self.filtered(
                lambda line: line.billing_id == billing).boq_line_id._origin
            if not items:
                continue
            domain = [
                ('boq_line_id', 'in', items.ids),
                ('billing_id.state', 'in', CONFIRMED_STATES),
                ('billing_id.billing_type', '=', billing.billing_type),
            ]
            # An unsaved certificate is not one of the earlier ones, and has
            # no id to exclude itself by.
            if billing._origin:
                domain.append(('billing_id', '!=', billing._origin.id))
            if billing.billing_type == 'subcontractor' \
                    and billing.subcontract_id:
                domain.append(('billing_id.subcontract_id', '=',
                               billing.subcontract_id._origin.id))
            groups = self.env['construction.ra.billing.line']._read_group(
                domain, ['boq_line_id'], ['disbursement_percent:sum'])
            for item, used in groups:
                released[(billing, item.id)] = used
        return released

    @api.depends('boq_line_id', 'billing_id.state', 'billing_id.billing_type',
                 'billing_id.subcontract_id')
    def _compute_disbursement_percent_remaining(self):
        released = self._disbursement_released_before()
        for line in self:
            item = line.boq_line_id._origin
            # Left unclamped on purpose: an item the earlier certificates
            # already released more than all of reads negative, and that is
            # the figure someone needs to see.
            line.disbursement_percent_remaining = 100.0 - released.get(
                (line.billing_id, item.id), 0.0)

    @api.onchange('boq_line_id')
    def _onchange_boq_line_item_no(self):
        """Keep the number in step with the item picked from the list."""
        if self.boq_line_id:
            self.item_no = self.boq_line_id.item_no

    @api.onchange('item_no')
    def _onchange_item_no(self):
        """Typing the number off the sheet pulls its item in.

        The surveyor works down a paper sheet that names items by number,
        not by description, so the number is the quickest way in. It is
        looked up among the bills the certificate is measured against -- or
        across the project's bills where none have been picked -- and only a
        single match fills the line: two items sharing a number is the sheet
        being ambiguous, and guessing between them would measure the wrong
        one.
        """
        number = (self.item_no or '').strip()
        if not number or self.boq_line_id.item_no == number:
            return
        billing = self.billing_id
        domain = [('item_no', '=', number), ('is_section', '=', False)]
        # On a form the certificate is a record that does not exist yet and
        # its x2many values arrive as copies, so the bills are read through
        # their origins -- the same reading ``_onchange_boq_ids`` does.
        bills = billing.boq_ids._origin
        if bills:
            domain.append(('boq_id', 'in', bills.ids))
        elif billing.project_id:
            domain.append(('boq_id.project_id', '=', billing.project_id.id))
        matches = self.env['construction.boq.line'].search(domain, limit=2)
        if len(matches) == 1:
            self.boq_line_id = matches
            # The same filling as picking it from the list: description,
            # unit, contract quantity, rate and what came before.
            self._onchange_boq_line_id()
            return
        where = ', '.join(bills.mapped('display_name')) or (
            billing.project_id.display_name or '')
        if not matches:
            message = self.env._(
                'No item numbered "%(number)s" on %(where)s. Check the '
                'number, or pick the item from the list.',
                number=number, where=where)
        else:
            message = self.env._(
                'More than one item on %(where)s is numbered "%(number)s", '
                'so pick the one meant from the list.',
                number=number, where=where)
        return {'warning': {
            'title': self.env._('Item not found'), 'message': message}}

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
