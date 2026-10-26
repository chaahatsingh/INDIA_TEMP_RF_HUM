"""Merge the rain, temperature and humidity tables into the final monthly climate table.

Run from the repo root:  python src/assemble_table.py   (after the three build_*_table.py scripts)
Output: data/processed/climate_monthly.csv
"""
import pandas as pd

from imd_data import REPO_ROOT

PROCESSED_DIR = REPO_ROOT / "data" / "processed"
NAMES_PATH = REPO_ROOT / "data" / "subdivision_names.csv"
OUTPUT_PATH = PROCESSED_DIR / "climate_monthly.csv"
KEY_COLUMNS = ["subdivision", "region_type", "ds"]

COLUMN_ORDER = [
    "subdivision", "region_type", "ds",
    "rain_total_mm", "rain_days",
    "tmax_mean_c", "tmin_mean_c", "tavg_c", "temp_n_cells",
    "rh_mean_pct", "rh_n_stations",
]


def read_table(name, clean_names):
    """Read one monthly table and replace IMD's subdivision names with the approved clean names."""
    table = pd.read_csv(PROCESSED_DIR / f"{name}_monthly.csv", parse_dates=["ds"])
    table["subdivision"] = table["subdivision"].map(clean_names)
    if table["subdivision"].isna().any():
        raise ValueError(f"{name}: a subdivision has no entry in {NAMES_PATH.name}")
    return table


def main():
    names = pd.read_csv(NAMES_PATH)
    clean_names = dict(zip(names["imd_name"], names["subdivision"]))

    rain = read_table("rain", clean_names)
    temperature = read_table("temperature", clean_names)
    humidity = read_table("humidity", clean_names)

    # Left joins on the full key; the row-count check catches any name mismatch or duplicate key
    merged = rain.merge(temperature, on=KEY_COLUMNS, how="left").merge(humidity, on=KEY_COLUMNS, how="left")
    if len(merged) != len(rain):
        raise ValueError(f"merge changed the row count: {len(rain)} -> {len(merged)}")

    merged = merged[COLUMN_ORDER].sort_values(["subdivision", "ds"])
    merged.to_csv(OUTPUT_PATH, index=False, float_format="%.2f", date_format="%Y-%m-%d")
    print(f"wrote {len(merged)} rows x {merged.shape[1]} columns to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
