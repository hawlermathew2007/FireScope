import numpy as np
import pandas as pd
import logging
import gc

from pathlib import Path

logger = logging.getLogger(__name__)


def build_annual_calibration(
    matched_dir,
    year,
    min_pairs=30,
    min_bin_samples=5,
    iqr_multiplier=1.5,
):
    """
    Build one annual MODIS-VIIRS VZA calibration model.

    Processing:
        1. Read matched Parquet batches individually.
        2. Calculate annual log FRP ratios.
        3. Calculate one annual IQR threshold.
        4. Read batches again and retain annual IQR inliers.
        5. Estimate MODIS VZA from track.
        6. Fit one annual VZA calibration model.

    The function only loads the columns required for calibration,
    not the complete matched datasets.

    Parameters
    ----------
    matched_dir : str or Path
        Directory containing matched_*.parquet files.

    year : int
        Target processing year.

    min_pairs : int
        Minimum number of calibration observations required
        before attempting quadratic fitting.

    min_bin_samples : int
        Minimum number of observations required in each
        one-degree VZA bin.

    iqr_multiplier : float
        IQR outlier threshold multiplier.

    Returns
    -------
    dict
        Annual calibration model compatible with
        predict_vza_ratio() and fuse_modis_footprints().
    """
    from ..utils.vza import estimate_vza_array

    matched_dir = Path(matched_dir)

    if not matched_dir.exists():
        raise FileNotFoundError(
            f"Matched directory does not exist: {matched_dir}"
        )

    if min_pairs < 1:
        raise ValueError("min_pairs must be >= 1")

    if min_bin_samples < 1:
        raise ValueError("min_bin_samples must be >= 1")

    if iqr_multiplier < 0:
        raise ValueError("iqr_multiplier must be >= 0")

    files = sorted(
        matched_dir.glob("matched_*.parquet")
    )

    if not files:
        logger.warning(
            "No matched Parquet files found for %s",
            year,
        )

        model = _fallback_model(
            reason="no_matched_files",
        )

        model["year"] = int(year)
        return model

    required_columns = [
        "frp",
        "frp_viirs_aggregated",
        "track",
        "acq_date",
    ]

    # ---------------------------------------------------------
    # PASS 1: Calculate the annual IQR thresholds.
    # ---------------------------------------------------------

    logger.info(
        "[%s] Pass 1: Calculating annual FRP ratio distribution",
        year,
    )

    log_ratio_arrays = []
    total_records = 0

    for path in files:
        try:
            data = pd.read_parquet(
                path,
                columns=required_columns,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Could not read calibration columns from {path}"
            ) from exc

        if data.empty:
            continue

        # Restrict records to the requested year.
        dates = pd.to_datetime(
            data["acq_date"],
            errors="coerce",
        )

        data = data.loc[
            dates.dt.year == year
        ]

        if data.empty:
            continue

        modis_frp = pd.to_numeric(
            data["frp"],
            errors="coerce",
        ).to_numpy(dtype=float)

        viirs_frp = pd.to_numeric(
            data["frp_viirs_aggregated"],
            errors="coerce",
        ).to_numpy(dtype=float)

        valid = (
            np.isfinite(modis_frp)
            & np.isfinite(viirs_frp)
            & (modis_frp > 0)
            & (viirs_frp > 0)
        )

        if not valid.any():
            continue

        ratios = np.log(
            viirs_frp[valid] / modis_frp[valid]
        )

        ratios = ratios[np.isfinite(ratios)]

        if len(ratios) == 0:
            continue

        log_ratio_arrays.append(ratios)
        total_records += len(ratios)

        logger.debug(
            "Read %s valid ratios from %s",
            f"{len(ratios):,}",
            path.name,
        )

        del data, dates, modis_frp, viirs_frp
        gc.collect()

    if not log_ratio_arrays:
        logger.warning(
            "[%s] No valid FRP ratios available for calibration",
            year,
        )

        model = _fallback_model(
            reason="no_valid_frp_ratios",
        )

        model["year"] = int(year)
        model["total_valid_pairs"] = 0
        return model

    # Combine only the scalar log-ratio values.
    annual_log_ratios = np.concatenate(
        log_ratio_arrays
    )

    del log_ratio_arrays
    gc.collect()

    # Calculate exact annual quartiles using NumPy's
    # default linear interpolation method.
    q1, q3 = np.quantile(
        annual_log_ratios,
        [0.25, 0.75],
    )

    iqr = q3 - q1

    lower = q1 - iqr_multiplier * iqr
    upper = q3 + iqr_multiplier * iqr

    logger.info(
        "[%s] Annual IQR thresholds: lower=%.6f, upper=%.6f",
        year,
        lower,
        upper,
    )

    del annual_log_ratios
    gc.collect()

    # ---------------------------------------------------------
    # PASS 2: Collect annual IQR inliers and estimate VZA.
    # ---------------------------------------------------------

    logger.info(
        "[%s] Pass 2: Preparing annual calibration observations",
        year,
    )

    calibration_frames = []
    screened_pairs = 0

    for path in files:
        data = pd.read_parquet(
            path,
            columns=required_columns,
        )

        if data.empty:
            continue

        dates = pd.to_datetime(
            data["acq_date"],
            errors="coerce",
        )

        data = data.loc[
            dates.dt.year == year
        ].copy()

        if data.empty:
            continue

        modis_frp = pd.to_numeric(
            data["frp"],
            errors="coerce",
        ).to_numpy(dtype=float)

        viirs_frp = pd.to_numeric(
            data["frp_viirs_aggregated"],
            errors="coerce",
        ).to_numpy(dtype=float)

        track = pd.to_numeric(
            data["track"],
            errors="coerce",
        ).to_numpy(dtype=float)

        log_ratio = np.full(
            len(data),
            np.nan,
            dtype=float,
        )

        valid = (
            np.isfinite(modis_frp)
            & np.isfinite(viirs_frp)
            & (modis_frp > 0)
            & (viirs_frp > 0)
        )

        log_ratio[valid] = np.log(
            viirs_frp[valid] / modis_frp[valid]
        )

        inlier = (
            np.isfinite(log_ratio)
            & (log_ratio >= lower)
            & (log_ratio <= upper)
        )

        if not inlier.any():
            continue

        # VZA is estimated only for calibration inliers.
        selected_track = track[inlier]

        vza = estimate_vza_array(
            selected_track
        )

        selected_modis_frp = modis_frp[inlier]
        selected_viirs_frp = viirs_frp[inlier]

        frame = pd.DataFrame({
            "vza_deg": np.asarray(vza, dtype=float),
            "frp": selected_modis_frp,
            "frp_viirs_aggregated": selected_viirs_frp,
        })

        calibration_frames.append(frame)

        screened_pairs += len(frame)

        logger.debug(
            "Collected %s calibration pairs from %s",
            f"{len(frame):,}",
            path.name,
        )

        del data, dates, modis_frp, viirs_frp
        del track, log_ratio, frame
        gc.collect()

    if not calibration_frames:
        logger.warning(
            "[%s] No observations survived annual IQR screening",
            year,
        )

        model = _fallback_model(
            reason="no_iqr_inliers",
        )

        model["year"] = int(year)
        model["total_valid_pairs"] = total_records
        model["iqr_lower"] = float(lower)
        model["iqr_upper"] = float(upper)
        return model

    calibration_data = pd.concat(
        calibration_frames,
        ignore_index=True,
    )

    del calibration_frames
    gc.collect()

    # ---------------------------------------------------------
    # PASS 3: Fit the existing VZA calibration model.
    # ---------------------------------------------------------

    logger.info(
        "[%s] Fitting annual VZA calibration using %s pairs",
        year,
        f"{len(calibration_data):,}",
    )

    model = fit_vza_calibration(
        calibration_data,
        min_pairs=min_pairs,
        min_bin_samples=min_bin_samples,
    )

    # Add annual calibration diagnostics without changing
    # the existing model keys.
    model["year"] = int(year)
    model["total_valid_pairs"] = int(total_records)
    model["screened_pairs"] = int(screened_pairs)
    model["iqr_multiplier"] = float(iqr_multiplier)
    model["iqr_lower"] = float(lower)
    model["iqr_upper"] = float(upper)
    model["iqr_q1"] = float(q1)
    model["iqr_q3"] = float(q3)

    logger.info(
        "[%s] Calibration completed: "
        "pairs=%s, bins=%s, fallback=%s, reason=%s",
        year,
        f"{model['n_pairs']:,}",
        model["n_bins"],
        model["fallback"],
        model["fallback_reason"],
    )

    del calibration_data
    gc.collect()

    return model

