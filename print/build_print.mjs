// Build the printable edition of HKDA Brief: one A5 PDF (plus HTML for Word conversion).
// Usage: node print/build_print.mjs <node_modules dir> [fonts dir]
// Reads the same data the site uses (site/app/data/*.json). Citations become numbered endnotes collected at the very end.
import fs from "fs";
import path from "path";
import { execFileSync } from "child_process";
import { createRequire } from "module";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const NM = path.resolve(process.argv[2] || "node_modules");
const FONTS = process.argv[3] ? path.resolve(process.argv[3]) : null;
const require = createRequire(path.join(NM, "x.js"));
const { marked } = require("marked");
const { chromium } = require("playwright");

const OUT = path.join(ROOT, "print");
const TMP = path.join(OUT, ".work");
fs.mkdirSync(TMP, { recursive: true });
const data = (f) => JSON.parse(fs.readFileSync(path.join(ROOT, "site/app/data", f + ".json"), "utf8"));
const MODS = data("modules"), PROJ = data("projects"), BIZ = data("business"), EX = data("extras"), SRC = data("sources");
const S = Object.fromEntries(SRC.map((s) => [s.id, s]));
const ASOF = "25 September 2026";
const DISCLAIMER = "For general information only. Not legal or regulatory advice. Always check the official source.";
const CLS = { industry: "Industry estimate", intl: "International official", foreign: "Foreign regulator", filing: "Company filing" };
const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
const esc = (s) => String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
function fmtDate(d) {
  const m = String(d || "").match(/^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/);
  if (!m) return d || "";
  return [m[3] ? String(+m[3]) : "", m[2] ? MONTHS[+m[2] - 1] : "", m[1]].filter(Boolean).join(" ");
}

// ---------- notes (one numbered list for the whole book) ----------
const HEAD = { "Status board": "Where things stand", "Open items": "Open questions", "Common mix-ups": "Common misunderstandings",
  "Read these first": "Official documents to read first", "What your bank must do": "What your bank must or should do" };

