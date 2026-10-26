"""Download NOAA GSOD daily station files for Indian stations, 2016-2025.

Run from the repo root:  python src/download_gsod.py
Files go to data/raw/gsod/<year>/<station_id>.csv (gitignored). Existing files are skipped,
so the script can be re-run safely after an interruption.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
import requests

from imd_data import RAW_DIR

STATION_CATALOGUE_URL = "https://www.ncei.noaa.gov/pub/data/noaa/isd-history.csv"
GSOD_URL = "https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/{year}/{station_id}.csv"
GSOD_DIR = RAW_DIR / "gsod"
START_YEAR, END_YEAR = 2016, 2025
MAX_WORKERS = 8  # modest parallelism, to be polite to NOAA's server


def indian_station_ids():
    """Return (station_id, name, lat, lon) for Indian stations whose record overlaps the period."""
    catalogue_path = GSOD_DIR / "isd-history.csv"
    if not catalogue_path.exists():
        GSOD_DIR.mkdir(parents=True, exist_ok=True)
        catalogue_path.write_bytes(requests.get(STATION_CATALOGUE_URL, timeout=90).content)
    stations = pd.read_csv(catalogue_path, dtype=str)
    stations = stations[stations["CTRY"] == "IN"].copy()
    began = pd.to_datetime(stations["BEGIN"])
    ended = pd.to_datetime(stations["END"])
    overlaps = (began <= f"{END_YEAR}-12-31") & (ended >= f"{START_YEAR}-01-01")
    stations = stations[overlaps]
    # GSOD file name = USAF + WBAN concatenated (e.g. 42071099999)
    stations["station_id"] = stations["USAF"] + stations["WBAN"]
    return stations[["station_id", "STATION NAME", "LAT", "LON"]]


def download_one(job):
    """Fetch one station-year. Returns 'ok', 'skipped' (already on disk) or 'missing' (404)."""
    year, station_id = job
    target = GSOD_DIR / str(year) / f"{station_id}.csv"
    if target.exists():
        return "skipped"
    for _attempt in range(3):
        try:
            response = requests.get(GSOD_URL.format(year=year, station_id=station_id), timeout=60)
        except requests.RequestException:
            continue
        if response.status_code == 404:
            return "missing"
        if response.ok:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(response.content)
            return "ok"
    return "failed"


def main():
    station_ids = indian_station_ids()["station_id"].tolist()
    jobs = [(year, sid) for year in range(START_YEAR, END_YEAR + 1) for sid in station_ids]
    print(f"{len(station_ids)} stations x {END_YEAR - START_YEAR + 1} years = {len(jobs)} files")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        results = list(pool.map(download_one, jobs))
    print({status: results.count(status) for status in set(results)})


if __name__ == "__main__":
    main()
