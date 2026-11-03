# -*- coding: utf-8 -*-
{
    'name': 'AKT - Web Fixes',
    'version': '19.0.1.0.0',
    'category': 'Technical',
    'summary': 'Front-end patches for core bugs in this Odoo build',
    'author': 'AKT Group',
    'license': 'LGPL-3',
    'depends': ['web', 'html_editor'],
    'assets': {
        'web.assets_backend': [
            'akt_web_fixes/static/src/js/editor_teardown_patch.js',
            'akt_web_fixes/static/src/js/align_plugin_patch.js',
        ],
    },
    'installable': True,
    'application': False,
}
