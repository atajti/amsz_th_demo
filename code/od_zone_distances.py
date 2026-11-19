"""Match OD volume data with zone centroid coordinates and Euclidean distances."""

import geopandas as gpd
import numpy as np
import pandas as pd


SHAPEFILE_PATH = 
OD_INPUT_PATH = 
OD_SHEET_NAME = "alapadatok"
OD_OUTPUT_PATH = 


def load_zone_centroids(shp_path: str = "data/bkk_adatok/zones/EFM_EXP_zone.shp") -> pd.DataFrame:
    """Load zone polygons and compute centroids in both EOV (meters) and WGS84 (lat/lon)."""
    gdf = gpd.read_file(shp_path)

    # Compute centroids in native projected CRS (HD72 / EOV, EPSG:23700, in meters)
    centroids_eov = gdf.geometry.centroid
    centroids_wgs84 = gpd.GeoSeries(centroids_eov, crs=gdf.crs).to_crs(epsg=4326)

    zones_df = pd.DataFrame({
        "zone_no": gdf["NO"].astype(int),
        "x": centroids_eov.x,
        "y": centroids_eov.y,
        "lat": centroids_wgs84.y,
        "lon": centroids_wgs84.x,
    })
    return zones_df


zone_centers = load_zone_centroids("data/bkk_adatok/zones/EFM_EXP_zone.shp")
od_df = pd.read_excel("data/od_volume_info.xlsx",
                      sheet_name="alapadatok")
od_df["from_no"] = od_df["from"].astype(str).str.split("_", n=1).str[0].astype(int)
od_df["to_no"] = od_df["to"].astype(str).str.split("_", n=1).str[0].astype(int)

from_coords = zone_centers.rename(columns={"zone_no": "from_no",
                                           "x": "from_x",
                                           "y": "from_y",
                                           "lat": "from_lat",
                                           "lon": "from_lon"})
to_coords = zone_centers.rename(columns={"zone_no": "to_no",
                                         "x": "to_x",
                                         "y": "to_y",
                                         "lat": "to_lat",
                                         "lon": "to_lon"})

merged = pd.merge(pd.merge(od_df,
                           from_coords,
                           on="from_no",
                           how="left"),
                  to_coords,
                  on="to_no",
                  how="left")


merged["distance_m"] = np.hypot(
    merged["to_x"] - merged["from_x"],
    merged["to_y"] - merged["from_y"],
)


merged.to_excel("data/od_volume_with_distances.xlsx",
                sheet_name="alapadatok",
                index=False)
