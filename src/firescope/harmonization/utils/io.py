from pathlib import Path
import pandas as pd
import logging

from ..configs.settings import MODISinfo, VIIRSinfo

logger = logging.getLogger(__name__)


def get_year_files(modis_dir: Path, viirs_dir: Path, year: int):
    modis_year_dir = Path(modis_dir) / str(year)
    viirs_year_dir = Path(viirs_dir) / str(year)

    modis_files = (
        sorted(modis_year_dir.glob("*.csv"))
        if modis_year_dir.exists()
        else []
    )

    viirs_files = (
        sorted(viirs_year_dir.glob("*.csv"))
        if viirs_year_dir.exists()
        else []
    )

    logger.info(f"[{year}] MODIS files: {len(modis_files)}")
    logger.info(f"[{year}] VIIRS files: {len(viirs_files)}")

    return modis_files, viirs_files


def validate_csv_header(path: Path, sensor: str):
    required = (
        MODISinfo.features if sensor.upper() == "MODIS"
        else VIIRSinfo.features
    )

    header = pd.read_csv(path, nrows=0)
    normalized = {str(c).strip().lower() for c in header.columns}

    missing = required - normalized
    if missing:
        raise ValueError(
            f"{path.name}: missing required columns: {sorted(missing)}"
        )


def iter_csv_chunks(
    files,
    sensor: str,
    chunksize: int = 100_000,
):
    """
    Yield one normalized source CSV chunk at a time.

    source_file and country_file are retained on every record.
    """
    for path in sorted(files):
        path = Path(path)

        try:
            validate_csv_header(path, sensor)

            reader = pd.read_csv(
                path,
                chunksize=chunksize,
                low_memory=False,
                dtype={
                    "confidence": "string",
                    "type": "string",
                    "acq_date": "string",
                    "acq_time": "string",
                },
            )

            for chunk in reader:
                chunk.columns = [
                    str(c).strip().lower()
                    for c in chunk.columns
                ]

                chunk["source_file"] = path.name
                chunk["country_file"] = path.stem

                yield chunk

        except Exception as exc:
            logger.error(
                f"Failed to read {path}: {exc}"
            )
