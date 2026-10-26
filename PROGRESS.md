# Progress

## Done
- Steps 1-2: repo setup, data spec (`DATA_DESCRIPTION.md`; sections 5, 7, 8 still to fill).
- Step 3: IMD rain explored (`notebooks/02_imd_rain_explore.ipynb`).
  - `imd.get_data('rain', 2023, 2023, fn_format='yearwise', file_dir='data/raw')` then `.get_xarray()`.
  - 0.25 deg grid: 129 lat x 135 lon, daily. -999 already converted to NaN by imdlib. ~71% NaN = ocean/outside India.
  - Latest year available: 2025 (2026 not published). Period = Jan 2016 - Dec 2025.
- Step 4: subdivision boundaries.
  - Source: https://mausam.imd.gov.in/imd_latest/contents/district_shapefiles/sd_boundary.json
  - Saved to `data/raw/boundaries/imd_sd_boundary.json` (gitignored; code should download it, URL goes in README).
  - 36 polygons. Columns: `region_cod`, `subdivisio` (name), `STATE` (stale, unused), `Area` (km2).
  - Licence NOT confirmed (no statement found). Mention in README.
  - File has NO declared CRS; coordinates are metres. `Area` == planar area in the file's own CRS, so it is an equal-area (Albers) projection.
  - Fitted CRS (approximate, ~10-20 km error, verified by overlay on rain land mask):
    `+proj=aea +lat_1=20.983 +lat_2=27.971 +lat_0=0 +lon_0=79.986 +x_0=402204 +y_0=66056 +datum=WGS84 +units=m`
  - geopandas wrongly assumes EPSG:4326 on read: use `.set_crs(crs, allow_override=True).to_crs(4326)`.
  - Names are IMD-style abbreviations (e.g. `N M M T`, `HAR. CHD & DELHI`); rename for the final table.

- Step 5: grid -> subdivision aggregation (`src/subdivisions.py`: `load_boundaries`, `cell_membership`).
  - Rule: a cell belongs to the polygon containing its CENTRE. Daily area-mean over cells, then sum days to months.
  - Kerala 2023 checked: 50 cells (~38k km2), monthly pattern realistic (Jul 603 mm, weak Aug 63 mm, annual 2371 mm).
  - All 36 subdivisions get >=1 cell (630-790 km2/cell). LAKSHADWEEP (1 cell) and A & N ISLAND (8 cells) have no rain data -> NaN.
- Step 6 (rain part): `python src/build_rain_table.py` -> `data/processed/rain_monthly.csv` (4320 rows = 36 x 120, 2016-01 to 2025-12).
  - Columns so far: subdivision (IMD names, not yet cleaned), region_type, ds, rain_total_mm, rain_days.
  - rain_days = days where the AREA-MEAN rain >= 2.5 mm (consistent with rain_total_mm). min_count=1 keeps all-NaN periods NaN (xarray default would give 0).
  - Validated: no duplicates, NaN only for the 2 island subdivisions, Kerala/Tamil Nadu/W. Rajasthan monthly patterns match known monsoon behaviour.
- Step 6b (temperature): `python src/build_temperature_table.py` -> `data/processed/temperature_monthly.csv` (4320 rows).
  - Columns: subdivision, region_type, ds, tmax_mean_c, tmin_mean_c, tavg_c = (tmax+tmin)/2, temp_n_cells.
  - Monthly mean of the area-averaged daily value. Grid is 1 deg (31x31); no sentinels found.
  - Shared loader moved to `src/imd_data.py` (`load_year(variable, year)`); rain output verified byte-identical after the refactor.
  - Validated: tmin<=tavg<=tmax everywhere, NaN only for the 2 islands, seasonal shapes correct (W. Rajasthan May 41C, Kerala flat 29-33C).
