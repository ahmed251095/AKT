"""Carry the old build-up flag onto the pricing method that replaced it.

``use_pricing_formula`` was a yes/no: the rate is built up, or it is typed.
The method it became says the same thing and one more -- that the ratios can
be read as shares of the selling price instead. Items already on the system
keep exactly the pricing they had.
"""
import logging

_logger = logging.getLogger(__name__)

TABLES = ('construction_tender_line', 'construction_boq_line')


def migrate(cr, version):
    for table in TABLES:
        cr.execute("""
            SELECT 1 FROM information_schema.columns
             WHERE table_name = %s AND column_name = 'use_pricing_formula'
        """, (table,))
        if not cr.fetchone():
            continue
        cr.execute("""
            UPDATE {table}
               SET pricing_method = CASE WHEN use_pricing_formula
                                         THEN 'buildup' ELSE 'manual' END
             WHERE pricing_method IS DISTINCT FROM
                   (CASE WHEN use_pricing_formula
                         THEN 'buildup' ELSE 'manual' END)
        """.format(table=table))
        _logger.info('aos_construction_ext: %s %s item(s) kept their pricing '
                     'mode.', cr.rowcount, table)
