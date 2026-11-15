/**
 * ui/status.js — loading spinner and error banner.
 *
 * Responsibility: show/hide the loading overlay and the red error box.
 * Depends on: dom.js
 */

import { dom } from "../dom.js";

export function showError(message, autoHide = false) {
  dom.error.textContent = message;
  dom.error.classList.add("is-visible");
  if (autoHide) window.setTimeout(() => dom.error.classList.remove("is-visible"), 6500);
}

export function clearError() {
  dom.error.classList.remove("is-visible");
  dom.error.textContent = "";
}

/* Also disables the year dropdown while a load is in flight. */
export function setLoading(isLoading, message = "Loading GeoJSON…") {
  dom.loadingText.textContent = message;
  dom.loading.hidden = !isLoading;
  dom.year.disabled = isLoading;
}
