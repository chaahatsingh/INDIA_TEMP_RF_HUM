"""Plot monthly climatology heatmaps (subdivision x calendar month) to validate the dataset.

Run from the repo root:  python src/plot_climatology.py
Output: figures/climatology_heatmaps.png
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from imd_data import REPO_ROOT
from subdivisions import load_boundaries

TABLE_PATH = REPO_ROOT / "data" / "processed" / "climate_monthly.csv"
NAMES_PATH = REPO_ROOT / "data" / "subdivision_names.csv"
BOUNDARY_PATH = REPO_ROOT / "data" / "raw" / "boundaries" / "imd_sd_boundary.json"
OUTPUT_PATH = REPO_ROOT / "figures" / "climatology_heatmaps.png"

# Rows we validate against known monsoon behaviour; their labels are drawn bold
CHECK_ROWS = {"Kerala", "Tamil Nadu, Puducherry & Karaikal", "West Rajasthan"}
MONTH_LABELS = list("JFMAMJJASOND")

# (column, title, colormap: one hue per variable, light to dark = low to high, colour norm)
PANELS = [
    ("rain_total_mm", "Rainfall (mm / month, sqrt colour scale)", "Blues", mcolors.PowerNorm(0.5)),
    ("tmax_mean_c", "Mean daily max temperature (°C)", "Oranges", None),
    ("rh_mean_pct", "Relative humidity (%)", "Greens", None),
]


def north_to_south_order():
    """Clean subdivision names sorted by polygon centroid latitude, northernmost first."""
    names = pd.read_csv(NAMES_PATH).set_index("imd_name")["subdivision"]
    boundaries = load_boundaries(BOUNDARY_PATH)
    centroid_latitude = boundaries.to_crs("EPSG:6933").centroid.to_crs(4326).y
    ranked = pd.Series(centroid_latitude.values, index=boundaries["subdivisio"].map(names)).sort_values(ascending=False)
    return list(ranked.index)


def main():
    table = pd.read_csv(TABLE_PATH, parse_dates=["ds"])
    table["month"] = table["ds"].dt.month
    order = north_to_south_order()

    figure, axes = plt.subplots(1, 3, figsize=(17, 10), sharey=True)
    for axis, (column, title, colormap, norm) in zip(axes, PANELS):
        climatology = table.groupby(["subdivision", "month"])[column].mean().unstack().reindex(order)
        grid = climatology.to_numpy()
        # Grey hatched background so missing (NaN) rows read as "no data", not as a low value
        axis.imshow(np.ones_like(grid), cmap=mcolors.ListedColormap(["#e6e6e6"]), aspect="auto")
        image = axis.imshow(np.ma.masked_invalid(grid), cmap=colormap, norm=norm, aspect="auto")
        for row, name in enumerate(order):
            if np.isnan(grid[row]).all():
                axis.text(5.5, row, "no data", ha="center", va="center", fontsize=7, color="#666666")
        axis.set_xticks(range(12), MONTH_LABELS)
        axis.set_title(title, fontsize=11, loc="left")
        axis.tick_params(length=0)
        for spine in axis.spines.values():
            spine.set_visible(False)
        colorbar = figure.colorbar(image, ax=axis, orientation="horizontal", pad=0.04, fraction=0.03)
        colorbar.outline.set_visible(False)

    axes[0].set_yticks(range(len(order)), order, fontsize=8)
    for label in axes[0].get_yticklabels():
        if label.get_text() in CHECK_ROWS:
            label.set_fontweight("bold")
    figure.suptitle(
        "India monthly climatology by IMD subdivision, 2016-2025 average (rows sorted north to south)",
        fontsize=13, x=0.01, ha="left",
    )
    figure.tight_layout(rect=(0, 0, 1, 0.97))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_PATH, dpi=110)
    print(f"saved {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
