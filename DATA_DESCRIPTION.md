# Data description

## 1. Purpose

Temperature, rainfall and humidity across the various subdivisions of India, so that
changes in these conditions can be correlated with petrol and diesel sales. To be used
eventually as an events table for a fuel forecasting project.

## 2. Unit of observation

One row per **IMD meteorological subdivision per calendar month**.

- `subdivision`: the region, using IMD's subdivision names (for example, Konkan & Goa,
  Madhya Maharashtra, Marathwada, Vidarbha). Some IMD abbreviations are expanded; the
  full mapping is in `data/subdivision_names.csv`.
- `ds`: the first day of the month (for example, 2023-07-01), so that the table can be
  joined on `ds` to monthly sales data without conversion.
- `region_type`: always `subdivision` in this version, so rows stay self-describing if
  other levels (states, districts) are added later.

A subdivision is used instead of a state because weather differs sharply inside large
states (for example, coastal Konkan vs. interior Maharashtra), and subdivisions are IMD's
own reporting unit for rainfall and temperature. Subdivisions do not always follow state
borders; where a subdivision spans more than one state, no single state is assigned to it.

## 3. Period

January 2016 to December 2025 (120 months), the last full year published by IMD at the
time of download. Every month appears for every subdivision; months where a value is
unavailable are left blank (NaN), never filled with 0.

Humidity is the exception to the full period: the NOAA source stops on 2025-08-24, so
August 2025 is based on 24 days and September to December 2025 are blank.

## 4. Geography

The 36 IMD meteorological subdivisions covering India, using the boundary file published
by IMD (see Sources). Present-day boundaries are applied to the whole period, so that a
subdivision's values are comparable across all years. The aggregation code takes a
boundary file as an input, so the same pipeline can be run at state or district level by
supplying a different file.

A grid cell belongs to a subdivision if its centre falls inside the subdivision's polygon.
Weather stations belong to the subdivision that contains them, or the nearest one within
40 km (this keeps coastal and island stations whose coordinates fall just outside the
simplified polygons).

## 5. Columns

| Column | Unit | Definition |
|---|---|---|
| `subdivision` | text | IMD subdivision name (cleaned; see `data/subdivision_names.csv`) |
| `region_type` | text | Always `subdivision` |
| `ds` | date | First day of the month |
| `rain_total_mm` | mm | Monthly rainfall: the daily rainfall averaged over the subdivision's grid cells, summed over the days of the month |
| `rain_days` | days | Number of days in the month on which the subdivision's area-averaged rainfall was at least 2.5 mm (IMD's "rainy day" threshold) |
| `tmax_mean_c` | °C | Mean over the month of the daily maximum temperature, averaged over the subdivision's grid cells |
| `tmin_mean_c` | °C | Same, for the daily minimum temperature |
| `tavg_c` | °C | (`tmax_mean_c` + `tmin_mean_c`) / 2 |
| `temp_n_cells` | count | Number of 1° temperature grid cells with data behind the temperature values (small = coarse) |
| `rh_mean_pct` | % | Mean relative humidity: computed per day from mean temperature and mean dew point, averaged per station-month, then averaged equally across the subdivision's stations |
| `rh_n_stations` | count | Number of stations behind `rh_mean_pct` (0 when it is blank) |

Daily values are always averaged across space first and then aggregated over time, so
subdivisions with more grid cells do not look wetter just for being bigger.

## 6. Missing data policy

Missing means blank (NaN), never 0. A zero rainfall month and an unknown month are
different things. Where an input is absent (no grid data, no station, or too few days),
the value is blank and the matching count column (`rh_n_stations`) is 0.

## 7. Sources

| Variable | Source | Resolution | Notes |
|---|---|---|---|
| Rainfall | IMD gridded daily rainfall, downloaded with the [`imdlib`](https://pypi.org/project/imdlib/) package (v0.4.0) from IMD Pune | 0.25° | Interpolated from rain-gauge records; years 2016-2025 |
| Temperature (max, min) | IMD gridded daily temperature, via `imdlib` | 1° | Interpolated from station records; years 2016-2025 |
| Humidity | NOAA NCEI Global Summary of the Day (GSOD), Indian stations | Station | Temperature and dew point only; relative humidity is computed from them (Magnus formula, Alduchov & Eskridge 1996 constants). 244 stations had usable data |
| Subdivision boundaries | IMD, `sd_boundary.json` (https://mausam.imd.gov.in/imd_latest/contents/district_shapefiles/sd_boundary.json) | 36 polygons | See limitations: no declared projection, licence not confirmed |

All data were downloaded on 2026-10-26. Everything is observation-based; no model-derived
(reanalysis) or synthetic data is used. NASA POWER was considered and set aside for
that reason.

Licence status: the IMD data and boundary file are published by the India Meteorological
Department, and I found no explicit licence statement for either, so re-use terms are
**unconfirmed**. Check IMD's terms before using this data commercially. NOAA NCEI
publishes GSOD openly; see NOAA's data-access pages for its current usage statement.
The raw downloads are not stored in this repository (`data/raw/` is git-ignored).

## 8. Limitations

**Coverage**
- **Islands.** Lakshadweep and the Andaman & Nicobar Islands have no rain or temperature
  (the IMD grids contain no data there), so those values are blank in every month.
  Their humidity comes from 1-2 stations.
- **Humidity ends in August 2025** (see Period). Arunachal Pradesh has a single station
  and is blank in 8 months; about 7% of subdivision-months rest on a single station.

**Spatial resolution**
- **Temperature is coarse.** The 1° grid is about 110 km, so small subdivisions get few
  cells (Kerala and Coastal Karnataka 2; Uttarakhand, Konkan & Goa and Haryana,
  Chandigarh & Delhi 3). Check `temp_n_cells`; do not use these values for anything
  finer than the subdivision.
- **Gridded values are interpolated from stations**, not direct measurements, and are
  smoother than reality, especially in mountains and in the Northeast.
- **Humidity is point data.** A few stations stand in for a whole subdivision, mostly
  airports and coastal observatories, and they are weighted equally.

**Method**
- **Relative humidity is derived from daily means.** GSOD gives daily mean temperature
  and dew point, so RH is the humidity at those mean conditions, not the mean of
  sub-daily RH. Requiring 8 or more observations a day instead of the GSOD minimum of 4
  changes monthly station RH by 0.03 points on average, so all days are kept.
- **Cell membership uses the cell centre.** About 6.5% of rain grid cells with data
  (321 of 4,964) lie in no subdivision, mostly on the coast or border, and are dropped.
- **Subdivision values are plain area averages**, not weighted by population or by fuel
  demand.

**Boundary file**
- The file has no declared projection. Its coordinates are Albers equal-area metres; the
  parameters were fitted and checked by overlay on the rain grid, which leaves an error
  of roughly 10-20 km. This is small next to the grid sizes but means edges are approximate.
- The file predates the 2019 split of Jammu & Kashmir, so the Jammu & Kashmir polygon
  includes Ladakh. Its `STATE` column and some names are outdated (for example `ORISSA`),
  which is why the data uses subdivision names only.
