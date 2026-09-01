"""valós utak és google javaslatok összevetése"""

from datetime import datetime
import numpy as np
import json
import pandas as pd
from code.gmaps_trip_durations import get_durations

with open("secrets/api_keys.json", "r") as secretsfile:
    GOOGLEMAPS_KEY = json.load(secretsfile)["googlemaps"]

def part_of_day(dt: datetime) -> str:
    """Categorize time of day into:
        - morning: 0-7
        - morning_rush: 7-9
        - middle: 9-16
        - afternoon_rush: 16-18
        - evening: 18-24"""
    if dt.hour < 7:
        return "morning"
    elif dt.hour < 9:
        return "morning_rush"
    elif dt.hour < 16:
        return "middle"
    elif dt.hour < 18:
        return "afternoon_rush"
    else:
        return "evening"



coord_cols = ["from_lat", "from_lon", "to_lat", "to_lon"]

cyc_df = pd.read_parquet("data/timeline_utak.parquet")
cyc_df[coord_cols] = cyc_df[coord_cols].apply(round, ndigits=3)
cyc_df["from_id"] = cyc_df["from_lat"].astype(str) + cyc_df["from_lon"].astype(str)
cyc_df["to_id"] = cyc_df["to_lat"].astype(str) + cyc_df["to_lon"].astype(str)
cyc_df["start"] = pd.to_datetime(cyc_df["start"], utc=True)
cyc_df["end"] = pd.to_datetime(cyc_df["end"], utc=True)
cyc_df["weekday"] = cyc_df["start"].dt.dayofweek.apply(lambda d: "weekday" if d<5 else "weekend")
cyc_df["part_of_day"] = pd.to_datetime(cyc_df["start"], utc=True).apply(part_of_day)
cyc_df["duration"] = cyc_df["end"]-cyc_df["start"]

most_freq_pos = pd.concat([(cyc_df[["from_lat", "from_lon"]]).rename(columns={"from_lat":"lat", "from_lon":"lon"}),
                           (cyc_df[["to_lat", "to_lon"]]).rename(columns={"to_lat":"lat", "to_lon":"lon"})]) \
                  .groupby(["lat", "lon"]).size().sort_values(ascending=False).reset_index().rename(columns={0:"freq"})
most_freq_pos["id"]=most_freq_pos["lat"].astype(str)+most_freq_pos["lon"].astype(str)



rel_df = cyc_df[(cyc_df["from_id"].isin(most_freq_pos[most_freq_pos["freq"]>100]["id"])) &
                (cyc_df["to_id"].isin(most_freq_pos[most_freq_pos["freq"]>100]["id"]))].copy()
                #(cyc_df["transport"]=="CYCLING")].copy()


real = rel_df.groupby(["from_id", "to_id", "transport"]) \
             .agg(duration_mean = ("duration", "mean"),
                 duration_std = ("duration", "std"),
                 count = ("duration", "size"),
                 from_lat = ("from_lat", "first"),
                 from_lon = ("from_lon", "first"),
                 to_lat = ("to_lat", "first"),
                 to_lon = ("to_lon", "first")) \
             .reset_index() \
             .sort_values("count", ascending=False)
real["duration_mean_sec"] = real["duration_mean"] / np.timedelta64(1, 's')
real["duration_std_sec"] = real["duration_std"] / np.timedelta64(1, 's')
real.drop(columns=["duration_mean", "duration_std"]).to_excel("data/valos_utak_all.xlsx", index=False)

relevant = real[(real["transport"].isin(["WALKING", "IN_PASSENGER_VEHICLE", "CYCLING"])) &
                (real["count"]>3)][["from_lat", "from_lon", "to_lat", "to_lon"]].drop_duplicates().reset_index()

test_list = []
for rownum in range(len(relevant)):
    test_list.append(get_durations(origin=tuple(relevant.loc[rownum, ["from_lat", "from_lon"]]),
                                   destination=tuple(relevant.loc[rownum, ["to_lat", "to_lon"]]),
                                   api_key=GOOGLEMAPS_KEY))

gmaps_results = pd.DataFrame(test_list)
gmaps_results["from_lat"] = gmaps_results["origin"].apply(lambda x: x[0])
gmaps_results["from_lon"] = gmaps_results["origin"].apply(lambda x: x[1])
gmaps_results["to_lat"] = gmaps_results["destination"].apply(lambda x: x[0])
gmaps_results["to_lon"] = gmaps_results["destination"].apply(lambda x: x[1])
gmaps_results.rename(columns={"transport":"mode"}, inplace=True)
gmaps_results["transport"]=gmaps_results["mode"].map({"driving":"IN_PASSENGER_VEHICLE",
                                                      "transit":"PUBLIC_TRANSPORT",
                                                      "bicycling":"CYCLING",
                                                      "walking":"WALKING"})


comparable = pd.merge(gmaps_results.drop(columns=["origin", "destination"]), real,
                      on=["transport", "from_lat", "from_lon", "to_lat", "to_lon"],
                      how="right").drop(columns="mode") \
               .rename(columns={"transport_sec":"predicted_duration"})
comparable.to_excel("data/comparable_trips.xlsx", index=False)
