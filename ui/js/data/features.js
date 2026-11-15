/**
 * data/features.js — accessors for GeoJSON features (the single source of truth for property names).
 *
 * Responsibility: KEYS lists every property name each field may use, first match wins.
 * The first name in each list is the one your firms_country_analysis.geojson actually has:
 *   iso_a3, country, continent, area_km2, total_fire_pixels, fire_density_per_10k_km2,
 *   peak_burning_month, season_duration_months, autocorr_12month,
 *   mean_frp_mw, max_frp_mw, daytime_fire_pct
 * If your data gains a new column or a renamed one, change it here only.
 * Depends on: utils/format.js
 */

import { valueFrom, number, normalizeIso } from "../utils/format.js";

const KEYS = {
  name: ["country", "name", "name_long", "admin", "NAME", "ADMIN"],
  iso: ["iso_a3", "adm0_a3", "sov_a3", "ISO_A3", "ADM0_A3"],
  continent: ["continent", "CONTINENT"],
  area: ["area_km2", "area"],
  totalPixels: ["total_fire_pixels", "total_fires", "fire_pixels"],
  density: ["fire_density_per_10k_km2", "fire_density", "density"],
  peakMonth: ["peak_burning_month", "peak_month"],
  seasonMonths: ["season_duration_months", "fire_season_duration", "season_duration"],
  autocorr12: ["autocorr_12month", "lag_12_autocorr", "autocorr_12", "autocorrelation"],
  meanFrp: ["mean_frp_mw", "mean_frp", "avg_frp", "frp"],
  maxFrp: ["max_frp_mw", "max_frp", "maximum_frp"],
  daytimePct: ["daytime_fire_pct", "daytime_percent", "daytime_proportion", "daytime_share", "daytime_fires"],
  pixelCount: ["total_fire_pixels", "fire_count", "count", "detections", "pixel_count", "value", "intensity"],
  pixelName: ["region_name", "sensor_region", "cell_id", "pixel_id", "name"],
  confidence: ["mean_confidence", "confidence"],
  sensor: ["satellite", "instrument", "sensor"],
  regionId: ["cell_id", "pixel_id", "region_id", "id"],
};

export function featureProperties(feature) {
  return feature?.properties || {};
}

const prop = (feature, key, fallback = null) => valueFrom(featureProperties(feature), KEYS[key], fallback);
const numeric = (feature, key, fallback = null) => number(prop(feature, key), fallback);

/* ---- country features ---- */

export function countryName(feature) {
  return prop(feature, "name", "Unknown country");
}

export function countryIso(feature) {
  return normalizeIso(prop(feature, "iso"));
}

export function countryContinent(feature) {
  return prop(feature, "continent");
}

export function countryArea(feature) {
  return numeric(feature, "area");
}

export function totalFirePixels(feature) {
  return numeric(feature, "totalPixels");
}

export function countryDensity(feature) {
  return numeric(feature, "density", 0);
}

export function peakMonth(feature) {
  return prop(feature, "peakMonth");
}

export function seasonMonths(feature) {
  return numeric(feature, "seasonMonths");
}

export function autocorr12(feature) {
  return numeric(feature, "autocorr12");
}

export function meanFrp(feature) {
  return numeric(feature, "meanFrp");
}

export function maxFrp(feature) {
  return numeric(feature, "maxFrp");
}

/* Always returns 0–100 (or null). `*_pct` / `*_percent` columns are already percentages;
   proportion-style columns (0–1) are scaled up. */
export function daytimePercent(feature) {
  const p = featureProperties(feature);
  for (const key of KEYS.daytimePct) {
    const value = number(p[key]);
    if (value === null) continue;
    if (key.endsWith("_pct") || key.endsWith("_percent")) return value;
    return Math.abs(value) <= 1 ? value * 100 : value;
  }
  return null;
}

/* ---- pixel / sensor-region features ---- */

export function pixelCount(feature) {
  return numeric(feature, "pixelCount", 0);
}

export function pixelName(feature) {
  return prop(feature, "pixelName");
}

export function pixelConfidence(feature) {
  return numeric(feature, "confidence");
}

export function pixelSensor(feature) {
  return prop(feature, "sensor");
}

export function pixelRegionId(feature) {
  return prop(feature, "regionId", feature?.id ?? null);
}

/* [lng, lat] for Point features, else [null, null]. */
export function pointCoordinates(feature) {
  if (feature?.geometry?.type !== "Point") return [null, null];
  return [number(feature.geometry.coordinates?.[0]), number(feature.geometry.coordinates?.[1])];
}

/* ---- geometry filters ---- */

export function polygonFeatures(features) {
  return features.filter((feature) => ["Polygon", "MultiPolygon"].includes(feature?.geometry?.type));
}

export function pointFeatures(features) {
  return features.filter((feature) => feature?.geometry?.type === "Point");
}