def screen_log_ratio_outliers(
    matched: pd.DataFrame,
    multiplier: float = 1.5,
) -> pd.DataFrame:

    if matched.empty:
        return matched.copy()

    data = matched.dropna(
        subset=[
            "frp_viirs_aggregated",
            "frp",
        ]
    ).copy()

    data = data[
        (data["frp_viirs_aggregated"] > 0)
        & (data["frp"] > 0)
    ]

    if data.empty:
        return data

    data["log_frp_ratio"] = np.log(
        data["frp_viirs_aggregated"] / data["frp"]
    )

    data = data[
        np.isfinite(data["log_frp_ratio"])
    ]

    if data.empty:
        return data

    q1 = data["log_frp_ratio"].quantile(0.25)
    q3 = data["log_frp_ratio"].quantile(0.75)

    iqr = q3 - q1

    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr

    return data[
        data["log_frp_ratio"].between(
            lower,
            upper,
        )
    ].copy()


def _fallback_model(
    global_ratio=1.0,
    n_pairs=0,
    bin_table=None,
    reason="insufficient_data",
):

    if bin_table is None:
        bin_table = pd.DataFrame()

    return {
        "coefficients": None,
        "global_ratio": float(global_ratio),
        "vza_min": None,
        "vza_max": None,
        "bin_table": bin_table,
        "fallback": True,
        "n_pairs": int(n_pairs),
        "n_bins": len(bin_table),
        "fallback_reason": reason,
    }


