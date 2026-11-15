/**
 * ui/controls.js — user input wiring.
 *
 * Responsibility:
 *   populateYears()  fill the year <select> from config.years (newest first)
 *   bindUi()         attach events: view buttons, year dropdown, clear button,
 *                    keyboard shortcuts (Esc = clear, C = country view, P = pixel view)
 * Depends on: settings.js, state.js, dom.js, controllers/view.js, controllers/selection.js
 */

import { config } from "../settings.js";
import { state } from "../state.js";
import { dom } from "../dom.js";
import { setMode, setYear } from "../controllers/view.js";
import { clearSelection } from "../controllers/selection.js";

export function populateYears() {
  const years = [...config.years].sort((a, b) => b - a);
  dom.year.replaceChildren(...years.map((year) => {
    const option = document.createElement("option");
    option.value = String(year);
    option.textContent = String(year);
    option.selected = year === state.year;
    return option;
  }));
  if (!years.includes(state.year)) state.year = config.defaultYear;
  dom.year.value = String(state.year);
}

export function bindUi() {
  document.querySelectorAll(".view-button").forEach((button) =>
    button.addEventListener("click", () => setMode(button.dataset.view)));

  dom.year.addEventListener("change", () => setYear(Number(dom.year.value)));
  dom.clearSelection.addEventListener("click", clearSelection);

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape") clearSelection();
    if (event.key.toLowerCase() === "c") setMode("country");
    if (event.key.toLowerCase() === "p") setMode("pixel");
  });
}
