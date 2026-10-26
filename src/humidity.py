"""Relative humidity from air temperature and dew point (Magnus-type formula)."""
import numpy as np

# Magnus constants from Alduchov & Eskridge (1996), valid for T in degrees C
MAGNUS_A = 17.625
MAGNUS_B_C = 243.04

# Dew point above air temperature is physically impossible. Tiny excesses are rounding
# noise (clip to 100%); anything larger is treated as a data error (NaN).
RH_ROUNDING_TOLERANCE_PCT = 0.5


def fahrenheit_to_celsius(temp_f):
    return (temp_f - 32.0) * 5.0 / 9.0


def relative_humidity_pct(temp_c, dewpoint_c):
    """Relative humidity (%) from air temperature and dew point, both in degrees C."""
    saturation_at_dewpoint = np.exp(MAGNUS_A * dewpoint_c / (MAGNUS_B_C + dewpoint_c))
    saturation_at_temp = np.exp(MAGNUS_A * temp_c / (MAGNUS_B_C + temp_c))
    relative_humidity = 100.0 * saturation_at_dewpoint / saturation_at_temp
    # Clip rounding noise, blank out impossible values (dew point clearly above temperature)
    relative_humidity = np.where(
        relative_humidity <= 100.0 + RH_ROUNDING_TOLERANCE_PCT,
        np.minimum(relative_humidity, 100.0),
        np.nan,
    )
    return relative_humidity
