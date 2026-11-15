/**
 * ui/trendChart.js — the small monthly line/area chart in the side panel.
 *
 * Responsibility: draw an inline SVG chart (grid, area, line, dots, axis labels)
 * from [{ label, value }] points, or show an "empty" message when there is no data.
 * No chart library needed.
 * Depends on: constants.js, settings.js, dom.js, utils/format.js
 */

import { SVG_NS } from "../constants.js";
import { config } from "../settings.js";
import { dom } from "../dom.js";
import { number, formatNumber, compactNumber } from "../utils/format.js";

function svgElement(name, attributes = {}) {
  const element = document.createElementNS(SVG_NS, name);
  Object.entries(attributes).forEach(([key, value]) => element.setAttribute(key, value));
  return element;
}

export function renderTrend(series, title, emptyMessage = "No monthly trend data is available for this feature.") {
  dom.trendTitle.textContent = title;
  dom.trendChart.replaceChildren();

  const clean = series.filter((item) => number(item.value) !== null).slice(-config.maxTrendPoints);
  if (!clean.length) {
    dom.trendChart.classList.remove("is-visible");
    dom.trendEmpty.hidden = false;
    dom.trendEmpty.textContent = emptyMessage;
    dom.trendSummary.textContent = "—";
    return;
  }

  dom.trendEmpty.hidden = true;
  dom.trendChart.classList.add("is-visible");

  const width = 320;
  const height = 150;
  const margin = { top: 10, right: 10, bottom: 25, left: 34 };
  const innerWidth = width - margin.left - margin.right;
  const innerHeight = height - margin.top - margin.bottom;
  const values = clean.map((item) => number(item.value, 0));
  const maximum = Math.max(1, ...values);
  const x = (index) => margin.left + (clean.length === 1 ? innerWidth / 2 : (index / (clean.length - 1)) * innerWidth);
  const y = (value) => margin.top + innerHeight - (value / maximum) * innerHeight;

  /* Gradient fill under the line. */
  const defs = svgElement("defs");
  const gradient = svgElement("linearGradient", { id: "trendGradient", x1: "0", x2: "0", y1: "0", y2: "1" });
  gradient.append(
    svgElement("stop", { offset: "0%", "stop-color": "#fb923c", "stop-opacity": ".38" }),
    svgElement("stop", { offset: "100%", "stop-color": "#fb923c", "stop-opacity": "0" }),
  );
  defs.append(gradient);
  dom.trendChart.append(defs);

  /* Horizontal grid lines + y-axis labels (0, 50%, max). */
  [0, 0.5, 1].forEach((fraction) => {
    const gridY = margin.top + innerHeight * fraction;
    dom.trendChart.append(svgElement("line", { x1: margin.left, x2: width - margin.right, y1: gridY, y2: gridY, class: "chart-grid" }));
    const label = svgElement("text", { x: margin.left - 6, y: gridY + 3, "text-anchor": "end", class: "chart-label" });
    label.textContent = compactNumber(maximum * (1 - fraction));
    dom.trendChart.append(label);
  });

  /* Line + filled area. */
  const line = clean.map((item, index) => `${index ? "L" : "M"}${x(index).toFixed(2)},${y(values[index]).toFixed(2)}`).join(" ");
  const area = `${line} L${x(clean.length - 1)},${margin.top + innerHeight} L${x(0)},${margin.top + innerHeight} Z`;
  dom.trendChart.append(svgElement("path", { d: area, class: "chart-area" }), svgElement("path", { d: line, class: "chart-line" }));

  /* Dots with native hover tooltips. */
  clean.forEach((item, index) => {
    const dot = svgElement("circle", { cx: x(index), cy: y(values[index]), r: 2.8, class: "chart-dot" });
    const tooltip = svgElement("title");
    tooltip.textContent = `${item.label}: ${formatNumber(values[index])}`;
    dot.append(tooltip);
    dom.trendChart.append(dot);
  });

  /* x-axis labels: first, middle, last. */
  [0, Math.floor((clean.length - 1) / 2), clean.length - 1]
    .filter((item, index, array) => array.indexOf(item) === index)
    .forEach((index) => {
      const anchor = index === 0 ? "start" : index === clean.length - 1 ? "end" : "middle";
      const label = svgElement("text", { x: x(index), y: height - 6, "text-anchor": anchor, class: "chart-label" });
      label.textContent = clean[index].label;
      dom.trendChart.append(label);
    });

  dom.trendSummary.textContent = `${compactNumber(values.reduce((sum, value) => sum + value, 0))} total`;
}
