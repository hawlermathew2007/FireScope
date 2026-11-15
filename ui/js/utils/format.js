/**
 * utils/format.js — pure helper functions (no DOM, no state).
 *
 * Responsibility: safely read values from messy GeoJSON properties and turn
 * them into display strings. Easy to unit-test because nothing here has side effects.
 * Depends on: constants.js
 */

import { MONTHS } from "../constants.js";

/* Return the first non-empty property from a list of possible key names. */
export function valueFrom(object, keys, fallback = null) {
  for (const key of keys) {
    const value = object?.[key];
    if (value !== undefined && value !== null && value !== "") return value;
  }
  return fallback;
}

/* Parse to a finite number (accepts "1,234"), else `fallback`. */
export function number(value, fallback = null) {
  if (value === null || value === undefined || value === "") return fallback;
  const parsed = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function formatNumber(value, maximumFractionDigits = 0) {
  const parsed = number(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat(undefined, { maximumFractionDigits }).format(parsed);
}

/* 12,345 -> "12.3K" (used on chart axes). */
export function compactNumber(value) {
  const parsed = number(value);
  if (parsed === null) return "—";
  return new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(parsed);
}

/* Accepts 0–1 fractions or 0–100 percentages. */
export function formatPercent(value) {
  let parsed = number(value);
  if (parsed === null) return "—";
  if (Math.abs(parsed) <= 1) parsed *= 100;
  return `${parsed.toFixed(1)}%`;
}

export function formatMonth(value) {
  const parsed = number(value);
  if (parsed !== null && parsed >= 1 && parsed <= 12) return MONTHS[parsed - 1];
  return value || "—";
}

export function normalizeIso(value) {
  const iso = String(value || "").trim().toUpperCase();
  return iso && iso !== "-99" ? iso : "";
}

/* Escape text before putting it into an HTML string (tooltips). */
export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
