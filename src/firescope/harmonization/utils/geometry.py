import numpy as np
import pandas as pd
from shapely.geometry import box

GEOMETRY_METHOD = "firms_approx_axis_aligned"


def approximate_footprints(df: pd.DataFrame):
    geoms = []

    for r in df.itertuples():
        lat = float(r.latitude)
        lon = float(r.longitude)
        scan = float(r.scan)
        track = float(r.track)

        if (
            not np.isfinite(lat)
            or not np.isfinite(lon)
            or not np.isfinite(scan)
            or not np.isfinite(track)
            or scan <= 0
            or track <= 0
        ):
            geoms.append(None)
            continue

        half_h_deg = track / 2.0 / 111.32
        coslat = max(abs(np.cos(np.deg2rad(lat))), 1e-4)
        half_w_deg = scan / 2.0 / (111.32 * coslat)

        geom = box(
            lon - half_w_deg,
            lat - half_h_deg,
            lon + half_w_deg,
            lat + half_h_deg,
        )

        geoms.append(geom if geom.is_valid and not geom.is_empty else None)

    return geoms


def add_approximate_footprints(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["geometry"] = approximate_footprints(out)
    out["geometry_method"] = GEOMETRY_METHOD

    return out[out["geometry"].notna()].reset_index(drop=True)
