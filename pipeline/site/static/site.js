// Global Digital Asset Radar -- minimal vanilla JS, no framework.
// Jobs: (1) trigger the split-flap entrance animation on the Trajectory
// Board (CSS handles prefers-reduced-motion itself -- this script only
// ever adds a data attribute, never checks the media query directly, so
// disabling motion in CSS alone is sufficient); (2) client-side filter
// (search + jurisdiction chips) for the Document Library; (3) remember,
// per jurisdiction, whether a visitor has already dismissed the Current
// State page's "New here? How to read this board" panel; (4) the
// Glossary page's jurisdiction-chip filter, plus a small hook that clears
// that filter when a followed "See also" crosslink's target is currently
// hidden by it.

// Shared across the Document Library's and Glossary's jurisdiction-chip
// filters (P7 plan: "chip state persists via the same localStorage
// jurisdiction key used elsewhere on the site") -- one key, so a
// visitor's chosen jurisdiction carries over between the two pages.
// Follows the same "gdar-<feature>" convention already established by
// theme.js's "gdar-theme" and this file's own orientation-panel key
// below.
var JURISDICTION_FILTER_STORAGE_KEY = "gdar-jurisdiction-filter";

// Wires up the "New here? How to read this board" <details> panel on the
// Current State page (see pipeline/site/templates/current_state.html)
// so a visitor's choice to collapse it persists across visits, scoped to
// this device and this one jurisdiction. The panel's HTML `open`
// attribute is the real default (no-JS visitors always see it open --
// the correct, safe default per the P7 plan); this function only ever
// collapses it after the fact, once localStorage says a prior visit
// already dismissed it for this jurisdiction.
//
// Storage key follows the same "gdar-<feature>" convention theme.js
// already established for "gdar-theme", scoped per jurisdiction via the
// panel's own data-jurisdiction-id attribute (set by the template from
// jurisdiction_id) since dismissing the panel on one jurisdiction's page
// says nothing about whether a first-time visitor to a different
// jurisdiction has seen it.
function initOrientationPanel(panel) {
  var jurisdictionId = panel.getAttribute("data-jurisdiction-id") || "unknown";
  var storageKey = "gdar-orientation-dismissed-" + jurisdictionId;

  try {
    if (localStorage.getItem(storageKey) === "true") {
      panel.open = false;
    }
  } catch (e) {
    // Private-mode/blocked storage access -- panel stays open, same safe
    // default as a no-JS visitor gets.
  }

  panel.addEventListener("toggle", function () {
    try {
      localStorage.setItem(storageKey, panel.open ? "false" : "true");
    } catch (e) {
      // Not persisted -- the choice just won't be remembered on the next
      // visit, a reasonable degradation, not an error.
    }
  });
}

function readStoredJurisdictionFilter() {
  try {
    return localStorage.getItem(JURISDICTION_FILTER_STORAGE_KEY) || "all";
  } catch (e) {
    return "all";
  }
}

function writeStoredJurisdictionFilter(value) {
  try {
    localStorage.setItem(JURISDICTION_FILTER_STORAGE_KEY, value);
  } catch (e) {
    // Not persisted -- the choice just won't be remembered on the next
    // visit/page, a reasonable degradation, not an error.
  }
}

// A row/term is visible under a selected jurisdiction chip if it is
// tagged with that jurisdiction id directly, OR tagged "global" -- a
// "global" (regime-independent) entry applies under every specific
// jurisdiction selection, not just "All". Reused identically by the
// Document Library (rows never actually carry "global" today, since a
// document always belongs to exactly one real jurisdiction -- this
// still behaves correctly, it just never matches) and the Glossary
// (terms genuinely do carry "global").
function jurisdictionTagsMatch(dataJurisdictions, selected) {
  if (selected === "all") {
    return true;
  }
  var tags = (dataJurisdictions || "").split(/\s+/).filter(Boolean);
  return tags.indexOf(selected) !== -1 || tags.indexOf("global") !== -1;
}

function setPressedChip(chips, selected) {
  chips.forEach(function (chip) {
    chip.setAttribute("aria-pressed", chip.getAttribute("data-jurisdiction") === selected ? "true" : "false");
  });
}

