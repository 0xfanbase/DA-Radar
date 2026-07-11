// Global Digital Asset Radar -- minimal vanilla JS, no framework.
// Two jobs: (1) trigger the split-flap entrance animation on the
// Trajectory Board (CSS handles prefers-reduced-motion itself -- this
// script only ever adds a data attribute, never checks the media query
// directly, so disabling motion in CSS alone is sufficient); (2)
// client-side filter for the Document Library search box.

document.addEventListener("DOMContentLoaded", function () {
  document.querySelectorAll(".trajectory-row").forEach(function (row) {
    row.setAttribute("data-flap", "true");
  });

  var searchBox = document.getElementById("doc-search");
  if (!searchBox) {
    return;
  }
  var rows = document.querySelectorAll("#doc-table-body tr");
  var status = document.getElementById("doc-search-status");
  searchBox.addEventListener("input", function () {
    var query = searchBox.value.trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (row) {
      var haystack = row.textContent.toLowerCase();
      var matches = haystack.indexOf(query) !== -1;
      row.style.display = matches ? "" : "none";
      if (matches) {
        shown += 1;
      }
    });
    if (status) {
      status.textContent = shown + " of " + rows.length + " documents shown";
    }
  });
});
