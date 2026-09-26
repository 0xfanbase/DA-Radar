/* HKDA Brief — single-page app. Data: data/sources.json, modules.json, projects.json */
(function () {
  "use strict";
  var S = { sources: [], byId: {}, modules: [], byCode: {}, projects: [], bySlug: {} };
  var view = document.getElementById("view");
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
    if (/In force|Issued|Published/i.test(st)) return "live";
    if (/Superseded|Historical|Research/i.test(st)) return "";
    if (/Information/i.test(st)) return "";
    return "coming";
  }
  function chip(st) { return '<span class="chip ' + statusClass(st) + '">' + esc(st) + "</span>"; }

  /* ---------- citations ---------- */
  function citeHTML(id, loc) {
    var s = S.byId[id];
    var label = s ? s.sl : id;
    return '<button type="button" class="cite" data-id="' + esc(id) + '" data-loc="' + esc(loc || "") + '">' + esc(label) + (loc ? " · " + esc(loc) : "") + "</button>";
  }
  function linkCitations(md) {
    return md.replace(/\[S:([^\]]+)\]/g, function (_, inner) {
      return inner.split(/;\s*S:/).map(function (part) {
        var m = part.trim().match(/^([0-9a-f]{12})\s*(?:,\s*([\s\S]*))?$/);
        return m ? citeHTML(m[1], (m[2] || "").trim()) : "[S:" + esc(part) + "]";
      }).join(" ");
    });
  }
  function renderMD(md) {
    var html = marked.parse(linkCitations(md), { mangle: false, headerIds: false });
    var tmp = document.createElement("div");
    tmp.innerHTML = html;
    tmp.querySelectorAll("table").forEach(function (t) { var w = document.createElement("div"); w.className = "tblwrap"; t.parentNode.insertBefore(w, t); w.appendChild(t); });
    tmp.querySelectorAll("a[href^='http']").forEach(function (a) { a.target = "_blank"; a.rel = "noopener"; });
    return tmp.innerHTML;
  }

  function openSheet(id, loc) {
    var s = S.byId[id]; if (!s) return;
    var root = document.getElementById("sheetroot");
    root.innerHTML = '<div class="scrim" data-close></div><div class="sheet" role="dialog" aria-modal="true" aria-label="Source details"><div class="grab"></div>' +
      '<button class="close" data-close aria-label="Close">×</button>' +
      '<div class="meta">' + esc(s.p.join(" + ")) + " · " + esc(fmtDate(s.d)) + " · " + esc(s.ty) + " " + chip(s.st) + "</div>" +
      "<h3>" + esc(s.t) + "</h3>" +
      (loc ? '<div class="locbig">' + esc(loc) + "</div>" : "") +
      (s.s ? "<p>" + esc(s.s) + "</p>" : "") +
      (s.rg ? '<p class="small muted"><b>How to read it:</b> ' + rgHtml(s.rg) + "</p>" : "") +
      '<div class="acts">' + (s.u ? '<a class="btn primary" href="' + esc(s.u) + '" target="_blank" rel="noopener">Open official document ↗</a>' : "") +
      '<a class="btn" href="#doc-' + esc(s.id) + '" data-close>See in Documents</a></div>' +
      '<p class="small muted" style="margin-top:1rem">Status as of ' + ASOF + ". Summary written in our own words; always check the official text.</p></div>";
    var closeBtn = root.querySelector(".close"); closeBtn.focus();
    root.querySelectorAll("[data-close]").forEach(function (el) { el.addEventListener("click", function () { root.innerHTML = ""; }); });
  }
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") document.getElementById("sheetroot").innerHTML = ""; });
  document.addEventListener("click", function (e) {
    var c = e.target.closest(".cite"); if (c) { e.preventDefault(); openSheet(c.dataset.id, c.dataset.loc); }
  });

  /* ---------- helpers ---------- */
  function footer() { return "<footer>" + DISCLAIMER + " Content reflects official publications up to " + ASOF + ".</footer>"; }
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
      '<p class="lede">Twenty-one short modules built from 737 official HKMA, SFC and government documents. Every fact names its paragraph and links to the source.</p></div>';
    h += '<h2 class="sec-h">Start here · about 90 minutes</h2><ol class="path">' + start.map(function (m) {
      return '<li><a href="#m-' + m.code + '"><div><b>' + esc(m.title) + '</b><br><span>' + m.code + " · " + m.minutes + " min" + (read[m.code] ? " · read" : "") + "</span></div><span>→</span></a></li>";
    }).join("") + "</ol>";
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
    var h = '<div class="read"><p class="kicker">Learn</p><h1 class="page-title">The course</h1><p class="lede">Five parts, 21 modules, 10–15 minutes each. You have marked ' + done + " of 21 as read.</p></div>";
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
      body = body.replace(/(<h2[^>]*>Status board<\/h2>)/, box + "$1");
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
    var tp = hs.filter(function (h) { return /Talking points/i.test(h.textContent); })[0];
    if (!tp) return;
    var el = tp.nextElementSibling;
    while (el && el.tagName !== "H2") {
      el.querySelectorAll && el.querySelectorAll("li").forEach(function (li) {
        var btn = document.createElement("button"); btn.className = "tp-copy"; btn.type = "button"; btn.textContent = "Copy";
        btn.addEventListener("click", function () {
          var text = li.innerText.replace(/Copy$/, "").trim();
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
  function vGlossary() {
    var m = S.byCode.E3; if (!m) return notFound();
    return '<article class="article"><p class="kicker">Reference</p><h1 class="page-title">' + esc(m.title) + "</h1>" + renderMD(m.md) + "</article>" + footer();
  }
  function notFound() { return '<div class="empty">That page does not exist. <a href="#home">Go home</a></div>'; }

  /* ---------- documents ---------- */
  var PUBS = ["HKMA", "SFC", "FSTB", "Government", "LegCo", "HKEX", "IRD", "Other"];
  var DEF = { q: "", pubs: [], ty: "", st: "", tp: "", br: "", from: "", to: "", sort: "new", hideRoutine: true, shown: 40 };
  function docState() { var s = store("docs") || {}; var o = {}; for (var k in DEF) o[k] = s[k] !== undefined ? s[k] : DEF[k]; o.shown = 40; return o; }
  var DS;
  function docRow(s) {
    var det = '<details><summary>Summary and key points</summary><div class="det">' +
      (s.s ? "<p>" + esc(s.s) + "</p>" : "") +
      (s.w ? '<p><b>Why it matters to a bank:</b> ' + esc(s.w) + "</p>" : "") +
      (s.k.length ? "<ul>" + s.k.map(function (k) { return "<li>" + esc(k[0]) + (k[1] ? ' <span class="loc">(' + esc(k[1]) + ")</span>" : "") + "</li>"; }).join("") + "</ul>" : "") +
      (s.rg ? '<p class="small muted"><b>How to read it:</b> ' + rgHtml(s.rg) + "</p>" : "") +
      (s.u ? '<a class="btn primary" href="' + esc(s.u) + '" target="_blank" rel="noopener">Open official document ↗</a>' : "") + "</div></details>";
    return '<li class="doc" id="doc-' + s.id + '"><div class="row1"><span>' + esc(fmtDate(s.d)) + "</span><span>·</span><span>" + esc(s.p.join(" + ")) + '</span><span class="chip src">' + esc(s.ty) + "</span>" + chip(s.st) +
      (s.br === "direct" ? '<span class="chip live">Binds banks</span>' : "") + "</div>" +
      (s.u ? '<a class="ttl" href="' + esc(s.u) + '" target="_blank" rel="noopener">' + esc(s.t) + '<span class="ext">↗</span></a>' : '<span class="ttl">' + esc(s.t) + "</span>") + det + "</li>";
  }
  function uniq(key, flat) { var o = {}; S.sources.forEach(function (s) { (flat ? s[key] : [s[key]]).forEach(function (v) { if (v) o[v] = 1; }); }); return Object.keys(o).sort(); }
  function opts(list, cur, all) { return '<option value="">' + all + "</option>" + list.map(function (v) { return '<option value="' + esc(v) + '"' + (v === cur ? " selected" : "") + ">" + esc(v) + "</option>"; }).join(""); }
  function filtered() {
    var q = DS.q.toLowerCase().trim();
    var list = S.sources.filter(function (s) {
      if (s.hid) return false;
      if (DS.hideRoutine && s.imp === "routine") return false;
      if (DS.pubs.length && !s.p.some(function (p) { return DS.pubs.indexOf(p) >= 0; })) return false;
      if (DS.ty && s.ty !== DS.ty) return false;
      if (DS.st && s.st !== DS.st) return false;
      if (DS.tp && s.tp.indexOf(DS.tp) < 0) return false;
      if (DS.br && s.br !== DS.br) return false;
      if (DS.from && (s.d || "") < DS.from) return false;
      if (DS.to && (s.d || "9999") > DS.to) return false;
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
    var h = '<div class="read"><p class="kicker">Documents</p><h1 class="page-title">All official documents</h1><p class="lede">Every HKMA, SFC and government publication in the research, newest first. Each title opens the official page or PDF.</p></div>';
    h += '<form class="filters" id="docf" onsubmit="return false">' +
      '<label class="wide">Search<input id="f-q" type="search" placeholder="Title, summary or topic" value="' + esc(DS.q) + '"></label>' +
      '<div class="pubs" role="group" aria-label="Publisher">' + PUBS.map(function (p) { return '<button type="button" data-pub="' + p + '" aria-pressed="' + (DS.pubs.indexOf(p) >= 0) + '">' + p + "</button>"; }).join("") + "</div>" +
      '<label>From<input id="f-from" type="date" value="' + esc(DS.from) + '"></label>' +
      '<label>To<input id="f-to" type="date" value="' + esc(DS.to) + '"></label>' +
      '<label>Type<select id="f-ty">' + opts(uniq("ty"), DS.ty, "All types") + "</select></label>" +
      '<label>Status<select id="f-st">' + opts(uniq("st"), DS.st, "All statuses") + "</select></label>" +
      '<label>Topic<select id="f-tp">' + opts(uniq("tp", true), DS.tp, "All topics") + "</select></label>" +
      '<label>Relevance to banks<select id="f-br"><option value="">All</option><option value="direct"' + (DS.br === "direct" ? " selected" : "") + '>Binds banks directly</option><option value="indirect"' + (DS.br === "indirect" ? " selected" : "") + '>Counterparties and due diligence</option><option value="context"' + (DS.br === "context" ? " selected" : "") + '>Background</option></select></label>' +
      '<label>Sort<select id="f-sort"><option value="new"' + (DS.sort === "new" ? " selected" : "") + '>Newest first</option><option value="old"' + (DS.sort === "old" ? " selected" : "") + '>Oldest first</option><option value="title"' + (DS.sort === "title" ? " selected" : "") + ">Title A–Z</option></select></label>" +
      '<label class="check wide"><input id="f-rt" type="checkbox"' + (DS.hideRoutine ? " checked" : "") + '> Hide routine notices (fraud warnings, FATF list updates)</label>' +
      '</form><div class="count"><span id="dcount"></span><button type="button" class="btn" id="f-reset" style="min-height:36px;padding:.3rem .8rem">Reset filters</button></div><ul class="docs" id="dlist"></ul><button type="button" class="btn more" id="dmore">Show more</button>';
    return h + footer();
  }
  function paintDocs() {
    var list = filtered();
    document.getElementById("dcount").textContent = list.length + " document" + (list.length === 1 ? "" : "s");
    document.getElementById("dlist").innerHTML = list.slice(0, DS.shown).map(docRow).join("") || '<li class="empty">No documents match. Try clearing a filter.</li>';
    document.getElementById("dmore").hidden = list.length <= DS.shown;
    var save = {}; for (var k in DS) if (k !== "shown") save[k] = DS[k]; store("docs", save);
  }
  function afterDocs(focusId) {
    var bind = function (id, key, ev) { document.getElementById(id).addEventListener(ev || "change", function (e) { DS[key] = e.target.type === "checkbox" ? e.target.checked : e.target.value; DS.shown = 40; paintDocs(); }); };
    bind("f-q", "q", "input"); bind("f-from", "from"); bind("f-to", "to"); bind("f-ty", "ty"); bind("f-st", "st"); bind("f-tp", "tp"); bind("f-br", "br"); bind("f-sort", "sort"); bind("f-rt", "hideRoutine");
    view.querySelectorAll("[data-pub]").forEach(function (b) {
      b.addEventListener("click", function () { var p = b.dataset.pub, i = DS.pubs.indexOf(p); if (i >= 0) DS.pubs.splice(i, 1); else DS.pubs.push(p); b.setAttribute("aria-pressed", i < 0); DS.shown = 40; paintDocs(); });
    });
    document.getElementById("dmore").addEventListener("click", function () { DS.shown += 40; paintDocs(); });
    document.getElementById("f-reset").addEventListener("click", function () { store("docs", {}); route(); });
    if (focusId) {
      var target = S.byId[focusId];
      if (target) { DS.q = ""; DS.pubs = []; DS.ty = DS.st = DS.tp = DS.br = DS.from = DS.to = ""; DS.hideRoutine = false; var list = filtered(); var idx = list.indexOf(target); DS.shown = Math.max(40, idx + 1); }
    }
    paintDocs();
    if (focusId) {
      var el = document.getElementById("doc-" + focusId);
      if (el) { el.scrollIntoView({ block: "center" }); var d = el.querySelector("details"); if (d) d.open = true; el.style.borderColor = "var(--source)"; }
    }
  }

  /* ---------- router ---------- */
  function setNav(tab) {
    document.querySelectorAll(".nav a, .tabbar a").forEach(function (a) { if (a.getAttribute("href") === "#" + tab) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current"); });
  }
  function route() {
    var h = (location.hash || "#home").slice(1), tab = "home", html, after;
    if (h === "home" || h === "") { html = vHome(); }
    else if (h === "learn") { tab = "learn"; html = vLearn(); }
    else if (/^m-[A-E]\d$/.test(h)) { tab = "learn"; var c = h.slice(2); html = vModule(c); after = function () { afterModule(c); }; }
    else if (h === "projects") { tab = "projects"; html = vProjects(); }
    else if (/^p-[a-z0-9-]+$/.test(h)) { tab = "projects"; html = vProject(h.slice(2)); }
    else if (h === "docs") { tab = "docs"; html = vDocs(); after = function () { afterDocs(); }; }
    else if (/^doc-[0-9a-f]{12}$/.test(h)) { tab = "docs"; html = vDocs(); var id = h.slice(4); after = function () { afterDocs(id); }; }
    else if (h === "glossary") { tab = "glossary"; html = vGlossary(); }
    else html = notFound();
    view.innerHTML = html; setNav(tab);
    if (after) after(); else window.scrollTo(0, 0);
    if (!/^doc-/.test(h)) window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", route);

  /* ---------- load ---------- */
  Promise.all(["sources", "modules", "projects"].map(function (n) { return fetch("data/" + n + ".json").then(function (r) { return r.json(); }); }))
    .then(function (d) {
      S.sources = d[0]; S.sources.forEach(function (s) { S.byId[s.id] = s; });
      S.modules = d[1]; S.modules.forEach(function (m) { S.byCode[m.code] = m; });
      S.projects = d[2]; S.projects.forEach(function (p) { S.bySlug[p.slug] = p; });
      route();
    })
    .catch(function () { view.innerHTML = '<div class="empty">The content could not be loaded. Please reload the page.</div>'; });
})();
