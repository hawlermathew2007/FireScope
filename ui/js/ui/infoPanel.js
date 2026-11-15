/**
 * ui/infoPanel.js — the side panel that describes the hovered / pinned feature.
 *
 * Responsibility: write the feature name, subtitle, metric rows and trend chart.
 *   showFeature(f)      -> dispatches to showCountry / showPixel by current mode
 *   showEmpty()         -> placeholder state ("Hover over a country", feature counts, source path)
 *   syncClearButton()   -> show the "clear selection" button only while something is pinned
 * To add or reorder a metric, edit the setMetrics([...]) lists below.
 * Property names are NOT listed here — they come from data/features.js accessors.
 * Depends on: dom.js, state.js, utils/format.js, data/features.js, data/trend.js, ui/trendChart.js
 */

import { dom } from "../dom.js";
import { state } from "../state.js";
import { formatNumber, formatMonth } from "../utils/format.js";
import {
  countryName, countryIso, countryContinent, countryArea, totalFirePixels, countryDensity,
  peakMonth, seasonMonths, autocorr12, meanFrp, maxFrp, daytimePercent,
  pixelCount, pixelName, pixelConfidence, pixelSensor, pixelRegionId, pointCoordinates,
  featureProperties,
} from "../data/features.js";
import { featureTrend } from "../data/trend.js";
import { renderTrend } from "./trendChart.js";

function setMetrics(rows) {
  dom.metricGrid.replaceChildren();
  rows.forEach(([label, value]) => {
    const row = document.createElement("div");
    row.className = "metric";
    const name = document.createElement("span");
    name.className = "metric-name";
    name.textContent = label;
    const metricValue = document.createElement("span");
    metricValue.className = "metric-value";
    metricValue.textContent = value ?? "—";
    row.append(name, metricValue);
    dom.metricGrid.append(row);
  });
}

/* "123.4 MW", or "—" when the value is missing. */
function withUnit(value, digits, unit) {
  return value == null ? "—" : `${formatNumber(value, digits)} ${unit}`;
}

function showCountry(feature) {
  dom.selectionName.textContent = countryName(feature);
  dom.selectionMeta.textContent = [countryIso(feature), countryContinent(feature), state.year].filter(Boolean).join(" • ");

  setMetrics([
    ["Total fire pixels", formatNumber(totalFirePixels(feature))],
    ["Fire density", `${formatNumber(countryDensity(feature), 2)} / 10k km²`],
    ["Area", withUnit(countryArea(feature), 0, "km²")],
    ["Peak burning month", formatMonth(peakMonth(feature))],
    ["Fire season", withUnit(seasonMonths(feature), 0, "months")],
    ["12-month autocorrelation", formatNumber(autocorr12(feature), 3)],
    ["Mean FRP", withUnit(meanFrp(feature), 2, "MW")],
    ["Maximum FRP", withUnit(maxFrp(feature), 2, "MW")],
    ["Daytime fires", withUnit(daytimePercent(feature), 1, "%").replace(" %", "%")],
  ]);
  renderTrend(featureTrend(feature), `${state.year} monthly detections`);
}

function showPixel(feature) {
  const [lng, lat] = pointCoordinates(feature);
  const coordinates = lat !== null && lng !== null ? `${lat.toFixed(2)}°, ${lng.toFixed(2)}°` : null;
  const confidence = pixelConfidence(feature);
  const p = featureProperties(feature);

  dom.selectionName.textContent = pixelName(feature) || coordinates || "Sensor region";
  dom.selectionMeta.textContent = [coordinates, pixelSensor(feature), state.year].filter(Boolean).join(" • ");

  setMetrics([
    ["Detections", formatNumber(pixelCount(feature))],
    ["Fire density", formatNumber(countryDensity(feature), 2)],
    ["Mean FRP", withUnit(meanFrp(feature), 1, "MW")],
    ["Maximum FRP", withUnit(maxFrp(feature), 1, "MW")],
    ["Mean confidence", confidence == null ? "—" : `${formatNumber(confidence, 1)}%`],
    ["Peak month", formatMonth(peakMonth(feature))],
    ["Sensor", pixelSensor(feature) ?? "—"],
    ["Region ID", pixelRegionId(feature) ?? p.id ?? "—"],
  ]);
  renderTrend(featureTrend(feature), `${state.year} monthly detections`);
}

export function showFeature(feature) {
  if (state.mode === "country") showCountry(feature);
  else showPixel(feature);
}

export function showEmpty() {
  const features = state.mode === "country" ? state.current.country : state.current.pixel;
  const sourcePath = state.datasets.get(state.year)?.[state.mode === "country" ? "countryPath" : "pixelPath"];
  const noun = state.mode === "country" ? "country" : "sensor region";

  dom.selectionName.textContent = features.length
    ? `Hover over a ${noun}`
    : `${state.mode === "country" ? "Country" : "Pixel"} data unavailable`;
  dom.selectionMeta.textContent = `${state.year} FIRMS GeoJSON`;

  setMetrics([
    ["Features loaded", formatNumber(features.length)],
    ["Display year", String(state.year)],
    ["GeoJSON source", sourcePath || "Not loaded"],
    ["Interaction", features.length ? "Hover or click a feature" : "Check js/config.js file paths"],
  ]);
  renderTrend(
    [],
    `${state.year} monthly detections`,
    features.length ? "Hover over a feature to inspect its monthly data." : `No ${state.mode} GeoJSON was loaded for ${state.year}.`,
  );
}

export function syncClearButton() {
  dom.clearSelection.classList.toggle("is-visible", Boolean(state.selected));
}
