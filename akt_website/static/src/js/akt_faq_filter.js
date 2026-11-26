/* The FAQ list is one page of static entries, so its search box filters in
   the browser instead of asking the server - the Django build queried the
   database, and there is no database behind these entries any more. */
(function () {
  "use strict";
  document.addEventListener("DOMContentLoaded", function () {
    var form = document.querySelector(".feature-search");
    if (!form) { return; }
    var q = form.querySelector('input[name="q"]');
    var cat = form.querySelector('select[name="category"]');
    var items = Array.prototype.slice.call(
      document.querySelectorAll("[data-faq-item], .faq-card, .faq-list > li")
    );
    if (!items.length) { return; }

    function apply(event) {
      if (event) { event.preventDefault(); }
      var needle = (q && q.value || "").trim().toLowerCase();
      var want = cat && cat.value || "";
      items.forEach(function (item) {
        var text = (item.textContent || "").toLowerCase();
        var itemCat = item.getAttribute("data-faq-category") || "";
        item.hidden = !((!needle || text.indexOf(needle) !== -1) &&
                        (!want || itemCat === want));
      });
    }

    form.addEventListener("submit", apply);
    if (q) { q.addEventListener("input", apply); }
    if (cat) { cat.addEventListener("change", apply); }
    apply();
  });
})();
