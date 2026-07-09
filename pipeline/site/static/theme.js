// Theme toggle: prefers-color-scheme is the default (handled purely by
// CSS media queries in style.css); this script only handles the explicit
// override -- clicking the button sets/persists a data-theme attribute,
// which wins over the OS preference via CSS specificity. The initial
// data-theme attribute (if a prior visit stored one) is already set by
// the inline script in base.html's <head>, before this file even loads,
// to avoid a flash of the wrong theme.
(function () {
  var STORAGE_KEY = "hkdar-theme";
  var toggle = document.getElementById("theme-toggle");
  if (!toggle) {
    return;
  }

  function storedTheme() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  function systemPrefersDark() {
    return (
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
    );
  }

  function effectiveTheme() {
    var explicit = document.documentElement.getAttribute("data-theme");
    if (explicit === "light" || explicit === "dark") {
      return explicit;
    }
    return systemPrefersDark() ? "dark" : "light";
  }

  function applyTheme(theme, persist) {
    document.documentElement.setAttribute("data-theme", theme);
    toggle.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
    if (persist) {
      try {
        localStorage.setItem(STORAGE_KEY, theme);
      } catch (e) {
        // Private-mode/blocked storage -- the choice just won't persist
        // across reloads, which is a reasonable degradation, not an error.
      }
    }
  }

  // Set the button's correct initial state on load, including the
  // OS-preference-only case where no data-theme attribute is set yet.
  applyTheme(effectiveTheme(), false);

  toggle.addEventListener("click", function () {
    var next = effectiveTheme() === "dark" ? "light" : "dark";
    applyTheme(next, true);
  });
})();
