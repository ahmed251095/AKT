"""Give the certificate lines already on the system their item number.

The number is new on the certificate, so every line written before this
carries none -- and those are exactly the lines someone is reading against a
paper sheet that names items by number. It is read off the bill item each
line already measures, which is where it would have come from anyway.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    cr.execute("""
        UPDATE construction_ra_billing_line AS line
           SET item_no = item.item_no
          FROM construction_boq_line AS item
         WHERE line.boq_line_id = item.id
           AND item.item_no IS NOT NULL
           AND item.item_no <> ''
           AND line.item_no IS NULL
    """)
    _logger.info('aos_construction_ext: %s certificate line(s) took the item '
                 'number off the bill.', cr.rowcount)