// Document Library: combines the free-text search box with the
// jurisdiction chip row -- a row must satisfy BOTH to stay visible, so
// the two filters compose instead of one silently clobbering the other's
// display:none.
function initDocumentLibraryFilters() {
  var rows = document.querySelectorAll("#doc-table-body tr[data-jurisdictions]");
  var searchBox = document.getElementById("doc-search");
  var status = document.getElementById("doc-search-status");
  var chipRow = document.getElementById("doc-jurisdiction-filter");
  var chips = chipRow ? chipRow.querySelectorAll(".filter-chip") : [];

  if (!rows.length && !searchBox) {
    return;
  }

  var selected = readStoredJurisdictionFilter();
  // If the stored selection doesn't correspond to any chip actually
  // rendered on this build (e.g. a jurisdiction that was seeded when the
  // choice was stored, then never seen again on a later, differently-
  // seeded build), fall back to "All" rather than silently hiding every
  // row with no visible selected chip to explain why.
  var knownIds = Array.prototype.map.call(chips, function (chip) {
    return chip.getAttribute("data-jurisdiction");
  });
  if (knownIds.length && knownIds.indexOf(selected) === -1) {
    selected = "all";
  }

  function apply() {
    var query = searchBox ? searchBox.value.trim().toLowerCase() : "";
    var shown = 0;
    rows.forEach(function (row) {
      var jurisdictionMatch = jurisdictionTagsMatch(row.getAttribute("data-jurisdictions"), selected);
      var textMatch = query === "" || row.textContent.toLowerCase().indexOf(query) !== -1;
      var visible = jurisdictionMatch && textMatch;
      row.style.display = visible ? "" : "none";
      if (visible) {
        shown += 1;
      }
    });
    if (status) {
      status.textContent = shown + " of " + rows.length + " documents shown";
    }
  }

  setPressedChip(chips, selected);
  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      selected = chip.getAttribute("data-jurisdiction");
      writeStoredJurisdictionFilter(selected);
      setPressedChip(chips, selected);
      apply();
    });
  });

  if (searchBox) {
    searchBox.addEventListener("input", apply);
  }

  apply();
}

// Glossary: jurisdiction chip filter over the (always-in-DOM)
// .glossary-term entries, plus a same-page "See also" crosslink hook: if
// the hash in the URL points at a term currently hidden by the active
// filter, the filter clears back to "All" so the link actually resolves
// instead of silently landing on a hidden element.
function initGlossaryFilters() {
  var terms = document.querySelectorAll(".glossary-term[data-jurisdictions]");
  if (!terms.length) {
    return;
  }
  var chipRow = document.getElementById("glossary-jurisdiction-filter");
  var chips = chipRow ? chipRow.querySelectorAll(".filter-chip") : [];

  var selected = readStoredJurisdictionFilter();
  var knownIds = Array.prototype.map.call(chips, function (chip) {
    return chip.getAttribute("data-jurisdiction");
  });
  if (knownIds.length && knownIds.indexOf(selected) === -1) {
    selected = "all";
  }

  function apply() {
    terms.forEach(function (term) {
      term.style.display = jurisdictionTagsMatch(term.getAttribute("data-jurisdictions"), selected) ? "" : "none";
    });
    setPressedChip(chips, selected);
  }

  chips.forEach(function (chip) {
    chip.addEventListener("click", function () {
      selected = chip.getAttribute("data-jurisdiction");
      writeStoredJurisdictionFilter(selected);
      apply();
    });
  });

  apply();

  // Cross-link hook: a term's anchor is "term-{id}" (see glossary.html);
  // if the current hash names a term that "apply()" just hid, clear the
  // filter to "All" so every cross-jurisdiction "See also" link always
  // resolves to something visible, regardless of which chip was active
  // when it was followed.
  function ensureHashTargetVisible() {
    if (!location.hash) {
      return;
    }
    var target;
    try {
      target = document.querySelector(location.hash);
    } catch (e) {
      return; // not a valid CSS selector (e.g. a hash with special characters)
    }
    if (!target) {
      return;
    }
    var wrapper = target.closest(".glossary-term");
    if (wrapper && wrapper.style.display === "none") {
      selected = "all";
      writeStoredJurisdictionFilter(selected);
      apply();
    }
  }
  window.addEventListener("hashchange", ensureHashTargetVisible);
  ensureHashTargetVisible();
}

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".trajectory-row").forEach(function (row) {
    row.setAttribute("data-flap", "true");
  });

  var orientationPanel = document.getElementById("orientation-panel");
  if (orientationPanel) {
    initOrientationPanel(orientationPanel);
  }

  initDocumentLibraryFilters();
  initGlossaryFilters();
});
