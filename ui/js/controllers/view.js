/**
 * controllers/view.js — switching the view mode and the year.
 *
 * Responsibility:
 *   setMode(mode)  "country" <-> "pixel": reset selection, update buttons, header text,
 *                  hint, legend, layer and panel; warn if that mode has no data.
 *   setYear(year)  load that year's GeoJSON (with spinner), then re-apply the current mode.
 *                  `loadSequence` makes sure a slow earlier request can't overwrite a newer one.
 * Depends on: settings.js, state.js, dom.js, data/loader.js, globe/globe.js,
 *             ui/status.js, ui/legend.js, ui/infoPanel.js
 */

import { config } from "../settings.js";
import { state } from "../state.js";
import { dom } from "../dom.js";
import { loadYear } from "../data/loader.js";
import { renderCurrentLayer } from "../globe/globe.js";
import { showError, clearError, setLoading } from "../ui/status.js";
import { renderLegend } from "../ui/legend.js";
import { showEmpty, syncClearButton } from "../ui/infoPanel.js";

function resetSelection() {
  state.selected = null;
  state.selectedKind = null;
  state.hovered = null;
  syncClearButton();
}

export function setMode(mode) {
  if (!["country", "pixel"].includes(mode)) return;
  state.mode = mode;
  resetSelection();

  document.querySelectorAll(".view-button").forEach((button) => {
    const active = button.dataset.view === mode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  dom.panelMode.textContent = `${mode.toUpperCase()} VIEW • ${state.year}`;
  dom.subtitle.textContent = mode === "country"
    ? `${state.year} country-level fire density and seasonality`
    : `${state.year} prepared sensor-region heat layer`;
  dom.hintText.textContent = mode === "country"
    ? "Hover a country • click to pin • drag to rotate"
    : "Hover a heat pixel • click to pin • drag to rotate";

  renderLegend();
  renderCurrentLayer();
  showEmpty();

  const features = mode === "country" ? state.current.country : state.current.pixel;
  if (!features.length) showError(`No ${mode} GeoJSON was found for ${state.year}. Check js/config.js.`, true);
  else clearError();
}

export async function setYear(year) {
  if (!config.years.includes(Number(year))) return;

  const sequence = ++state.loadSequence;
  state.year = Number(year);
  dom.year.value = String(state.year);
  resetSelection();
  setLoading(true, `Loading ${state.year} GeoJSON…`);
  clearError();

  const dataset = await loadYear(state.year);
  if (sequence !== state.loadSequence) return;   // a newer year was requested meanwhile

  state.current = { country: dataset.country, pixel: dataset.pixel };
  setLoading(false);
  setMode(state.mode);

  if (!dataset.country.length && !dataset.pixel.length) {
    showError(`No GeoJSON files were found for ${state.year}. Update the templates in js/config.js.`);
  } else if (dataset.errors.length) {
    const missing = !dataset.country.length ? "country" : "pixel";
    showError(`${state.year} ${missing} GeoJSON was not found; the other view remains available.`, true);
  }
}
