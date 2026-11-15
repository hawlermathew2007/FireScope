import numpy as np
from scipy.optimize import brentq
from ..configs.settings import MODISinfo


def estimate_vza_array(track_km):

    if track_km < 1.0:
        return np.nan

    # NASA's along-track pixel dimension model
    def track_model(omega):
        return MODISinfo.satellite_distance * MODISinfo.ifov * (
            np.cos(omega) -
            np.sqrt(
                (MODISinfo.earth_radius / MODISinfo.satellite_distance)**2 - np.sin(omega)**2
            )
        )

    try:
        # Estimate satellite scan angle
        omega = brentq(
            lambda x: track_model(x) - track_km,
            0.0,
            np.deg2rad(55.0)
        )

        # Convert scan angle to viewing zenith angle
        argument = (MODISinfo.satellite_distance / MODISinfo.earth_radius) * np.sin(omega)

        if abs(argument) > 1:
            return np.nan

        vza = np.arcsin(argument)

        return np.degrees(vza)

    except ValueError:
        return np.nan


if __name__ == "__main__":
    track_values = [1.0, 1.1, 1.2, 1.5, 2.0]

    for track in track_values:
        print(
            f"Track: {track:.1f} km | "
            f"Estimated VZA: "
            f"{estimate_vza_array(track):.2f} degrees"
        )
