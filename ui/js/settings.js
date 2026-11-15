/**
 * settings.js — runtime configuration.
 *
 * Responsibility: build the single `config` object the app reads.
 * Priority (lowest → highest):
 *   1. defaults below
 *   2. window.FIRMS_APP_CONFIG   (set by your classic js/config.js, loaded before main.js)
 *   3. URL query params          (?year=2022&country=...&pixels=...)
 * Depends on: nothing.
 */

const appConfig = window.FIRMS_APP_CONFIG || {};

export const config = {
  years: [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
  defaultYear: 2025,
  countryGeoJsonTemplates: ["data/firms_country_analysis_{year}.geojson"],
  pixelGeoJsonTemplates: ["data/firms_pixels_{year}.geojson"],
  maxTrendPoints: 12,
  initialPointOfView: { lat: 8, lng: 18, altitude: 2.15 },
  ...appConfig,
};

export const query = new URLSearchParams(window.location.search);

if (query.get("country")) config.countryGeoJsonTemplates = [query.get("country")];
if (query.get("pixels")) config.pixelGeoJsonTemplates = [query.get("pixels")];
