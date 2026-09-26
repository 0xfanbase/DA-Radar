# Printed edition

`HKDA-Brief-Volume-1.pdf` (the rules: Parts A–E and project profiles) and `HKDA-Brief-Volume-2.pdf`
(business: Part F, business lines, cases, comparison, timeline, glossary). A4, wider left margin for binding,
citations as numbered endnotes per chapter. `.docx` versions are for editing or uploading to Google Drive
(Drive converts them to Google Docs; Word/Docs builds the contents list).

Rebuild after the site data changes (`python3 site/build.py` first):

    node print/build_print.mjs <node_modules with marked + playwright> [fonts dir with local.css]

Word files: convert `print/.work/HKDA-Brief-Volume-N.html` with pandoc (`--toc`).
The printed edition does not update; each cover states its "as of" date.