- Step 7 (humidity): DONE. `python src/build_humidity_table.py` -> `data/processed/humidity_monthly.csv` (4320 rows; columns subdivision, region_type, ds, rh_mean_pct, rh_n_stations). Equal-weight mean over stations; `assign_points_to_regions` added to `src/subdivisions.py`. 242 of 244 stations assigned. 152 NaN rows = 144 (Sep-Dec 2025, NOAA gap) + 8 (Arunachal, single station). Islands have RH (Lakshadweep ~2 stations, A&N 1). 7% of subdivision-months rest on a single station. Details:
  - Source: NOAA GSOD via `python src/download_gsod.py` -> `data/raw/gsod/<year>/<station>.csv` (gitignored; 2008 files, 141 MB; 244 Indian stations with data). Daily TEMP/DEWP in F, 9999.9 = missing.
  - Coverage: 4-10 stations per subdivision typically; thinnest Arunachal (1), Coastal Karnataka (2), N M M T (2). Usable station-month = >=15 usable days (10/15/20 gives the same coverage).
  - **GSOD data ends 2025-08-24**: Aug 2025 is partial (24 days); Sep-Dec 2025 will be NaN (decision: keep the full Jan 2016 - Dec 2025 period, leave those NaN).
  - Station -> subdivision: point-in-polygon; stations outside all polygons go to the nearest polygon if within 40 km, else dropped (drops T B I A, bad coordinates, and Car Nicobar, 61 km). Islands then get humidity even though rain/temp are NaN.
  - Obs-count check: GSOD needs >=4 obs/day (42% of days have 8, 18% have 4, 12% have 24). Requiring >=8 changes monthly station RH by 0.03 pts on average but drops 28% of station-months -> keep all days.
  - `src/humidity.py`: Magnus formula (a=17.625, b=243.04 C, Alduchov & Eskridge 1996), tested against textbook values (20/10 C -> 52.5%, 30/20 C -> 55.1%). Dew point above temp by more than rounding (0.5%) -> NaN; none occurred in the data.
  - Limitation: GSOD only gives daily means, so RH is computed from mean T and mean Td (RH at mean conditions), not the mean of sub-daily RH.
- Step 8: DONE. `python src/assemble_table.py` -> `data/processed/climate_monthly.csv` (4320 rows x 11 columns, the final table). Clean names from `data/subdivision_names.csv` (user-approved; single source of truth for names). Merge asserts row count unchanged.
  - Validation figure: `python src/plot_climatology.py` -> `figures/climatology_heatmaps.png` (subdivision x calendar month, rows north to south).
  - Checked against known patterns: Kerala wettest Jul/Aug/Jun, 64% of rain in Jun-Sep; Tamil Nadu wettest Nov/Oct, 44% of rain in Oct-Dec (38% Jun-Sep); W. Rajasthan 87% of rain in Jun-Sep, only 4% Oct-Dec. All as expected.
  - 199 exact-zero rain months are real dry months (Jan/Feb/Nov/Dec mostly; Gujarat, Konkan, Maharashtra), not misread NaNs.

## Known limitations to document
- A&N Islands and Lakshadweep lie outside the rain grid's data -> rain is NaN there.
- 321 of 4964 grid cells with data (6.5%) are in no subdivision: 295 are within 0.25 deg of a polygon (coast/border fringe, centre falls just outside), 26 farther (max 0.44 deg), scattered. Dropped, not reassigned.
- Temperature grid is 1 deg: Kerala and Coastal Karnataka get only 2 cells, Uttarakhand / Konkan & Goa / Haryana-Chandigarh-Delhi 3. Values are coarse there; see `temp_n_cells`. Lakshadweep has 0 cells, A&N has 1 with no data (both NaN).
- The boundary file predates the 2019 J&K split: the Jammu & Kashmir polygon includes Ladakh.
- Boundary projection is fitted, not official (~10-20 km).

## Next
- Step 9: README (sources, licences, limitations, date pulled), commit and push.
- Steps 8-9: assemble the final table (merge rain + temperature + humidity), validate with heatmaps, README.
