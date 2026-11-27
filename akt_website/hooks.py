from odoo import api, SUPERUSER_ID


def post_init(env):
    """Set up the parts the client may edit afterwards.

    Everything that must be re-applied on an upgrade as well lives in
    akt.website.setup.apply, which data/sync.xml calls on both. Only what
    would overwrite the client's own work is here, where it runs once.
    """
    if not hasattr(env, 'cr'):  # older signature: (cr, registry)
        env = api.Environment(env, SUPERUSER_ID, {})
    env['akt.website.setup'].first_install()
