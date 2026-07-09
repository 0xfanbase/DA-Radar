// Interactive timeline ribbon (pipeline/site/templates/_timeline.html).
// Feature-detects its own markup and no-ops if absent, same pattern
// site.js already uses for the document-search feature. Every marker is
// a real <a href> and works with this script absent entirely -- hover/
// focus tooltips and the shared <details> fallback list are the only
// things this file adds, never the sole way to reach the underlying
// card/document.
(function () {
  var ribbons = document.querySelectorAll("[data-timeline-root]");
  if (!ribbons.length) {
    return;
  }

  ribbons.forEach(function (ribbon) {
    var tooltip = ribbon.querySelector(".timeline-tooltip");
    var markers = ribbon.querySelectorAll(".timeline-marker");
    if (!tooltip || !markers.length) {
      return;
    }

    function showTooltip(marker) {
      var label = marker.querySelector(".timeline-marker-label");
      var date = marker.getAttribute("data-date") || "";
      var source = marker.getAttribute("data-source") || "";
      var title = label ? label.textContent : "";

      // Built with textContent only, never innerHTML -- card/document
      // titles are ultimately AI-generated or analyst-authored text.
      tooltip.textContent = "";
      var dateEl = document.createElement("strong");
      dateEl.textContent = date;
      tooltip.appendChild(dateEl);
      tooltip.appendChild(document.createTextNode(" — " + title));
      if (source) {
        tooltip.appendChild(document.createTextNode(" (" + source + ")"));
      }

      var rect = marker.getBoundingClientRect();
      var ribbonRect = ribbon.getBoundingClientRect();
      tooltip.style.left = rect.left - ribbonRect.left + "px";
      tooltip.style.top = rect.bottom - ribbonRect.top + 4 + "px";
      tooltip.hidden = false;
    }

    function hideTooltip() {
      tooltip.hidden = true;
    }

    markers.forEach(function (marker) {
      marker.addEventListener("pointerenter", function () {
        showTooltip(marker);
      });
      marker.addEventListener("pointerleave", hideTooltip);
      marker.addEventListener("focus", function () {
        showTooltip(marker);
      });
      marker.addEventListener("blur", hideTooltip);
    });

    ribbon.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        hideTooltip();
      }
    });
  });
})();
