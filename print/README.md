# Printed edition

`HKDA-Brief.pdf` is one A4 book, laid out for printing 2 pages per sheet. Body text is 13 pt. It contains the cover,
How to read, the map and reading order, Since the last edition, Contents, Parts A to E, the project profiles, Part F,
the business lines, the case studies, the comparison page, the answers to "Check yourself" and all notes at the back.
`HKDA-Brief.docx` is the same content for editing or for uploading to Google Drive, which converts it to a Google Doc.

Rebuild after the site data changes (run `python3 site/build.py` first):

    node print/build_print.mjs <node_modules with marked + playwright> [fonts dir with local.css]

For the Word file, convert `print/.work/HKDA-Brief.html` with pandoc (`--toc`).
The printed edition does not update. Its cover states its "as of" date.
