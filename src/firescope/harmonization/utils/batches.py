from pathlib import Path
import gc
import logging

import pandas as pd

from ..utils.chunk_processor import load_parquet_directory
from ..utils.vza import estimate_vza_array
from ..core.deduplication import deduplicate_footprints
from ..core.spatial_matching import aggregate_viirs_to_modis
from ..core.fusion import fuse_modis_footprints


logger = logging.getLogger(__name__)


def _write_parquet_atomic(df, output_path):
    """
    Write a DataFrame to Parquet atomically.

    Shapely geometries are serialized to WKB before writing,
    because PyArrow cannot directly serialize Shapely objects.
    """
    output_path = Path(output_path)

    temp_path = output_path.with_name(
        output_path.stem + ".tmp.parquet"
    )

    data = df.copy()

    # Convert Shapely geometry objects into WKB bytes.
    if "geometry" in data.columns:
        data["geometry_wkb"] = data["geometry"].map(
            lambda geom: (
                geom.wkb
                if geom is not None and hasattr(geom, "wkb")
                else None
            )
        )

        # Remove unsupported Shapely objects.
        data.drop(
            columns=["geometry"],
            inplace=True,
        )

    try:
        data.to_parquet(
            temp_path,
            index=False,
            engine="pyarrow",
            compression="snappy",
        )

        temp_path.replace(output_path)

    except Exception:
        if temp_path.exists():
            temp_path.unlink()

        raise

    finally:
        del data


def _batch_marker(directory, prefix, batch_start, batch_end):
    """
    Return a completion-marker path for a date batch.
    """
    name = (
        f"{prefix}_{batch_start:%Y%m%d}_"
        f"{batch_end:%Y%m%d}.done"
    )
    return Path(directory) / name


def generate_matched_batches(
    year,
    modis_temp,
    viirs_temp,
    matched_dir,
    batch_days=5,
    dedup_time_seconds=0,
    overlap_threshold=0.30,
    max_time_minutes=5,
    force_reprocess=False,
):
    if batch_days < 1:
        raise ValueError("batch_days must be >= 1")

    matched_dir = Path(matched_dir)
    matched_dir.mkdir(parents=True, exist_ok=True)

    start = pd.Timestamp(year=year, month=1, day=1)
    end = pd.Timestamp(year=year, month=12, day=31)

    batch_start = start

    while batch_start <= end:
        batch_end = min(
            batch_start + pd.Timedelta(days=batch_days - 1),
            end,
        )

        batch_name = (
            f"{batch_start:%Y%m%d}_{batch_end:%Y%m%d}"
        )

        output_path = matched_dir / f"matched_{batch_name}.parquet"
        marker_path = _batch_marker(
            matched_dir,
            "matched",
            batch_start,
            batch_end,
        )

        if not force_reprocess and marker_path.exists():
            logger.info("Already matched: %s", batch_name)
        else:
            if force_reprocess:
                marker_path.unlink(missing_ok=True)
                output_path.unlink(missing_ok=True)

            logger.info(
                "[%s] Matching batch %s to %s",
                year,
                batch_start.date(),
                batch_end.date(),
            )

            load_start = batch_start - pd.Timedelta(days=1)
            load_end = batch_end + pd.Timedelta(days=1)

            modis = None
            viirs = None
            central_modis = None
            matched = None

            try:
                modis = load_parquet_directory(
                    modis_temp,
                    start_date=load_start,
                    end_date=load_end,
                )

                viirs = load_parquet_directory(
                    viirs_temp,
                    start_date=load_start,
                    end_date=load_end,
                )

                if modis.empty:
                    logger.info(
                        "No MODIS records in batch %s",
                        batch_name,
                    )
                else:
                    modis = deduplicate_footprints(
                        modis,
                        time_seconds=dedup_time_seconds,
                        overlap_threshold=overlap_threshold,
                    )

                    if not viirs.empty:
                        viirs = deduplicate_footprints(
                            viirs,
                            time_seconds=dedup_time_seconds,
                            overlap_threshold=overlap_threshold,
                        )

                    central_mask = (
                        (modis["acq_date"] >= batch_start.strftime("%Y-%m-%d"))
                        &
                        (modis["acq_date"] <= batch_end.strftime("%Y-%m-%d"))
                    )

                    central_modis = modis.loc[
                        central_mask
                    ].copy()

                    if central_modis.empty or viirs.empty:
                        logger.info(
                            "No possible matches in %s "
                            "(central MODIS=%d, buffered VIIRS=%d)",
                            batch_name,
                            len(central_modis),
                            len(viirs),
                        )
                    else:
                        matched = aggregate_viirs_to_modis(
                            central_modis,
                            viirs,
                            max_time_minutes=max_time_minutes,
                        )

                        if matched.empty:
                            logger.info(
                                "No matched records in %s",
                                batch_name,
                            )
                        else:
                            _write_parquet_atomic(
                                matched,
                                output_path,
                            )

                            logger.info(
                                "Saved %s matched records to %s",
                                f"{len(matched):,}",
                                output_path.name,
                            )

                # Mark the batch complete only after processing
                # has finished successfully, including empty batches.
                marker_path.touch()

            except Exception:
                logger.exception(
                    "Failed to process matching batch %s",
                    batch_name,
                )
                raise

            finally:
                del modis, viirs, central_modis, matched
                gc.collect()

        # Always advance to the next batch.
        batch_start = batch_end + pd.Timedelta(days=1)

    return matched_dir


def generate_harmonized_batches(
    year,
    matched_dir,
    calibration_model,
    output_dir,
    force_reprocess=False,
):
    """
    Apply one annual VZA calibration model to every matched batch
    and generate harmonized MODIS-footprint records.

    The model should be fitted once using annual matched data.
    It should not be refitted independently for each batch.
    """
    if calibration_model is None:
        raise ValueError(
            "An annual calibration_model is required."
        )

    matched_dir = Path(matched_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(matched_dir.glob("matched_*.parquet"))

    if not files:
        logger.warning(
            "No matched Parquet files found in %s",
            matched_dir,
        )
        return output_dir

    for path in files:
        date_range = path.stem.replace("matched_", "")
        output_path = output_dir / f"harmonized_{date_range}.parquet"
        marker_path = output_dir / f"harmonized_{date_range}.done"

        if not force_reprocess and marker_path.exists():
            logger.info("Already harmonized: %s", output_path.name)
            continue

        if force_reprocess:
            marker_path.unlink(missing_ok=True)
            output_path.unlink(missing_ok=True)

        logger.info("Harmonizing batch: %s", date_range)

        matched = pd.read_parquet(path)

        if matched.empty:
            marker_path.touch()
            continue

        try:
            if "track" not in matched.columns:
                raise KeyError(
                    f"'track' column missing in {path.name}"
                )

            # Estimate VZA using the MODIS scan-track geometry model.
            matched["vza_deg"] = estimate_vza_array(
                matched["track"].to_numpy(dtype=float)
            )

            # Apply the same annual calibration model to all valid
            # matched records, including observations excluded from
            # the calibration-fitting sample by IQR screening.
            harmonized = fuse_modis_footprints(
                matched,
                calibration_model,
            )

            harmonized["year"] = year

            _write_parquet_atomic(harmonized, output_path)
            marker_path.touch()

            logger.info(
                "Saved %s harmonized records to %s",
                f"{len(harmonized):,}",
                output_path.name,
            )

        finally:
            del matched
            if "harmonized" in locals():
                del harmonized
            gc.collect()

    return output_dir
