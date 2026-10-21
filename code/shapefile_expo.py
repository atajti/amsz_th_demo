"""Read shapefile"""

import pandas as pd
import shapefile
import geopandas as gpd
from itertools import chain


def read_shapefile(sf_shape):
    """
    Read a shapefile into a Pandas dataframe with a 'coords' 
    column holding the geometry information. This uses the pyshp
    package
    """

    fields = [x[0] for x in sf_shape.fields][1:]
    records = [y[:] for y in sf_shape.records()]
    #records = sf_shape.records()
    shps = [s.points for s in sf_shape.shapes()]
    df = pd.DataFrame(columns=fields, data=records)
    df = df.assign(coords=shps)
    return df



gdf = gpd.read_file("data/EFM 2025-ös adatok/EFM_30_link_módosított.shp")

print("Original CRS:", gdf.crs)
gdf_wgs84 = gdf.to_crs(epsg=4326)
gdf_wgs84.to_file("data/efm_converted/efm_converted_wgs84.shp")
gdf_wgs84.to_file("data/efm_kml/efm_kml", driver="KML")


EFM_path = "data/efm_converted/efm_converted_wgs84"

sf = shapefile.Reader(EFM_path)
shp_df = read_shapefile(sf)
shp_df.groupby("UTTIPUS~25").first(5).reset_index()[["UTTIPUS~25","coords", "KEREKPA~26"]].to_csv("data/kp_uttipus_teszt_googlecoords.csv", sep=";")

shp_df["KP"].groupby(["UTTIPUS~25", "TSYSSET"]).size()
"KP" in set(chain.from_iterable([tsysset.split(",") for tsysset in shp_df["TSYSSET"].to_list()]))
shp_df["JARMUTIPUSOK"] = shp_df["TSYSSET"].str.split(",")
shp_df["KEREKPAROZHATO"] = shp_df["JARMUTIPUSOK"].apply(lambda jt: "KP" in jt)
first_five = shp_df[shp_df["KEREKPAROZHATO"]].groupby(["UTTIPUS~25"]).head(5)[["UTTIPUS~25","coords", "KEREKPA~26"]]






