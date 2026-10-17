// Pestanyes: sense JavaScript es veuen tots els panells; amb JavaScript, només el triat.
document.documentElement.classList.add("js");
for (const list of document.querySelectorAll('[role="tablist"]')) {
  const tabs = [...list.querySelectorAll('[role="tab"]')];
  const select = (tab) => {
    for (const t of tabs) {
      const on = t === tab;
      t.setAttribute("aria-selected", on);
      t.tabIndex = on ? 0 : -1;
      document.getElementById(t.getAttribute("aria-controls")).hidden = !on;
    }
  };
  tabs.forEach((tab, i) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (e) => {
      const step = { ArrowRight: 1, ArrowLeft: -1 }[e.key];
      if (!step) return;
      const next = tabs[(i + step + tabs.length) % tabs.length];
      next.focus();
      select(next);
    });
  });
  select(tabs.find((t) => t.getAttribute("aria-selected") === "true") || tabs[0]);
}

// Tooltip compartit per a tots els elements amb `data-tip` (ratolí, tacte i teclat).
(() => {
  const tip = document.querySelector(".tooltip");
  if (!tip) return;

  const show = (el, x, y) => {
    tip.textContent = el.dataset.tip;
    tip.hidden = false;
    const { width, height } = tip.getBoundingClientRect();
    const left = Math.min(Math.max(8, x + 12), window.innerWidth - width - 8);
    const top = y - height - 12 < 8 ? y + 16 : y - height - 12;
    tip.style.left = `${left}px`;
    tip.style.top = `${top}px`;
  };
  const hide = () => { tip.hidden = true; };

  document.addEventListener("pointermove", (e) => {
    const el = e.target.closest("[data-tip]");
    if (el) show(el, e.clientX, e.clientY);
    else hide();
  });
  document.addEventListener("focusin", (e) => {
    const el = e.target.closest("[data-tip]");
    if (!el) return;
    const r = el.getBoundingClientRect();
    show(el, r.left + r.width / 2, r.top);
  });
  document.addEventListener("focusout", hide);
  window.addEventListener("scroll", hide, { passive: true });
})();
