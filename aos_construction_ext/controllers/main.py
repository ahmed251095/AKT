import io

import xlsxwriter
from xlsxwriter.utility import xl_range

from odoo import http
from odoo.http import content_disposition, request


class ConstructionTenderSheet(http.Controller):
    """Excel export of the priced tender, the file the office actually bids with."""

    @http.route(
        '/construction/tender/<model("construction.tender"):tender>/pricing.xlsx',
        type='http', auth='user')
    def tender_pricing_sheet(self, tender, **kwargs):
        tender.check_access('read')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        self._write_sheet(workbook, tender)
        workbook.close()
        content = output.getvalue()
        output.close()
        filename = '%s.xlsx' % (tender.ref or tender.name or 'tender')
        return request.make_response(content, headers=[
            ('Content-Type',
             'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Length', len(content)),
            ('Content-Disposition', content_disposition(filename)),
        ])

    def _write_sheet(self, workbook, tender):
        _ = request.env._
        currency = tender.currency_id
        is_rtl = (request.env.context.get('lang') or '').startswith('ar')

        title = workbook.add_format({
            'bold': True, 'font_size': 14, 'align': 'center',
            'valign': 'vcenter'})
        header = workbook.add_format({
            'bold': True, 'bg_color': '#DDEBF7', 'border': 1,
            'align': 'center', 'valign': 'vcenter', 'text_wrap': True})
        text = workbook.add_format({'border': 1, 'valign': 'vcenter'})
        number = workbook.add_format({
            'border': 1, 'num_format': '#,##0.00', 'valign': 'vcenter'})
        percent = workbook.add_format({
            'border': 1, 'num_format': '0.00"%"', 'valign': 'vcenter'})
        total = workbook.add_format({
            'border': 1, 'bold': True, 'num_format': '#,##0.00',
            'bg_color': '#F2F2F2'})
        total_label = workbook.add_format({
            'border': 1, 'bold': True, 'bg_color': '#F2F2F2'})

        sheet = workbook.add_worksheet(_('Pricing'))
        if is_rtl:
            sheet.right_to_left()

        columns = [
            (_('No.'), 8), (_('Item No.'), 14), (_('Description'), 42),
            (_('Unit'), 10), (_('Quantity'), 12),
            (_('Dry Cost'), 14), (_('Operating Cost'), 14),
            (_('Base Cost'), 14), (_('Profit %'), 10),
            (_('Contingency %'), 12), (_('Administration %'), 14),
            (_('Expenses %'), 12), (_('Tax %'), 10),
            (_('Unit Rate'), 14), (_('Total'), 16),
        ]
        last_col = len(columns) - 1

        sheet.merge_range(0, 0, 0, last_col, tender.name or '', title)
        sheet.write(1, 0, _('Tender No.'), header)
        sheet.write(1, 1, tender.ref or '', text)
        sheet.write(1, 2, _('Client'), header)
        sheet.write(1, 3, tender.client_id.display_name or '', text)
        sheet.write(1, 4, _('Currency'), header)
        sheet.write(1, 5, currency.name or '', text)

        row = 3
        for index, (label, width) in enumerate(columns):
            sheet.set_column(index, index, width)
            sheet.write(row, index, label, header)
        sheet.set_row(row, 32)

        row += 1
        first_data_row = row
        for index, line in enumerate(tender.line_ids.sorted('sequence'), 1):
            if line.is_section:
                sheet.merge_range(row, 0, row, last_col,
                                  line.description or '', total_label)
                row += 1
                continue
            sheet.write_number(row, 0, index, number)
            sheet.write(row, 1, line.item_no or '', text)
            sheet.write(row, 2, line.description or '', text)
            sheet.write(row, 3, line.uom_id.name or '', text)
            sheet.write_number(row, 4, line.qty, number)
            sheet.write_number(row, 5, line.dry_cost, number)
            sheet.write_number(row, 6, line.operating_cost, number)
            sheet.write_number(row, 7, line.base_cost, number)
            sheet.write_number(row, 8, line.profit_percent, percent)
            sheet.write_number(row, 9, line.contingency_percent, percent)
            sheet.write_number(row, 10, line.admin_percent, percent)
            sheet.write_number(row, 11, line.expense_percent, percent)
            sheet.write_number(row, 12, line.tax_percent, percent)
            sheet.write_number(row, 13, line.unit_rate, number)
            sheet.write_number(row, 14, line.amount, number)
            row += 1

        sheet.write(row, 0, _('Total'), total_label)
        for column in range(1, last_col):
            sheet.write(row, column, '', total_label)
        if row > first_data_row:
            sheet.write_formula(
                row, last_col,
                '=SUM(%s)' % xl_range(
                    first_data_row, last_col, row - 1, last_col),
                total, tender.estimated_value)
        else:
            sheet.write_number(row, last_col, 0.0, total)
