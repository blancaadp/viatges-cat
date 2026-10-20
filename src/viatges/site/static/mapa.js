// Mapa de bombolles: tria la mesura (viatges o despesa) i la zona (món o Europa).
// Sense JavaScript es veu el mapa del món amb els viatges.
for (const figure of document.querySelectorAll(".mapa")) {
  for (const button of figure.querySelectorAll(".map-controls button")) {
    button.addEventListener("click", () => {
      const [key, value] = Object.entries(button.dataset)[0];
      figure.dataset[key] = value;
      for (const b of button.parentElement.querySelectorAll("button")) {
        b.setAttribute("aria-pressed", b === button);
      }
    });
  }
}
