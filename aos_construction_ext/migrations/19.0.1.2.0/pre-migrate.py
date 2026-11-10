# -*- coding: utf-8 -*-
"""Keep contract values that were typed in before the field became computed.

``contract_value`` turns into a stored computed field in this version: the
total of the project's approved BOQs. Projects that already carry a figure
somebody entered by hand are switched onto the manual override so the
recompute does not wipe it. Projects left at zero pick up their BOQ total.
"""


def migrate(cr, version):
    cr.execute("""
        ALTER TABLE construction_project
            ADD COLUMN IF NOT EXISTS contract_value_manual numeric,
            ADD COLUMN IF NOT EXISTS contract_value_is_manual boolean
    """)
    cr.execute("""
        UPDATE construction_project
           SET contract_value_manual = contract_value,
               contract_value_is_manual = true
         WHERE COALESCE(contract_value, 0) != 0
           AND contract_value_manual IS NULL
    """)
    cr.execute("""
        UPDATE construction_project
           SET contract_value_is_manual = false
         WHERE contract_value_is_manual IS NULL
    """)
