# Translation tooling

`ar_terms.py` holds the English -> Arabic glossary for both construction
modules. `build_ar_po.py` reads the module sources and regenerates
`<module>/i18n/ar_001.po` from it.

    python3 tools/build_ar_po.py

Add a term to `ar_terms.py` and re-run to pick it up. The script reports any
source string it finds without a translation.

Terminology follows the client's operations notes: مناقصة for a tender,
مقايسة for the bill of quantities, مستخلص for a payment certificate,
تأمين ابتدائي / نهائي for the bid and performance bonds.
