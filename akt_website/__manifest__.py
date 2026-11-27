{
    'name': 'AKT Group Website',
    'summary': 'The AKT Group public site, as an Odoo website',
    'description': """
The public site of AKT Group for General Contracting and Development,
rebuilt page for page on Odoo's website so every page stays editable from
the builder. Arabic is the site's language and English is the translation;
the quotation, contact, appointment and supplier forms open CRM leads.
""",
    'author': 'AKT Group',
    'website': 'https://www.akt-grp.com',
    'category': 'Website',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'depends': ['website', 'crm'],
    'data': [
        'views/assets.xml',
        'data/crm_data.xml',
        'views/layout.xml',
        'views/pages.xml',
        'views/form_messages.xml',
        'data/sync.xml',
    ],
    'post_init_hook': 'post_init',
    'installable': True,
    'application': True,
}