def fit_vza_calibration(
    matched: pd.DataFrame,
    min_pairs: int = 30,
    min_bin_samples: int = 5,
):
    """
    Fit:

        R(theta) = a*theta^2 + b*theta + c

    theta:
        VZA in degrees.

    The calibration observations should already have passed
    the annual log-ratio IQR screening step.
    """

    if matched.empty:
        return _fallback_model()

    required = [
        "vza_deg",
        "frp",
        "frp_viirs_aggregated",
    ]

    data = matched.dropna(
        subset=required
    ).copy()

    data = data[
        (data["frp"] > 0)
        & (data["frp_viirs_aggregated"] > 0)
        & np.isfinite(data["vza_deg"])
    ]

    if data.empty:
        return _fallback_model()

    data["frp_ratio"] = (
        data["frp_viirs_aggregated"]
        / data["frp"]
    )

    data = data[
        np.isfinite(data["frp_ratio"])
        & (data["frp_ratio"] > 0)
    ]

    if data.empty:
        return _fallback_model()

    global_ratio = float(
        data["frp_ratio"].median()
    )

    if len(data) < min_pairs:
        return _fallback_model(
            global_ratio=global_ratio,
            n_pairs=len(data),
            reason="insufficient_pairs",
        )

    data["vza_bin"] = np.floor(
        data["vza_deg"]
    ).astype(int)

    bins = (
        data.groupby("vza_bin")
        .agg(
            mean_vza=("vza_deg", "mean"),
            mean_ratio=("frp_ratio", "mean"),
            count=("frp_ratio", "size"),
        )
        .reset_index()
    )

    bins = bins[
        bins["count"] >= min_bin_samples
    ].copy()

    if len(bins) < 3:
        return _fallback_model(
            global_ratio=global_ratio,
            n_pairs=len(data),
            bin_table=bins,
            reason="insufficient_vza_bins",
        )

    x = bins["mean_vza"].to_numpy(dtype=float)
    y = bins["mean_ratio"].to_numpy(dtype=float)

    weights = np.sqrt(
        bins["count"].to_numpy(dtype=float)
    )

    try:
        coefficients = np.polyfit(
            x,
            y,
            deg=2,
            w=weights,
        )
    except (ValueError, np.linalg.LinAlgError):
        return _fallback_model(
            global_ratio=global_ratio,
            n_pairs=len(data),
            bin_table=bins,
            reason="polynomial_fit_failed",
        )

    if not np.all(np.isfinite(coefficients)):
        return _fallback_model(
            global_ratio=global_ratio,
            n_pairs=len(data),
            bin_table=bins,
            reason="invalid_coefficients",
        )

    return {
        "coefficients": coefficients,
        "global_ratio": global_ratio,
        "vza_min": float(x.min()),
        "vza_max": float(x.max()),
        "bin_table": bins,
        "fallback": False,
        "n_pairs": len(data),
        "n_bins": len(bins),
        "fallback_reason": None,
    }


def predict_vza_ratio(
    vza_values,
    model,
):

    values = np.asarray(
        vza_values,
        dtype=float,
    )

    global_ratio = float(
        model["global_ratio"]
    )

    coefficients = model["coefficients"]

    if coefficients is None:
        return np.full(
            values.shape,
            global_ratio,
            dtype=float,
        )

    predicted = np.polyval(
        coefficients,
        values,
    )

    valid = (
        np.isfinite(values)
        & np.isfinite(predicted)
        & (predicted > 0)
        & (values >= model["vza_min"])
        & (values <= model["vza_max"])
    )

    return np.where(
        valid,
        predicted,
        global_ratio,
    )
