// Interactive timeline ribbon (pipeline/site/templates/_timeline.html).
// Feature-detects its own markup and no-ops if absent, same pattern
// site.js already uses for the document-search feature. Every marker/pill
// is a real <a href> and works with this script absent entirely -- hover/
// focus tooltips and the shared <details> fallback list are the only
// things this file adds, never the sole way to reach the underlying
// card/document/trajectory entry.
(function () {
  var ribbons = document.querySelectorAll("[data-timeline-root]");
  if (!ribbons.length) {
    return;
  }

  // Positions the shared tooltip element under the given target (a
  // Band 1 .timeline-marker or a Band 2 .ahead-pill), clamped to the
  // ribbon's own width so it never overflows past either edge. Shared by
  // both bands so the two hover/focus experiences match, per the P7
  // spec's "matching the ribbon's existing tooltip pattern".
  function positionTooltip(ribbon, tooltip, target) {
    tooltip.hidden = false;
    var rect = target.getBoundingClientRect();
    var ribbonRect = ribbon.getBoundingClientRect();
    var left = rect.left - ribbonRect.left;
    var maxLeft = ribbonRect.width - tooltip.offsetWidth;
    tooltip.style.left = Math.max(0, Math.min(left, maxLeft)) + "px";
    tooltip.style.top = rect.bottom - ribbonRect.top + 4 + "px";
  }

  ribbons.forEach(function (ribbon) {
    var tooltip = ribbon.querySelector(".timeline-tooltip");
    var markers = ribbon.querySelectorAll(".timeline-marker");
    var pills = ribbon.querySelectorAll(".ahead-pill");
    if (!tooltip || (!markers.length && !pills.length)) {
      return;
    }

    function hideTooltip() {
      tooltip.hidden = true;
    }

    function showMarkerTooltip(marker) {
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

      positionTooltip(ribbon, tooltip, marker);
    }

    // Band 2's own tooltip: the pill already shows its window, event text,
    // and a confidence label inline (see _timeline.html), so this only
    // adds what ISN'T already visible on the pill face -- the pillar name
    // (a real pillar color is on the pill's border, but not everyone can
    // read color alone) and a plain-language expansion of "announced" vs
    // "indicated". Same textContent-only construction as showMarkerTooltip
    // -- pillar name and event text both ultimately come from analyst-
    // authored content.
    function showPillTooltip(pill) {
      var pillarName = pill.getAttribute("data-pillar-name") || "";
      var confidence = pill.getAttribute("data-confidence") || "";
      var confidenceText =
        confidence === "announced"
          ? "Officially announced by a regulator"
          : "Indicated, not yet formally announced";

      tooltip.textContent = "";
      if (pillarName) {
        var pillarEl = document.createElement("strong");
        pillarEl.textContent = pillarName;
        tooltip.appendChild(pillarEl);
        tooltip.appendChild(document.createTextNode(" — "));
      }
      tooltip.appendChild(document.createTextNode(confidenceText));

      positionTooltip(ribbon, tooltip, pill);
    }

    markers.forEach(function (marker) {
      marker.addEventListener("pointerenter", function () {
        showMarkerTooltip(marker);
      });
      marker.addEventListener("pointerleave", hideTooltip);
      marker.addEventListener("focus", function () {
        showMarkerTooltip(marker);
      });
      marker.addEventListener("blur", hideTooltip);
    });

    pills.forEach(function (pill) {
      pill.addEventListener("pointerenter", function () {
        showPillTooltip(pill);
      });
      pill.addEventListener("pointerleave", hideTooltip);
      pill.addEventListener("focus", function () {
        showPillTooltip(pill);
      });
      pill.addEventListener("blur", hideTooltip);
    });

    ribbon.addEventListener("keydown", function (event) {
      if (event.key === "Escape") {
        hideTooltip();
      }
    });
  });
})();
