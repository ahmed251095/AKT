# -*- coding: utf-8 -*-
from odoo import Command


def post_init_hook(env):
    """Assign system administrators to the Construction Administrator group."""
    admin_group = env.ref('aos_construction_management.group_construction_admin', raise_if_not_found=False)
    system_group = env.ref('base.group_system', raise_if_not_found=False)
    if not admin_group or not system_group:
        return
    users = env['res.users'].sudo().search([('group_ids', 'in', system_group.id)])
    if users:
        users.write({'group_ids': [Command.link(admin_group.id)]})
