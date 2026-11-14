import { DENSITY_BINS, NO_DATA_COLOR } from "./constants.js";

export function formatNumber(value, decimals = 0) {
  if (value === null || value === undefined || value === "") {
    return "N/A";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "N/A";
  }

  return number.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function densityColor(value) {
  const density = Number(value);

  if (!Number.isFinite(density)) {
    return NO_DATA_COLOR;
  }

  return DENSITY_BINS.find((bin) => density < bin.max).color;
}

/* Log scale keeps countries with extreme fire counts from dominating the globe. */
export function polygonHeight(feature) {
  const fires = Number(feature.properties?.total_fire_pixels);

  if (!Number.isFinite(fires) || fires <= 0) {
    return 0.006;
  }

  return Math.min(0.16, 0.01 + Math.log10(fires + 1) * 0.018);
}
