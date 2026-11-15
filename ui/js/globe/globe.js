/**
 * globe/globe.js — everything that talks to globe.gl.
 *
 * Responsibility:
 *   - initGlobe(handlers): create the globe, texture, camera, auto-rotate, resize.
 *   - renderCurrentLayer(): push the current mode's features/colours/altitudes to the globe.
 * It does NOT decide what hover/click mean — those arrive as `handlers`
 * ({ onHover, onClick }) from controllers/selection.js, which avoids circular imports.
 * Depends on: settings.js, state.js, dom.js, utils/format.js, data/features.js, ui/colors.js
 * External: window.Globe (globe.gl loaded from CDN in index.html)
 */

import { config } from "../settings.js";
import { state } from "../state.js";
import { dom } from "../dom.js";
import { number, valueFrom, formatNumber, escapeHtml } from "../utils/format.js";
import {
  featureProperties,
  pixelCount,
  pixelName,
  pointCoordinates,
  polygonFeatures,
  pointFeatures,
} from "../data/features.js";
import { countryColor, pixelColor } from "../ui/colors.js";

export function renderCurrentLayer() {
  if (!state.globe) return;
  const features = state.mode === "country" ? state.current.country : state.current.pixel;
  const polygons = polygonFeatures(features);
  const points = state.mode === "pixel" ? pointFeatures(features) : [];

  state.globe
    .polygonsData(polygons)
    .polygonCapColor(state.mode === "country" ? countryColor : pixelColor)
    .polygonSideColor(() => (state.mode === "country" ? "rgba(15,23,42,.72)" : "rgba(190,18,60,.34)"))
    .polygonStrokeColor(() => (state.mode === "country" ? "rgba(226,232,240,.28)" : "rgba(255,237,213,.18)"))
    .polygonAltitude((feature) => {
      if (state.selected === feature) return state.mode === "country" ? 0.025 : 0.035;
      return state.mode === "country" ? 0.009 : 0.016;
    })
    .pointsData(points)
    .pointColor(pixelColor)
    .pointRadius((feature) => number(valueFrom(featureProperties(feature), ["radius", "point_radius", "pixel_radius"]), 0.11))
    .pointAltitude((feature) => number(valueFrom(featureProperties(feature), ["altitude", "point_altitude"]), 0.025));
}

function pointTooltip(feature) {
  const [lng, lat] = pointCoordinates(feature);
  const title = pixelName(feature) || `${lat?.toFixed(2)}°, ${lng?.toFixed(2)}°`;
  return `<div style="padding:7px 9px;background:#081321;color:#f8fafc;border:1px solid #334155;border-radius:8px;font:12px system-ui"><b>${escapeHtml(title)}</b><br>${escapeHtml(formatNumber(pixelCount(feature)))} detections</div>`;
}

export function initGlobe({ onHover, onClick }) {
  if (typeof window.Globe !== "function") throw new Error("Globe.gl did not load. Check the CDN connection.");

  state.globe = new window.Globe(dom.globe)
    .width(window.innerWidth)
    .height(window.innerHeight)
    .backgroundColor("rgba(0,0,0,0)")
    .globeImageUrl("https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-night.jpg")
    .bumpImageUrl("https://cdn.jsdelivr.net/npm/three-globe/example/img/earth-topology.png")
    .showAtmosphere(true)
    .atmosphereColor("#38bdf8")
    .atmosphereAltitude(0.16)
    .polygonsData([])
    .polygonsTransitionDuration(250)
    .pointsData([])
    .pointLat((feature) => pointCoordinates(feature)[1])
    .pointLng((feature) => pointCoordinates(feature)[0])
    .pointResolution(4)
    .pointsMerge(false)
    .pointsTransitionDuration(250)
    .pointLabel(pointTooltip)
    .onPolygonHover(onHover)
    .onPolygonClick(onClick)
    .onPointHover(onHover)
    .onPointClick(onClick);

  state.globe.pointOfView(config.initialPointOfView, 0);

  const controls = state.globe.controls();
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.22;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  /* Stop auto-rotation permanently once the user grabs the globe. */
  dom.globe.addEventListener("pointerdown", () => { controls.autoRotate = false; }, { once: true });
  window.addEventListener("resize", () => state.globe.width(window.innerWidth).height(window.innerHeight));
}
