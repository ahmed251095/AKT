from odoo import api, fields, models
from odoo.exceptions import UserError

#: Expense categories of the base module, mapped onto the cost lines the
#: management report is read by.
EXPENSE_FIELDS = {
    'material': 'expense_material',
    'labour': 'expense_labour',
    'equipment': 'expense_equipment',
    'subcontract': 'expense_subcontract',
    'overhead': 'expense_overhead',
    'other': 'expense_other',
}

CERTIFIED_STATES = ('approved', 'invoiced', 'paid')


class ConstructionProject(models.Model):
    _inherit = 'construction.project'

    # ------------------------------------------------------------------
    # Origin
    # ------------------------------------------------------------------
    authority_type_id = fields.Many2one(
        'construction.authority.type', string='Authority Type')
    contract_duration_days = fields.Integer(
        string='Contract Duration (days)',
        help='Execution period agreed in the contract.')

    # ------------------------------------------------------------------
    # Team - the departments that sit on a running project
    # ------------------------------------------------------------------
    electrical_engineer_id = fields.Many2one(
        'res.users', string='Electrical Engineer')
    mechanical_engineer_id = fields.Many2one(
        'res.users', string='Mechanical Engineer')
    logistics_manager_id = fields.Many2one(
        'res.users', string='Logistics Manager',
        help='Owns plant movement and transport between sites.')
    finance_manager_id = fields.Many2one(
        'res.users', string='Finance Manager')
    financial_responsible_id = fields.Many2one(
        'res.users', string='Finance Responsible')
    accountant_id = fields.Many2one(
        'res.users', string='Responsible Accountant',
        help='The accountant who owns this project file.')
    hr_supervisor_id = fields.Many2one(
        'res.users', string='HR Supervisor')
    employee_ids = fields.Many2many(
        'hr.employee', 'construction_project_employee_rel',
        'project_id', 'employee_id', string='Assigned Employees')
    employee_count = fields.Integer(
        string='Employees', compute='_compute_employee_count')

    # ------------------------------------------------------------------
    # Stores
    # ------------------------------------------------------------------
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Site Warehouse',
        help='Warehouse the site draws its materials from.')
    stock_location_id = fields.Many2one(
        'stock.location', string='Site Location',
        domain="[('usage', '=', 'internal')]")

    # ------------------------------------------------------------------
    # Project file
    # ------------------------------------------------------------------
    document_ids = fields.One2many(
        'construction.document', 'project_id', string='Project Documents')
    document_count = fields.Integer(
        string='Documents', compute='_compute_document_status')
    document_missing_count = fields.Integer(
        string='Missing Documents', compute='_compute_document_status')
    drive_folder_url = fields.Char(
        string='Drive Folder',
        help='Link to the shared folder holding the contract, the BOQ and the '
             'drawings.')

    # ------------------------------------------------------------------
    # Performance bond
    # ------------------------------------------------------------------
    performance_bond_required = fields.Boolean(
        string='Performance Bond Required', default=True)
    performance_bond_percent = fields.Float(
        string='Performance Bond (%)', default=lambda self:
        self.env.company.construction_performance_bond_percent)
    performance_bond_amount = fields.Monetary(
        string='Performance Bond Amount', currency_field='currency_id',
        compute='_compute_performance_bond_amount', store=True, readonly=False)
    performance_bond_bank_id = fields.Many2one('res.bank', string='Issuing Bank')
    performance_bond_ref = fields.Char(string='Bond Reference')
    performance_bond_issue_date = fields.Date(string='Bond Issue Date')
    performance_bond_expiry_date = fields.Date(string='Bond Expiry Date')
    performance_bond_return_date = fields.Date(
        string='Bond Release Date', copy=False)
    performance_bond_state = fields.Selection(
        [('not_required', 'Not Required'),
         ('to_issue', 'To Issue'),
         ('issued', 'Issued'),
         ('held', 'Held by Client'),
         ('released', 'Released'),
         ('forfeited', 'Forfeited')],
        string='Bond Status', default='to_issue', copy=False, tracking=True)

    # ------------------------------------------------------------------
    # Hold
    # ------------------------------------------------------------------
    hold_reason = fields.Text(string='Hold Reason', readonly=True, copy=False)
    hold_date = fields.Date(string='Held Since', readonly=True, copy=False)
    hold_requested_by = fields.Many2one(
        'res.users', string='Hold Requested By', readonly=True, copy=False)
    hold_approved_by = fields.Many2one(
        'res.users', string='Hold Approved By', readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Handover and closure
    # ------------------------------------------------------------------
    initial_handover_date = fields.Date(
        string='Initial Handover', copy=False,
        help='Date the client took provisional delivery of the works.')
    final_handover_date = fields.Date(
        string='Final Handover', copy=False,
        help='Date the maintenance period ended and the works were finally '
             'accepted.')
    closure_note = fields.Text(string='Closure Notes')

    # ------------------------------------------------------------------
    # Cost and profit analysis
    # ------------------------------------------------------------------
    expense_material = fields.Monetary(
        string='Raw Materials', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    expense_labour = fields.Monetary(
        string='Salaries & Wages', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    expense_equipment = fields.Monetary(
        string='Equipment', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    expense_subcontract = fields.Monetary(
        string='Subcontractor Expenses', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    expense_overhead = fields.Monetary(
        string='Overheads', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    expense_other = fields.Monetary(
        string='Other Expenses', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    direct_purchase_total = fields.Monetary(
        string='Direct Purchases', currency_field='currency_id',
        compute='_compute_cost_breakdown',
        help='Purchase orders booked on the project, excluding those raised '
             'against a subcontract, which the subcontractor certificates '
             'already account for.')
    subcontract_certified_total = fields.Monetary(
        string='Certified Subcontractor Work', currency_field='currency_id',
        compute='_compute_cost_breakdown')
    customer_certified_total = fields.Monetary(
        string='Total Certificates', currency_field='currency_id',
        compute='_compute_cost_breakdown',
        help='Value of the payment certificates approved for the client.')
    project_total_cost = fields.Monetary(
        string='Total Cost', currency_field='currency_id',
        compute='_compute_cost_breakdown',
        help='Recorded expenses, plus certified subcontractor work, plus '
             'purchases booked against the project.')
    project_net_profit = fields.Monetary(
        string='Net Profit', currency_field='currency_id',
        compute='_compute_cost_breakdown',
        help='Total certificates less total cost.')
    project_net_margin = fields.Float(
        string='Net Margin (%)', compute='_compute_cost_breakdown')

    # ------------------------------------------------------------------
    # HR follow-up
    # ------------------------------------------------------------------
    hr_case_ids = fields.One2many(
        'construction.hr.case', 'project_id', string='HR Cases')
    hr_case_count = fields.Integer(
        string='HR Cases', compute='_compute_hr_case_count')

    state = fields.Selection(
        selection_add=[
            ('active',),
            ('handover', 'Handover'),
        ],
        ondelete={'handover': 'set default'})

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('employee_ids')
    def _compute_employee_count(self):
        for project in self:
            project.employee_count = len(project.employee_ids)

    @api.depends('hr_case_ids')
    def _compute_hr_case_count(self):
        for project in self:
            project.hr_case_count = len(project.hr_case_ids)

    @api.depends('contract_value', 'performance_bond_percent',
                 'performance_bond_required')
    def _compute_performance_bond_amount(self):
        for project in self:
            if not project.performance_bond_required:
                project.performance_bond_amount = 0.0
                continue
            project.performance_bond_amount = (
                project.contract_value * project.performance_bond_percent
                / 100.0)

    @api.depends('document_ids.is_submitted', 'document_ids.is_required')
    def _compute_document_status(self):
        for project in self:
            documents = project.document_ids
            missing = documents.filtered(
                lambda d: d.is_required and not d.is_submitted)
            project.document_count = len(documents)
            project.document_missing_count = len(missing)

    @api.depends('purchase_total', 'contract_value')
    def _compute_cost_breakdown(self):
        expense_groups = self.env['construction.expense']._read_group(
            [('project_id', 'in', self.ids), ('state', '=', 'approved')],
            ['project_id', 'category'], ['amount:sum'])
        expenses = {}
        for project, category, amount in expense_groups:
            expenses.setdefault(project.id, {})[category] = amount

        billing_groups = self.env['construction.ra.billing']._read_group(
            [('project_id', 'in', self.ids),
             ('state', 'in', CERTIFIED_STATES)],
            ['project_id', 'billing_type'], ['total_amount:sum'])
        billings = {}
        for project, billing_type, amount in billing_groups:
            billings.setdefault(project.id, {})[billing_type] = amount

        direct_purchases = self.env['purchase.order']._read_group(
            [('construction_project_id', 'in', self.ids),
             ('state', 'in', ('purchase', 'done')),
             ('construction_subcontract_id', '=', False)],
            ['construction_project_id'], ['amount_total:sum'])
        purchased = {
            project.id: amount for project, amount in direct_purchases}

        for project in self:
            by_category = expenses.get(project.id, {})
            for category, field_name in EXPENSE_FIELDS.items():
                project[field_name] = by_category.get(category, 0.0)
            by_type = billings.get(project.id, {})
            project.subcontract_certified_total = by_type.get(
                'subcontractor', 0.0)
            project.customer_certified_total = by_type.get('customer', 0.0)
            project.direct_purchase_total = purchased.get(project.id, 0.0)
            project.project_total_cost = (
                sum(by_category.values())
                + project.subcontract_certified_total
                + project.direct_purchase_total)
            project.project_net_profit = (
                project.customer_certified_total - project.project_total_cost)
            project.project_net_margin = (
                100.0 * project.project_net_profit
                / project.customer_certified_total
                if project.customer_certified_total else 0.0)

    # ------------------------------------------------------------------
    # Project file
    # ------------------------------------------------------------------
    def action_load_standard_documents(self):
        Document = self.env['construction.document']
        types = self.env['construction.document.type'].search([
            ('scope', 'in', ('project', 'both')),
        ])
        for project in self:
            existing = project.document_ids.document_type_id
            for doc_type in types - existing:
                Document.create({
                    'project_id': project.id,
                    'document_type_id': doc_type.id,
                    'is_required': doc_type.is_default_required,
                })
        return True

    # ------------------------------------------------------------------
    # Hold
    # ------------------------------------------------------------------
    def action_hold(self):
        """Holding a site costs money, so it needs a reason on the record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Hold Project'),
            'res_model': 'construction.project.hold',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_project_id': self.id},
        }

    def action_confirm_hold(self, reason):
        for project in self:
            project.write({
                'hold_reason': reason,
                'hold_date': fields.Date.context_today(project),
                'hold_requested_by': self.env.user.id,
                'hold_approved_by': self.env.user.id,
            })
            super(ConstructionProject, project).action_hold()
            project.message_post(body=self.env._(
                'Project put on hold. Reason: %s', reason))
        return True

    def action_activate(self):
        result = super().action_activate()
        self.filtered('hold_reason').write({
            'hold_reason': False,
            'hold_date': False,
            'hold_requested_by': False,
            'hold_approved_by': False,
        })
        return result

    # ------------------------------------------------------------------
    # Handover and closure
    # ------------------------------------------------------------------
    def action_start_handover(self):
        for project in self:
            if project.state != 'active':
                raise UserError(self.env._(
                    'Only a running project can move to handover.'))
            project.state = 'handover'
        return True

    def action_complete(self):
        """A project closes once it is handed over and the bond is back."""
        for project in self:
            if not project.initial_handover_date:
                raise UserError(self.env._(
                    'Record the initial handover date before closing "%s".',
                    project.display_name))
            if project.performance_bond_required and \
                    project.performance_bond_state not in (
                        'released', 'forfeited'):
                raise UserError(self.env._(
                    'The performance bond of "%s" has not been released yet.',
                    project.display_name))
            open_certificates = self.env['construction.ra.billing'].search_count([
                ('project_id', '=', project.id),
                ('state', 'in', ('draft', 'submitted')),
            ])
            if open_certificates:
                raise UserError(self.env._(
                    '"%(project)s" still has %(count)s payment certificate(s) '
                    'that are neither approved nor cancelled.',
                    project=project.display_name, count=open_certificates))
        return super().action_complete()

    def action_performance_bond_issued(self):
        self.write({'performance_bond_state': 'issued'})
        return True

    def action_performance_bond_released(self):
        for project in self:
            project.write({
                'performance_bond_state': 'released',
                'performance_bond_return_date': fields.Date.context_today(
                    project),
            })
            project.message_post(body=self.env._('Performance bond released.'))
        return True

    # ------------------------------------------------------------------
    # Smart buttons
    # ------------------------------------------------------------------
    def action_view_documents(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Project Documents'),
            'res_model': 'construction.document',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }

    def action_view_hr_cases(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('HR Cases'),
            'res_model': 'construction.hr.case',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id},
        }
