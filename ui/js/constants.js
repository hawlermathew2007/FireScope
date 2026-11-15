/**
 * constants.js — fixed values that never change at runtime.
 *
 * Responsibility: colour scales, legend break points, month labels.
 * Edit here to restyle the map or change density/intensity thresholds.
 * Depends on: nothing.
 */

/* Country polygons: colour index = last break that the density reaches. */
export const COUNTRY_COLORS = ["#172033", "#123454", "#155e75", "#0e7490", "#ca8a04", "#ea580c", "#e11d48", "#881337"];
export const COUNTRY_BREAKS = [0, 10, 50, 100, 250, 500, 1000, 2000];

/* Pixel / sensor-region layer. */
export const PIXEL_COLORS = ["#fef08a", "#facc15", "#fb923c", "#f43f5e", "#be123c"];
export const PIXEL_BREAKS = [0, 1, 5, 20, 100, 500];

export const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export const SVG_NS = "http://www.w3.org/2000/svg";
