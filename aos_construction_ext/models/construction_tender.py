from odoo import api, fields, models
from odoo.exceptions import UserError

from . import pricing

#: Tender dates that raise a reminder activity, with the flag that stops the
#: reminder from being raised twice for the same date.
REMINDER_DATES = [
    ('submission_deadline', 'reminder_submission_sent', 'Submission deadline'),
    ('envelope_opening_date', 'reminder_envelope_sent', 'Envelope opening'),
    ('award_decision_date', 'reminder_award_sent', 'Award decision'),
]


class ConstructionTender(models.Model):
    _inherit = 'construction.tender'

    # ------------------------------------------------------------------
    # Operation identity
    # ------------------------------------------------------------------
    authority_type_id = fields.Many2one(
        'construction.authority.type', string='Authority Type',
        help='Endowment, agricultural company, ministry, private owner... '
             'It drives the paperwork and the bid bond the client expects.')
    operation_duration_days = fields.Integer(
        string='Operation Duration (days)',
        help='Execution period the tender conditions allow, counted from the '
             'site handover.')
    envelope_opening_date = fields.Datetime(
        string='Envelope Opening',
        help='When the client opens the envelopes. Later than the submission '
             'deadline.')
    award_decision_date = fields.Datetime(
        string='Award Decision',
        help='When the client is expected to announce the award.')

    financial_responsible_id = fields.Many2one(
        'res.users', string='Finance Responsible',
        help='Who owns the financial envelope and the bond for this tender.')
    technical_office_user_id = fields.Many2one(
        'res.users', string='Technical Office Reviewer')
    technical_office_opinion = fields.Text(
        string='Technical Office Opinion',
        help='Whether the technical office recommends bidding, and on what '
             'terms.')
    technical_review_date = fields.Date(string='Technical Review Date')

    # ------------------------------------------------------------------
    # Tender document (conditions booklet)
    # ------------------------------------------------------------------
    tender_doc_price = fields.Monetary(
        string='Tender Document Fee', currency_field='currency_id',
        help='What the conditions booklet costs to buy from the client.')
    tender_doc_value = fields.Monetary(
        string='Declared Operation Value', currency_field='currency_id',
        help='Value the client states in the tender announcement.')
    tender_doc_purchased = fields.Boolean(
        string='Booklet Purchased', copy=False)
    tender_doc_purchase_date = fields.Date(
        string='Purchase Date', copy=False)
    tender_doc_payment_id = fields.Many2one(
        'account.payment', string='Fee Payment', copy=False,
        help='The payment that settled the booklet fee.')

    # ------------------------------------------------------------------
    # Bid bond
    # ------------------------------------------------------------------
    bid_bond_required = fields.Boolean(string='Bid Bond Required', default=True)
    bid_bond_percent = fields.Float(
        string='Bid Bond (%)', default=lambda self:
        self.env.company.construction_bid_bond_percent)
    bid_bond_amount = fields.Monetary(
        string='Bid Bond Amount', currency_field='currency_id',
        compute='_compute_bid_bond_amount', store=True, readonly=False)
    bid_bond_type = fields.Selection(
        [('cash', 'Cash Deposit'),
         ('cheque', 'Certified Cheque'),
         ('letter_guarantee', 'Letter of Guarantee')],
        string='Bond Instrument', default='letter_guarantee')
    bid_bond_bank_id = fields.Many2one('res.bank', string='Issuing Bank')
    bid_bond_ref = fields.Char(string='Bond Reference')
    bid_bond_issue_date = fields.Date(string='Bond Issue Date')
    bid_bond_expiry_date = fields.Date(string='Bond Expiry Date')
    bid_bond_return_date = fields.Date(string='Bond Release Date', copy=False)
    bid_bond_state = fields.Selection(
        [('not_required', 'Not Required'),
         ('to_issue', 'To Issue'),
         ('issued', 'Issued'),
         ('held', 'Held by Client'),
         ('released', 'Released'),
         ('forfeited', 'Forfeited')],
        string='Bond Status', default='to_issue', copy=False, tracking=True)

    # ------------------------------------------------------------------
    # Management approval
    # ------------------------------------------------------------------
    approval_user_id = fields.Many2one(
        'res.users', string='Approved By', readonly=True, copy=False)
    approval_date = fields.Datetime(
        string='Approval Date', readonly=True, copy=False)
    rejection_reason = fields.Text(
        string='Rejection Reason', readonly=True, copy=False)
    requested_budget = fields.Monetary(
        string='Requested Budget', currency_field='currency_id',
        help='Cash the tender needs up front: booklet fee, bond and study '
             'costs. This is what management approves.')
    requested_engineer_ids = fields.Many2many(
        'res.users', 'construction_tender_requested_engineer_rel',
        'tender_id', 'user_id', string='Requested Engineers',
        help='Engineers the technical office asks to be freed for the study.')

    # ------------------------------------------------------------------
    # Document checklist
    # ------------------------------------------------------------------
    document_ids = fields.One2many(
        'construction.document', 'tender_id', string='Required Documents')
    # Stored so the bid-file state can be filtered on and reported, which is
    # the whole point of tracking it.
    document_count = fields.Integer(
        string='Documents', compute='_compute_document_status', store=True)
    document_missing_count = fields.Integer(
        string='Missing Documents', compute='_compute_document_status',
        store=True)
    document_progress = fields.Float(
        string='Documents Ready (%)', compute='_compute_document_status',
        store=True)
    technical_file_ready = fields.Boolean(
        string='Technical File Ready', compute='_compute_document_status',
        store=True)
    financial_file_ready = fields.Boolean(
        string='Financial File Ready', compute='_compute_document_status',
        store=True)

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------
    reminder_days = fields.Integer(
        string='Remind Before (days)', default=lambda self:
        self.env.company.construction_reminder_days)
    reminder_submission_sent = fields.Boolean(copy=False)
    reminder_envelope_sent = fields.Boolean(copy=False)
    reminder_award_sent = fields.Boolean(copy=False)

    state = fields.Selection(
        selection_add=[
            ('draft',),
            ('pending_approval', 'Waiting Management Approval'),
            ('rejected', 'Rejected by Management'),
            ('lost',),
            ('bond_pending', 'Lost - Bond Not Released'),
        ],
        ondelete={
            'pending_approval': 'set default',
            'rejected': 'set default',
            'bond_pending': 'set default',
        })

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('bid_bond_percent', 'estimated_value', 'tender_doc_value',
                 'bid_bond_required')
    def _compute_bid_bond_amount(self):
        for tender in self:
            if not tender.bid_bond_required:
                tender.bid_bond_amount = 0.0
                continue
            # The client sets the bond on the value it announced; we fall back
            # on our own estimate while that value is still unknown.
            basis = tender.tender_doc_value or tender.estimated_value
            tender.bid_bond_amount = basis * tender.bid_bond_percent / 100.0

    @api.depends('document_ids.is_submitted', 'document_ids.is_required',
                 'document_ids.file_type')
    def _compute_document_status(self):
        for tender in self:
            documents = tender.document_ids
            required = documents.filtered('is_required')
            missing = required.filtered(lambda d: not d.is_submitted)
            tender.document_count = len(documents)
            tender.document_missing_count = len(missing)
            tender.document_progress = (
                100.0 * (len(required) - len(missing)) / len(required)
                if required else 0.0)
            tender.technical_file_ready = not missing.filtered(
                lambda d: d.file_type == 'technical')
            tender.financial_file_ready = not missing.filtered(
                lambda d: d.file_type in ('financial', 'legal'))

    # ------------------------------------------------------------------
    # Onchanges
    # ------------------------------------------------------------------
    @api.onchange('authority_type_id')
    def _onchange_authority_type_id(self):
        authority = self.authority_type_id
        if authority.default_bid_bond_percent:
            self.bid_bond_percent = authority.default_bid_bond_percent
        if authority.is_government:
            self.bid_bond_required = True

    @api.onchange('bid_bond_required')
    def _onchange_bid_bond_required(self):
        self.bid_bond_state = 'to_issue' if self.bid_bond_required \
            else 'not_required'

    # ------------------------------------------------------------------
    # Approval cycle
    # ------------------------------------------------------------------
    def action_request_approval(self):
        """Ask management to open the operation.

        Nothing is spent before this is answered: the booklet fee and the bond
        both wait for the approval.
        """
        for tender in self:
            if tender.state != 'draft':
                raise UserError(self.env._(
                    'Only a draft tender can be sent for approval.'))
            if not tender.client_id:
                raise UserError(self.env._(
                    'Set the tendering authority before asking for approval.'))
            if not tender.submission_deadline:
                raise UserError(self.env._(
                    'Set the submission deadline before asking for approval.'))
            tender.state = 'pending_approval'
            tender._notify_management()
        return True

    def action_approve(self):
        for tender in self:
            if tender.state != 'pending_approval':
                raise UserError(self.env._(
                    'Only a tender waiting for approval can be approved.'))
            tender.write({
                'state': 'in_progress',
                'approval_user_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
                'rejection_reason': False,
            })
            tender._close_approval_activities()
            tender.message_post(body=self.env._(
                'Opening approved. Budget released: %(budget)s.',
                budget=tender.requested_budget))
        return True

    def action_open_reject_wizard(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Reject Tender'),
            'res_model': 'construction.tender.reject',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tender_id': self.id},
        }

    def action_reject(self, reason=None):
        for tender in self:
            if tender.state != 'pending_approval':
                raise UserError(self.env._(
                    'Only a tender waiting for approval can be rejected.'))
            tender.write({
                'state': 'rejected',
                'rejection_reason': reason,
                'approval_user_id': self.env.user.id,
                'approval_date': fields.Datetime.now(),
            })
            tender._close_approval_activities()
            tender.message_post(body=self.env._(
                'Opening rejected. Reason: %s', reason or ''))
        return True

    def _notify_management(self):
        """Raise a to-do on every construction manager."""
        self.ensure_one()
        group = self.env.ref(
            'aos_construction_ext.group_construction_dept_management',
            raise_if_not_found=False)
        users = group.all_user_ids if group else self.env['res.users']
        for user in users:
            self.activity_schedule(
                'aos_construction_ext.mail_activity_type_tender_approval',
                user_id=user.id,
                summary=self.env._('Approve opening of tender %s', self.name),
                note=self.env._(
                    'Requested budget: %(budget)s. Submission deadline: '
                    '%(deadline)s.',
                    budget=self.requested_budget,
                    deadline=self.submission_deadline or '-'))

    def _close_approval_activities(self):
        self.activity_feedback(
            ['aos_construction_ext.mail_activity_type_tender_approval'],
            feedback=self.env._('Answered by management.'))

    # ------------------------------------------------------------------
    # Tender document purchase
    # ------------------------------------------------------------------
    def action_buy_tender_document(self):
        """Record that the conditions booklet was bought."""
        for tender in self:
            if tender.state in ('draft', 'pending_approval', 'rejected'):
                raise UserError(self.env._(
                    'The booklet fee can only be spent after management has '
                    'approved opening the tender.'))
            tender.write({
                'tender_doc_purchased': True,
                'tender_doc_purchase_date': fields.Date.context_today(tender),
            })
            tender.message_post(body=self.env._(
                'Conditions booklet purchased for %s.', tender.tender_doc_price))
        return True

    def action_register_tender_doc_payment(self):
        """Open a prefilled outbound payment for the booklet fee."""
        self.ensure_one()
        if not self.tender_doc_price:
            raise UserError(self.env._('Set the tender document fee first.'))
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Tender Document Fee'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_partner_id': self.client_id.id,
                'default_amount': self.tender_doc_price,
                'default_currency_id': self.currency_id.id,
                'default_memo': self.env._(
                    'Tender document fee - %s', self.name),
            },
        }

    # ------------------------------------------------------------------
    # Pricing sheet
    # ------------------------------------------------------------------
    def action_print_pricing_sheet(self):
        """Download the priced schedule the bid is built from."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/construction/tender/%s/pricing.xlsx' % self.id,
            'target': 'self',
        }

    def action_apply_company_ratios(self):
        """Re-apply the company ratios to every item of the tender."""
        for tender in self:
            tender.line_ids.action_apply_company_ratios()
        return True

    # ------------------------------------------------------------------
    # Documents checklist
    # ------------------------------------------------------------------
    def action_load_standard_documents(self):
        """Pull the standard checklist onto the tender."""
        Document = self.env['construction.document']
        types = self.env['construction.document.type'].search([
            ('scope', 'in', ('tender', 'both')),
        ])
        for tender in self:
            existing = tender.document_ids.document_type_id
            for doc_type in types - existing:
                Document.create({
                    'tender_id': tender.id,
                    'document_type_id': doc_type.id,
                    'is_required': doc_type.is_default_required,
                })
        return True

    # ------------------------------------------------------------------
    # Submission
    # ------------------------------------------------------------------
    def action_submit(self):
        """Refuse to submit a bid whose file is not complete."""
        for tender in self:
            if tender.state != 'in_progress':
                raise UserError(self.env._(
                    'Only a tender the management has approved and the '
                    'technical office is studying can be submitted.'))
            if tender.document_missing_count:
                missing = tender.document_ids.filtered(
                    lambda d: d.is_required and not d.is_submitted)
                raise UserError(self.env._(
                    'These required documents are still missing:\n%s',
                    '\n'.join('- %s' % d.display_name for d in missing)))
            expired = tender.document_ids.filtered('is_expired')
            if expired:
                raise UserError(self.env._(
                    'These documents have expired:\n%s',
                    '\n'.join('- %s' % d.display_name for d in expired)))
            if tender.bid_bond_required and \
                    tender.bid_bond_state not in ('issued', 'held'):
                raise UserError(self.env._(
                    'The bid bond has to be issued before the bid is '
                    'submitted.'))
            if not tender.line_ids:
                raise UserError(self.env._(
                    'Price the tender items before submitting.'))
        result = super().action_submit()
        for tender in self:
            if tender.bid_bond_state == 'issued':
                tender.bid_bond_state = 'held'
        return result

    # ------------------------------------------------------------------
    # Award / loss
    # ------------------------------------------------------------------
    def action_mark_won(self):
        result = super().action_mark_won()
        for tender in self:
            tender._propagate_pricing_to_boq()
            tender._propagate_to_project()
        return result

    def _propagate_pricing_to_boq(self):
        """Carry the build-up figures onto the BOQ the base module created.

        The base module copies tender items into an initial BOQ but only knows
        about the plain rates, so the cost breakdown would be lost exactly when
        the site starts needing it.
        """
        self.ensure_one()
        boq = self.env['construction.boq'].search(
            [('project_id', '=', self.project_id.id)], order='id', limit=1)
        if not boq:
            return
        tender_lines = self.line_ids.sorted('sequence')
        boq_lines = boq.line_ids.sorted('sequence')
        if len(tender_lines) != len(boq_lines):
            # Someone edited the BOQ already; match on description instead of
            # guessing, and leave unmatched lines alone.
            for boq_line in boq_lines:
                match = tender_lines.filtered(
                    lambda t: t.description == boq_line.description)[:1]
                if match:
                    boq_line.write(self._pricing_values(match))
            return
        for tender_line, boq_line in zip(tender_lines, boq_lines):
            boq_line.write(self._pricing_values(tender_line))

    @staticmethod
    def _pricing_values(tender_line):
        values = {field: tender_line[field]
                  for field in pricing.PRICING_COPY_FIELDS}
        # The rates travel with the breakdown. Items priced by hand carry no
        # breakdown to rebuild them from, and would otherwise land at zero.
        values['cost_rate'] = tender_line.cost_rate
        values['unit_rate'] = tender_line.unit_rate
        values['tender_line_id'] = tender_line.id
        return values

    def _propagate_to_project(self):
        self.ensure_one()
        project = self.project_id
        if not project:
            return
        values = {
            'authority_type_id': self.authority_type_id.id,
            'financial_responsible_id': self.financial_responsible_id.id,
        }
        if self.operation_duration_days and not project.end_date:
            values['contract_duration_days'] = self.operation_duration_days
        project.write(values)

    def action_lose(self):
        """A lost tender stays open until the bid bond comes back."""
        holding = self.filtered(
            lambda t: t.bid_bond_required
            and t.bid_bond_state in ('issued', 'held'))
        released = self - holding
        result = True
        if released:
            result = super(ConstructionTender, released).action_lose()
        for tender in holding:
            tender.state = 'bond_pending'
            tender.message_post(body=self.env._(
                'Tender lost. Kept open until the bid bond of %s is released.',
                tender.bid_bond_amount))
        return result

    def action_bond_released(self):
        """Accounting confirms the bond came back, so the file can close."""
        for tender in self:
            tender.write({
                'bid_bond_state': 'released',
                'bid_bond_return_date': fields.Date.context_today(tender),
            })
            if tender.state == 'bond_pending':
                tender.state = 'lost'
            tender.message_post(body=self.env._('Bid bond released.'))
        return True

    def action_bond_issued(self):
        self.write({'bid_bond_state': 'issued'})
        return True

    def action_bond_forfeited(self):
        for tender in self:
            tender.bid_bond_state = 'forfeited'
            if tender.state == 'bond_pending':
                tender.state = 'lost'
            tender.message_post(body=self.env._(
                'Bid bond forfeited: %s.', tender.bid_bond_amount))
        return True

    # ------------------------------------------------------------------
    # Reminders
    # ------------------------------------------------------------------
    @api.model
    def _cron_tender_reminders(self):
        """Raise a to-do before each tender date falls due."""
        now = fields.Datetime.now()
        open_states = ('draft', 'pending_approval', 'in_progress', 'submitted')
        for date_field, flag_field, label in REMINDER_DATES:
            tenders = self.search([
                ('state', 'in', open_states),
                (date_field, '!=', False),
                (date_field, '>=', now),
                (flag_field, '=', False),
            ])
            for tender in tenders:
                due = tender[date_field]
                if (due - now).days > max(tender.reminder_days, 0):
                    continue
                tender._schedule_reminder(label, due)
                tender[flag_field] = True
        return True

    def _schedule_reminder(self, label, due):
        self.ensure_one()
        users = (self.responsible_id | self.technical_office_user_id
                 | self.financial_responsible_id)
        if not users:
            users = self.create_uid
        for user in users:
            self.activity_schedule(
                'mail.mail_activity_data_todo', user_id=user.id,
                date_deadline=fields.Date.to_date(due),
                summary=self.env._('%(label)s for %(tender)s',
                                   label=label, tender=self.name),
                note=self.env._('Due on %s.', due))
