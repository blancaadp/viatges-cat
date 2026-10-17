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
