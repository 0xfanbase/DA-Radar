// Build the printable edition of HKDA Brief: two A4 PDF volumes (plus HTML for Word conversion).
// Usage: node print/build_print.mjs <node_modules dir> [fonts dir]
// Reads the same data the site uses (site/app/data/*.json). Citations become numbered endnotes per chapter.
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

// ---------- chapter rendering ----------
const HEAD = { "Status board": "Where things stand", "Open items": "Open questions", "Common mix-ups": "Common misunderstandings",
  "Read these first": "Official documents to read first", "What your bank must do": "What your bank must or should do" };

class Notes {
  constructor() { this.list = []; this.idx = new Map(); }
  ref(id, loc) {
    const key = id + "|" + loc;
    if (!this.idx.has(key)) { this.list.push({ id, loc }); this.idx.set(key, this.list.length); }
    return this.idx.get(key);
  }
  html() {
    if (!this.list.length) return "";
    return '<section class="notes"><h3>Notes</h3><ol>' + this.list.map(({ id, loc }) => {
      const s = S[id];
      if (!s) return "<li>Source " + esc(id) + (loc ? ", " + esc(loc) : "") + "</li>";
      const pub = (s.p || []).join(", ");
      const kind = s.cls ? "<b>[" + esc(CLS[s.cls] || "Non-official") + "]</b> " : "";
      return "<li>" + kind + esc(pub) + (pub ? ". " : "") + "<i>" + esc(s.t) + "</i>" + (s.d ? ", " + esc(fmtDate(s.d)) : "") + "." +
        (loc ? " " + esc(loc.charAt(0).toUpperCase() + loc.slice(1)) + "." : "") +
        (s.u ? ' <span class="url">' + esc(s.u) + "</span>" : "") + "</li>";
    }).join("") + "</ol></section>";
  }
}

function cite(md, notes) {
  // [S:id, loc] or [I:id, loc], chains separated by ";" inside one bracket
  md = md.replace(/\[((?:[SI]):[0-9a-f]{12}[^\]]*)\]/g, (_, inner) => {
    const nums = inner.split(/;\s*(?=[SI]:[0-9a-f]{12})/).map((part) => {
      const m = part.match(/^[SI]:([0-9a-f]{12})\s*,?\s*(.*)$/s);
      return m ? notes.ref(m[1], m[2].trim()) : null;
    }).filter(Boolean);
    return '<sup class="fn">' + nums.join(",") + "</sup>";
  });
  return md.replace(/<\/sup>\s*;?\s*<sup class="fn">/g, ",");
}

