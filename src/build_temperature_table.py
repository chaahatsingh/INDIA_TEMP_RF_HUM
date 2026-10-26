"""Build the monthly temperature table: one row per IMD subdivision per month.

Run from the repo root:  python src/build_temperature_table.py
Output: data/processed/temperature_monthly.csv

The temperature grid is 1 degree (~110 km), so small subdivisions only get a few cells.
`temp_n_cells` records how many cells sit behind each value.
"""
import pandas as pd

from imd_data import RAW_DIR, REPO_ROOT, load_year
from subdivisions import cell_membership, load_boundaries

BOUNDARY_PATH = RAW_DIR / "boundaries" / "imd_sd_boundary.json"
OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "temperature_monthly.csv"

START_YEAR, END_YEAR = 2016, 2025
NAME_COLUMN = "subdivisio"


def monthly_mean_for_year(daily_grid, membership, name):
    """Monthly mean of the subdivision's area-averaged daily temperature (NaN if no data)."""
    daily_mean = daily_grid.where(membership == name).mean(["lat", "lon"])
    return daily_mean.resample(time="MS").mean()


def monthly_temperature_for_year(tmax, tmin, boundaries):
    """Return a DataFrame of monthly temperature stats per subdivision for one year."""
    membership = cell_membership(tmax, boundaries, NAME_COLUMN)  # tmax and tmin share a grid
    tables = []
    for name in boundaries[NAME_COLUMN]:
        tmax_monthly = monthly_mean_for_year(tmax, membership, name)
        tmin_monthly = monthly_mean_for_year(tmin, membership, name)
        cells_with_data = int(((membership == name) & ~tmax.isnull().all("time")).sum())
        tables.append(pd.DataFrame({
            "subdivision": name,
            "region_type": "subdivision",
            "ds": tmax_monthly.time.values,
            "tmax_mean_c": tmax_monthly.values,
            "tmin_mean_c": tmin_monthly.values,
            "tavg_c": (tmax_monthly.values + tmin_monthly.values) / 2,
            "temp_n_cells": cells_with_data,
        }))
    return pd.concat(tables, ignore_index=True)


def main():
    boundaries = load_boundaries(BOUNDARY_PATH)
    yearly_tables = []
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"processing {year}")
        yearly_tables.append(
            monthly_temperature_for_year(load_year("tmax", year), load_year("tmin", year), boundaries)
        )
    table = pd.concat(yearly_tables, ignore_index=True).sort_values(["subdivision", "ds"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_PATH, index=False, float_format="%.2f")
    print(f"wrote {len(table)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
