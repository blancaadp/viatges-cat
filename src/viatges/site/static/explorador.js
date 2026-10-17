// Explorador de viatges: filtra, ordena i pagina al navegador les dades de dades/viatges.json.
(async () => {
  const base = document.body.dataset.base;
  const PAGE = 50;
  const eur = new Intl.NumberFormat("ca-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 });
  const num = new Intl.NumberFormat("ca-ES");
  const ZERO = {
    imputat_a_altre: "Import imputat a un altre registre",
    pagat_per_tercers: "Pagat per tercers",
    pendent: "Import pendent",
    sense_despesa: "Import 0",
  };
  const norm = (s) => (s ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  const date = (iso) => (iso ? iso.slice(8, 10) + "/" + iso.slice(5, 7) + "/" + iso.slice(0, 4) : "—");

  const form = document.getElementById("filtres");
  const tbody = document.getElementById("files");
  const resum = document.getElementById("resum");
  const pagina = document.getElementById("pagina");
  const prev = document.getElementById("anterior");
  const next = document.getElementById("seguent");

  let data;
  try {
    data = await (await fetch(`${base}dades/viatges.json`)).json();
  } catch {
    resum.textContent = "No s'han pogut carregar les dades.";
    return;
  }
  const idx = Object.fromEntries(data.columns.map((c, i) => [c, i]));
  const trips = data.rows.map((r) => {
    const t = Object.fromEntries(data.columns.map((c) => [c, r[idx[c]]]));
    t.paisos = (t.paisos_iso2 || "").split(";").filter(Boolean);
    t.text = norm([t.nom, t.carrec, t.destinacio, t.motiu, t.paisos.map((p) => data.paisos[p]).join(" ")].join(" "));
    return t;
  });

  // Opcions dels desplegables
  const fill = (name, values, label = (v) => v) => {
    const select = form.elements[name];
    for (const v of values) select.add(new Option(label(v), v));
  };
  fill("any", [...new Set(trips.map((t) => t.data_inici_iso?.slice(0, 4)).filter(Boolean))].sort().reverse());
  fill("ambit", [...new Set(trips.map((t) => t.ambit).filter(Boolean))].sort((a, b) => a.localeCompare(b, "ca")));
  fill("pais", Object.keys(data.paisos).sort((a, b) => data.paisos[a].localeCompare(data.paisos[b], "ca")), (k) => data.paisos[k]);

  // Estat inicial des de l'URL (p. ex. ?pais=JP des de la pàgina d'inici)
  const params = new URLSearchParams(location.search);
  for (const name of ["q", "any", "ambit", "pais"]) if (params.has(name)) form.elements[name].value = params.get(name);
  form.elements.amaga.checked = params.get("amaga") === "1";

  let sortKey = "data_inici_iso";
  let sortDir = -1;
  let page = 0;
  let current = [];

  const filtered = () => {
    const q = norm(form.elements.q.value.trim()).split(/\s+/).filter(Boolean);
    const any = form.elements.any.value;
    const ambit = form.elements.ambit.value;
    const pais = form.elements.pais.value;
    const amaga = form.elements.amaga.checked;
    return trips.filter((t) =>
      q.every((w) => t.text.includes(w)) &&
      (!any || t.data_inici_iso?.startsWith(any)) &&
      (!ambit || t.ambit === ambit) &&
      (!pais || t.paisos.includes(pais)) &&
      (!amaga || (!t.exclos_analisi && !t.flag_duplicat)));
  };

  const badges = (t) => {
    const out = [];
    if (t.exclos_analisi) out.push("Durada anòmala");
    if (t.flag_duplicat) out.push("Duplicat");
    if (t.motiu_import_zero) out.push(ZERO[t.motiu_import_zero]);
    return out.map((b) => `<span class="badge">${b}</span>`).join("");
  };

  const render = () => {
    current = filtered().sort((a, b) => {
      const x = a[sortKey], y = b[sortKey];
      if (x == null) return 1;
      if (y == null) return -1;
      return (x < y ? -1 : x > y ? 1 : 0) * sortDir;
    });
    const pages = Math.max(1, Math.ceil(current.length / PAGE));
    page = Math.min(page, pages - 1);
    const slice = current.slice(page * PAGE, page * PAGE + PAGE);
    tbody.innerHTML = slice.map((t) => `
      <tr>
        <td class="num">${date(t.data_inici_iso)}</td>
        <td><a href="${base}viatge/${encodeURIComponent(t.id)}/">${esc(t.nom)}</a><span class="meta">${esc(t.carrec)}</span></td>
        <td>${esc(t.destinacio)}<span class="meta">${badges(t)}</span></td>
        <td class="num">${t.durada_dies ?? "—"}</td>
        <td class="num">${t.total_eur == null ? "—" : eur.format(t.total_eur)}</td>
      </tr>`).join("");
    const total = current.reduce((s, t) => s + (t.exclos_analisi || t.flag_duplicat ? 0 : t.total_eur || 0), 0);
    resum.textContent = `${num.format(current.length)} viatges · ${eur.format(total)} sense comptar duplicats ni exclosos`;
    pagina.textContent = `Pàgina ${page + 1} de ${pages}`;
    prev.disabled = page === 0;
    next.disabled = page >= pages - 1;
    for (const b of document.querySelectorAll("th button")) {
      b.setAttribute("aria-sort", b.dataset.sort === sortKey ? (sortDir > 0 ? "ascending" : "descending") : "none");
    }
  };

  const syncUrl = () => {
    const p = new URLSearchParams();
    for (const name of ["q", "any", "ambit", "pais"]) if (form.elements[name].value) p.set(name, form.elements[name].value);
    if (form.elements.amaga.checked) p.set("amaga", "1");
    history.replaceState(null, "", p.size ? `?${p}` : location.pathname);
  };

  form.addEventListener("input", () => { page = 0; syncUrl(); render(); });
  prev.addEventListener("click", () => { page--; render(); });
  next.addEventListener("click", () => { page++; render(); });
  for (const b of document.querySelectorAll("th button")) {
    b.addEventListener("click", () => {
      sortDir = sortKey === b.dataset.sort ? -sortDir : -1;
      sortKey = b.dataset.sort;
      render();
    });
  }

  document.getElementById("csv").addEventListener("click", () => {
    const cols = ["id", "data_inici_iso", "data_fi_iso", "durada_dies", "nom", "carrec", "ambit", "destinacio", "motiu", "total_eur", "exclos_analisi", "flag_duplicat", "motiu_import_zero"];
    const cell = (v) => (v == null ? "" : /[",\n;]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));
    const csv = [cols.join(","), ...current.map((t) => cols.map((c) => cell(t[c])).join(","))].join("\n");
    const url = URL.createObjectURL(new Blob(["﻿" + csv], { type: "text/csv;charset=utf-8" }));
    const a = Object.assign(document.createElement("a"), { href: url, download: "viatges-filtrats.csv" });
    a.click();
    URL.revokeObjectURL(url);
  });

  render();
})();
