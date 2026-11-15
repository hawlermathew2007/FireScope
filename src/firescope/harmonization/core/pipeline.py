from pathlib import Path
import logging

from .calibration import build_annual_calibration
from ..utils.io import get_year_files
from ..utils.batches import (
    generate_matched_batches,
    generate_harmonized_batches
)
from ..utils.chunk_processor import process_files_to_parquet

logger = logging.getLogger(__name__)


def preprocess_year(
    year,
    modis_files,
    viirs_files,
    work_dir,
    chunksize=100_000,
):
    work_dir = Path(work_dir)

    modis_temp = work_dir / str(year) / "modis"
    viirs_temp = work_dir / str(year) / "viirs"

    logger.info(
        "[%s] Preprocessing MODIS files.",
        year,
    )

    process_files_to_parquet(
        modis_files,
        modis_temp,
        sensor="MODIS",
        vegetation_only=True,
        chunksize=chunksize,
    )

    logger.info(
        "[%s] Preprocessing VIIRS files.",
        year,
    )

    process_files_to_parquet(
        viirs_files,
        viirs_temp,
        sensor="VIIRS",
        vegetation_only=True,
        chunksize=chunksize,
    )

    return modis_temp, viirs_temp


def run_year(
    year: int,
    modis_dir: Path,
    viirs_dir: Path,
    work_dir: Path,
    results_dir: Path,
    chunksize: int = 100_000,
    batch_days: int = 1,
    force_reprocess: bool = False,
):
    """
    Run annual MODIS-VIIRS harmonization without loading
    the entire year's records into memory.

    Stages:
        1. CSV -> chunked Parquet preprocessing
        2. Daily or multi-day matching
        3. Annual calibration
        4. Daily or multi-day fusion
    """

    if batch_days < 1:
        raise ValueError("batch_days must be >= 1")

    modis_files, viirs_files = get_year_files(
        modis_dir,
        viirs_dir,
        year,
    )

    if not modis_files:
        logger.warning(
            "[%s] No MODIS files found.",
            year,
        )
        return None

    if not viirs_files:
        logger.warning(
            "[%s] No VIIRS files found.",
            year,
        )
        return None

    work_dir = Path(work_dir)
    results_dir = Path(results_dir)

    year_work_dir = work_dir / str(year)
    year_results_dir = results_dir / str(year)

    matched_dir = year_work_dir / "matched"

    logger.info(
        "[%s] Starting harmonization. Batch size: %s day(s).",
        year,
        batch_days,
    )

    # Stage 1: CSV -> Parquet
    modis_temp, viirs_temp = preprocess_year(
        year=year,
        modis_files=modis_files,
        viirs_files=viirs_files,
        work_dir=work_dir,
        chunksize=chunksize,
    )

    # Stage 2: Batch deduplication and spatial matching
    logger.info(
        "[%s] Starting batch matching.",
        year,
    )

    generate_matched_batches(
        year=year,
        modis_temp=modis_temp,
        viirs_temp=viirs_temp,
        matched_dir=matched_dir,
        batch_days=batch_days,
        force_reprocess=force_reprocess,
    )

    # Stage 3: Annual calibration
    logger.info(
        "[%s] Building annual calibration model.",
        year,
    )

    calibration_model = build_annual_calibration(
        matched_dir=matched_dir,
        year=year,
        min_pairs=30,
        min_bin_samples=5,
        iqr_multiplier=1.5,
    )

    logger.info(
        "[%s] Calibration fallback: %s",
        year,
        calibration_model["fallback"],
    )

    logger.info(
        "[%s] Calibration pairs: %s",
        year,
        calibration_model.get("n_pairs", 0),
    )

    # Stage 4: Batch fusion
    logger.info(
        "[%s] Starting batch fusion.",
        year,
    )

    output_paths = generate_harmonized_batches(
        year=year,
        matched_dir=matched_dir,
        calibration_model=calibration_model,
        output_dir=year_results_dir,
        batch_days=batch_days,
        force_reprocess=force_reprocess,
    )

    logger.info(
        "[%s] Harmonization completed.",
        year,
    )

    return output_paths
