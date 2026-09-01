"""Import Google data timeline"""
import json
import re
import pandas as pd
from pprint import pprint


def parse_point(s):
    """
    '47.4979°, 19.0402°' -> (47.4979,19.0402)
    """
    if not s:
        return None, None
    nums = re.findall(r"-?\d+\.\d+", s["latLng"])
    if len(nums) >= 2:
        return float(nums[0]), float(nums[1])
    return None, None


with open("data/Timeline.json") as timelinefile:
    timeline = json.load(timelinefile)

rows = []

for seg in timeline.get("semanticSegments", []):
    activity = seg.get("activity")
    if not activity:
        continue
    lat1, lon1 = parse_point(activity.get("start"))
    lat2, lon2 = parse_point(activity.get("end"))
    rows.append({
        "start": seg.get("startTime"),
        "end": seg.get("endTime"),
        "transport": activity.get("topCandidate").get("type"),
        "distance_m": activity.get("distanceMeters"),
        "from_lat": lat1,
        "from_lon": lon1,
        "to_lat": lat2,
        "to_lon": lon2
    })

df = pd.DataFrame(rows)
df.to_parquet("data/timeline_utak.parquet")

print(df.head())

df["transport"].value_counts()
df["from_lat"].value_counts()
df["to_lat"].value_counts()
df["from_lon"].value_counts()
df["to_lon"].value_counts()
df.info()
df[(df["from_lat"].isin(df["from_lat"].nlargest(3))) |
   (df["from_lon"].isin(df["from_lon"].nlargest(3))) |
   (df["to_lat"].isin(df["to_lat"].nlargest(3))) |
   (df["to_lon"].isin(df["to_lon"].nlargest(3)))]

cyc_df = df[df["transport"]=="CYCLING"]
cyc_df[(cyc_df["from_lat"].isin(cyc_df["from_lat"].nlargest(3))) |
   (cyc_df["from_lon"].isin(cyc_df["from_lon"].nlargest(3))) |
   (cyc_df["to_lat"].isin(cyc_df["to_lat"].nlargest(3))) |
   (cyc_df["to_lon"].isin(cyc_df["to_lon"].nlargest(3)))].info()
cyc_df["duration"] = pd.to_datetime(cyc_df["end"], utc=True)-pd.to_datetime(cyc_df["start"], utc=True)

cyc_df.to_excel("data/bringas_utak.xlsx")