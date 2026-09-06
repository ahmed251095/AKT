from odoo import api, fields, models


class ConstructionDocument(models.Model):
    """One paper in a tender file or a project file.

    Keeping the checklist as records rather than loose attachments is what lets
    the system answer two questions the office asks every week: is the bid file
    complete, and is any certificate about to expire.
    """
    _name = 'construction.document'
    _description = 'Construction Document'
    _order = 'file_type, sequence, id'

    tender_id = fields.Many2one(
        'construction.tender', string='Tender', ondelete='cascade', index=True)
    project_id = fields.Many2one(
        'construction.project', string='Project', ondelete='cascade',
        index=True)
    document_type_id = fields.Many2one(
        'construction.document.type', string='Document Type', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    file_type = fields.Selection(
        related='document_type_id.file_type', string='File', store=True)
    is_required = fields.Boolean(string='Required', default=True)
    is_submitted = fields.Boolean(string='Provided')
    submission_date = fields.Date(string='Provided On')
    issue_date = fields.Date(string='Issue Date')
    expiry_date = fields.Date(string='Expiry Date')
    is_expired = fields.Boolean(
        string='Expired', compute='_compute_is_expired', store=True)
    reference = fields.Char(string='Reference')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'construction_document_attachment_rel',
        'document_id', 'attachment_id', string='Files')
    attachment_count = fields.Integer(
        string='Files', compute='_compute_attachment_count')
    note = fields.Text(string='Notes')

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        today = fields.Date.context_today(self)
        for document in self:
            document.is_expired = bool(
                document.expiry_date and document.expiry_date < today)

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for document in self:
            document.attachment_count = len(document.attachment_ids)

    @api.depends('document_type_id', 'tender_id', 'project_id')
    def _compute_display_name(self):
        for document in self:
            document.display_name = document.document_type_id.name or ''

    @api.onchange('attachment_ids')
    def _onchange_attachment_ids(self):
        """Attaching the paper is what marks it provided."""
        if self.attachment_ids and not self.is_submitted:
            self.is_submitted = True
            self.submission_date = fields.Date.context_today(self)
