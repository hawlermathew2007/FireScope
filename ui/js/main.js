/**
 * main.js — application entry point.
 *
 * Responsibility: run the start-up sequence in order and nothing else.
 *   1. populate year dropdown and bind UI events
 *   2. draw the initial legend and empty panel
 *   3. create the globe (stop with an error if globe.gl failed to load)
 *   4. load the default year's data
 * Load it from index.html with:  <script type="module" src="js/main.js"></script>
 */

import { state } from "./state.js";
import { initGlobe } from "./globe/globe.js";
import { populateYears, bindUi } from "./ui/controls.js";
import { renderLegend } from "./ui/legend.js";
import { showEmpty } from "./ui/infoPanel.js";
import { showError, setLoading } from "./ui/status.js";
import { handleHover, handleClick } from "./controllers/selection.js";
import { setYear } from "./controllers/view.js";

async function start() {
  populateYears();
  bindUi();
  renderLegend();
  showEmpty();

  try {
    initGlobe({ onHover: handleHover, onClick: handleClick });
  } catch (error) {
    setLoading(false);
    showError(`Unable to initialize globe: ${error.message}`);
    return;
  }

  await setYear(state.year);
}

start();
