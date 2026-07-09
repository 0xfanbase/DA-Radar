// HK Digital Asset Radar -- minimal vanilla JS, no framework.
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
  searchBox.addEventListener("input", function () {
    var query = searchBox.value.trim().toLowerCase();
    rows.forEach(function (row) {
      var haystack = row.textContent.toLowerCase();
      row.style.display = haystack.indexOf(query) === -1 ? "none" : "";
    });
  });
});
