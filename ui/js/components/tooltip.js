import { MONTH_NAMES } from "../constants.js";
import { formatNumber } from "../js/utils.js";

/* Returns the HTML string globe.gl shows on hover. Styled via .globe-tooltip in styles.css. */
export function tooltipHtml(feature) {
  const p = feature.properties;

  return `
    <div class="globe-tooltip">
      <b class="globe-tooltip-title">${p.country ?? "Unknown Country"}</b><br>
      Fire Pixels: <b>${formatNumber(p.total_fire_pixels)}</b><br>
      Density: <b>${formatNumber(p.fire_density_per_10k_km2, 2)}</b> / 10k km²<br>
      Peak: <b>${MONTH_NAMES[Number(p.peak_burning_month)] ?? "N/A"}</b>
    </div>`;
}
