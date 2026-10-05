(function () {
  "use strict";

  var app = document.getElementById("app");

  // Mobile sidebar
  var toggles = document.querySelectorAll("[data-sidebar-toggle]");
  function setSidebar(open) {
    app.classList.toggle("sidebar-open", open);
    toggles.forEach(function (btn) { btn.setAttribute("aria-expanded", String(open)); });
  }
  toggles.forEach(function (btn) {
    btn.addEventListener("click", function () { setSidebar(!app.classList.contains("sidebar-open")); });
  });
  document.querySelectorAll("[data-sidebar-close]").forEach(function (el) {
    el.addEventListener("click", function () { setSidebar(false); });
  });

  // Dropdown menus
  var dropdowns = document.querySelectorAll("[data-dropdown]");
  function closeDropdowns(except) {
    dropdowns.forEach(function (dd) {
      if (dd === except) return;
      dd.querySelector(".dropdown-menu").hidden = true;
      dd.querySelector("[data-dropdown-toggle]").setAttribute("aria-expanded", "false");
    });
  }
  dropdowns.forEach(function (dd) {
    var btn = dd.querySelector("[data-dropdown-toggle]");
    var menu = dd.querySelector(".dropdown-menu");
    btn.addEventListener("click", function (event) {
      event.stopPropagation();
      closeDropdowns(dd);
      menu.hidden = !menu.hidden;
      btn.setAttribute("aria-expanded", String(!menu.hidden));
    });
  });
  document.addEventListener("click", function () { closeDropdowns(null); });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeDropdowns(null);
      setSidebar(false);
    }
  });

  // Filter dropdowns submit their form as soon as they change
  document.querySelectorAll("select[data-autosubmit]").forEach(function (select) {
    select.addEventListener("change", function () { select.form.submit(); });
  });
})();
