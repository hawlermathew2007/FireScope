from dataclasses import dataclass
from pydantic_settings import BaseSettings
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_DIR / "data"


class MODISinfo(BaseSettings):
    earth_radius: float = 6378.137        # Earth radius (km)
    satellite_altitude: float = 705.0     # Satellite altitude (km)
    ifov: float = 0.0014184397            # MODIS angular IFOV parameter (rad)
    features: set = {
        "latitude", "longitude", "brightness", "scan", "track", "acq_date",
        "acq_time", "satellite", "instrument", "confidence", "version",
        "bright_t31", "frp", "daynight", "type",
    }

    @property
    def satellite_distance(self) -> float:  # km
        return self.earth_radius + self.satellite_altitude


class VIIRSinfo(BaseSettings):
    features: set = {
        "latitude", "longitude", "bright_ti4", "scan", "track", "acq_date",
        "acq_time", "satellite", "instrument", "confidence", "version",
        "bright_ti5", "frp", "daynight", "type",
    }


@dataclass(frozen=True)
class Settings:
    start_year: int = 2023  # test only (this is an argument to be inputted)
    end_year: int = 2024

    modis_dir: Path = DATA_DIR / "raw" / "modis"
    viirs_dir: Path = DATA_DIR / "raw" / "viirs-noaa20"

    work_dir: Path = DATA_DIR / "processing"
    results_dir: Path = DATA_DIR / "results"

    chunksize = 50_000
    # max_time_difference_minutes: int = 5
    # anomaly_iqr_multiplier: float = 1.5
    # min_calibration_pairs: int = 30
    # vegetation_fires_only: bool = True


SETTINGS = Settings()
MODISinfo = MODISinfo()
VIIRSinfo = VIIRSinfo()
