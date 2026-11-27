# Regenerating akt_website

The module is generated from a local mirror of the site it reproduces, so
that a change there can be carried over by re-running these scripts rather
than by hand-editing eighty-four pages.

Take the mirror of the rendered pages first (wget stops at the site's
`nofollow` robots tag unless told otherwise):

    wget -e robots=off --mirror --page-requisites --adjust-extension \
         --no-host-directories --reject-regex '/management/' \
         --domains aktgroup.pythonanywhere.com \
         https://aktgroup.pythonanywhere.com/ar/ \
         https://aktgroup.pythonanywhere.com/en/

Set `AKT_MIRROR` to where it landed and `AKT_BASE` to the site it came from;
both default to the pythonanywhere build. Only the HTML is read from the
mirror. The static files are fetched from the site by the URLs the pages
ask for, because wget renames whatever the server labels oddly - it saved
`hero-poster.webp` as `hero-poster.webp.html` - and because the theme files
are assembled by collectstatic and do not exist under `static/` in the
source tree.

Then, in order:

    python3 build_static.py    # fetch the static files; url map + fingerprints
    python3 build_module.py    # manifest, assets, menus, layout, pages
    python3 build_terms.py     # i18n/ar_terms.json  (needs odoo importable)
    python3 build_po.py        # i18n/ar.po

`build_terms.py` and `build_po.py` import `odoo.tools.translate`, so run them
with an interpreter that can import Odoo:

    PYTHONPATH=/path/to/odoo-source /path/to/venv/bin/python build_terms.py

The stylesheets are linked from the page rather than bundled, so nothing
else would tell a browser one of them changed. `build_static.py` writes the
sha1 of each file's bytes to `fingerprints.json`, and every URL it hands
out carries it as `?v=`. Run `build_static.py` before `build_module.py` or
the links will carry last run's stamps.

Everything under `akt_website/` except what you add by hand is overwritten,
so put hand-written code in `controllers/`, `models/`, `hooks.py` and
`views/form_messages.xml` - the generator does not touch those.

## Checking the result

With the module installed on a local database serving on port 8169:

    python3 compare_both.py    # every page, both languages, against the mirror
    python3 test_forms.py      # the four forms, and three rejections
    python3 test_upload.py     # a form post carrying attachments

`compare_both.py` should report 36 identical English pages and 35 Arabic.
The one that differs is `/company/credentials`; see the note in
`build_terms.py` about a term that needs two translations in one view.
