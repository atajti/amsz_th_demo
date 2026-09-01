"""map timeline dataframe"""
import folium
import pandas as pd


cyc_df = pd.read_parquet("data/timeline_utak.parquet")
coord_cols = ["from_lat", "from_lon", "to_lat", "to_lon"]
cyc_df[coord_cols] = cyc_df[coord_cols].apply(round, ndigits=3)
cyc_df["from_id"] = cyc_df["from_lat"].astype(str) + cyc_df["from_lon"].astype(str)
cyc_df["to_id"] = cyc_df["to_lat"].astype(str) + cyc_df["to_lon"].astype(str)
most_freq_pos = pd.concat([(cyc_df[["from_lat", "from_lon"]]).rename(columns={"from_lat":"lat", "from_lon":"lon"}),
                           (cyc_df[["to_lat", "to_lon"]]).rename(columns={"to_lat":"lat", "to_lon":"lon"})]) \
                  .groupby(["lat", "lon"]).size().sort_values(ascending=False) \
                  .reset_index() \
                  .rename(columns={0:"freq"}) \
                  .dropna()
most_freq_pos["id"]=most_freq_pos["lat"].astype(str)+most_freq_pos["lon"].astype(str)



rel_df = cyc_df[(cyc_df["from_id"].isin(most_freq_pos[most_freq_pos["freq"]>100]["id"])) &
                (cyc_df["to_id"].isin(most_freq_pos[most_freq_pos["freq"]>100]["id"])) &
                (cyc_df["transport"]=="CYCLING")].dropna()


m = folium.Map(
    location=[rel_df["from_lat"].mean(), rel_df["from_lon"].mean()],
    zoom_start=14
)

folium.TileLayer(
    tiles="http://localhost:5000/tiles/{z}/{x}/{y}.png",
    attr="OpenStreetMap cached"
).add_to(m)

colors = {
    "WALKING": "green",
    "CYCLING": "blue",
    "IN_PASSENGER_VEHICLE": "red",
    "IN_BUS": "orange",
    "IN_TRAIN": "black"
}


for _, row in rel_df.iterrows():
    folium.PolyLine(
        [
            (row["from_lat"], row["from_lon"]),
            (row["to_lat"], row["to_lon"])
        ],
        color=colors.get(row["transport"], "gray"),
        weight=3,
        opacity=0.1
    ).add_to(m)


m.save("data/bringasterkep.html")
