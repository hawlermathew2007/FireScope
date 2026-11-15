/**
 * data/loader.js — fetch GeoJSON files.
 *
 * Responsibility: expand "{year}" path templates, try each candidate path,
 * validate the FeatureCollection, and cache results per year in state.datasets.
 * Country and pixel files load in parallel; one failing does not block the other.
 * Depends on: settings.js, state.js
 */

import { config } from "../settings.js";
import { state } from "../state.js";

function pathsFor(templates, year) {
  return templates.map((template) => template.replaceAll("{year}", String(year)));
}

async function fetchGeoJson(templates, year) {
  const errors = [];
  for (const path of pathsFor(templates, year)) {
    try {
      const response = await fetch(path, { cache: "no-store" });
      if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
      const geojson = await response.json();
      if (geojson?.type !== "FeatureCollection" || !Array.isArray(geojson.features)) {
        throw new Error("not a FeatureCollection");
      }
      return { path, features: geojson.features.filter((feature) => feature?.geometry) };
    } catch (error) {
      errors.push(`${path}: ${error.message}`);
    }
  }
  throw new Error(errors.join(" | "));
}

/* Returns { country, pixel, countryPath, pixelPath, errors } for a year (cached). */
export async function loadYear(year) {
  if (state.datasets.has(year)) return state.datasets.get(year);

  const [countryResult, pixelResult] = await Promise.allSettled([
    fetchGeoJson(config.countryGeoJsonTemplates, year),
    fetchGeoJson(config.pixelGeoJsonTemplates, year),
  ]);

  const dataset = {
    country: countryResult.status === "fulfilled" ? countryResult.value.features : [],
    pixel: pixelResult.status === "fulfilled" ? pixelResult.value.features : [],
    countryPath: countryResult.status === "fulfilled" ? countryResult.value.path : null,
    pixelPath: pixelResult.status === "fulfilled" ? pixelResult.value.path : null,
    errors: [
      countryResult.status === "rejected" ? `Country: ${countryResult.reason.message}` : null,
      pixelResult.status === "rejected" ? `Pixel: ${pixelResult.reason.message}` : null,
    ].filter(Boolean),
  };
  state.datasets.set(year, dataset);
  return dataset;
}
