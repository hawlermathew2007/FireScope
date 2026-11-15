/**
 * data/trend.js — turn a feature's monthly history into chart-ready points.
 *
 * Responsibility: accept every shape the GeoJSON might store monthly counts in
 * (JSON string, array of numbers, array of objects, {label: value} map, or
 * separate jan/feb/... properties) and return [{ label, value }, ...].
 * Depends on: constants.js, utils/format.js, data/features.js
 */

import { MONTHS } from "../constants.js";
import { valueFrom, number } from "../utils/format.js";
import { featureProperties } from "./features.js";

export function parseTrend(value, properties) {
  let parsed = value;
  if (typeof parsed === "string") {
    try { parsed = JSON.parse(parsed); } catch { parsed = null; }
  }

  if (Array.isArray(parsed)) {
    if (parsed.every((item) => number(item) !== null)) {
      return parsed.slice(0, 12).map((item, index) => ({ label: MONTHS[index], value: number(item, 0) }));
    }
    return parsed.map((item, index) => ({
      label: valueFrom(item, ["date", "month", "period", "label"], MONTHS[index] || String(index + 1)),
      value: number(valueFrom(item, ["value", "count", "detections", "fires"]), 0),
    }));
  }

  if (parsed && typeof parsed === "object") {
    return Object.entries(parsed).map(([label, count]) => ({ label, value: number(count, 0) }));
  }

  /* Fallback: one property per month (jan, feb, month_01, m01, ...). */
  const monthlyKeys = [
    ["jan", "january", "month_01", "m01"], ["feb", "february", "month_02", "m02"],
    ["mar", "march", "month_03", "m03"], ["apr", "april", "month_04", "m04"],
    ["may", "month_05", "m05"], ["jun", "june", "month_06", "m06"],
    ["jul", "july", "month_07", "m07"], ["aug", "august", "month_08", "m08"],
    ["sep", "september", "month_09", "m09"], ["oct", "october", "month_10", "m10"],
    ["nov", "november", "month_11", "m11"], ["dec", "december", "month_12", "m12"],
  ];
  const monthly = monthlyKeys.map((keys, index) => ({ label: MONTHS[index], value: number(valueFrom(properties, keys)) }));
  return monthly.some((item) => item.value !== null) ? monthly.map((item) => ({ ...item, value: item.value || 0 })) : [];
}

export function featureTrend(feature) {
  const p = featureProperties(feature);
  const embedded = valueFrom(p, ["monthly_fire_counts", "monthly_counts", "fire_history", "history", "historical_trend", "monthly_history"]);
  return parseTrend(embedded, p);
}
