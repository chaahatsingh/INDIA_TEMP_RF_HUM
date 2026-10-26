"""Helpers for assigning IMD grid cells to subdivisions (or any other boundary file)."""
import geopandas as gpd
import numpy as np
import xarray as xr

# IMD's sd_boundary.json has no declared CRS. This Albers projection was fitted
# (see PROGRESS.md) and verified by overlaying the polygons on the rain grid.
IMD_SUBDIVISION_CRS = (
    "+proj=aea +lat_1=20.983 +lat_2=27.971 +lat_0=0 +lon_0=79.986 "
    "+x_0=402204 +y_0=66056 +datum=WGS84 +units=m"
)


def load_boundaries(path, source_crs=IMD_SUBDIVISION_CRS):
    """Read a boundary file and return it in lon/lat (EPSG:4326).

    allow_override is needed because geopandas assumes GeoJSON is already lon/lat,
    which is wrong for this file.
    """
    boundaries = gpd.read_file(path)
    return boundaries.set_crs(source_crs, allow_override=True).to_crs(4326)


def assign_points_to_regions(points, boundaries, name_column, max_distance_km=40):
    """Assign each point to the region containing it, or the nearest one within max_distance_km.

    points: GeoDataFrame in EPSG:4326 with a unique index. Returns a Series of region names
    (index = points.index); points further than the limit from every region are left out.
    A point inside a polygon is at distance 0 from it, so one nearest-join covers both cases.
    Distances are measured in an equal-area projection so the limit really is in kilometres.
    """
    projected_points = points[["geometry"]].to_crs("EPSG:6933")
    projected_regions = boundaries[[name_column, "geometry"]].to_crs("EPSG:6933")
    joined = gpd.sjoin_nearest(
        projected_points, projected_regions, how="inner", max_distance=max_distance_km * 1000
    )
    joined = joined[~joined.index.duplicated(keep="first")]  # a tie between two polygons: keep one
    return joined[name_column]


def cell_membership(grid, boundaries, name_column):
    """Label each grid cell with the region whose polygon contains its centre.

    grid: xarray DataArray/Dataset with `lat` and `lon` coordinates.
    Returns a DataArray (lat, lon) of region names; cells outside every polygon are "".
    """
    lon_centres, lat_centres = np.meshgrid(grid.lon.values, grid.lat.values)
    cell_points = gpd.GeoDataFrame(
        geometry=gpd.points_from_xy(lon_centres.ravel(), lat_centres.ravel()),
        crs=4326,
    )
    joined = gpd.sjoin(cell_points, boundaries[[name_column, "geometry"]], predicate="within", how="left")
    # A point on a shared border can match two polygons; keep the first match only.
    joined = joined[~joined.index.duplicated(keep="first")]
    labels = joined[name_column].fillna("").to_numpy().reshape(lon_centres.shape)
    return xr.DataArray(labels, coords={"lat": grid.lat, "lon": grid.lon}, dims=("lat", "lon"))
