/* HKDA Brief — single-page app. Data: data/sources.json, modules.json, projects.json */
(function () {
  "use strict";
  var S = { sources: [], byId: {}, modules: [], byCode: {}, projects: [], bySlug: {}, x: { obligations: [], talking: [], timeline: [], glossary: [], coming: [] }, biz: { lines: [], cases: [], compare: null }, byLine: {}, byCase: {} };
  var view = document.getElementById("view");
  document.documentElement.lang = "en";
  var DISCLAIMER = "For general information only. Not legal or regulatory advice. Always check the official source.";
  var ASOF = "25 Sep 2026";

  function rgHtml(t) { return esc(t).replace(/\(?\bids? ([0-9a-f]{12})\)?/g, function (_, id) { return '(<a href="#doc-' + id + '">see document</a>)'; }); }
  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]; }); }
  function store(k, v) { try { if (v === undefined) return JSON.parse(localStorage.getItem("hkda:" + k)); localStorage.setItem("hkda:" + k, JSON.stringify(v)); } catch (e) { return null; } }
  function fmtDate(d) {
    if (!d) return "Undated";
    var m = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"], p = d.split("-");
    return (p[2] ? +p[2] + " " : "") + (p[1] ? m[+p[1] - 1] + " " : "") + p[0];
  }
  function statusClass(st) {
    if (/not yet|pending|future|Conclusions|Consult|Bill|Pilot|target|Exploratory|proposals/i.test(st)) return "coming";
    if (/^(In force|Issued)/i.test(st)) return "live";
    return "";
  }
  function chip(st) { return '<span class="chip ' + statusClass(st) + '">' + esc(st) + "</span>"; }

  /* ---------- citations ---------- */
  var CLS = { industry: "Industry estimate", intl: "International official", foreign: "Foreign regulator", filing: "Company filing" };
  function citeHTML(id, loc) {
    var s = S.byId[id];
    var short = s ? s.p.join("/") + (s.d ? " " + s.d.slice(0, 4) : "") : "Source";
    var full = (s ? s.t : id) + (loc ? ", " + loc : "");
    var cls = s && s.cls ? " ind " + s.cls : "";
    var pre = s && s.cls ? (s.cls === "industry" ? "Estimate · " : s.cls === "intl" ? "International · " : s.cls === "foreign" ? "Foreign · " : "Filing · ") : "";
    return '<button type="button" class="cite' + cls + '" data-id="' + esc(id) + '" data-loc="' + esc(loc || "") + '" title="' + esc(full) + '" aria-label="' + (s && s.cls ? esc(CLS[s.cls]) : "Source") + ": " + esc(full) + '">' + esc(pre + short) + (loc ? " · " + esc(loc) : "") + "</button>";
  }
  function linkCitations(md) {
    return md.replace(/\[((?:S|I):[^\]]+)\]/g, function (whole, inner) {
      return inner.split(/;\s*(?=(?:S|I):)/).map(function (part) {
        var m = part.trim().match(/^(?:S|I):([0-9a-f]{12})\s*(?:,\s*([\s\S]*))?$/);
        return m ? citeHTML(m[1], (m[2] || "").trim()) : esc(whole);
      }).join(" ");
    });
  }
  function joinCites(md) { return md.replace(/\]\s*;\s*\[(S|I):/g, "] [$1:"); }
  function renderMD(md) {
    md = md.replace(/^(>\s*\*\*[^\n]*)$/gm, ">\n$1\n>");   // blank line before too, so a slot never joins a list above it   // each labelled slot of an analysis box on its own line
    var html = marked.parse(linkCitations(joinCites(md)), { mangle: false, headerIds: false })
      .replace(/\s?\(concept\)/g, ' <span class="concept" title="A general explanation of how the business works, not a sourced fact about Hong Kong">concept</span>');
    var tmp = document.createElement("div");
    tmp.innerHTML = html;
    var HEAD = { "Status board": "Where things stand", "Open items": "Open questions", "Common mix-ups": "Common misunderstandings",
      "Read these first": "Official documents to read first", "What your bank must do": "What your bank must or should do",
      "Key facts": "Key facts", "In 60 seconds": "In 60 seconds", "Related modules": "Related modules" };
    tmp.querySelectorAll("h2").forEach(function (h) { var t = h.textContent.trim(); if (HEAD[t]) h.textContent = HEAD[t]; });
    tmp.querySelectorAll("blockquote").forEach(function (b) {   // labelled analysis boxes
      var st = b.querySelector("strong");
      if (st && /^Analysis/.test(st.textContent)) { b.className = "analysis"; b.setAttribute("aria-label", "Analysis, not official"); }
    });
    tmp.querySelectorAll("table").forEach(function (t) { var w = document.createElement("div"); w.className = "tblwrap"; w.tabIndex = 0; w.setAttribute("role", "region"); w.setAttribute("aria-label", "Table (scrolls sideways)"); t.parentNode.insertBefore(w, t); w.appendChild(t); });
    tmp.querySelectorAll("a[href^='http']").forEach(function (a) { a.target = "_blank"; a.rel = "noopener"; });
    return tmp.innerHTML;
  }

  var lastFocus = null;
  function closeSheet(restore) {
    var root = document.getElementById("sheetroot");
    if (!root.innerHTML) return;
    root.innerHTML = ""; document.body.classList.remove("noscroll");
    if (restore !== false && lastFocus && document.contains(lastFocus)) lastFocus.focus();
    lastFocus = null;
  }
  function openSheet(id, loc) {
    var s = S.byId[id]; if (!s) return;
    var root = document.getElementById("sheetroot");
    lastFocus = document.activeElement;
    root.innerHTML = '<div class="scrim" data-close></div><div class="sheet" role="dialog" aria-modal="true" aria-labelledby="sheet-h"><div class="grab"></div>' +
      '<button class="close" data-close aria-label="Close">×</button>' +
      '<div class="meta">' + esc(s.p.join(" + ")) + " · " + esc(fmtDate(s.d)) + " · " + esc(s.ty) + (s.cls ? "" : " " + chip(s.st)) + "</div>" +
      '<h3 id="sheet-h">' + esc(s.t) + "</h3>" +
      (loc ? '<div class="locbig">' + esc(loc) + "</div>" : "") +
      (s.cls ? '<p class="note"><b>' + esc(CLS[s.cls]) + ".</b> " + (s.cls === "foreign" ? "Official in its own country, but not a Hong Kong source" : s.cls === "filing" ? "The company\u2019s own reported figures, not an official Hong Kong source" : s.cls === "intl" ? "An international body, not a Hong Kong source" : "Not an official Hong Kong source; figures are the publisher's estimates") + (s.geo ? ". Scope: " + esc(s.geo) : "") + (s.sponsor && !/none/i.test(s.sponsor) ? ". Paid for by: " + esc(s.sponsor) : "") + (s.conflict ? ". The publisher sells services in this market, so it may have an interest in the figures" : "") + ".</p>" : "") +
      (s.s ? "<p>" + esc(s.s) + "</p>" : "") +
      (s.cls && s.k.length ? '<ul class="small">' + s.k.slice(0, 6).map(function (k) { return "<li>" + esc(k[0]) + (k[1] ? ' <span class="loc">(' + esc(k[1]) + ")</span>" : "") + "</li>"; }).join("") + "</ul>" : "") +
      (s.rg ? '<p class="small muted"><b>' + (s.cls ? "How it was measured, and limits:" : "Where to look:") + "</b> " + rgHtml(s.rg) + "</p>" : "") +
      '<div class="acts">' + (s.u ? '<a class="btn primary" href="' + esc(s.u) + '" target="_blank" rel="noopener">' + (s.cls ? "Open the source ↗" : "Open official document ↗") + "</a>" : "") +
      '<a class="btn" href="#doc-' + esc(s.id) + '" data-close>Show in the document list</a></div>' +
      '<p class="small muted" style="margin-top:1rem">' + (s.cls ? "Summary written in our own words; check the original." : "Status as of " + ASOF + ". Summary written in our own words; always check the official text.") + "</p></div>";
    document.body.classList.add("noscroll");
    var closeBtn = root.querySelector(".close"); closeBtn.focus();
    root.querySelectorAll("[data-close]").forEach(function (el) {
      el.addEventListener("click", function () { closeSheet(!el.getAttribute("href")); });
    });
  }
  document.addEventListener("keydown", function (e) {
    var root = document.getElementById("sheetroot");
    if (!root.innerHTML) return;
    if (e.key === "Escape") { closeSheet(); return; }
    if (e.key === "Tab") {   // keep focus inside the dialog
      var f = root.querySelectorAll(".sheet a[href], .sheet button");
      if (!f.length) return;
      var first = f[0], last = f[f.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      else if (!root.contains(document.activeElement)) { e.preventDefault(); first.focus(); }
    }
  });
  document.addEventListener("click", function (e) {
    var c = e.target.closest(".cite"); if (c) { e.preventDefault(); openSheet(c.dataset.id, c.dataset.loc); }
  });

  /* ---------- helpers ---------- */
  function footer() { return "<footer>" + DISCLAIMER + " Content reflects official publications up to " + ASOF + '. <a href="#help">How to read this site</a></footer>'; }
  function readSet() { return store("read") || {}; }
  function projectsFor(code) {
    return S.projects.filter(function (p) { return new RegExp("\\b" + code + "\\b").test(p.coveredIn || ""); });
  }

  /* ---------- views ---------- */
  function vHome() {
    var read = readSet();
    var start = S.modules.filter(function (m) { return m.start; });
    var recent = S.sources.filter(function (s) { return !s.hid && s.imp !== "routine" && s.br !== "context"; }).slice(0, 6);
    var h = '<div class="read"><p class="kicker">Hong Kong · digital assets · bank compliance</p>' +
      '<h1 class="page-title">Know the rules, the projects and the moving pieces.</h1>' +
      '<p class="lede">' + S.modules.length + ' short modules built from ' + S.sources.filter(function (x) { return !x.cls; }).length + ' official HKMA, SFC and government documents. Every fact names its paragraph and links to the source.</p></div>';
    var mins = start.reduce(function (a, m) { return a + m.minutes; }, 0);
    h += '<h2 class="sec-h">Start here · about ' + Math.round(mins / 5) * 5 + ' minutes</h2><ol class="path">' + start.map(function (m) {
      return '<li><a href="#m-' + m.code + '"><div><b>' + esc(m.title) + '</b><br><span>' + m.code + " · " + m.minutes + " min" + (read[m.code] ? " · read" : "") + "</span></div><span>→</span></a></li>";
    }).join("") + "</ol>";
    if (S.x.changes && S.x.changes.length) {
      var c = S.x.changes[0];
      h += '<div class="box"><h3>What changed · ' + esc(c.d) + "</h3>" + renderMD(c.md) + "</div>";
    }
    if (S.biz.lines.length) h += '<h2 class="sec-h">Think like a COO</h2><div class="mcards"><a class="card" href="#business"><h3>Business and opportunities</h3><p>' + S.biz.lines.length + " business lines, " + S.biz.cases.length + ' case studies and how regulation shapes the P&amp;L.</p></a><a class="card" href="#m-F1"><h3>Part F: the course</h3><p>Where the money is, costs and capital, market structure, timing and scenarios, the COO toolkit, your path to COO.</p></a></div>';
    h += '<h2 class="sec-h">Before a meeting</h2><div class="mcards">' +
      '<a class="card" href="#briefings"><h3>Briefings</h3><p>Talking points for the CEO, CCO, business heads and Risk.</p></a>' +
      '<a class="card" href="#obligations"><h3>Obligations</h3><p>' + S.x.obligations.length + ' obligations as a checklist.</p></a>' +
      '<a class="card" href="#timeline"><h3>Timeline</h3><p>What is coming next, and every milestone since 2017.</p></a></div>';
    if (S.projects.length) {
      h += '<h2 class="sec-h">Projects and initiatives</h2><div class="grid">' + S.projects.slice(0, 6).map(projCard).join("") + '</div><p><a href="#projects">All projects and initiatives →</a></p>';
    }
    h += '<h2 class="sec-h">Recent publications that matter to banks</h2><ul class="docs">' + recent.map(docRow).join("") + '</ul><p><a href="#docs">All documents →</a></p>';
    h += footer();
    return h;
  }

  function vLearn() {
    var read = readSet(), parts = {};
    S.modules.forEach(function (m) { (parts[m.part] = parts[m.part] || { t: m.partTitle, ms: [] }).ms.push(m); });
    var done = S.modules.filter(function (m) { return read[m.code]; }).length;
    var ms = S.modules.filter(function (m) { return m.code !== "E3"; }).map(function (m) { return m.minutes; });
    var h = '<div class="read"><p class="kicker">Learn</p><h1 class="page-title">The course</h1><p class="lede">' + (function () { var o = {}; S.modules.forEach(function (m) { o[m.part] = 1; }); return Object.keys(o).length; })() + " parts and " + S.modules.length + " modules, most " + Math.min.apply(null, ms) + "–" + Math.max.apply(null, ms) + " minutes each. You have marked " + done + " of " + S.modules.length + " as read.</p></div>";
    Object.keys(parts).sort().forEach(function (k) {
      h += '<h2 class="sec-h">' + k + ". " + esc(parts[k].t) + '</h2><div class="grid">' + parts[k].ms.map(function (m) {
        return '<a class="card" href="#m-' + m.code + '"><div class="meta"><span class="code">' + m.code + "</span><span>" + m.minutes + " min</span>" + (m.start ? '<span class="chip live">Start here</span>' : "") + (read[m.code] ? '<span class="done">✓ Read</span>' : "") + "</div><h3>" + esc(m.title) + "</h3></a>";
      }).join("") + "</div>";
    });
    return h + footer();
  }

  function vModule(code) {
    var m = S.byCode[code]; if (!m) return notFound();
    var i = S.modules.indexOf(m), prev = S.modules[i - 1], next = S.modules[i + 1];
    var projs = projectsFor(code);
    var body = renderMD(m.md);
    if (projs.length) {
      var box = '<div class="box"><h3>Initiatives in this area</h3><div class="links">' + projs.map(function (p) { return '<a href="#p-' + p.slug + '">' + esc(p.title) + "</a>"; }).join("") + "</div></div>";
      body = body.replace(/(<h2[^>]*>Where things stand<\/h2>)/, box + "$1");
    }
    var read = readSet();
    var h = '<article class="article"><p class="kicker">' + m.code + " · " + esc(m.partTitle) + " · " + m.minutes + ' min</p><h1 class="page-title">' + esc(m.title) + "</h1>" + body + "</article>";
    h += '<p style="margin-top:2rem"><button class="btn" id="markread">' + (read[code] ? "✓ Marked as read" : "Mark as read") + "</button></p>";
    h += '<div class="pager">' + (prev ? '<a href="#m-' + prev.code + '"><small>Previous</small>' + esc(prev.title) + "</a>" : "<span></span>") + (next ? '<a href="#m-' + next.code + '" style="text-align:right"><small>Next</small>' + esc(next.title) + "</a>" : "<span></span>") + "</div>";
    return h + footer();
  }
  function afterModule(code) {
    var b = document.getElementById("markread");
    if (b) b.addEventListener("click", function () { var r = readSet(); r[code] = !r[code]; store("read", r); b.textContent = r[code] ? "✓ Marked as read" : "Mark as read"; });
    // copy buttons on talking points
    var hs = Array.prototype.slice.call(view.querySelectorAll("h2"));
    var tp = hs.filter(function (h) { return /Talking points/i.test(h.textContent); })[0];   // headings renamed for display only
    if (!tp) return;
    var el = tp.nextElementSibling;
    while (el && el.tagName !== "H2") {
      el.querySelectorAll && el.querySelectorAll("li").forEach(function (li) {
        var btn = document.createElement("button"); btn.className = "tp-copy"; btn.type = "button"; btn.textContent = "Copy";
        btn.addEventListener("click", function () {
          var c = li.cloneNode(true); c.querySelectorAll(".tp-copy").forEach(function (x) { x.remove(); });
          var text = c.innerText.trim();
          var done = function () { btn.textContent = "Copied"; };
          try { navigator.clipboard.writeText(text).then(done, sel); } catch (e) { sel(); }
          function sel() { var r = document.createRange(); r.selectNodeContents(li); var s = getSelection(); s.removeAllRanges(); s.addRange(r); btn.textContent = "Selected"; }
        });
        li.appendChild(btn);
      });
      el = el.nextElementSibling;
    }
  }

  function projCard(p) {
    return '<a class="card" href="#p-' + p.slug + '"><div class="meta">' + (p.status ? chip(p.status) : "") + (p.runBy ? "<span>" + esc(p.runBy) + "</span>" : "") + "</div><h3>" + esc(p.title) + "</h3><p>" + esc(p.oneLine || "") + "</p></a>";
  }
  function vProjects() {
    var h = '<div class="read"><p class="kicker">Projects and initiatives</p><h1 class="page-title">Every official initiative, in one place</h1><p class="lede">What each one is, who runs it, where it stands, and what it means for your bank.</p></div>';
    h += S.projects.length ? '<div class="grid">' + S.projects.map(projCard).join("") + "</div>" : '<div class="empty">Project profiles are being verified and will appear here shortly.</div>';
    return h + footer();
  }
  function vProject(slug) {
    var p = S.bySlug[slug]; if (!p) return notFound();
    return '<article class="article"><p class="kicker">Project or initiative</p><h1 class="page-title">' + esc(p.title) + "</h1>" + renderMD(p.md) + '</article><p style="margin-top:2rem"><a href="#projects">← All projects and initiatives</a></p>' + footer();
  }
  /* ---------- obligations, briefings, timeline, glossary ---------- */
  function inl(md) { return marked.parseInline(linkCitations(joinCites(md))); }
  function hashStr(t) { var h = 0; for (var i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) | 0; return (h >>> 0).toString(36); }
  function segBtns(list, cur, attr) { return '<div class="seg" role="group">' + list.map(function (v) { return '<button type="button" data-' + attr + '="' + esc(v) + '" aria-pressed="' + (v === cur) + '">' + esc(v) + "</button>"; }).join("") + "</div>"; }
  function modOpts(cur, withProjects) {
    var h = '<option value="">' + (withProjects ? "All modules and projects" : "All modules") + '</option><optgroup label="Modules">' + S.modules.filter(function (m) { return m.code !== "E3"; }).map(function (m) { return '<option value="' + m.code + '"' + (m.code === cur ? " selected" : "") + ">" + m.code + " " + esc(m.title) + "</option>"; }).join("") + "</optgroup>";
    if (withProjects) h += '<optgroup label="Projects">' + S.projects.map(function (p) { var v = "p-" + p.slug; return '<option value="' + v + '"' + (v === cur ? " selected" : "") + ">" + esc(p.title) + "</option>"; }).join("") + "</optgroup>";
    return h;
  }
  function byModule(items, render) {
    var h = "", last = "";
    items.forEach(function (it) {
      if (it.code !== last) {
        if (last) h += "</ul>"; last = it.code;
        var pj = /^p-/.test(it.code) ? S.bySlug[it.code.slice(2)] : null, m = S.byCode[it.code];
        h += '<h2 class="grp">' + esc(pj ? pj.title : m ? m.title : it.code) + ' <a href="#' + (pj ? it.code : "m-" + it.code) + '">' + (pj ? "Project" : it.code) + " →</a></h2><ul class=\"items\">";
      }
      h += render(it);
    });
    return h ? h + "</ul>" : '<div class="empty">Nothing matches. Try another filter.</div>';
  }

  var CATS = ["All", "Obligations", "Controls and monitoring", "Tell or consult the regulator", "Checks on partners"];
  var OB = { cat: "All", mod: "", q: "" };
  function vObligations() {
    var h = '<div class="read"><p class="kicker">Obligations</p><h1 class="page-title">What the bank must or should do</h1><p class="lede">Every requirement and expectation from the topic modules, sorted into four kinds. Each item keeps the regulator\u2019s own word: <b>must</b> means required; <b>should</b> means expected. Tick what your bank has covered. Ticks are saved on this device only.</p></div>';
    h += '<div class="tools"><label>Module<select id="ob-mod">' + modOpts(OB.mod) + '</select></label><label>Search<input id="ob-q" type="search" placeholder="e.g. cold storage, travel rule" value="' + esc(OB.q) + '"></label></div>';
    h += segBtns(CATS, OB.cat, "cat") + '<div class="count"><span id="ob-count"></span></div><div class="progress"><i id="ob-bar" style="width:0"></i></div><div id="ob-list"></div>';
    return h + footer();
  }
  function paintOb() {
    var ticks = store("ticks") || {}, q = OB.q.toLowerCase();
    var list = S.x.obligations.filter(function (o) { return (OB.cat === "All" || o.cat === OB.cat) && (!OB.mod || o.code === OB.mod) && (!q || o.md.toLowerCase().indexOf(q) >= 0); });
    var done = list.filter(function (o) { return ticks[hashStr(o.code + o.md)]; }).length;
    document.getElementById("ob-count").textContent = list.length + " items · " + done + " ticked";
    document.getElementById("ob-bar").style.width = (list.length ? Math.round(100 * done / list.length) : 0) + "%";
    document.getElementById("ob-list").innerHTML = byModule(list, function (o) {
      var k = hashStr(o.code + o.md), on = !!ticks[k];
      return '<li class="item' + (on ? " ticked" : "") + '"><input type="checkbox" data-tick="' + k + '"' + (on ? " checked" : "") + ' aria-label="Covered"><div class="txt"><span class="tag">' + esc(o.cat) + "</span>" + inl(o.md) + "</div></li>";
    });
  }
  function afterOb() {
    document.getElementById("ob-mod").addEventListener("change", function (e) { OB.mod = e.target.value; paintOb(); });
    document.getElementById("ob-q").addEventListener("input", function (e) { OB.q = e.target.value; paintOb(); });
    view.querySelectorAll("[data-cat]").forEach(function (b) { b.addEventListener("click", function () { OB.cat = b.dataset.cat; view.querySelectorAll("[data-cat]").forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); paintOb(); }); });
    document.getElementById("ob-list").addEventListener("change", function (e) {
      var k = e.target.dataset && e.target.dataset.tick; if (!k) return;
      var t = store("ticks") || {}; if (e.target.checked) t[k] = 1; else delete t[k]; store("ticks", t); paintOb();
    });
    paintOb();
  }

  var AUDS = ["CEO", "CCO", "Business", "Risk"];
  var AUDNAME = { CEO: "the CEO", CCO: "the Chief Compliance Officer", Business: "business heads", Risk: "Risk and the CRO" };
  var BR = { aud: "CEO", mod: "" };
  function vBriefings() {
    var h = '<div class="read"><p class="kicker">Briefings</p><h1 class="page-title">What to say, and to whom</h1><p class="lede">Short talking points for each audience, drawn from every module. Each one names its source. Copy a line, or copy the whole set before a meeting.</p></div>';
    h += segBtns(AUDS, BR.aud, "aud") + '<div class="tools"><label>Module or project<select id="br-mod">' + modOpts(BR.mod, true) + '</select></label><button type="button" class="btn" id="br-all">Copy all shown</button></div><p class="small muted" id="br-who"></p><div id="br-list"></div>';
    return h + footer();
  }
  function paintBr() {
    var list = S.x.talking.filter(function (t) { return t.aud === BR.aud && (!BR.mod || t.code === BR.mod); });
    document.getElementById("br-who").textContent = list.length + (list.length === 1 ? " point" : " points") + " for " + AUDNAME[BR.aud] + ".";
    document.getElementById("br-list").innerHTML = byModule(list, function (t) {
      return '<li class="item noc"><div class="txt">' + inl(t.md) + '</div><div class="acts2"><button type="button" class="tp-copy" data-copy>Copy</button></div></li>';
    });
  }
  function copyText(text, btn, node) {
    var ok = function () { btn.textContent = "Copied"; setTimeout(function () { btn.textContent = btn.dataset.label || "Copy"; }, 1500); };
    var sel = function () { var r = document.createRange(); r.selectNodeContents(node); var g = getSelection(); g.removeAllRanges(); g.addRange(r); btn.textContent = "Selected"; };
    try { navigator.clipboard.writeText(text).then(ok, sel); } catch (e) { sel(); }
  }
  function afterBr() {
    view.querySelectorAll("[data-aud]").forEach(function (b) { b.addEventListener("click", function () { BR.aud = b.dataset.aud; view.querySelectorAll("[data-aud]").forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); paintBr(); }); });
    document.getElementById("br-mod").addEventListener("change", function (e) { BR.mod = e.target.value; paintBr(); });
    document.getElementById("br-list").addEventListener("click", function (e) {
      var b = e.target.closest("[data-copy]"); if (!b) return; var li = b.closest("li"); copyText(li.querySelector(".txt").innerText.trim(), b, li.querySelector(".txt"));
    });
    var all = document.getElementById("br-all"); all.dataset.label = "Copy all shown";
    all.addEventListener("click", function () {
      var txt = Array.prototype.map.call(view.querySelectorAll("#br-list .txt"), function (n) { return "• " + n.innerText.trim(); }).join("\n");
      copyText("For " + AUDNAME[BR.aud] + ":\n" + txt, all, document.getElementById("br-list"));
    });
    paintBr();
  }

  var TLP = ["All", "HKMA", "SFC", "FSTB", "Government", "Other"];
  var TL = { by: "All", q: "" };
  function tlMatch(by) {
    if (TL.by === "All") return true;
    if (TL.by === "Other") return !/HKMA|SFC|FSTB|Government|LegCo|IRD/.test(by);
    if (TL.by === "Government") return /Government|LegCo|IRD/.test(by);
    return by.indexOf(TL.by) >= 0;
  }
  function vTimeline() {
    var h = '<div class="read"><p class="kicker">Timeline</p><h1 class="page-title">What happened, and what is next</h1><p class="lede">Upcoming items first, as the government or regulator has stated them (these are their targets, not forecasts). Then every milestone since 2017, newest first.</p></div>';
    h += segBtns(TLP, TL.by, "by") + '<div class="tools"><label>Search<input id="tl-q" type="search" placeholder="e.g. Ensemble, custody, CARF" value="' + esc(TL.q) + '"></label></div><div id="tl-body"></div>';
    return h + footer();
  }
  function paintTl() {
    var q = TL.q.toLowerCase();
    var co = S.x.coming.filter(function (c) { return tlMatch(c.by) && (!q || (c.what + " " + c.who).toLowerCase().indexOf(q) >= 0); });
    var h = '<h2 class="sec-h">Coming next <span class="small muted">(as of ' + ASOF + ")</span></h2>";
    h += co.length ? '<ul class="items">' + co.map(function (c) {
      return '<li class="item noc"><div class="txt"><span class="tag">' + esc(c.when) + " · " + esc(c.by) + "</span><b>" + inl(c.what) + "</b> " + chip(c.st.replace(/,.*$/, "")) + '<div class="small muted">Applies to: ' + esc(c.who) + "</div><div>" + inl(c.src) + "</div></div></li>";
    }).join("") + "</ul>" : '<div class="empty">Nothing upcoming matches.</div>';
    var ev = S.x.timeline.filter(function (t) { return tlMatch(t.by) && (!q || t.ev.toLowerCase().indexOf(q) >= 0); }).slice().sort(function (a, b) { return b.k.localeCompare(a.k); });
    h += '<h2 class="sec-h">Milestones, 2017 to 2026</h2>';
    var yr = "";
    ev.forEach(function (t) {
      var y = t.k.slice(0, 4);
      if (y !== yr) { if (yr) h += "</ul>"; yr = y; h += '<div class="year">' + y + '</div><ul class="tl">'; }
      h += '<li><div class="when">' + esc(t.d) + " · " + esc(t.by) + '</div><div class="ev">' + inl(t.ev) + "</div><div>" + inl(t.src) + "</div></li>";
    });
    h += yr ? "</ul>" : '<div class="empty">No milestones match.</div>';
    document.getElementById("tl-body").innerHTML = h;
  }
  function afterTl() {
    view.querySelectorAll("[data-by]").forEach(function (b) { b.addEventListener("click", function () { TL.by = b.dataset.by; view.querySelectorAll("[data-by]").forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); paintTl(); }); });
    document.getElementById("tl-q").addEventListener("input", function (e) { TL.q = e.target.value; paintTl(); });
    paintTl();
  }

  function vGloss() {
    var h = '<div class="read"><p class="kicker">Glossary</p><h1 class="page-title">Terms in plain English</h1><p class="lede">About 80 terms, each with the official document and paragraph that sets it out. For the full reference page, see <a href="#m-E3">module E3</a>.</p></div>';
    h += '<div class="tools"><label>Search<input id="gl-q" type="search" placeholder="e.g. RI, Group 1a, travel rule"></label></div><div id="gl-body"></div>';
    return h + footer();
  }
  function paintGl(q) {
    q = (q || "").toLowerCase(); var h = "", g = "";
    S.x.glossary.filter(function (t) { return !q || (t.term + " " + t.def).toLowerCase().indexOf(q) >= 0; }).forEach(function (t) {
      if (t.g !== g) { if (g) h += "</dl>"; g = t.g; h += '<h2 class="grp">' + esc(g) + '</h2><dl class="gl">'; }
      h += "<dt>" + esc(t.term) + "</dt><dd>" + inl(t.def) + " " + inl(t.src) + "</dd>";
    });
    document.getElementById("gl-body").innerHTML = g ? h + "</dl>" : '<div class="empty">No term matches.</div>';
  }
  function afterGl() { document.getElementById("gl-q").addEventListener("input", function (e) { paintGl(e.target.value); }); paintGl(""); }

  /* ---------- business (Part F) ---------- */
  var CHAIN = ["All", "Issue", "Distribute", "Trade", "Hold", "Settle and pay", "Finance", "Advise and manage"];
  var BZ = { chain: "All", seg: "" };
  function lineCard(l) {
    return '<a class="card" href="#b-' + l.slug + '"><div class="meta">' + (l.status ? chip(l.status) : "") + "<span>" + esc(l.chain.join(" · ")) + "</span></div><h3>" + esc(l.title) + '</h3><p class="small"><b>Bank role:</b> ' + esc(l.role) + '</p><p class="small muted">' + l.nS + " official " + (l.nS === 1 ? "fact" : "facts") + " · " + l.nI + " non-official " + (l.nI === 1 ? "figure" : "figures") + "</p></a>";
  }
  function caseCard(c, i) {
    return '<a class="card" href="#case-' + c.slug + '"><div class="meta"><span class="code">Case ' + (i + 1) + "</span><span>" + c.minutes + ' min</span><span class="chip">Fictional</span></div><h3>' + esc(c.title.replace(/^Case \d+:\s*/, "")) + "</h3><p>" + esc(c.teaser) + "</p></a>";
  }
  function vBusiness() {
    if (!S.biz.lines.length) return '<div class="read"><p class="kicker">Business and opportunities</p><h1 class="page-title">Where the money is, and what it takes</h1><p class="lede">This section is being written and checked. It will cover each digital-asset business line open to a Hong Kong bank, case studies, and a factual comparison with Singapore and the UAE.</p><p><a href="#learn">Go to the course \u2192</a></p></div>' + footer();
    var segs = {};
    S.biz.lines.forEach(function (l) { l.segments.split(/[,;/]\s*/).forEach(function (x) { x = x.trim(); if (x) segs[x.charAt(0).toUpperCase() + x.slice(1)] = 1; }); });
    var h = '<div class="read"><p class="kicker">Business and opportunities</p><h1 class="page-title">Where the money is, and what it takes</h1><p class="lede">Each digital-asset business a Hong Kong bank can run: its role, who pays, what drives cost and capital, the permission it needs, and what regulators have said. Written to help you think like a chief operating officer (COO).</p>' +
      '<p class="note">Facts are official and cited. Source buttons marked <b>Estimate</b>, <b>Filing</b>, <b>International</b> or <b>Foreign</b> point to named sources that are not official Hong Kong sources. Boxes marked <b>Analysis \u2014 not official</b> give a way to think about a question. They are not forecasts or advice.</p></div>';
    h += '<h2 class="sec-h">Business lines</h2>' + segBtns(CHAIN, BZ.chain, "chain") +
      '<div class="tools"><label>Client segment<select id="bz-seg"><option value="">All segments</option>' + Object.keys(segs).sort().map(function (x) { return '<option' + (x === BZ.seg ? " selected" : "") + ">" + esc(x) + "</option>"; }).join("") + '</select></label></div><div id="bz-list"></div>';
    if (S.biz.cases.length) h += '<h2 class="sec-h">Case studies</h2><p class="small muted">Short stories with invented people and firms, each with decisions to make. The Hong Kong rules in them are real and cited.</p><div class="grid">' + S.biz.cases.map(caseCard).join("") + "</div>";
    h += '<h2 class="sec-h">Go deeper</h2><div class="mcards">' + S.modules.filter(function (m) { return m.part === "F"; }).map(function (m) { return '<a class="card" href="#m-' + m.code + '"><div class="meta"><span class="code">' + m.code + "</span><span>" + m.minutes + " min</span></div><h3>" + esc(m.title) + "</h3></a>"; }).join("") +
      (S.biz.compare ? '<a class="card" href="#compare"><div class="meta"><span class="code">Compare</span></div><h3>' + esc(S.biz.compare.title) + "</h3><p>Hong Kong, Singapore and Dubai rules side by side, from each regulator\u2019s own documents. No ranking.</p></a>" : "") + "</div>";
    return h + footer();
  }
  function paintBz() {
    var list = S.biz.lines.filter(function (l) { return (BZ.chain === "All" || l.chain.indexOf(BZ.chain) >= 0) && (!BZ.seg || l.segments.toLowerCase().indexOf(BZ.seg.toLowerCase()) >= 0); });
    document.getElementById("bz-list").innerHTML = list.length ? '<div class="grid">' + list.map(lineCard).join("") + "</div>" : '<div class="empty">No business line matches. Try another filter.</div>';
  }
  function afterBz() {
    if (!document.getElementById("bz-list")) return;
    view.querySelectorAll("[data-chain]").forEach(function (b) { b.addEventListener("click", function () { BZ.chain = b.dataset.chain; view.querySelectorAll("[data-chain]").forEach(function (x) { x.setAttribute("aria-pressed", x === b); }); paintBz(); }); });
    document.getElementById("bz-seg").addEventListener("change", function (e) { BZ.seg = e.target.value; paintBz(); });
    paintBz();
  }
  function vLine(slug) {
    var l = S.byLine[slug]; if (!l) return notFound();
    var i = S.biz.lines.indexOf(l), prev = S.biz.lines[i - 1], next = S.biz.lines[i + 1];
    return '<article class="article"><p class="kicker">Business line' + (l.status ? " · " + esc(l.status) : "") + '</p><h1 class="page-title">' + esc(l.title) + "</h1>" + renderMD(l.md) + "</article>" +
      '<div class="pager">' + (prev ? '<a href="#b-' + prev.slug + '"><small>Previous</small>' + esc(prev.title) + "</a>" : "<span></span>") + (next ? '<a href="#b-' + next.slug + '" style="text-align:right"><small>Next</small>' + esc(next.title) + "</a>" : "<span></span>") + '</div><p style="margin-top:1.5rem"><a href="#business">\u2190 All business lines</a></p>' + footer();
  }
  function vCase(slug) {
    var c = S.byCase[slug]; if (!c) return notFound();
    var i = S.biz.cases.indexOf(c), prev = S.biz.cases[i - 1], next = S.biz.cases[i + 1];
    return '<article class="article case"><p class="kicker">Case study ' + (i + 1) + " · fictional · " + c.minutes + ' min</p><h1 class="page-title">' + esc(c.title.replace(/^Case \d+:\s*/, "")) + "</h1>" + renderMD(c.md) + "</article>" +
      '<div class="pager">' + (prev ? '<a href="#case-' + prev.slug + '"><small>Previous case</small>' + esc(prev.title.replace(/^Case \d+:\s*/, "")) + "</a>" : "<span></span>") + (next ? '<a href="#case-' + next.slug + '" style="text-align:right"><small>Next case</small>' + esc(next.title.replace(/^Case \d+:\s*/, "")) + "</a>" : "<span></span>") + '</div><p style="margin-top:1.5rem"><a href="#business">\u2190 Business and opportunities</a></p>' + footer();
  }
  function vCompare() {
    var c = S.biz.compare; if (!c) return notFound();
    return '<article class="article"><p class="kicker">Comparison · facts only, no ranking</p><h1 class="page-title">' + esc(c.title) + "</h1>" + renderMD(c.md) + '</article><p style="margin-top:1.5rem"><a href="#business">\u2190 Business and opportunities</a></p>' + footer();
  }

  function vHelp() {
    var rows = function (list) { return '<div class="tblwrap" tabindex="0" role="region" aria-label="Table (scrolls sideways)"><table><tbody>' + list.map(function (r) { return "<tr><th scope=\"row\">" + r[0] + "</th><td>" + r[1] + "</td></tr>"; }).join("") + "</tbody></table></div>"; };
    return '<article class="article"><p class="kicker">Help</p><h1 class="page-title">How to read this site</h1>' +
      '<p class="lede">Every fact on this site comes from an official document and shows exactly where it comes from. The Business section also uses clearly marked figures from named non-official sources: industry estimates, company filings, international bodies and foreign regulators. This page explains the labels.</p>' +
      "<h2>The words that carry legal weight</h2>" + rows([["<b>must</b> / <b>required</b>", "The law or a binding rule requires it."], ["<b>should</b> / <b>expects</b>", "The regulator expects it. It is guidance rather than law."], ["<b>may</b>", "It is allowed, not required."], ["<b>proposes</b> / <b>would</b>", "A proposal. It is not law yet."], ["<b>stated target</b>", "A plan or date the government or a regulator has announced. It is not a forecast by this site."]]) +
      "<h2>Status labels</h2>" + rows([[chip("In force"), "The rule applies now."], [chip("Issued, not yet in force"), "Published, but it starts later."], [chip("Consultation"), "The regulator is asking for views. Nothing is final."], [chip("Conclusions published"), "The consultation is finished and the final policy is set, but the law may not be made yet."], [chip("Bill"), "A draft law is before the Legislative Council (LegCo)."], [chip("Pilot"), "A trial with selected firms."], [chip("Exploratory"), "Regulators are studying the idea. No rule or live service yet."], [chip("Stated target"), "An announced plan or date."], [chip("Superseded"), "Replaced by a newer document. Kept for history."], [chip("Past event"), "A past event or announcement, kept for background."]]) +
      "<h2>Source buttons</h2>" + rows([['<span class="cite">HKMA 2026 \u00b7 para 11(n)</span>', "Solid blue buttons are official Hong Kong sources. Tap one to see who published it, when, the exact paragraph, and a link to the official document."], ['<span class="cite ind industry">Estimate \u00b7 Citi 2025</span>', "A figure from a named non-official source, such as a bank or consultancy. Treat it as an estimate, not a fact. Used only in the Business section."], ['<span class="cite ind intl">Intl \u00b7 BIS 2025</span>', "A report from an international official body, such as the Bank for International Settlements (BIS). Not a Hong Kong source."], ['<span class="cite ind foreign">Foreign \u00b7 MAS 2024</span>', "A document from a regulator outside Hong Kong, such as Singapore\u2019s MAS or Dubai\u2019s VARA. Official where it was issued, but not a Hong Kong source. Used only in the Business section."], ['<span class="cite ind filing">Filing \u00b7 OSL 2025</span>', "Figures from a company\u2019s own published results. We quote the numbers only and do not comment on the company."], ['<span class="concept">concept</span>', "A plain explanation of how a business works in general. It is not a fact about Hong Kong."], ['<span class="concept">illustrative</span>', "A round, made-up number used to show how something works. It is not an estimate."]]) +
      "<h2>Analysis boxes</h2><p>In the Business section, a shaded box marked <b>Analysis \u2014 not official</b> gives a way to think about a question. It is not a forecast and not advice. Each box asks one question, gives a way to think about it, lists what the answer depends on and the official signposts to watch, and ends by saying what it is not.</p>" +
      "<h2>Dates</h2><p>Everything reflects official publications up to " + ASOF + ". A scheduled update checks for new documents every weekday.</p></article>" + footer();
  }

  function vMore() {
    var items = [["help", "How to read this site", "What must, should and may mean, and what each label and button means."], ["business", "Business", "Business lines, case studies and the path to COO."], ["obligations", "Obligations", "Every obligation, as a checklist you can tick."], ["briefings", "Briefings", "Talking points for the CEO, CCO, business and Risk."], ["timeline", "Timeline", "What is coming next, and every milestone since 2017."], ["glossary", "Glossary", "About 80 terms in plain English, with sources."]];
    return '<div class="read"><p class="kicker">More</p><h1 class="page-title">Reference tools</h1></div><div class="mcards">' + items.map(function (i) { return '<a class="card" href="#' + i[0] + '"><h3>' + i[1] + "</h3><p>" + i[2] + "</p></a>"; }).join("") + "</div>" + footer();
  }
  function notFound() { return '<div class="empty">That page does not exist. <a href="#home">Go home</a></div>' + footer(); }

  /* ---------- documents ---------- */
  var PUBS = ["HKMA", "SFC", "FSTB", "Government", "LegCo", "HKEX", "IRD", "Other", "Industry"];
  var DEF = { q: "", pubs: [], ty: "", st: "", tp: "", br: "", from: "", to: "", sort: "new", hideRoutine: true, shown: 40 };
  function docState() { var s = store("docs") || {}; var o = {}; for (var k in DEF) o[k] = s[k] !== undefined ? s[k] : DEF[k]; o.shown = 40; o.focus = ""; return o; }
  function advCount() { return ["ty", "st", "tp", "br", "from", "to"].filter(function (k) { return DS[k]; }).length + (DS.sort !== "new" ? 1 : 0); }
  var DS;
  function docRow(s) {
    var det = '<details><summary>Summary and key points</summary><div class="det">' +
      (s.s ? "<p>" + esc(s.s) + "</p>" : "") +
      (s.w ? '<p><b>Why it matters to a bank:</b> ' + esc(s.w) + "</p>" : "") +
      (s.k.length ? "<ul>" + s.k.map(function (k) { return "<li>" + esc(k[0]) + (k[1] ? ' <span class="loc">(' + esc(k[1]) + ")</span>" : "") + "</li>"; }).join("") + "</ul>" : "") +
      (s.rg ? '<p class="small muted"><b>Where to look:</b> ' + rgHtml(s.rg) + "</p>" : "") +
      (s.u ? '<a class="btn primary" href="' + esc(s.u) + '" target="_blank" rel="noopener">' + (s.cls ? "Open the source ↗" : "Open official document ↗") + '</a>' : "") + "</div></details>";
    return '<li class="doc" id="doc-' + s.id + '"><div class="row1"><span>' + esc(fmtDate(s.d)) + "</span><span>·</span><span>" + esc(s.p.join(" + ")) + '</span><span class="chip src">' + esc(s.ty) + "</span>" + chip(s.st) +
      (s.br === "direct" ? (/^In force/.test(s.st) ? '<span class="chip live">Binds banks</span>' : '<span class="chip src">About banks</span>') : "") + "</div>" +
      (s.u ? '<a class="ttl" href="' + esc(s.u) + '" target="_blank" rel="noopener">' + esc(s.t) + '<span class="ext">↗</span></a>' : '<span class="ttl">' + esc(s.t) + "</span>") + det + "</li>";
  }
  function uniq(key, flat) { var o = {}; S.sources.forEach(function (s) { (flat ? s[key] : [s[key]]).forEach(function (v) { if (v) o[v] = 1; }); }); return Object.keys(o).sort(); }
  function opts(list, cur, all) { return '<option value="">' + all + "</option>" + list.map(function (v) { return '<option value="' + esc(v) + '"' + (v === cur ? " selected" : "") + ">" + esc(v) + "</option>"; }).join(""); }
  function filtered() {
    var q = DS.q.toLowerCase().trim();
    var list = S.sources.filter(function (s) {
      if (DS.focus) return s.id === DS.focus;
      if (s.hid) return false;
      if (DS.hideRoutine && s.imp === "routine") return false;
      var wantInd = DS.pubs.indexOf("Industry") >= 0, offPubs = DS.pubs.filter(function (p) { return p !== "Industry"; });
      if (s.cls) { if (!wantInd) return false; }                              // non-official only when asked for
      else if (offPubs.length ? !s.p.some(function (p) { return offPubs.indexOf(p) >= 0; }) : wantInd) return false;
      if (DS.ty && s.ty !== DS.ty) return false;
      if (DS.st && s.st !== DS.st) return false;
      if (DS.tp && s.tp.indexOf(DS.tp) < 0) return false;
      if (DS.br && s.br !== DS.br) return false;
      var lo = s.d.length === 7 ? s.d + "-01" : s.d, hi = s.d.length === 7 ? s.d + "-31" : s.d;   // month-only dates cover the whole month
      if (DS.from && (hi || "") < DS.from) return false;
      if (DS.to && (lo || "9999") > DS.to) return false;
      if (q && (s.t + " " + s.s + " " + s.tp.join(" ")).toLowerCase().indexOf(q) < 0) return false;
      return true;
    });
    list.sort(function (a, b) {
      if (DS.sort === "old") return (a.d || "9999").localeCompare(b.d || "9999");
      if (DS.sort === "title") return a.t.localeCompare(b.t);
      return (b.d || "").localeCompare(a.d || "");
    });
    return list;
  }
  function vDocs() {
    DS = docState();
    var h = '<div class="read"><p class="kicker">Documents</p><h1 class="page-title">All official documents</h1><p class="lede">Every HKMA, SFC and government document used to build this guide, newest first. Tap a title to open the official page or PDF. Tap \u201cSummary and key points\u201d for a plain-English summary. Industry, company and foreign documents used in the Business section are hidden unless you tap \u201cNon-official sources\u201d.</p></div>';
    h += '<form class="filters" id="docf" onsubmit="return false">' +
      '<label class="wide">Search<input id="f-q" type="search" placeholder="Title, summary or topic" value="' + esc(DS.q) + '"></label>' +
      '<div class="pubs" role="group" aria-label="Publisher">' + PUBS.map(function (p) { return '<button type="button" data-pub="' + p + '" aria-pressed="' + (DS.pubs.indexOf(p) >= 0) + '">' + (p === "Industry" ? "Non-official sources" : p) + "</button>"; }).join("") + "</div>" +
      '<details class="fx" id="fx"' + (advCount() || window.innerWidth >= 760 ? " open" : "") + '><summary>More filters' + (advCount() ? " (" + advCount() + " on)" : "") + '</summary><div class="fgrid">' +
      '<label>From<input id="f-from" type="date" value="' + esc(DS.from) + '"></label>' +
      '<label>To<input id="f-to" type="date" value="' + esc(DS.to) + '"></label>' +
      '<label>Type<select id="f-ty">' + opts(uniq("ty"), DS.ty, "All types") + "</select></label>" +
      '<label>Status<select id="f-st">' + opts(uniq("st"), DS.st, "All statuses") + "</select></label>" +
      '<label>Topic<select id="f-tp">' + opts(uniq("tp", true), DS.tp, "All topics") + "</select></label>" +
      '<label>Relevance to banks<select id="f-br"><option value="">All</option><option value="direct"' + (DS.br === "direct" ? " selected" : "") + '>About banks directly</option><option value="indirect"' + (DS.br === "indirect" ? " selected" : "") + '>About banks\u2019 partners and clients</option><option value="context"' + (DS.br === "context" ? " selected" : "") + '>Background only</option></select></label>' +
      '<label>Sort<select id="f-sort"><option value="new"' + (DS.sort === "new" ? " selected" : "") + '>Newest first</option><option value="old"' + (DS.sort === "old" ? " selected" : "") + '>Oldest first</option><option value="title"' + (DS.sort === "title" ? " selected" : "") + ">Title A–Z</option></select></label></div></details>" +
      '<label class="check wide"><input id="f-rt" type="checkbox"' + (DS.hideRoutine ? " checked" : "") + '> Hide routine notices (fraud warnings and lists of high-risk countries)</label>' +
      '</form><div id="focusnote"></div><div class="count"><span id="dcount"></span><button type="button" class="btn" id="f-reset" style="min-height:36px;padding:.3rem .8rem">Reset filters</button></div><ul class="docs" id="dlist"></ul><button type="button" class="btn more" id="dmore">Show more</button>';
    return h + footer();
  }
  function paintDocs() {
    var list = filtered();
    document.getElementById("dcount").textContent = list.length + " document" + (list.length === 1 ? "" : "s");
    document.getElementById("dlist").innerHTML = list.slice(0, DS.shown).map(docRow).join("") || '<li class="empty">No documents match. Try clearing a filter.</li>';
    document.getElementById("dmore").hidden = list.length <= DS.shown;
    if (!DS.focus) { var save = {}; for (var k in DS) if (k !== "shown" && k !== "focus") save[k] = DS[k]; store("docs", save); }
  }
  function afterDocs(focusId) {
    var bind = function (id, key, ev) { document.getElementById(id).addEventListener(ev || "change", function (e) { DS.focus = ""; document.getElementById("focusnote").innerHTML = ""; DS[key] = e.target.type === "checkbox" ? e.target.checked : e.target.value; DS.shown = 40; paintDocs(); }); };
    bind("f-q", "q", "input"); bind("f-from", "from"); bind("f-to", "to"); bind("f-ty", "ty"); bind("f-st", "st"); bind("f-tp", "tp"); bind("f-br", "br"); bind("f-sort", "sort"); bind("f-rt", "hideRoutine");
    view.querySelectorAll("[data-pub]").forEach(function (b) {
      b.addEventListener("click", function () { DS.focus = ""; document.getElementById("focusnote").innerHTML = ""; var p = b.dataset.pub, i = DS.pubs.indexOf(p); if (i >= 0) DS.pubs.splice(i, 1); else DS.pubs.push(p); b.setAttribute("aria-pressed", i < 0); DS.shown = 40; paintDocs(); });
    });
    document.getElementById("dmore").addEventListener("click", function () { DS.shown += 40; paintDocs(); });
    document.getElementById("f-reset").addEventListener("click", function () { store("docs", {}); route(); });
    if (focusId && S.byId[focusId]) {
      DS.focus = focusId;
      document.getElementById("focusnote").innerHTML = '<p class="note">Showing the document you followed from a citation' + (S.byId[focusId].hid ? " (a catalogue page; the documents it lists have their own entries)" : "") + '. <a href="#docs">Show all documents</a></p>';
    }
    paintDocs();
    if (focusId) {
      var el = document.getElementById("doc-" + focusId);
      if (el) { el.scrollIntoView({ block: "center" }); var d = el.querySelector("details"); if (d) d.open = true; el.style.borderColor = "var(--source)"; }
    }
  }

  /* ---------- router ---------- */
  function setNav(tab) {
    var more = { obligations: 1, briefings: 1, timeline: 1, glossary: 1, business: 1 };
    document.querySelectorAll(".nav a, .tabbar a").forEach(function (a) { if (a.getAttribute("href") === "#" + tab) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
    document.querySelectorAll(".tabbar a").forEach(function (a) { if (a.getAttribute("href") === "#more" && more[tab]) a.setAttribute("aria-current", "page"); });
    document.querySelectorAll(".nav a.m").forEach(function (a) { if (more[tab] && tab !== "business") a.setAttribute("aria-current", "page"); });
  }
  var TITLES = { help: "How to read this site", business: "Business and opportunities", compare: "Hong Kong, Singapore and the UAE", home: "Home", learn: "Learn", projects: "Projects", docs: "Documents", glossary: "Glossary", obligations: "Obligations", briefings: "Briefings", timeline: "Timeline", more: "More" };
  var stack = [], pos = {};
  function pageTitle(h) {
    if (/^m-/.test(h) && S.byCode[h.slice(2)]) return h.slice(2) + " " + S.byCode[h.slice(2)].title;
    if (/^p-/.test(h) && S.bySlug[h.slice(2)]) return S.bySlug[h.slice(2)].title;
    if (/^b-/.test(h) && S.byLine[h.slice(2)]) return S.byLine[h.slice(2)].title;
    if (/^case-/.test(h) && S.byCase[h.slice(5)]) return S.byCase[h.slice(5)].title;
    if (/^doc-/.test(h) && S.byId[h.slice(4)]) return S.byId[h.slice(4)].sl;
    return TITLES[h] || "Not found";
  }
  function route() {
    closeSheet(false);
    var h = (location.hash || "#home").slice(1) || "home", tab = "home", html, after;
    var prev = stack[stack.length - 1], back = stack.length > 1 && stack[stack.length - 2] === h;
    if (prev) pos[prev] = window.scrollY;
    if (back) stack.pop(); else if (prev !== h) stack.push(h);
    if (h === "home" || h === "") { html = vHome(); }
    else if (h === "learn") { tab = "learn"; html = vLearn(); }
    else if (h === "business") { tab = "business"; html = vBusiness(); after = afterBz; }
    else if (/^b-[a-z0-9-]+$/.test(h)) { tab = "business"; html = vLine(h.slice(2)); }
    else if (/^case-[a-z0-9-]+$/.test(h)) { tab = "business"; html = vCase(h.slice(5)); }
    else if (h === "compare") { tab = "business"; html = vCompare(); }
    else if (/^m-[A-F]\d[a-z]?$/.test(h)) { tab = "learn"; var c = h.slice(2); html = vModule(c); after = function () { afterModule(c); }; }
    else if (h === "projects") { tab = "projects"; html = vProjects(); }
    else if (/^p-[a-z0-9-]+$/.test(h)) { tab = "projects"; html = vProject(h.slice(2)); }
    else if (h === "docs") { tab = "docs"; html = vDocs(); after = function () { afterDocs(); }; }
    else if (/^doc-[0-9a-f]{12}$/.test(h)) { tab = "docs"; html = vDocs(); var id = h.slice(4); after = function () { afterDocs(id); }; }
    else if (h === "glossary") { tab = "glossary"; html = vGloss(); after = afterGl; }
    else if (h === "obligations") { tab = "obligations"; html = vObligations(); after = afterOb; }
    else if (h === "briefings") { tab = "briefings"; html = vBriefings(); after = afterBr; }
    else if (h === "timeline") { tab = "timeline"; html = vTimeline(); after = afterTl; }
    else if (h === "more") { tab = "more"; html = vMore(); }
    else if (h === "help") { tab = "more"; html = vHelp(); }
    else html = notFound();
    view.innerHTML = html; setNav(tab);
    document.title = pageTitle(h) + " · HKDA Brief";
    if (after) after();
    if (!/^doc-/.test(h)) window.scrollTo(0, back && pos[h] ? pos[h] : 0);
    if (prev) view.focus({ preventScroll: true });
  }
  window.addEventListener("hashchange", route);

  /* ---------- load ---------- */
  Promise.all(["sources", "modules", "projects", "extras", "business"].map(function (n) { return fetch("data/" + n + ".json").then(function (r) { return r.json(); }); }))
    .then(function (d) {
      S.sources = d[0]; S.sources.forEach(function (s) { S.byId[s.id] = s; });
      S.modules = d[1]; S.modules.forEach(function (m) { S.byCode[m.code] = m; });
      S.x = d[3];
      S.biz = d[4] || S.biz; S.biz.lines.forEach(function (l) { S.byLine[l.slug] = l; }); S.biz.cases.forEach(function (c) { S.byCase[c.slug] = c; });
      S.projects = d[2]; S.projects.forEach(function (p) { S.bySlug[p.slug] = p; });
      route();
    })
    .catch(function () { view.innerHTML = '<div class="empty">The content could not be loaded. Please reload the page.</div>'; });
})();
