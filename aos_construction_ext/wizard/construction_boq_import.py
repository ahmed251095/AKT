import base64
import io
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

from . import boq_sheet
from ..models import pricing

_logger = logging.getLogger(__name__)

#: The documents a priced sheet can be read into, and the field its items hang
#: off. Both carry the same item fields, so one reader fills either.
TARGETS = {
    'construction.boq': ('construction.boq.line', 'boq_id'),
    'construction.tender': ('construction.tender.line', 'tender_id'),
}

#: The sheet the office prices on. A workbook usually carries two more --
#: the same items net of tax, and at the association discount -- which are
#: worked out from this one and carry neither cost nor ratios.
PRICED_SHEET = 'شامل'

#: A rate is read as agreeing with the sheet within this many currency units.
RATE_TOLERANCE = 0.5


class ConstructionBoqImport(models.TransientModel):
    _name = 'construction.boq.import'
    _description = 'Import Priced Items from a Sheet'

    file = fields.Binary(string='Excel Sheet', required=True, attachment=False)
    filename = fields.Char(string='Filename')
    res_model = fields.Char(
        string='Document Model', required=True,
        default=lambda self: self.env.context.get('active_model'))
    res_id = fields.Integer(
        string='Document', required=True,
        default=lambda self: self.env.context.get('active_id'))

    rate_source = fields.Selection(
        [('ratios', 'Work the rate out from the ratios'),
         ('sheet', 'Take the rate as it stands in the sheet')],
        string='Rate', default='ratios', required=True,
        help='The ratios keep the items live: change a cost or a ratio later '
             'and the rate follows. Taking the rate as it stands matches the '
             'sheet to the piastre but leaves the item priced by hand.')
    mode = fields.Selection(
        [('append', 'Add to the items already there'),
         ('replace', 'Replace the items')],
        string='Existing Items', default='append', required=True)

    log = fields.Text(string='Result', readonly=True)
    state = fields.Selection(
        [('draft', 'Draft'), ('done', 'Done')], default='draft')

    # ------------------------------------------------------------------
    # The document being filled
    # ------------------------------------------------------------------
    def _document(self):
        if self.res_model not in TARGETS:
            raise UserError(self.env._(
                'A priced sheet is read into a bill of quantities or a '
                'tender, not into %s.', self.res_model))
        document = self.env[self.res_model].browse(self.res_id).exists()
        if not document:
            raise UserError(self.env._('The document is no longer there.'))
        return document

    # ------------------------------------------------------------------
    # Units
    # ------------------------------------------------------------------
    def _uom_map(self):
        """The office's unit names against the units on the system.

        A unit the system ships archived is brought back: an item measured in
        cubic metres cannot be stored against a unit nobody can pick.
        """
        mapping = {}
        revived = []
        for names, xmlid in boq_sheet.UOM_XMLIDS.items():
            uom = self.env.ref(xmlid, raise_if_not_found=False)
            if not uom:
                continue
            if not uom.active:
                uom.active = True
                revived.append(uom.display_name)
            for name in names:
                mapping[boq_sheet.normalise(name)] = uom
        return mapping, revived

    # ------------------------------------------------------------------
    # Reading
    # ------------------------------------------------------------------
    def _sheet_entries(self):
        try:
            import openpyxl
        except ImportError:
            raise UserError(self.env._(
                'Reading an Excel sheet needs the openpyxl library, which is '
                'not installed on this server. Install python3-openpyxl and '
                'restart Odoo.'))
        try:
            workbook = openpyxl.load_workbook(
                io.BytesIO(base64.b64decode(self.file)), data_only=True)
        except Exception as error:
            _logger.info('construction.boq.import: unreadable workbook: %s',
                         error)
            # The reason travels with the message: a file saved in the old
            # .xls format and a server whose openpyxl cannot open any file
            # both fail here, and they are fixed in different places.
            raise UserError(self.env._(
                'This file could not be opened as an Excel workbook: %s. '
                'Save it as .xlsx and try again.', error))
        wanted = boq_sheet.normalise(PRICED_SHEET)
        sheet = next(
            (candidate for candidate in workbook
             if boq_sheet.normalise(candidate.title) == wanted),
            workbook[workbook.sheetnames[0]])
        try:
            return sheet.title, boq_sheet.read(sheet)
        except LookupError:
            raise UserError(self.env._(
                'No row in "%s" names the columns, so there is nothing to '
                'read it by. The sheet needs a header row carrying at least '
                'a description column and a quantity column.', sheet.title))

    # ------------------------------------------------------------------
    # Writing
    # ------------------------------------------------------------------
    def _line_values(self, entry, sequence, uoms, unknown_uoms):
        values = {
            'sequence': sequence,
            'item_no': entry['item_no'],
            'description': entry['description'],
            'is_section': entry['is_section'],
        }
        if entry['is_section']:
            return values

        uom = uoms.get(entry['uom'])
        if entry['uom'] and not uom:
            unknown_uoms.add(entry['uom'])
        values.update({
            'uom_id': uom.id if uom else False,
            'qty': entry['qty'],
        })
        if self.rate_source == 'sheet':
            # The sheet's own figures stand, and the item carries no
            # breakdown for anything to be derived from.
            values.update({
                'pricing_method': 'manual',
                'dry_cost': entry['cost'],
                'cost_rate': entry['cost'],
                'unit_rate': entry['rate'],
            })
            return values
        values.update({
            'pricing_method': 'margin',
            'dry_cost': entry['cost'],
            'operating_cost': 0.0,
            'authority_percent': entry['authority'],
            'admin_percent': entry['admin'],
            'contingency_percent': entry['contingency'],
            'profit_percent': entry['profit'],
            'expense_percent': 0.0,
            # Typed straight in: the sheet carries a rate, not a tax record.
            # ``tax_ids`` is left out of the values on purpose - setting it
            # would send the tax ratio back to what the taxes say.
            'tax_percent': entry['tax'],
        })
        return values

    def action_import(self):
        self.ensure_one()
        document = self._document()
        line_model, parent_field = TARGETS[self.res_model]
        sheet_name, entries = self._sheet_entries()
        if not entries:
            raise UserError(self.env._(
                'Sheet "%s" carries no items under its header row.',
                sheet_name))

        uoms, revived = self._uom_map()
        unknown_uoms = set()
        lines = self.env[line_model].with_context(
            **{pricing.KEEP_PRICING_MODE: True})

        if self.mode == 'replace':
            document.line_ids.unlink()

        sequence = max(document.line_ids.mapped('sequence') or [0]) + 10
        created = lines.create([
            dict(self._line_values(entry, sequence + index * 10,
                                   uoms, unknown_uoms),
                 **{parent_field: document.id})
            for index, entry in enumerate(entries)])

        self.log = self._result(entries, created, sheet_name, unknown_uoms,
                                revived)
        self.state = 'done'
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ------------------------------------------------------------------
    # What the import actually did
    # ------------------------------------------------------------------
    def _result(self, entries, created, sheet_name, unknown_uoms, revived):
        items = [entry for entry in entries if not entry['is_section']]
        sections = len(entries) - len(items)
        report = [
            self.env._('Read from sheet "%s".', sheet_name),
            self.env._('%(items)s items and %(sections)s section headings '
                       'written.', items=len(items), sections=sections),
        ]

        sheet_total = sum(entry['total'] for entry in items)
        written_total = sum(created.filtered(
            lambda line: not line.is_section).mapped('amount'))
        report.append(self.env._(
            'Sheet total %(sheet)s, written total %(written)s.',
            sheet=round(sheet_total, 2), written=round(written_total, 2)))

        if self.rate_source == 'ratios':
            off = self._rates_off_the_sheet(items, created)
            if off:
                report.append(self.env._(
                    '%s items came out at a rate the sheet does not carry. '
                    'The ratios on those rows do not add up to the rate '
                    'beside them; the rate the ratios give is what was '
                    'written. Rows: %s',
                    len(off), ', '.join(str(row) for row in off[:15])))
            else:
                report.append(self.env._(
                    'Every rate worked out from the ratios matches the rate '
                    'in the sheet.'))

        if unknown_uoms:
            report.append(self.env._(
                'No unit on the system answers to: %s. Those items were '
                'written without one.', ', '.join(sorted(unknown_uoms))))
        if revived:
            report.append(self.env._(
                'Units brought back out of the archive so the items could '
                'use them: %s.', ', '.join(revived)))
        return '\n'.join(report)

    def _rates_off_the_sheet(self, items, created):
        """Rows whose written rate is not the one the sheet shows."""
        written = [line for line in created if not line.is_section]
        off = []
        for entry, line in zip(items, written):
            if not entry['rate']:
                continue
            if abs(line.unit_rate - entry['rate']) > RATE_TOLERANCE:
                off.append(entry['row'])
        return off
