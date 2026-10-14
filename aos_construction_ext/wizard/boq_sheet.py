"""Reading a priced bill of quantities out of the estimation office's workbook.

The office prices in Excel and has done for years: one row per item, the cost
rate in one column and the ratios that make up the selling rate in the next
few. The sheet is the source document, so the reader is written around the
shape the office already uses rather than around an export format nobody would
fill in by hand.

Three things make a sheet readable:

* the header row is found by its labels, not by its position, so the notes and
  the title above it do not have to be removed first;
* a row carrying a quantity is an item, a row carrying only text is a section
  heading, and anything else -- the conditions, the totals at the foot -- is
  skipped;
* ratios written as fractions (0.03) and as percentages (3) both arrive as 3,
  because both spellings turn up in the same workbook.
"""

#: Every spelling of a column heading seen in the office's sheets, against the
#: name this module knows the column by. Matched after normalisation, so the
#: alef/ya/ta-marbuta variants and stray spaces do not need listing.
COLUMN_LABELS = {
    'item_no': ('م', 'م.', 'بند', 'رقم البند', 'كود'),
    'description': ('وصف الاعمال', 'الوصف', 'بيان الاعمال', 'البيان',
                    'وصف البند', 'الاعمال'),
    'uom': ('الوحده', 'وحده', 'وحده القياس'),
    'qty': ('الكميه', 'كميه', 'الكميات'),
    'cost': ('سعر تكلفه', 'سعر التكلفه', 'التكلفه', 'تكلفه', 'سعر التكلفه للوحده'),
    'authority': ('نسبه جهه', 'نسبه الجهه', 'جهه'),
    'admin': ('نسبه تشغيل اداره', 'نسبه اداره', 'نسبه الاداره',
              'تشغيل واداره', 'نسبه تشغيل وادره'),
    'contingency': ('نسبه اضافيه', 'نسبه اضافيات', 'اضافيه'),
    'profit': ('هامش ربح', 'هامش الربح', 'نسبه الربح', 'ربح'),
    'tax': ('ضرائب', 'ضريبه', 'الضرائب', 'الضريبه'),
    'rate': ('الفئه', 'فئه', 'سعر الوحده', 'الفئه شامله الضريبه'),
    'total': ('الاجمالي', 'اجمالي', 'الاجمالى'),
}

#: The columns a sheet has to carry before it can be read at all.
REQUIRED_COLUMNS = ('description', 'qty')

#: How far down the sheet the header row is looked for.
HEADER_SEARCH_ROWS = 25

#: Unit names as the office writes them, against the Odoo unit they mean.
#: Resolved by external id so a renamed unit still matches.
UOM_XMLIDS = {
    ('م2', 'م٢', 'متر مربع', 'م مربع', 'm2'): 'uom.product_uom_square_meter',
    ('م3', 'م٣', 'متر مكعب', 'م مكعب', 'm3'): 'uom.product_uom_cubic_meter',
    ('م.ط', 'م.ط.', 'م ط', 'مط', 'متر طولي', 'متر طول', 'متر', 'م'): 'uom.product_uom_meter',
    ('طن', 'ton'): 'uom.product_uom_ton',
    ('كجم', 'كيلو', 'كيلو جرام', 'kg'): 'uom.product_uom_kgm',
    ('لتر', 'l'): 'uom.product_uom_litre',
    ('عدد', 'وحده', 'قطعه', 'مقطوعيه', 'جمله', 'unit'): 'uom.product_uom_unit',
}

#: Arabic letters that are written more than one way for the same word.
_LETTERS = str.maketrans({
    'أ': 'ا', 'إ': 'ا', 'آ': 'ا', 'ٱ': 'ا',
    'ى': 'ي', 'ئ': 'ي',
    'ة': 'ه',
    'ـ': '',
    'ً': '', 'ٌ': '', 'ٍ': '', 'َ': '', 'ُ': '',
    'ِ': '', 'ّ': '', 'ْ': '',
})


def normalise(value):
    """One spelling of a label, so the sheets do not have to agree on one."""
    if value is None:
        return ''
    text = str(value).replace('\n', ' ').replace(' ', ' ')
    text = text.translate(_LETTERS).strip().lower()
    return ' '.join(text.split())


def _label_index():
    return {normalise(label): column
            for column, labels in COLUMN_LABELS.items()
            for label in labels}


def ratio(value):
    """A ratio as a percentage, whichever way the sheet spells it.

    ``0.03`` and ``3`` are the same three per cent: the first is how a
    spreadsheet formula carries it, the second how someone types it. A ratio
    of a whole one is read as one per cent -- a hundred per cent ratio would
    leave nothing to cover the cost, and no sheet carries one.
    """
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return 0.0
    return float(value) * 100.0 if 0.0 < value < 1.0 else float(value)


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0.0
    return float(value)


def find_header(sheet):
    """The row the columns are named on, and where each one sits.

    Returns ``(row_number, {column: index})``, or ``(0, {})`` when no row in
    the top of the sheet names the columns this reader needs.
    """
    labels = _label_index()
    for row_number, row in enumerate(
            sheet.iter_rows(min_row=1, max_row=HEADER_SEARCH_ROWS,
                            values_only=True), start=1):
        found = {}
        for index, cell in enumerate(row):
            column = labels.get(normalise(cell))
            if column and column not in found:
                found[column] = index
        if all(column in found for column in REQUIRED_COLUMNS):
            return row_number, found
    return 0, {}


def read(sheet):
    """The rows of ``sheet`` as items and section headings, in sheet order.

    Raises ``LookupError`` when the sheet carries no header row this reader
    recognises -- there is nothing to guess at from a sheet of bare numbers.
    """
    header_row, columns = find_header(sheet)
    if not columns:
        raise LookupError(sheet.title)

    def cell(row, column):
        index = columns.get(column)
        return row[index] if index is not None and index < len(row) else None

    entries = []
    for row_number, row in enumerate(
            sheet.iter_rows(min_row=header_row + 1, values_only=True),
            start=header_row + 1):
        description = normalise(cell(row, 'description'))
        if not description:
            # The conditions at the top and the totals at the foot sit in the
            # item-number column with nothing beside them.
            continue
        quantity = cell(row, 'qty')
        raw_description = str(cell(row, 'description')).strip()
        item_no = cell(row, 'item_no')
        item_no = str(item_no).strip() if item_no not in (None, '') else ''
        if not isinstance(quantity, (int, float)) or isinstance(quantity, bool) \
                or not quantity:
            entries.append({
                'row': row_number,
                'is_section': True,
                'item_no': item_no,
                'description': raw_description,
            })
            continue
        entries.append({
            'row': row_number,
            'is_section': False,
            'item_no': item_no,
            'description': raw_description,
            'uom': normalise(cell(row, 'uom')),
            'qty': float(quantity),
            'cost': number(cell(row, 'cost')),
            'authority': ratio(cell(row, 'authority')),
            'admin': ratio(cell(row, 'admin')),
            'contingency': ratio(cell(row, 'contingency')),
            'profit': ratio(cell(row, 'profit')),
            'tax': ratio(cell(row, 'tax')),
            'rate': number(cell(row, 'rate')),
            'total': number(cell(row, 'total')),
        })
    return entries
