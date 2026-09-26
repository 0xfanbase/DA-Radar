# Printed edition

`HKDA-Brief.pdf` is one book on **A5 pages** (148 × 210 mm) with **14 pt body text**. Print it at 100% ("actual size")
on A5 paper, or two A5 pages per A4 sheet with no further shrinking. Either way the text prints at 14 pt.
It contains the cover, How to read, the map and reading order, Since the last edition, Contents, Parts A to E,
the project profiles, Part F, the business lines, the case studies, the comparison page, the answers to
"Check yourself" and all notes at the back (9 pt). Wide tables are shrunk only as far as needed to fit the page
(never below 9 pt).
`HKDA-Brief.docx` holds the same content for editing or for Google Drive; set the page size in Word or Docs.

Rebuild after the site data changes (run `python3 site/build.py` first):

    node print/build_print.mjs <node_modules with marked + playwright> [fonts dir with local.css]

For the Word file, convert `print/.work/HKDA-Brief.html` with pandoc (`--toc`).
The printed edition does not update. Its cover states its "as of" date.
