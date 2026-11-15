import numpy as np
import pandas as pd


def _parse_datetime(df: pd.DataFrame) -> pd.Series:
    dates = pd.to_datetime(df["acq_date"], errors="coerce")

    raw_time = (
        df["acq_time"]
        .astype("string")
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
        .str.zfill(4)
    )

    valid_time = raw_time.str.fullmatch(r"\d{4}")

    parsed_time = pd.to_datetime(
        raw_time.where(valid_time),
        format="%H%M",
        errors="coerce",
    )

    return (
        dates
        + pd.to_timedelta(parsed_time.dt.hour, unit="h")
        + pd.to_timedelta(parsed_time.dt.minute, unit="m")
    )


def modis_confidence_class(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None

    if not np.isfinite(value) or not 0 <= value <= 100:
        return None

    if value < 30:
        return "low"
    if value < 80:
        return "nominal"

    return "high"


def viirs_confidence_class(value):
    value = str(value).strip().lower()

    return {
        "l": "low",
        "n": "nominal",
        "h": "high",
    }.get(value)


def normalize(df: pd.DataFrame, sensor: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    sensor = sensor.upper()

    if sensor not in {"MODIS", "VIIRS"}:
        raise ValueError("sensor must be MODIS or VIIRS")

    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]

    numeric_columns = [
        "latitude",
        "longitude",
        "scan",
        "track",
        "frp",
    ]

    if sensor == "MODIS":
        numeric_columns += ["brightness", "bright_t31"]
    else:
        numeric_columns += ["bright_ti4", "bright_ti5"]

    for col in numeric_columns:
        if col in out.columns:
            out[col] = pd.to_numeric(
                out[col],
                errors="coerce",
            )

    required = [
        "latitude",
        "longitude",
        "scan",
        "track",
        "frp",
        "acq_date",
        "acq_time",
        "confidence",
    ]

    missing = [col for col in required if col not in out.columns]

    if missing:
        raise ValueError(
            f"{sensor} data missing columns: {missing}"
        )

    # FIRMS time precision is minute-level.
    # Do not interpret this as a true second-resolution timestamp.
    out["datetime_utc"] = _parse_datetime(out)

    out["sensor"] = sensor

    if sensor == "MODIS":
        out["confidence_class"] = (
            out["confidence"].map(modis_confidence_class)
        )
    else:
        out["confidence_class"] = (
            out["confidence"].map(viirs_confidence_class)
        )

    out["confidence_rank"] = (
        out["confidence_class"]
        .map({
            "low": 1,
            "nominal": 2,
            "high": 3,
        })
        .astype("Int64")
    )

    # Preserve the original sensor confidence.
    out["sensor_confidence"] = out["confidence"]

    return out


def prescreen(
    df: pd.DataFrame,
    vegetation_only: bool = True,
) -> pd.DataFrame:

    if df.empty:
        return df.copy()

    required = [
        "latitude",
        "longitude",
        "scan",
        "track",
        "frp",
        "datetime_utc",
        "confidence_rank",
    ]

    missing = [col for col in required if col not in df.columns]

    if missing:
        raise ValueError(
            f"Missing normalized columns: {missing}"
        )

    out = df.dropna(subset=required).copy()

    out = out[
        (out["frp"] > 0)
        & (out["scan"] > 0)
        & (out["track"] > 0)
        & out["latitude"].between(-90, 90)
        & out["longitude"].between(-180, 180)
    ]

    if vegetation_only:
        if "type" not in out.columns:
            raise ValueError(
                "type column required for vegetation_only=True"
            )

        fire_type = pd.to_numeric(
            out["type"],
            errors="coerce",
        )

        out = out[fire_type == 0]

    return out.reset_index(drop=True)
