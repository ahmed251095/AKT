{
    'name': 'Construction Management - Business Extension',
    'version': '19.0.1.0.0',
    'category': 'Services/Construction',
    'summary': 'Tender pricing formula, bid bonds, management approval cycle, '
               'document checklists, project team roles and closure workflow',
    'description': """
Business extension for Construction Management
==============================================

Adds the operating model actually used by the contractor on top of
``aos_construction_management``:

* **Build-up pricing** - every tender / BOQ item is priced from its dry cost and
  operating cost, then marked up by profit, contingency and administration, and
  finally by the general expense ratio. Rates stop being typed by hand.
* **Bid and performance bonds** - amounts, guarantee type, bank, expiry and the
  release cycle that has to finish before a losing tender can be closed.
* **Management approval** - a tender is opened only after the board approves the
  request, and the tender document fee is only spent after that approval.
* **Document checklists** - technical and financial files with the papers the
  tender conditions ask for; a bid cannot be submitted while a required paper is
  missing.
* **Deadline reminders** - activities raised a configurable number of days before
  submission, envelope opening and award dates.
* **Project team roles** - electrical, mechanical, logistics, finance, accountant
  and HR supervisor alongside the existing project and site managers.
* **Hold and closure** - holding a project needs a reason and an approval, and
  completing one needs handover plus a released performance bond.
* **Cost analysis** - project expenses split by nature for the profit statement.
""",
    'author': 'Ahmed Salah',
    'website': 'https://leapai.ai',
    'depends': [
        'aos_construction_management',
        'mail',
        'account',
        'purchase',
        'stock',
        'hr',
    ],
    'data': [
        'security/construction_ext_security.xml',
        'security/ir.model.access.csv',
        'data/construction_authority_type_data.xml',
        'data/construction_document_type_data.xml',
        'data/construction_labour_type_data.xml',
        'data/construction_ext_data.xml',
        'wizard/construction_tender_reject_views.xml',
        'wizard/construction_project_hold_views.xml',
        'views/construction_authority_type_views.xml',
        'views/construction_document_views.xml',
        'views/construction_tender_views.xml',
        'views/construction_boq_views.xml',
        'views/construction_percentage_fix_views.xml',
        'views/account_payment_views.xml',
        'views/construction_billing_views.xml',
        'views/construction_project_views.xml',
        'views/construction_subcontract_views.xml',
        'views/construction_work_order_views.xml',
        'views/construction_material_requisition_views.xml',
        'views/construction_labour_views.xml',
        'views/construction_hr_case_views.xml',
        'views/construction_salary_views.xml',
        'views/res_config_settings_views.xml',
        'views/construction_ext_menus.xml',
        'report/construction_reports.xml',
        'report/tender_cover_letter_template.xml',
        'report/project_profit_statement_template.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'assets': {
        'web.assets_backend': [
            'aos_construction_ext/static/src/scss/rtl.scss',
            'aos_construction_ext/static/src/js/dashboard_patch.js',
            'aos_construction_ext/static/src/xml/dashboard_cards.xml',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
