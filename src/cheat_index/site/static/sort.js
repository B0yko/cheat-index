(function () {
  "use strict";
  var collator = new Intl.Collator(undefined, { numeric: true, sensitivity: "base" });

  function key(cell) {
    var v = cell.getAttribute("data-sort");
    return v === null ? cell.textContent.trim() : v;
  }

  function sortBy(table, col, dir) {
    var body = table.tBodies[0];
    var rows = Array.prototype.map.call(body.rows, function (row, i) {
      return { row: row, v: key(row.cells[col]), i: i };
    });
    var numeric = rows.every(function (r) { return r.v === "" || isFinite(Number(r.v)); });
    rows.sort(function (a, b) {
      if (a.v === "" || b.v === "") return a.v === b.v ? a.i - b.i : a.v === "" ? 1 : -1;
      var d = numeric ? Number(a.v) - Number(b.v) : collator.compare(a.v, b.v);
      return d ? d * dir : a.i - b.i;
    });
    rows.forEach(function (r) { body.appendChild(r.row); });
  }

  document.querySelectorAll("table.sortable").forEach(function (table) {
    var heads = table.tHead.rows[0].cells;
    Array.prototype.forEach.call(heads, function (th, col) {
      var btn = document.createElement("button");
      btn.type = "button";
      while (th.firstChild) btn.appendChild(th.firstChild);
      th.appendChild(btn);
      btn.addEventListener("click", function () {
        var dir = th.getAttribute("aria-sort") === "ascending" ? -1 : 1;
        Array.prototype.forEach.call(heads, function (h) { h.removeAttribute("aria-sort"); });
        th.setAttribute("aria-sort", dir === 1 ? "ascending" : "descending");
        sortBy(table, col, dir);
      });
    });
  });
})();
