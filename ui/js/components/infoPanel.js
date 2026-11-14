import { MONTH_NAMES } from "../constants.js";
import { formatNumber } from "../js/utils.js";

function setText(id, text) {
  document.getElementById(id).textContent = text;
}

function withUnit(formatted, unit) {
  return formatted === "N/A" ? "N/A" : `${formatted}${unit}`;
}

export function updateInfoPanel(feature) {
  if (!feature?.properties) {
    return;
  }

  const p = feature.properties;

  setText("countryName", p.country ?? p.name ?? p.NAME ?? "Unknown Country");
  setText("iso", `${p.iso_a3 ?? "N/A"} • MODIS FIRMS`);
  setText("continent", p.continent ?? "N/A");
  setText("totalFires", formatNumber(p.total_fire_pixels));
  setText(
    "density",
    withUnit(formatNumber(p.fire_density_per_10k_km2, 2), " / 10k km²"),
  );
  setText("peakMonth", MONTH_NAMES[Number(p.peak_burning_month)] ?? "N/A");

  const season = Number(p.season_duration_months);
  setText("seasonDuration", Number.isFinite(season) ? `${season} months` : "N/A");

  setText("autocorr", formatNumber(p.autocorr_12month, 3));
  setText("meanFrp", withUnit(formatNumber(p.mean_frp_mw, 2), " MW"));
  setText("maxFrp", withUnit(formatNumber(p.max_frp_mw, 2), " MW"));
  setText("daytime", withUnit(formatNumber(p.daytime_fire_pct, 1), "%"));
}
