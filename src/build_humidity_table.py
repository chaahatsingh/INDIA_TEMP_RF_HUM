"""Build the monthly relative-humidity table: one row per IMD subdivision per month.

Run from the repo root:  python src/build_humidity_table.py   (after src/download_gsod.py)
Output: data/processed/humidity_monthly.csv

Daily RH comes from NOAA GSOD station temperature and dew point. A station-month needs at
least MIN_DAYS_PER_MONTH usable days; a subdivision-month is the equal-weight mean over its
stations. `rh_n_stations` records how many stations sit behind each value.
"""
import glob

import geopandas as gpd
import pandas as pd

from humidity import fahrenheit_to_celsius, relative_humidity_pct
from imd_data import RAW_DIR, REPO_ROOT
from subdivisions import assign_points_to_regions, load_boundaries

BOUNDARY_PATH = RAW_DIR / "boundaries" / "imd_sd_boundary.json"
GSOD_DIR = RAW_DIR / "gsod"
OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "humidity_monthly.csv"

START_YEAR, END_YEAR = 2016, 2025
MIN_DAYS_PER_MONTH = 15
GSOD_MISSING = 9999.0  # GSOD writes 9999.9 for a missing value
NAME_COLUMN = "subdivisio"


def load_daily_rh():
    """Read every GSOD station file and return daily RH per station (rows with TEMP and DEWP only)."""
    frames = [
        pd.read_csv(path, usecols=["STATION", "DATE", "LATITUDE", "LONGITUDE", "TEMP", "DEWP"])
        for path in glob.glob(str(GSOD_DIR / "*" / "*.csv"))
    ]
    daily = pd.concat(frames, ignore_index=True)
    daily = daily[(daily["TEMP"] < GSOD_MISSING) & (daily["DEWP"] < GSOD_MISSING)].copy()
    daily["STATION"] = daily["STATION"].astype(str)
    daily["rh_pct"] = relative_humidity_pct(
        fahrenheit_to_celsius(daily["TEMP"].to_numpy()), fahrenheit_to_celsius(daily["DEWP"].to_numpy())
    )
    daily["ds"] = pd.to_datetime(daily["DATE"]).dt.to_period("M").dt.to_timestamp()
    return daily


def station_months(daily):
    """Monthly mean RH per station, keeping only months with enough usable days."""
    grouped = daily.dropna(subset=["rh_pct"]).groupby(["STATION", "ds"])["rh_pct"]
    monthly = grouped.agg(rh_mean_pct="mean", usable_days="size").reset_index()
    return monthly[monthly["usable_days"] >= MIN_DAYS_PER_MONTH]


def main():
    boundaries = load_boundaries(BOUNDARY_PATH)
    daily = load_daily_rh()

    stations = daily.groupby("STATION")[["LATITUDE", "LONGITUDE"]].first()
    station_points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(stations["LONGITUDE"], stations["LATITUDE"]),
        index=stations.index, crs=4326,
    )
    stations["subdivision"] = assign_points_to_regions(station_points, boundaries, NAME_COLUMN)
    print(f"stations: {len(stations)} | assigned to a subdivision: {int(stations['subdivision'].notna().sum())}")

    monthly = station_months(daily).merge(stations[["subdivision"]], left_on="STATION", right_index=True)
    monthly = monthly.dropna(subset=["subdivision"])
    by_subdivision = monthly.groupby(["subdivision", "ds"]).agg(
        rh_mean_pct=("rh_mean_pct", "mean"), rh_n_stations=("STATION", "nunique")
    )

    # Full grid of every subdivision x every month, so gaps are explicit NaN rows, never missing rows
    all_months = pd.date_range(f"{START_YEAR}-01-01", f"{END_YEAR}-12-01", freq="MS")
    full_index = pd.MultiIndex.from_product([boundaries[NAME_COLUMN], all_months], names=["subdivision", "ds"])
    table = by_subdivision.reindex(full_index).reset_index()
    table["rh_n_stations"] = table["rh_n_stations"].fillna(0).astype(int)  # 0 stations = no data
    table.insert(1, "region_type", "subdivision")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.sort_values(["subdivision", "ds"]).to_csv(OUTPUT_PATH, index=False, float_format="%.2f")
    print(f"wrote {len(table)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
