// Cercador de persones: filtra i ordena la taula ja generada a l'HTML (sense JS es veu sencera).
(() => {
  const input = document.getElementById("cerca-persona");
  const tbody = document.getElementById("persones");
  const resum = document.getElementById("resum-persones");
  const more = document.getElementById("mostra-totes");
  if (!input || !tbody) return;

  const INITIAL = 10;
  const norm = (s) => (s ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const rows = [...tbody.rows];
  // Cada paraula cercada ha de ser l'inici d'una paraula del nom o del càrrec ("illa" no troba "Villarroya")
  for (const r of rows) r.words = r.dataset.cerca.split(" ");
  let showAll = false;
  let sortKey = "total";
  let sortDir = -1;

  const render = () => {
    const words = norm(input.value.trim()).split(/\s+/).filter(Boolean);
    const matches = rows.filter((r) => words.every((w) => r.words.some((x) => x.startsWith(w))));
    matches.sort((a, b) => {
      const x = a.dataset[sortKey], y = b.dataset[sortKey];
      const cmp = sortKey === "nom" || sortKey === "darrer" ? x.localeCompare(y, "ca") : Number(x) - Number(y);
      return cmp * sortDir;
    });
    const limit = words.length || showAll ? matches.length : INITIAL;
    const visible = new Set(matches.slice(0, limit));
    for (const r of rows) r.hidden = !visible.has(r);
    for (const r of matches) tbody.appendChild(r); // aplica l'ordre
    more.hidden = words.length > 0 || showAll;
    if (words.length) {
      resum.textContent = matches.length === 1 ? "1 persona trobada." : `${matches.length} persones trobades.`;
    } else {
      resum.textContent = showAll ? `${rows.length} persones.` : `${rows.length} persones. Es mostren les ${INITIAL} primeres.`;
    }
    for (const b of document.querySelectorAll("#cercador th button")) {
      b.closest("th").setAttribute("aria-sort", b.dataset.sort === sortKey ? (sortDir > 0 ? "ascending" : "descending") : "none");
    }
  };

  input.addEventListener("input", () => {
    const p = new URLSearchParams(location.search);
    input.value ? p.set("q", input.value) : p.delete("q");
    history.replaceState(null, "", p.size ? `?${p}` : location.pathname);
    render();
  });
  // Amb un sol resultat, Retorn porta directament a la fitxa
  input.addEventListener("keydown", (e) => {
    if (e.key !== "Enter") return;
    const first = rows.find((r) => !r.hidden);
    const visible = rows.filter((r) => !r.hidden);
    if (visible.length === 1 && first) location.href = first.querySelector("a").href;
  });
  more.addEventListener("click", () => { showAll = true; render(); });
  for (const b of document.querySelectorAll("#cercador th button")) {
    b.addEventListener("click", () => {
      const key = b.dataset.sort;
      sortDir = key === sortKey ? -sortDir : key === "nom" ? 1 : -1;
      sortKey = key;
      render();
    });
  }

  input.value = new URLSearchParams(location.search).get("q") ?? "";
  render();
})();
