import { DENSITY_BINS } from "../constants.js";

export function renderLegend(container = document.getElementById("legendRows")) {
  container.innerHTML = DENSITY_BINS.map(
    (bin) => `
      <div class="legendRow">
        <span class="legendBox" style="background: ${bin.color}"></span>
        ${bin.label}
      </div>`,
  ).join("");
}
