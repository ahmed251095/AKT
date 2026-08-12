# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    construction_project_id = fields.Many2one('construction.project', string='Construction Project', index=True)
    construction_requisition_id = fields.Many2one('construction.material.requisition', string='Material Requisition', index=True)
    construction_subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract', index=True)


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    construction_project_id = fields.Many2one(
        related='order_id.construction_project_id', store=True, index=True,
        string='Construction Project')


class AccountMove(models.Model):
    _inherit = 'account.move'

    construction_project_id = fields.Many2one('construction.project', string='Construction Project', index=True)
    construction_billing_id = fields.Many2one('construction.ra.billing', string='Construction Certificate', index=True)
    construction_subcontract_id = fields.Many2one('construction.subcontract', string='Subcontract', index=True)


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    construction_project_id = fields.Many2one(
        related='move_id.construction_project_id', store=True, index=True,
        string='Construction Project')
