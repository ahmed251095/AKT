"""Freezing a document once it has been approved.

The same shape turns up on the bill of quantities, its items, the payment
certificates and their lines, so the rule lives here once.

What it has to get right is the difference between a person editing the
document and Odoo keeping its own figures up to date. Computed and related
fields are written constantly - a subcontract is signed and the assigned
quantity on a bill item moves, an expense is approved and a total shifts -
and refusing those writes would not protect the document, it would stop it
from recomputing. So only the fields someone typed are guarded.
"""
from odoo.exceptions import UserError

# Chatter, followers and activities are not the document.
_SIDE_CHANNELS = ('message_', 'activity_', 'rating_', 'website_message_')


def typed_fields(records, vals, unlocked=()):
    """The field names in ``vals`` a person is actually setting.

    ``unlocked`` names the fields the workflow itself writes - the state,
    and whatever the buttons stamp on the record as it moves along.
    """
    fields = records._fields
    return [
        name for name in vals
        if name in fields
        and not fields[name].compute
        and not fields[name].related
        and name not in unlocked
        and not name.startswith(_SIDE_CHANNELS)
    ]


def refuse(records, message):
    """Raise ``message`` naming the records that are frozen."""
    raise UserError('%s\n%s' % (
        message,
        '\n'.join('- %s' % record.display_name for record in records),
    ))
