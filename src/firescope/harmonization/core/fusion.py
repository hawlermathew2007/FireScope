import numpy as np
import pandas as pd

from .calibration import predict_vza_ratio


def fuse_modis_footprints(
    matched_modis: pd.DataFrame,
    calibration_model,
) -> pd.DataFrame:

    if matched_modis.empty:
        return matched_modis.copy()

    out = matched_modis.copy()

    required = [
        "frp",
        "vza_deg",
        "confidence_rank",
        "frp_viirs_aggregated",
        "viirs_confidence_rank",
    ]

    missing = [
        col for col in required
        if col not in out.columns
    ]

    if missing:
        raise ValueError(
            f"Missing fusion columns: {missing}"
        )

    # Preserve original MODIS measurements and confidence.
    out["frp_modis_original"] = out["frp"]

    out["modis_confidence"] = (
        out["confidence"]
        if "confidence" in out.columns
        else None
    )

    out["modis_confidence_class"] = (
        out["confidence_class"]
        if "confidence_class" in out.columns
        else None
    )

    # Preserve original VIIRS confidence fields.
    out["viirs_confidence"] = (
        out["viirs_confidence"]
        if "viirs_confidence" in out.columns
        else None
    )

    out["viirs_confidence_class"] = (
        out["viirs_confidence_class"]
        if "viirs_confidence_class" in out.columns
        else None
    )

    # Apply annual calibration model.
    out["calibration_ratio"] = predict_vza_ratio(
        out["vza_deg"].to_numpy(dtype=float),
        calibration_model,
    )

    out["frp_modis_adjusted"] = (
        out["frp_modis_original"]
        * out["calibration_ratio"]
    )

    modis_rank = pd.to_numeric(
        out["confidence_rank"],
        errors="coerce",
    )

    viirs_rank = pd.to_numeric(
        out["viirs_confidence_rank"],
        errors="coerce",
    )

    modis_frp = pd.to_numeric(
        out["frp_modis_adjusted"],
        errors="coerce",
    )

    viirs_frp = pd.to_numeric(
        out["frp_viirs_aggregated"],
        errors="coerce",
    )

    modis_valid = (
        modis_rank.notna()
        & modis_frp.notna()
        & np.isfinite(modis_frp)
        & (modis_frp > 0)
    )

    viirs_valid = (
        viirs_rank.notna()
        & viirs_frp.notna()
        & np.isfinite(viirs_frp)
        & (viirs_frp > 0)
    )

    # VIIRS wins only if its rank is strictly higher.
    # MODIS wins confidence ties.
    use_viirs = (
        viirs_valid
        & (
            ~modis_valid
            | (viirs_rank > modis_rank)
        )
    )

    use_modis = (
        modis_valid
        & ~use_viirs
    )

    out["frp_harmonized"] = np.nan
    out["fusion_source"] = None
    out["confidence_selected_sensor"] = None
    out["confidence_selected_rank"] = pd.NA
    out["confidence_class"] = None
    out["confidence"] = None

    # Select FRP.
    out.loc[
        use_viirs,
        "frp_harmonized",
    ] = viirs_frp[use_viirs]

    out.loc[
        use_modis,
        "frp_harmonized",
    ] = modis_frp[use_modis]

    # Select source.
    out.loc[
        use_viirs,
        "fusion_source",
    ] = "VIIRS_NOAA20"

    out.loc[
        use_modis,
        "fusion_source",
    ] = "MODIS_ADJUSTED"

    out.loc[
        use_viirs,
        "confidence_selected_sensor",
    ] = "VIIRS"

    out.loc[
        use_modis,
        "confidence_selected_sensor",
    ] = "MODIS"

    # Select confidence rank.
    out.loc[
        use_viirs,
        "confidence_selected_rank",
    ] = viirs_rank[use_viirs]

    out.loc[
        use_modis,
        "confidence_selected_rank",
    ] = modis_rank[use_modis]

    # Select standardized confidence class.
    if "viirs_confidence_class" in out.columns:
        out.loc[
            use_viirs,
            "confidence_class",
        ] = out.loc[
            use_viirs,
            "viirs_confidence_class",
        ]

    if "modis_confidence_class" in out.columns:
        out.loc[
            use_modis,
            "confidence_class",
        ] = out.loc[
            use_modis,
            "modis_confidence_class",
        ]

    # Select original sensor confidence.
    if "viirs_confidence" in out.columns:
        out.loc[
            use_viirs,
            "confidence",
        ] = out.loc[
            use_viirs,
            "viirs_confidence",
        ]

    if "modis_confidence" in out.columns:
        out.loc[
            use_modis,
            "confidence",
        ] = out.loc[
            use_modis,
            "modis_confidence",
        ]

    # Retain only records with a selected FRP.
    out = out.dropna(
        subset=["frp_harmonized"]
    ).copy()

    out["confidence_selected_rank"] = (
        out["confidence_selected_rank"]
        .astype("Int64")
    )

    # Final FRP represents the harmonized FRP.
    out["frp"] = out["frp_harmonized"]

    return out.reset_index(drop=True)
