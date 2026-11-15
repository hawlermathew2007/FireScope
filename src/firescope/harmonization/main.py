import logging

from .general.logger import setup_logger
from .configs.settings import SETTINGS
from .core.pipeline import run_year


setup_logger()
logger = logging.getLogger(__name__)


def main():
    s = SETTINGS

    logger.info("Starting main()")
    logger.info(f"Test run_year availability: {run_year}")
    logger.info("Year range: %s - %s", s.start_year, s.end_year)
    logger.info("MODIS directory: %s", s.modis_dir)
    logger.info("VIIRS directory: %s", s.viirs_dir)
    logger.info("Results directory: %s", s.results_dir)

    if s.start_year > s.end_year:
        raise ValueError("HARM_START_YEAR must be <= HARM_END_YEAR")

    for year in range(
        s.start_year,
        s.end_year + 1,
    ):
        try:
            run_year(
                year=year,
                modis_dir=s.modis_dir,
                viirs_dir=s.viirs_dir,
                work_dir=s.work_dir,
                results_dir=s.results_dir,
                chunksize=s.chunksize,
            )
            logger.info("Successfully completed %s", year)

        except Exception:
            logger.exception("Harmonization failed for year %s", year)
            raise


if __name__ == "__main__":
    print(
        f"Start data harmonization of MODIS and VIIRS-NOAA20 data "
        f"({SETTINGS.start_year} - {SETTINGS.end_year})",
        flush=True,
    )

    print("...", flush=True)

    try:
        main()
    finally:
        print("Execution reached the end of main()", flush=True)

    print("Done harmonizing!", flush=True)
