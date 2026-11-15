/**
 * state.js — the app's single mutable state object.
 *
 * Responsibility: hold everything that changes while the app runs
 * (view mode, year, loaded datasets, hovered/selected feature, globe instance).
 * Other modules import and mutate `state` directly; nothing else owns data.
 * Depends on: settings.js
 */

import { config, query } from "./settings.js";

export const state = {
  mode: "country",                                  // "country" | "pixel"
  year: Number(query.get("year")) || config.defaultYear,
  globe: null,                                      // globe.gl instance (set in globe/globe.js)
  datasets: new Map(),                              // year -> loaded dataset cache
  current: { country: [], pixel: [] },              // features for the displayed year
  selected: null,                                   // pinned feature (click)
  selectedKind: null,                               // mode the pinned feature belongs to
  hovered: null,                                    // feature under the cursor
  loadSequence: 0,                                  // guards against out-of-order year loads
};
