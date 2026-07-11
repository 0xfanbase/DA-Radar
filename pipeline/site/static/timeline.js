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
      var status = marker.getAttribute("data-status") || "";
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
      if (status && status !== "verified" && status !== "corrected") {
        var statusEl = document.createElement("div");
        statusEl.className = "timeline-tooltip-status";
        statusEl.textContent = status.charAt(0).toUpperCase() + status.slice(1);
        tooltip.appendChild(statusEl);
      }

      tooltip.hidden = false;
      var rect = marker.getBoundingClientRect();
      var ribbonRect = ribbon.getBoundingClientRect();
      var left = rect.left - ribbonRect.left;
      var maxLeft = ribbonRect.width - tooltip.offsetWidth;
      tooltip.style.left = Math.max(0, Math.min(left, maxLeft)) + "px";
      tooltip.style.top = rect.bottom - ribbonRect.top + 4 + "px";
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
