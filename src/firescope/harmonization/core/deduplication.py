import numpy as np
import pandas as pd

from shapely.geometry import box
from shapely.strtree import STRtree

from ..core.preprocessing import prescreen


def _create_approximate_geometry(row):
    """
    Approximate axis-aligned footprint.

    This is a fallback only. It does not reconstruct the actual
    satellite footprint corners.
    """

    lat = float(row["latitude"])
    lon = float(row["longitude"])

    half_h = float(row["track"]) / 2.0 / 111.32

    cos_lat = max(
        abs(np.cos(np.deg2rad(lat))),
        1e-4,
    )

    half_w = (
        float(row["scan"])
        / 2.0
        / (111.32 * cos_lat)
    )

    return box(
        lon - half_w,
        lat - half_h,
        lon + half_w,
        lat + half_h,
    )


def _overlap_ratio(geom_a, geom_b):
    if geom_a is None or geom_b is None:
        return 0.0

    if geom_a.is_empty or geom_b.is_empty:
        return 0.0

    intersection = geom_a.intersection(geom_b)

    if intersection.is_empty:
        return 0.0

    denominator = min(
        geom_a.area,
        geom_b.area,
    )

    if denominator <= 0:
        return 0.0

    return float(intersection.area / denominator)


def _find_duplicate_components(
    data,
    time_seconds,
    overlap_threshold,
):
    """
    Find connected duplicate groups using a spatial index.

    Note:
    The overlap calculation here uses the supplied geometry's
    coordinate system. For physically meaningful area overlap,
    use geometries in an appropriate metric projection.
    """

    geometries = data["geometry"].tolist()

    tree = STRtree(geometries)

    geometry_lookup = {
        id(geom): i
        for i, geom in enumerate(geometries)
    }

    parent = np.arange(len(data), dtype=np.int64)

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]

        return x

    def union(a, b):
        root_a = find(a)
        root_b = find(b)

        if root_a != root_b:
            parent[root_b] = root_a

    timestamps = (
        data["datetime_utc"]
        .astype("int64")
        .to_numpy()
    )

    for i, geom in enumerate(geometries):

        candidates = tree.query(geom)

        for candidate in candidates:

            # Shapely 2 returns integer indices.
            # Shapely 1 returns geometry objects.
            if isinstance(candidate, (int, np.integer)):
                j = int(candidate)
            else:
                j = geometry_lookup.get(id(candidate))

            if j is None or j <= i:
                continue

            delta_seconds = (
                abs(timestamps[i] - timestamps[j])
                / 1e9
            )

            if delta_seconds > time_seconds:
                continue

            overlap = _overlap_ratio(
                geom,
                geometries[j],
            )

            if overlap >= overlap_threshold:
                union(i, j)

    return np.array(
        [find(i) for i in range(len(data))],
        dtype=np.int64,
    )


def deduplicate_footprints(
    df: pd.DataFrame,
    time_seconds: int = 60,
    overlap_threshold: float = 0.30,
    vegetation_only: bool = True,
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    data = df.copy()

    if "datetime_utc" not in data.columns:
        raise ValueError(
            "Run normalize() before deduplicate_footprints()."
        )

    data = prescreen(
        data,
        vegetation_only=vegetation_only,
    )

    if data.empty:
        return data

    if "geometry" not in data.columns:
        data["geometry"] = [
            _create_approximate_geometry(row)
            for _, row in data.iterrows()
        ]

    data = data.dropna(subset=["geometry"]).reset_index(drop=True)

    if data.empty:
        return data

    components = _find_duplicate_components(
        data,
        time_seconds=time_seconds,
        overlap_threshold=overlap_threshold,
    )

    data["_duplicate_group"] = components

    # Highest confidence first; earliest time breaks ties.
    data = data.sort_values(
        by=[
            "_duplicate_group",
            "confidence_rank",
            "datetime_utc",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="stable",
    )

    # Preserve the strongest representative record.
    representatives = (
        data.groupby(
            "_duplicate_group",
            sort=False,
        )
        .head(1)
        .copy()
    )

    # Average FRP within each duplicate group.
    mean_frp = (
        data.groupby("_duplicate_group")["frp"]
        .mean()
    )

    representatives["frp"] = (
        representatives["_duplicate_group"]
        .map(mean_frp)
    )

    representatives = representatives.drop(
        columns=["_duplicate_group"]
    )

    return representatives.reset_index(drop=True)