function renderMD(md, notes) {
  md = md.replace(/^(>\s*\*\*[^\n]*)$/gm, ">\n$1\n>");
  md = md.replace(/\[([^\]]+)\]\(#[^)]*\)/g, "$1");                       // internal links become plain text
  let html = marked.parse(cite(md, notes), { mangle: false, headerIds: false });
  html = html.replace(/\s?\(concept\)/g, ' <span class="tag">concept</span>');
  html = html.replace(/<h2>([^<]+)<\/h2>/g, (m, t) => "<h2>" + (HEAD[t.trim()] || t) + "</h2>");
  html = html.replace(/<blockquote>\s*<p>\s*<strong>Analysis/g, '<blockquote class="analysis"><p><strong>Analysis');
  return html;
}

let CH = 0;
const toc = [];
function chapter({ kicker, title, meta, md, rows, extra, level = 2 }) {
  const n = ++CH, notes = new Notes();
  toc.push({ n, title, kicker, level });
  let body = md ? renderMD(md, notes) : "";
  if (rows) body += rows(notes);
  if (extra) body += extra;
  return '<section class="chapter"><span class="mk">@@CH' + String(n).padStart(3, "0") + '@@</span>' +
    (kicker ? '<p class="kicker">' + esc(kicker) + "</p>" : "") + "<h1>" + esc(title) + "</h1>" +
    (meta ? '<p class="meta">' + meta + "</p>" : "") + '<div class="body">' + body + "</div>" + notes.html() + "</section>";
}
function partPage(label, title, intro) {
  const n = ++CH;
  toc.push({ n, title: label + ": " + title, level: 1 });
  return '<section class="part"><span class="mk">@@CH' + String(n).padStart(3, "0") + '@@</span><p class="kicker">' + esc(label) + "</p><h1>" + esc(title) + "</h1>" +
    (intro ? "<p>" + esc(intro) + "</p>" : "") + "</section>";
}
const chipTxt = (st) => st ? '<span class="chip">' + esc(st) + "</span>" : "";

const HOWTO = `<section class="chapter howto"><h1>How to read this edition</h1>
<p>This is a printed copy of HKDA Brief, a private learning site. It reflects official publications up to <b>${ASOF}</b>. It does not update. Before you rely on any point, check the official source and the live site.</p>
<h2>Notes</h2><p>Every fact carries a small number. The number points to a note at the end of the chapter. The note gives the publisher, the document, its date, the exact paragraph or page, and the web address.</p>
<h2>The words that carry legal weight</h2><table><tbody>
<tr><th>must / required</th><td>The law or a binding rule requires it.</td></tr>
<tr><th>should / expects</th><td>The regulator expects it. It is guidance rather than law.</td></tr>
<tr><th>may</th><td>It is allowed, not required.</td></tr>
<tr><th>proposes / would</th><td>A proposal. It is not law yet.</td></tr>
<tr><th>stated target</th><td>A plan or date the government or a regulator has announced. It is not a forecast by this guide.</td></tr></tbody></table>
<h2>Status labels</h2><table><tbody>
<tr><th>In force</th><td>The rule applies now.</td></tr><tr><th>Issued, not yet in force</th><td>Published, but it starts later.</td></tr>
<tr><th>Consultation</th><td>The regulator is asking for views. Nothing is final.</td></tr>
<tr><th>Conclusions published</th><td>The consultation is finished and the policy is set, but the law may not be made yet.</td></tr>
<tr><th>Bill</th><td>A draft law is before the Legislative Council (LegCo).</td></tr><tr><th>Pilot</th><td>A trial with selected firms.</td></tr>
<tr><th>Exploratory</th><td>Regulators are studying the idea. No rule or live service yet.</td></tr>
<tr><th>Stated target</th><td>An announced plan or date.</td></tr><tr><th>Superseded</th><td>Replaced by a newer document. Kept for history.</td></tr></tbody></table>
<h2>Non-official sources (Business section only)</h2><p>A note that starts with <b>[Industry estimate]</b>, <b>[Company filing]</b>, <b>[International official]</b> or <b>[Foreign regulator]</b> is not an official Hong Kong source. Industry figures are estimates, not facts. Company figures are quoted without comment.</p>
<h2>Other marks</h2><table><tbody>
<tr><th><span class="tag">concept</span></th><td>A plain explanation of how a business works in general. It is not a fact about Hong Kong.</td></tr>
<tr><th>(illustrative)</th><td>A round, made-up number used to show how something works. It is not an estimate.</td></tr>
<tr><th>Analysis — not official</th><td>A shaded box that gives a way to think about a question. It asks one question, explains how to think about it, lists what the answer depends on and the official signposts to watch, and says what it is not. It is not a forecast and not advice.</td></tr></tbody></table>
<p class="disc">${DISCLAIMER}</p></section>`;

// ---------- volumes ----------
function vol1() {
  let h = "";
  const parts = [...new Set(MODS.filter((m) => m.part !== "F").map((m) => m.part))];
  for (const p of parts) {
    const ms = MODS.filter((m) => m.part === p);
    h += partPage("Part " + p, ms[0].partTitle);
    for (const m of ms) h += chapter({ kicker: "Part " + p + " · Module " + m.code, title: m.code + " " + m.title, md: m.md });
  }
  h += partPage("Projects", "Official projects and initiatives", "One profile for each official initiative: what it is, where it stands, and what it means for a bank.");
  for (const p of PROJ) h += chapter({ kicker: "Project profile", title: p.title, meta: chipTxt(p.status) + (p.runBy ? " Run by: " + esc(p.runBy) : ""), md: p.md });
  return h;
}
function vol2() {
  let h = "";
  const fm = MODS.filter((m) => m.part === "F");
  h += partPage("Part F", fm[0].partTitle, "How the business works: where the money is, what regulation costs, who does what, timing, running the business and the path to chief operating officer (COO).");
  for (const m of fm) h += chapter({ kicker: "Part F · Module " + m.code, title: m.code + " " + m.title, md: m.md });
  h += partPage("Business lines", "Sixteen business lines open to a Hong Kong bank", "Each line gives the bank's role, who pays, cost and capital drivers, the regulatory gate, official signals and industry benchmarks.");
  for (const l of BIZ.lines) h += chapter({ kicker: "Business line · " + l.chain.join(" · "), title: l.title, meta: chipTxt(l.status), md: l.md });
  h += partPage("Case studies", "Six case studies", "Fictional cases. All people and firms are invented. Facts about Hong Kong rules are real and cited.");
  for (const c of [...BIZ.cases].sort((a, b) => a.slug.localeCompare(b.slug, "en", { numeric: true }))) h += chapter({ kicker: "Case study · fictional", title: c.title, md: c.md });
  if (BIZ.compare) h += chapter({ kicker: "Comparison · facts only, no ranking", title: BIZ.compare.title, md: BIZ.compare.md });
  h += partPage("Reference", "Timeline and glossary");
  h += chapter({ kicker: "Reference", title: "Timeline", rows: (notes) => {
    let y = "", out = "";
    for (const t of [...EX.timeline].sort((a, b) => a.k.localeCompare(b.k))) {
      const yr = t.k.slice(0, 4);
      if (yr !== y) { if (y) out += "</tbody></table>"; out += "<h2>" + yr + '</h2><table class="tl"><tbody>'; y = yr; }
      out += "<tr><th>" + esc(t.d) + "</th><td>" + esc(t.ev) + cite(" " + (t.src || ""), notes) + '<br><span class="by">' + esc(t.by) + "</span></td></tr>";
    }
    return out + "</tbody></table>";
  } });
  h += chapter({ kicker: "Reference", title: "Glossary", rows: (notes) => {
    let g = "", out = "";
    for (const t of EX.glossary) {
      if (t.g !== g) { if (g) out += "</dl>"; out += "<h2>" + esc(t.g) + '</h2><dl class="gl">'; g = t.g; }
      out += "<dt>" + esc(t.term) + "</dt><dd>" + esc(t.def) + cite(" " + (t.src || ""), notes) + "</dd>";
    }
    return out + "</dl>";
  } });
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
function cover(vol, sub, blurb) {
  return page("Cover", `<section class="cover"><p class="kicker">Private copy · Edition as of ${ASOF}</p><h1>HKDA Brief</h1>
  <p class="sub">Hong Kong digital-asset rules for a bank's head of compliance</p><div class="rule"></div>
  <h2>Volume ${vol}</h2><p class="vt">${esc(sub)}</p><p class="blurb">${esc(blurb)}</p>
  <p class="disc">${DISCLAIMER}<br>Official sources: Hong Kong Monetary Authority (HKMA), Securities and Futures Commission (SFC), Financial Services and the Treasury Bureau (FSTB), the Legislative Council and other Hong Kong government bodies.</p></section>`);
}

const findPages = (pdf) => JSON.parse(execFileSync("python3", ["-c", `
import sys,json,re,pymupdf
d=pymupdf.open(sys.argv[1]); out={}
for i,p in enumerate(d):
    for m in re.findall(r'@@CH(\\d{3})@@', p.get_text()):
        out.setdefault(int(m), i+1)
print(json.dumps(out))`, pdf]).toString());

async function build(browser, vol, sub, blurb, bodyFn) {
  CH = 0; toc.length = 0;
  const body = bodyFn();
  const headerTemplate = `<div style="font:7.5pt Georgia,serif;color:#777;width:100%;padding:0 20mm 0 26mm;display:flex;justify-content:space-between"><span>HKDA Brief · Volume ${vol}: ${esc(sub)}</span><span>As of ${ASOF}</span></div>`;
  const footerTemplate = `<div style="font:7pt Georgia,serif;color:#777;width:100%;padding:0 20mm 0 26mm;display:flex;justify-content:space-between"><span>${DISCLAIMER}</span><span style="font-size:8.5pt;color:#333"><span class="pageNumber"></span></span></div>`;
  const opts = { format: "A4", printBackground: true, displayHeaderFooter: true, headerTemplate, footerTemplate,
    margin: { top: "20mm", bottom: "18mm", left: "26mm", right: "20mm" } };
  const pg = await browser.newPage();
  const render = async (pages, file) => {
    const html = page("HKDA Brief Volume " + vol, HOWTO + tocHtml(pages) + body);
    fs.writeFileSync(path.join(TMP, `vol${vol}.html`), html);
    await pg.goto("file://" + path.join(TMP, `vol${vol}.html`), { waitUntil: "load" });
    await pg.evaluate(() => document.fonts.ready);
    await pg.pdf({ path: file, ...opts });
  };
  const pass1 = path.join(TMP, `vol${vol}-pass1.pdf`);
  await render(null, pass1);
  const pages = findPages(pass1);
  const main = path.join(TMP, `vol${vol}-main.pdf`);
  await render(pages, main);
  const check = findPages(main);
  const moved = Object.keys(pages).filter((k) => pages[k] !== check[k]);
  if (moved.length) throw new Error(`Volume ${vol}: contents page numbers moved on second pass: ${moved.join(",")}`);
  // cover (no header/footer), then merge
  await pg.setContent(cover(vol, sub, blurb), { waitUntil: "load" });
  await pg.evaluate(() => document.fonts.ready);
  const cov = path.join(TMP, `vol${vol}-cover.pdf`);
  await pg.pdf({ path: cov, format: "A4", printBackground: true, margin: { top: "0", bottom: "0", left: "0", right: "0" } });
  const final = path.join(OUT, `HKDA-Brief-Volume-${vol}.pdf`);
  execFileSync("python3", ["-c", `
import sys,pypdf
w=pypdf.PdfWriter()
for f in sys.argv[2:]: w.append(f)
w.add_metadata({"/Title":"HKDA Brief - Volume ${vol}","/Author":"HKDA Brief","/Subject":"As of ${ASOF}"})
w.write(sys.argv[1])`, final, cov, main]);
  // Word-friendly HTML (contents without page numbers)
  fs.writeFileSync(path.join(TMP, `HKDA-Brief-Volume-${vol}.html`),
    page("HKDA Brief Volume " + vol, `<section class="cover plain"><h1>HKDA Brief</h1><h2>Volume ${vol}: ${esc(sub)}</h2><p>Edition as of ${ASOF}. ${DISCLAIMER}</p></section>` +
      HOWTO + tocHtml({}) + body).replace(/<span class="mk">[^<]*<\/span>/g, ""));
  await pg.close();
  const n = execFileSync("python3", ["-c", "import sys,pypdf;print(len(pypdf.PdfReader(sys.argv[1]).pages))", final]).toString().trim();
  console.log(`Volume ${vol}: ${toc.length} contents entries, ${n} pages -> ${final}`);
}

const browser = await chromium.launch({ executablePath: process.env.CHROME || undefined });
await build(browser, 1, "The rules", "Parts A to E: the regulators, the regimes, what they mean for a bank, capital, AML, technology, tax and the policy pipeline. Plus a profile of every official project.", vol1);
await build(browser, 2, "Business and opportunities", "Part F, sixteen business lines, six case studies, a Hong Kong, Singapore and Dubai comparison, the timeline and the glossary.", vol2);
await browser.close();
