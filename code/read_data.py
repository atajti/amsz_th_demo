"""Import Google data timeline"""
import json
import re
import os
from os import PathLike
from pprint import pprint
from itertools import chain
import pandas as pd
from code.location_deduplication import load_points, cluster_points



def find_jsonfile_paths(root: str | PathLike = ".") -> list:
    """searches a directory forr googel timeline files"""
    full_paths = []
    for path, subdirs, files in os.walk(root):
        for name in files:
            full_paths.append([f for f in files if f.endswith(".json")])
    return list(chain.from_iterable(full_paths))


def detect_old_timeline(timeline_data: dict) -> bool:
    """checks if a json is old timeline format"""
    return"locations" in timeline_data

def detect_new_timeline(timeline_data) -> bool:
    """checks if a soon is new timeline format"""
    return "semanticSegments" in timeline_data


def load_timeline(filepath: str|PathLike) -> dict:
    """reads a timeline, adds type = old/new flag"""
    try:
        with open(filepath, "r") as jsonfile:
            data = json.load(jsonfile)
    except Exception as e:
        print(f"{e} when reading {filepath}")
        return None
    if detect_old_timeline(data):
        data["timeline_type"] = "old"
    elif detect_new_timeline(data):
        data["timeline_type"] = "new"
    else:
        print(f"No timeline type could be identified in file {filepath}, skipping.")
    return data


def read_timelines(folder: str|PathLike = ".") -> list[dict]:
    """reads all timeline data hat is found"""
    jsonfiles = find_jsonfile_paths(folder)
    timeline_list = [load_timeline(f"{folder}/{jsonf}") for jsonf in jsonfiles]





def get_semanticsegmets(folder):


all_timelines = read_timelines("data")


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