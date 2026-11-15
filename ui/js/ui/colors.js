/**
 * ui/colors.js — map colour rules.
 *
 * Responsibility: decide the fill colour of a feature, taking value
 * (density / detections) and interaction (selected, hovered) into account.
 * Depends on: constants.js, state.js, data/features.js
 */

import { COUNTRY_BREAKS, COUNTRY_COLORS, PIXEL_BREAKS, PIXEL_COLORS } from "../constants.js";
import { state } from "../state.js";
import { countryDensity, pixelCount } from "../data/features.js";

function thresholdColor(value, breaks, colors) {
  let index = 0;
  breaks.forEach((threshold, i) => { if (value >= threshold) index = i; });
  return colors[Math.min(index, colors.length - 1)];
}

export function countryColor(feature) {
  if (state.selectedKind === "country" && state.selected === feature) return "#fde68a";
  if (!state.selected && state.hovered === feature) return "#fdba74";
  return thresholdColor(countryDensity(feature), COUNTRY_BREAKS, COUNTRY_COLORS);
}

export function pixelColor(feature) {
  if (state.selectedKind === "pixel" && state.selected === feature) return "#ffffff";
  if (!state.selected && state.hovered === feature) return "#fff7ed";
  return thresholdColor(pixelCount(feature), PIXEL_BREAKS, PIXEL_COLORS);
}
