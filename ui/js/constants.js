export const GEOJSON_URL = "firms_country_analysis.geojson";

export const GLOBE_TEXTURE_URL =
  "//cdn.jsdelivr.net/npm/three-globe/example/img/earth-dark.jpg";

export const MONTH_NAMES = [
  "",
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

/* Fire density bins (per 10,000 km²). Shared by the map colours and the legend.
   `max` is exclusive; the last bin is open-ended. */
export const DENSITY_BINS = [
  { max: 100, color: "#ffffb2", label: "Under 100" },
  { max: 500, color: "#fecc5c", label: "100 – 499" },
  { max: 1000, color: "#fd8d3c", label: "500 – 999" },
  { max: 2000, color: "#f03b20", label: "1,000 – 1,999" },
  { max: Infinity, color: "#bd0026", label: "2,000+" },
];

export const NO_DATA_COLOR = "#475569";
export const HOVER_COLOR = "#22d3ee";
