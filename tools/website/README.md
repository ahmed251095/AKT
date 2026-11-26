# Regenerating akt_website

The module is generated from a local mirror of the site it reproduces, so
that a change there can be carried over by re-running these scripts rather
than by hand-editing eighty-four pages.

Take the mirror first (wget stops at the site's `nofollow` robots tag unless
told otherwise):

    wget -e robots=off --mirror --page-requisites --adjust-extension \
         --no-host-directories --reject-regex '/management/' \
         --domains akt-preview-production.up.railway.app \
         https://akt-preview-production.up.railway.app/ar/ \
         https://akt-preview-production.up.railway.app/en/

`MIRROR` at the top of `common.py` and `build_static.py` points at it.

Then, in order:

    python3 build_static.py    # static files, de-hashed, plus the url map
    python3 build_module.py    # manifest, assets, menus, layout, pages
    python3 build_terms.py     # i18n/ar_terms.json  (needs odoo importable)
    python3 build_po.py        # i18n/ar.po

`build_terms.py` and `build_po.py` import `odoo.tools.translate`, so run them
with an interpreter that can import Odoo:

    PYTHONPATH=/path/to/odoo-source /path/to/venv/bin/python build_terms.py

Everything under `akt_website/` except what you add by hand is overwritten,
so put hand-written code in `controllers/`, `models/`, `hooks.py` and
`views/form_messages.xml` - the generator does not touch those.

## Checking the result

With the module installed on a local database serving on port 8169:

    python3 compare_both.py    # every page, both languages, against the mirror
    python3 test_forms.py      # the four forms, and three rejections
    python3 test_upload.py     # a form post carrying attachments

`compare_both.py` should report 42 identical English pages and 41 Arabic.
The one that differs is `/company/credentials`; see the note in
`build_terms.py` about a term that needs two translations in one view.
