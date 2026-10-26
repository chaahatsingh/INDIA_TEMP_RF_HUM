"""Build the monthly rainfall table: one row per IMD subdivision per month.

Run from the repo root:  python src/build_rain_table.py
Output: data/processed/rain_monthly.csv
"""
import pandas as pd

from imd_data import RAW_DIR, REPO_ROOT, load_year
from subdivisions import cell_membership, load_boundaries

BOUNDARY_PATH = RAW_DIR / "boundaries" / "imd_sd_boundary.json"
OUTPUT_PATH = REPO_ROOT / "data" / "processed" / "rain_monthly.csv"

START_YEAR, END_YEAR = 2016, 2025
RAINY_DAY_THRESHOLD_MM = 2.5  # IMD's definition of a "rainy day"
NAME_COLUMN = "subdivisio"


def monthly_rain_for_year(rain, boundaries):
    """Return a DataFrame of monthly rain stats per subdivision for one year."""
    membership = cell_membership(rain, boundaries, NAME_COLUMN)
    tables = []
    for name in boundaries[NAME_COLUMN]:
        # Daily rain averaged over the subdivision's cells (NaN cells are skipped).
        daily_mean = rain.where(membership == name).mean(["lat", "lon"])
        # min_count=1 keeps all-NaN periods as NaN; the default would turn them into 0.
        rain_total = daily_mean.resample(time="MS").sum(min_count=1)
        rainy_day = (daily_mean >= RAINY_DAY_THRESHOLD_MM).where(daily_mean.notnull())
        rain_days = rainy_day.resample(time="MS").sum(min_count=1)
        tables.append(pd.DataFrame({
            "subdivision": name,
            "region_type": "subdivision",
            "ds": rain_total.time.values,
            "rain_total_mm": rain_total.values,
            "rain_days": rain_days.values,
        }))
    return pd.concat(tables, ignore_index=True)


def main():
    boundaries = load_boundaries(BOUNDARY_PATH)
    yearly_tables = []
    for year in range(START_YEAR, END_YEAR + 1):
        print(f"processing {year}")
        yearly_tables.append(monthly_rain_for_year(load_year("rain", year), boundaries))
    table = pd.concat(yearly_tables, ignore_index=True).sort_values(["subdivision", "ds"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(OUTPUT_PATH, index=False, float_format="%.2f")
    print(f"wrote {len(table)} rows to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
