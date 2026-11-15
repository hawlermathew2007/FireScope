/**
 * controllers/selection.js — what hover, click and "clear" do.
 *
 * Responsibility:
 *   handleHover(f)   preview a feature in the panel (ignored while one is pinned)
 *   handleClick(f)   pin a feature
 *   clearSelection() unpin and return to the empty panel
 * These are handed to initGlobe() in main.js, and clearSelection is also wired to
 * the Escape key and the clear button in ui/controls.js.
 * Depends on: state.js, globe/globe.js, ui/infoPanel.js
 */

import { state } from "../state.js";
import { renderCurrentLayer } from "../globe/globe.js";
import { showFeature, showEmpty, syncClearButton } from "../ui/infoPanel.js";

export function handleHover(feature) {
  if (state.selected) return;
  state.hovered = feature || null;
  if (feature) showFeature(feature);
  else showEmpty();
  renderCurrentLayer();
}

export function handleClick(feature) {
  if (!feature) return;
  state.selected = feature;
  state.selectedKind = state.mode;
  state.hovered = feature;
  showFeature(feature);
  syncClearButton();
  renderCurrentLayer();
}

export function clearSelection() {
  state.selected = null;
  state.selectedKind = null;
  state.hovered = null;
  syncClearButton();
  showEmpty();
  renderCurrentLayer();
}
