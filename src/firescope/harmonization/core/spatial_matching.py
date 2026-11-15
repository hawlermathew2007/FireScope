import numpy as np
import pandas as pd

from shapely.geometry import Point
from shapely.strtree import STRtree


def _query_tree_indices(tree, query_geom, n_geometries):
    """
    Return candidate indices from a Shapely 2.x STRtree.
    """
    result = tree.query(query_geom)

    if len(result) == 0:
        return np.array([], dtype=np.int64)

    result = np.asarray(result)

    if not np.issubdtype(result.dtype, np.integer):
        raise RuntimeError(
            "This implementation requires Shapely 2.x."
        )

    indices = result.astype(np.int64)

    return indices[
        (indices >= 0) & (indices < n_geometries)
    ]


def _empty_result(modis):
    """
    Return an empty DataFrame with the MODIS columns and
    the expected VIIRS aggregation columns.
    """
    out = modis.iloc[0:0].copy()

    additional_columns = {
        "frp_viirs_aggregated": "float64",
        "viirs_match_count": "int64",
        "viirs_match_time_delta_min": "float64",
        "viirs_confidence_rank": "Int64",
        "viirs_confidence_class": "object",
        "viirs_confidence": "object",
        "bright_ti4": "float64",
        "bright_ti5": "float64",
    }

    for column, dtype in additional_columns.items():
        if column not in out.columns:
            out[column] = pd.Series(dtype=dtype)

    return out


def aggregate_viirs_to_modis(
    modis: pd.DataFrame,
    viirs: pd.DataFrame,
    max_time_minutes: float = 5.0,
) -> pd.DataFrame:
    """
    Aggregate VIIRS detections to MODIS footprints.

    Spatial rule:
        VIIRS detection centre must be covered by the MODIS polygon.

    Temporal rule:
        Absolute acquisition time difference must be <=
        max_time_minutes.

    Aggregation:
        VIIRS FRP: sum
        VIIRS brightness temperatures: arithmetic mean
        VIIRS confidence: highest ordinal confidence rank

    Output:
        Only MODIS footprints with at least one VIIRS contributor.
    """

    if modis.empty or viirs.empty:
        return _empty_result(modis)

    required_modis = {
        "geometry",
        "datetime_utc",
        "frp",
    }

    required_viirs = {
        "latitude",
        "longitude",
        "geometry",
        "datetime_utc",
        "frp",
        "confidence_rank",
        "confidence_class",
        "confidence",
    }

    missing_modis = required_modis - set(modis.columns)
    missing_viirs = required_viirs - set(viirs.columns)

    if missing_modis:
        raise ValueError(
            f"MODIS columns missing: {sorted(missing_modis)}"
        )

    if missing_viirs:
        raise ValueError(
            f"VIIRS columns missing: {sorted(missing_viirs)}"
        )

    if max_time_minutes < 0:
        raise ValueError(
            "max_time_minutes must be non-negative."
        )

    m = modis.reset_index(drop=True).copy()
    v = viirs.reset_index(drop=True).copy()

    # Keep only usable MODIS records.
    m = m[
        m["geometry"].notna()
        & m["datetime_utc"].notna()
        & m["frp"].notna()
        & (m["frp"] > 0)
    ].reset_index(drop=True)

    # Keep only usable VIIRS records.
    v = v[
        v["geometry"].notna()
        & v["datetime_utc"].notna()
        & v["latitude"].notna()
        & v["longitude"].notna()
        & v["frp"].notna()
        & (v["frp"] > 0)
        & v["confidence_rank"].notna()
    ].reset_index(drop=True)

    if m.empty or v.empty:
        return _empty_result(modis)

    # Build actual VIIRS detection centre points from coordinates.
    viirs_centres = [
        Point(float(lon), float(lat))
        for lon, lat in zip(
            v["longitude"],
            v["latitude"],
        )
    ]

    tree = STRtree(viirs_centres)

    max_seconds = float(max_time_minutes) * 60.0

    matched_rows = []

    for _, modis_row in m.iterrows():

        modis_geom = modis_row["geometry"]

        if modis_geom is None or modis_geom.is_empty:
            continue

        # Find VIIRS centres potentially inside this MODIS polygon.
        candidate_indices = _query_tree_indices(
            tree,
            modis_geom,
            len(viirs_centres),
        )

        if candidate_indices.size == 0:
            continue

        # Exact point-in-polygon test.
        inside_indices = [
            idx
            for idx in candidate_indices
            if modis_geom.covers(viirs_centres[idx])
        ]

        if not inside_indices:
            continue

        candidates = v.iloc[inside_indices].copy()

        # Apply temporal criterion.
        time_delta_seconds = (
            candidates["datetime_utc"]
            - modis_row["datetime_utc"]
        ).dt.total_seconds().abs()

        candidates = candidates.loc[
            time_delta_seconds <= max_seconds
        ].copy()

        if candidates.empty:
            continue

        # Confidence rank should be present, but validate again.
        candidates = candidates.dropna(
            subset=["confidence_rank"]
        )

        if candidates.empty:
            continue

        # Determine highest-confidence contributor.
        candidates = candidates.sort_values(
            ["confidence_rank", "datetime_utc"],
            ascending=[False, True],
            kind="stable",
        )

        best_viirs = candidates.iloc[0]

        row = modis_row.to_dict()

        row["frp_viirs_aggregated"] = float(
            candidates["frp"].sum()
        )

        row["viirs_match_count"] = int(
            len(candidates)
        )

        row["viirs_match_time_delta_min"] = float(
            (
                candidates["datetime_utc"]
                - modis_row["datetime_utc"]
            )
            .dt.total_seconds()
            .abs()
            .min()
            / 60.0
        )

        row["viirs_confidence_rank"] = int(
            best_viirs["confidence_rank"]
        )

        row["viirs_confidence_class"] = (
            best_viirs["confidence_class"]
        )

        row["viirs_confidence"] = (
            best_viirs["confidence"]
        )

        for column in ["bright_ti4", "bright_ti5"]:
            if column in candidates.columns:
                row[column] = candidates[column].mean()
            else:
                row[column] = np.nan

        matched_rows.append(row)

    if not matched_rows:
        return _empty_result(modis)

    result = pd.DataFrame(matched_rows)

    result["viirs_confidence_rank"] = (
        result["viirs_confidence_rank"].astype("Int64")
    )

    return result.reset_index(drop=True)
