import { GLOBE_TEXTURE_URL, HOVER_COLOR } from "../constants.js";
import { densityColor, polygonHeight } from "../js/utils.js";
import { tooltipHtml } from "./tooltip.js";
import { updateInfoPanel } from "./infoPanel.js";

/* Builds the globe.gl instance. `Globe` is the global provided by the globe.gl <script>. */
export function createGlobe(element, countries) {
  let hoveredCountry = null;

  const globe = new window.Globe(element, { animateIn: true })
    .globeImageUrl(GLOBE_TEXTURE_URL)
    .atmosphereColor("#60a5fa")
    .atmosphereAltitude(0.16)
    .polygonsData(countries)
    /* height = total fire pixels (log scale) */
    .polygonAltitude((feature) =>
      polygonHeight(feature) + (feature === hoveredCountry ? 0.015 : 0),
    )
    /* colour = fire density */
    .polygonCapColor((feature) =>
      feature === hoveredCountry
        ? HOVER_COLOR
        : densityColor(feature.properties?.fire_density_per_10k_km2),
    )
    .polygonSideColor(() => "rgba(255,80,20,0.22)")
    .polygonStrokeColor(() => "rgba(255,255,255,0.35)")
    .polygonLabel(tooltipHtml)
    .onPolygonHover((feature) => {
      hoveredCountry = feature || null;

      if (feature) {
        updateInfoPanel(feature);
      }
      element.style.cursor = feature ? "pointer" : "grab";

      /* Re-trigger accessors so the hovered polygon updates colour and altitude. */
      globe
        .polygonCapColor(globe.polygonCapColor())
        .polygonAltitude(globe.polygonAltitude());
    })
    .onPolygonClick(updateInfoPanel);

  const controls = globe.controls();
  controls.autoRotate = true;
  controls.autoRotateSpeed = 0.3;
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;

  /* Pause rotation while the pointer is over the globe. */
  element.addEventListener("mouseenter", () => (controls.autoRotate = false));
  element.addEventListener("mouseleave", () => (controls.autoRotate = true));

  return globe;
}