const NOTES = { list: [], idx: new Map() };
function noteRef(id, loc) {
  const key = id + "|" + loc;
  if (!NOTES.idx.has(key)) { NOTES.list.push({ id, loc }); NOTES.idx.set(key, NOTES.list.length); }
  return NOTES.idx.get(key);
}
function notesHtml() {
  return '<section class="chapter notes"><span class="mk">@@CH' + String(++CH).padStart(3, "0") + '@@</span>' +
    '<h1>Notes</h1><p class="lead">Each number in the text points to one note below. A note gives the publisher, the document, its date, the exact paragraph or page, and the web address. The same source and paragraph keep the same number throughout the book.</p><ol>' +
    NOTES.list.map(({ id, loc }) => {
      const s = S[id];
      if (!s) return "<li>Source " + esc(id) + (loc ? ", " + esc(loc) : "") + "</li>";
      const pub = (s.p || []).join(", ");
      const kind = s.cls ? "<b>[" + esc(CLS[s.cls] || "Non-official") + "]</b> " : "";
      return "<li>" + kind + esc(pub) + (pub ? ". " : "") + "<i>" + esc(s.t) + "</i>" + (s.d ? ", " + esc(fmtDate(s.d)) : "") + "." +
        (loc ? " " + esc(loc.charAt(0).toUpperCase() + loc.slice(1)) + "." : "") +
        (s.u ? ' <span class="url">' + esc(s.u) + "</span>" : "") + "</li>";
    }).join("") + "</ol></section>";
}
function cite(md) {
  md = md.replace(/\[((?:[SI]):[0-9a-f]{12}[^\]]*)\]/g, (_, inner) => {
    const nums = inner.split(/;\s*(?=[SI]:[0-9a-f]{12})/).map((part) => {
      const m = part.match(/^[SI]:([0-9a-f]{12})\s*,?\s*(.*)$/s);
      return m ? noteRef(m[1], m[2].trim()) : null;
    }).filter(Boolean);
    return '<sup class="fn">' + [...new Set(nums)].join(",<wbr>") + "</sup>";
  });
  return md.replace(/<\/sup>\s*;?\s*<sup class="fn">/g, ",<wbr>");
}
function renderMD(md) {
  md = md.replace(/^(>\s*\*\*[^\n]*)$/gm, ">\n$1\n>");
  md = md.replace(/\[([^\]]+)\]\(#[^)]*\)/g, "$1");                       // internal links become plain text
  let html = marked.parse(cite(md), { mangle: false, headerIds: false });
  html = html.replace(/\s?\(concept\)/g, ' <span class="tag">concept</span>');
  html = html.replace(/<th>Status \(chip\)<\/th>/g, "<th>Status</th>").replace(/<th>Source<\/th>/g, '<th>Src</th>');
  html = html.replace(/<h2>([^<]+)<\/h2>/g, (m, t) => "<h2>" + (HEAD[t.trim()] || t) + "</h2>");
  html = html.replace(/<blockquote>\s*<p>\s*<strong>Analysis/g, '<blockquote class="analysis"><p><strong>Analysis');
  html = html.replace(/<blockquote>\s*<p>\s*<strong>Commercial and customer benefits/g, '<blockquote class="benefits"><p><strong>Commercial and customer benefits');
  return html;
}

// "## Check yourself": keep the questions in the chapter, move the answers to the answer key at the back.
const ANSWERS = [];
function splitQuiz(md, title) {
  const m = md.match(/\n## Check yourself\s*\n([\s\S]*?)(?=\n## |\s*$)/);
  if (!m) return md;
  const items = [];
  const qs = m[1].split(/\n(?=\d+\.\s)/).map((b) => b.trim()).filter((b) => /^\d+\./.test(b));
  for (const b of qs) {
    const q = b.replace(/^\d+\.\s*/, "").split(/\n\s*\*\*Answer:\*\*/)[0].trim();
    const a = (b.split(/\*\*Answer:\*\*/)[1] || "").trim();
    items.push({ q, a });
  }
  if (!items.length) return md;
  ANSWERS.push({ title, items });
  const block = "\n## Check yourself\n\nAnswer from memory, then check the answer key at the back of the book.\n\n" +
    items.map((it, i) => (i + 1) + ". " + it.q).join("\n") + "\n";
  return md.replace(m[0], block);
}
function answersHtml() {
  if (!ANSWERS.length) return "";
  return '<section class="chapter answers"><span class="mk">@@CH' + String(++CH).padStart(3, "0") + '@@</span><h1>Answers to "Check yourself"</h1>' +
    ANSWERS.map((c) => "<h2>" + esc(c.title) + "</h2><ol>" +
      c.items.map((it) => '<li><p class="q">' + renderInline(it.q) + "</p><p>" + renderInline(it.a) + "</p></li>").join("") + "</ol>").join("") + "</section>";
}
const renderInline = (t) => marked.parseInline(cite(t.replace(/\[([^\]]+)\]\(#[^)]*\)/g, "$1")));

let CH = 0;
const toc = [];
function chapter({ kicker, title, meta, md }) {
  const n = ++CH;
  toc.push({ n, title, level: 2 });
  const body = renderMD(splitQuiz(md, title));
  return '<section class="chapter"><span class="mk">@@CH' + String(n).padStart(3, "0") + '@@</span>' +
    (kicker ? '<p class="kicker">' + esc(kicker) + "</p>" : "") + "<h1>" + esc(title) + "</h1>" +
    (meta ? '<p class="meta">' + meta + "</p>" : "") + '<div class="body">' + body + "</div></section>";
}
function front(title, html) {
  const n = ++CH;
  toc.push({ n, title, level: 1 });
  return '<section class="chapter front"><span class="mk">@@CH' + String(n).padStart(3, "0") + '@@</span>' + html + "</section>";
}
function partPage(label, title, intro) {
  const n = ++CH;
  toc.push({ n, title: label + ": " + title, level: 1 });
  return '<section class="part"><span class="mk">@@CH' + String(n).padStart(3, "0") + '@@</span><p class="kicker">' + esc(label) + "</p><h1>" + esc(title) + "</h1>" +
    (intro ? "<p>" + esc(intro) + "</p>" : "") + "</section>";
}
const chipTxt = (st) => st ? '<span class="chip">' + esc(st) + "</span>" : "";

const HOWTO = `<h1>How to read this book</h1>
<p>This is a printed copy of HKDA Brief, a private learning site. It covers official publications up to <b>${ASOF}</b>. Market events appear only where an official source records them. The book does not update. Before you rely on any point, check the official source and the live site.</p>
<h2>Notes</h2><p>Every fact carries a small number. All notes are listed together at the very end of the book. A note gives the publisher, the document, its date, the exact paragraph or page, and the web address.</p>
<h2>The words that carry legal weight</h2><table><tbody>
<tr><th>must / required</th><td>The law or a binding rule requires it.</td></tr>
<tr><th>should / expects</th><td>The regulator expects it. It is usually guidance rather than law. <b>Exception:</b> in the HKMA's anti-money laundering (AML) Guideline, "should" is mandatory, just like "must" (para 1.6 of that Guideline).</td></tr>
<tr><th>may</th><td>It is allowed, not required.</td></tr>
<tr><th>proposes / would</th><td>A proposal. It is not law yet.</td></tr>
<tr><th>stated target</th><td>A plan or date the government or a regulator has announced. It is not a forecast by this book.</td></tr></tbody></table>
<h2>Status labels</h2><table><tbody>
<tr><th>In force</th><td>The rule applies now.</td></tr><tr><th>Issued, not yet in force</th><td>Published, but it starts later.</td></tr>
<tr><th>Consultation</th><td>The regulator is asking for views. Nothing is final.</td></tr>
<tr><th>Conclusions published</th><td>The consultation is finished and the policy is set, but the law may not be made yet.</td></tr>
<tr><th>Bill</th><td>A draft law is before the Legislative Council (LegCo).</td></tr><tr><th>Pilot</th><td>A trial with selected firms.</td></tr>
<tr><th>Exploratory</th><td>Regulators are studying the idea. No rule or live service yet.</td></tr>
<tr><th>Stated target</th><td>An announced plan or date.</td></tr><tr><th>Superseded</th><td>Replaced by a newer document. Kept for history.</td></tr></tbody></table>
<h2>Non-official sources</h2><p>A note that starts with <b>[Industry estimate]</b>, <b>[Company filing]</b>, <b>[International official]</b> or <b>[Foreign regulator]</b> is not an official Hong Kong source. Industry figures are estimates, not facts. Company figures are quoted without comment.</p>
<h2>Other marks</h2><table><tbody>
<tr><th><span class="tag">concept</span></th><td>A plain explanation of how a business works in general. It is not a fact about Hong Kong.</td></tr>
<tr><th>(illustrative)</th><td>A round, made-up number used to show how something works. It is not an estimate.</td></tr>
<tr><th>Analysis — not official</th><td>A shaded box that gives a way to think about a question. It asks one question, explains how to think about it, lists what the answer depends on and the official signposts to watch, and says what it is not. It is not a forecast and not advice.</td></tr>
<tr><th>Commercial and customer benefits</th><td>A green box on each project and on the technology modules: what customers and the bank gain, the evidence so far and its limits. Benefits come from official sources (often stated as aims) or labelled industry estimates.</td></tr>
<tr><th>Check yourself</th><td>Five recall questions at the end of each module. Answer from memory, then check the answer key at the back.</td></tr></tbody></table>
<p class="disc">${DISCLAIMER}</p>`;

// optional study pages written as Markdown in docs/study/
const study = (f) => { const p = path.join(ROOT, "docs/study", f); return fs.existsSync(p) ? fs.readFileSync(p, "utf8") : null; };
function sinceLast() {
  const log = fs.readFileSync(path.join(ROOT, "docs/CHANGELOG.md"), "utf8");
  const parts = log.split(/\n(?=## )/).filter((p) => p.startsWith("## ")).slice(0, 2);
  return "<h1>Since the last edition</h1><p>The most recent changes to the content, newest first. The full list is in the live site's change log.</p>" +
    parts.map((p) => marked.parse(p.replace(/^## /, "### "))).join("");
}

function book() {
  let h = "";
  h += front("How to read this book", HOWTO);
  const map = study("map.md");
  if (map) h += front("Start here: the map and reading order", renderMD(map.replace(/^# .*\n/, "<h1>Start here: the map and reading order</h1>\n")));
  h += front("Since the last edition", sinceLast());
  h += "@@TOC@@";
  const parts = [...new Set(MODS.map((m) => m.part))];
  for (const p of parts) {
    const ms = MODS.filter((m) => m.part === p);
    if (p === "F") {
      h += partPage("Projects", "Official projects and initiatives", "One profile for each official initiative: what it is, where it stands, and what it means for a bank.");
      for (const x of PROJ) h += chapter({ kicker: "Project profile", title: x.title, meta: chipTxt(x.status) + (x.runBy ? " Run by: " + esc(x.runBy) : ""), md: x.md });
    }
    h += partPage("Part " + p, ms[0].partTitle, p === "F" ? "How the business works: where the money is, what regulation costs, who does what, timing, running the business and the path to chief operating officer (COO)." : "");
    for (const m of ms) h += chapter({ kicker: "Part " + p + " · Module " + m.code, title: m.code + " " + m.title, md: m.md });
  }
  h += partPage("Business lines", "Sixteen business lines open to a Hong Kong bank", "Each line gives the bank's role, who pays, cost and capital drivers, the regulatory gate, official signals and industry benchmarks.");
  for (const l of BIZ.lines) h += chapter({ kicker: "Business line · " + l.chain.join(" · "), title: l.title, meta: chipTxt(l.status), md: l.md });
  h += partPage("Case studies", "Case studies", "Fictional cases. All people and firms are invented. Facts about Hong Kong rules are real and cited.");
  for (const c of [...BIZ.cases].sort((a, b) => a.slug.localeCompare(b.slug, "en", { numeric: true }))) h += chapter({ kicker: "Case study · fictional", title: c.title, md: c.md });
  if (BIZ.compare) h += chapter({ kicker: "Comparison · facts only, no ranking", title: BIZ.compare.title, md: BIZ.compare.md });
  h += answersHtml();
  toc.push({ n: CH, title: 'Answers to "Check yourself"', level: 1 });
  h += notesHtml();
  toc.push({ n: CH, title: "Notes", level: 1 });
  return h;
}

// ---------- page assembly ----------
const fontCss = FONTS && fs.existsSync(path.join(FONTS, "local.css"))
  ? fs.readFileSync(path.join(FONTS, "local.css"), "utf8").replace(/url\(([^)]+)\)/g, (m, f) => "url(file://" + path.join(FONTS, f.replace(/["']/g, "")) + ")") : "";
const CSS = fs.readFileSync(path.join(OUT, "print.css"), "utf8");
const page = (title, body) => `<!doctype html><html lang="en"><head><meta charset="utf-8"><title>${esc(title)}</title><style>${fontCss}\n${CSS}</style></head><body>${body}</body></html>`;

function tocHtml(pages) {
  return '<section class="toc"><h1>Contents</h1><ol>' + toc.map((t) =>
    '<li class="l' + t.level + '"><span class="t">' + esc(t.title) + '</span><span class="dots"></span><span class="pg">' + (pages ? pages[t.n] ?? "" : "000") + "</span></li>").join("") + "</ol></section>";
}
const COVER = page("Cover", `<section class="cover"><p class="kicker">Private copy · Edition as of ${ASOF}</p><h1>HKDA Brief</h1>
  <p class="sub">Hong Kong digital-asset rules for a bank's head of compliance</p><div class="rule"></div>
  <p class="blurb">The regulators and regimes; what they mean for a bank; capital, anti-money laundering, the Travel Rule, sanctions, technology and tax; every official project; and the business side: where the money is, sixteen business lines, case studies and the path to chief operating officer.</p>
  <p class="disc">${DISCLAIMER}<br>Official sources: Hong Kong Monetary Authority (HKMA), Securities and Futures Commission (SFC), Financial Services and the Treasury Bureau (FSTB), the Legislative Council and other Hong Kong government bodies.</p></section>`);

const findPages = (pdf) => JSON.parse(execFileSync("python3", ["-c", `
import sys,json,re,pymupdf
d=pymupdf.open(sys.argv[1]); out={}
for i,p in enumerate(d):
    for m in re.findall(r'@@CH(\\d{3})@@', p.get_text()):
        out.setdefault(int(m), i+1)
print(json.dumps(out))`, pdf]).toString());

async function build(browser) {
  const body = book();
  const headerTemplate = `<div style="font:8pt Georgia,serif;color:#777;width:100%;padding:0 11mm 0 15mm;display:flex;justify-content:space-between"><span>HKDA Brief</span><span>As of ${ASOF}</span></div>`;
  const footerTemplate = `<div style="font:7pt Georgia,serif;color:#777;width:100%;padding:0 11mm 0 15mm;display:flex;justify-content:space-between;align-items:baseline"><span>Not legal or regulatory advice. Check the official source.</span><span style="font-size:10pt;color:#333"><span class="pageNumber"></span></span></div>`;
  const opts = { format: "A5", printBackground: true, displayHeaderFooter: true, headerTemplate, footerTemplate,
    margin: { top: "14mm", bottom: "14mm", left: "15mm", right: "11mm" } };
  const pg = await browser.newPage();
  const html = (pages) => page("HKDA Brief", body.replace("@@TOC@@", tocHtml(pages)));
  const render = async (pages, file) => {
    fs.writeFileSync(path.join(TMP, "book.html"), html(pages));
    await pg.setViewportSize({ width: 461, height: 900 });   // A5 text width (148 mm - 26 mm margins) at 96 dpi
    await pg.goto("file://" + path.join(TMP, "book.html"), { waitUntil: "load" });
    await pg.evaluate(() => document.fonts.ready);
    const fit = await pg.evaluate(() => {   // shrink any too-wide table step by step (not below 9pt), then allow word breaks
      const W = document.body.clientWidth; let shrunk = 0, broken = 0;
      document.querySelectorAll("table").forEach((t) => {
        let fs = 11;
        while (t.getBoundingClientRect().width > W + 0.5 && fs > 9) { fs -= 0.5; t.style.fontSize = fs + "pt"; }
        if (fs < 11) shrunk++;
        if (t.getBoundingClientRect().width > W + 0.5) { t.style.overflowWrap = "anywhere"; t.querySelectorAll("td,th").forEach((c) => (c.style.overflowWrap = "anywhere")); broken++; }
      });
      return { W, shrunk, broken, sw: document.documentElement.scrollWidth };
    });
    console.log("table fit:", JSON.stringify(fit));
    await pg.pdf({ path: file, ...opts });
  };
  const pass1 = path.join(TMP, "book-pass1.pdf");
  await render(null, pass1);
  const pages = findPages(pass1);
  const main = path.join(TMP, "book-main.pdf");
  await render(pages, main);
  const check = findPages(main);
  const moved = Object.keys(pages).filter((k) => pages[k] !== check[k]);
  if (moved.length) throw new Error("Contents page numbers moved on second pass: " + moved.join(","));
  await pg.setContent(COVER, { waitUntil: "load" });
  await pg.evaluate(() => document.fonts.ready);
  const cov = path.join(TMP, "book-cover.pdf");
  await pg.pdf({ path: cov, format: "A5", printBackground: true, margin: { top: "0", bottom: "0", left: "0", right: "0" } });
  const final = path.join(OUT, "HKDA-Brief.pdf");
  // merge cover + book, add bookmarks (PDF page = printed page + 1 for the cover)
  const outline = JSON.stringify(toc.map((t) => [t.level, t.title, (check[t.n] || 1) + 1]));
  execFileSync("python3", ["-c", `
import sys,json,pymupdf
out=pymupdf.open(); out.insert_pdf(pymupdf.open(sys.argv[2])); out.insert_pdf(pymupdf.open(sys.argv[3]))
toc=json.loads(sys.argv[4]); fixed=[]; last=0
for lvl,t,p in toc:
    lvl=min(lvl,last+1) if fixed else 1; fixed.append([lvl,t,p]); last=lvl
out.set_toc(fixed)
out.set_metadata({"title":"HKDA Brief","author":"HKDA Brief","subject":"As of ${ASOF}"})
out.save(sys.argv[1], garbage=3, deflate=True)`, final, cov, main, outline]);
  // Word-friendly HTML (Word builds its own contents list)
  fs.writeFileSync(path.join(TMP, "HKDA-Brief.html"),
    page("HKDA Brief", `<section class="cover plain"><h1>HKDA Brief</h1><p>Hong Kong digital-asset rules for a bank's head of compliance. Edition as of ${ASOF}. ${DISCLAIMER}</p></section>` +
      body.replace("@@TOC@@", "")).replace(/<span class="mk">[^<]*<\/span>/g, ""));
  await pg.close();
  const n = execFileSync("python3", ["-c", "import sys,pypdf;print(len(pypdf.PdfReader(sys.argv[1]).pages))", final]).toString().trim();
  console.log(`Book: ${toc.length} contents entries, ${NOTES.list.length} notes, ${ANSWERS.length} quizzes, ${n} pages -> ${final}`);
}

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
await build(browser);
await browser.close();
