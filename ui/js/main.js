import { GEOJSON_URL } from "./constants.js";
import { createGlobe } from "./components/globe.js";
import { renderLegend } from "./components/legend.js";
import { updateInfoPanel } from "./components/infoPanel.js";

function showError(message) {
  const box = document.getElementById("error");
  box.style.display = "block";
  box.textContent = message;
}

async function loadCountries() {
  const response = await fetch(GEOJSON_URL);

  if (!response.ok) {
    throw new Error(`GeoJSON request failed: HTTP ${response.status}`);
  }

  const data = await response.json();

  if (data.type !== "FeatureCollection" || !Array.isArray(data.features)) {
    throw new Error("Invalid GeoJSON FeatureCollection.");
  }

  return data.features.filter((feature) => {
    const type = feature.geometry?.type;
    const iso = feature.properties?.iso_a3;
    return (type === "Polygon" || type === "MultiPolygon") && iso !== "ATA";
  });
}

async function init() {
  renderLegend();

  try {
    const countries = await loadCountries();
    console.log("Countries loaded:", countries.length);

    createGlobe(document.getElementById("globeViz"), countries);

    if (countries.length > 0) {
      updateInfoPanel(countries[0]);
    }
  } catch (error) {
    console.error(error);
    showError("Unable to initialize globe: " + error.message);
  }
}

init();
