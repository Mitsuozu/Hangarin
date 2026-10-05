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

  // ---------- Motion ----------
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Count numbers up on the dashboard (stat cards and the progress ring)
  if (!reduceMotion) {
    document.querySelectorAll(".stat-value, .ring-value").forEach(function (el) {
      var match = el.textContent.trim().match(/^(\d+)(%?)$/);
      if (!match) return;
      var target = parseInt(match[1], 10);
      var suffix = match[2];
      if (target === 0) return;
      var duration = 900;
      var start = null;
      el.textContent = "0" + suffix;
      function tick(now) {
        if (start === null) start = now;
        var t = Math.min((now - start) / duration, 1);
        var eased = 1 - Math.pow(1 - t, 3);
        el.textContent = Math.round(target * eased) + suffix;
        if (t < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }

  // Completing a task: show the new state right away, let the animation play, then submit
  document.querySelectorAll("form.task-check").forEach(function (form) {
    form.addEventListener("submit", function (event) {
      if (reduceMotion || form.dataset.busy) return;
      event.preventDefault();
      form.dataset.busy = "1";
      var btn = form.querySelector(".check");
      var row = form.closest(".task, .row-item");
      var done = !btn.classList.contains("is-checked");
      btn.classList.toggle("is-checked", done);
      btn.classList.add("is-popping");
      btn.setAttribute("aria-pressed", String(done));
      if (row) row.classList.toggle("is-done", done);
      setTimeout(function () { form.submit(); }, 380);
    });
  });
})();
