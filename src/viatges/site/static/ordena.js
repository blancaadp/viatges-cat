// Taules ordenables (`table.sortable`): cada capçalera amb `data-col` ordena per la columna
// indicada, fent servir el valor numèric o de text de `data-v` de cada cel·la.
// Sense JavaScript les taules es veuen igualment, ordenades per defecte.
for (const table of document.querySelectorAll("table.sortable")) {
  const tbody = table.tBodies[0];
  const buttons = [...table.querySelectorAll("thead button[data-col]")];
  for (const button of buttons) {
    button.type = "button";
    button.addEventListener("click", () => {
      const col = Number(button.dataset.col);
      const text = button.dataset.type === "text";
      // Primer clic: text de A a Z, números de més a menys; després, alterna
      const current = button.getAttribute("aria-sort");
      const next = current === "ascending" ? -1 : current === "descending" ? 1 : text ? 1 : -1;
      const value = (row) => row.cells[col].dataset.v;
      const rows = [...tbody.rows].sort((a, b) =>
        (text ? value(a).localeCompare(value(b), "ca") : Number(value(a)) - Number(value(b))) * next
      );
      for (const r of rows) tbody.appendChild(r);
      for (const b of buttons) b.setAttribute("aria-sort", b === button ? (next > 0 ? "ascending" : "descending") : "none");
    });
  }
}
