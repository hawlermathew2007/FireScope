/**
 * ui/legend.js — colour legend.
 *
 * Responsibility: rebuild the legend (title, unit, colour chips, low/high labels)
 * whenever the mode or year changes.
 * Depends on: constants.js, state.js, dom.js
 */

import { COUNTRY_COLORS, PIXEL_COLORS } from "../constants.js";
import { state } from "../state.js";
import { dom } from "../dom.js";

export function renderLegend() {
  const colors = state.mode === "country" ? COUNTRY_COLORS.slice(1) : PIXEL_COLORS;

  dom.legendTitle.textContent = state.mode === "country" ? "Fire density / 10,000 km²" : "Detection intensity";
  dom.legendUnit.textContent = `${state.year} ${state.mode}`;
  dom.legendRows.replaceChildren();

  const scale = document.createElement("div");
  scale.className = "legend-scale";
  scale.style.gridTemplateColumns = `repeat(${colors.length}, 1fr)`;
  colors.forEach((color) => {
    const chip = document.createElement("span");
    chip.className = "legend-chip";
    chip.style.background = color;
    scale.append(chip);
  });

  const labels = document.createElement("div");
  labels.className = "legend-labels";
  labels.innerHTML = state.mode === "country"
    ? "<span>10</span><span>250</span><span>2,000+</span>"
    : "<span>Low</span><span>Medium</span><span>High</span>";

  dom.legendRows.append(scale, labels);
}
