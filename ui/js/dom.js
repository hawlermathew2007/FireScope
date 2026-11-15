/**
 * dom.js — cached references to HTML elements.
 *
 * Responsibility: look up every element by id once, so other modules never
 * call document.getElementById themselves. If you rename an id in index.html,
 * this is the only JS file that needs to change.
 * Depends on: nothing. (Safe because module scripts run after the DOM is parsed.)
 */

const $ = (id) => document.getElementById(id);

export const dom = {
  globe: $("globeViz"),
  year: $("yearSelect"),
  subtitle: $("headerSubtitle"),
  panelMode: $("panelMode"),
  selectionName: $("selectionName"),
  selectionMeta: $("selectionMeta"),
  metricGrid: $("metricGrid"),
  clearSelection: $("clearSelection"),
  trendTitle: $("trendTitle"),
  trendSummary: $("trendSummary"),
  trendChart: $("trendChart"),
  trendEmpty: $("trendEmpty"),
  legendTitle: $("legendTitle"),
  legendUnit: $("legendUnit"),
  legendRows: $("legendRows"),
  hintText: $("hintText"),
  loading: $("loading"),
  loadingText: $("loadingText"),
  error: $("error"),
};
