"""Download and open IMD gridded daily data (rain, tmax, tmin)."""
from pathlib import Path

import imdlib as imd

REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = REPO_ROOT / "data" / "raw"


def load_year(variable, year):
    """Download (if not already on disk) and open one year of a daily IMD variable.

    variable: "rain", "tmax" or "tmin". Returns an xarray DataArray (time, lat, lon).
    imdlib already converts IMD's -999 "no data" marker to NaN.
    """
    if not (RAW_DIR / variable / f"{year}.grd").exists():
        imd.get_data(variable, year, year, fn_format="yearwise", file_dir=str(RAW_DIR))
    data = imd.open_data(variable, year, year, fn_format="yearwise", file_dir=str(RAW_DIR))
    return data.get_xarray()[variable]
